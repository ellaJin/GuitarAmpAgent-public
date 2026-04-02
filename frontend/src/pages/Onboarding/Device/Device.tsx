// src/pages/Onboarding/Device/Device.tsx
import React, { useMemo, useState } from "react";
import "./Device.css";
import { useDevice } from "./useDevice";

export default function Device() {
  const {
    loading,
    showForm,
    setShowForm,
    formData,
    updateField,
    handleActivate,
    brands,
    modelsByBrand,
    error,
    selectedDeviceImageUrl,
    isAddMode,
  } = useDevice();

  const [useCustomBrand, setUseCustomBrand] = useState(false);
  const [useCustomModel, setUseCustomModel] = useState(false);

  const selectedBrand = formData.brand;
  const brandModels = useMemo(
    () => modelsByBrand[selectedBrand] || [],
    [modelsByBrand, selectedBrand]
  );

  const pickBrand = (b: string) => {
    updateField("brand", b);
    updateField("model", ""); // reset model when brand changes
    setUseCustomBrand(false);
    setUseCustomModel(false);
  };

  const pickModel = (m: string) => {
    updateField("model", m);
    setUseCustomModel(false);
  };

  return (
    <div className="onboarding-page">
      <div className="onboarding-card">
        {!showForm ? (
          <div className="step-welcome">
            <div className="icon-badge">
              <span role="img" aria-label="tools">
                🛠️
              </span>
            </div>

            <h1 className="onboarding-title">
              {isAddMode ? "Add a Device" : "Activate your device"}
            </h1>

            <p className="onboarding-subtitle">
              Choose your device brand and model to continue.
            </p>

            <button
              className="primary-action-btn"
              onClick={() => setShowForm(true)}
              disabled={loading}
            >
              Get started
            </button>

            <div className="onboarding-help">
              Having trouble? <a href="/support">Visit the Help Center</a>
            </div>
          </div>
        ) : (
          <div className="step-split">
            {/* LEFT: options + inputs */}
            <div className="step-form">
              <h2 className="onboarding-title">Enter device details</h2>
              <p className="onboarding-subtitle">
                Pick a popular option or type your own.
              </p>

              <form className="modern-form" onSubmit={handleActivate}>
                {/* BRAND OPTIONS */}
                <div className="field-block">
                  <div className="field-label-row">
                    <span className="field-label">Brand</span>
                    <button
                      type="button"
                      className="mini-link"
                      onClick={() => setUseCustomBrand((v) => !v)}
                      disabled={loading}
                    >
                      {useCustomBrand ? "Use options" : "Type instead"}
                    </button>
                  </div>

                  {!useCustomBrand ? (
                    <div className="pill-row">
                      {brands.map((b) => (
                        <button
                          key={b}
                          type="button"
                          className={`pill ${selectedBrand === b ? "pill--active" : ""}`}
                          onClick={() => pickBrand(b)}
                          disabled={loading}
                        >
                          {b}
                        </button>
                      ))}
                      <button
                        type="button"
                        className={`pill ${useCustomBrand ? "pill--active" : ""}`}
                        onClick={() => {
                          setUseCustomBrand(true);
                          updateField("brand", "");
                          updateField("model", "");
                          setUseCustomModel(true);
                        }}
                        disabled={loading}
                      >
                        Other
                      </button>
                    </div>
                  ) : (
                    <div className="input-group">
                      <input
                        placeholder="Type brand (e.g., Headrush)"
                        value={formData.brand}
                        onChange={(e) => {
                          updateField("brand", e.target.value);
                          updateField("model", "");
                        }}
                        required
                        disabled={loading}
                      />
                    </div>
                  )}
                </div>

                {/* MODEL OPTIONS */}
                <div className="field-block">
                  <div className="field-label-row">
                    <span className="field-label">Model</span>
                    <button
                      type="button"
                      className="mini-link"
                      onClick={() => setUseCustomModel((v) => !v)}
                      disabled={loading}
                    >
                      {useCustomModel ? "Use options" : "Type instead"}
                    </button>
                  </div>

                  {!useCustomModel && brandModels.length > 0 ? (
                    <div className="pill-row">
                      {brandModels.map((m) => (
                        <button
                          key={m}
                          type="button"
                          className={`pill ${formData.model === m ? "pill--active" : ""}`}
                          onClick={() => pickModel(m)}
                          disabled={loading}
                        >
                          {m}
                        </button>
                      ))}
                      <button
                        type="button"
                        className={`pill ${useCustomModel ? "pill--active" : ""}`}
                        onClick={() => {
                          setUseCustomModel(true);
                          updateField("model", "");
                        }}
                        disabled={loading}
                      >
                        Other
                      </button>
                    </div>
                  ) : (
                    <div className="input-group">
                      <input
                        placeholder="Type model (e.g., Quad Cortex)"
                        value={formData.model}
                        onChange={(e) => updateField("model", e.target.value)}
                        required
                        disabled={loading}
                      />
                      {brandModels.length === 0 && !useCustomBrand && (
                        <div className="hint-text">
                          Pick a popular brand to see model options, or type a custom model.
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {error && <div className="form-error">{error}</div>}

                <button className="primary-action-btn" type="submit" disabled={loading}>
                  {loading ? "Saving..." : isAddMode ? "Add to My Devices" : "Save and Start to Chat"}
                </button>

                <button
                  className="text-link-btn"
                  type="button"
                  onClick={() => setShowForm(false)}
                  disabled={loading}
                >
                  Back
                </button>
              </form>
            </div>

            {/* RIGHT: preview */}
            <div className="preview-panel" aria-live="polite">
              {selectedDeviceImageUrl ? (
                <div className="device-preview">
                  <img
                    className="device-image"
                    src={selectedDeviceImageUrl}
                    alt={`${formData.brand} ${formData.model}`}
                  />
                  <div className="device-meta">
                    <div className="device-name">{formData.brand}</div>
                    <div className="device-model">{formData.model}</div>
                  </div>
                </div>
              ) : (
                <div className="device-preview device-preview--empty">
                  <div className="device-empty-icon">🎸</div>
                  <div className="device-empty-title">Select a supported device</div>
                  <div className="device-empty-subtitle">
                    Choose one of the popular Brand + Model options to show a preview on the right.
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}