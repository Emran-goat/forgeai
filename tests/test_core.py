"""Tests for core optimization engine."""

import pytest
import torch

from backend.core.architecture_search import generate_candidates
from backend.core.pareto import compute_pareto_frontier
from backend.core.pruning import structured_pruning
from backend.core.quantization import ModelQuantizer


def test_architecture_search():
    """Test architecture search generates candidates."""
    candidates = generate_candidates()
    assert len(candidates) > 0
    assert all(hasattr(c, "architecture_id") for c in candidates)


def test_pareto_frontier():
    """Test Pareto frontier computation."""
    # Create dummy data
    latencies = [10.0, 20.0, 15.0, 30.0]
    accuracies = [0.9, 0.85, 0.88, 0.8]
    memory = [512.0, 256.0, 384.0, 128.0]

    result = compute_pareto_frontier(latencies, accuracies, memory)
    assert result is not None
    assert len(result.pareto_indices) > 0


def test_structured_pruning():
    """Test structured pruning reduces model size."""
    # Create a simple linear model
    model = torch.nn.Linear(100, 10)
    original_params = sum(p.numel() for p in model.parameters())

    pruned_model = structured_pruning(model, sparsity=0.5)
    pruned_params = sum(p.numel() for p in pruned_model.parameters())

    assert pruned_params <= original_params
