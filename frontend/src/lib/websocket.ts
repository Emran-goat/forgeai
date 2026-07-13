export interface OptimizationMessage {
  type: "progress" | "candidate" | "complete" | "error";
  optimization_id: string;
  data: {
    progress?: number;
    current_step?: string;
    candidate?: {
      id: string;
      latency_ms: number;
      memory_mb: number;
      accuracy: number;
      techniques: string[];
    };
    error?: string;
  };
  timestamp: string;
}

export type MessageHandler = (message: OptimizationMessage) => void;
export type StatusHandler = (status: "connecting" | "connected" | "disconnected" | "error") => void;

export class OptimizationWebSocket {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private handlers: Set<MessageHandler> = new Set();
  private statusHandlers: Set<StatusHandler> = new Set();
  private optimizationId: string = "";
  private intentionalClose = false;

  constructor(private baseUrl: string = "ws://localhost:8000") {}

  connect(optimizationId: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    this.optimizationId = optimizationId;
    this.intentionalClose = false;
    this.emitStatus("connecting");

    const url = `${this.baseUrl}/ws/optimization/${optimizationId}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.emitStatus("connected");
    };

    this.ws.onmessage = (event) => {
      try {
        const message: OptimizationMessage = JSON.parse(event.data);
        this.handlers.forEach((handler) => handler(message));
      } catch (e) {
        console.error("Failed to parse WebSocket message:", e);
      }
    };

    this.ws.onclose = (event) => {
      if (this.intentionalClose) {
        this.emitStatus("disconnected");
        return;
      }
      if (event.code === 1006) {
        this.emitStatus("error");
      }
      this.attemptReconnect();
    };

    this.ws.onerror = () => {
      this.emitStatus("error");
    };
  }

  disconnect(): void {
    this.intentionalClose = true;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.handlers.clear();
    this.statusHandlers.clear();
  }

  onMessage(handler: MessageHandler): () => void {
    this.handlers.add(handler);
    return () => {
      this.handlers.delete(handler);
    };
  }

  onStatus(handler: StatusHandler): () => void {
    this.statusHandlers.add(handler);
    return () => {
      this.statusHandlers.delete(handler);
    };
  }

  private emitStatus(status: "connecting" | "connected" | "disconnected" | "error"): void {
    this.statusHandlers.forEach((handler) => handler(status));
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.emitStatus("error");
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    setTimeout(() => this.connect(this.optimizationId), delay);
  }
}

export function connectOptimization(
  optimizationId: string,
  onMessage: MessageHandler,
  onStatus?: StatusHandler
): () => void {
  const ws = new OptimizationWebSocket();
  ws.connect(optimizationId);
  const unsubscribeMsg = ws.onMessage(onMessage);
  const unsubscribeStatus = onStatus ? ws.onStatus(onStatus) : () => {};

  return () => {
    unsubscribeMsg();
    unsubscribeStatus();
    ws.disconnect();
  };
}
