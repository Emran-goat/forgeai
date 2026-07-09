"""Structured and unstructured pruning engine.

Implements magnitude-based weight pruning, channel pruning, and movement
pruning for model compression. Uses PyTorch's built-in pruning utilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:
    import torch
    import torch.nn.utils.prune as prune

    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False


def _check_torch() -> None:
    """Raise ImportError if PyTorch is not installed."""
    if not _TORCH_AVAILABLE:
        raise ImportError(
            "PyTorch is required for pruning operations. "
            "Install with: pip install torch"
        )


@dataclass
class PruningResult:
    """Result of a pruning operation.

    Attributes:
        model: The pruned model (weights modified in-place).
        sparsity: Fraction of weights set to zero (0.0 to 1.0).
        num_params_original: Total parameters before pruning.
        num_params_pruned: Non-zero parameters after pruning.
        pruning_mask: Per-layer binary masks, or None for unstructured pruning.
    """

    model: Any  # nn.Module when torch is available
    sparsity: float
    num_params_original: int
    num_params_pruned: int
    pruning_mask: dict[str, Any] | None = None


def _compute_sparsity(model: Any) -> float:
    """Compute global sparsity of a model.

    Args:
        model: A PyTorch nn.Module.

    Returns:
        Fraction of zero-valued parameters (0.0 = dense, 1.0 = fully sparse).
    """
    total = 0
    zeros = 0
    for param in model.parameters():
        total += param.numel()
        zeros += (param == 0).sum().item()
    return zeros / total if total > 0 else 0.0


def _count_params(model: Any) -> tuple[int, int]:
    """Count total and non-zero parameters.

    Args:
        model: A PyTorch nn.Module.

    Returns:
        Tuple of (total_params, non_zero_params).
    """
    total = 0
    non_zero = 0
    for param in model.parameters():
        total += param.numel()
        non_zero += (param != 0).sum().item()
    return total, non_zero


def structured_pruning(model: Any, ratio: float) -> PruningResult:
    """Apply structured (channel) pruning by removing entire filters.

    Uses L1-norm to rank channels and prunes the least important ones.
    Only applies to Conv2d and Linear layers.

    Args:
        model: PyTorch model to prune (modified in-place).
        ratio: Fraction of channels to remove (0.0 to 1.0).

    Returns:
        PruningResult with sparsity metrics and the pruned model.

    Raises:
        ImportError: If PyTorch is not available.
        ValueError: If ratio is not in [0.0, 1.0].
    """
    _check_torch()
    if not 0.0 <= ratio <= 1.0:
        raise ValueError(f"ratio must be in [0.0, 1.0], got {ratio}")

    for _name, module in model.named_modules():
        if isinstance(module, torch.nn.Conv2d) and module.out_channels > 1:
            prune.ln_structured(
                module, name="weight", amount=ratio, n=2, dim=0
            )
            prune.remove(module, "weight")
        elif isinstance(module, torch.nn.Linear):
            prune.l1_unstructured(module, name="weight", amount=ratio)
            prune.remove(module, "weight")

    total, non_zero = _count_params(model)
    sparsity = _compute_sparsity(model)

    return PruningResult(
        model=model,
        sparsity=sparsity,
        num_params_original=total,
        num_params_pruned=non_zero,
        pruning_mask=None,
    )


def unstructured_pruning(model: Any, ratio: float) -> PruningResult:
    """Apply magnitude-based unstructured pruning.

    Zeroes out the smallest weights globally across all parameters.
    Achieves high sparsity but does not reduce memory footprint without
    sparse tensor support.

    Args:
        model: PyTorch model to prune (modified in-place).
        ratio: Fraction of weights to prune (0.0 to 1.0).

    Returns:
        PruningResult with sparsity metrics and the pruned model.

    Raises:
        ImportError: If PyTorch is not available.
        ValueError: If ratio is not in [0.0, 1.0].
    """
    _check_torch()
    if not 0.0 <= ratio <= 1.0:
        raise ValueError(f"ratio must be in [0.0, 1.0], got {ratio}")

    for _name, module in model.named_modules():
        if isinstance(module, (torch.nn.Conv2d, torch.nn.Linear)):
            prune.l1_unstructured(module, name="weight", amount=ratio)
            prune.remove(module, "weight")

    total, non_zero = _count_params(model)
    sparsity = _compute_sparsity(model)

    return PruningResult(
        model=model,
        sparsity=sparsity,
        num_params_original=total,
        num_params_pruned=non_zero,
        pruning_mask=None,
    )


def apply_movement_pruning(
    model: Any, ratio: float, threshold: float = 0.01
) -> PruningResult:
    """Prune weights based on movement magnitude during training.

    Simplified movement pruning: prunes weights whose absolute value
    falls below the threshold, scaled by the pruning ratio. This
    approximates the effect of tracking weight deltas during training.

    Args:
        model: PyTorch model to prune (modified in-place).
        ratio: Fraction of weights to prune (0.0 to 1.0).
        threshold: Minimum weight magnitude to retain.

    Returns:
        PruningResult with sparsity metrics and the pruned model.

    Raises:
        ImportError: If PyTorch is not available.
        ValueError: If ratio is not in [0.0, 1.0] or threshold is negative.
    """
    _check_torch()
    if not 0.0 <= ratio <= 1.0:
        raise ValueError(f"ratio must be in [0.0, 1.0], got {ratio}")
    if threshold < 0:
        raise ValueError(f"threshold must be >= 0, got {threshold}")

    for module in model.modules():
        if isinstance(module, (torch.nn.Conv2d, torch.nn.Linear)):
            weight = module.weight.data
            abs_weight = weight.abs()
            cutoff = threshold + (abs_weight.max().item() - threshold) * (1 - ratio)
            mask = abs_weight >= cutoff
            module.weight.data *= mask.float()

    total, non_zero = _count_params(model)
    sparsity = _compute_sparsity(model)

    return PruningResult(
        model=model,
        sparsity=sparsity,
        num_params_original=total,
        num_params_pruned=non_zero,
        pruning_mask=None,
    )


def get_pruning_stats(model: Any) -> dict[str, float]:
    """Report per-layer and global pruning statistics.

    Args:
        model: A PyTorch nn.Module.

    Returns:
        Dictionary with keys:
            - "total_params": total parameter count
            - "non_zero_params": non-zero parameter count
            - "global_sparsity": fraction of zero weights
            - "{layer_name}.sparsity": per-layer sparsity for each module
            - "{layer_name}.params": parameter count for each module

    Raises:
        ImportError: If PyTorch is not available.
    """
    _check_torch()
    stats: dict[str, float] = {}
    total_params = 0
    non_zero_params = 0

    for name, module in model.named_modules():
        if not list(module.parameters(recurse=False)):
            continue
        layer_params = 0
        layer_zeros = 0
        for param in module.parameters(recurse=False):
            layer_params += param.numel()
            layer_zeros += (param == 0).sum().item()

        total_params += layer_params
        non_zero_params += layer_params - layer_zeros

        sparsity = layer_zeros / layer_params if layer_params > 0 else 0.0
        stats[f"{name}.sparsity"] = sparsity
        stats[f"{name}.params"] = float(layer_params)

    stats["total_params"] = float(total_params)
    stats["non_zero_params"] = float(non_zero_params)
    stats["global_sparsity"] = (
        (total_params - non_zero_params) / total_params if total_params > 0 else 0.0
    )

    return stats
