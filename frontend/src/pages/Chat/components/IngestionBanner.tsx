// src/pages/Chat/IngestionBanner.tsx
import React, { useMemo, useState } from "react";
import type { IngestionJob } from "../../hooks/useIngestionJob";

type Props = {
  job: IngestionJob | null;
};

export default function IngestionBanner({ job }: Props) {
  const [hidden, setHidden] = useState(false);

  const enrichTotal = Number(job?.enrichment_total || 0);
  const enrichDone = Number(job?.enrichment_done || 0);

  const enrichPct = useMemo(() => {
    if (!enrichTotal) return 0;
    return Math.max(0, Math.min(100, Math.round((enrichDone / enrichTotal) * 100)));
  }, [enrichDone, enrichTotal]);

  const isEnrichRunning =
    job?.enrichment_status === "RUNNING" || job?.enrichment_status === "PENDING";
  const isEnrichFailed = job?.enrichment_status === "FAILED";

  if (hidden || !job) return null;

  // 1) 失敗狀態 (使用一致的 CSS 類名)
  if (job.status === "FAILED") {
    return (
      <div className="ingestion-banner-container ingestion-failed" style={{ backgroundColor: '#fee2e2', borderColor: '#ef4444' }}>
        <div className="ingestion-banner-title" style={{ color: '#b91c1c' }}>❌ Manual ingestion failed</div>
        <div style={{ fontSize: '14px', color: '#b91c1c' }}>{job.error ? job.error : "Unknown error"}</div>
        <button className="ingestion-close" onClick={() => setHidden(true)} style={{ position: 'absolute', top: '10px', right: '10px', border: 'none', background: 'none', cursor: 'pointer' }}>×</button>
      </div>
    );
  }

  // 2) READY 狀態 (對應你照片中的紅框 2)
  if (job.status === "READY") {
    return (
      <div className="ingestion-banner-container" style={{ position: 'relative', backgroundColor: '#ecfdf5', border: '1px solid #10b981', padding: '16px', borderRadius: '12px', marginBottom: '20px' }}>
        <div className="ingestion-banner-title" style={{ color: '#065f46', fontWeight: '700', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          ✅ Manual is ready
        </div>
        <div style={{ fontSize: '14px', color: '#065f46' }}>
          {isEnrichFailed 
            ? "Effects extraction failed (non-blocking). You can still ask questions."
            : isEnrichRunning 
            ? `Extracting effects… ${enrichDone}/${enrichTotal} (${enrichPct}%)`
            : "You can ask questions about your device manual now."
          }
        </div>
        <button onClick={() => setHidden(true)} style={{ position: 'absolute', top: '12px', right: '12px', border: 'none', background: 'none', cursor: 'pointer', fontSize: '18px', color: '#065f46' }}>×</button>
        
        {isEnrichRunning && (
          <div style={{ height: '6px', background: '#d1fae5', borderRadius: '3px', marginTop: '10px', overflow: 'hidden' }}>
            <div style={{ width: `${enrichPct}%`, height: '100%', background: '#10b981', transition: 'width 0.3s' }} />
          </div>
        )}
      </div>
    );
  }

  // 3) RUNNING 狀態
  const pct = Math.max(0, Math.min(100, Number(job.progress || 0)));
  return (
    <div className="ingestion-banner-container" style={{ backgroundColor: '#eff6ff', border: '1px solid #3b82f6', padding: '16px', borderRadius: '12px', marginBottom: '20px' }}>
      <div className="ingestion-banner-title" style={{ color: '#1d4ed8', fontWeight: '700' }}>
        {job.stage === "CHUNKING" ? "Reading manual..." : "Indexing manual..."}
      </div>
      <div style={{ fontSize: '14px', color: '#1d4ed8' }}>Chat is available, but accuracy is improving...</div>
      <div style={{ height: '6px', background: '#dbeafe', borderRadius: '3px', marginTop: '10px', overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: '#3b82f6', transition: 'width 0.3s' }} />
      </div>
    </div>
  );
}