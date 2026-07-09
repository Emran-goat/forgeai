"""GPU metrics collection utilities."""

from typing import Any


def get_gpu_metrics() -> dict[str, Any]:
    """Get current GPU utilization, memory, and temperature."""
    return {
        "utilization_pct": 0.0,
        "memory_used_gb": 0.0,
        "memory_total_gb": 0.0,
        "temperature_c": 0.0,
        "power_watts": 0.0,
    }


def start_profiling() -> None:
    """Start GPU profiling session."""
    pass


def stop_profiling() -> dict[str, Any]:
    """Stop profiling and return collected metrics."""
    return {"duration_s": 0.0, "avg_utilization": 0.0, "peak_memory_gb": 0.0}
