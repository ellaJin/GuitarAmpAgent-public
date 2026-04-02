// src/pages/Admin/AdminHome/useAdminHome.ts
import { useState, useEffect, useCallback } from "react";
import { api } from "../../../lib/api";

const ADMIN_TOKEN_KEY = "admin_token";

/**
 * Represents one bound document (kb_source) for a device.
 * Each device can have multiple kb_sources.
 */
export type KbSource = {
  kb_source_id: string;

  // Core document info
  source_type: string;   // mixed / effects_settings / user_manual
  title: string;         // kb_sources.name
  file_name: string;     // from documents table
  created_at: string;

  // Flags (useful for admin and future unlink)
  is_active: boolean;
  is_public: boolean;

  // Latest ingestion job info
  job_id: string;
  job_status: string;
  job_stage: string;
  job_progress: number;
  job_error: string;

  // Effect extraction / enrichment
  enrichment_status: string;
  enrichment_total: number;
  enrichment_done: number;

  // MIDI enrichment — independent of effect enrichment
  midi_enrichment_status: string;
  midi_enrichment_total: number;
};

/**
 * Represents a device (device_models row).
 * This is the main entity in AdminHome.
 */
export type Device = {
  device_model_id: string;

  brand: string;
  model: string;
  variant: string | null;

  // Device metadata
  source: string;
  is_public: boolean;
  created_at: string;

  // Capability flags
  supports_midi: boolean;
  supports_snapshots: boolean;
  supports_command_center: boolean;

  // Bound documents
  sources: KbSource[];
};

export const useAdminHome = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Admin token — persisted to localStorage so it survives navigation
  const [adminToken, setAdminTokenState] = useState<string>(
    () => localStorage.getItem(ADMIN_TOKEN_KEY) ?? ""
  );

  const setAdminToken = useCallback((token: string) => {
    setAdminTokenState(token);
    localStorage.setItem(ADMIN_TOKEN_KEY, token);
  }, []);

  const fetchDevices = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get("/admin/devices/");
      setDevices(res.data ?? []);
    } catch (err: any) {
      console.error("Failed to load devices:", err);
      setError(err?.response?.data?.detail ?? "Failed to load devices.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDevices();
  }, [fetchDevices]);

  // ---- Unlink ----
  const [unlinkLoading, setUnlinkLoading] = useState(false);
  const [unlinkError, setUnlinkError] = useState<string | null>(null);

  const unlinkSource = useCallback(
    async (deviceModelId: string, kbSourceId: string): Promise<boolean> => {
      setUnlinkLoading(true);
      setUnlinkError(null);
      try {
        const headers = adminToken.trim()
          ? { "x-admin-token": adminToken.trim() }
          : undefined;
        await api.delete(
          `/admin/devices/${deviceModelId}/sources/${kbSourceId}`,
          { headers }
        );
        await fetchDevices();
        return true;
      } catch (err: any) {
        const msg =
          err?.response?.data?.detail ?? "Unlink failed. Check backend logs.";
        setUnlinkError(msg);
        return false;
      } finally {
        setUnlinkLoading(false);
      }
    },
    [adminToken, fetchDevices]
  );

  return {
    devices,
    loading,
    error,
    refetch: fetchDevices,
    adminToken,
    setAdminToken,
    unlinkSource,
    unlinkLoading,
    unlinkError,
  };
};