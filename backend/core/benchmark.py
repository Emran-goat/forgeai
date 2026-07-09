"""ROCm-based benchmark profiler for model latency, throughput, and VRAM usage.

Provides GPU benchmarking with warmup iterations, CUDA event timing,
VRAM tracking, and FLOPs estimation. Supports AMD ROCm and NVIDIA CUDA.
"""

from __future__ import annotations

import statistics
import time
from dataclasses import dataclass, field
from typing import Any

import torch
from torch import nn


@dataclass(frozen=True)
class BenchmarkConfig:
    """Configuration for GPU benchmark runs.

    Attributes:
        hardware_target: Target hardware identifier (e.g., "mi300x").
        iterations: Number of timed iterations to run.
        warmup_iterations: Number of warmup iterations (discarded from results).
        batch_size: Batch size for input tensors.
        input_shape: Shape of input tensor (batch, channels, height, width).
        measure_vram: Whether to track VRAM allocation.
    """

    hardware_target: str = "mi300x"
    iterations: int = 100
    warmup_iterations: int = 10
    batch_size: int = 1
    input_shape: tuple[int, ...] = (1, 3, 224, 224)
    measure_vram: bool = True


@dataclass
class BenchmarkResult:
    """Result of a GPU benchmark run.

    Attributes:
        latency_ms: Mean inference latency in milliseconds.
        latency_std_ms: Standard deviation of latency in milliseconds.
        throughput_img_s: Images processed per second.
        vram_peak_gb: Peak VRAM usage in gigabytes.
        vram_avg_gb: Average VRAM usage in gigabytes.
        flops_g: Estimated floating-point operations in billions.
        hardware_info: Dictionary of GPU hardware properties.
    """

    latency_ms: float
    latency_std_ms: float
    throughput_img_s: float
    vram_peak_gb: float
    vram_avg_gb: float
    flops_g: float
    hardware_info: dict[str, Any] = field(default_factory=dict)


class GPUBenchmark:
    """GPU benchmark runner for measuring model performance.

    Uses CUDA/ROCm events for precise timing and tracks VRAM usage
    across warmup and timed iterations.

    Attributes:
        config: Benchmark configuration.
    """

    def __init__(self, config: BenchmarkConfig | None = None) -> None:
        """Initialize the GPU benchmark.

        Args:
            config: Benchmark configuration. Uses defaults if not provided.
        """
        self.config = config or BenchmarkConfig()

    def run(self, model: nn.Module) -> BenchmarkResult:
        """Run a full benchmark on the given model.

        Executes warmup iterations (discarded), then timed iterations
        with CUDA event timing. Measures VRAM if enabled and computes
        FLOPs estimation.

        Args:
            model: PyTorch model to benchmark. Must be on the target device.

        Returns:
            Comprehensive benchmark results including latency, throughput,
            VRAM usage, and FLOPs.

        Raises:
            RuntimeError: If no CUDA/ROCm device is available.
        """
        if not torch.cuda.is_available():
            return self._run_cpu_fallback(model)

        device = torch.device("cuda")
        model.eval()
        model.to(device)

        input_tensor = torch.randn(
            self.config.input_shape, device=device, dtype=torch.float32
        )

        self._warmup(model, input_tensor)

        latencies = self._timed_iterations(model, input_tensor)

        vram_stats = self._measure_vram(model, input_tensor) if self.config.measure_vram else (0.0, 0.0)

        flops = estimate_flops(model, self.config.input_shape)

        mean_lat = statistics.mean(latencies)
        std_lat = statistics.stdev(latencies) if len(latencies) > 1 else 0.0
        throughput = (1000.0 * self.config.batch_size) / mean_lat if mean_lat > 0 else 0.0

        return BenchmarkResult(
            latency_ms=round(mean_lat, 4),
            latency_std_ms=round(std_lat, 4),
            throughput_img_s=round(throughput, 2),
            vram_peak_gb=round(vram_stats[0], 4),
            vram_avg_gb=round(vram_stats[1], 4),
            flops_g=round(flops, 2),
            hardware_info=self._get_gpu_info(),
        )

    def _warmup(self, model: nn.Module, input_tensor: torch.Tensor) -> None:
        """Execute warmup iterations to stabilize GPU clocks.

        Args:
            model: Model to warm up.
            input_tensor: Sample input tensor.
        """
        with torch.no_grad():
            for _ in range(self.config.warmup_iterations):
                model(input_tensor)

    def _timed_iterations(
        self, model: nn.Module, input_tensor: torch.Tensor
    ) -> list[float]:
        """Run timed iterations and collect per-iteration latencies.

        Uses CUDA events for precise GPU-side timing when available,
        falls back to CPU-side time.perf_counter for CPU execution.

        Args:
            model: Model to benchmark.
            input_tensor: Sample input tensor.

        Returns:
            List of per-iteration latencies in milliseconds.
        """
        latencies: list[float] = []

        use_cuda_events = input_tensor.is_cuda and torch.cuda.is_available()

        with torch.no_grad():
            if use_cuda_events:
                start_event = torch.cuda.Event(enable_timing=True)  # type: ignore[no-untyped-call]
                end_event = torch.cuda.Event(enable_timing=True)  # type: ignore[no-untyped-call]

                for _ in range(self.config.iterations):
                    start_event.record()
                    model(input_tensor)
                    end_event.record()
                    torch.cuda.synchronize()
                    latencies.append(start_event.elapsed_time(end_event))
            else:
                for _ in range(self.config.iterations):
                    t0 = time.perf_counter()
                    model(input_tensor)
                    t1 = time.perf_counter()
                    latencies.append((t1 - t0) * 1000.0)

        return latencies

    def _measure_vram(
        self, model: nn.Module, input_tensor: torch.Tensor
    ) -> tuple[float, float]:
        """Measure VRAM usage during inference.

        Tracks peak and average VRAM allocation across timed iterations.

        Args:
            model: Model to benchmark.
            input_tensor: Sample input tensor.

        Returns:
            Tuple of (peak_gb, average_gb) VRAM usage.
        """
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.empty_cache()

        allocations: list[int] = []

        with torch.no_grad():
            for _ in range(self.config.iterations):
                model(input_tensor)
                allocations.append(torch.cuda.memory_allocated())

        peak_bytes = torch.cuda.max_memory_allocated()
        avg_bytes = statistics.mean(allocations) if allocations else 0

        peak_gb = peak_bytes / (1024 ** 3)
        avg_gb = avg_bytes / (1024 ** 3)

        return (peak_gb, avg_gb)

    def _get_gpu_info(self) -> dict[str, Any]:
        """Retrieve GPU hardware properties.

        Returns:
            Dictionary with GPU name, VRAM total, compute capability,
            and other device properties. Empty dict if no CUDA device.
        """
        if not torch.cuda.is_available():
            return {"device": "cpu"}

        props = torch.cuda.get_device_properties(0)
        return {
            "name": props.name,
            "total_memory_gb": round(props.total_memory / (1024 ** 3), 2),
            "major": props.major,
            "minor": props.minor,
            "multi_processor_count": props.multi_processor_count,
            "is_integrated": props.is_integrated,
            "is_multi_gpu_board": props.is_multi_gpu_board,
        }

    def _run_cpu_fallback(self, model: nn.Module) -> BenchmarkResult:
        """Run benchmark on CPU when no GPU is available.

        Args:
            model: Model to benchmark on CPU.

        Returns:
            Benchmark results with CPU timing and zero VRAM usage.
        """
        model.eval()
        input_tensor = torch.randn(self.config.input_shape, dtype=torch.float32)

        self._warmup(model, input_tensor)
        latencies = self._timed_iterations(model, input_tensor)
        flops = estimate_flops(model, self.config.input_shape)

        mean_lat = statistics.mean(latencies)
        std_lat = statistics.stdev(latencies) if len(latencies) > 1 else 0.0
        throughput = (1000.0 * self.config.batch_size) / mean_lat if mean_lat > 0 else 0.0

        return BenchmarkResult(
            latency_ms=round(mean_lat, 4),
            latency_std_ms=round(std_lat, 4),
            throughput_img_s=round(throughput, 2),
            vram_peak_gb=0.0,
            vram_avg_gb=0.0,
            flops_g=round(flops, 2),
            hardware_info={"device": "cpu"},
        )


