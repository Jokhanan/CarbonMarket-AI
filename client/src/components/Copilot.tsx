import { useState, useRef, useEffect } from "react";
import { useLocation } from "wouter";
import { Send, RefreshCw, Minimize2, Bot } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { ChatMessage } from "@/lib/api";

function MessageBubble({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-xl px-3 py-2 text-sm leading-relaxed ${
          isUser
            ? "bg-primary text-primary-foreground rounded-br-sm"
            : "bg-card border border-border/50 text-foreground rounded-bl-sm"
        }`}
      >
        {msg.content}
        {msg.navigate_to && (
          <div className="mt-1.5 text-xs opacity-80 italic">
            Navigating to {msg.navigate_to}...
          </div>
        )}
      </div>
    </div>
  );
}

export default function Copilot() {
  const [location, navigate] = useLocation();

  // Auto-detect project from URL /projects/:id
  const projectIdMatch = location.match(/^\/projects\/(\d+)/);
  const projectId = projectIdMatch ? parseInt(projectIdMatch[1]) : undefined;
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: projectId
        ? "AI Copilot ready. I can help you draft sections, analyze parameters, run simulations, or navigate tabs. What do you need?"
        : "AI Copilot ready. I can help you create projects, compare methodologies, or answer questions about carbon standards.",
    },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, open]);

  async function send() {
    const text = input.trim();
    if (!text || sending) return;

    const userMsg: ChatMessage = { role: "user", content: text };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setSending(true);

    try {
      const body: Record<string, unknown> = {
        message: text,
        history: messages.slice(-10).map((m) => ({ role: m.role, content: m.content })),
      };
      if (projectId) body.project_id = projectId;

      const r = await fetch("/api/projects/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();

      const reply: ChatMessage = {
        role: "assistant",
        content: data.response ?? data.message ?? data.reply ?? "Done.",
        action: data.action,
        navigate_to: data.navigate_to,
      };

      setMessages((m) => [...m, reply]);

      if (data.navigate_to) {
        setTimeout(() => navigate(data.navigate_to), 800);
      }
    } catch (e) {
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: `Sorry, something went wrong: ${String(e).slice(0, 120)}`,
        },
      ]);
    } finally {
      setSending(false);
    }
  }

  return (
    <>
      {/* FAB */}
      <button
        data-testid="button-copilot-fab"
        onClick={() => setOpen(true)}
        className={`fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-gradient-to-br from-primary to-primary/70 text-white shadow-lg shadow-primary/30 flex items-center justify-center transition-all hover:scale-110 hover:shadow-xl hover:shadow-primary/40 ${open ? "hidden" : ""}`}
        style={{ animation: "pulse-glow 3s ease-in-out infinite" }}
      >
        <Bot className="w-6 h-6" />
      </button>

      {/* Chat panel */}
      {open && (
        <div
          data-testid="copilot-panel"
          className="fixed bottom-6 right-6 z-50 w-[360px] flex flex-col bg-background border border-border rounded-2xl shadow-2xl overflow-hidden"
          style={{ height: "480px" }}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-primary to-primary/70">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-md bg-white/20 flex items-center justify-center">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div>
                <div className="text-sm font-semibold text-white leading-none">AI Copilot</div>
                <div className="text-[10px] text-white/70 mt-0.5">Carbon Intelligence</div>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setMessages([messages[0]])}
                className="text-white/60 hover:text-white p-1 rounded transition-colors text-xs"
                title="Clear history"
              >
                Clear
              </button>
              <button
                onClick={() => setOpen(false)}
                className="text-white/60 hover:text-white p-1 rounded transition-colors"
              >
                <Minimize2 className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3">
            {messages.map((msg, i) => (
              <MessageBubble key={i} msg={msg} />
            ))}
            {sending && (
              <div className="flex justify-start">
                <div className="bg-card border border-border/50 rounded-xl rounded-bl-sm px-3 py-2">
                  <RefreshCw className="w-4 h-4 animate-spin text-muted-foreground" />
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Suggestions */}
          {messages.length === 1 && (
            <div className="px-3 pb-2 flex flex-wrap gap-1.5">
              {(projectId
                ? ["Draft section A.1", "Run ER simulation", "Explain fNRB", "Check parameters"]
                : ["Create a new project", "Compare TPDDTEC vs VM0050", "What is a PDD?"]
              ).map((s) => (
                <button
                  key={s}
                  onClick={() => { setInput(s); }}
                  className="px-2.5 py-1 rounded-full text-xs bg-primary/10 text-primary hover:bg-primary/20 transition-colors border border-primary/20"
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          {/* Input */}
          <div className="px-3 pb-3 pt-2 border-t border-border/50">
            <div className="flex items-center gap-2">
              <Input
                data-testid="copilot-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
                placeholder="Ask anything about this project..."
                className="flex-1 bg-input border-border h-9 text-sm"
                disabled={sending}
              />
              <Button
                data-testid="button-copilot-send"
                size="sm"
                onClick={send}
                disabled={sending || !input.trim()}
                className="h-9 w-9 p-0 shrink-0"
              >
                {sending ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
