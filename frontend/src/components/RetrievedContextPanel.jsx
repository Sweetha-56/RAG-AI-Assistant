export default function RetrievedContextPanel({ retrievedDocs = [] }) {
  return (
    <section className="panel-card detail-card">
      <div className="panel-card-header">
        <h3>Retrieved Context</h3>
      </div>

      <div className="retrieved-context-panel">
        {retrievedDocs.length === 0 ? (
          <div className="empty-state">No retrieved context yet.</div>
        ) : (
          retrievedDocs.map((doc, index) => (
            <div key={index} className="context-card">
              <div className="context-title">Context {index + 1}</div>
              <div className="context-body">{doc}</div>
            </div>
          ))
        )}
      </div>
    </section>
  );
}