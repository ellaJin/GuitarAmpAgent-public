//frontend/src/pages/Register/Register.tsx

import React from "react";
import "./Register.css";
import { useRegister } from "./useRegister";
import { EyeIcon, EyeOffIcon } from "../../components/Icons";
import registerBg from "../../assets/guitar.jpg"; // put your guitar image here

export default function Register() {
  const {
    formData, setFormData, error, loading,
    handleRegister, pwdVisibility, confirmPwdVisibility
  } = useRegister();

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
          <h1 className="reg-header">Register your account</h1>

          <form onSubmit={handleRegister} className="reg-form">
            <div className="reg-field">
              <label className="reg-label">Name</label>
              <input
                className="reg-input"
                type="text"
                value={formData.name || ""}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
                placeholder="Your full name"
              />
            </div>

            <div className="reg-field">
              <label className="reg-label">Email</label>
              <input
                className="reg-input"
                type="email"
                value={formData.email || ""}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
                placeholder="name@example.com"
              />
            </div>

            <div className="reg-field">
              <label className="reg-label">Password</label>
              <div className="reg-input-wrapper">
                <input
                  className="reg-input"
                  type={pwdVisibility.showPwd ? "text" : "password"}
                  value={formData.password || ""}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required
                  placeholder="Create a password"
                />
                <button
                  type="button"
                  className="reg-eye"
                  onClick={pwdVisibility.toggle}
                  aria-label={pwdVisibility.showPwd ? "Hide password" : "Show password"}
                >
                  {pwdVisibility.showPwd ? <EyeOffIcon /> : <EyeIcon />}
                </button>
              </div>
            </div>

            <div className="reg-field">
              <label className="reg-label">Confirm Password</label>
              <div className="reg-input-wrapper">
                <input
                  className="reg-input"
                  type={confirmPwdVisibility.showPwd ? "text" : "password"}
                  value={formData.confirmPassword || ""}
                  onChange={(e) =>
                    setFormData({ ...formData, confirmPassword: e.target.value })
                  }
                  required
                  placeholder="Repeat your password"
                />
                <button
                  type="button"
                  className="reg-eye"
                  onClick={confirmPwdVisibility.toggle}
                  aria-label={confirmPwdVisibility.showPwd ? "Hide password" : "Show password"}
                >
                  {confirmPwdVisibility.showPwd ? <EyeOffIcon /> : <EyeIcon />}
                </button>
              </div>
            </div>

            {error && (
              <div className="reg-error" role="alert">
                ⚠️ {error}
              </div>
            )}

            <button className="reg-btn" type="submit" disabled={loading}>
              {loading ? "Registering..." : "Sign up"}
            </button>
          </form>

          <div className="reg-footer">
            Already have an account?{" "}
            <a href="/login" className="reg-link">
              Sign in.
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
