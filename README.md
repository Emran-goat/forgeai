# ForgeAI

**The compiler for efficient AI models.**

ForgeAI finds the fastest, most efficient version of any AI model for your target hardware. Upload a model, specify your constraints, and get an optimized export running on AMD MI300X GPUs.

## What it does

ForgeAI runs a 6-phase optimization pipeline:

1. **Architecture Search** -- explores student architectures (ViT variants, ResNet, MobileNet) that trade off accuracy for speed
2. **Knowledge Distillation** -- trains smaller models to mimic the original using soft targets and feature alignment
3. **Pruning** -- removes redundant weights (structured, unstructured, movement-based)
4. **Quantization** -- reduces precision (INT8, INT4, FP8) with optional quantization-aware training
5. **Benchmarking** -- measures real latency, throughput, and memory on target hardware
6. **Pareto Analysis** -- finds the optimal accuracy-speed tradeoff and selects the knee point

The result: a model that runs 2-10x faster with minimal accuracy loss, exported as ONNX or TorchScript.

## Architecture

```
forgeai/
├── backend/              # FastAPI + PyTorch
│   ├── api/              # REST routes + WebSocket
│   ├── core/             # Optimization engine (8 modules)
│   ├── models/           # Pydantic schemas + SQLite DB
│   └── services/         # Business logic layer
├── frontend/             # Next.js 14 + shadcn/ui
│   └── src/app/          # 6 pages with Japanese minimalist UI
├── demo/                 # 7 self-contained HTML demo pages
└── forgeai-demo/         # Remotion video project (1920×1080)
```

## Quick start

### Backend

```bash
cd backend
pip install -e .
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Demo pages

```bash
cd demo
python -m http.server 8080
# Open http://localhost:8080
```

### Docker

```bash
# Clone and configure
cp .env.example .env
# Edit .env with your FIREWORKS_API_KEY

# Build and run
docker compose up --build

# Or use the deploy script
chmod +x deploy.sh
./deploy.sh
```

### Deploy to HuggingFace Spaces

1. Push to GitHub
2. Go to [huggingface.co/new-space](https://huggingface.co/new-space)
3. Select "Docker" as the SDK
4. Connect your GitHub repo
5. Set `FIREWORKS_API_KEY` in Space secrets
6. Deploy

## Tech stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI 0.110+, Pydantic v2, WebSocket |
| ML | PyTorch 2.2+, ROCm 6.0+, timm |
| Database | SQLite + aiosqlite |
| Frontend | Next.js 14, Tailwind CSS, shadcn/ui, Recharts |
| Video | Remotion (1920×1080, 30fps) |
| Cloud Inference | Fireworks AI (AMD Instinct MI300X backend) |
| Target GPU | AMD MI300X (192GB HBM3) |

## Key features

- **Multi-objective optimization** -- latency, memory, and accuracy on the Pareto frontier
- **Live progress** -- WebSocket-streamed optimization phases to the UI
- **Hardware-aware** -- benchmarks against real AMD GPU specs (MI300X, MI250X)
- **Fireworks AI integration** -- hosted inference on AMD MI300X via Fireworks API
- **One-click export** -- ONNX and TorchScript with automatic optimization flags
- **6-phase pipeline** -- architecture search, distillation, pruning, quantization, benchmark, Pareto selection

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/models` | POST | Upload a model |
| `/api/optimizations` | POST | Start optimization job |
| `/api/optimizations/{id}` | GET | Check job status |
| `/api/candidates` | GET | List candidate architectures |
| `/api/benchmarks` | GET | Query benchmark results |
| `/api/benchmarks/fireworks` | GET | Benchmark Fireworks AI on AMD MI300X |
| `/api/exports` | POST | Export optimized model |
| `/ws/{job_id}` | WS | Live progress stream |

## Demo video

The 56-second Remotion demo video is at `demo/forgeai-demo.mp4`. It covers the full pipeline from upload to export with Japanese minimalist motion design.

## AMD GPU Usage (Hackathon Track 3)

This project demonstrates AMD GPU resource usage through two channels:

1. **Local PyTorch + ROCm** -- Direct optimization on AMD MI300X hardware
2. **Fireworks AI API** -- Hosted inference on AMD Instinct MI300X GPUs

The Fireworks integration is visible in:
- `backend/core/fireworks_client.py` -- API client with latency/throughput metrics
- `backend/api/benchmarks.py` -- `/benchmarks/fireworks` endpoint
- Demo page 04 (Benchmark Charts) shows Fireworks vs local comparison

## License

MIT
