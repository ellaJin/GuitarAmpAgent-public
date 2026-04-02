// src/pages/Admin/AdminHome/AdminHome.tsx
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAdminHome, type Device, type KbSource } from "./useAdminHome";
import { useAdminIngestionJob } from "../../../hooks/useAdminIngestionJob";
import "./AdminHome.css";

const SOURCE_TYPE_LABEL: Record<string, string> = {
  effects_settings: "Effects Settings",
  mixed: "Mixed",
  user_manual: "User Manual",
};

const STATUS_ICON: Record<string, string> = {
  READY: "✅",
  RUNNING: "🔄",
  PENDING: "⏳",
  FAILED: "❌",
  SKIPPED: "⏭️",
  DONE: "✅",
};

// ---- SourceRow ----

type SourceRowProps = {
  source: KbSource;
  showMidi: boolean;
  onUnlink: (kbSourceId: string) => void;
  actionsDisabled: boolean;
};

function SourceRow({
  source,
  showMidi,
  onUnlink,
  actionsDisabled,
}: SourceRowProps) {
  const { job } = useAdminIngestionJob(source.job_id || null, {
    enabled:
      !!source.job_id &&
      source.job_status !== "READY" &&
      source.job_status !== "FAILED",
  });

  const [confirmingUnlink, setConfirmingUnlink] = useState(false);

  // Use live job data if available, fallback to static data from list API
  const status = job?.status ?? source.job_status;
  const enrichStatus = job?.enrichment_status ?? source.enrichment_status;
  const enrichTotal = Number(job?.enrichment_total ?? 0);
  const enrichDone = Number(job?.enrichment_done ?? 0);
  const progress = Number(job?.progress ?? 0);
  const midiStatus = job?.midi_enrichment_status ?? source.midi_enrichment_status;

  const typeLabel =
    SOURCE_TYPE_LABEL[source.source_type] ?? source.source_type;
  const enrichPct = enrichTotal ? Math.round((enrichDone / enrichTotal) * 100) : 0;

  const handleUnlinkClick = () => {
    if (actionsDisabled) return;
    setConfirmingUnlink(true);
  };

  const handleUnlinkConfirm = () => {
    setConfirmingUnlink(false);
    onUnlink(source.kb_source_id);
  };

  const handleUnlinkCancel = () => {
    setConfirmingUnlink(false);
  };

  return (
    <div className={`source-row${showMidi ? " source-row--midi" : ""}`}>
      <div className="source-title-wrap">
        <span className="source-title">{source.title}</span>

        <div className="source-meta">
          <span className="source-file">{source.file_name || "—"}</span>
          <span className="dot">•</span>
          <span className="source-created">{source.created_at}</span>

          <span className="dot">•</span>
          <div className="source-actions">
            {confirmingUnlink ? (
              <>
                <span className="source-unlink-confirm-label">Remove?</span>
                <button
                  className="btn-mini danger"
                  type="button"
                  onClick={handleUnlinkConfirm}
                >
                  Yes
                </button>
                <button
                  className="btn-mini"
                  type="button"
                  onClick={handleUnlinkCancel}
                >
                  No
                </button>
              </>
            ) : (
              <button
                className="btn-mini danger"
                type="button"
                onClick={handleUnlinkClick}
                disabled={actionsDisabled}
                title="Remove this document and all its data"
              >
                Unlink
              </button>
            )}
          </div>
        </div>
      </div>

      <span className="source-type">{typeLabel}</span>

      {/* Main ingestion status */}
      <div className="source-status">
        <span>
          {STATUS_ICON[status] ?? "❓"} {status}
        </span>
        {status === "RUNNING" && (
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
        )}
      </div>

      {/* Effect extraction status */}
      <div className="source-enrichment">
        <span>
          {STATUS_ICON[enrichStatus] ?? "❓"} {enrichStatus}
        </span>
        {enrichStatus === "RUNNING" && enrichTotal > 0 && (
          <div className="progress-bar">
            <div
              className="progress-fill enrichment"
              style={{ width: `${enrichPct}%` }}
            />
          </div>
        )}
      </div>

      {/* MIDI extraction status — only rendered when device supports MIDI */}
      {showMidi && (
        <div className="source-midi-status">
          <span>{STATUS_ICON[midiStatus] ?? "❓"} {midiStatus}</span>
        </div>
      )}
    </div>
  );
}

// ---- DeviceCard ----

