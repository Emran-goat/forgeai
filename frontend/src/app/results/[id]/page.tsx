"use client";

import Link from "next/link";
import { ArrowLeft, Download, ExternalLink } from "lucide-react";

const mockCandidates = [
  {
    id: "c1",
    name: "INT8 Quantized",
    latency_ms: 23.4,
    memory_mb: 1024,
    accuracy: 94.8,
    techniques: ["INT8 Quantization", "Layer Fusion"],
    pareto_rank: 1,
    is_pareto_optimal: true,
  },
  {
    id: "c2",
    name: "FP16 Mixed",
    latency_ms: 31.2,
    memory_mb: 1536,
    accuracy: 95.2,
    techniques: ["FP16 Mixed Precision"],
    pareto_rank: 1,
    is_pareto_optimal: true,
  },
  {
    id: "c3",
    name: "Pruned 30%",
    latency_ms: 28.7,
    memory_mb: 896,
    accuracy: 93.1,
    techniques: ["Structured Pruning", "INT8 Quantization"],
    pareto_rank: 1,
    is_pareto_optimal: true,
  },
  {
    id: "c4",
    name: "Baseline FP32",
    latency_ms: 45.0,
    memory_mb: 2048,
    accuracy: 96.5,
    techniques: [],
    pareto_rank: 2,
    is_pareto_optimal: false,
  },
];

export default function ParetoPage({ params }: { params: { id: string } }) {
  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex items-center gap-4 mb-8">
        <Link
          href="/results"
          className="p-2 rounded-lg hover:bg-accent/10 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-3xl font-bold">Pareto Frontier</h1>
          <p className="text-muted-foreground">
            Optimization {params.id} - Latency vs Accuracy
          </p>
        </div>
      </div>

      {/* Chart Placeholder */}
      <div className="border border-border rounded-xl p-8 mb-8 bg-card">
        <div className="h-96 flex items-center justify-center border-2 border-dashed border-border rounded-lg">
          <div className="text-center">
            <div className="text-4xl mb-4">📊</div>
            <p className="text-muted-foreground">
              Pareto frontier chart will render here
            </p>
            <p className="text-sm text-muted-foreground/70 mt-2">
              Using Recharts to visualize latency vs accuracy trade-offs
            </p>
          </div>
        </div>
      </div>

      {/* Candidates List */}
      <h2 className="text-xl font-semibold mb-4">Candidates</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {mockCandidates.map((candidate) => (
          <div
            key={candidate.id}
            className={`p-4 rounded-xl border transition-all ${
              candidate.is_pareto_optimal
                ? "border-forgeai-success/50 bg-forgeai-success/5"
                : "border-border"
            }`}
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="font-medium">{candidate.name}</h3>
                {candidate.is_pareto_optimal && (
                  <span className="text-xs text-forgeai-success">Pareto Optimal</span>
                )}
              </div>
              <button className="p-2 rounded-lg hover:bg-accent/10 transition-colors">
                <Download className="w-4 h-4" />
              </button>
            </div>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <div className="text-muted-foreground">Latency</div>
                <div className="font-mono">{candidate.latency_ms} ms</div>
              </div>
              <div>
                <div className="text-muted-foreground">Memory</div>
                <div className="font-mono">{candidate.memory_mb} MB</div>
              </div>
              <div>
                <div className="text-muted-foreground">Accuracy</div>
                <div className="font-mono">{candidate.accuracy}%</div>
              </div>
            </div>
            {candidate.techniques.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {candidate.techniques.map((tech) => (
                  <span
                    key={tech}
                    className="px-2 py-1 rounded bg-muted text-xs text-muted-foreground"
                  >
                    {tech}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
