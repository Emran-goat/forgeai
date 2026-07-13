"use client";

import {
  BarChart3,
  Zap,
  Eye,
  Download,
  LineChart,
  TrendingDown,
  GitCompare,
  Target,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface PreloadedPromptsProps {
  onSelect: (prompt: string) => void;
  category?: "all" | "analyze" | "optimize" | "visualize" | "export";
}

interface PromptCard {
  id: string;
  prompt: string;
  title: string;
  description: string;
  category: "analyze" | "optimize" | "visualize" | "export";
  icon: React.ReactNode;
}

const PROMPTS: PromptCard[] = [
  {
    id: "explain-results",
    prompt: "Explain these results",
    title: "Explain Results",
    description: "Get a clear breakdown of optimization outcomes",
    category: "analyze",
    icon: <BarChart3 className="w-4 h-4" strokeWidth={1.5} />,
  },
  {
    id: "stricter-constraints",
    prompt: "What would happen with stricter constraints?",
    title: "Stricter Constraints",
    description: "Explore tighter latency and memory targets",
    category: "analyze",
    icon: <TrendingDown className="w-4 h-4" strokeWidth={1.5} />,
  },
  {
    id: "recommend-candidate",
    prompt: "Recommend the best candidate",
    title: "Best Candidate",
    description: "AI picks the optimal model variant",
    category: "optimize",
    icon: <Target className="w-4 h-4" strokeWidth={1.5} />,
  },
  {
    id: "knee-point",
    prompt: "Why is this the knee point on the Pareto frontier?",
    title: "Knee Point",
    description: "Understand the Pareto frontier tradeoff",
    category: "visualize",
    icon: <LineChart className="w-4 h-4" strokeWidth={1.5} />,
  },
  {
    id: "tradeoff",
    prompt: "What's the tradeoff between Candidate A and B?",
    title: "Tradeoff Analysis",
    description: "Compare two candidates side by side",
    category: "analyze",
    icon: <GitCompare className="w-4 h-4" strokeWidth={1.5} />,
  },
  {
    id: "auto-optimize",
    prompt: "Optimize my model for lowest latency on MI300X",
    title: "Auto Optimize",
    description: "Let AI choose and run the best config",
    category: "optimize",
    icon: <Zap className="w-4 h-4" strokeWidth={1.5} />,
  },
  {
    id: "visualize-pareto",
    prompt: "Show me a Pareto chart of all candidates",
    title: "Pareto Chart",
    description: "Interactive latency vs accuracy plot",
    category: "visualize",
    icon: <Eye className="w-4 h-4" strokeWidth={1.5} />,
  },
  {
    id: "export-guide",
    prompt: "Export the best model to ONNX and give me a deployment guide",
    title: "Export + Guide",
    description: "Download optimized model with instructions",
    category: "export",
    icon: <Download className="w-4 h-4" strokeWidth={1.5} />,
  },
];

const CATEGORY_LABELS: Record<string, string> = {
  all: "All",
  analyze: "Analyze",
  optimize: "Optimize",
  visualize: "Visualize",
  export: "Export",
};

export function PreloadedPrompts({
  onSelect,
  category = "all",
}: PreloadedPromptsProps) {
  const filtered =
    category === "all"
      ? PROMPTS
      : PROMPTS.filter((p) => p.category === category);

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Sparkles className="w-3.5 h-3.5 text-[#1a1a2e]/30" strokeWidth={1.5} />
        <span className="text-[10px] uppercase tracking-[0.15em] text-[#1a1a2e]/30 font-medium">
          Quick Actions
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {filtered.map((card, i) => (
          <button
            key={card.id}
            onClick={() => onSelect(card.prompt)}
            className={cn(
              "group flex items-start gap-3 p-3 text-left border border-[#e8e4e1] rounded-md bg-white hover:border-[#1a1a2e]/15 transition-all duration-200",
              "framework-card"
            )}
            style={{ animationDelay: `${i * 60}ms` }}
          >
            <div className="mt-0.5 text-[#1a1a2e]/20 group-hover:text-[#c0392b]/60 transition-colors duration-200">
              {card.icon}
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-xs font-medium text-[#0f0f0f] mb-0.5 truncate">
                {card.title}
              </div>
              <div className="text-[10px] text-[#1a1a2e]/35 leading-relaxed truncate">
                {card.description}
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
