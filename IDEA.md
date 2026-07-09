# ForgeAI — Hardware-Aware AI Model Optimization

## One-liner
"The compiler for efficient AI models."

## Tagline
Compile your AI for the hardware it deserves.

## Problem
Most AI model compression assumes "smaller = better." But Model A with fewer parameters may run slower than Model B on AMD MI300X because Model B better utilizes HBM3 bandwidth and ROCm kernels. The optimal compressed model depends on the hardware it runs on.

## Core Innovation
**Hardware-aware distillation**: Automatically find the fastest and most efficient version of a model for a specific hardware target. The hardware determines what "optimal" means.

## Workflow

### Input
- Teacher Model (PyTorch checkpoint)
- Target Hardware (MI300X, MI325X, CPU, edge device)
- Latency Budget (e.g., 20 ms)
- Memory Budget (e.g., 2 GB)
- Accuracy Target (e.g., 95%)

### Pipeline
1. Architecture Search — generate candidate student architectures
2. Knowledge Distillation — train students with teacher signals
3. Pruning — remove redundant weights
4. Quantization — INT8/FP8/INT4 optimization
5. Kernel Optimization — ROCm-specific tuning
6. ROCm Benchmarking — real latency/throughput on AMD GPUs
7. Deployment Package — export ONNX/TorchScript + benchmark report

### Output
- Optimized weights
- ONNX/TorchScript export
- Benchmark report
- Deployment package

## Multi-Objective Optimization
Simultaneously optimize for:
- Accuracy
- Latency
- Throughput
- VRAM usage
- Energy consumption
- Cost per million inferences

Generate a Pareto frontier where users choose their trade-off.

## Platform Vision (SaaS/API)
1. Upload a PyTorch checkpoint
2. Select target hardware
3. Platform searches for best student architecture
4. Returns optimized model + benchmark report + deployment package

## Demo Flow
1. Upload teacher model
2. Select MI300X
3. Run optimization
4. Watch candidate students evaluated
5. Show leaderboard of architectures
6. Export winning model
7. Switch target hardware to CUDA GPU → winner changes

## Scope (Hackathon)
- Vision model: DINOv2 or Vision Transformer
- Small language model (transformer)
- Both families prove framework is general, not narrowly scoped

## Why This Wins AMD Hackathon
- Showcases deep technical work leveraging AMD ROCm ecosystem
- Unusual — most teams build agent workflows
- Solid benchmarks + polished demo = stands out
- Directly relevant to AMD's efficient AI deployment story
