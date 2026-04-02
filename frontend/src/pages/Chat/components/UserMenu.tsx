// src/pages/Chat/components/UserMenu.tsx
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import HelpSubMenu from "./HelpSubMenu";

type Props = {
  displayName: string;
  handle: string;
  onLogout: () => void;
  onOpenSettings: () => void; // ✅ 新增：開啟真正的 SettingsPanel modal
};

export default function UserMenu({ displayName, handle, onLogout, onOpenSettings }: Props) {
  const [view, setView] = useState<"main" | "help">("main");
  const navigate = useNavigate();

  if (view === "help") {
    return (
      <HelpSubMenu
        onBack={() => setView("main")}
        onHelpCenter={() => window.open("https://example.com/help", "_blank")}
        onTerms={() => window.open("https://example.com/terms", "_blank")}
        onReportBug={() => window.open("https://example.com/report-bug", "_blank")}
      />
    );
  }

  const initials = (displayName?.trim()?.[0] || "C").toUpperCase();

  return (
    <div className="user-menu">
      {/* Header */}
      <div className="user-menu-header">
        <div className="user-menu-avatar">{initials}</div>
        <div className="user-menu-meta">
          <div className="user-menu-name">{displayName}</div>
          <div className="user-menu-handle">{handle}</div>
        </div>
      </div>

      <div className="user-menu-divider" />

      {/* ✅ Settings：直接開 modal，不進子選單 */}
      <button className="user-menu-item" type="button" onClick={onOpenSettings}>
        <GearIcon />
        <span>Settings</span>
      </button>

      {/* My Devices */}
      <button className="user-menu-item" type="button" onClick={() => navigate("/devices")}>
        <MyDevicesIcon />
        <span>My Devices</span>
      </button>

      {/* Song Library */}
      <button className="user-menu-item" type="button" onClick={() => navigate("/songs")}>
        <MusicLibraryIcon />
        <span>Song Library</span>
      </button>

      {/* Help */}
      <button className="user-menu-item" type="button" onClick={() => setView("help")}>
        <HelpCircleIcon />
        <span>Help</span>
        <ChevronRightIcon className="menu-right" />
      </button>

      <div className="user-menu-divider" />

      {/* Logout */}
      <button className="user-menu-item danger" type="button" onClick={onLogout}>
        <LogoutIcon />
        <span>Log out</span>
      </button>
    </div>
  );
}

/* ======= Black/White Icons (SVG, currentColor) ======= */

function GearIcon() {
  return (
    <svg className="menu-ico" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="currentColor"
        d="M19.14 12.94c.04-.31.06-.63.06-.94s-.02-.63-.06-.94l2.03-1.58a.5.5 0 0 0 .12-.64l-1.92-3.32a.5.5 0 0 0-.6-.22l-2.39.96a7.03 7.03 0 0 0-1.63-.94l-.36-2.54A.5.5 0 0 0 13.9 1h-3.8a.5.5 0 0 0-.49.42l-.36 2.54c-.58.24-1.12.55-1.63.94l-2.39-.96a.5.5 0 0 0-.6.22L2.71 7.48a.5.5 0 0 0 .12.64l2.03 1.58c-.04.31-.06.63-.06.94s.02.63.06.94L2.83 14.52a.5.5 0 0 0-.12.64l1.92 3.32c.13.22.39.3.6.22l2.39-.96c.5.39 1.05.7 1.63.94l.36 2.54c.04.24.25.42.49.42h3.8c.24 0 .45-.18.49-.42l.36-2.54c.58-.24 1.12-.55 1.63-.94l2.39.96c.22.08.47 0 .6-.22l1.92-3.32a.5.5 0 0 0-.12-.64l-2.03-1.58zM12 15.5A3.5 3.5 0 1 1 12 8a3.5 3.5 0 0 1 0 7.5z"
      />
    </svg>
  );
}

function HelpCircleIcon() {
  return (
    <svg className="menu-ico" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="currentColor"
        d="M12 2C6.49 2 2 6.48 2 12s4.49 10 10 10 10-4.48 10-10S17.51 2 12 2zm0 17a1.25 1.25 0 1 1 0-2.5A1.25 1.25 0 0 1 12 19zm1.2-5.7c-.64.45-.7.6-.7 1.2v.25h-1.5v-.45c0-1.1.45-1.7 1.2-2.2.62-.43 1.05-.75 1.05-1.35 0-.72-.55-1.2-1.35-1.2-.8 0-1.35.48-1.43 1.25H9.92c.12-1.62 1.42-2.75 3.05-2.75 1.78 0 2.85 1.08 2.85 2.55 0 1.2-.7 1.85-1.47 2.4z"
      />
    </svg>
  );
}

function LogoutIcon() {
  return (
    <svg className="menu-ico" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="currentColor"
        d="M10 17v-2h4v-2h-4V11l-3 3 3 3zm9-14H5c-1.1 0-2 .9-2 2v4h2V5h14v14H5v-4H3v4c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2z"
      />
    </svg>
  );
}

function MyDevicesIcon() {
  return (
    <svg className="menu-ico" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="currentColor"
        d="M21 3H3a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h5v2H6v2h12v-2h-2v-2h5a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2zm0 14H3V5h18v12z"
      />
    </svg>
  );
}

function MusicLibraryIcon() {
  return (
    <svg className="menu-ico" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="currentColor"
        d="M12 3v10.55A4 4 0 1 0 14 17V7h4V3h-6zm-2 16a2 2 0 1 1 0-4 2 2 0 0 1 0 4z"
      />
    </svg>
  );
}

function ChevronRightIcon({ className = "" }: { className?: string }) {
  return (
    <svg className={`menu-ico ${className}`} width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="currentColor"
        d="M9.29 6.71a1 1 0 0 0 0 1.41L13.17 12l-3.88 3.88a1 1 0 1 0 1.41 1.41l4.59-4.59a1 1 0 0 0 0-1.41L10.7 6.7a1 1 0 0 0-1.41.01z"
      />
    </svg>
  );
}



