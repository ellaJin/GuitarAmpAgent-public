// src/pages/MyDevices/useMyDevices.ts
import { useState, useEffect, useCallback } from "react";
import { api, API_BASE_URL } from "../../lib/api";

export type UserDevice = {
  user_device_id: string;
  is_active: boolean;
  device_model_id: string;
  brand: string;
  model: string;
  variant: string | null;
  image_url: string | null;
};

export function useMyDevices() {
  const [devices, setDevices] = useState<UserDevice[]>([]);
  const [loading, setLoading] = useState(false);
  const [activating, setActivating] = useState<string | null>(null); // user_device_id being activated

  const fetchDevices = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get<UserDevice[]>("/devices/my");
      setDevices(data ?? []);
    } catch (err) {
      console.error("[useMyDevices] fetch failed:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDevices();
  }, [fetchDevices]);

  const activateDevice = useCallback(async (userDeviceId: string) => {
    setActivating(userDeviceId);
    try {
      const { data } = await api.put<UserDevice[]>(`/devices/my/${userDeviceId}/activate`);
      setDevices(data ?? []);
    } catch (err) {
      console.error("[useMyDevices] activate failed:", err);
    } finally {
      setActivating(null);
    }
  }, []);

  const resolveImageUrl = (path: string | null): string | null => {
    if (!path) return null;
    return `${API_BASE_URL}${path}`;
  };

  return { devices, loading, activating, fetchDevices, activateDevice, resolveImageUrl };
}
