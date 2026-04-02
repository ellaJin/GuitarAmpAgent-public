// src/hooks/useIngestionJob.ts
import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "../lib/api";

export type JobStatus = "PENDING" | "RUNNING" | "READY" | "FAILED";
export type EnrichmentStatus = "PENDING" | "RUNNING" | "DONE" | "FAILED" | string;

export type IngestionJob = {
  id: string;
  status: JobStatus;
  stage: string;
  progress: number;
  error?: string | null;
  kb_source_id?: string;
  document_id?: string;

  // effects enrichment
  enrichment_status?: EnrichmentStatus | null;
  enrichment_total?: number | null;
  enrichment_done?: number | null;

  // MIDI enrichment — independent of effect enrichment
  midi_enrichment_status?: string | null;
  midi_enrichment_total?: number | null;
};

type UseIngestionJobOptions = {
  pollMs?: number;            // 轮询间隔，默认 1500ms
  stopOnTerminal?: boolean;   // 是否在“真正结束”后停止轮询（默认 true）
  enabled?: boolean;          // 是否启用
};

/**
 * useIngestionJob
 *
 * - 轮询 GET /jobs/{jobId}
 * - “真正结束”定义：
 *    - job.status === FAILED 直接结束
 *    - job.status === READY 且 enrichment_status 是 DONE/FAILED（或 total=0 且 DONE）才结束
 * - 这样 READY 后 enrichment 仍会继续更新进度
 */
export function useIngestionJob(
  jobId?: string | null,
  options: UseIngestionJobOptions = {}
) {
  const {
    pollMs = 5000,
    stopOnTerminal = true,
    enabled = true,
  } = options;

  const [job, setJob] = useState<IngestionJob | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const timerRef = useRef<number | null>(null);

  const canRun = useMemo(
    () => Boolean(enabled && jobId),
    [enabled, jobId]
  );

  const shouldStop = (data: IngestionJob) => {
    if (!stopOnTerminal) return false;

    // 主流程失败：直接停止
    if (data.status === "FAILED") return true;

    // READY：manual 可用，但 enrichment 可能还在跑
    if (data.status === "READY") {
      const es = data.enrichment_status;
      // enrichment 明确结束（DONE/FAILED）才停止
      if (es === "DONE" || es === "FAILED") return true;

      // 没有 enrichment 字段/还没初始化：不要停（兼容旧后端）
      return false;
    }

    // RUNNING/PENDING：继续轮询
    return false;
  };

  const clearTimer = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  const refresh = async () => {
    if (!jobId) return;
    setLoading(true);
    setError(null);

    try {
      const { data } = await api.get<IngestionJob>(`/jobs/${jobId}`);
      setJob(data);

      if (shouldStop(data)) {
        clearTimer();
      }
    } catch (e: any) {
      // 网络错误：不一定要永久停轮询，但你现在的策略是停掉 + 提示
      clearTimer();
      setError("Failed to fetch ingestion job status");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!canRun) return;

    refresh();
    timerRef.current = window.setInterval(refresh, pollMs);

    return () => {
      clearTimer();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [canRun, pollMs]);

  return {
    job,
    loading,
    error,
    refresh,
  };
}
