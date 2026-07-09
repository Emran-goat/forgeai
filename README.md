# ForgeAI

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/imports-isort-1674b1.svg)](https://pycqa.github.io/isort/)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-9b59b6.svg)](https://mypy-lang.org/)
[![Tests](https://img.shields.io/badge/tests-pytest-brightgreen.svg)](https://docs.pytest.org/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg)](https://www.docker.com/)
[![ROCm](https://img.shields.io/badge/ROCm-6.0+-ED1C24.svg)](https://rocm.docs.amd.com/)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-Spaces-yellow.svg)](https://huggingface.co/spaces)

**The compiler for efficient AI models.**

ForgeAI automatically finds the fastest, most efficient version of any AI model for your target hardware. Upload a model, specify your constraints, and get an optimized export running on AMD MI300X GPUs.

[Paper](#) | [Demo](#demo-video) | [API Reference](#api) | [Contributing](CONTRIBUTING.md)

## Key Features

- **6-phase optimization pipeline** -- Architecture search, distillation, pruning, quantization, benchmarking, Pareto analysis
- **Multi-objective optimization** -- Latency, memory, and accuracy on the Pareto frontier
- **Hardware-aware** -- Benchmarks against real AMD GPU specs (MI300X, MI250X)
- **Live progress** -- WebSocket-streamed optimization phases to the UI
- **Fireworks AI integration** -- Hosted inference on AMD MI300X via Fireworks API
- **One-click export** -- ONNX and TorchScript with automatic optimization flags

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

## Installation

### Prerequisites

- Python 3.11+
- Node.js 18+
- AMD GPU with ROCm 6.0+ (optional, for local benchmarking)

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/Emran-goat/forgeai.git
cd forgeai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Start the server
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
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

### HuggingFace Spaces

1. Push to GitHub
2. Go to [huggingface.co/new-space](https://huggingface.co/new-space)
3. Select "Docker" as the SDK
4. Connect your GitHub repo
5. Set `FIREWORKS_API_KEY` in Space secrets
6. Deploy

## Usage

### Upload a Model

```python
import requests

# Upload a PyTorch checkpoint
files = {'file': open('model.pth', 'rb')}
response = requests.post('http://localhost:8000/api/models', files=files)
model_id = response.json()['id']
```

### Start Optimization

```python
# Create optimization job
data = {
    'model_id': model_id,
    'hardware': 'MI300X',
    'constraints': {
        'max_latency_ms': 50,
        'max_memory_mb': 1024,
        'min_accuracy': 0.95
    }
}
response = requests.post('http://localhost:8000/api/optimizations', json=data)
job_id = response.json()['id']
```

### Monitor Progress

```python
import websocket
import json

ws = websocket.create_connection(f'ws://localhost:8000/ws/{job_id}')
while True:
    message = json.loads(ws.recv())
    print(f"Phase: {message['phase']}, Progress: {message['progress']}%")
    if message.get('completed'):
        break
```

### Export Optimized Model

```python
# Export to ONNX
data = {
    'optimization_id': job_id,
    'format': 'onnx'
}
response = requests.post('http://localhost:8000/api/exports', json=data)
# Download the exported model
```

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/models` | POST | Upload a model |
| `/api/models/{id}` | GET | Get model info |
| `/api/optimizations` | POST | Start optimization job |
| `/api/optimizations/{id}` | GET | Check job status |
| `/api/candidates` | GET | List candidate architectures |
| `/api/benchmarks` | GET | Query benchmark results |
| `/api/benchmarks/fireworks` | GET | Benchmark Fireworks AI on AMD MI300X |
| `/api/exports` | POST | Export optimized model |
| `/api/exports/{id}` | GET | Get export info |
| `/api/hardware` | GET | Get hardware specs |
| `/ws/{job_id}` | WS | Live progress stream |
| `/health` | GET | Health check |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI 0.110+, Pydantic v2, WebSocket |
| ML | PyTorch 2.2+, ROCm 6.0+, timm |
| Database | SQLite + aiosqlite |
| Frontend | Next.js 14, Tailwind CSS, shadcn/ui, Recharts |
| Video | Remotion (1920x1080, 30fps) |
| Cloud Inference | Fireworks AI (AMD Instinct MI300X backend) |
| Target GPU | AMD MI300X (192GB HBM3) |

## Demo Video

The 56-second Remotion demo video is at `demo/forgeai-demo.mp4`. It covers the full pipeline from upload to export with Japanese minimalist motion design.

## AMD GPU Usage (Hackathon Track 3)

This project demonstrates AMD GPU resource usage through two channels:

1. **Local PyTorch + ROCm** -- Direct optimization on AMD MI300X hardware
2. **Fireworks AI API** -- Hosted inference on AMD Instinct MI300X GPUs

The Fireworks integration is visible in:
- `backend/core/fireworks_client.py` -- API client with latency/throughput metrics
- `backend/api/benchmarks.py` -- `/benchmarks/fireworks` endpoint
- Demo page 04 (Benchmark Charts) shows Fireworks vs local comparison

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to ForgeAI.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Citation

If you find ForgeAI useful, please cite:

```bibtex
@software{forgeai2024,
  title={ForgeAI: Hardware-Aware AI Model Optimization Platform},
  author={ForgeAI Team},
  year={2024},
  url={https://github.com/Emran-goat/forgeai}
}
```

## Acknowledgments

- Built for the AMD Developer Hackathon ACT II, Track 3 (Unicorn)
- Powered by [Fireworks AI](https://fireworks.ai/) for hosted inference on AMD MI300X
- UI inspired by Japanese minimalist design (wabi-sabi aesthetic)
