// src/pages/Register/useRegister.ts
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../lib/api";
import { validatePassword } from "./passwordValidator";
import { useTogglePassword } from "../../hooks/useTogglePassword";

export const useRegister = () => {
  const nav = useNavigate();
  const [formData, setFormData] = useState({ name: "", email: "", password: "", confirmPassword: "" });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // 分别控制密码显示/隐藏
  const pwdVisibility = useTogglePassword();
  const confirmPwdVisibility = useTogglePassword();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // 1. 前端逻辑校验
    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    const pwError = validatePassword(formData.password);
    if (pwError) {
      setError(pwError);
      return;
    }

    setLoading(true);
    try {
      // 2. 发送请求：恢复使用你确认正确的字段名 display_name
      await api.post("/auth/register", {
        email: formData.email,
        password: formData.password,
        display_name: formData.name
      });

      nav("/login");
    } catch (err: any) {
      // 3. 核心修复：防止对象直接进入渲染导致白屏
      const detail = err?.response?.data?.detail;

      if (Array.isArray(detail)) {
        // 如果是 FastAPI 的 422 错误数组，提取第一条错误的消息字符串
        const firstError = detail[0];
        const fieldName = firstError?.loc?.[1] || "Error";
        const message = firstError?.msg || "Invalid input";
        setError(`${fieldName}: ${message}`);
      } else if (typeof detail === "string") {
        setError(detail);
      } else {
        setError("Registration failed. Please check your network or input.");
      }

      console.error("Registration Error Detail:", detail);
    } finally {
      setLoading(false);
    }
  };

  return {
    formData,
    setFormData,
    error,
    loading,
    handleRegister,
    pwdVisibility,
    confirmPwdVisibility
  };
};