def estimate_flops(model: nn.Module, input_shape: tuple[int, ...]) -> float:
    """Estimate floating-point operations for a forward pass.

    Uses torch.profiler to count FLOPs when available, falling back
    to a parameter-based heuristic estimation.

    Args:
        model: PyTorch model to profile.
        input_shape: Shape of the input tensor.

    Returns:
        Estimated FLOPs in billions (GFLOPs).
    """
    model.eval()
    device = next(model.parameters()).device if list(model.parameters()) else torch.device("cpu")
    input_tensor = torch.randn(input_shape, device=device, dtype=torch.float32)

    try:
        with torch.profiler.profile(
            activities=[torch.profiler.ProfilerActivity.CPU],
            record_shapes=True,
        ) as prof, torch.no_grad():
            model(input_tensor)

        total_flops = 0
        for event in prof.key_averages():
            if hasattr(event, "flops") and event.flops > 0:
                total_flops += event.flops

        if total_flops > 0:
            return total_flops / 1e9
    except (RuntimeError, AttributeError):
        pass

    return _estimate_flops_heuristic(model)


def _estimate_flops_heuristic(model: nn.Module) -> float:
    """Estimate FLOPs using a parameter-count heuristic.

    Approximates 2 * params FLOPs per forward pass for typical
    feed-forward networks.

    Args:
        model: PyTorch model.

    Returns:
        Estimated FLOPs in billions.
    """
    total_params = sum(p.numel() for p in model.parameters())
    return (2 * total_params) / 1e9


def compare_baselines(
    model_a: BenchmarkResult, model_b: BenchmarkResult
) -> dict[str, Any]:
    """Compare two benchmark results to quantify trade-offs.

    Computes speedup ratio, memory savings, and a summary of the
    performance trade-off between two model configurations.

    Args:
        model_a: Benchmark result for the first model (baseline).
        model_b: Benchmark result for the second model (comparison).

    Returns:
        Dictionary with speedup_ratio, memory_savings_gb, and trade_off_summary.
    """
    speedup = model_a.latency_ms / model_b.latency_ms if model_b.latency_ms > 0 else 0.0
    memory_savings = model_a.vram_peak_gb - model_b.vram_peak_gb

    if speedup > 1.0 and memory_savings > 0:
        summary = "Model B is faster and uses less memory."
    elif speedup > 1.0:
        summary = "Model B is faster but uses more memory."
    elif memory_savings > 0:
        summary = "Model B uses less memory but is slower."
    else:
        summary = "Model B is slower and uses more memory."

    return {
        "speedup_ratio": round(speedup, 4),
        "memory_savings_gb": round(memory_savings, 4),
        "throughput_delta_img_s": round(
            model_b.throughput_img_s - model_a.throughput_img_s, 2
        ),
        "flops_delta_g": round(model_b.flops_g - model_a.flops_g, 2),
        "trade_off_summary": summary,
    }
