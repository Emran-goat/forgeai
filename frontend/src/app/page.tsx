import Link from "next/link";
import {
  Upload,
  Zap,
  BarChart3,
  Download,
  ArrowRight,
  Layers,
  GitBranch,
  Settings2,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const steps = [
  {
    num: "01",
    icon: Upload,
    title: "Upload",
    description: "Drop your PyTorch, ONNX, or TensorFlow model.",
    href: "/upload",
  },
  {
    num: "02",
    icon: Layers,
    title: "Architecture Search",
    description: "Explore candidate architectures for your hardware target.",
    href: "/optimize",
  },
  {
    num: "03",
    icon: Zap,
    title: "Optimize",
    description: "Pruning, quantization, and knowledge distillation.",
    href: "/optimize",
  },
  {
    num: "04",
    icon: BarChart3,
    title: "Benchmark",
    description: "Measure latency, memory, and accuracy on target hardware.",
    href: "/results",
  },
  {
    num: "05",
    icon: GitBranch,
    title: "Pareto Analysis",
    description: "Find optimal trade-offs across the multi-objective frontier.",
    href: "/results",
  },
  {
    num: "06",
    icon: Settings2,
    title: "Hyperparameter Tuning",
    description: "Auto-tune learning rates, batch sizes, and schedules.",
    href: "/optimize",
  },
  {
    num: "07",
    icon: Download,
    title: "Export",
    description: "Deploy-ready ONNX or TorchScript output.",
    href: "/export",
  },
];

export default function HomePage() {
  return (
    <div className="min-h-full">
      {/* Hero */}
      <section className="hero-section relative px-8 pt-32 pb-28 overflow-hidden">
        <div className="hero-bg" aria-hidden="true" />

        <div className="relative max-w-3xl mx-auto text-center">
          <p className="stagger-1 text-[11px] font-medium tracking-[0.25em] uppercase text-[#1a1a2e]/40 mb-6">
            Hardware-Aware Optimization
          </p>

          <h1 className="stagger-2 text-5xl sm:text-6xl font-light tracking-tight text-[#0f0f0f] mb-6 leading-[1.1]">
            The compiler for
            <br />
            <span className="text-forgeai-vermilion">efficient</span> AI
          </h1>

          <p className="stagger-3 text-base text-[#1a1a2e]/50 max-w-lg mx-auto mb-12 leading-relaxed font-light">
            Find the perfect balance between latency, memory, and accuracy
            for your specific deployment target.
          </p>

          <div className="stagger-4 flex items-center justify-center gap-4">
            <Button
              asChild
              className="bg-[#0f0f0f] text-white hover:bg-[#1a1a2e] px-6 h-10 text-[13px] font-medium rounded-md transition-colors duration-200"
            >
              <Link href="/upload" className="gap-2">
                Get Started
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </Button>
            <Button
              asChild
              variant="outline"
              className="border-[#1a1a2e]/15 text-muted-foreground hover:bg-[#e8e4e1]/40 hover:text-foreground px-6 h-10 text-[13px] font-medium rounded-md transition-colors duration-200"
            >
              <Link href="/results">View Results</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Process */}
      <section className="px-8 pb-28">
        <div className="max-w-4xl mx-auto">
          <p className="stagger-5 text-[11px] font-medium tracking-[0.25em] uppercase text-[#1a1a2e]/40 mb-3 text-center">
            Process
          </p>
          <h2 className="stagger-5 text-2xl font-light text-center text-[#0f0f0f] mb-16 tracking-tight">
            Seven phases to production
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-px bg-[#1a1a2e]/8 rounded-lg overflow-hidden">
            {steps.map((step, i) => (
              <Link
                key={step.href}
                href={step.href}
                className={`stagger-5 group relative bg-white p-8 transition-all duration-300 hover:bg-[#e8e4e1]/30 hover:-translate-y-1 hover:shadow-[0_8px_30px_rgba(0,0,0,0.04)] card-accent`}
              >
                <span className="card-number">{step.num}</span>
                <div className="relative">
                  <step.icon
                    className="w-5 h-5 text-[#1a1a2e]/30 mb-4 transition-colors duration-200 group-hover:text-[#c0392b]"
                    strokeWidth={1.5}
                  />
                  <h3 className="text-sm font-medium text-[#0f0f0f] mb-2 tracking-wide">
                    {step.title}
                  </h3>
                  <p className="text-[13px] text-[#1a1a2e]/40 leading-relaxed font-light">
                    {step.description}
                  </p>
                </div>
                <ArrowRight className="absolute right-6 top-8 w-4 h-4 text-[#1a1a2e]/20 opacity-0 group-hover:opacity-100 transition-all duration-200 group-hover:translate-x-1" />
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="px-8 pb-28">
        <div className="max-w-4xl mx-auto stats-divider pt-16">
          <div className="grid grid-cols-3 gap-8 text-center">
            <div className="stat-item">
              <div className="text-3xl font-light text-[#0f0f0f] mb-1 tracking-tight">
                <span className="stat-number" data-target="10">10</span><span className="text-forgeai-vermilion">+</span>
              </div>
              <div className="text-[11px] tracking-[0.15em] uppercase text-[#1a1a2e]/40">
                Targets
              </div>
            </div>
            <div className="stat-item">
              <div className="text-3xl font-light text-[#0f0f0f] mb-1 tracking-tight">
                &lt;<span className="stat-number" data-target="5">5</span>min
              </div>
              <div className="text-[11px] tracking-[0.15em] uppercase text-[#1a1a2e]/40">
                Speed
              </div>
            </div>
            <div className="stat-item">
              <div className="text-3xl font-light text-[#0f0f0f] mb-1 tracking-tight">
                <span className="stat-number" data-target="95">95</span>%<span className="text-forgeai-vermilion">+</span>
              </div>
              <div className="text-[11px] tracking-[0.15em] uppercase text-[#1a1a2e]/40">
                Accuracy
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-8 pb-12">
        <div className="max-w-4xl mx-auto footer-divider pt-8 text-center">
          <div className="flex items-center justify-center gap-6 mb-4">
            <div className="w-8 h-[1px] bg-[#1a1a2e]/10" />
            <span className="text-[11px] font-medium tracking-[0.2em] uppercase text-[#1a1a2e]/25">
              ForgeAI
            </span>
            <div className="w-8 h-[1px] bg-[#1a1a2e]/10" />
          </div>
          <p className="text-[11px] text-[#1a1a2e]/30 tracking-wider">
            Built for the AMD MI300X Hackathon
          </p>
        </div>
      </footer>
    </div>
  );
}
