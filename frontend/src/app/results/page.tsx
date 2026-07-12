"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import {
  ArrowUpRight,
  Inbox,
  Check,
} from "lucide-react";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { cn } from "@/lib/utils";
import {
  fetchOptimizations,
  getCandidates,
  type Optimization,
  type Candidate,
} from "@/lib/api";

interface OptimizationRow extends Optimization {
  candidates?: Candidate[];
  bestLatency?: number;
  bestAccuracy?: number;
  candidateCount?: number;
  completedPhases?: number;
  bestHyperparams?: Record<string, number>;
}

const PHASES = [
  "Architecture Search",
  "Distillation",
  "Pruning",
  "Quantization",
  "Benchmark",
  "Pareto Analysis",
  "Hyperparameter Tuning",
];

const MOCK_OPTIMIZATIONS: OptimizationRow[] = [
  {
    id: "mock-1",
    model_id: "DINOv2-Base",
    hardware: "AMD MI300X",
    status: "completed",
    created_at: new Date(Date.now() - 3600000).toISOString(),
    constraints: { max_latency_ms: 50, max_memory_mb: 4096, min_accuracy: 90 },
    completedPhases: 7,
    bestHyperparams: { learning_rate: 0.0003, batch_size: 32, weight_decay: 0.01, warmup_steps: 5 },
    candidateCount: 5,
    bestLatency: 18.3,
    bestAccuracy: 96.2,
    candidates: [
      { id: "m1-c1", optimization_id: "mock-1", name: "INT8 Quantized", latency_ms: 18.3, accuracy: 96.2, memory_mb: 1536, techniques: ["quantization"], is_pareto_optimal: true, pareto_rank: 1 },
      { id: "m1-c2", optimization_id: "mock-1", name: "Pruned 30%", latency_ms: 24.7, accuracy: 94.8, memory_mb: 1024, techniques: ["pruning"], is_pareto_optimal: true, pareto_rank: 1 },
      { id: "m1-c3", optimization_id: "mock-1", name: "FP16 Mixed", latency_ms: 22.1, accuracy: 96.0, memory_mb: 2048, techniques: ["quantization"], is_pareto_optimal: false, pareto_rank: 2 },
      { id: "m1-c4", optimization_id: "mock-1", name: "Pruned 50%", latency_ms: 15.1, accuracy: 92.4, memory_mb: 768, techniques: ["pruning", "quantization"], is_pareto_optimal: true, pareto_rank: 1 },
      { id: "m1-c5", optimization_id: "mock-1", name: "Baseline FP32", latency_ms: 38.6, accuracy: 97.1, memory_mb: 3072, techniques: [], is_pareto_optimal: false, pareto_rank: 3 },
    ],
  },
  {
    id: "mock-2",
    model_id: "ViT-B/16",
    hardware: "AMD MI300X",
    status: "completed",
    created_at: new Date(Date.now() - 7200000).toISOString(),
    constraints: { max_latency_ms: 40, max_memory_mb: 3072, min_accuracy: 88 },
    completedPhases: 6,
    bestHyperparams: { learning_rate: 0.0005, batch_size: 16, weight_decay: 0.005 },
    candidateCount: 4,
    bestLatency: 12.9,
    bestAccuracy: 95.7,
    candidates: [
      { id: "m2-c1", optimization_id: "mock-2", name: "INT8 Quantized", latency_ms: 12.9, accuracy: 95.7, memory_mb: 1280, techniques: ["quantization"], is_pareto_optimal: true, pareto_rank: 1 },
      { id: "m2-c2", optimization_id: "mock-2", name: "INT4 Quantized", latency_ms: 9.4, accuracy: 91.2, memory_mb: 768, techniques: ["quantization"], is_pareto_optimal: true, pareto_rank: 1 },
      { id: "m2-c3", optimization_id: "mock-2", name: "Pruned 40%", latency_ms: 16.8, accuracy: 94.1, memory_mb: 1024, techniques: ["pruning"], is_pareto_optimal: false, pareto_rank: 2 },
      { id: "m2-c4", optimization_id: "mock-2", name: "Baseline FP32", latency_ms: 28.5, accuracy: 96.3, memory_mb: 2560, techniques: [], is_pareto_optimal: false, pareto_rank: 3 },
    ],
  },
  {
    id: "mock-3",
    model_id: "GPT-2 Small",
    hardware: "AMD MI250X",
    status: "completed",
    created_at: new Date(Date.now() - 10800000).toISOString(),
    constraints: { max_latency_ms: 80, max_memory_mb: 4096, min_accuracy: 85 },
    completedPhases: 7,
    bestHyperparams: { learning_rate: 0.001, batch_size: 64, weight_decay: 0.02, warmup_steps: 10 },
    candidateCount: 6,
    bestLatency: 32.4,
    bestAccuracy: 89.6,
    candidates: [
      { id: "m3-c1", optimization_id: "mock-3", name: "INT8 Quantized", latency_ms: 32.4, accuracy: 89.6, memory_mb: 1536, techniques: ["quantization"], is_pareto_optimal: true, pareto_rank: 1 },
      { id: "m3-c2", optimization_id: "mock-3", name: "Pruned 25%", latency_ms: 41.7, accuracy: 91.3, memory_mb: 2048, techniques: ["pruning"], is_pareto_optimal: false, pareto_rank: 2 },
      { id: "m3-c3", optimization_id: "mock-3", name: "FP16 Mixed", latency_ms: 36.2, accuracy: 90.1, memory_mb: 2560, techniques: ["quantization"], is_pareto_optimal: false, pareto_rank: 2 },
      { id: "m3-c4", optimization_id: "mock-3", name: "INT4 Quantized", latency_ms: 22.8, accuracy: 85.4, memory_mb: 1024, techniques: ["quantization"], is_pareto_optimal: true, pareto_rank: 1 },
      { id: "m3-c5", optimization_id: "mock-3", name: "Pruned 50%", latency_ms: 27.9, accuracy: 86.2, memory_mb: 1280, techniques: ["pruning", "quantization"], is_pareto_optimal: false, pareto_rank: 3 },
      { id: "m3-c6", optimization_id: "mock-3", name: "Baseline FP32", latency_ms: 62.1, accuracy: 92.8, memory_mb: 4096, techniques: [], is_pareto_optimal: false, pareto_rank: 4 },
    ],
  },
];

