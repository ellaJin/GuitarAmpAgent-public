// frontend/src/pages/Register/useVerifyCode.ts
import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { api } from "../../lib/api";

interface RegisterState {
  email: string;
  password: string;
  display_name: string;
}

const RESEND_COOLDOWN_SECONDS = 60;

export const useVerifyCode = () => {
  const nav = useNavigate();
  const location = useLocation();
  const state = (location.state as RegisterState | null) ?? null;

  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  // A code was already sent by the register step right before we got here,
  // so the resend cooldown starts running immediately.
  const [cooldown, setCooldown] = useState(RESEND_COOLDOWN_SECONDS);

  useEffect(() => {
    // No email/password in hand (e.g. page was opened directly, or refreshed
    // and lost router state) -- nothing to verify or resend, so bounce back.
    if (!state?.email) {
      nav("/register", { replace: true });
    }
  }, [state, nav]);

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setInterval(() => setCooldown((c) => Math.max(0, c - 1)), 1000);
    return () => clearInterval(timer);
  }, [cooldown]);

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!state?.email) return;
    setError(null);
    setLoading(true);
    try {
      const { data } = await api.post("/auth/register/verify", {
        email: state.email,
        code,
      });
      localStorage.setItem("access_token", data.access_token);
      nav("/bootstrap");
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Verification failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (cooldown > 0 || !state?.email || resending) return;
    setError(null);
    setInfo(null);
    setResending(true);
    try {
      const { data } = await api.post("/auth/register", {
        email: state.email,
        password: state.password,
        display_name: state.display_name,
      });
      setInfo(data?.message ?? "Verification code sent.");
      setCooldown(RESEND_COOLDOWN_SECONDS);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Failed to resend code.");
    } finally {
      setResending(false);
    }
  };

  return {
    email: state?.email ?? "",
    code,
    setCode,
    error,
    info,
    loading,
    resending,
    cooldown,
    handleVerify,
    handleResend,
  };
};
