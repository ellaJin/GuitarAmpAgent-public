// frontend/src/pages/Register/VerifyCode.tsx

import React from "react";
import { Link } from "react-router-dom";
import "./Register.css";
import { useVerifyCode } from "./useVerifyCode";
import registerBg from "../../assets/guitar.jpg";

export default function VerifyCode() {
  const {
    email, code, setCode, error, info, loading, resending, cooldown,
    handleVerify, handleResend
  } = useVerifyCode();

  return (
    <div className="reg-container">
      <div className="reg-shell">
        {/* LEFT: image panel */}
        <div
          className="reg-art"
          style={{ backgroundImage: `url(${registerBg})` }}
          aria-hidden="true"
        />

        {/* RIGHT: form panel */}
        <div className="reg-panel">
          <h1 className="reg-header">Verify your email</h1>
          <p className="reg-subtext">
            We sent a 6-digit code to <strong>{email}</strong>. It expires in 10 minutes.
          </p>

          <form onSubmit={handleVerify} className="reg-form">
            <div className="reg-field">
              <label className="reg-label">Verification code</label>
              <input
                className="reg-input reg-input-code"
                type="text"
                inputMode="numeric"
                pattern="\d{6}"
                maxLength={6}
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                required
                placeholder="123456"
                autoFocus
              />
            </div>

            {error && (
              <div className="reg-error" role="alert">
                ⚠️ {error}
              </div>
            )}

            {info && (
              <div className="reg-info" role="status">
                {info}
              </div>
            )}

            <button className="reg-btn" type="submit" disabled={loading || code.length !== 6}>
              {loading ? "Verifying..." : "Verify & continue"}
            </button>
          </form>

          <div className="reg-footer">
            Didn't get it?{" "}
            {cooldown > 0 ? (
              <span className="reg-muted">Resend available in {cooldown}s</span>
            ) : (
              <button
                type="button"
                className="reg-link reg-link-btn"
                onClick={handleResend}
                disabled={resending}
              >
                {resending ? "Sending..." : "Resend code"}
              </button>
            )}
          </div>

          <div className="reg-footer">
            <Link to="/login" className="reg-link">
              Back to sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