function PhaseProgress({ completedPhases = 0 }: { completedPhases?: number }) {
  return (
    <div className="flex items-center gap-1.5">
      {PHASES.map((phase, i) => {
        const isCompleted = i < completedPhases;
        const isCurrent = i === completedPhases - 1;
        return (
          <div key={phase} className="group relative">
            <div
              className={cn(
                "w-2 h-2 rounded-full transition-colors duration-200",
                isCompleted
                  ? isCurrent
                    ? "bg-[#c0392b]"
                    : "bg-[#0f0f0f]/40"
                  : "bg-[#e8e4e1]"
              )}
            />
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-[#0f0f0f] text-white text-[10px] rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
              {phase}
              {isCompleted && <Check className="inline w-2.5 h-2.5 ml-1" />}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function BestHyperparamsCard({ params }: { params: Record<string, number> }) {
  const labels: Record<string, string> = {
    learning_rate: "Learning Rate",
    batch_size: "Batch Size",
    weight_decay: "Weight Decay",
    warmup_steps: "Warmup Steps",
    dropout: "Dropout",
    momentum: "Momentum",
  };

  return (
    <div className="border border-[#1a1a2e]/6 rounded-md p-4 bg-white">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-[10px] uppercase tracking-[0.15em] text-[#1a1a2e]/30 font-medium">
          Best Hyperparameters
        </span>
      </div>
      <div className="grid grid-cols-2 gap-x-6 gap-y-2">
        {Object.entries(params).map(([key, value]) => (
          <div key={key} className="flex items-center justify-between">
            <span className="text-xs text-[#1a1a2e]/40">
              {labels[key] ?? key.replace(/_/g, " ")}
            </span>
            <span className="text-xs font-mono text-[#0f0f0f] tabular-nums">
              {typeof value === "number" ? (value < 1 ? value.toExponential(1) : value) : value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function SkeletonRow() {
  return (
    <tr className="border-t border-[#1a1a2e]/10">
      <td className="px-5 py-4">
        <div className="h-4 w-28 bg-[#1a1a2e]/5 rounded animate-pulse" />
      </td>
      <td className="px-5 py-4">
        <div className="h-4 w-24 bg-[#1a1a2e]/5 rounded animate-pulse" />
      </td>
      <td className="px-5 py-4">
        <div className="h-5 w-16 bg-[#1a1a2e]/5 rounded-full animate-pulse" />
      </td>
      <td className="px-5 py-4">
        <div className="h-4 w-8 bg-[#1a1a2e]/5 rounded animate-pulse" />
      </td>
      <td className="px-5 py-4">
        <div className="h-4 w-20 bg-[#1a1a2e]/5 rounded animate-pulse" />
      </td>
      <td className="px-5 py-4">
        <div className="h-4 w-16 bg-[#1a1a2e]/5 rounded animate-pulse" />
      </td>
    </tr>
  );
}

function CustomTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-white border border-[#1a1a2e]/10 px-4 py-3 rounded-md shadow-none">
      <p className="text-xs font-medium text-[#0f0f0f] mb-1">{d.name}</p>
      <p className="text-xs text-[#1a1a2e]/60">
        {d.latency_ms.toFixed(1)} ms · {d.accuracy.toFixed(1)}%
      </p>
      <p className="text-xs text-[#1a1a2e]/60">
        {d.memory_mb.toFixed(0)} MB
      </p>
    </div>
  );
}

export default function ResultsPage() {
  const [optimizations, setOptimizations] = useState<OptimizationRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [chartData, setChartData] = useState<Candidate[]>([]);
  const [showMock, setShowMock] = useState(false);
  const hasAnimated = useRef(false);

  useEffect(() => {
    fetchOptimizations()
      .then(async (opts) => {
        const enriched = await Promise.all(
          opts.map(async (opt) => {
            try {
              const candidates = await getCandidates(opt.id);
              const completed = candidates;
              return {
                ...opt,
                candidates,
                completedPhases: opt.status === "completed" ? 7 : opt.status === "running" ? 3 : 0,
                bestLatency: completed.length
                  ? Math.min(...completed.map((c) => c.latency_ms))
                  : undefined,
                bestAccuracy: completed.length
                  ? Math.max(...completed.map((c) => c.accuracy))
                  : undefined,
                candidateCount: candidates.length,
              };
            } catch {
              return { ...opt, candidates: [], candidateCount: 0 };
            }
          })
        );
        setOptimizations(enriched);

        const allCandidates = enriched.flatMap((o) => o.candidates ?? []);
        setChartData(allCandidates);

        if (enriched.length === 0) {
          setShowMock(true);
          setOptimizations(MOCK_OPTIMIZATIONS);
          setChartData(MOCK_OPTIMIZATIONS.flatMap((o) => o.candidates ?? []));
        }
      })
      .catch(() => {
        setShowMock(true);
        setOptimizations(MOCK_OPTIMIZATIONS);
        setChartData(MOCK_OPTIMIZATIONS.flatMap((o) => o.candidates ?? []));
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!loading && optimizations.length > 0 && !hasAnimated.current) {
      hasAnimated.current = true;
    }
  }, [loading, optimizations]);

  const handleExpand = async (opt: OptimizationRow) => {
    if (expandedId === opt.id) {
      setExpandedId(null);
      return;
    }
    setExpandedId(opt.id);
    if (!opt.candidates?.length) {
      try {
        const candidates = await getCandidates(opt.id);
        setOptimizations((prev) =>
          prev.map((o) =>
            o.id === opt.id
              ? {
                  ...o,
                  candidates,
                  candidateCount: candidates.length,
                  bestLatency: candidates.length
                    ? Math.min(...candidates.map((c) => c.latency_ms))
                    : undefined,
                  bestAccuracy: candidates.length
                    ? Math.max(...candidates.map((c) => c.accuracy))
                    : undefined,
                }
              : o
          )
        );
        setChartData((prev) => [...prev, ...candidates]);
      } catch {}
    }
  };

  const formatDate = (d: string) =>
    new Date(d).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });

  return (
    <div className="min-h-full">
      <div className="max-w-6xl mx-auto px-6 py-20">
        <header className="mb-16">
          <h1 className="text-3xl font-light tracking-tight text-[#0f0f0f] mb-3">
            Results
          </h1>
          <p className="text-[#1a1a2e]/50 text-sm tracking-wide">
            {showMock ? "Demo results with sample optimizations" : "Optimization runs and Pareto analysis"}
          </p>
        </header>

        {loading ? (
          <div className="border border-[#1a1a2e]/8 rounded-md overflow-hidden bg-white">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#1a1a2e]/8">
                    {["Model", "Hardware", "Status", "Phases", "Best Latency", "Best Accuracy"].map(
                      (h) => (
                        <th
                          key={h}
                          className="px-5 py-3 text-left text-xs font-medium text-[#1a1a2e]/40 uppercase tracking-wider"
                        >
                          {h}
                        </th>
                      )
                    )}
                  </tr>
                </thead>
                <tbody>
                  {Array.from({ length: 4 }).map((_, i) => (
                  <SkeletonRow key={i} />
                ))}
              </tbody>
            </table>
          </div>
        ) : optimizations.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-32 text-center">
            <Inbox className="w-12 h-12 text-[#1a1a2e]/15 mb-6 icon-breathe" />
            <p className="text-[#1a1a2e]/40 text-sm">No optimizations yet</p>
            <Link
              href="/optimize"
              className="mt-6 text-xs text-[#c0392b] hover:text-[#c0392b]/80 transition-colors duration-200 tracking-wide"
            >
              Start an optimization
            </Link>
          </div>
        ) : (
          <>
            <div className="border border-[#1a1a2e]/8 rounded-md overflow-hidden bg-white mb-16">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-[#1a1a2e]/8">
                    {["Model", "Hardware", "Status", "Phases", "Best Latency", "Best Accuracy"].map(
                      (h) => (
                        <th
                          key={h}
                          className="px-5 py-3 text-left text-xs font-medium text-[#1a1a2e]/40 uppercase tracking-wider"
                        >
                          {h}
                        </th>
                      )
                    )}
                  </tr>
                </thead>
                <tbody>
                  {optimizations.map((opt, i) => (
                    <OptimizationRowComponent
                      key={opt.id}
                      opt={opt}
                      expanded={expandedId === opt.id}
                      onExpand={() => handleExpand(opt)}
                      formatDate={formatDate}
                      rowIndex={i}
                    />
                  ))}
                </tbody>
              </table>
            </div>

            {chartData.length > 0 && (
              <section>
                <h2 className="text-lg font-light text-[#0f0f0f] mb-2">
                  Pareto Frontier
                </h2>
                <p className="text-xs text-[#1a1a2e]/40 mb-8 tracking-wide">
                  Latency vs accuracy · size = memory
                </p>
                <div className="border border-[#1a1a2e]/8 rounded-md bg-white p-6">
                  <ResponsiveContainer width="100%" height={400}>
                    <ScatterChart margin={{ top: 10, right: 20, bottom: 10, left: 10 }}>
                      <CartesianGrid
                        strokeDasharray="3 3"
                        stroke="#1a1a2e"
                        strokeOpacity={0.06}
                        vertical={false}
                      />
                      <XAxis
                        type="number"
                        dataKey="latency_ms"
                        name="Latency"
                        unit=" ms"
                        tick={{ fill: "#1a1a2e", opacity: 0.4, fontSize: 11 }}
                        axisLine={{ stroke: "#1a1a2e", strokeOpacity: 0.08 }}
                        tickLine={false}
                      />
                      <YAxis
                        type="number"
                        dataKey="accuracy"
                        name="Accuracy"
                        unit="%"
                        tick={{ fill: "#1a1a2e", opacity: 0.4, fontSize: 11 }}
                        axisLine={{ stroke: "#1a1a2e", strokeOpacity: 0.08 }}
                        tickLine={false}
                      />
                      <Tooltip content={<CustomTooltip />} cursor={false} />
                      <Scatter data={chartData} shape={(props: any) => {
                        const { cx, cy, payload } = props;
                        const r = Math.max(4, Math.min(10, payload.memory_mb / 200));
                        return (
                          <circle
                            cx={cx}
                            cy={cy}
                            r={r}
                            fill={payload.is_pareto_optimal ? "#c0392b" : "#1a1a2e"}
                            fillOpacity={payload.is_pareto_optimal ? 1 : 0.25}
                            className="animate-[dotScaleIn_0.4s_cubic-bezier(0.16,1,0.3,1)_both]"
                            style={{
                              transformOrigin: `${cx}px ${cy}px`,
                            }}
                          />
                        );
                      }} />
                    </ScatterChart>
                  </ResponsiveContainer>
                </div>
              </section>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function OptimizationRowComponent({
  opt,
  expanded,
  onExpand,
  formatDate,
  rowIndex,
}: {
  opt: OptimizationRow;
  expanded: boolean;
  onExpand: () => void;
  formatDate: (d: string) => string;
  rowIndex: number;
}) {
  const statusColors: Record<string, string> = {
    completed: "bg-[#1a1a2e]/8 text-[#1a1a2e]/70",
    running: "bg-[#c0392b]/8 text-[#c0392b]",
    pending: "bg-[#e8e4e1] text-[#1a1a2e]/50",
    failed: "bg-[#c0392b]/10 text-[#c0392b]/70",
  };

  return (
    <>
      <tr
        className={cn(
          "border-t border-[#1a1a2e]/8 cursor-pointer transition-colors duration-200 hover:bg-[#e8e4e1]/30 row-animate",
          expanded && "bg-[#e8e4e1]/20"
        )}
        style={{ animationDelay: `${rowIndex * 80}ms` }}
        onClick={onExpand}
      >
        <td className="px-5 py-4">
          <span className="text-sm font-medium text-[#0f0f0f]">
            {opt.model_id}
          </span>
        </td>
        <td className="px-5 py-4">
          <span className="text-sm text-[#1a1a2e]/50">{opt.hardware}</span>
        </td>
        <td className="px-5 py-4">
          <span
            className={cn(
              "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
              statusColors[opt.status] ?? statusColors.pending
            )}
          >
            {opt.status}
          </span>
        </td>
        <td className="px-5 py-4">
          <PhaseProgress completedPhases={opt.completedPhases} />
        </td>
        <td className="px-5 py-4">
          <span className="text-sm font-mono text-[#0f0f0f]">
            {opt.bestLatency != null ? `${opt.bestLatency.toFixed(1)} ms` : "—"}
          </span>
        </td>
        <td className="px-5 py-4">
          <span className="text-sm font-mono text-[#0f0f0f]">
            {opt.bestAccuracy != null ? `${opt.bestAccuracy.toFixed(1)}%` : "—"}
          </span>
        </td>
      </tr>

      {expanded && opt.candidates && opt.candidates.length > 0 && (
        <tr>
          <td colSpan={6} className="px-5 pb-4">
            <div className="ml-4 mt-1 border border-[#1a1a2e]/6 rounded-md overflow-hidden expand-enter expand-enter-active">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-[#e8e4e1]/30">
                    {["Candidate", "Latency", "Accuracy", "Memory", "Techniques", "Pareto"].map(
                      (h) => (
                        <th
                          key={h}
                          className="px-4 py-2 text-left font-medium text-[#1a1a2e]/40 uppercase tracking-wider"
                        >
                          {h}
                        </th>
                      )
                    )}
                  </tr>
                </thead>
                <tbody>
                  {opt.candidates
                    .slice()
                    .sort((a, b) => a.pareto_rank - b.pareto_rank)
                    .map((c, ci) => (
                      <tr
                        key={c.id}
                        className="border-t border-[#1a1a2e]/6 row-animate"
                        style={{ animationDelay: `${ci * 60}ms` }}
                      >
                        <td className="px-4 py-2.5 font-medium text-[#0f0f0f]">
                          {c.name}
                        </td>
                        <td className="px-4 py-2.5 font-mono text-[#1a1a2e]/60">
                          {c.latency_ms.toFixed(1)} ms
                        </td>
                        <td className="px-4 py-2.5 font-mono text-[#1a1a2e]/60">
                          {c.accuracy.toFixed(1)}%
                        </td>
                        <td className="px-4 py-2.5 font-mono text-[#1a1a2e]/60">
                          {c.memory_mb.toFixed(0)} MB
                        </td>
                        <td className="px-4 py-2.5 text-[#1a1a2e]/40">
                          {c.techniques.join(", ")}
                        </td>
                        <td className="px-4 py-2.5">
                          {c.is_pareto_optimal ? (
                            <span className="text-[#c0392b] text-xs font-medium">
                              optimal
                            </span>
                          ) : (
                            <span className="text-[#1a1a2e]/25">
                              rank {c.pareto_rank}
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
            {opt.bestHyperparams && Object.keys(opt.bestHyperparams).length > 0 && (
              <div className="mt-3">
                <BestHyperparamsCard params={opt.bestHyperparams} />
              </div>
            )}
            <div className="mt-3 flex justify-end">
              <Link
                href={`/export?optimization=${opt.id}`}
                className="inline-flex items-center gap-1.5 text-xs text-[#c0392b] hover:text-[#c0392b]/80 transition-colors duration-200 tracking-wide"
              >
                Export best candidate
                <ArrowUpRight className="w-3 h-3" />
              </Link>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
