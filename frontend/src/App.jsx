import { useEffect, useState } from "react";
import Header from "./components/Header";
import UploadPanel from "./components/UploadPanel";
import QuestionBox from "./components/QuestionBox";
import ChatPanel from "./components/ChatPanel";
import FilesPanel from "./components/FilesPanel";
import HistoryPanel from "./components/HistoryPanel";
import FileDetailsPanel from "./components/FileDetailsPanel";
import {
  askQuestion,
  fetchFiles,
  fetchHistory,
  fetchFileDetails,
  deleteFile,
  healthCheck,
} from "./services/api";
import "./App.css";

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello. Upload a document and ask a question. I will answer using the most relevant content across all uploaded files, unless you select a specific file.",
      sources: [],
      retrieved_docs: [],
      image_paths: [],
    },
  ]);

  const [files, setFiles] = useState([]);
  const [history, setHistory] = useState([]);
  const [askBusy, setAskBusy] = useState(false);
  const [backendStatus, setBackendStatus] = useState("Checking backend...");
  const [selectedHistoryIndex, setSelectedHistoryIndex] = useState(null);
  const [selectedFile, setSelectedFile] = useState("");
  const [selectedFileDetails, setSelectedFileDetails] = useState(null);

  async function loadFiles() {
    try {
      const data = await fetchFiles();
      setFiles(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error("Failed to load files:", e);
      setFiles([]);
    }
  }

  async function loadHistory() {
    try {
      const data = await fetchHistory();
      setHistory(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error("Failed to load history:", e);
      setHistory([]);
    }
  }

  async function checkBackend() {
    try {
      await healthCheck();
      setBackendStatus("Backend is healthy");
    } catch (e) {
      setBackendStatus("Backend unavailable");
    }
  }

  useEffect(() => {
    checkBackend();
    loadFiles();
    loadHistory();
  }, []);

  async function handleAsk(question) {
    setAskBusy(true);
    setSelectedHistoryIndex(null);

    const userMessage = {
      role: "user",
      content: selectedFile
        ? `${question}\n\n[Specific file: ${selectedFile}]`
        : `${question}\n\n[Searching across all uploaded files]`,
    };

    const newMessages = [...messages, userMessage];
    setMessages(newMessages);

    try {
      const result = await askQuestion(question, selectedFile || null);

      const assistantMessage = {
        role: "assistant",
        content: result?.answer || "No answer returned.",
        sources: result?.sources || [],
        retrieved_docs: result?.retrieved_docs || [],
        image_paths: result?.image_paths || [],
        expandedSection: null,
      };

      setMessages([...newMessages, assistantMessage]);
      await loadHistory();
    } catch (error) {
      setMessages([
        ...newMessages,
        {
          role: "assistant",
          content: `Question failed: ${error.message}`,
          sources: [],
          retrieved_docs: [],
          image_paths: [],
          expandedSection: null,
        },
      ]);
    } finally {
      setAskBusy(false);
    }
  }

  async function handleUploadSuccess() {
    await loadFiles();
  }

  async function handleSelectFile(fileName) {
    setSelectedFile(fileName);

    try {
      const details = await fetchFileDetails(fileName);
      setSelectedFileDetails(details);
    } catch (e) {
      console.error("Failed to load file details:", e);
      setSelectedFileDetails(null);
    }
  }

  async function handleDeleteFile(fileName) {
    try {
      await deleteFile(fileName);
      if (selectedFile === fileName) {
        setSelectedFile("");
        setSelectedFileDetails(null);
      }
      await loadFiles();
    } catch (e) {
      console.error("Delete failed:", e);
      alert(`Delete failed: ${e.message}`);
    }
  }

  function handleUseAllFiles() {
    setSelectedFile("");
    setSelectedFileDetails(null);
  }

  function handleHistorySelect(item, index) {
    setSelectedHistoryIndex(index);
    if (item?.file_name) {
      setSelectedFile(item.file_name);
    } else {
      setSelectedFile("");
    }

    setMessages([
      {
        role: "user",
        content: item?.file_name
          ? `${item?.question || ""}\n\n[Specific file: ${item.file_name}]`
          : `${item?.question || ""}\n\n[Searching across all uploaded files]`,
      },
      {
        role: "assistant",
        content: item?.answer || "",
        sources: item?.sources || [],
        retrieved_docs: item?.retrieved_docs || [],
        image_paths: item?.image_paths || [],
        expandedSection: null,
      },
    ]);
  }

  function handleToggleMessageSection(messageIndex, sectionName) {
    setMessages((prev) =>
      prev.map((msg, idx) => {
        if (idx !== messageIndex) return msg;
        return {
          ...msg,
          expandedSection:
            msg.expandedSection === sectionName ? null : sectionName,
        };
      })
    );
  }

  return (
    <div className="app-shell">
      <Header backendStatus={backendStatus} />

      <div className="app-layout">
        <aside className="sidebar">
          <UploadPanel onUploadSuccess={handleUploadSuccess} />

          <FilesPanel
            files={files}
            selectedFile={selectedFile}
            onSelectFile={handleSelectFile}
            onDeleteFile={handleDeleteFile}
            onUseAllFiles={handleUseAllFiles}
          />

          <FileDetailsPanel details={selectedFileDetails} />

          <HistoryPanel
            history={history}
            selectedIndex={selectedHistoryIndex}
            onSelectHistory={handleHistorySelect}
          />
        </aside>

        <main className="chat-workspace">
          <ChatPanel
            messages={messages || []}
            onToggleSection={handleToggleMessageSection}
          />

          <QuestionBox
            onAsk={handleAsk}
            busy={askBusy}
            selectedFile={selectedFile}
          />
        </main>
      </div>
    </div>
  );
}