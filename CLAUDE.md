# ForgeAI — Working Memory

## Project
**ForgeAI** — Hardware-Aware AI Model Optimization Platform
"The compiler for efficient AI models."

## Current State
- **Phase:** 5 (Polish & Demo) — In Progress
- **Day:** 1
- **Status:** Phases 1-4 complete. Remotion video rendered (56s, 3.3 MB). README written. Demo index updated.
- **Build:** 7 routes compile clean (8 static pages + 7 demo HTML + 1 Remotion video)

## Architecture Decisions
| Decision | Choice | ADR |
|----------|--------|-----|
| API Framework | FastAPI 0.110+ | ADR-001 |
| ML Framework | PyTorch 2.2+ (ROCm) | ADR-002 |
| Database | SQLite + aiosqlite | ADR-003 |
| Frontend | Next.js 14 + shadcn/ui | ADR-004 |
| Real-time | WebSocket | ADR-005 |
| Architecture | Monolith with clean modules | ADR-006 |
| Japanese Minimalist UI | Wabi-sabi aesthetic, vermilion accent | ADR-007 |

## Key Files
| File | Purpose |
|------|---------|
| `PLAN.md` | Full hackathon build plan |
| `IDEA.md` | Project concept and vision |
| `.forgeai/progress.md` | Task completion tracker |
| `.forgeai/session-log.md` | Session history |
| `.forgeai/decisions.md` | Architecture Decision Records |

## Tech Stack
- **Backend:** Python 3.11, FastAPI, PyTorch, timm, aiosqlite
- **Frontend:** Next.js 14, Tailwind CSS, shadcn/ui, Recharts
- **Infra:** Docker + ROCm, GitHub Actions
- **GPU:** AMD MI300X via ROCm 6.0+

## Conventions
- Type hints on all functions (mypy --strict)
- Google-style docstrings
- pytest with >90% coverage
- Async/await for I/O operations
- Pydantic v2 for all schemas

## Current Task
Phase 4 complete. Next: Phase 5 — End-to-end testing, demo script, README, deploy.

## Core Engine Status
| Module | Status | Key Classes |
|--------|--------|-------------|
| `architecture_search.py` | Complete | `StudentArchitecture`, `generate_candidates()`, `build_model_from_config()` |
| `distillation.py` | Complete | `KnowledgeDistiller`, `DistillationConfig`, `DistillationResult` |
| `pruning.py` | Complete | `structured_pruning()`, `unstructured_pruning()`, `PruningResult` |
| `quantization.py` | Complete | `ModelQuantizer`, `QuantizationConfig`, `QuantizationResult` |
| `benchmark.py` | Complete | `GPUBenchmark`, `BenchmarkConfig`, `BenchmarkResult` |
| `pareto.py` | Complete | `compute_pareto_frontier()`, `ParetoResult`, `select_knee_point()` |
| `optimizer.py` | Complete | `OptimizationOrchestrator`, `OptimizationPhase`, progress callbacks |
| `export.py` | Complete | `export_to_onnx()`, `export_to_torchscript()`, `ExportResult` |

## API Routes Status
| Route | Status | Key Endpoints |
|-------|--------|---------------|
| `api/models.py` | Complete | POST/GET/DELETE with DB, chunked upload, architecture detection |
| `api/optimizations.py` | Complete | POST/GET/DELETE with background tasks, cancellation |
| `api/candidates.py` | Complete | GET candidates for optimization |
| `api/benchmarks.py` | Complete | GET benchmarks with hardware filter, Pareto query |
| `api/exports.py` | Complete | POST/GET exports with FileResponse download |
| `api/hardware.py` | Complete | GET MI300X/MI250X/CPU specs |
| `api/websocket.py` | Complete | WS with ConnectionManager, progress callbacks |

## Services Status
| Service | Status | Key Functions |
|---------|--------|---------------|
| `model_service.py` | Complete | save_model, delete_model_file, detect_architecture |
| `optimization_service.py` | Complete | start_optimization, cancel_optimization (background tasks) |
| `benchmark_service.py` | Complete | store_benchmark_result, get_benchmarks_for_candidate |

## People / Context
- Hackathon project targeting AMD judges
- Demo on MI300X hardware
- Support vision models (DINOv2, ViT) + small language models
- Multi-objective optimization with Pareto frontier

## Preferences
- Concise code, no unnecessary comments
- Prefer existing libraries over custom code
- Run lint/typecheck after every change
- Save context to files after every significant action
