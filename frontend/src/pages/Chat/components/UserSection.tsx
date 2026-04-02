// src/pages/Chat/UserSection.tsx
import React, { useEffect, useRef, useState } from "react";
import UserMenu from "./UserMenu";

type Props = {
  displayName: string;
  onOpenSettings: () => void; // ✅ 新增
};

export default function UserSection({ displayName, onOpenSettings }: Props) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement | null>(null);

  const handle = "@wha7755";

  useEffect(() => {
    function onDown(e: MouseEvent) {
      if (open && ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, [open]);

  return (
    <div className="user-section-container" ref={ref}>
      <button className="user-trigger" onClick={() => setOpen((v) => !v)} type="button">
        <div className="user-avatar-circle">{displayName?.[0] ?? "U"}</div>
        <div className="user-meta">
          <div className="user-name-text">{displayName}</div>
          <div className="user-plan-text">Free</div>
        </div>
      </button>

      {open && (
        <UserMenu
          displayName={displayName}
          handle={handle}
          onOpenSettings={() => {
            setOpen(false);      // ✅ 關掉 dropdown
            onOpenSettings();    // ✅ 打開 SettingsPanel modal
          }}
          onLogout={() => {
            localStorage.clear();
            window.location.href = "/login";
          }}
        />
      )}
    </div>
  );
}

