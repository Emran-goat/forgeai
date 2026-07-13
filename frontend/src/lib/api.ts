const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ApiOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
}

async function request<T>(endpoint: string, options: ApiOptions = {}): Promise<T> {
  const { method = "GET", body, headers = {} } = options;

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: "Unknown error" }));
    throw new Error(error.message || `API error: ${response.status}`);
  }

  return response.json();
}

export interface Model {
  id: string;
  name: string;
  framework: "pytorch" | "onnx" | "tensorflow";
  size_mb: number;
  uploaded_at: string;
  status: "uploaded" | "processing" | "ready";
}

export interface Optimization {
  id: string;
  model_id: string;
  hardware: string;
  constraints: {
    max_latency_ms: number;
    max_memory_mb: number;
    min_accuracy: number;
  };
  status: "pending" | "running" | "completed" | "failed";
  created_at: string;
  completed_at?: string;
}

export interface Candidate {
  id: string;
  optimization_id: string;
  name: string;
  latency_ms: number;
  memory_mb: number;
  accuracy: number;
  techniques: string[];
  pareto_rank: number;
  is_pareto_optimal: boolean;
}

export interface HyperparameterConfig {
  n_trials: number;
  timeout_seconds: number;
}

export interface TuningResult {
  best_params: Record<string, number>;
  best_value: number;
  n_trials_completed: number;
  convergence_trial: number;
}

export interface Benchmark {
  id: string;
  candidate_id: string;
  metric_name: string;
  original_value: number;
  optimized_value: number;
  improvement_percent: number;
}

export async function fetchModels(): Promise<Model[]> {
  return request<Model[]>("/api/models");
}

export async function uploadModel(file: File, framework: string): Promise<Model> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("framework", framework);

  const response = await fetch(`${API_BASE_URL}/api/models/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Upload failed");
  }

  return response.json();
}

export async function createOptimization(
  modelId: string,
  hardware: string,
  constraints: Optimization["constraints"],
  hyperparams?: HyperparameterConfig
): Promise<Optimization> {
  return request<Optimization>("/api/optimizations", {
    method: "POST",
    body: { model_id: modelId, hardware, constraints, hyperparams },
  });
}

export async function fetchOptimizations(): Promise<Optimization[]> {
  return request<Optimization[]>("/api/optimizations");
}

export async function getOptimization(id: string): Promise<Optimization> {
  return request<Optimization>(`/api/optimizations/${id}`);
}

export async function getCandidates(optimizationId: string): Promise<Candidate[]> {
  return request<Candidate[]>(`/api/optimizations/${optimizationId}/candidates`);
}

export async function getBenchmarks(candidateId: string): Promise<Benchmark[]> {
  return request<Benchmark[]>(`/api/candidates/${candidateId}/benchmarks`);
}

export async function requestExport(
  candidateId: string,
  format: "onnx" | "torchscript" | "tensorrt"
): Promise<{ download_url: string }> {
  return request(`/api/candidates/${candidateId}/export`, {
    method: "POST",
    body: { format },
  });
}
