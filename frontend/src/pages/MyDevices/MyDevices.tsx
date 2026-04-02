// src/pages/MyDevices/MyDevices.tsx
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./MyDevices.css";
import { useMyDevices, type UserDevice } from "./useMyDevices";

export default function MyDevices() {
  const navigate = useNavigate();
  const { devices, loading, activating, activateDevice, resolveImageUrl } = useMyDevices();

  // Tracks which card is showing the inline confirmation
  const [confirmingId, setConfirmingId] = useState<string | null>(null);

  const activeDevice = devices.find((d) => d.is_active);

  const handleActivateClick = (userDeviceId: string) => {
    setConfirmingId(userDeviceId);
  };

  const handleConfirmYes = async (userDeviceId: string) => {
    setConfirmingId(null);
    await activateDevice(userDeviceId);
  };

  const handleConfirmNo = () => {
    setConfirmingId(null);
  };

  const deviceDisplayName = (d: UserDevice) =>
    [d.brand, d.model, d.variant].filter(Boolean).join(" ");

  return (
    <div className="mydevices-root">
      <div className="mydevices-header">
        <span className="mydevices-title">My Devices</span>
        <div className="mydevices-header-actions">
          <button
            className="mydevices-add-btn"
            type="button"
            onClick={() => navigate("/onboarding/device?from=devices")}
          >
            + Add Device
          </button>
          <button
            className="mydevices-back-btn"
            type="button"
            onClick={() => navigate("/chat")}
          >
            ← Back to Chat
          </button>
        </div>
      </div>

      {loading && <div className="mydevices-empty">Loading...</div>}

      {!loading && devices.length === 0 && (
        <div className="mydevices-empty">
          No devices yet. Click "+ Add Device" to bind your first device.
        </div>
      )}

      {!loading && devices.length > 0 && (
        <div className="mydevices-grid">
          {devices.map((device) => {
            const imageUrl = resolveImageUrl(device.image_url);
            const isConfirming = confirmingId === device.user_device_id;
            const isActivating = activating === device.user_device_id;

            return (
              <div
                key={device.user_device_id}
                className={`device-card-user${device.is_active ? " is-active" : ""}`}
              >
                {device.is_active && (
                  <span className="device-active-badge">Active</span>
                )}

                {/* Image or placeholder */}
                {imageUrl ? (
                  <img
                    className="device-card-image"
                    src={imageUrl}
                    alt={deviceDisplayName(device)}
                  />
                ) : (
                  <div className="device-card-image-placeholder">🎸</div>
                )}

                {/* Info */}
                <div className="device-card-info">
                  <div className="device-card-brand">{device.brand}</div>
                  <div className="device-card-model">{device.model}</div>
                  {device.variant && (
                    <div className="device-card-variant">{device.variant}</div>
                  )}
                </div>

                {/* Actions — only for non-active devices */}
                {!device.is_active && (
                  <div className="device-card-actions">
                    {isConfirming ? (
                      <div className="device-confirm-row">
                        <span className="device-confirm-label">
                          Switch active device to{" "}
                          <strong>{deviceDisplayName(device)}</strong>?
                          {activeDevice && (
                            <><br />Current: <strong>{deviceDisplayName(activeDevice)}</strong></>
                          )}
                        </span>
                        <div className="device-confirm-btns">
                          <button
                            className="device-confirm-yes"
                            type="button"
                            onClick={() => handleConfirmYes(device.user_device_id)}
                            disabled={isActivating}
                          >
                            {isActivating ? "Switching..." : "Yes"}
                          </button>
                          <button
                            className="device-confirm-no"
                            type="button"
                            onClick={handleConfirmNo}
                          >
                            No
                          </button>
                        </div>
                      </div>
                    ) : (
                      <button
                        className="device-activate-btn"
                        type="button"
                        onClick={() => handleActivateClick(device.user_device_id)}
                        disabled={!!activating}
                      >
                        Activate
                      </button>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
