import { useState } from "react";
import { uploadAndIngestMultipleFiles } from "../services/api";

export default function UploadPanel({ onUploadSuccess }) {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [status, setStatus] = useState("");
  const [resultSummary, setResultSummary] = useState(null);

  function handleFileChange(e) {
    const files = Array.from(e.target.files || []);
    setSelectedFiles(files);
    setStatus("");
    setResultSummary(null);
  }

  async function handleUpload() {
    if (!selectedFiles.length) {
      setStatus("Please select one or more files first.");
      return;
    }

    try {
      setUploading(true);
      setStatus("Uploading and ingesting selected files...");
      setResultSummary(null);

      const result = await uploadAndIngestMultipleFiles(selectedFiles);

      const successCount = (result.ingest_results || []).filter(
        (x) => x.status === "ingested"
      ).length;

      const failedCount =
        (result.failed_uploads?.length || 0) +
        (result.ingest_results || []).filter((x) => x.status === "failed").length;

      const totalChunks = (result.ingest_results || [])
        .filter((x) => x.status === "ingested")
        .reduce((sum, x) => sum + (x.points_upserted || 0), 0);

      setStatus(
        `Completed. Success: ${successCount}, Failed: ${failedCount}, Total chunks created: ${totalChunks}`
      );

      setResultSummary(result);
      setSelectedFiles([]);

      if (onUploadSuccess) {
        await onUploadSuccess();
      }
    } catch (error) {
      setStatus(`Upload/Ingest failed: ${error.message}`);
    } finally {
      setUploading(false);
    }
  }

  return (
    <section className="sidebar-card">
      <div className="sidebar-card-header">
        <h3>Upload Document(s)</h3>
      </div>

      <div className="upload-panel">
        <label className="upload-dropzone">
          <input
            type="file"
            multiple
            accept=".pdf,.txt,.docx,.xlsx,.pptx,.png,.jpg,.jpeg,.bmp,.tiff,.tif"
            onChange={handleFileChange}
            hidden
          />
          <div className="upload-title">Choose one or more documents</div>
          <div className="upload-subtitle">
            Supported: PDF, TXT, DOCX, XLSX, PPTX, PNG, JPG, JPEG, BMP, TIFF
          </div>
        </label>

        {selectedFiles.length > 0 && (
          <div className="selected-file-list">
            <strong>Selected files:</strong>
            <ul>
              {selectedFiles.map((file, index) => (
                <li key={`${file.name}-${index}`}>
                  {file.name}
                </li>
              ))}
            </ul>
          </div>
        )}

        <button
          className="upload-btn"
          onClick={handleUpload}
          disabled={uploading || selectedFiles.length === 0}
        >
          {uploading ? "Uploading & Ingesting..." : "Upload & Ingest All"}
        </button>

        {status && <div className="upload-status">{status}</div>}

        {resultSummary && (
          <div className="upload-result-summary">
            <h4>Upload/Ingest Summary</h4>

            {resultSummary.uploaded?.length > 0 && (
              <>
                <div><strong>Uploaded:</strong></div>
                <ul>
                  {resultSummary.uploaded.map((item, idx) => (
                    <li key={`uploaded-${idx}`}>
                      {item.file_name}
                    </li>
                  ))}
                </ul>
              </>
            )}

            {resultSummary.ingest_results?.length > 0 && (
              <>
                <div><strong>Ingest Results:</strong></div>
                <ul>
                  {resultSummary.ingest_results.map((item, idx) => (
                    <li key={`ingest-${idx}`}>
                      {item.file_name} - {item.status}
                      {item.status === "ingested" && ` (${item.points_upserted} chunks)`}
                      {item.error && ` - ${item.error}`}
                    </li>
                  ))}
                </ul>
              </>
            )}

            {resultSummary.failed_uploads?.length > 0 && (
              <>
                <div><strong>Failed Uploads:</strong></div>
                <ul>
                  {resultSummary.failed_uploads.map((item, idx) => (
                    <li key={`failed-${idx}`}>
                      {item.file_name} - {item.error}
                    </li>
                  ))}
                </ul>
              </>
            )}
          </div>
        )}
      </div>
    </section>
  );
}