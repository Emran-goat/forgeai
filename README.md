# ForgeAI

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-3776AB.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![ROCm](https://img.shields.io/badge/ROCm-6.0+-ED1C24.svg)](https://rocm.docs.amd.com/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg)](https://www.docker.com/)

Hardware-aware AI model optimization for AMD GPUs. Upload a PyTorch checkpoint, run a 6-phase optimization pipeline (architecture search, distillation, pruning, quantization, benchmarking, Pareto analysis), and export an optimized model for MI300X.

Built for [AMD Developer Hackathon ACT II, Track 3](https://github.com/Emran-goat/forgeai).

## Install

```bash
git clone https://github.com/Emran-goat/forgeai.git
cd forgeai
pip install -r requirements.txt
```

For the frontend:

```bash
cd frontend && npm install && npm run dev
```

Or with Docker:

```bash
cp .env.example .env  # set FIREWORKS_API_KEY
docker compose up --build
```

## Usage

```python
import requests

# Upload
files = {"file": open("model.pth", "rb")}
model_id = requests.post("http://localhost:8000/api/models", files=files).json()["id"]

# Optimize
job_id = requests.post("http://localhost:8000/api/optimizations", json={
    "model_id": model_id,
    "hardware": "MI300X",
    "constraints": {"max_latency_ms": 50, "max_memory_mb": 1024, "min_accuracy": 0.95}
}).json()["id"]

# Export
requests.post("http://localhost:8000/api/exports", json={"optimization_id": job_id, "format": "onnx"})
```

## Architecture

```
forgeai/
├── backend/          # FastAPI + PyTorch optimization engine
│   ├── api/          # REST + WebSocket routes
│   ├── core/         # 8 optimization modules
│   └── services/     # Business logic
├── frontend/         # Next.js 14 + shadcn/ui
├── demo/             # 7 standalone HTML demos
└── forgeai-demo/     # Remotion video (56s, 1080p)
```

## Tech stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI, Pydantic v2, WebSocket |
| ML | PyTorch 2.2+, timm, ROCm 6.0+ |
| Database | SQLite + aiosqlite |
| Frontend | Next.js 14, Tailwind CSS, shadcn/ui, Recharts |
| Target GPU | AMD MI300X (192GB HBM3) |
| Hosted inference | Fireworks AI (AMD Instinct MI300X) |

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/models` | POST/GET/DELETE | Upload and manage models |
| `/api/optimizations` | POST/GET | Start and track optimization jobs |
| `/api/candidates` | GET | List candidate architectures |
| `/api/benchmarks` | GET | Query benchmark results |
| `/api/benchmarks/fireworks` | GET | Fireworks AI vs local comparison |
| `/api/exports` | POST/GET | Export optimized models (ONNX/TorchScript) |
| `/api/hardware` | GET | Hardware specs |
| `/ws/{job_id}` | WS | Live optimization progress |

## License

Apache 2.0. See [LICENSE](LICENSE).

## Cite

```bibtex
@software{forgeai2024,
  title={ForgeAI: Hardware-Aware AI Model Optimization Platform},
  author={ForgeAI Team},
  year={2024},
  url={https://github.com/Emran-goat/forgeai}
}
```
