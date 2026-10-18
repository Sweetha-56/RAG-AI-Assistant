export default function HistoryPanel({
  history = [],
  selectedIndex = null,
  onSelectHistory,
}) {
  return (
    <section className="sidebar-card history-panel">
      <div className="sidebar-card-header">
        <h3>Chat History</h3>
      </div>

      {history.length === 0 ? (
        <p className="sidebar-empty">No chat history yet.</p>
      ) : (
        <div className="history-list">
          {history
            .slice()
            .reverse()
            .map((item, reverseIndex) => {
              const actualIndex = history.length - 1 - reverseIndex;
              const isSelected = actualIndex === selectedIndex;

              return (
                <button
                  key={actualIndex}
                  className={`history-entry ${isSelected ? "selected-history" : ""}`}
                  onClick={() => onSelectHistory?.(item, actualIndex)}
                  type="button"
                >
                  <div className="history-question">
                    {item?.question || "Untitled chat"}
                  </div>

                  {item?.file_name && (
                    <div className="history-file-name">
                      File: {item.file_name}
                    </div>
                  )}

                  <div className="history-answer-preview">
                    {item?.answer || ""}
                  </div>
                </button>
              );
            })}
        </div>
      )}
    </section>
  );
}