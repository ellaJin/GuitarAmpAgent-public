// src/pages/Admin/Eval/EvalPage.tsx
import { useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useEvalPage } from "./useEvalPage";
import "../AdminHome/AdminHome.css";
import "./EvalPage.css";

function ScoreCard({
  label,
  value,
  composite,
}: {
  label: string;
  value: number | null;
  composite?: boolean;
}) {
  const display =
    value !== null && value !== undefined ? value.toFixed(3) : "N/A";
  const isNa = value === null || value === undefined;
  return (
    <div className={`eval-card${composite ? " composite" : ""}`}>
      <span className={`eval-score${isNa ? " na" : ""}`}>{display}</span>
      <span className="eval-label">{label}</span>
    </div>
  );
}

function fmt(val: number | null): string {
  return val !== null && val !== undefined ? val.toFixed(3) : "N/A";
}

export default function EvalPage() {
  const nav = useNavigate();
  const {
    adminToken,
    setAdminToken,
    devices,
    devicesLoading,
    devicesError,
    selectedDeviceModelId,
    setSelectedDeviceModelId,
    inputMode,
    setInputMode,
    questionFile,
    setQuestionFile,
    questionText,
    setQuestionText,
    loading,
    error,
    result,
    handleRun,
    downloadCsv,
  } = useEvalPage();

  const fileInputRef = useRef<HTMLInputElement>(null);
  const pickFile = () => {
    if (!loading) fileInputRef.current?.click();
  };

  // One option per device, keyed by device_model_id
  const deviceOptions: { value: string; label: string }[] = devices.map((d) => ({
    value: d.device_model_id,
    label: [d.brand, d.model, d.variant].filter(Boolean).join(" "),
  }));

  return (
    <div className="admin-page">
      <div className="admin-card">
        <button className="eval-back" onClick={() => nav("/admin")}>
          ← Back to Admin
        </button>

        <header className="admin-header">
          <h1>RAG Eval</h1>
          <p>
            Select a knowledge base source, provide a question set, and run a
            RAGAS evaluation to measure Faithfulness, Answer Relevancy, and
            Context Precision.
          </p>
        </header>

        {/* Admin token */}
        <div className="admin-token-row">
          <label className="admin-token-label">Admin Token</label>
          <input
            className="admin-token-input"
            type="password"
            value={adminToken}
            onChange={(e) => setAdminToken(e.target.value)}
            placeholder="x-admin-token (optional)"
            disabled={loading}
          />
        </div>

        {/* Device selector */}
        <label className="field-label">Device</label>
        {devicesError && <div className="error-msg">{devicesError}</div>}
        <select
          className="eval-select"
          value={selectedDeviceModelId}
          onChange={(e) => setSelectedDeviceModelId(e.target.value)}
          disabled={loading || devicesLoading}
        >
          <option value="">
            {devicesLoading ? "Loading devices…" : "— Select a device —"}
          </option>
          {deviceOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>

        {/* Question set input — Upload / Paste tabs */}
        <label className="field-label">Question Set</label>
        <div className="eval-tabs">
          <button
            className={`eval-tab${inputMode === "paste" ? " active" : ""}`}
            onClick={() => setInputMode("paste")}
            disabled={loading}
          >
            Paste JSON
          </button>
          <button
            className={`eval-tab${inputMode === "upload" ? " active" : ""}`}
            onClick={() => setInputMode("upload")}
            disabled={loading}
          >
            Upload JSON File
          </button>
        </div>

        {inputMode === "paste" ? (
          <>
            <textarea
              className="eval-textarea"
              value={questionText}
              onChange={(e) => setQuestionText(e.target.value)}
              placeholder='[{"question": "How do I calibrate the pedal?", "ground_truth": "Choose MENU > PDL CALIBRATION…"}, …]'
              disabled={loading}
            />
          </>
        ) : (
          <>
            <div
              className={`eval-dropzone${loading ? " disabled" : ""}`}
              role="button"
              tabIndex={0}
              onClick={pickFile}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") pickFile();
              }}
            >
              <div className="eval-dz-title">
                {questionFile ? questionFile.name : "Click to select a JSON file"}
              </div>
              <div className="eval-dz-sub">
                {questionFile
                  ? `${(questionFile.size / 1024).toFixed(1)} KB`
                  : "Accepts .json files"}
              </div>
              <input
                ref={fileInputRef}
                type="file"
                hidden
                accept=".json,application/json"
                onChange={(e) => setQuestionFile(e.target.files?.[0] ?? null)}
              />
            </div>
          </>
        )}

        <div className="eval-hint">
          Expected format:{" "}
          <code>
            {"[{\"question\": \"…\", \"ground_truth\": \"…\"}, …]"}
          </code>
          <br />
          <code>ground_truth</code> is optional — Context Precision will show{" "}
          <code>N/A</code> when omitted.
        </div>

        {/* Run button */}
        <div className="admin-actions" style={{ marginTop: 20 }}>
          <button
            className="primary"
            onClick={handleRun}
            disabled={loading || !selectedDeviceModelId}
          >
            {loading ? "Evaluating…" : "Run Evaluation"}
          </button>
        </div>

        {error && <div className="error-msg">{error}</div>}

        {loading && (
          <div className="eval-loading">
            Running RAGAS evaluation — this may take a minute…
          </div>
        )}

        {/* Results */}
        {result && !loading && (
          <>
            <div className="eval-section-title">Summary</div>
            <div className="eval-grid">
              <ScoreCard
                label="Faithfulness"
                value={result.summary.faithfulness}
              />
              <ScoreCard
                label="Answer Relevancy"
                value={result.summary.answer_relevancy}
              />
              <ScoreCard
                label="Context Precision"
                value={result.summary.context_precision}
              />
              <ScoreCard
                label="Composite Score"
                value={result.summary.composite_score}
                composite
              />
            </div>

            <div className="eval-section-title">Per-Question Results</div>
            <div className="eval-actions-row">
              <button className="btn-mini" onClick={downloadCsv}>
                Download CSV
              </button>
            </div>
            <div className="eval-table-wrap">
              <table className="eval-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Question</th>
                    <th>Faithfulness</th>
                    <th>Answer Relevancy</th>
                    <th>Context Precision</th>
                    <th>Answer</th>
                  </tr>
                </thead>
                <tbody>
                  {result.rows.map((row, i) => (
                    <tr key={i}>
                      <td className="num">{i + 1}</td>
                      <td className="question-cell">
                        <div className="eval-cell-text">{row.question}</div>
                      </td>
                      <td className="num">{fmt(row.faithfulness)}</td>
                      <td className="num">{fmt(row.answer_relevancy)}</td>
                      <td className="num">
                        {row.has_ground_truth
                          ? fmt(row.context_precision)
                          : "N/A"}
                      </td>
                      <td className="answer-cell">
                        <div className="eval-cell-text">{row.answer}</div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
