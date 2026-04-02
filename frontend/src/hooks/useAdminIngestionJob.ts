// src/hooks/useAdminIngestionJob.ts
import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "../lib/api";
import type { IngestionJob } from "./useIngestionJob";

type Options = {
  pollMs?: number;
  stopOnTerminal?: boolean;
  enabled?: boolean;
};

export function useAdminIngestionJob(
  jobId?: string | null,
  options: Options = {}
) {
  const { pollMs = 3000, stopOnTerminal = true, enabled = true } = options;

  const [job, setJob] = useState<IngestionJob | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<number | null>(null);

  const canRun = useMemo(() => Boolean(enabled && jobId), [enabled, jobId]);

  const shouldStop = (data: IngestionJob) => {
    if (!stopOnTerminal) return false;
    if (data.status === "FAILED") return true;
    if (data.status === "READY") {
      // Effects must be terminal first (unchanged)
      const es = data.enrichment_status;
      if (es !== "DONE" && es !== "FAILED" && es !== "SKIPPED") return false;

      // If MIDI tracking is in progress, keep polling until it settles.
      // null/undefined means no MIDI tracking (old records) → stop normally.
      const ms = data.midi_enrichment_status;
      if (ms === "RUNNING" || ms === "PENDING") return false;

      return true;
    }
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
    try {
      // Points to admin job endpoint — no login token required
      const { data } = await api.get<IngestionJob>(`/admin/devices/jobs/${jobId}`);
      setJob(data);
      if (shouldStop(data)) clearTimer();
    } catch (e: any) {
      clearTimer();
      setError("Failed to fetch job status");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!canRun) return;
    refresh();
    timerRef.current = window.setInterval(refresh, pollMs);
    return () => clearTimer();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [canRun, pollMs]);

  return { job, loading, error, refresh };
}