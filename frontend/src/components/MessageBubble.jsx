export default function MessageBubble({ message }) {
  const isUser = message.role === "user";

  return (
    <div className={`message-row ${isUser ? "row-user" : "row-agent"}`}>
      <div className={`bubble ${isUser ? "bubble-user" : "bubble-agent"}`}>
        {message.pending ? (
          <span className="typing" aria-label="Agent is thinking">
            <span />
            <span />
            <span />
          </span>
        ) : (
          <>
            <p className="bubble-text">{message.text}</p>

            {!isUser && message.error && <p className="bubble-error">{message.text}</p>}

            {!isUser && !message.error && (
              <div className="bubble-meta">
                <span className="meta-item">{message.latencyMs}ms</span>
                <span className="meta-item">confidence {message.confidence}</span>
                {message.escalate && <span className="meta-flag">flagged for review</span>}
              </div>
            )}

            {!isUser && message.sources?.length > 0 && (
              <details className="sources">
                <summary>{message.sources.length} source{message.sources.length > 1 ? "s" : ""}</summary>
                <ul>
                  {message.sources.map((s, i) => (
                    <li key={i}>
                      <span className="source-name">{s.source}</span>
                      <span className="source-score">{s.score}</span>
                      <p className="source-snippet">{s.snippet}</p>
                    </li>
                  ))}
                </ul>
              </details>
            )}
          </>
        )}
      </div>
    </div>
  );
}
