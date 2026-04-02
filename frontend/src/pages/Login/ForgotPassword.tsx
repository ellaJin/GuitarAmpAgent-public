import React, { useState } from "react";
import "./Login.css"; // 共用 Login 的樣式以保持 UI 一致

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    // 這裡模擬 API 呼叫
    setTimeout(() => {
      setLoading(false);
      setSubmitted(true);
    }, 1500);
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <header className="login-header">
          <h1 className="login-title">Reset Password</h1>
          <p className="login-subtitle">
            {submitted 
              ? "Check your email for reset instructions." 
              : "Enter your email to receive a password reset link."}
          </p>
        </header>

        {!submitted ? (
          <form onSubmit={handleSubmit}>
            <div className="login-field">
              <label htmlFor="reset-email" className="login-label">Email Address</label>
              <input
                id="reset-email"
                type="email"
                placeholder="name@example.com"
                className="login-input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <button type="submit" className="main-btn" disabled={loading}>
              {loading ? "Sending..." : "Send Reset Link"}
            </button>
          </form>
        ) : (
          <button onClick={() => window.location.href = "/login"} className="main-btn">
            Back to Login
          </button>
        )}

        <p className="signup-text">
          Remembered your password? <a href="/login" className="signup-link">Log in</a>
        </p>
      </div>
    </div>
  );
}