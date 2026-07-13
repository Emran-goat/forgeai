"use client";

import { useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Play, ArrowLeft, Loader2, Gauge, HardDrive, Target, Wand2, SlidersHorizontal } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { createOptimization } from "@/lib/api";
import { AISetupWizard } from "@/components/ai-setup-wizard";
import type { OptimizationConfig } from "@/lib/api";

const hardwareOptions = [
  { id: "mi300x", name: "MI300X", memory: "192 GB", tag: "AMD" },
  { id: "a100", name: "A100", memory: "80 GB", tag: "NVIDIA" },
  { id: "l4", name: "L4", memory: "24 GB", tag: "NVIDIA" },
  { id: "cpu", name: "CPU", memory: "Variable", tag: "Generic" },
];

interface Constraints {
  max_latency_ms: number;
  max_memory_mb: number;
  min_accuracy: number;
}

interface Hyperparams {
  n_trials: number;
  timeout_seconds: number;
}

function OptimizePageInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const modelId = searchParams.get("modelId") || "";

  const [mode, setMode] = useState<"manual" | "ai">("ai");
  const [selectedHardware, setSelectedHardware] = useState("mi300x");
  const [constraints, setConstraints] = useState<Constraints>({
    max_latency_ms: 50,
    max_memory_mb: 4096,
    min_accuracy: 95,
  });
  const [hyperparams, setHyperparams] = useState<Hyperparams>({
    n_trials: 50,
    timeout_seconds: 3600,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleStart = async () => {
    if (!modelId) {
      setError("No model selected. Please upload a model first.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const optimization = await createOptimization(modelId, selectedHardware, constraints, hyperparams);
      router.push(`/results?optimizationId=${optimization.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start optimization");
      setLoading(false);
    }
  };

  const handleAIConfigReady = (config: OptimizationConfig) => {
    setSelectedHardware(config.target_hardware.toLowerCase().replace(/\s+/g, ""));
    setConstraints({
      max_latency_ms: config.constraints.max_latency_ms,
      max_memory_mb: config.constraints.max_memory_gb * 1024,
      min_accuracy: config.constraints.min_accuracy_retention * 100,
    });
    setHyperparams({
      n_trials: config.parameters.n_trials,
      timeout_seconds: config.parameters.timeout,
    });
    setMode("manual");
  };

  return (
    <div className="min-h-full p-8 md:p-16 max-w-4xl mx-auto">
      <div className="space-y-2 mb-8">
        <h1 className="text-3xl font-light tracking-tight text-[#0f0f0f]">
          Configure
        </h1>
        <p className="text-sm text-[#1a1a2e]/50 font-light">
          Select your target hardware and set optimization constraints.
        </p>
      </div>

      <div className="flex items-center gap-1 p-0.5 bg-[#e8e4e1]/40 rounded-md w-fit mb-10">
        <button
          onClick={() => setMode("ai")}
          className={cn(
            "inline-flex items-center gap-1.5 px-4 py-2 text-xs tracking-wide rounded transition-all duration-200",
            mode === "ai"
              ? "bg-white text-[#0f0f0f] shadow-sm"
              : "text-[#1a1a2e]/40 hover:text-[#0f0f0f]"
          )}
        >
          <Wand2 className="w-3.5 h-3.5" strokeWidth={1.5} />
          AI Assistant
        </button>
        <button
          onClick={() => setMode("manual")}
          className={cn(
            "inline-flex items-center gap-1.5 px-4 py-2 text-xs tracking-wide rounded transition-all duration-200",
            mode === "manual"
              ? "bg-white text-[#0f0f0f] shadow-sm"
              : "text-[#1a1a2e]/40 hover:text-[#0f0f0f]"
          )}
        >
          <SlidersHorizontal className="w-3.5 h-3.5" strokeWidth={1.5} />
          Manual Setup
        </button>
      </div>

      {mode === "ai" ? (
        <AISetupWizard modelId={modelId} onConfigReady={handleAIConfigReady} />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          <div className="space-y-4">
            <label className="text-xs uppercase tracking-widest text-[#1a1a2e]/40 block">
              Target Hardware
            </label>
            <div className="grid grid-cols-2 gap-3">
              {hardwareOptions.map((hw) => (
                <button
                  key={hw.id}
                  onClick={() => setSelectedHardware(hw.id)}
                  className={cn(
                    "p-4 rounded-lg border text-left transition-all duration-200",
                    selectedHardware === hw.id
                      ? "border-[#0f0f0f]/20 bg-[#0f0f0f]/[0.02]"
                      : "border-[#e8e4e1] hover:border-[#1a1a2e]/15"
                  )}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-[#1a1a2e]/30 uppercase tracking-wider">{hw.tag}</span>
                    {selectedHardware === hw.id && (
                      <span className="w-1.5 h-1.5 rounded-full bg-[#c0392b]" />
                    )}
                  </div>
                  <div className="text-sm font-medium text-[#0f0f0f]">{hw.name}</div>
                  <div className="text-xs text-[#1a1a2e]/40 mt-1">{hw.memory}</div>
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-6">
            <label className="text-xs uppercase tracking-widest text-[#1a1a2e]/40 block">
              Constraints
            </label>

            <div className="space-y-6">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-2 text-sm text-[#0f0f0f]">
                    <Gauge className="w-3.5 h-3.5 text-[#1a1a2e]/30" strokeWidth={1.5} />
                    Max Latency
                  </label>
                  <span className="text-xs text-[#1a1a2e]/40 tabular-nums">
                    {constraints.max_latency_ms} ms
                  </span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="200"
                  value={constraints.max_latency_ms}
                  onChange={(e) =>
                    setConstraints({ ...constraints, max_latency_ms: Number(e.target.value) })
                  }
                  className="w-full h-px bg-[#e8e4e1] appearance-none cursor-pointer
                    [&::-webkit-slider-thumb]:appearance-none
                    [&::-webkit-slider-thumb]:w-3
                    [&::-webkit-slider-thumb]:h-3
                    [&::-webkit-slider-thumb]:rounded-full
                    [&::-webkit-slider-thumb]:bg-[#0f0f0f]
                    [&::-webkit-slider-thumb]:border-0
                    [&::-webkit-slider-thumb]:cursor-pointer
                    [&::-webkit-slider-thumb]:transition-transform
                    [&::-webkit-slider-thumb]:duration-200
                    [&::-webkit-slider-thumb]:hover:scale-150
                    [&::-moz-range-thumb]:w-3
                    [&::-moz-range-thumb]:h-3
                    [&::-moz-range-thumb]:rounded-full
                    [&::-moz-range-thumb]:bg-[#0f0f0f]
                    [&::-moz-range-thumb]:border-0
                    [&::-moz-range-thumb]:cursor-pointer"
                />
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-2 text-sm text-[#0f0f0f]">
                    <HardDrive className="w-3.5 h-3.5 text-[#1a1a2e]/30" strokeWidth={1.5} />
                    Max Memory
                  </label>
                  <span className="text-xs text-[#1a1a2e]/40 tabular-nums">
                    {constraints.max_memory_mb} MB
                  </span>
                </div>
                <input
                  type="range"
                  min="512"
                  max="16384"
                  step="512"
                  value={constraints.max_memory_mb}
                  onChange={(e) =>
                    setConstraints({ ...constraints, max_memory_mb: Number(e.target.value) })
                  }
                  className="w-full h-px bg-[#e8e4e1] appearance-none cursor-pointer
                    [&::-webkit-slider-thumb]:appearance-none
                    [&::-webkit-slider-thumb]:w-3
                    [&::-webkit-slider-thumb]:h-3
                    [&::-webkit-slider-thumb]:rounded-full
                    [&::-webkit-slider-thumb]:bg-[#0f0f0f]
                    [&::-webkit-slider-thumb]:border-0
                    [&::-webkit-slider-thumb]:cursor-pointer
                    [&::-webkit-slider-thumb]:transition-transform
                    [&::-webkit-slider-thumb]:duration-200
                    [&::-webkit-slider-thumb]:hover:scale-150
                    [&::-moz-range-thumb]:w-3
                    [&::-moz-range-thumb]:h-3
                    [&::-moz-range-thumb]:rounded-full
                    [&::-moz-range-thumb]:bg-[#0f0f0f]
                    [&::-moz-range-thumb]:border-0
                    [&::-moz-range-thumb]:cursor-pointer"
                />
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-2 text-sm text-[#0f0f0f]">
                    <Target className="w-3.5 h-3.5 text-[#1a1a2e]/30" strokeWidth={1.5} />
                    Min Accuracy
                  </label>
                  <span className="text-xs text-[#1a1a2e]/40 tabular-nums">
                    {constraints.min_accuracy}%
                  </span>
                </div>
                <input
                  type="range"
                  min="50"
                  max="100"
                  value={constraints.min_accuracy}
                  onChange={(e) =>
                    setConstraints({ ...constraints, min_accuracy: Number(e.target.value) })
                  }
                  className="w-full h-px bg-[#e8e4e1] appearance-none cursor-pointer
                    [&::-webkit-slider-thumb]:appearance-none
                    [&::-webkit-slider-thumb]:w-3
                    [&::-webkit-slider-thumb]:h-3
                    [&::-webkit-slider-thumb]:rounded-full
                    [&::-webkit-slider-thumb]:bg-[#0f0f0f]
                    [&::-webkit-slider-thumb]:border-0
                    [&::-webkit-slider-thumb]:cursor-pointer
                    [&::-webkit-slider-thumb]:transition-transform
                    [&::-webkit-slider-thumb]:duration-200
                    [&::-webkit-slider-thumb]:hover:scale-150
                    [&::-moz-range-thumb]:w-3
                    [&::-moz-range-thumb]:h-3
                    [&::-moz-range-thumb]:rounded-full
                    [&::-moz-range-thumb]:bg-[#0f0f0f]
                    [&::-moz-range-thumb]:border-0
                    [&::-moz-range-thumb]:cursor-pointer"
                />
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <label className="text-xs uppercase tracking-widest text-[#1a1a2e]/40 block">
              Hyperparameter Tuning
            </label>

            <div className="space-y-6">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-2 text-sm text-[#0f0f0f]">
                    <Target className="w-3.5 h-3.5 text-[#1a1a2e]/30" strokeWidth={1.5} />
                    Number of Trials
                  </label>
                  <span className="text-xs text-[#1a1a2e]/40 tabular-nums">
                    {hyperparams.n_trials}
                  </span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="200"
                  step="10"
                  value={hyperparams.n_trials}
                  onChange={(e) =>
                    setHyperparams({ ...hyperparams, n_trials: Number(e.target.value) })
                  }
                  className="w-full h-px bg-[#e8e4e1] appearance-none cursor-pointer
                    [&::-webkit-slider-thumb]:appearance-none
                    [&::-webkit-slider-thumb]:w-3
                    [&::-webkit-slider-thumb]:h-3
                    [&::-webkit-slider-thumb]:rounded-full
                    [&::-webkit-slider-thumb]:bg-[#0f0f0f]
                    [&::-webkit-slider-thumb]:border-0
                    [&::-webkit-slider-thumb]:cursor-pointer
                    [&::-webkit-slider-thumb]:transition-transform
                    [&::-webkit-slider-thumb]:duration-200
                    [&::-webkit-slider-thumb]:hover:scale-150
                    [&::-moz-range-thumb]:w-3
                    [&::-moz-range-thumb]:h-3
                    [&::-moz-range-thumb]:rounded-full
                    [&::-moz-range-thumb]:bg-[#0f0f0f]
                    [&::-moz-range-thumb]:border-0
                    [&::-moz-range-thumb]:cursor-pointer"
                />
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-2 text-sm text-[#0f0f0f]">
                    <Target className="w-3.5 h-3.5 text-[#1a1a2e]/30" strokeWidth={1.5} />
                    Timeout
                  </label>
                  <span className="text-xs text-[#1a1a2e]/40 tabular-nums">
                    {Math.floor(hyperparams.timeout_seconds / 60)}m
                  </span>
                </div>
                <input
                  type="range"
                  min="600"
                  max="7200"
                  step="300"
                  value={hyperparams.timeout_seconds}
                  onChange={(e) =>
                    setHyperparams({ ...hyperparams, timeout_seconds: Number(e.target.value) })
                  }
                  className="w-full h-px bg-[#e8e4e1] appearance-none cursor-pointer
                    [&::-webkit-slider-thumb]:appearance-none
                    [&::-webkit-slider-thumb]:w-3
                    [&::-webkit-slider-thumb]:h-3
                    [&::-webkit-slider-thumb]:rounded-full
                    [&::-webkit-slider-thumb]:bg-[#0f0f0f]
                    [&::-webkit-slider-thumb]:border-0
                    [&::-webkit-slider-thumb]:cursor-pointer
                    [&::-webkit-slider-thumb]:transition-transform
                    [&::-webkit-slider-thumb]:duration-200
                    [&::-webkit-slider-thumb]:hover:scale-150
                    [&::-moz-range-thumb]:w-3
                    [&::-moz-range-thumb]:h-3
                    [&::-moz-range-thumb]:rounded-full
                    [&::-moz-range-thumb]:bg-[#0f0f0f]
                    [&::-moz-range-thumb]:border-0
                    [&::-moz-range-thumb]:cursor-pointer"
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {error && (
        <p className="mt-6 text-xs text-[#c0392b]">{error}</p>
      )}

      <div className="mt-12 flex items-center justify-between">
        <Link
          href="/upload"
          className="inline-flex items-center gap-2 px-6 py-3 text-sm text-[#1a1a2e]/50 hover:text-[#0f0f0f] transition-colors duration-200"
        >
          <ArrowLeft className="w-4 h-4" strokeWidth={1.5} />
          Back
        </Link>
        {mode === "manual" && (
          <button
            onClick={handleStart}
            disabled={loading}
            className={cn(
              "inline-flex items-center gap-2 px-8 py-3 text-sm tracking-wide rounded transition-colors duration-200",
              !loading
                ? "text-[#fafaf9] bg-[#0f0f0f] hover:bg-[#1a1a2e]"
                : "text-[#1a1a2e]/30 bg-[#e8e4e1]/50 cursor-not-allowed"
            )}
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" strokeWidth={1.5} />
                Starting...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" strokeWidth={1.5} />
                Start Optimization
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
}

export default function OptimizePage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-full p-8 md:p-16 max-w-4xl mx-auto">
          <div className="h-8 w-48 bg-[#1a1a2e]/5 rounded animate-pulse mb-12" />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            <div className="h-64 bg-[#1a1a2e]/5 rounded animate-pulse" />
            <div className="h-64 bg-[#1a1a2e]/5 rounded animate-pulse" />
          </div>
        </div>
      }
    >
      <OptimizePageInner />
    </Suspense>
  );
}
