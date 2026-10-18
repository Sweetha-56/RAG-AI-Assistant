export default function SourcesPanel({ sources = [] }) {
  return (
    <section className="panel-card detail-card">
      <div className="panel-card-header">
        <h3>Sources</h3>
      </div>

      <div className="sources-panel">
        {sources.length === 0 ? (
          <div className="empty-state">No sources available.</div>
        ) : (
          sources.map((source, index) => (
            <div key={index} className="source-card">
              <div><strong>File:</strong> {source.source_file || "-"}</div>
              <div><strong>Type:</strong> {source.entry_type || "-"}</div>
              <div><strong>Page:</strong> {source.page_number || "-"}</div>
              <div><strong>Sheet:</strong> {source.sheet_name || "-"}</div>
              <div><strong>Slide:</strong> {source.slide_number || "-"}</div>
            </div>
          ))
        )}
      </div>
    </section>
  );
}