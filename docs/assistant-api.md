# ForgeAI Assistant API Contract

## Base URL
```
/api/v1/assistant
```

## Endpoints

### 1. POST /api/v1/assistant/setup
**Purpose:** Parse natural language into optimization config

**Request:**
```json
{
  "message": "I have a ResNet50 checkpoint, need it under 20ms latency on MI300X, can tolerate 3% accuracy drop, memory budget 4GB",
  "model_id": "optional-uuid-if-uploaded"
}
```

**Response:**
```json
{
  "config": {
    "model_type": "vision",
    "target_hardware": "MI300X",
    "constraints": {
      "max_latency_ms": 20,
      "max_memory_gb": 4,
      "min_accuracy_retention": 0.97
    },
    "recommended_phases": ["pruning", "quantization", "benchmark", "pareto"],
    "parameters": {
      "sparsity": 0.3,
      "quantization_format": "INT8",
      "n_trials": 20,
      "timeout": 300
    }
  },
  "explanation": "Based on your requirements, I recommend structured pruning at 30% sparsity followed by INT8 quantization. This should achieve ~20ms latency while staying within your 4GB memory budget.",
  "suggested_prompts": [
    "Run the optimization with these settings",
    "Make it more aggressive — push for 15ms",
    "Prioritize accuracy over speed"
  ]
}
```

---

### 2. POST /api/v1/assistant/chat
**Purpose:** Chat with AI about optimization (streaming)

**Request:**
```json
{
  "message": "Why did pruning help more than quantization?",
  "context": {
    "optimization_id": "uuid",
    "pipeline_state": "complete",
    "results": {
      "phases": [...],
      "candidates": [...],
      "pareto_front": [...]
    }
  }
}
```

**Response (SSE stream):**
```
data: {"type": "token", "content": "Pruning "}
data: {"type": "token", "content": "removed "}
data: {"type": "token", "content": "30% "}
...
data: {"type": "done", "usage": {"prompt_tokens": 1200, "completion_tokens": 450}}
```

**Preloaded prompts:**
- "Explain these results"
- "What would happen with stricter constraints?"
- "Recommend the best candidate"
- "Why is this the knee point on the Pareto frontier?"
- "What's the tradeoff between Candidate A and B?"

---

### 3. POST /api/v1/assistant/run
**Purpose:** Let AI decide and trigger optimization

**Request:**
```json
{
  "message": "Optimize my model for lowest latency on MI300X",
  "model_id": "uuid",
  "auto_config": true
}
```

**Response:**
```json
{
  "optimization_id": "uuid",
  "config_generated": {
    "phases": ["pruning", "quantization", "benchmark", "pareto"],
    "parameters": {...}
  },
  "explanation": "I'll run pruning (30% structured) → INT8 quantization → benchmark on MI300X → Pareto analysis. Estimated time: 2-3 minutes.",
  "websocket_url": "ws://localhost:8000/api/v1/ws/optimization/uuid"
}
```

---

### 4. POST /api/v1/assistant/visualize
**Purpose:** Generate charts from optimization results

**Request:**
```json
{
  "chart_type": "auto",
  "data": {
    "optimization_id": "uuid",
    "candidates": [...],
    "pareto_front": [...]
  },
  "options": {
    "show_knee_point": true,
    "highlight_candidate": "uuid",
    "overlay": null
  }
}
```

**Response:**
```json
{
  "chart": {
    "type": "plotly",
    "data": [...],
    "layout": {...}
  },
  "explanation": "This chart shows the latency-accuracy tradeoff across 12 candidates. The red dot is the knee point — best balance of speed and accuracy.",
  "suggested_next": [
    "Add memory usage as bubble size",
    "Show before/after comparison",
    "Overlay Pareto frontier"
  ]
}
```

---

### 5. POST /api/v1/assistant/export
**Purpose:** AI-assisted export

**Request:**
```json
{
  "message": "Export the best model to ONNX and give me a deployment guide",
  "optimization_id": "uuid",
  "format": "onnx"
}
```

**Response:**
```json
{
  "export_id": "uuid",
  "format": "onnx",
  "download_url": "/api/v1/exports/uuid/download",
  "guide": "# ONNX Deployment Guide\n\n## MI300X Inference\n...",
  "explanation": "Exported with opset=17, dynamic batch axes. For MI300X, use ONNX Runtime with ROCm EP..."
}
```

---

## System Prompts

