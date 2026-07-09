"use client";

import { useState, useRef, useEffect } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Send, Bot, User, Sparkles, Zap, ListTree } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

const SUGGESTED_PROMPTS = [
  "Which batteries are at risk?",
  "Show vehicles needing maintenance",
  "Summarize carbon savings",
  "How is the fleet doing overall?",
];

function sessionId() {
  if (typeof window === "undefined") return "server";
  const existing = window.sessionStorage.getItem("ev-guardian-chat-session");
  if (existing) return existing;
  const id = `sess-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  window.sessionStorage.setItem("ev-guardian-chat-session", id);
  return id;
}

export default function AssistantPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "I'm the EV Guardian assistant. Ask me about battery risk, maintenance, suppliers, or carbon savings across the fleet.",
    },
  ]);
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const sid = useRef(sessionId());

  const { data: status } = useQuery({
    queryKey: ["chat-status"],
    queryFn: () => api.chat.status(),
    staleTime: 60_000,
  });

  const { mutate: sendMessage, isPending } = useMutation({
    mutationFn: (message: string) => api.chat.send(sid.current, message),
    onSuccess: (res) => {
      setMessages((prev) => [...prev, { role: "assistant", content: res.reply }]);
    },
    onError: () => {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Something went wrong reaching the fleet intelligence service. Please try again.",
        },
      ]);
    },
  });

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  function handleSend(text?: string) {
    const message = (text ?? input).trim();
    if (!message || isPending) return;
    setMessages((prev) => [...prev, { role: "user", content: message }]);
    setInput("");
    sendMessage(message);
  }

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight flex items-center gap-2">
            AI fleet assistant <Sparkles className="h-4 w-4 text-[var(--signal-agent)]" />
          </h1>
          <p className="text-sm text-foreground-muted">
            Natural-language interface over live fleet, battery, supplier, and carbon data.
          </p>
        </div>
        {status && (
          <div
            className={`flex shrink-0 items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium ${
              status.gemini_configured
                ? "border-[var(--signal-agent)]/40 bg-[var(--signal-agent)]/10 text-[var(--signal-agent)]"
                : "border-border-default bg-surface-elevated text-foreground-muted"
            }`}
            title={
              status.gemini_configured
                ? `Powered by Gemini (${status.model}) — full natural-language understanding`
                : "No GEMINI_API_KEY configured — running on a rule-based fallback with limited pattern matching. Add a key to apps/api/.env for full AI understanding."
            }
          >
            {status.gemini_configured ? <Zap className="h-3.5 w-3.5" /> : <ListTree className="h-3.5 w-3.5" />}
            {status.gemini_configured ? "AI mode (Gemini)" : "Rule-based mode"}
          </div>
        )}
      </div>

      <Card className="flex-1 flex flex-col !p-0 overflow-hidden min-h-[500px]">
        <div ref={scrollRef} className="flex-1 overflow-y-auto px-5 py-5 space-y-4">
          {messages.map((m, i) => (
            <div key={i} className={`flex gap-3 ${m.role === "user" ? "justify-end" : ""}`}>
              {m.role === "assistant" && (
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-[var(--signal-agent)] to-[var(--signal-info)]">
                  <Bot className="h-4 w-4 text-white" />
                </div>
              )}
              <div
                className={`max-w-[75%] rounded-[var(--radius)] px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ${
                  m.role === "user"
                    ? "bg-[var(--signal-info)] text-white"
                    : "bg-surface-elevated text-foreground"
                }`}
              >
                {m.content}
              </div>
              {m.role === "user" && (
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-surface-elevated border border-border-default">
                  <User className="h-4 w-4 text-foreground-muted" />
                </div>
              )}
            </div>
          ))}
          {isPending && (
            <div className="flex gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-[var(--signal-agent)] to-[var(--signal-info)]">
                <Bot className="h-4 w-4 text-white" />
              </div>
              <div className="rounded-[var(--radius)] bg-surface-elevated px-4 py-3">
                <div className="flex gap-1">
                  {[0, 1, 2].map((i) => (
                    <span
                      key={i}
                      className="h-1.5 w-1.5 rounded-full bg-foreground-dim animate-pulse"
                      style={{ animationDelay: `${i * 0.15}s` }}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {messages.length <= 1 && (
          <div className="px-5 pb-3 flex flex-wrap gap-2">
            {SUGGESTED_PROMPTS.map((p) => (
              <button
                key={p}
                onClick={() => handleSend(p)}
                className="rounded-full border border-border-default bg-surface px-3 py-1.5 text-xs text-foreground-muted hover:bg-surface-elevated hover:text-foreground transition-colors"
              >
                {p}
              </button>
            ))}
          </div>
        )}

        <div className="border-t border-border-subtle p-4 flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask about fleet health, battery risk, suppliers, carbon..."
            className="flex-1 rounded-[var(--radius-sm)] border border-border-subtle bg-surface px-3.5 py-2.5 text-sm placeholder:text-foreground-dim focus:outline-none focus:border-[var(--signal-info)]"
            disabled={isPending}
          />
          <Button onClick={() => handleSend()} disabled={isPending || !input.trim()} size="icon">
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </Card>
    </div>
  );
}
