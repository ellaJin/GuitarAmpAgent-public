// src/pages/Admin/AddDocument/AddDocument.tsx
import { useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useAddDocument, SOURCE_TYPE_OPTIONS } from "./useAddDocument";
// Reuse DeviceAdmin's stylesheet — same design language
import "../DeviceAdmin/DeviceAdmin.css";

export default function AddDocument() {
  const nav = useNavigate();
  const {
    deviceName,
    loading,
    adminToken,
    setAdminToken,
    sourceType,
    setSourceType,
    manualFile,
    setManualFile,
    handleSubmit,
  } = useAddDocument();

  const manualInputRef = useRef<HTMLInputElement>(null);
  const pickManual = () => { if (!loading) manualInputRef.current?.click(); };

  return (
    <div className="admin-page">
      <div className="admin-card">
        <header className="admin-header">
          <h1>Add Document</h1>
          <p>
            Upload an additional PDF for <strong>{deviceName}</strong>. The document will be
            ingested and indexed independently. Device capabilities are inherited from the
            existing device record and are not changed here.
          </p>
        </header>

        <form className="admin-form" onSubmit={handleSubmit}>
          <label className="field">
            <span>Admin Token (optional)</span>
            <input
              type="password"
              value={adminToken}
              onChange={(e) => setAdminToken(e.target.value)}
              placeholder="x-admin-token"
              disabled={loading}
            />
          </label>

          <label className="field">
            <span>Document Type</span>
            <select
              value={sourceType}
              onChange={(e) => setSourceType(e.target.value)}
              disabled={loading}
            >
              {SOURCE_TYPE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </label>

          {/* Manual PDF (required) */}
          <div
            className={`dropzone ${loading ? "disabled" : ""}`}
            role="button"
            tabIndex={0}
            onClick={pickManual}
            onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") pickManual(); }}
          >
            <div className="dz-title">Manual PDF (required)</div>
            <div className="dz-sub">
              {manualFile ? (
                <>
                  <strong>{manualFile.name}</strong>{" "}
                  <span className="muted">({(manualFile.size / 1024 / 1024).toFixed(2)} MB)</span>
                </>
              ) : (
                "Click to select a PDF file"
              )}
            </div>
            <input
              ref={manualInputRef}
              type="file"
              hidden
              accept=".pdf,application/pdf"
              onChange={(e) => setManualFile(e.target.files?.[0] ?? null)}
            />
          </div>

          <button className="primary" type="submit" disabled={loading || !manualFile}>
            {loading ? "Uploading…" : "Upload & Index"}
          </button>

          <button
            type="button"
            className="primary"
            style={{ background: "transparent", color: "#e8e8e8", marginTop: 0 }}
            onClick={() => nav("/admin")}
            disabled={loading}
          >
            Cancel
          </button>

          <div className="hint">
            After upload, you will be redirected to the admin home page where you can monitor
            ingestion progress for this document.
          </div>
        </form>
      </div>
    </div>
  );
}
