// src/pages/Chat/components/HelpSubMenu.tsx
import React from "react";

type Props = {
  onBack: () => void;
  onHelpCenter?: () => void;
  onTerms?: () => void;
  onReportBug?: () => void;
};

export default function HelpSubMenu({
  onBack,
  onHelpCenter,
  onTerms,
  onReportBug,
}: Props) {
  return (
    <div className="user-menu">
      <div className="submenu-header">
        <button className="submenu-back" onClick={onBack} aria-label="Back">
          <ArrowLeftIcon />
        </button>
        <span className="submenu-title">Help</span>
      </div>

      <div className="user-menu-divider" />

      <button className="user-menu-item" type="button" onClick={onHelpCenter}>
        <LifeRingIcon />
        <span>Help center</span>
      </button>

      <button className="user-menu-item" type="button" onClick={onTerms}>
        <DocIcon />
        <span>Terms &amp; policies</span>
      </button>

      <button className="user-menu-item" type="button" onClick={onReportBug}>
        <BugIcon />
        <span>Report Bug</span>
      </button>
    </div>
  );
}

/* ======= Black/White Icons (SVG, currentColor) ======= */

function ArrowLeftIcon() {
  return (
    <svg className="menu-ico" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="currentColor"
        d="M14.7 6.3a1 1 0 0 1 0 1.4L10.4 12l4.3 4.3a1 1 0 1 1-1.4 1.4l-5-5a1 1 0 0 1 0-1.4l5-5a1 1 0 0 1 1.4 0z"
      />
    </svg>
  );
}

function LifeRingIcon() {
  return (
    <svg className="menu-ico" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="currentColor"
        d="M12 2a10 10 0 1 0 10 10A10.01 10.01 0 0 0 12 2Zm0 4a6 6 0 0 1 4.24 1.76L14.7 9.3A3.5 3.5 0 0 0 9.3 14.7l-1.54 1.54A6 6 0 0 1 12 6Zm0 12a6 6 0 0 1-4.24-1.76l1.54-1.54A3.5 3.5 0 0 0 14.7 9.3l1.54-1.54A6 6 0 0 1 12 18Zm0-5.5A2.5 2.5 0 1 1 14.5 12 2.5 2.5 0 0 1 12 12.5Z"
      />
    </svg>
  );
}

function DocIcon() {
  return (
    <svg className="menu-ico" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="currentColor"
        d="M6 2h9l5 5v15a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zm8 1.5V8h4.5L14 3.5zM8 12h8v-2H8v2zm0 4h8v-2H8v2zm0 4h6v-2H8v2z"
      />
    </svg>
  );
}

function BugIcon() {
  return (
    <svg className="menu-ico" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="currentColor"
        d="M20 8h-3.2a4.9 4.9 0 0 0-1.1-1.7l1.7-1.7-1.4-1.4-2 2A6.3 6.3 0 0 0 12 4a6.3 6.3 0 0 0-2 .2l-2-2L6.6 3.6l1.7 1.7A4.9 4.9 0 0 0 7.2 8H4v2h3v2H4v2h3.2A6 6 0 0 0 11 20.9V18H9v-2h6v2h-2v2.9A6 6 0 0 0 16.8 16H20v-2h-3v-2h3V10h-3V8zm-5 6H9V8h6v6z"
      />
    </svg>
  );
}
