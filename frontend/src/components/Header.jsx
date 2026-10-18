export default function Header({ backendStatus }) {
  const healthy = backendStatus?.toLowerCase().includes("healthy");

  return (
    <header className="topbar">
      <div className="brand-block">
        <div className="brand-icon">AZ</div>
        <div>
          <h1>Local RAG Assistant</h1>
          <p>Upload, search across documents, inspect file chunks, and ask grounded questions.</p>
        </div>
      </div>

      <div className={`status-chip ${healthy ? "healthy" : "unhealthy"}`}>
        {backendStatus}
      </div>
    </header>
  );
}