### Setup System Prompt
```
You are ForgeAI's optimization advisor. Parse the user's natural language 
description into a structured optimization config.

Rules:
- Extract model type (vision, language, multimodal)
- Extract hardware target (MI300X, MI250X, CPU)
- Extract constraints (latency, memory, accuracy)
- Recommend optimization phases based on model type
- Suggest reasonable default parameters
- Always explain your reasoning
- Provide 2-3 follow-up prompts the user might want

Available phases: architecture_search, distillation, pruning, quantization, 
benchmark, pareto, hyperparameter
```

### Chat System Prompt
```
You are ForgeAI's optimization assistant. You have access to the user's 
optimization results, pipeline state, and hardware specifications.

Rules:
- Explain results in clear, non-technical language when possible
- Use specific numbers from the data (latency, params, accuracy)
- Suggest concrete next steps
- If asked about tradeoffs, quantify them
- Reference specific candidates by name/ID
- Be concise — 2-4 paragraphs max per response

Context will include: optimization results, candidate metrics, Pareto front, 
hardware specs, pipeline phases completed.
```

### Run System Prompt
```
You are ForgeAI's optimization planner. Given the user's goal, generate 
a complete optimization configuration.

Rules:
- Select phases based on model type and goals
- Set reasonable parameters (don't over-optimize)
- Explain each phase choice
- Estimate total runtime
- If constraints are aggressive, warn the user
- Always include benchmark and pareto phases for comparison
```

### Visualize System Prompt
```
You are ForgeAI's visualization expert. Generate Plotly chart specifications 
from optimization data.

Rules:
- Default to scatter plots for tradeoff data
- Use latency on X-axis, accuracy on Y-axis
- Size bubbles by memory usage if available
- Highlight knee point in red
- Label key candidates
- Provide clear axis labels and title
- Explain what the chart shows
- Suggest 2-3 alternative views
```

---

## Usage Examples

### cURL

```bash
# Setup: Parse natural language into config
curl -X POST http://localhost:8000/api/v1/assistant/setup \
  -H "Content-Type: application/json" \
  -d '{"message": "Optimize ResNet50 for MI300X, under 20ms latency"}'

# Chat: Ask about results
curl -X POST http://localhost:8000/api/v1/assistant/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Why is pruning better than quantization here?"}'

# Stream: Real-time chat
curl -X POST http://localhost:8000/api/v1/assistant/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain these results"}' \
  --no-buffer

# Run: Let AI decide and optimize
curl -X POST http://localhost:8000/api/v1/assistant/run \
  -H "Content-Type: application/json" \
  -d '{"message": "Optimize for lowest latency on MI300X"}'

# Visualize: Generate chart
curl -X POST http://localhost:8000/api/v1/assistant/visualize \
  -H "Content-Type: application/json" \
  -d '{"chart_type": "auto", "data": {"candidates": [...]}}'

# Export: AI-assisted export
curl -X POST http://localhost:8000/api/v1/assistant/export \
  -H "Content-Type: application/json" \
  -d '{"message": "Export to ONNX", "format": "onnx"}'
```

### Python

```python
import httpx

# Setup
resp = httpx.post("http://localhost:8000/api/v1/assistant/setup", json={
    "message": "Optimize ResNet50 for MI300X, under 20ms latency"
})
config = resp.json()["config"]

# Chat
resp = httpx.post("http://localhost:8000/api/v1/assistant/chat", json={
    "message": "Explain these results",
    "context": {"optimization_id": "uuid"}
})
print(resp.json()["response"])

# Stream chat
with httpx.stream("POST", "http://localhost:8000/api/v1/assistant/chat/stream",
                   json={"message": "Tell me more"}) as r:
    for line in r.iter_lines():
        if line.startswith("data: "):
            print(line[6:])
```

### Frontend (TypeScript)

```typescript
import { setupOptimization, chatWithAssistant, visualizeResults } from "@/lib/api";

// Setup
const { config, explanation } = await setupOptimization(
  "Optimize ResNet50 for MI300X, under 20ms latency"
);

// Stream chat
const stream = await chatWithAssistant("Explain these results", {
  optimization_id: "uuid"
});
const reader = stream.getReader();
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  if (value.type === "token") process.stdout.write(value.content!);
}

// Visualize
const { chart, explanation } = await visualizeResults({
  candidates: [{ latency_ms: 10, accuracy: 0.95 }]
});
```
