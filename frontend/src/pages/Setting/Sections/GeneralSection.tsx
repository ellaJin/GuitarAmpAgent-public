import React, { useState } from "react";

export default function GeneralSection() {
  const [language, setLanguage] = useState("auto");
  const [spoken, setSpoken] = useState("auto");

  return (
    <>
      <div className="settings-row">
        <div>
          <div className="label">Language</div>
          <div className="hint">Used for menus and text.</div>
        </div>
        <select
          className="settings-select"
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
        >
          <option value="auto">Auto-detect</option>
          <option value="en">English</option>
          <option value="zh">中文</option>
        </select>
      </div>

      <div className="settings-row">
        <div>
          <div className="label">Spoken language</div>
          <div className="hint">Used for voice features.</div>
        </div>
        <select
          className="settings-select"
          value={spoken}
          onChange={(e) => setSpoken(e.target.value)}
        >
          <option value="auto">Auto-detect</option>
          <option value="en">English</option>
          <option value="zh">中文</option>
        </select>
      </div>
    </>
  );
}

