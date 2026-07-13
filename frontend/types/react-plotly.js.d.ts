declare namespace Plotly {
  interface Data {
    [key: string]: unknown;
  }

  interface Layout {
    [key: string]: unknown;
  }

  interface Config {
    [key: string]: unknown;
  }

  interface Frame {
    [key: string]: unknown;
  }

  interface Figure {
    data: Data[];
    layout: Layout;
  }

  type PlotMouseEvent = { points: Array<{ curveNumber: number; pointNumber: number; data: Data }> };
  type PlotSelectionEvent = PlotMouseEvent;
  type LegendClickEvent = { event: MouseEvent; nextLevel: string[]; curveNumber: number };
  type LegendDoubleClickEvent = LegendClickEvent;
  type RelayoutEvent = Record<string, unknown>;
  type RestyleEvent = [Record<string, unknown>, number[], number[]];
  type ButtonClickEvent = { event: MouseEvent };
  type FrameAnimationEvent = { name: string; animation: { frame: Frame; trace: number; group: string } };
  type SliderChangeEvent = { slider: { active: number }; previousActive: number };
  type SliderEndEvent = SliderChangeEvent;
  type ClickAnnotationEvent = { event: MouseEvent; index: number; fullAnnotation: string };
}

declare module "react-plotly.js" {
  import { Component } from "react";

  interface PlotParams {
    data: Plotly.Data[];
    layout?: Partial<Plotly.Layout>;
    config?: Partial<Plotly.Config>;
    frames?: Plotly.Frame[];
    revision?: number;
    onInitialized?: (figure: Plotly.Figure) => void;
    onUpdate?: (figure: Plotly.Figure) => void;
    onPurge?: (figure: Plotly.Figure) => void;
    onError?: (err: Error) => void;
    onAfterExport?: () => void;
    onAfterPlot?: () => void;
    onAnimated?: () => void;
    onAnimatingFrame?: (event: Plotly.FrameAnimationEvent) => void;
    onAnimationInterrupted?: () => void;
    onAutoSize?: () => void;
    onBeforeExport?: () => void;
    onButtonClicked?: (event: Plotly.ButtonClickEvent) => void;
    onClick?: (event: Plotly.PlotMouseEvent) => void;
    onClickAnnotation?: (event: Plotly.ClickAnnotationEvent) => void;
    onDeselect?: () => void;
    onDoubleClick?: () => void;
    onFramework?: () => void;
    onHover?: (event: Plotly.PlotMouseEvent) => void;
    onLegendClick?: (event: Plotly.LegendClickEvent) => boolean;
    onLegendDoubleClick?: (event: Plotly.LegendDoubleClickEvent) => boolean;
    onRelayout?: (event: Plotly.RelayoutEvent) => void;
    onRestyle?: (event: Plotly.RestyleEvent) => void;
    onRedraw?: () => void;
    onSelected?: (event: Plotly.PlotSelectionEvent) => void;
    onSelecting?: (event: Plotly.PlotSelectionEvent) => void;
    onSliderChange?: (event: Plotly.SliderChangeEvent) => void;
    onSliderEnd?: (event: Plotly.SliderEndEvent) => void;
    onTransitioning?: () => void;
    onTransitionInterrupted?: () => void;
    onUnhover?: (event: Plotly.PlotMouseEvent) => void;
    style?: React.CSSProperties;
    className?: string;
    useResizeHandler?: boolean;
    divId?: string;
  }

  export default class Plot extends Component<PlotParams> {}
}
