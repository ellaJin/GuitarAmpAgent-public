// src/pages/Admin/Eval/useEvalPage.ts
import { useState, useEffect, useCallback } from "react";
import { api } from "../../../lib/api";

const ADMIN_TOKEN_KEY = "admin_token";

export type EvalQuestion = {
  question: string;
  ground_truth?: string;
};

export type EvalRow = {
  question: string;
  answer: string;
  faithfulness: number | null;
  answer_relevancy: number | null;
  context_precision: number | null;
  has_ground_truth: boolean;
};

export type EvalSummary = {
  faithfulness: number | null;
  answer_relevancy: number | null;
  context_precision: number | null;
  composite_score: number | null;
};

export type EvalResult = {
  summary: EvalSummary;
  rows: EvalRow[];
};

export type Device = {
  device_model_id: string;
  brand: string;
  model: string;
  variant: string | null;
  sources: { kb_source_id: string; title: string }[];
};

export type InputMode = "upload" | "paste";

export const useEvalPage = () => {
  const [adminToken, setAdminTokenState] = useState<string>(
    () => localStorage.getItem(ADMIN_TOKEN_KEY) ?? ""
  );
  const setAdminToken = useCallback((t: string) => {
    setAdminTokenState(t);
    localStorage.setItem(ADMIN_TOKEN_KEY, t);
  }, []);

  // Device list
  const [devices, setDevices] = useState<Device[]>([]);
  const [devicesLoading, setDevicesLoading] = useState(true);
  const [devicesError, setDevicesError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await api.get("/admin/devices/");
        setDevices(res.data ?? []);
      } catch (e: any) {
        setDevicesError(e?.response?.data?.detail ?? "Failed to load devices.");
      } finally {
        setDevicesLoading(false);
      }
    })();
  }, []);

  // Selected device_model_id
  const [selectedDeviceModelId, setSelectedDeviceModelId] = useState("");

  // Input mode
  const [inputMode, setInputMode] = useState<InputMode>("paste");

  // File upload
  const [questionFile, setQuestionFile] = useState<File | null>(null);

  // Paste input
  const [questionText, setQuestionText] = useState("");

  // Eval state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EvalResult | null>(null);

  const _parseQuestions = async (): Promise<EvalQuestion[] | null> => {
    let raw = "";
    if (inputMode === "upload") {
      if (!questionFile) {
        setError("Please select a JSON file.");
        return null;
      }
      raw = await questionFile.text();
    } else {
      raw = questionText.trim();
      if (!raw) {
        setError("Please paste a JSON question set.");
        return null;
      }
    }

    try {
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) {
        setError("JSON must be an array of question objects.");
        return null;
      }
      const questions: EvalQuestion[] = parsed.map((item: any, i: number) => {
        if (!item.question || typeof item.question !== "string") {
          throw new Error(`Item ${i} is missing a "question" string field.`);
        }
        return {
          question: item.question.trim(),
          ground_truth: item.ground_truth?.trim() || undefined,
        };
      });
      return questions;
    } catch (e: any) {
      setError(`Invalid JSON: ${e.message}`);
      return null;
    }
  };

  const handleRun = async () => {
    setError(null);
    setResult(null);

    if (!selectedDeviceModelId) {
      setError("Please select a device.");
      return;
    }

    const questions = await _parseQuestions();
    if (!questions) return;

    setLoading(true);
    try {
      const headers = adminToken.trim()
        ? { "x-admin-token": adminToken.trim() }
        : undefined;

      const res = await api.post(
        "/admin/eval/run",
        { device_model_id: selectedDeviceModelId, questions },
        { headers }
      );
      setResult(res.data);
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Evaluation failed. Check backend logs.");
    } finally {
      setLoading(false);
    }
  };

  const downloadCsv = () => {
    if (!result) return;
    const headers = [
      "question",
      "faithfulness",
      "answer_relevancy",
      "context_precision",
      "answer",
    ];
    const escape = (s: string) => `"${(s ?? "").replace(/"/g, '""')}"`;
    const rows = result.rows.map((r) =>
      [
        escape(r.question),
        r.faithfulness ?? "N/A",
        r.answer_relevancy ?? "N/A",
        r.context_precision ?? "N/A",
        escape(r.answer),
      ].join(",")
    );
    const csv = [headers.join(","), ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "eval_results.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  return {
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
  };
};