type DeviceCardProps = {
  device: Device;
  onAdd: (deviceModelId: string, deviceName: string) => void;
  onUnlink: (deviceModelId: string, kbSourceId: string) => void;
  actionsDisabled: boolean;
};

function DeviceCard({ device, onAdd, onUnlink, actionsDisabled }: DeviceCardProps) {
  const name = [device.brand, device.model, device.variant]
    .filter(Boolean)
    .join(" ");

  const badges = [
    { key: "supports_midi", label: "MIDI", on: device.supports_midi },
    { key: "supports_snapshots", label: "Snapshots", on: device.supports_snapshots },
    { key: "supports_command_center", label: "Command Center", on: device.supports_command_center },
  ].filter((b) => b.on);

  return (
    <div className="device-card">
      <div className="device-header">
        <div className="device-name">{name}</div>
        <button
          className="btn-mini"
          type="button"
          onClick={() => onAdd(device.device_model_id, name)}
          disabled={actionsDisabled}
          title="Upload another PDF for this device"
        >
          + Add Document
        </button>
      </div>

      <div className="device-meta">
        <div className="device-meta-line">
          <span className="device-meta-item">
            <span className="device-meta-label">Source:</span> {device.source || "—"}
          </span>
          <span className="dot">•</span>
          <span className="device-meta-item">
            <span className="device-meta-label">Public:</span>{" "}
            {device.is_public ? "true" : "false"}
          </span>
          <span className="dot">•</span>
          <span className="device-meta-item">
            <span className="device-meta-label">Created:</span>{" "}
            {device.created_at}
          </span>
        </div>

        {badges.length > 0 && (
          <div className="device-badges">
            {badges.map((b) => (
              <span key={b.key} className="cap-badge">
                {b.label}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className={`source-list-header${device.supports_midi ? " source-list-header--midi" : ""}`}>
        <span>Document</span>
        <span>Type</span>
        <span>Ingestion</span>
        <span>Effects</span>
        {device.supports_midi && <span>MIDI</span>}
      </div>

      <div className="source-list">
        {device.sources.length === 0 ? (
          <div className="no-sources">No documents linked.</div>
        ) : (
          device.sources.map((s) => (
            <SourceRow
              key={s.kb_source_id}
              source={s}
              showMidi={device.supports_midi}
              onUnlink={(kbSourceId) => onUnlink(device.device_model_id, kbSourceId)}
              actionsDisabled={actionsDisabled}
            />
          ))
        )}
      </div>
    </div>
  );
}

// ---- AdminHome ----

export default function AdminHome() {
  const nav = useNavigate();
  const {
    devices,
    loading,
    error,
    refetch,
    adminToken,
    setAdminToken,
    unlinkSource,
    unlinkLoading,
    unlinkError,
  } = useAdminHome();

  const handleAdd = (deviceModelId: string, deviceName: string) => {
    nav(`/admin/add-document/${deviceModelId}`, {
      state: { deviceName },
    });
  };

  const handleUnlink = async (deviceModelId: string, kbSourceId: string) => {
    await unlinkSource(deviceModelId, kbSourceId);
  };

  const actionsDisabled = loading || unlinkLoading;

  return (
    <div className="admin-page">
      <div className="admin-card">
        <header className="admin-header">
          <h1>Admin Home</h1>
          <p>Manage system devices and monitor ingestion progress.</p>
        </header>

        {/* Admin token field — persisted to localStorage */}
        <div className="admin-token-row">
          <label className="admin-token-label">Admin Token</label>
          <input
            className="admin-token-input"
            type="password"
            value={adminToken}
            onChange={(e) => setAdminToken(e.target.value)}
            placeholder="x-admin-token (optional)"
          />
        </div>

        <div className="admin-actions">
          <button className="primary" onClick={() => nav("/admin/device")}>
            + Upload New Device PDF
          </button>
          <button className="secondary" onClick={refetch} disabled={loading}>
            {loading ? "Refreshing…" : "Refresh"}
          </button>
        </div>

        {error && <div className="error-msg">{error}</div>}
        {unlinkError && <div className="error-msg">{unlinkError}</div>}

        {!loading && devices.length === 0 && (
          <div className="empty-msg">No devices uploaded yet.</div>
        )}

        <div className="device-list">
          {devices.map((d) => (
            <DeviceCard
              key={d.device_model_id}
              device={d}
              onAdd={handleAdd}
              onUnlink={handleUnlink}
              actionsDisabled={actionsDisabled}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
