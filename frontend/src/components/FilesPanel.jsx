export default function FilesPanel({
  files = [],
  selectedFile = "",
  onSelectFile,
  onDeleteFile,
  onUseAllFiles,
}) {
  return (
    <section className="sidebar-card">
      <div className="sidebar-card-header files-header">
        <h3>Uploaded Files</h3>
        <button type="button" className="use-all-btn" onClick={onUseAllFiles}>
          Use All Files
        </button>
      </div>

      {files.length === 0 ? (
        <p className="sidebar-empty">No uploaded files yet.</p>
      ) : (
        <ul className="sidebar-list">
          {files.map((file, index) => {
            const fileName =
              typeof file === "string" ? file : file?.name || "Unnamed file";
            const isSelected = fileName === selectedFile;

            return (
              <li key={index} className="file-row">
                <button
                  type="button"
                  className={`file-select-btn ${isSelected ? "selected-file-btn" : ""}`}
                  onClick={() => onSelectFile?.(fileName)}
                >
                  <span className="file-tag">DOC</span>
                  <span className="sidebar-item-text">{fileName}</span>
                </button>

                <button
                  type="button"
                  className="delete-file-btn"
                  onClick={() => onDeleteFile?.(fileName)}
                  title={`Delete ${fileName}`}
                >
                  Delete
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}