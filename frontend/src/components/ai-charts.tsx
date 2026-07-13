"use client";

import { useState, useEffect, useCallback } from "react";
import { Loader2 } from "lucide-react";
import dynamic from "next/dynamic";
import { cn } from "@/lib/utils";
import { visualizeResults, type VisualizeResponse } from "@/lib/api";

const Plot = dynamic(() => import("react-plotly.js"), {
  ssr: false,
  loading: () => (
    <div className="h-[300px] flex items-center justify-center bg-white border border-[#e8e4e1] rounded-md">
      <Loader2 className="w-5 h-5 text-[#1a1a2e]/20 animate-spin" />
    </div>
  ),
});

interface AIChartsProps {
  data: Record<string, unknown>;
  className?: string;
}

export function AICharts({ data, className }: AIChartsProps) {
  const [chartData, setChartData] = useState<VisualizeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchChart = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await visualizeResults(data);
      setChartData(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate chart");
    } finally {
      setLoading(false);
    }
  }, [data]);

  useEffect(() => {
    if (data && Object.keys(data).length > 0) {
      fetchChart();
    }
  }, [data, fetchChart]);

  if (loading) {
    return (
      <div className={cn("space-y-3", className)}>
        <div className="h-[300px] bg-white border border-[#e8e4e1] rounded-md animate-pulse" />
        <div className="h-4 w-2/3 bg-[#1a1a2e]/5 rounded animate-pulse" />
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn("space-y-3", className)}>
        <div className="h-[300px] flex items-center justify-center bg-white border border-[#e8e4e1] rounded-md">
          <p className="text-xs text-[#1a1a2e]/30">{error}</p>
        </div>
      </div>
    );
  }

  if (!chartData) return null;

  return (
    <div className={cn("space-y-3", className)}>
      <div className="bg-white border border-[#e8e4e1] rounded-md overflow-hidden">
        <Plot
          data={chartData.chart.data as Plotly.Data[]}
          layout={{
            ...(chartData.chart.layout as Record<string, unknown>),
            autosize: true,
            margin: { t: 30, r: 20, b: 40, l: 50 },
            paper_bgcolor: "transparent",
            plot_bgcolor: "transparent",
            font: {
              family: "Inter, system-ui, sans-serif",
              size: 11,
              color: "#1a1a2e",
            },
            xaxis: {
              ...((chartData.chart.layout.xaxis ?? {}) as Record<string, unknown>),
              gridcolor: "rgba(26, 26, 46, 0.06)",
              zerolinecolor: "rgba(26, 26, 46, 0.06)",
            },
            yaxis: {
              ...((chartData.chart.layout.yaxis ?? {}) as Record<string, unknown>),
              gridcolor: "rgba(26, 26, 46, 0.06)",
              zerolinecolor: "rgba(26, 26, 46, 0.06)",
            },
          }}
          config={{ displayModeBar: false, responsive: true }}
          className="w-full"
          style={{ height: "300px" }}
        />
      </div>

      {chartData.explanation && (
        <p className="text-xs text-[#1a1a2e]/50 leading-relaxed px-1">
          {chartData.explanation}
        </p>
      )}

      {chartData.suggested_next.length > 0 && (
        <div className="flex flex-wrap gap-1.5 px-1">
          {chartData.suggested_next.map((action) => (
            <button
              key={action}
              className="px-2.5 py-1.5 text-[10px] text-[#0f0f0f]/60 border border-[#e8e4e1] rounded-full hover:border-[#1a1a2e]/15 hover:bg-white transition-all duration-200"
            >
              {action}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
