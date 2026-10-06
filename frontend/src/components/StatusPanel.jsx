import { useRef, useState } from "react";
import { uploadDocument } from "../api";

export default function StatusPanel({ health, onDocumentIndexed }) {
  const fileInput = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [lastUpload, setLastUpload] = useState(null);

  const ready = health?.vector_store_ready;

  async function handleFile(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setLastUpload(null);
    try {
      const result = await uploadDocument(file);
      setLastUpload(result);
      onDocumentIndexed?.();
    } catch (err) {
      setLastUpload({ filename: file.name, status: "failed", chunks_indexed: 0, error: err.message });
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-mark" aria-hidden="true" />
        <div>
          <div className="brand-name">Support Console</div>
          <div className="brand-sub">Enterprise knowledge agent</div>
        </div>
      </div>

      <div className="status-block">
        <div className="status-row">
          <span className={`status-dot ${ready ? "dot-ready" : "dot-warn"}`} />
          <span>{ready ? "Knowledge base ready" : "Knowledge base empty"}</span>
        </div>
        <div className="status-meta">
          {health ? `${health.documents_indexed} chunks indexed` : "checking…"}
        </div>
      </div>

      <div className="upload-block">
        <div className="section-label">Add a document</div>
        <p className="section-hint">.txt, .md, or .pdf — indexed immediately.</p>
        <button
          className="upload-btn"
          onClick={() => fileInput.current?.click()}
          disabled={uploading}
        >
          {uploading ? "Indexing…" : "Upload document"}
        </button>
        <input
          ref={fileInput}
          type="file"
          accept=".txt,.md,.pdf"
          hidden
          onChange={handleFile}
        />
        {lastUpload && (
          <div className={`upload-result ${lastUpload.status === "failed" ? "result-fail" : "result-ok"}`}>
            {lastUpload.status === "failed"
              ? `Failed to index ${lastUpload.filename}`
              : `Indexed ${lastUpload.filename} — ${lastUpload.chunks_indexed} chunks`}
          </div>
        )}
      </div>

      <div className="sidebar-footer">
        <div className="section-label">How this works</div>
        <p className="section-hint">
          Every question is answered by two agents in sequence: one retrieves
          matching passages from your documents, the other writes a grounded
          reply. Answers with weak source matches are flagged for a human.
        </p>
      </div>
    </aside>
  );
}
