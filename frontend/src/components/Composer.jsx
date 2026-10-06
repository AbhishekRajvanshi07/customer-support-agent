import { useState } from "react";

export default function Composer({ onSend, disabled }) {
  const [value, setValue] = useState("");

  function submit(e) {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  }

  return (
    <form className="composer" onSubmit={submit}>
      <textarea
        className="composer-input"
        placeholder="Ask about billing, password resets, API limits…"
        value={value}
        rows={1}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            submit(e);
          }
        }}
      />
      <button className="composer-send" type="submit" disabled={disabled || !value.trim()}>
        Send
      </button>
    </form>
  );
}
