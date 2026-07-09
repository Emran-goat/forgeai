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

export class OptimizationWebSocket {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private handlers: Set<MessageHandler> = new Set();

  constructor(private baseUrl: string = "ws://localhost:8000") {}

  connect(optimizationId: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    const url = `${this.baseUrl}/ws/optimization/${optimizationId}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log("WebSocket connected");
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      try {
        const message: OptimizationMessage = JSON.parse(event.data);
        this.handlers.forEach((handler) => handler(message));
      } catch (e) {
        console.error("Failed to parse WebSocket message:", e);
      }
    };

    this.ws.onclose = () => {
      console.log("WebSocket closed");
      this.attemptReconnect(optimizationId);
    };

    this.ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.handlers.clear();
  }

  onMessage(handler: MessageHandler): () => void {
    this.handlers.add(handler);
    return () => {
      this.handlers.delete(handler);
    };
  }

  private attemptReconnect(optimizationId: string): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("Max reconnection attempts reached");
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    setTimeout(() => this.connect(optimizationId), delay);
  }
}

export function connectOptimization(
  optimizationId: string,
  onMessage: MessageHandler
): () => void {
  const ws = new OptimizationWebSocket();
  ws.connect(optimizationId);
  const unsubscribe = ws.onMessage(onMessage);

  return () => {
    unsubscribe();
    ws.disconnect();
  };
}
