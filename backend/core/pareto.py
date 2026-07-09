"""Multi-objective Pareto frontier calculator.

Implements non-dominated sorting, crowding distance computation,
and knee-point selection for hardware-aware model optimization.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from backend.models.schemas import CandidateInfo, ParetoPoint


@dataclass
class ParetoResult:
    """Result of Pareto frontier computation.

    Attributes:
        frontier: List of Pareto-optimal candidate points.
        dominated: List of dominated candidate points.
        num_objectives: Number of optimization objectives used.
    """

    frontier: list[ParetoPoint] = field(default_factory=list)
    dominated: list[ParetoPoint] = field(default_factory=list)
    num_objectives: int = 4


# Maps objective names to whether higher values are better.
_OBJECTIVE_DIRECTION: dict[str, bool] = {
    "accuracy": True,
    "accuracy_top1": True,
    "throughput": True,
    "throughput_img_s": True,
    "latency": False,
    "latency_ms": False,
    "vram": False,
    "vram_gb": False,
}


def _get_objective_value(candidate: CandidateInfo, objective: str) -> float:
    """Extract the objective value from a candidate.

    Args:
        candidate: The candidate to extract the value from.
        objective: Name of the objective (e.g., "accuracy", "latency_ms").

    Returns:
        The numeric value of the objective.

    Raises:
        ValueError: If the objective is not found on the candidate.
    """
    if candidate.metrics is None:
        raise ValueError(
            f"Candidate {candidate.id} has no metrics for objective '{objective}'"
        )

    mapping: dict[str, float] = {
        "accuracy": candidate.metrics.accuracy_top1,
        "accuracy_top1": candidate.metrics.accuracy_top1,
        "throughput": candidate.metrics.throughput_img_s,
        "throughput_img_s": candidate.metrics.throughput_img_s,
        "latency": candidate.metrics.latency_ms,
        "latency_ms": candidate.metrics.latency_ms,
        "vram": candidate.metrics.vram_gb,
        "vram_gb": candidate.metrics.vram_gb,
    }

    if objective not in mapping:
        raise ValueError(f"Unknown objective: {objective}")

    return mapping[objective]


def _candidate_to_pareto_point(
    candidate: CandidateInfo, objectives: list[str]
) -> ParetoPoint:
    """Convert a CandidateInfo to a ParetoPoint.

    Args:
        candidate: The candidate to convert.
        objectives: List of objective names used in the computation.

    Returns:
        A ParetoPoint with values extracted from the candidate.
    """
    metrics = candidate.metrics
    return ParetoPoint(
        candidate_id=candidate.id,
        accuracy=metrics.accuracy_top1 if metrics else 0.0,
        latency_ms=metrics.latency_ms if metrics else 0.0,
        throughput_img_s=metrics.throughput_img_s if metrics else 0.0,
        vram_gb=metrics.vram_gb if metrics else 0.0,
        is_pareto_optimal=True,
    )


def compute_pareto_frontier(
    candidates: list[CandidateInfo],
    objectives: list[str] | None = None,
) -> ParetoResult:
    """Compute the Pareto frontier using non-dominated sorting.

    Identifies Pareto-optimal candidates across multiple objectives.
    Assigns Pareto ranks where rank 0 is the frontier, rank 1 is
    dominated by the frontier, etc.

    For accuracy and throughput: higher is better.
    For latency and VRAM: lower is better.

    Args:
        candidates: List of candidate architectures with metrics.
        objectives: List of objective names to optimize. Defaults to
            ["accuracy", "latency", "throughput", "vram"].

    Returns:
        ParetoResult containing the frontier and dominated sets.

    Raises:
        ValueError: If fewer than 2 candidates are provided.
    """
    if objectives is None:
        objectives = ["accuracy", "latency", "throughput", "vram"]

    if len(candidates) < 2:
        points = [
            _candidate_to_pareto_point(c, objectives) for c in candidates
        ]
        return ParetoResult(
            frontier=points,
            dominated=[],
            num_objectives=len(objectives),
        )

    ranked = _non_dominated_sort(candidates, objectives)

    frontier_points: list[ParetoPoint] = []
    dominated_points: list[ParetoPoint] = []

    for candidate, rank in ranked:
        point = _candidate_to_pareto_point(candidate, objectives)
        point.is_pareto_optimal = rank == 0
        if rank == 0:
            frontier_points.append(point)
        else:
            point.is_pareto_optimal = False
            dominated_points.append(point)

    return ParetoResult(
        frontier=frontier_points,
        dominated=dominated_points,
        num_objectives=len(objectives),
    )


def _non_dominated_sort(
    candidates: list[CandidateInfo], objectives: list[str]
) -> list[tuple[CandidateInfo, int]]:
    """Perform non-dominated sorting to assign Pareto ranks.

    Implements a fast non-dominated sort that assigns rank 0 to
    the Pareto frontier, rank 1 to candidates dominated only by
    rank-0 candidates, etc.

    Args:
        candidates: List of candidates to sort.
        objectives: List of objective names.

    Returns:
        List of (candidate, rank) tuples sorted by rank ascending.
    """
    n = len(candidates)
    domination_count = [0] * n
    dominated_set: list[list[int]] = [[] for _ in range(n)]

    for i in range(n):
        for j in range(i + 1, n):
            if is_dominated(candidates[i], candidates[j], objectives):
                domination_count[i] += 1
                dominated_set[j].append(i)
            elif is_dominated(candidates[j], candidates[i], objectives):
                domination_count[j] += 1
                dominated_set[i].append(j)

    ranks: list[tuple[CandidateInfo, int]] = []
    current_rank = 0
    remaining = list(range(n))

    while remaining:
        rank_front: list[int] = []
        for i in remaining:
            if domination_count[i] == 0:
                rank_front.append(i)

        if not rank_front:
            for i in remaining:
                ranks.append((candidates[i], current_rank))
            break

        for i in rank_front:
            ranks.append((candidates[i], current_rank))
            remaining.remove(i)
            for j in dominated_set[i]:
                if j in remaining:
                    domination_count[j] -= 1

        current_rank += 1

    return sorted(ranks, key=lambda x: x[1])


def is_dominated(
    a: CandidateInfo, b: CandidateInfo, objectives: list[str]
) -> bool:
    """Check if candidate a is dominated by candidate b.

    Candidate b dominates a if b is at least as good in all objectives
    and strictly better in at least one.

    Args:
        a: First candidate (potentially dominated).
        b: Second candidate (potentially dominating).
        objectives: List of objective names to compare.

    Returns:
        True if b dominates a, False otherwise.
    """
    all_at_least_as_good = True
    strictly_better_in_one = False

    for objective in objectives:
        val_a = _get_objective_value(a, objective)
        val_b = _get_objective_value(b, objective)
        higher_is_better = _OBJECTIVE_DIRECTION.get(objective, True)

        if higher_is_better:
            if val_b < val_a:
                all_at_least_as_good = False
                break
            if val_b > val_a:
                strictly_better_in_one = True
        else:
            if val_b > val_a:
                all_at_least_as_good = False
                break
            if val_b < val_a:
                strictly_better_in_one = True

    return all_at_least_as_good and strictly_better_in_one


def compute_crowding_distance(frontier: list[ParetoPoint]) -> list[float]:
    """Compute crowding distance for diversity preservation on the frontier.

    Points at the boundaries of the frontier (minimum and maximum values
    for each objective) receive infinity distance to preserve extreme points.

    Args:
        frontier: List of Pareto-optimal points.

    Returns:
        List of crowding distances parallel to the input frontier.
    """
    n = len(frontier)
    if n <= 2:
        return [math.inf] * n

    distances = [0.0] * n
    objectives_list = ["accuracy", "latency_ms", "throughput_img_s", "vram_gb"]

    for objective in objectives_list:
        sorted_indices = sorted(range(n), key=lambda i: _get_point_value(frontier[i], objective))
        distances[sorted_indices[0]] = math.inf
        distances[sorted_indices[-1]] = math.inf

        min_val = _get_point_value(frontier[sorted_indices[0]], objective)
        max_val = _get_point_value(frontier[sorted_indices[-1]], objective)
        spread = max_val - min_val

        if spread <= 0:
            continue

        for k in range(1, n - 1):
            distances[sorted_indices[k]] += (
                _get_point_value(frontier[sorted_indices[k + 1]], objective)
                - _get_point_value(frontier[sorted_indices[k - 1]], objective)
            ) / spread

    return distances


def _get_point_value(point: ParetoPoint, objective: str) -> float:
    """Extract a value from a ParetoPoint by objective name.

    Args:
        point: The Pareto point.
        objective: Name of the objective.

    Returns:
        Numeric value of the objective.
    """
    mapping: dict[str, float] = {
        "accuracy": point.accuracy,
        "latency_ms": point.latency_ms,
        "throughput_img_s": point.throughput_img_s,
        "vram_gb": point.vram_gb,
    }
    return mapping.get(objective, 0.0)


def select_knee_point(frontier: list[ParetoPoint]) -> ParetoPoint | None:
    """Find the knee point on the Pareto frontier.

    The knee point is the point with maximum curvature, representing
    the "best compromise" solution that balances all objectives.

    Uses a normalized distance-based heuristic: the point whose
    Euclidean distance to the utopia point is maximized relative
    to its neighbors.

    Args:
        frontier: List of Pareto-optimal points.

    Returns:
        The knee point, or None if the frontier is empty.
    """
    if not frontier:
        return None

    if len(frontier) == 1:
        return frontier[0]

    if len(frontier) == 2:
        return frontier[0]

    objectives_list = ["accuracy", "latency_ms", "throughput_img_s", "vram_gb"]

    min_vals: dict[str, float] = {}
    max_vals: dict[str, float] = {}
    for obj in objectives_list:
        vals = [_get_point_value(p, obj) for p in frontier]
        min_vals[obj] = min(vals)
        max_vals[obj] = max(vals)

    def normalize(point: ParetoPoint) -> dict[str, float]:
        normalized: dict[str, float] = {}
        for obj in objectives_list:
            spread = max_vals[obj] - min_vals[obj]
            if spread <= 0:
                normalized[obj] = 0.5
            else:
                val = _get_point_value(point, obj)
                norm = (val - min_vals[obj]) / spread
                if _OBJECTIVE_DIRECTION.get(obj, True):
                    normalized[obj] = norm
                else:
                    normalized[obj] = 1.0 - norm
        return normalized

    utopia = {obj: 1.0 for obj in objectives_list}

    knee_index = 0
    max_dist = -1.0

    for i, point in enumerate(frontier):
        norm = normalize(point)
        dist = sum((norm[obj] - utopia[obj]) ** 2 for obj in objectives_list) ** 0.5
        if dist > max_dist:
            max_dist = dist
            knee_index = i

    return frontier[knee_index]
