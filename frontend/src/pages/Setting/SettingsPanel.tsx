// /src/pages/Setting/SettingsPanel.tsx
import React, { useEffect, useMemo, useState } from "react";
import "./SettingsPanel.css";

import type { SettingsKey } from "./Sections/types";
import { SETTINGS_MENU } from "./Sections/types";

import GeneralSection from "./Sections/GeneralSection";
import NotificationsSection from "./Sections/NotificationsSection";
import SecuritySection from "./Sections/SecuritySection";
import AccountSection from "./Sections/AccountSection";

type Props = {
  open: boolean;
  onClose: () => void;
};

export default function SettingsPanel({ open, onClose }: Props) {
  const [active, setActive] = useState<SettingsKey>("general");

  // 每次打開都回到 General（更像 ChatGPT）
  useEffect(() => {
    if (open) setActive("general");
  }, [open]);

  const content = useMemo(() => {
    switch (active) {
      case "general":
        return <GeneralSection />;
      case "notifications":
        return <NotificationsSection />;
      case "security":
        return <SecuritySection />;
      case "account":
        return <AccountSection />;
      default:
        return null;
    }
  }, [active]);

  if (!open) return null;

  const title = SETTINGS_MENU.find((m) => m.key === active)?.label ?? "";

  return (
    <div className="settings-overlay" onClick={onClose}>
      <div className="settings-shell" onClick={(e) => e.stopPropagation()}>
        {/* left */}
        <aside className="settings-nav">
          <div className="settings-nav-header">
            <button className="settings-close" onClick={onClose} aria-label="Close settings" type="button">
              ✕
            </button>
            <div className="settings-nav-title">Settings</div>
          </div>

          <div className="settings-nav-divider" />

          <div className="settings-nav-list">
            {SETTINGS_MENU.map((item) => (
              <button
                key={item.key}
                className={`settings-nav-item ${active === item.key ? "active" : ""}`}
                onClick={() => setActive(item.key)}
                type="button"
              >
                <span className="settings-nav-icon">{item.icon}</span>
                <span className="settings-nav-label">{item.label}</span>
              </button>
            ))}
          </div>
        </aside>

        {/* right */}
        <main className="settings-content">
          <div className="settings-content-title">{title}</div>
          <div className="settings-content-divider" />
          <div className="settings-content-body">{content}</div>
        </main>
      </div>
    </div>
  );
}
