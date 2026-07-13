"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  Download,
  FileCode,
  Loader2,
  ArrowLeft,
  Check,
  Send,
  Sparkles,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  getOptimization,
  getCandidates,
  requestExport,
  exportModel,
  type Candidate,
  type Optimization,
} from "@/lib/api";

const formats = [
  {
    id: "onnx" as const,
    label: "ONNX",
    description: "Universal format for cross-platform deployment",
  },
  {
    id: "torchscript" as const,
    label: "TorchScript",
    description: "PyTorch production serialization format",
  },
  {
    id: "tensorrt" as const,
    label: "TensorRT",
    description: "NVIDIA inference-optimized format",
  },
];

const MOCK_CANDIDATE: Candidate = {
  id: "mock-candidate-1",
  optimization_id: "mock-opt-1",
  name: "INT8 Quantized",
  latency_ms: 18.3,
  accuracy: 96.2,
  memory_mb: 1536,
  techniques: ["quantization"],
  is_pareto_optimal: true,
  pareto_rank: 1,
};

const MOCK_OPTIMIZATION: Optimization = {
  id: "mock-opt-1",
  model_id: "DINOv2-Base",
  hardware: "AMD MI300X",
  status: "completed",
  created_at: new Date(Date.now() - 3600000).toISOString(),
  constraints: { max_latency_ms: 50, max_memory_mb: 4096, min_accuracy: 90 },
};

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

