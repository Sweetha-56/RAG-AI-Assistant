export default function FileDetailsPanel({ details }) {
  return (
    <section className="sidebar-card">
      <div className="sidebar-card-header">
        <h3>File Details</h3>
      </div>

      {!details ? (
        <p className="sidebar-empty">
          Select a file to view chunk details and related metadata.
        </p>
      ) : (
        <div className="file-details">
          <div><strong>Name:</strong> {details.name}</div>
          <div><strong>Type:</strong> {details.type}</div>
          <div><strong>Chunks Created:</strong> {details.chunk_count}</div>
          <div><strong>Entry Types:</strong> {details.entry_types?.join(", ") || "-"}</div>
          <div><strong>Pages:</strong> {details.pages?.join(", ") || "-"}</div>

          <div className="chunk-preview-section">
            <strong>Chunk Preview</strong>
            {details.preview_chunks?.length ? (
              <div className="chunk-preview-list">
                {details.preview_chunks.map((chunk, index) => (
                  <div key={index} className="chunk-preview-card">
                    <div className="chunk-meta">
                      Page: {chunk.page_number} | Type: {chunk.entry_type}
                    </div>
                    <div className="chunk-text">{chunk.text_preview}</div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="sidebar-empty">No chunk preview available.</p>
            )}
          </div>
        </div>
      )}
    </section>
  );
}