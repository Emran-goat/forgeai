# ForgeAI — Architecture Decision Records

## ADR-001: Monolith with Clean Module Boundaries

**Status:** Accepted  
**Date:** 2026-07-09

### Context
ForgeAI needs to orchestrate architecture search, distillation, pruning, quantization, and benchmarking. The hackathon timeline is 3-5 days.

### Decision
Build as a monolithic FastAPI application with clear internal module boundaries (ports/adapters pattern).

### Alternatives Considered
- **Microservices:** Rejected — too much overhead for hackathon timeline, network complexity, deployment complexity
- **Lambda/Serverless:** Rejected — GPU workloads don't fit serverless well

### Consequences
- Positive: Simple deployment, no network latency, easy debugging
- Negative: Can't scale components independently (acceptable for hackathon)
- Mitigation: Clean module boundaries allow future extraction

---

## ADR-002: PyTorch + ROCm for GPU Operations

**Status:** Accepted  
**Date:** 2026-07-09

### Context
ForgeAI needs to run model training, inference, and benchmarking on AMD MI300X GPUs.

### Decision
Use PyTorch 2.2+ with ROCm backend for all GPU operations.

### Alternatives Considered
- **JAX:** Rejected — smaller ROCm ecosystem
- **TensorFlow:** Rejected — less AMD support than PyTorch

### Consequences
- Positive: Direct MI300X support, native torch API, full ecosystem
- Negative: Some libraries may need ROCm-specific builds
- Mitigation: Docker with ROCm base image ensures consistent environment

---

## ADR-003: SQLite for Benchmark Results

**Status:** Accepted  
**Date:** 2026-07-09

### Context
Need to store benchmark results, optimization history, and candidate metrics.

### Decision
Use SQLite with aiosqlite for async access.

### Alternatives Considered
- **PostgreSQL:** Rejected — requires separate server, overkill for hackathon
- **Redis:** Rejected — not suitable for structured query data

### Consequences
- Positive: Zero setup, single file, easy to export/share
- Negative: Not suitable for concurrent high-write production
- Mitigation: Can migrate to PostgreSQL later

---

## ADR-004: Next.js + shadcn/ui for Frontend

**Status:** Accepted  
**Date:** 2026-07-09

### Context
Need a polished UI for the demo that shows upload, optimization progress, leaderboard, and Pareto charts.

### Decision
Use Next.js 14 (App Router) with Tailwind CSS and shadcn/ui components.

### Alternatives Considered
- **Streamlit:** Rejected — too limited for custom UI, poor demo quality
- **React + Vite:** Rejected — Next.js gives better DX and deployment options

### Consequences
- Positive: Fast development, polished components, deployable to Vercel
- Negative: More setup than Streamlit
- Mitigation: shadcn/ui provides pre-built components

---

## ADR-005: WebSocket for Live Progress

**Status:** Accepted  
**Date:** 2026-07-09

### Context
Optimization runs take minutes to hours. Users need real-time feedback on candidate evaluations.

### Decision
Use FastAPI WebSocket for streaming optimization progress to the UI.

### Alternatives Considered
- **Server-Sent Events (SSE):** Rejected — unidirectional, can't send commands
- **Polling:** Rejected — wasteful, higher latency

### Consequences
- Positive: Real-time updates, key demo feature, bidirectional
- Negative: More complex connection management
- Mitigation: FastAPI has native WebSocket support

---

## ADR-006: REST API Design

**Status:** Accepted  
**Date:** 2026-07-09

### Context
Need API for model upload, optimization management, benchmark retrieval, and export.

### Decision
REST API with OpenAPI auto-documentation. WebSocket for streaming.

### Alternatives Considered
- **GraphQL:** Rejected — unnecessary complexity for hackathon, REST is simpler
- **gRPC:** Rejected — harder to debug, less browser support

### Consequences
- Positive: Standard, well-understood, auto-docs from FastAPI
- Negative: Fixed endpoint structure
- Mitigation: API versioning (v1) allows future evolution

---

## ADR-007: Japanese Minimalist Frontend Aesthetic

**Status:** Accepted  
**Date:** 2026-07-09

### Context
The frontend needs a distinctive, polished design for the hackathon demo that stands out from generic AI tool UIs.

### Decision
Adopt a minimalistic modern Japanese (和風) aesthetic with wabi-sabi principles.

### Design Tokens
- **Palette:** deep indigo (#1a1a2e), warm charcoal (#16213e), stone (#e8e4e1), ink black (#0f0f0f), soft white (#fafaf9), vermilion accent (#c0392b)
- **Typography:** Inter font, light weights (300/400), generous tracking
- **Spacing:** Ma (間) — whitespace as design element, generous padding
- **Borders:** 1px, no shadows, subtle opacity transitions
- **Animation:** 200ms ease transitions, fade-in keyframes

### Consequences
- Positive: Distinctive, premium feel; memorable demo; stands out from competitors
- Negative: Hardcoded color values in some components (acceptable for hackathon)
- Mitigation: CSS variables in globals.css allow future theming
