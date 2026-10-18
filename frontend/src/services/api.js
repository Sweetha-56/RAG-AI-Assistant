const API_BASE = "http://localhost:8000";
const API_PREFIX = `${API_BASE}/api`;

export async function healthCheck() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error("Health check failed");
  return res.json();
}

export async function uploadFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_PREFIX}/upload/`, {
    method: "POST",
    body: formData,
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Upload failed");
  return data;
}

export async function uploadMultipleFiles(files) {
  const formData = new FormData();

  files.forEach((file) => {
    formData.append("files", file);
  });

  const res = await fetch(`${API_PREFIX}/upload/multiple/`, {
    method: "POST",
    body: formData,
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Multiple upload failed");
  return data;
}

export async function ingestFile(fileName) {
  const res = await fetch(`${API_PREFIX}/ingest/file/${encodeURIComponent(fileName)}`, {
    method: "POST",
    headers: {
      accept: "application/json",
    },
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Ingestion failed");
  return data;
}

export async function uploadAndIngestFile(file) {
  const uploadResult = await uploadFile(file);
  const fileName = uploadResult.file_name || file.name;
  const ingestResult = await ingestFile(fileName);

  return {
    upload: uploadResult,
    ingest: ingestResult,
  };
}

export async function uploadAndIngestMultipleFiles(files) {
  const uploadResult = await uploadMultipleFiles(files);

  const uploadedFiles = uploadResult?.uploaded || [];
  const failedUploads = uploadResult?.failed || [];

  const ingestResults = [];

  for (const item of uploadedFiles) {
    try {
      const ingest = await ingestFile(item.file_name);
      ingestResults.push({
        file_name: item.file_name,
        status: "ingested",
        points_upserted: ingest.points_upserted ?? 0
      });
    } catch (error) {
      ingestResults.push({
        file_name: item.file_name,
        status: "failed",
        error: error.message
      });
    }
  }

  return {
    uploaded: uploadedFiles,
    failed_uploads: failedUploads,
    ingest_results: ingestResults
  };
}

export async function ingestAllUploads() {
  const res = await fetch(`${API_PREFIX}/ingest/uploads`, {
    method: "POST",
    headers: {
      accept: "application/json",
    },
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Failed to ingest uploaded files");
  return data;
}

export async function askQuestion(question, fileName = null) {
  const res = await fetch(`${API_PREFIX}/query/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      accept: "application/json",
    },
    body: JSON.stringify({
      question,
      file_name: fileName,
    }),
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Question failed");
  return data;
}

export async function fetchFiles() {
  const res = await fetch(`${API_PREFIX}/files/`, {
    headers: { accept: "application/json" },
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Failed to fetch files");
  return data;
}

export async function fetchFileDetails(fileName) {
  const res = await fetch(`${API_PREFIX}/files/${encodeURIComponent(fileName)}`, {
    headers: { accept: "application/json" },
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Failed to fetch file details");
  return data;
}

export async function deleteFile(fileName) {
  const res = await fetch(`${API_PREFIX}/files/${encodeURIComponent(fileName)}`, {
    method: "DELETE",
    headers: { accept: "application/json" },
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Failed to delete file");
  return data;
}

export async function fetchHistory() {
  const res = await fetch(`${API_PREFIX}/history/`, {
    headers: { accept: "application/json" },
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Failed to fetch history");
  return data;
}

export async function clearHistory() {
  const res = await fetch(`${API_PREFIX}/history/`, {
    method: "DELETE",
    headers: { accept: "application/json" },
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Failed to clear history");
  return data;
}

export async function deleteHistoryItem(index) {
  const res = await fetch(`${API_PREFIX}/history/${index}`, {
    method: "DELETE",
    headers: { accept: "application/json" },
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Failed to delete history item");
  return data;
}

export function buildImageUrl(path) {
  return `${API_PREFIX}/image?path=${encodeURIComponent(path)}`;
}