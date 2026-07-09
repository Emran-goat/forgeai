"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  Upload,
  Zap,
  BarChart3,
  Download,
  Cpu,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Home", icon: Home },
  { href: "/upload", label: "Upload", icon: Upload },
  { href: "/optimize", label: "Optimize", icon: Zap },
  { href: "/results", label: "Results", icon: BarChart3 },
  { href: "/export", label: "Export", icon: Download },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 flex-shrink-0 border-r border-border bg-card flex flex-col">
      <div className="px-6 pt-8 pb-6">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-8 h-8 rounded-md bg-primary/5 border border-border flex items-center justify-center transition-colors duration-200 group-hover:bg-primary/10">
            <Cpu className="w-4 h-4 text-muted-foreground" />
          </div>
          <span className="text-sm font-medium tracking-wide text-foreground">
            ForgeAI
          </span>
        </Link>
      </div>

      <nav className="flex-1 px-3">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const isActive = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 rounded-md text-[13px] font-medium transition-all duration-200 ease-out",
                    isActive
                      ? "text-foreground bg-muted"
                      : "text-muted-foreground hover:text-foreground hover:bg-accent/10"
                  )}
                >
                  <item.icon className="w-4 h-4 flex-shrink-0" strokeWidth={1.5} />
                  <span>{item.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="px-6 py-5 border-t border-border">
        <span className="text-[11px] text-muted-foreground tracking-wider uppercase">
          v0.1.0
        </span>
      </div>
    </aside>
  );
}
