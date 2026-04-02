//frontend/src/pages/Login/Login.tsx
import React, { useEffect, useRef } from "react";
import "./Login.css";
import { useLogin } from "./useLogin";
import { EyeIcon, EyeOffIcon } from "../../components/Icons";
import loginVideo from "../../assets/login-video.mp4";

export default function Login() {
  const {
    email,
    setEmail,
    password,
    setPassword,
    showPwd,
    togglePwd,
    error,
    loading,
    handleLogin,
    handleGoogleLogin,
  } = useLogin();

  const videoRef = useRef<HTMLVideoElement | null>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    let rafId: number;
    let dir: 1 | -1 = 1;
    let lastTime: number | null = null;
    const SPEED = 1; // seconds of video per real second
    const EDGE = 0.03;

    const tick = (now: number) => {
      const delta = lastTime !== null ? (now - lastTime) / 1000 : 0;
      lastTime = now;

      const dur = video.duration;
      if (Number.isFinite(dur) && dur > 0 && !video.seeking) {
        let next = video.currentTime + dir * SPEED * delta;

        if (next >= dur - EDGE) {
          next = dur - EDGE;
          dir = -1;
        } else if (next <= EDGE) {
          next = EDGE;
          dir = 1;
        }

        video.currentTime = next;
      }

      rafId = requestAnimationFrame(tick);
    };

    const start = () => {
      lastTime = null; // reset delta on resume to avoid big jump
      rafId = requestAnimationFrame(tick);
    };

    const stop = () => cancelAnimationFrame(rafId);

    const onLoaded = () => start();
    video.addEventListener("loadeddata", onLoaded);
    if (video.readyState >= 2) start();

    const onVis = () => (document.hidden ? stop() : start());
    document.addEventListener("visibilitychange", onVis);

    return () => {
      video.removeEventListener("loadeddata", onLoaded);
      document.removeEventListener("visibilitychange", onVis);
      stop();
    };
  }, []);

  return (
    <div className="login-shell">
      <div className="login-container">
        {/* LEFT: video */}
        <div className="login-left">
          <video
            ref={videoRef}
            className="login-video"
            src={loginVideo}
            muted
            playsInline
            preload="auto"
          />
        </div>

        {/* RIGHT: login content */}
        <div className="login-right">
          <div className="login-card">
            <header className="login-header">
              <h1 className="login-title">Welcome back!</h1>
              <p className="login-subtitle">Sign into your account</p>
            </header>

            <div className="social-section">
              <button
                type="button"
                className="social-btn google-btn"
                onClick={handleGoogleLogin}
                disabled={loading}
              >
                <img
                  src="https://www.google.com/favicon.ico"
                  alt=""
                  className="social-icon"
                />
                <span>{loading ? "Connecting..." : "Continue with Google"}</span>
              </button>
            </div>

            <div className="divider">
              <hr />
              <span>Or email</span>
              <hr />
            </div>

            <form onSubmit={handleLogin} noValidate>
              <div className="login-field">
                <label htmlFor="email" className="login-label">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  placeholder="name@example.com"
                  className={`login-input ${error ? "input-error" : ""}`}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                />
              </div>

              <div className="login-field">
                <label htmlFor="password" className="login-label">
                  Password
                </label>

                <div className="pwd-wrapper">
                  <input
                    id="password"
                    type={showPwd ? "text" : "password"}
                    placeholder="Enter your password"
                    className={`login-input ${error ? "input-error" : ""}`}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    autoComplete="current-password"
                  />

                  <button
                    type="button"
                    onClick={togglePwd}
                    className="eye-btn"
                    aria-label={showPwd ? "Hide password" : "Show password"}
                  >
                    {showPwd ? <EyeOffIcon /> : <EyeIcon />}
                  </button>
                </div>

                <div className="forgot-password-container">
                  <a href="/forgot-password" className="forgot-link">
                    Forgot password?
                  </a>
                </div>
              </div>

              {error && (
                <div className="error-container" role="alert">
                  <p className="error-text">{error}</p>
                </div>
              )}

              <button
                type="submit"
                className={`main-btn ${loading ? "btn-loading" : ""}`}
                disabled={loading}
              >
                {loading ? (
                  <span className="loader-text">Logging in...</span>
                ) : (
                  "Log in"
                )}
              </button>
            </form>

            <p className="signup-text">
              Don't have an account?{" "}
              <a href="/register" className="signup-link">
                Sign up
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}