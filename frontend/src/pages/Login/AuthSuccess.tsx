import React, { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

const AuthSuccess = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    // 从 URL 查询参数中获取 token (后端通过 ?token=xxx 传过来)
    const token = searchParams.get("token");

    if (token) {
      // 1. 存储 Token 到本地
      localStorage.setItem("access_token", token);

      // 2. 可以在这里做一些初始化操作（如获取用户信息）
      console.log("Google Login Success, redirecting...");

      // 3. 跳转到主页面
      navigate("/bootstrap");
    } else {
      // 如果没有 token，说明认证失败，跳回登录页并显示错误
      console.error("Auth failed: No token found in URL");
      navigate("/login?error=google_auth_failed");
    }
  }, [searchParams, navigate]);

  return (
    <div className="login-container" style={{ textAlign: 'center', paddingTop: '100px' }}>
      <div className="login-card">
        <h2 className="login-title">Authenticating...</h2>
        <p className="login-subtitle">Please wait while we set up your session.</p>
        {/* 这里可以放一个 Loading 动画 */}
        <div className="loader-text">Loading...</div>
      </div>
    </div>
  );
};

export default AuthSuccess;