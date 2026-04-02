import React from "react";

export default function AccountSection() {
  return (
    <>
      <div className="settings-row">
        <div>
          <div className="label">Payment</div>
          <div className="hint">Manage your billing and payment methods.</div>
        </div>
        <button className="settings-btn" type="button">
          Payment
        </button>
      </div>

      <div className="settings-row">
        <div>
          <div className="label">Delete account</div>
          <div className="hint">This action cannot be undone.</div>
        </div>
        <button className="settings-btn danger" type="button">
          Delete account
        </button>
      </div>
    </>
  );
}




