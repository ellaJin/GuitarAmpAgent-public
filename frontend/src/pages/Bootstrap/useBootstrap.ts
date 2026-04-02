// src/pages/Bootstrap/useBootstrap.ts
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthCheck } from "../../hooks/useAuthCheck"; // 引入公共 Hook

export const useBootstrap = () => {
  const nav = useNavigate();
  const { user, loading, check } = useAuthCheck();

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      nav("/login");
    } else {
      check(); // 执行公共鉴权逻辑
    }
  }, []); // 仅在初始化时运行一次

  useEffect(() => {
    // 当鉴权结束且 user 有数据时进行分发
    if (!loading) {
      if (user) {
        if (!user.active_device) {
          nav("/onboarding/device");
        } else {
          nav("/chat");
        }
      } else {
        // user 为 null 说明鉴权失败
        localStorage.removeItem("access_token");
        nav("/login");
      }
    }
  }, [user, loading, nav]);

  return { loading };
};