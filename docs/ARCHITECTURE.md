# ForgeAI Architecture

## Overview

ForgeAI is a hardware-aware AI model optimization platform that automatically finds the fastest, most efficient version of any AI model for target hardware.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js 14)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Upload  │  │ Optimize │  │ Results  │  │  Export  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     API Layer (FastAPI)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Models  │  │Optimize  │  │Benchmark │  │  Export  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Core Engine (PyTorch + ROCm)                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 Optimization Pipeline                   │   │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐│   │
│  │  │Search│→│Distil│→│Prune │→│Quant │→│Bench │→│Pareto││   │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘│   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Storage Layer                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  SQLite  │  │  Models  │  │ Exports  │  │ Fireworks│       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. API Layer (`backend/api/`)

| Module | Description |
|--------|-------------|
| `models.py` | Model upload, retrieval, and deletion |
| `optimizations.py` | Optimization job management |
| `candidates.py` | Architecture candidate queries |
| `benchmarks.py` | Benchmark result queries and Fireworks integration |
| `exports.py` | Model export (ONNX, TorchScript) |
| `hardware.py` | Hardware specification queries |
| `websocket.py` | Real-time progress streaming |

### 2. Core Engine (`backend/core/`)

| Module | Description |
|--------|-------------|
| `architecture_search.py` | Generates candidate architectures from search space |
| `distillation.py` | Knowledge distillation with soft targets and feature alignment |
| `pruning.py` | Structured, unstructured, and movement pruning |
| `quantization.py` | INT8/INT4/FP8 quantization with QAT |
| `benchmark.py` | GPU/CPU benchmarking with FLOPs and VRAM measurement |
| `pareto.py` | Multi-objective optimization with Pareto frontier |
| `optimizer.py` | 7-phase orchestrator with progress callbacks |
| `export.py` | ONNX and TorchScript export |
| `fireworks_client.py` | Fireworks AI API client for hosted inference |

### 3. Data Layer (`backend/models/`)

| Module | Description |
|--------|-------------|
| `schemas.py` | Pydantic v2 models for API validation |
| `database.py` | Async SQLite database with aiosqlite |

### 4. Services Layer (`backend/services/`)

| Module | Description |
|--------|-------------|
| `model_service.py` | Model file management and architecture detection |
| `optimization_service.py` | Background optimization job management |
| `benchmark_service.py` | Benchmark result storage and retrieval |
| `gemma_service.py` | Fireworks Gemma 4 API client for AI assistant |
| `optimization_advisor.py` | Natural language to optimization config translation |
| `visualization.py` | Auto-chart generation (Pareto, comparison, timeline) |

### 5. AI Assistant (`backend/api/assistant.py`)

| Endpoint | Purpose |
|----------|---------|
| `POST /setup` | Natural language → optimization config via Gemma |
| `POST /chat` | Context-aware chat about results |
| `POST /chat/stream` | SSE streaming chat response |
| `POST /run` | AI generates and triggers full optimization |
| `POST /visualize` | Auto-chart generation with AI explanation |
| `POST /export` | AI-assisted export with deployment guide |

**Flow:**
1. User sends natural language request
2. `gemma_service` calls Fireworks Gemma 4 API
3. `optimization_advisor` parses response into structured config
4. Response includes config, explanation, and suggested follow-ups

## Data Flow

1. **Upload**: User uploads PyTorch checkpoint via API
2. **Detection**: System detects model architecture (ViT, ResNet, etc.)
3. **Search**: Generates candidate architectures from search space
4. **Optimize**: Runs 7-phase pipeline (search → distill → prune → quantize → benchmark → Pareto → hyperparameter tuning)
5. **Results**: Returns Pareto frontier with optimal candidates
6. **Export**: Exports selected model to ONNX/TorchScript

## Technology Stack

- **Backend**: Python 3.11, FastAPI, PyTorch, timm, aiosqlite
- **Frontend**: Next.js 14, Tailwind CSS, shadcn/ui, Recharts
- **Infrastructure**: Docker, ROCm 6.0+, GitHub Actions
- **Cloud Inference**: Fireworks AI (AMD Instinct MI300X)

## Design Principles

1. **Async-first**: All I/O operations use async/await
2. **Type-safe**: Full type hints with mypy --strict
3. **Modular**: Clean separation of concerns
4. **Observable**: WebSocket progress streaming
5. **Hardware-aware**: Benchmarks against real GPU specs
