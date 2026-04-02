// src/pages/Admin/AddDocument/useAddDocument.ts
import { useState } from "react";
import { useNavigate, useParams, useLocation } from "react-router-dom";
import { api } from "../../../lib/api";

const ADMIN_TOKEN_KEY = "admin_token";

const SOURCE_TYPE_OPTIONS = [
  { value: "mixed", label: "Mixed (single PDF, all content)" },
  { value: "effects_settings", label: "Effects Settings (dedicated effect parameter PDF)" },
  { value: "user_manual", label: "User Manual (operation guide only, no effect list)" },
] as const;

export { SOURCE_TYPE_OPTIONS };

export const useAddDocument = () => {
  const nav = useNavigate();
  const { deviceModelId } = useParams<{ deviceModelId: string }>();
  const location = useLocation();

  // Device name passed via navigation state from AdminHome
  const deviceName: string = (location.state as any)?.deviceName ?? "this device";

  const [loading, setLoading] = useState(false);
  const [adminToken, setAdminTokenState] = useState<string>(
    () => localStorage.getItem(ADMIN_TOKEN_KEY) ?? ""
  );

  const setAdminToken = (token: string) => {
    setAdminTokenState(token);
    localStorage.setItem(ADMIN_TOKEN_KEY, token);
  };

  const [sourceType, setSourceType] = useState("mixed");
  const [manualFile, setManualFile] = useState<File | null>(null);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!manualFile) {
      alert("Please select a manual PDF first.");
      return;
    }
    if (!deviceModelId) {
      alert("Device ID is missing from the URL.");
      return;
    }

    setLoading(true);
    try {
      const fd = new FormData();
      fd.append("source_type", sourceType);
      fd.append("manual_file", manualFile);

      const headers = adminToken.trim()
        ? { "x-admin-token": adminToken.trim() }
        : undefined;

      const res = await api.post(
        `/admin/devices/${deviceModelId}/documents`,
        fd,
        { headers }
      );

      const payload = res?.data;
      if (payload?.job_id) localStorage.setItem("ingestion_job_id", String(payload.job_id));
      if (payload?.document_id) localStorage.setItem("ingestion_document_id", String(payload.document_id));
      if (payload?.kb_source_id) localStorage.setItem("ingestion_kb_source_id", String(payload.kb_source_id));

      nav("/admin");
    } catch (err: any) {
      console.error("Add document failed:", err);
      alert(err?.response?.data?.detail ?? "Upload failed. Please check the backend logs.");
    } finally {
      setLoading(false);
    }
  };

  return {
    deviceModelId,
    deviceName,
    loading,
    adminToken,
    setAdminToken,
    sourceType,
    setSourceType,
    manualFile,
    setManualFile,
    handleSubmit,
  };
};
