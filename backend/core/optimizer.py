"""Main optimization pipeline orchestrator.

Coordinates the full optimization pipeline: architecture search,
knowledge distillation, pruning, quantization, benchmarking,
and Pareto frontier computation.
"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Awaitable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)

from backend.models.schemas import CandidateInfo, CandidateMetrics

# Global registry for active optimization states.
_active_optimizations: dict[str, OptimizationState] = {}


class OptimizationPhase(StrEnum):
    """Phases of the optimization pipeline."""

    SEARCH = "search"
    DISTILL = "distill"
    PRUNE = "prune"
    QUANTIZE = "quantize"
    BENCHMARK = "benchmark"
    PARETO = "pareto"
    HYPERPARAMETER_TUNING = "hyperparameter_tuning"


@dataclass
class OptimizationState:
    """Tracks the state of an active optimization run.

    Attributes:
        optimization_id: Unique identifier for this optimization.
        current_phase: Currently executing phase.
        phases_completed: Number of phases completed.
        total_phases: Total number of phases.
        candidates: List of candidate architectures.
        start_time: Unix timestamp when optimization started.
        is_cancelled: Whether cancellation has been requested.
    """

    optimization_id: str
    current_phase: OptimizationPhase
    phases_completed: int = 0
    total_phases: int = 7
    candidates: list[CandidateInfo] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    is_cancelled: bool = False


class OptimizationOrchestrator:
    """Orchestrates the full optimization pipeline.

    Manages the lifecycle of an optimization run through all six phases,
    from architecture search to Pareto frontier computation. Supports
    progress callbacks for WebSocket streaming and graceful cancellation.

    Attributes:
        optimization_id: Unique identifier for this optimization.
        config: Configuration dictionary with search space, constraints, etc.
        state: Current optimization state.
    """

    def __init__(self, optimization_id: str, config: dict[str, Any]) -> None:
        """Initialize the optimization orchestrator.

        Args:
            optimization_id: Unique identifier for this optimization run.
            config: Configuration dictionary containing model_id, hardware_target,
                constraints, objectives, and search_space.
        """
        self.optimization_id = optimization_id
        self.config = config
        self.state = OptimizationState(
            optimization_id=optimization_id,
            current_phase=OptimizationPhase.SEARCH,
        )
        _active_optimizations[optimization_id] = self.state

    async def run(
        self,
        progress_callback: Callable[[str, dict[str, Any]], Awaitable[None]] | None = None,
    ) -> dict[str, Any]:
        """Execute the full optimization pipeline.

        Runs all six phases sequentially, reporting progress via callback
        and handling cancellation at each phase boundary.

        Args:
            progress_callback: Optional async callback invoked with (phase_name, data)
                for each phase transition and completion.

        Returns:
            Dictionary containing optimization_id, status, candidates,
            pareto_frontier, and total_duration_s.

        Raises:
            RuntimeError: If the optimization is cancelled during execution.
        """
        self.state.start_time = time.time()

        try:
            candidates = await self._run_phase(
                OptimizationPhase.SEARCH,
                self._phase_search,
                progress_callback,
            )

            candidates = await self._run_phase(
                OptimizationPhase.DISTILL,
                lambda: self._phase_distill(candidates),
                progress_callback,
            )

            candidates = await self._run_phase(
                OptimizationPhase.PRUNE,
                lambda: self._phase_prune(candidates),
                progress_callback,
            )

            candidates = await self._run_phase(
                OptimizationPhase.QUANTIZE,
                lambda: self._phase_quantize(candidates),
                progress_callback,
            )

            candidates = await self._run_phase(
                OptimizationPhase.BENCHMARK,
                lambda: self._phase_benchmark(candidates),
                progress_callback,
            )

            result = await self._run_phase(
                OptimizationPhase.PARETO,
                lambda: self._phase_pareto(candidates),
                progress_callback,
            )

            tuning_result = await self._run_phase(
                OptimizationPhase.HYPERPARAMETER_TUNING,
                lambda: self._phase_hyperparam_tune(candidates),
                progress_callback,
            )

            duration = time.time() - self.state.start_time

            if progress_callback:
                await progress_callback("completed", {
                    "optimization_id": self.optimization_id,
                    "total_candidates": len(self.state.candidates),
                    "duration_s": round(duration, 2),
                })

            _active_optimizations.pop(self.optimization_id, None)

            return {
                "optimization_id": self.optimization_id,
                "status": "completed",
                "candidates": [c.model_dump() for c in self.state.candidates],
                "pareto_frontier": result,
                "hyperparameter_tuning": tuning_result,
                "total_duration_s": round(duration, 2),
            }

        except CancellationError:
            _active_optimizations.pop(self.optimization_id, None)
            return {
                "optimization_id": self.optimization_id,
                "status": "cancelled",
                "candidates": [c.model_dump() for c in self.state.candidates],
                "pareto_frontier": None,
                "total_duration_s": round(time.time() - self.state.start_time, 2),
            }

    async def _run_phase(
        self,
        phase: OptimizationPhase,
        phase_fn: Callable[..., Any],
        progress_callback: Callable[[str, dict[str, Any]], Awaitable[None]] | None = None,
    ) -> Any:
        """Execute a single phase with progress reporting and cancellation checks.

        Args:
            phase: The phase to execute.
            phase_fn: Callable that executes the phase logic.
            progress_callback: Optional async progress callback.

        Returns:
            Result of the phase function.

        Raises:
            CancellationError: If cancellation is requested.
        """
        self._check_cancelled()
        self.state.current_phase = phase

        if progress_callback:
            await progress_callback("phase_start", {
                "phase": phase.value,
                "phases_completed": self.state.phases_completed,
                "total_phases": self.state.total_phases,
            })

        result = await phase_fn()

        self.state.phases_completed += 1

        if progress_callback:
            await progress_callback("phase_complete", {
                "phase": phase.value,
                "phases_completed": self.state.phases_completed,
                "total_phases": self.state.total_phases,
                "candidates_count": len(self.state.candidates),
            })

        return result

    def _check_cancelled(self) -> None:
        """Check if cancellation has been requested.

        Raises:
            CancellationError: If the optimization has been cancelled.
        """
        if self.state.is_cancelled:
            raise CancellationError(f"Optimization {self.optimization_id} cancelled")

    async def _phase_search(self) -> list[CandidateInfo]:
        """Generate candidate architectures via architecture search.

        Returns:
            List of generated candidate architectures.
        """
        from backend.core.architecture_search import generate_candidates
        from backend.models.schemas import SearchSpace

        search_space_data = self.config.get("search_space", {})
        search_space = SearchSpace(**search_space_data) if search_space_data else SearchSpace()
        num_candidates = self.config.get("num_candidates", 10)

        arch_candidates = generate_candidates(search_space, num_candidates)

        candidates: list[CandidateInfo] = []
        for arch in arch_candidates:
            candidate = CandidateInfo(
                id=str(uuid.uuid4()),
                optimization_id=self.optimization_id,
                architecture=arch.name,
                params_m=arch.params_m,
            )
            candidates.append(candidate)

        self.state.candidates = candidates
        return candidates

    async def _phase_distill(
        self, candidates: list[CandidateInfo]
    ) -> list[CandidateInfo]:
        """Train each candidate via knowledge distillation.

        Args:
            candidates: List of candidates to train.

        Returns:
            Updated list of candidates with training results.
        """
        from backend.core.distillation import DistillationConfig, KnowledgeDistiller

        config = DistillationConfig(
            temperature=self.config.get("distillation_temperature", 4.0),
            alpha=self.config.get("distillation_alpha", 0.7),
            epochs=self.config.get("distillation_epochs", 10),
        )
        distiller = KnowledgeDistiller(config)

        for candidate in candidates:
            self._check_cancelled()

            try:
                from torch import nn

                from backend.core.architecture_search import build_model_from_config

                config = {
                    "architecture_type": candidate.architecture,
                    "variant": candidate.architecture,
                    "input_size": 224 * 224 * 3,
                }
                student = build_model_from_config(config)
                teacher = build_model_from_config(config)

                train_loader = _create_dummy_loader()
                val_loader = _create_dummy_loader()

                result = distiller.distill(
                    teacher=teacher,
                    student=student,
                    train_loader=train_loader,
                    val_loader=val_loader,
                )

                candidate.metrics = CandidateMetrics(
                    accuracy_top1=result.val_accuracy,
                    latency_ms=0.0,
                    throughput_img_s=0.0,
                    vram_gb=0.0,
                    flops_g=0.0,
                )
            except Exception:
                logger.exception("Distillation failed for candidate %s", candidate.id)
                candidate.metrics = CandidateMetrics(
                    accuracy_top1=0.0,
                    latency_ms=0.0,
                    throughput_img_s=0.0,
                    vram_gb=0.0,
                    flops_g=0.0,
                )

        return candidates

    async def _phase_prune(
        self, candidates: list[CandidateInfo]
    ) -> list[CandidateInfo]:
        """Apply pruning to each candidate.

        Args:
            candidates: List of candidates to prune.

        Returns:
            Updated list of candidates after pruning.
        """
        from backend.core.pruning import structured_pruning

        search_space_data = self.config.get("search_space", {})
        pruning_ratios = search_space_data.get("pruning_ratios", [0.3])

        for candidate in candidates:
            self._check_cancelled()

            try:
                from torch import nn

                from backend.core.architecture_search import build_model_from_config

                config = {
                    "architecture_type": candidate.architecture,
                    "variant": candidate.architecture,
                    "input_size": 224 * 224 * 3,
                }
                model = build_model_from_config(config)

                ratio = pruning_ratios[0] if pruning_ratios else 0.3
                result = structured_pruning(model, ratio)

                if candidate.metrics:
                    candidate.params_m = round(
                        candidate.params_m * (1.0 - result.sparsity), 2
                    )
            except Exception:
                logger.exception("Pruning failed for candidate %s", candidate.id)

        return candidates

    async def _phase_quantize(
        self, candidates: list[CandidateInfo]
    ) -> list[CandidateInfo]:
        """Quantize each candidate.

        Args:
            candidates: List of candidates to quantize.

        Returns:
            Updated list of candidates after quantization.
        """
        from backend.core.quantization import ModelQuantizer, QuantizationConfig

        search_space_data = self.config.get("search_space", {})
        quantization_modes = search_space_data.get("quantization_modes", ["int8"])

        for candidate in candidates:
            self._check_cancelled()

            try:
                from torch import nn

                from backend.core.architecture_search import build_model_from_config

                config = {
                    "architecture_type": candidate.architecture,
                    "variant": candidate.architecture,
                    "input_size": 224 * 224 * 3,
                }
                model = build_model_from_config(config)

                mode = quantization_modes[0] if quantization_modes else "int8"
                q_config = QuantizationConfig(mode=mode, use_qat=False)
                quantizer = ModelQuantizer(q_config)
                quantizer.quantize(model)

                if candidate.metrics and mode in ("int8", "int4"):
                    reduction = 0.5 if mode == "int8" else 0.75
                    candidate.params_m = round(
                        candidate.params_m * (1.0 - reduction * 0.3), 2
                    )
            except Exception:
                logger.exception("Quantization failed for candidate %s", candidate.id)

        return candidates

    async def _phase_benchmark(
        self, candidates: list[CandidateInfo]
    ) -> list[CandidateInfo]:
        """Benchmark each candidate on target hardware.

        Args:
            candidates: List of candidates to benchmark.

        Returns:
            Updated list of candidates with benchmark metrics.
        """
        from backend.core.benchmark import BenchmarkConfig, GPUBenchmark

        hardware_target = self.config.get("hardware_target", "mi300x")
        config = BenchmarkConfig(
            hardware_target=hardware_target,
            iterations=self.config.get("benchmark_iterations", 100),
            warmup_iterations=self.config.get("benchmark_warmup_iterations", 10),
        )
        benchmark = GPUBenchmark(config)

        for candidate in candidates:
            self._check_cancelled()

            try:
                from torch import nn

                from backend.core.architecture_search import build_model_from_config

                config = {
                    "architecture_type": candidate.architecture,
                    "variant": candidate.architecture,
                    "input_size": 224 * 224 * 3,
                }
                model = build_model_from_config(config)
                result = benchmark.run(model)

                candidate.metrics = CandidateMetrics(
                    accuracy_top1=candidate.metrics.accuracy_top1 if candidate.metrics else 0.0,
                    latency_ms=result.latency_ms,
                    throughput_img_s=result.throughput_img_s,
                    vram_gb=result.vram_peak_gb,
                    flops_g=result.flops_g,
                )
            except Exception:
                logger.exception("Benchmark failed for candidate %s", candidate.id)
                if candidate.metrics is None:
                    candidate.metrics = CandidateMetrics(
                        accuracy_top1=0.0,
                        latency_ms=0.0,
                        throughput_img_s=0.0,
                        vram_gb=0.0,
                        flops_g=0.0,
                    )

        return candidates

    async def _phase_pareto(
        self, candidates: list[CandidateInfo]
    ) -> dict[str, Any]:
        """Compute Pareto frontier from benchmarked candidates.

        Args:
            candidates: List of candidates with benchmark metrics.

        Returns:
            Dictionary with frontier and dominated sets.
        """
        from backend.core.pareto import (
            compute_crowding_distance,
            compute_pareto_frontier,
            select_knee_point,
        )

        objectives = self.config.get(
            "objectives", ["accuracy", "latency", "throughput", "vram"]
        )

        result = compute_pareto_frontier(candidates, objectives)

        for candidate in self.state.candidates:
            for point in result.frontier:
                if candidate.id == point.candidate_id:
                    candidate.is_pareto_optimal = True
                    candidate.pareto_rank = 0
                    break
            else:
                for point in result.dominated:
                    if candidate.id == point.candidate_id:
                        candidate.is_pareto_optimal = False
                        break

        crowding_distances = compute_crowding_distance(result.frontier)
        knee_point = select_knee_point(result.frontier)

        return {
            "frontier": [p.model_dump() for p in result.frontier],
            "dominated": [p.model_dump() for p in result.dominated],
            "crowding_distances": [round(d, 4) if d != float("inf") else "inf" for d in crowding_distances],
            "knee_point": knee_point.model_dump() if knee_point else None,
            "num_objectives": result.num_objectives,
        }

    async def _phase_hyperparam_tune(
        self, candidates: list[CandidateInfo]
    ) -> dict[str, Any]:
        """Tune hyperparameters using Optuna.

        Runs Bayesian optimization over distillation, pruning, and
        quantization parameters to find the best configuration.

        Args:
            candidates: List of candidates to tune hyperparameters for.

        Returns:
            Dictionary with TuningResult data.
        """
        from backend.core.hyperparameter import HyperparameterConfig, HyperparameterTuner
        from backend.models.schemas import ConstraintSet

        constraints_data = self.config.get("constraints", {})
        constraints = ConstraintSet(**constraints_data) if constraints_data else ConstraintSet()

        weights = self.config.get("objective_weights", {
            "accuracy": 1.0,
            "latency": 0.5,
            "vram": 0.3,
        })

        hp_config = HyperparameterConfig(
            n_trials=self.config.get("n_trials", 50),
            timeout_seconds=self.config.get("tuning_timeout_seconds", 3600),
            objective_weights=weights,
            constraints=constraints,
            hardware_target=self.config.get("hardware_target", "mi300x"),
        )

        tuner = HyperparameterTuner(hp_config)
        result = tuner.run_trials(candidates=candidates)

        import asyncio
        tuning_result = await result if asyncio.iscoroutine(result) else result

        for candidate in candidates:
            if candidate.metrics and tuning_result.best_params:
                pr = tuning_result.best_params.get("pruning_ratio", 0.3)
                qb = tuning_result.best_params.get("quantization_bits", 8)
                reduction = pr * (1.0 - qb / 32.0)
                candidate.params_m = round(candidate.params_m * (1.0 - max(0.0, reduction)), 2)

        return tuning_result.model_dump()


class CancellationError(Exception):
    """Raised when an optimization is cancelled."""


def cancel_optimization(optimization_id: str) -> bool:
    """Request cancellation of an active optimization.

    Sets the cancellation flag on the optimization state so that
    the next phase boundary check will raise CancellationError.

    Args:
        optimization_id: ID of the optimization to cancel.

    Returns:
        True if cancellation was requested, False if not found.
    """
    state = _active_optimizations.get(optimization_id)
    if state is None:
        return False

    state.is_cancelled = True
    return True


def get_optimization_state(optimization_id: str) -> OptimizationState | None:
    """Get the state of an active optimization.

    Args:
        optimization_id: ID of the optimization to query.

    Returns:
        The OptimizationState if found, None otherwise.
    """
    return _active_optimizations.get(optimization_id)


def _create_dummy_loader() -> Any:
    """Create a dummy DataLoader for distillation.

    Returns:
        A DataLoader yielding random input-label batches.
    """
    import torch
    from torch.utils.data import DataLoader, TensorDataset

    inputs = torch.randn(8, 224 * 224 * 3)
    labels = torch.randint(0, 1000, (8,))
    dataset = TensorDataset(inputs, labels)
    return DataLoader(dataset, batch_size=8)
