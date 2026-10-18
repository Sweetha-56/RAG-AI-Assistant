import ReactMarkdown from "react-markdown";
import { buildImageUrl } from "../services/api";

export default function ChatPanel({ messages = [], onToggleSection }) {
  return (
    <section className="chat-panel-card">
      <div className="chat-panel-header">
        <h2>Conversation</h2>
      </div>

      <div className="chat-thread">
        {messages.map((message, index) => {
          const isAssistant = message.role === "assistant";
          const expanded = message.expandedSection || null;

          return (
            <div
              key={index}
              className={`chat-message ${isAssistant ? "assistant" : "user"}`}
            >
              <div className="chat-bubble">
                <div className="chat-role">
                  {isAssistant ? "Assistant" : "You"}
                </div>

                <div className="chat-content markdown-content">
                  {isAssistant ? (
                    <ReactMarkdown>{message.content || ""}</ReactMarkdown>
                  ) : (
                    message.content
                  )}
                </div>

                {isAssistant && (
                  <>
                    <div className="message-actions">
                      <button
                        className={`message-tab-btn ${
                          expanded === "sources" ? "active" : ""
                        }`}
                        onClick={() => onToggleSection(index, "sources")}
                        disabled={!message.sources?.length}
                      >
                        Sources
                      </button>

                      <button
                        className={`message-tab-btn ${
                          expanded === "context" ? "active" : ""
                        }`}
                        onClick={() => onToggleSection(index, "context")}
                        disabled={!message.retrieved_docs?.length}
                      >
                        Retrieved Context
                      </button>

                      <button
                        className={`message-tab-btn ${
                          expanded === "images" ? "active" : ""
                        }`}
                        onClick={() => onToggleSection(index, "images")}
                        disabled={!message.image_paths?.length}
                      >
                        Related Images
                      </button>
                    </div>

                    {expanded === "sources" && (
                      <div className="message-detail-panel">
                        <h4>Sources</h4>
                        <div className="detail-grid">
                          {message.sources?.map((source, i) => (
                            <div key={i} className="detail-card">
                              <div><strong>File:</strong> {source.source_file || "-"}</div>
                              <div><strong>Type:</strong> {source.entry_type || "-"}</div>
                              <div><strong>Page:</strong> {source.page_number || "-"}</div>
                              <div><strong>Sheet:</strong> {source.sheet_name || "-"}</div>
                              <div><strong>Slide:</strong> {source.slide_number || "-"}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {expanded === "context" && (
                      <div className="message-detail-panel">
                        <h4>Retrieved Context</h4>
                        <div className="detail-grid">
                          {message.retrieved_docs?.map((doc, i) => (
                            <div key={i} className="detail-card">
                              <div className="detail-card-title">Context {i + 1}</div>
                              <div className="detail-card-content">{doc}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {expanded === "images" && (
                      <div className="message-detail-panel">
                        <h4>Related Images</h4>
                        <div className="image-grid">
                          {message.image_paths?.map((path, i) => (
                            <div key={i} className="image-card">
                              <img
                                src={buildImageUrl(path)}
                                alt={`related-${i}`}
                                className="related-image"
                              />
                              <div className="image-caption">{path}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}