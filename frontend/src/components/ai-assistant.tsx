"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Send, Loader2, Sparkles, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { chatWithAssistant, type ChatHistoryMessage, type ChatStreamChunk } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface AIAssistantProps {
  optimizationId?: string;
  context?: Record<string, unknown>;
  onConfigGenerated?: (config: Record<string, unknown>) => void;
  isOpen: boolean;
  onClose: () => void;
}

const PRELOADED_PROMPTS = [
  "Explain these results",
  "What would happen with stricter constraints?",
  "Recommend the best candidate",
  "Why is this the knee point on the Pareto frontier?",
  "What's the tradeoff between Candidate A and B?",
];

export function AIAssistant({
  optimizationId,
  context,
  isOpen,
  onClose,
}: AIAssistantProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const messagesRef = useRef<Message[]>([]);

  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  const handleSend = useCallback(
    async (text: string) => {
      if (!text.trim() || isStreaming) return;

      const userMsg: Message = {
        id: `u-${Date.now()}`,
        role: "user",
        content: text.trim(),
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMsg]);
      setInput("");
      setIsStreaming(true);

      const assistantMsg: Message = {
        id: `a-${Date.now()}`,
        role: "assistant",
        content: "",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMsg]);

      const history: ChatHistoryMessage[] = messagesRef.current.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      try {
        const stream = await chatWithAssistant(
          text,
          { optimization_id: optimizationId, ...context },
          history
        );

        const reader = stream.getReader();
        let accumulated = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = value as ChatStreamChunk;
          if (chunk.type === "token" && chunk.content) {
            accumulated += chunk.content;
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMsg.id ? { ...m, content: accumulated } : m
              )
            );
          }
        }
      } catch {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsg.id
              ? { ...m, content: "Something went wrong. Please try again." }
              : m
          )
        );
      } finally {
        setIsStreaming(false);
      }
    },
    [isStreaming, optimizationId, context]
  );

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend(input);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="flex flex-col h-full border border-[#e8e4e1] rounded-lg bg-[#fafaf9] overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#e8e4e1]">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-[#1a1a2e]/40" strokeWidth={1.5} />
          <span className="text-xs font-medium text-[#0f0f0f] tracking-wide">
            AI Assistant
          </span>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded hover:bg-[#e8e4e1]/50 transition-colors duration-200"
        >
          <X className="w-3.5 h-3.5 text-[#1a1a2e]/30" strokeWidth={1.5} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 min-h-0">
        {messages.length === 0 && (
          <div className="space-y-3 pt-4">
            <p className="text-xs text-[#1a1a2e]/30 tracking-wide">
              Ask anything about your optimization
            </p>
            {PRELOADED_PROMPTS.map((prompt) => (
              <button
                key={prompt}
                onClick={() => handleSend(prompt)}
                disabled={isStreaming}
                className="block w-full text-left px-3 py-2.5 text-xs text-[#0f0f0f]/70 border border-[#e8e4e1] rounded-md hover:border-[#1a1a2e]/15 hover:bg-white transition-all duration-200 disabled:opacity-40"
              >
                {prompt}
              </button>
            ))}
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn(
              "flex flex-col gap-1",
              msg.role === "user" ? "items-end" : "items-start"
            )}
          >
            <div
              className={cn(
                "max-w-[85%] px-3.5 py-2.5 rounded-lg text-xs leading-relaxed",
                msg.role === "user"
                  ? "bg-[#0f0f0f] text-[#fafaf9]"
                  : "bg-white border border-[#e8e4e1] text-[#0f0f0f]"
              )}
            >
              {msg.content || (
                <span className="inline-flex items-center gap-1.5 text-[#1a1a2e]/30">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  Thinking...
                </span>
              )}
            </div>
            <span className="text-[10px] text-[#1a1a2e]/20 px-1">
              {msg.timestamp.toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </span>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="px-4 pb-4 pt-2 border-t border-[#e8e4e1]">
        <div className="flex items-center gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your results..."
            disabled={isStreaming}
            className="flex-1 px-3 py-2 text-xs bg-white border border-[#e8e4e1] rounded-md focus:outline-none focus:border-[#1a1a2e]/20 transition-colors duration-200 placeholder:text-[#1a1a2e]/25 disabled:opacity-40"
          />
          <button
            onClick={() => handleSend(input)}
            disabled={!input.trim() || isStreaming}
            className={cn(
              "p-2 rounded-md transition-colors duration-200",
              input.trim() && !isStreaming
                ? "bg-[#0f0f0f] text-[#fafaf9] hover:bg-[#1a1a2e]"
                : "bg-[#e8e4e1]/50 text-[#1a1a2e]/20 cursor-not-allowed"
            )}
          >
            {isStreaming ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" strokeWidth={1.5} />
            ) : (
              <Send className="w-3.5 h-3.5" strokeWidth={1.5} />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
