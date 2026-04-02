// src/pages/Chat/SettingsSubMenu.tsx
import React from "react";

type Props = {
  onBack: () => void;
};

export default function SettingsSubMenu({ onBack }: Props) {
  return (
    <div className="user-menu">
      <div className="submenu-header">
        <button className="submenu-back" onClick={onBack} aria-label="Back">
          <ArrowLeftIcon />
        </button>
        <span className="submenu-title">Settings</span>
      </div>

      <div className="user-menu-divider" />

      <button className="user-menu-item" type="button">
        <GearIcon />
        <span>General</span>
      </button>

      <button className="user-menu-item" type="button">
        <BellIcon />
        <span>Notifications</span>
      </button>

      <button className="user-menu-item" type="button">
        <ShieldIcon />
        <span>Security</span>
      </button>

      <button className="user-menu-item" type="button">
        <UserIcon />
        <span>Account</span>
      </button>
    </div>
  );
}

/* ============ SVG Icons (currentColor) ============ */

function ArrowLeftIcon() {
  return (
    <svg className="menu-ico" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path fill="currentColor" d="M14.7 6.3a1 1 0 0 1 0 1.4L10.4 12l4.3 4.3a1 1 0 1 1-1.4 1.4l-5-5a1 1 0 0 1 0-1.4l5-5a1 1 0 0 1 1.4 0z" />
    </svg>
  );
}

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

function BellIcon() {
  return (
    <svg className="menu-ico" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="currentColor"
        d="M12 22a2.5 2.5 0 0 0 2.45-2h-4.9A2.5 2.5 0 0 0 12 22zm7-6V11a7 7 0 1 0-14 0v5l-2 2v1h18v-1l-2-2z"
      />
    </svg>
  );
}

function ShieldIcon() {
  return (
    <svg className="menu-ico" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="currentColor"
        d="M12 2 4 5v6c0 5 3.4 9.7 8 11 4.6-1.3 8-6 8-11V5l-8-3zm0 18c-3.3-1.2-6-4.8-6-9V6.3L12 4l6 2.3V11c0 4.2-2.7 7.8-6 9z"
      />
    </svg>
  );
}

function UserIcon() {
  return (
    <svg className="menu-ico" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="currentColor"
        d="M12 12a4 4 0 1 0-4-4 4 4 0 0 0 4 4zm0 2c-4.4 0-8 2.2-8 5v1h16v-1c0-2.8-3.6-5-8-5z"
      />
    </svg>
  );
}

