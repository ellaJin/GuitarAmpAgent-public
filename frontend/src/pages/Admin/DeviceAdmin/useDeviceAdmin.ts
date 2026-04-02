// useDeviceAdmin.ts
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../../lib/api";

type FormState = {
  brand: string;
  model: string;
  variant: string;
  source_type: string;
  supports_midi: boolean;
  supports_snapshots: boolean;
  supports_command_center: boolean;
};

//  value ：string -> string，boolean -> boolean
type UpdateField = <K extends keyof FormState>(field: K, value: FormState[K]) => void;

export const useDeviceAdmin = () => {
  const nav = useNavigate();

  const [loading, setLoading] = useState(false);
  const [adminToken, setAdminToken] = useState("");

  const [manualFile, setManualFile] = useState<File | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);

  const [formData, setFormData] = useState<FormState>({
    brand: "",
    model: "",
    variant: "",
    source_type: "mixed",
    supports_midi: false,
    supports_snapshots: false,
    supports_command_center: false,
  });

  const updateField: UpdateField = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!manualFile) {
      alert("Please select a manual PDF first.");
      return;
    }

    setLoading(true);
    try {
      const fd = new FormData();
      fd.append("brand", formData.brand.trim());
      fd.append("model", formData.model.trim());

      const v = formData.variant.trim();
      if (v) fd.append("variant", v);

      // source_type drives pick_profile() and should_run_effect_pipeline() on backend
      fd.append("source_type", formData.source_type);

      // capability flags — stored on device_models
      fd.append("supports_midi", formData.supports_midi ? "true" : "false");
      fd.append("supports_snapshots", formData.supports_snapshots ? "true" : "false");
      fd.append(
        "supports_command_center",
        formData.supports_command_center ? "true" : "false"
      );

      fd.append("manual_file", manualFile);
      if (imageFile) fd.append("image_file", imageFile);

      const headers = adminToken.trim()
        ? { "x-admin-token": adminToken.trim() }
        : undefined;

      const res = await api.post("/admin/devices/activate", fd, { headers });
      const payload = res?.data;

      if (payload?.job_id) localStorage.setItem("ingestion_job_id", String(payload.job_id));
      else localStorage.removeItem("ingestion_job_id");

      if (payload?.document_id)
        localStorage.setItem("ingestion_document_id", String(payload.document_id));
      if (payload?.kb_source_id)
        localStorage.setItem("ingestion_kb_source_id", String(payload.kb_source_id));

      // redirect to admin home instead of chat
      nav("/admin");
    } catch (err: any) {
      console.error("Admin upload failed:", err);
      alert(err?.response?.data?.detail ?? "Upload failed. Please check the backend logs.");
    } finally {
      setLoading(false);
    }
  };

  return {
    loading,
    adminToken,
    setAdminToken,
    formData,
    updateField,
    manualFile,
    setManualFile,
    imageFile,
    setImageFile,
    handleSubmit,
  };
};