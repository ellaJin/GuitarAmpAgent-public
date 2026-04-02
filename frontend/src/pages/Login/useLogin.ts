import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../lib/api";
import { useTogglePassword } from "../../hooks/useTogglePassword"; 

export const useLogin = () => {
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { showPwd, toggle: togglePwd } = useTogglePassword();

  const handleGoogleLogin = () => {
    console.log("Redirecting to Google login...");
    // 指向後端新增的入口
    window.location.href = "http://127.0.0.1:8000/auth/google/login";
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { data } = await api.post("/auth/login", { email, password });
      localStorage.setItem("access_token", data.access_token);
      nav("/bootstrap");
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Login failed.");
    } finally {
      setLoading(false);
    }
  };

  return {
    email, setEmail, password, setPassword,
    showPwd, togglePwd, error, loading,
    handleLogin, handleGoogleLogin
  };
};