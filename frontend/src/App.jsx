import { useEffect, useRef, useState } from "react";
import StatusPanel from "./components/StatusPanel.jsx";
import MessageBubble from "./components/MessageBubble.jsx";
import Composer from "./components/Composer.jsx";
import { fetchHealth, sendMessage } from "./api";
import "./App.css";

function makeSessionId() {
  return `session-${Math.random().toString(36).slice(2, 10)}`;
}

export default function App() {
  const [health, setHealth] = useState(null);
  const [messages, setMessages] = useState([
    {
      role: "agent",
      text:
        "Hi, I'm the support agent. Ask me about billing, password resets, API limits, data export, or cancellations — I'll answer from the indexed knowledge base.",
      sources: [],
      confidence: null,
      escalate: false,
      latencyMs: null,
    },
  ]);
  const [sending, setSending] = useState(false);
  const sessionId = useRef(makeSessionId());
  const scrollRef = useRef(null);

  async function refreshHealth() {
    try {
      const h = await fetchHealth();
      setHealth(h);
    } catch {
      setHealth({ status: "unreachable", vector_store_ready: false, documents_indexed: 0 });
    }
  }

  useEffect(() => {
    refreshHealth();
    const interval = setInterval(refreshHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  async function handleSend(text) {
    setMessages((prev) => [
      ...prev,
      { role: "user", text },
      { role: "agent", pending: true },
    ]);
    setSending(true);

    try {
      const res = await sendMessage(sessionId.current, text);
      setMessages((prev) => {
        const next = [...prev];
        next[next.length - 1] = {
          role: "agent",
          text: res.answer,
          sources: res.sources,
          confidence: res.confidence,
          escalate: res.escalate,
          latencyMs: res.latency_ms,
        };
        return next;
      });
    } catch (err) {
      setMessages((prev) => {
        const next = [...prev];
        next[next.length - 1] = { role: "agent", text: err.message, error: true };
        return next;
      });
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="app-shell">
      <StatusPanel health={health} onDocumentIndexed={refreshHealth} />

      <main className="chat-panel">
        <div className="chat-scroll" ref={scrollRef}>
          {messages.map((m, i) => (
            <MessageBubble key={i} message={m} />
          ))}
        </div>
        <Composer onSend={handleSend} disabled={sending} />
      </main>
    </div>
  );
}