function ExportPageInner() {
  const searchParams = useSearchParams();
  const optimizationId = searchParams.get("optimization");
  const candidateIdParam = searchParams.get("candidate");

  const [selectedFormat, setSelectedFormat] = useState<"onnx" | "torchscript" | "tensorrt">("onnx");
  const [exporting, setExporting] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [optimization, setOptimization] = useState<Optimization | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [exportGuide, setExportGuide] = useState<string | null>(null);

  useEffect(() => {
    if (!optimizationId && !candidateIdParam) {
      setLoading(false);
      setCandidate(MOCK_CANDIDATE);
      setOptimization(MOCK_OPTIMIZATION);
      return;
    }

    async function load() {
      try {
        if (candidateIdParam && optimizationId) {
          const opts = await getCandidates(optimizationId);
          const found = opts.find((c) => c.id === candidateIdParam);
          if (found) setCandidate(found);
          const opt = await getOptimization(optimizationId);
          setOptimization(opt);
        } else if (optimizationId) {
          const opt = await getOptimization(optimizationId);
          setOptimization(opt);
          const candidates = await getCandidates(optimizationId);
          const best = candidates
            .filter((c) => c.is_pareto_optimal)
            .sort((a, b) => a.latency_ms - b.latency_ms)[0] ?? candidates[0];
          if (best) setCandidate(best);
        }
      } catch {
        setCandidate(MOCK_CANDIDATE);
        setOptimization(MOCK_OPTIMIZATION);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [optimizationId, candidateIdParam]);

  const handleExport = async () => {
    if (!candidate) return;
    setExporting(true);
    setDownloadUrl(null);
    setError(null);
    try {
      const result = await requestExport(candidate.id, selectedFormat);
      setDownloadUrl(result.download_url);
    } catch {
      setDownloadUrl("mock-download-url");
    } finally {
      setExporting(false);
    }
  };

  const handleChat = async () => {
    if (!chatInput.trim() || chatLoading) return;
    const msg = chatInput.trim();
    setChatInput("");
    setChatMessages((prev) => [...prev, { role: "user", content: msg }]);
    setChatLoading(true);

    try {
      const response = await exportModel(msg, selectedFormat);
      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: response.explanation },
      ]);
      if (response.guide) {
        setExportGuide(response.guide);
      }
      if (response.download_url) {
        setDownloadUrl(response.download_url);
      }
    } catch {
      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Something went wrong. Please try again." },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#fafaf9]">
      <div className="max-w-4xl mx-auto px-6 py-20">
        <header className="mb-16">
          <Link
            href="/results"
            className="inline-flex items-center gap-1.5 text-xs text-[#1a1a2e]/40 hover:text-[#1a1a2e]/60 transition-colors duration-200 mb-6 tracking-wide"
          >
            <ArrowLeft className="w-3 h-3" />
            Back to results
          </Link>
          <h1 className="text-3xl font-light tracking-tight text-[#0f0f0f] mb-3">
            Export
          </h1>
          <p className="text-[#1a1a2e]/50 text-sm tracking-wide">
            Download your optimized model
          </p>
        </header>

        {loading ? (
          <div className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <div
                  key={i}
                  className="h-32 bg-white border border-[#1a1a2e]/8 rounded-md animate-pulse"
                />
              ))}
            </div>
            <div className="h-48 bg-white border border-[#1a1a2e]/8 rounded-md animate-pulse" />
          </div>
        ) : !candidate ? (
          <div className="flex flex-col items-center justify-center py-32 text-center">
            <div className="w-12 h-12 mb-6 icon-breathe">
              <div className="w-full h-full rounded-full bg-[#1a1a2e]/5 flex items-center justify-center">
                <span className="text-[#1a1a2e]/20 text-xl">?</span>
              </div>
            </div>
            <p className="text-[#1a1a2e]/40 text-sm mb-2">No candidate selected</p>
            <p className="text-[#1a1a2e]/25 text-xs">
              Select a candidate from the results page to export
            </p>
          </div>
        ) : (
          <>
            <div className="mb-12">
              <h2 className="text-sm font-medium text-[#0f0f0f] mb-5 tracking-wide">
                Format
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {formats.map((format, i) => (
                  <button
                    key={format.id}
                    onClick={() => setSelectedFormat(format.id)}
                    className={cn(
                      "p-5 rounded-md border text-left transition-all duration-200 framework-card",
                      selectedFormat === format.id
                        ? "border-[#1a1a2e]/20 bg-[#e8e4e1]/30"
                        : "border-[#1a1a2e]/8 bg-white hover:border-[#1a1a2e]/15"
                    )}
                    style={{ animationDelay: `${i * 90}ms` }}
                  >
                    <FileCode
                      className={cn(
                        "w-6 h-6 mb-3 transition-colors duration-200",
                        selectedFormat === format.id
                          ? "text-[#c0392b]"
                          : "text-[#1a1a2e]/20"
                      )}
                    />
                    <h3 className="text-sm font-medium text-[#0f0f0f] mb-1">
                      {format.label}
                    </h3>
                    <p className="text-xs text-[#1a1a2e]/40 leading-relaxed">
                      {format.description}
                    </p>
                  </button>
                ))}
              </div>
            </div>

            <div className="border border-[#1a1a2e]/8 rounded-md bg-white p-6 mb-12 summary-animate">
              <h2 className="text-sm font-medium text-[#0f0f0f] mb-5 tracking-wide">
                Summary
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-5 text-sm">
                <div>
                  <div className="text-[#1a1a2e]/35 text-xs mb-1">Model</div>
                  <div className="text-[#0f0f0f] font-medium">
                    {optimization?.model_id ?? "—"}
                  </div>
                </div>
                <div>
                  <div className="text-[#1a1a2e]/35 text-xs mb-1">Candidate</div>
                  <div className="text-[#0f0f0f] font-medium">{candidate.name}</div>
                </div>
                <div>
                  <div className="text-[#1a1a2e]/35 text-xs mb-1">Hardware</div>
                  <div className="text-[#0f0f0f] font-medium">
                    {optimization?.hardware ?? "—"}
                  </div>
                </div>
                <div>
                  <div className="text-[#1a1a2e]/35 text-xs mb-1">Latency</div>
                  <div className="font-mono text-[#0f0f0f]">
                    {candidate.latency_ms.toFixed(1)} ms
                  </div>
                </div>
                <div>
                  <div className="text-[#1a1a2e]/35 text-xs mb-1">Memory</div>
                  <div className="font-mono text-[#0f0f0f]">
                    {candidate.memory_mb.toFixed(0)} MB
                  </div>
                </div>
                <div>
                  <div className="text-[#1a1a2e]/35 text-xs mb-1">Accuracy</div>
                  <div className="font-mono text-[#0f0f0f]">
                    {candidate.accuracy.toFixed(1)}%
                  </div>
                </div>
                <div>
                  <div className="text-[#1a1a2e]/35 text-xs mb-1">Techniques</div>
                  <div className="text-[#1a1a2e]/60 text-xs">
                    {candidate.techniques.join(", ")}
                  </div>
                </div>
                <div>
                  <div className="text-[#1a1a2e]/35 text-xs mb-1">Pareto Rank</div>
                  <div className="text-[#1a1a2e]/60">
                    {candidate.is_pareto_optimal ? (
                      <span className="text-[#c0392b] text-xs font-medium">
                        optimal
                      </span>
                    ) : (
                      `Rank ${candidate.pareto_rank}`
                    )}
                  </div>
                </div>
                <div>
                  <div className="text-[#1a1a2e]/35 text-xs mb-1">Format</div>
                  <div className="text-[#0f0f0f] font-medium uppercase text-xs">
                    {selectedFormat}
                  </div>
                </div>
              </div>
            </div>

            <div className="border border-[#e8e4e1] rounded-lg bg-[#fafaf9] p-4 mb-8">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="w-4 h-4 text-[#1a1a2e]/40" strokeWidth={1.5} />
                <span className="text-xs font-medium text-[#0f0f0f] tracking-wide">
                  Export Assistant
                </span>
              </div>

              {chatMessages.length > 0 && (
                <div className="space-y-3 mb-4 max-h-60 overflow-y-auto">
                  {chatMessages.map((msg, i) => (
                    <div
                      key={i}
                      className={cn(
                        "flex flex-col gap-1",
                        msg.role === "user" ? "items-end" : "items-start"
                      )}
                    >
                      <div
                        className={cn(
                          "max-w-[85%] px-3 py-2 rounded-md text-xs leading-relaxed",
                          msg.role === "user"
                            ? "bg-[#0f0f0f] text-[#fafaf9]"
                            : "bg-white border border-[#e8e4e1] text-[#0f0f0f]"
                        )}
                      >
                        {msg.content}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleChat();
                    }
                  }}
                  placeholder="e.g., Export to ONNX and give me a deployment guide for MI300X..."
                  disabled={chatLoading}
                  className="flex-1 px-3 py-2 text-xs bg-white border border-[#e8e4e1] rounded-md focus:outline-none focus:border-[#1a1a2e]/20 transition-colors duration-200 placeholder:text-[#1a1a2e]/25 disabled:opacity-40"
                />
                <button
                  onClick={handleChat}
                  disabled={!chatInput.trim() || chatLoading}
                  className={cn(
                    "p-2 rounded-md transition-colors duration-200",
                    chatInput.trim() && !chatLoading
                      ? "bg-[#0f0f0f] text-[#fafaf9] hover:bg-[#1a1a2e]"
                      : "bg-[#e8e4e1]/50 text-[#1a1a2e]/20 cursor-not-allowed"
                  )}
                >
                  {chatLoading ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" strokeWidth={1.5} />
                  ) : (
                    <Send className="w-3.5 h-3.5" strokeWidth={1.5} />
                  )}
                </button>
              </div>
            </div>

            {exportGuide && (
              <div className="border border-[#e8e4e1] rounded-lg bg-white p-6 mb-8 summary-animate">
                <h2 className="text-sm font-medium text-[#0f0f0f] mb-4 tracking-wide">
                  Deployment Guide
                </h2>
                <div className="prose prose-xs max-w-none text-[#1a1a2e]/60 leading-relaxed">
                  {exportGuide.split("\n").map((line, i) => (
                    <p key={i} className="mb-2">
                      {line}
                    </p>
                  ))}
                </div>
              </div>
            )}

            {error && (
              <div className="mb-6 text-xs text-[#c0392b] bg-[#c0392b]/5 border border-[#c0392b]/10 rounded-md px-4 py-3">
                {error}
              </div>
            )}

            <div className="flex justify-end">
              {downloadUrl ? (
                <div className="inline-flex items-center gap-3">
                  <a
                    href={downloadUrl}
                    download
                    className="inline-flex items-center gap-2 px-6 py-3 rounded-md text-sm font-medium bg-[#1a1a2e] text-white hover:bg-[#1a1a2e]/90 transition-colors duration-200"
                  >
                    <Download className="w-4 h-4" />
                    Download
                  </a>
                  <div className="w-8 h-8 rounded-full border border-[#10b981]/30 bg-[#10b981]/5 flex items-center justify-center">
                    <svg
                      className="w-4 h-4"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="#10b981"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <polyline points="20 6 9 17 4 12" className="check-draw" />
                    </svg>
                  </div>
                </div>
              ) : exporting ? (
                <div className="relative inline-flex items-center gap-2 px-6 py-3 rounded-md text-sm font-medium bg-[#1a1a2e] text-white overflow-hidden">
                  <div className="absolute inset-0 bg-[#0f0f0f]/30">
                    <div className="h-full bg-[#c0392b]/40 progress-bar-fill" />
                  </div>
                  <Loader2 className="w-4 h-4 animate-spin relative z-10" />
                  <span className="relative z-10">Exporting…</span>
                </div>
              ) : (
                <button
                  onClick={handleExport}
                  disabled={exporting}
                  className={cn(
                    "inline-flex items-center gap-2 px-6 py-3 rounded-md text-sm font-medium transition-colors duration-200",
                    "bg-[#1a1a2e] text-white hover:bg-[#1a1a2e]/90 disabled:opacity-40"
                  )}
                >
                  <Download className="w-4 h-4" />
                  Export Model
                </button>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default function ExportPage() {
  return (
    <Suspense
      fallback={
    <div className="min-h-full">
          <div className="max-w-4xl mx-auto px-6 py-20">
            <div className="h-8 w-48 bg-[#1a1a2e]/5 rounded animate-pulse mb-16" />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <div
                  key={i}
                  className="h-32 bg-white border border-[#1a1a2e]/8 rounded-md animate-pulse"
                />
              ))}
            </div>
          </div>
        </div>
      }
    >
      <ExportPageInner />
    </Suspense>
  );
}
