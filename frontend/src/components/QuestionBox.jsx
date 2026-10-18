import { useState } from "react";

export default function QuestionBox({ onAsk, busy, selectedFile }) {
  const [question, setQuestion] = useState("");

  function handleSubmit() {
    const q = question.trim();
    if (!q || busy) return;
    onAsk(q);
    setQuestion("");
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }

  return (
    <section className="composer-panel">
      <div className="composer-box">
        <div className="selected-file-banner">
          {selectedFile
            ? `Scoped to file: ${selectedFile}`
            : "Using all uploaded files for retrieval"}
        </div>

        <textarea
          rows="3"
          placeholder="Ask a question about your uploaded documents..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={busy}
        />

        <div className="composer-actions">
          <span className="composer-hint">
            Press Enter to send, Shift+Enter for a new line
          </span>
          <button className="send-btn" onClick={handleSubmit} disabled={busy || !question.trim()}>
            {busy ? "Generating..." : "Send"}
          </button>
        </div>
      </div>
    </section>
  );
}