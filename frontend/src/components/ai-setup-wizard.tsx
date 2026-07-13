"use client";

import { useState } from "react";
import {
  ArrowRight,
  ArrowLeft,
  Check,
  Loader2,
  Sparkles,
  Wand2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { setupOptimization, runOptimization, type OptimizationConfig } from "@/lib/api";

interface AISetupWizardProps {
  modelId?: string;
  onConfigReady: (config: OptimizationConfig) => void;
}

type Step = "input" | "review" | "confirm";

export function AISetupWizard({ modelId, onConfigReady }: AISetupWizardProps) {
  const [step, setStep] = useState<Step>("input");
  const [message, setMessage] = useState("");
  const [config, setConfig] = useState<OptimizationConfig | null>(null);
  const [explanation, setExplanation] = useState("");
  const [suggestedPrompts, setSuggestedPrompts] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSetup = async (overrideMessage?: string) => {
    const msg = overrideMessage || message;
    if (!msg.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const response = await setupOptimization(msg, modelId);
      setConfig(response.config);
      setExplanation(response.explanation);
      setSuggestedPrompts(response.suggested_prompts);
      setStep("review");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate config");
    } finally {
      setLoading(false);
    }
  };

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await runOptimization(message, modelId);
      onConfigReady(response.config_generated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start optimization");
    } finally {
      setLoading(false);
    }
  };

  const handleUseConfig = () => {
    if (config) {
      onConfigReady(config);
    }
  };

  return (
    <div className="border border-[#e8e4e1] rounded-lg bg-[#fafaf9] overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-[#e8e4e1]">
        <Wand2 className="w-4 h-4 text-[#1a1a2e]/40" strokeWidth={1.5} />
        <span className="text-xs font-medium text-[#0f0f0f] tracking-wide">
          AI Setup
        </span>
        <div className="flex items-center gap-1.5 ml-auto">
          {(["input", "review", "confirm"] as Step[]).map((s, i) => (
            <div
              key={s}
              className={cn(
                "w-1.5 h-1.5 rounded-full transition-colors duration-200",
                step === s
                  ? "bg-[#c0392b]"
                  : i < ["input", "review", "confirm"].indexOf(step)
                  ? "bg-[#0f0f0f]/20"
                  : "bg-[#e8e4e1]"
              )}
            />
          ))}
        </div>
      </div>

      <div className="p-4">
        {step === "input" && (
          <div className="space-y-4">
            <p className="text-xs text-[#1a1a2e]/40 leading-relaxed">
              Describe your model and constraints in plain language. The AI will
              generate an optimized configuration.
            </p>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="e.g., I have a ResNet50 checkpoint, need it under 20ms latency on MI300X, can tolerate 3% accuracy drop..."
              rows={3}
              className="w-full px-3 py-2.5 text-xs bg-white border border-[#e8e4e1] rounded-md resize-none focus:outline-none focus:border-[#1a1a2e]/20 transition-colors duration-200 placeholder:text-[#1a1a2e]/25"
            />

            {suggestedPrompts.length > 0 && step === "input" && (
              <div className="flex flex-wrap gap-2">
                {suggestedPrompts.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => handleSetup(prompt)}
                    disabled={loading}
                    className="px-2.5 py-1.5 text-[10px] text-[#0f0f0f]/60 border border-[#e8e4e1] rounded-full hover:border-[#1a1a2e]/15 hover:bg-white transition-all duration-200"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            )}

            {error && (
              <p className="text-xs text-[#c0392b]">{error}</p>
            )}

            <div className="flex justify-end">
              <button
                onClick={() => handleSetup()}
                disabled={!message.trim() || loading}
                className={cn(
                  "inline-flex items-center gap-2 px-5 py-2 text-xs tracking-wide rounded transition-colors duration-200",
                  message.trim() && !loading
                    ? "text-[#fafaf9] bg-[#0f0f0f] hover:bg-[#1a1a2e]"
                    : "text-[#1a1a2e]/30 bg-[#e8e4e1]/50 cursor-not-allowed"
                )}
              >
                {loading ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" strokeWidth={1.5} />
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5" strokeWidth={1.5} />
                    Generate Config
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {step === "review" && config && (
          <div className="space-y-4">
            <p className="text-xs text-[#1a1a2e]/40 leading-relaxed">{explanation}</p>

            <div className="bg-white border border-[#e8e4e1] rounded-md p-4 space-y-3">
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <span className="text-[#1a1a2e]/30 block mb-0.5">Model Type</span>
                  <span className="text-[#0f0f0f] font-medium">{config.model_type}</span>
                </div>
                <div>
                  <span className="text-[#1a1a2e]/30 block mb-0.5">Hardware</span>
                  <span className="text-[#0f0f0f] font-medium">{config.target_hardware}</span>
                </div>
                <div>
                  <span className="text-[#1a1a2e]/30 block mb-0.5">Max Latency</span>
                  <span className="text-[#0f0f0f] font-mono">{config.constraints.max_latency_ms} ms</span>
                </div>
                <div>
                  <span className="text-[#1a1a2e]/30 block mb-0.5">Max Memory</span>
                  <span className="text-[#0f0f0f] font-mono">{config.constraints.max_memory_gb} GB</span>
                </div>
                <div>
                  <span className="text-[#1a1a2e]/30 block mb-0.5">Min Accuracy</span>
                  <span className="text-[#0f0f0f] font-mono">
                    {(config.constraints.min_accuracy_retention * 100).toFixed(1)}%
                  </span>
                </div>
                <div>
                  <span className="text-[#1a1a2e]/30 block mb-0.5">Quantization</span>
                  <span className="text-[#0f0f0f] font-mono">{config.parameters.quantization_format}</span>
                </div>
              </div>

              <div className="border-t border-[#e8e4e1] pt-3">
                <span className="text-[#1a1a2e]/30 text-[10px] uppercase tracking-wider block mb-2">
                  Recommended Phases
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {config.recommended_phases.map((phase) => (
                    <span
                      key={phase}
                      className="px-2 py-0.5 text-[10px] bg-[#e8e4e1]/50 text-[#0f0f0f]/60 rounded-full"
                    >
                      {phase}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {error && (
              <p className="text-xs text-[#c0392b]">{error}</p>
            )}

            <div className="flex items-center justify-between">
              <button
                onClick={() => setStep("input")}
                className="inline-flex items-center gap-1.5 text-xs text-[#1a1a2e]/40 hover:text-[#0f0f0f] transition-colors duration-200"
              >
                <ArrowLeft className="w-3 h-3" strokeWidth={1.5} />
                Back
              </button>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleUseConfig}
                  className="inline-flex items-center gap-1.5 px-4 py-2 text-xs text-[#0f0f0f] border border-[#e8e4e1] rounded hover:bg-white transition-colors duration-200"
                >
                  Use Config
                </button>
                <button
                  onClick={handleRun}
                  disabled={loading}
                  className="inline-flex items-center gap-2 px-5 py-2 text-xs tracking-wide text-[#fafaf9] bg-[#c0392b] rounded hover:bg-[#c0392b]/90 transition-colors duration-200 disabled:opacity-40"
                >
                  {loading ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" strokeWidth={1.5} />
                  ) : (
                    <>
                      Let AI Decide
                      <ArrowRight className="w-3.5 h-3.5" strokeWidth={1.5} />
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
