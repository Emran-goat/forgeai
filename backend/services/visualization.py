from __future__ import annotations

from backend.models.assistant import ChartData


def generate_pareto_chart(
    candidates: list[dict],
    knee_point: dict | None = None,
) -> ChartData:
    x_lat = [c.get("latency_ms", 0) for c in candidates]
    y_acc = [c.get("accuracy", 0) for c in candidates]
    sizes = [max(10, c.get("memory_mb", 50) / 5) for c in candidates]
    names = [c.get("name", f"C{i}") for i, c in enumerate(candidates)]

    scatter_main = {
        "x": x_lat,
        "y": y_acc,
        "mode": "markers",
        "type": "scatter",
        "text": names,
        "marker": {
            "size": sizes,
            "color": "#6366f1",
            "opacity": 0.7,
            "line": {"width": 1, "color": "#312e81"},
        },
        "name": "Candidates",
        "hovertemplate": "%{text}<br>Latency: %{x:.1f}ms<br>Accuracy: %{y:.2%}<extra></extra>",
    }

    traces = [scatter_main]

    if knee_point:
        knee_trace = {
            "x": [knee_point.get("latency_ms", 0)],
            "y": [knee_point.get("accuracy", 0)],
            "mode": "markers",
            "type": "scatter",
            "text": ["Knee Point"],
            "marker": {
                "size": 18,
                "color": "#ef4444",
                "symbol": "star",
                "line": {"width": 2, "color": "#fff"},
            },
            "name": "Knee Point",
            "hovertemplate": "%{text}<br>Latency: %{x:.1f}ms<br>Accuracy: %{y:.2%}<extra></extra>",
        }
        traces.append(knee_trace)

    layout = {
        "title": {"text": "Latency vs Accuracy Tradeoff", "font": {"size": 18}},
        "xaxis": {"title": "Latency (ms)", "gridcolor": "#e5e7eb"},
        "yaxis": {"title": "Accuracy", "gridcolor": "#e5e7eb", "tickformat": ".1%"},
        "paper_bgcolor": "#fafaf9",
        "plot_bgcolor": "#fafaf9",
        "showlegend": True,
        "legend": {"x": 0.7, "y": 0.95},
    }

    return ChartData(chart_type="scatter", data=traces, layout=layout)


def generate_comparison_chart(
    before: dict,
    after: dict,
) -> ChartData:
    metrics = ["latency_ms", "memory_mb", "params_m", "accuracy"]
    labels = ["Latency (ms)", "Memory (MB)", "Params (M)", "Accuracy"]
    before_vals = [before.get(m, 0) for m in metrics]
    after_vals = [after.get(m, 0) for m in metrics]

    bar_before = {
        "x": labels,
        "y": before_vals,
        "type": "bar",
        "name": "Before",
        "marker": {"color": "#94a3b8"},
    }

    bar_after = {
        "x": labels,
        "y": after_vals,
        "type": "bar",
        "name": "After",
        "marker": {"color": "#6366f1"},
    }

    layout = {
        "title": {"text": "Before vs After Optimization", "font": {"size": 18}},
        "barmode": "group",
        "paper_bgcolor": "#fafaf9",
        "plot_bgcolor": "#fafaf9",
        "showlegend": True,
        "legend": {"x": 0.7, "y": 0.95},
    }

    return ChartData(chart_type="bar", data=[bar_before, bar_after], layout=layout)


def generate_phase_timeline(phases: list[dict]) -> ChartData:
    names = [p.get("name", f"Phase {i}") for i, p in enumerate(phases)]
    durations = [p.get("duration_s", 0) for p in phases]
    statuses = [p.get("status", "pending") for p in phases]

    colors = []
    for s in statuses:
        if s == "complete":
            colors.append("#22c55e")
        elif s == "running":
            colors.append("#f59e0b")
        elif s == "failed":
            colors.append("#ef4444")
        else:
            colors.append("#94a3b8")

    bar = {
        "x": names,
        "y": durations,
        "type": "bar",
        "marker": {"color": colors},
        "text": [f"{d:.1f}s" for d in durations],
        "textposition": "outside",
    }

    layout = {
        "title": {"text": "Pipeline Phase Duration", "font": {"size": 18}},
        "xaxis": {"title": "Phase"},
        "yaxis": {"title": "Duration (seconds)"},
        "paper_bgcolor": "#fafaf9",
        "plot_bgcolor": "#fafaf9",
        "showlegend": False,
    }

    return ChartData(chart_type="bar", data=[bar], layout=layout)


def generate_auto_chart(data: dict, options: dict) -> ChartData:
    candidates = data.get("candidates", [])
    pareto_front = data.get("pareto_front", [])
    knee_point = data.get("knee_point")
    phases = data.get("phases", [])
    before = data.get("before")
    after = data.get("after")

    if before and after:
        return generate_comparison_chart(before, after)

    if phases:
        return generate_phase_timeline(phases)

    if candidates:
        knee = knee_point or (pareto_front[0] if pareto_front else None)
        return generate_pareto_chart(candidates, knee)

    return ChartData(
        chart_type="scatter",
        data=[{"x": [0], "y": [0], "type": "scatter", "mode": "markers"}],
        layout={"title": {"text": "No data available"}},
    )
