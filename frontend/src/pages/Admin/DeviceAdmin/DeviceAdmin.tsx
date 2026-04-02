// DeviceAdmin.tsx
import { useEffect, useMemo, useRef } from "react";
import { useDeviceAdmin } from "./useDeviceAdmin";
import "./DeviceAdmin.css";

// Source type options — hardcoded, matches backend VALID_SOURCE_TYPES
const SOURCE_TYPE_OPTIONS = [
  { value: "mixed", label: "Mixed (single PDF, all content)" },
  { value: "effects_settings", label: "Effects Settings (dedicated effect parameter PDF)" },
  { value: "user_manual", label: "User Manual (operation guide only, no effect list)" },
];

export default function DeviceAdmin() {
  const {
    loading,
    adminToken,
    setAdminToken,
    formData,
    updateField,
    manualFile,
    setManualFile,
    imageFile,
    setImageFile,
    handleSubmit,
  } = useDeviceAdmin();

  const manualInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);

  const pickManual = () => { if (!loading) manualInputRef.current?.click(); };
  const pickImage  = () => { if (!loading) imageInputRef.current?.click(); };

  // Avoid leaking object URLs when changing images
  const imagePreviewUrl = useMemo(() => {
    if (!imageFile) return null;
    return URL.createObjectURL(imageFile);
  }, [imageFile]);

  useEffect(() => {
    return () => {
      if (imagePreviewUrl) URL.revokeObjectURL(imagePreviewUrl);
    };
  }, [imagePreviewUrl]);

  return (
    <div className="admin-page">
      <div className="admin-card">
        <header className="admin-header">
          <h1>Admin: Upload Device (System KB)</h1>
          <p>
            Upload a device manual (PDF) and an optional device picture. The backend will ingest
            the manual using the <code>system</code> user and create embeddings in the background.
          </p>
        </header>

        <form className="admin-form" onSubmit={handleSubmit}>
          <label className="field">
            <span>Admin Token (optional)</span>
            <input
              value={adminToken}
              onChange={(e) => setAdminToken(e.target.value)}
              placeholder="x-admin-token"
              disabled={loading}
            />
          </label>

          <div className="grid2">
            <label className="field">
              <span>Brand</span>
              <input
                value={formData.brand}
                onChange={(e) => updateField("brand", e.target.value)}
                placeholder="Boss"
                required
                disabled={loading}
              />
            </label>

            <label className="field">
              <span>Model</span>
              <input
                value={formData.model}
                onChange={(e) => updateField("model", e.target.value)}
                placeholder="GT-1"
                required
                disabled={loading}
              />
            </label>
          </div>

          <label className="field">
            <span>Variant (optional)</span>
            <input
              value={formData.variant}
              onChange={(e) => updateField("variant", e.target.value)}
              placeholder="FW 1.3 / MkII / Pro"
              disabled={loading}
            />
          </label>

          {/* Source type — drives pipeline routing on backend */}
          <label className="field">
            <span>Document Type</span>
            <select
              value={formData.source_type}
              onChange={(e) => updateField("source_type", e.target.value)}
              disabled={loading}
            >
              {SOURCE_TYPE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </label>

          {/* Device capability flags */}
          <div className="field">
            <span>Device Capabilities</span>
            <div className="checkbox-group">
              <label className="checkbox-item">
                <input
                  type="checkbox"
                  checked={formData.supports_midi}
                  onChange={(e) => updateField("supports_midi", e.target.checked)}
                  disabled={loading}
                />
                <span>Supports MIDI</span>
                <small>Enables MIDI CC/PC/Bank extraction pipeline after ingestion</small>
              </label>

              <label className="checkbox-item">
                <input
                  type="checkbox"
                  checked={formData.supports_snapshots}
                  onChange={(e) => updateField("supports_snapshots", e.target.checked)}
                  disabled={loading}
                />
                <span>Supports Snapshots</span>
                <small>Device has a snapshot/scene system (e.g. Helix snapshots)</small>
              </label>

              <label className="checkbox-item">
                <input
                  type="checkbox"
                  checked={formData.supports_command_center}
                  onChange={(e) => updateField("supports_command_center", e.target.checked)}
                  disabled={loading}
                />
                <span>Supports Command Center</span>
                <small>Device has a Command Center or MIDI assign feature</small>
              </label>
            </div>
          </div>

          {/* Device image (optional) */}
          <div
            className={`dropzone ${loading ? "disabled" : ""}`}
            role="button"
            tabIndex={0}
            onClick={pickImage}
            onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") pickImage(); }}
          >
            <div className="dz-title">Device Picture (optional)</div>
            <div className="dz-sub">
              {imageFile ? (
                <>
                  <strong>{imageFile.name}</strong>{" "}
                  <span className="muted">({(imageFile.size / 1024 / 1024).toFixed(2)} MB)</span>
                </>
              ) : (
                "Click to select an image (png/jpg/webp)"
              )}
            </div>
            {imagePreviewUrl && <img className="preview" src={imagePreviewUrl} alt="device preview" />}
            <input
              ref={imageInputRef}
              type="file"
              hidden
              accept="image/*"
              onChange={(e) => setImageFile(e.target.files?.[0] ?? null)}
            />
          </div>

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
            {loading ? "Uploading…" : "Submit (Index in Background)"}
          </button>

          <div className="hint">
            After upload, you will be redirected to the admin home page where you can monitor
            ingestion progress and upload additional PDFs for the same device.
          </div>
        </form>
      </div>
    </div>
  );
}