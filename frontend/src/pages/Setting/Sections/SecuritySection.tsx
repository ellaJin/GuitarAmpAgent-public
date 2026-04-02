import React from "react";

export default function SecuritySection() {
  return (
    <div className="settings-row">
      <div>
        <div className="label">Change password</div>
        <div className="hint">Update your account password.</div>
      </div>
      <button className="settings-btn" type="button">
        Change password
      </button>
    </div>
  );
}

