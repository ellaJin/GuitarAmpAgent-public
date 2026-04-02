// src/pages/Onboarding/Device/useDevice.ts
import { useState, useEffect, useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api, API_BASE_URL } from "../../../lib/api";

type ApiDevice = {
  device_model_id: string;
  brand: string;
  model: string;
  variant: string | null;
  image_url: string | null;
};

export const useDevice = () => {
  const nav = useNavigate();
  const [searchParams] = useSearchParams();
  const isAddMode = searchParams.get("from") === "devices";

  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [availableDevices, setAvailableDevices] = useState<ApiDevice[]>([]);
  const [devicesLoading, setDevicesLoading] = useState(true);

  const [formData, setFormData] = useState({ brand: "", model: "" });

  // Fetch available devices on mount
  useEffect(() => {
    api
      .get<ApiDevice[]>("/devices/available")
      .then((res) => setAvailableDevices(res.data ?? []))
      .catch(() => {
        // Non-fatal: form still renders, submit will catch missing device
      })
      .finally(() => setDevicesLoading(false));
  }, []);

  // Derive brand list and brand→models map from the API response
  const brands = useMemo(
    () => [...new Set(availableDevices.map((d) => d.brand))].sort(),
    [availableDevices]
  );

  const modelsByBrand = useMemo(() => {
    const map: Record<string, string[]> = {};
    for (const d of availableDevices) {
      if (!map[d.brand]) map[d.brand] = [];
      map[d.brand].push(d.model);
    }
    return map;
  }, [availableDevices]);

  // Look up the full device record for the current brand+model selection
  const selectedDevice = useMemo(
    () =>
      availableDevices.find(
        (d) => d.brand === formData.brand && d.model === formData.model
      ) ?? null,
    [availableDevices, formData.brand, formData.model]
  );

  const selectedDeviceModelId = selectedDevice?.device_model_id ?? null;
  const selectedDeviceImageUrl = selectedDevice?.image_url
    ? `${API_BASE_URL}${selectedDevice.image_url}`
    : null;

  const handleActivate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const brand = formData.brand.trim();
    const model = formData.model.trim();

    if (!brand || !model) {
      setError("Please enter both brand and model.");
      return;
    }

    if (!selectedDeviceModelId) {
      setError(
        "This device isn't in our system yet. Please select one of the supported devices."
      );
      return;
    }

    setLoading(true);
    try {
      if (isAddMode) {
        await api.post("/devices/bind-inactive", { device_model_id: selectedDeviceModelId });
        nav("/devices");
      } else {
        await api.post("/devices/bind", { device_model_id: selectedDeviceModelId });
        localStorage.setItem("device_info", JSON.stringify({ brand, model }));
        nav("/chat");
      }
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ?? "Something went wrong. Please try again.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const updateField = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  return {
    loading: loading || devicesLoading,
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
  };
};
