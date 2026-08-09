//frontend/src/pages/Chat/components/MessageActions.tsx
import React, { useState } from "react";
import { api } from "../../../lib/api";

type Props = {
  content: string;
  messageId?: string;
  userMessage?: string;
  isToneRecipe?: boolean; // ✅ 新增
};

function extractSongName(userMessage: string): string {
  // 嘗試從用戶訊息中提取歌名
  // 常見模式：「調XX」「彈XX」「XX的效果」「XX 的設定」
  const patterns = [
    /[「"']([^「"']+)[」"']/,           // 引號內的文字
    /(?:調|彈|play|set up|tone for|sound like)\s+(.+?)(?:的|效果|設定|$)/i,
    /(.+?)(?:的效果|的音色|的設定|效果設定|tone|sound)/i,
  ];

  for (const pattern of patterns) {
    const match = userMessage.match(pattern);
    if (match && match[1]) {
      return match[1].trim().slice(0, 40);
    }
  }

  // 找不到就用用戶訊息前幾個字
  const words = userMessage.trim().slice(0, 30);
  return words || "My Song";
}

function defaultSongName(userMessage: string, aiContent: string): string {
  if (userMessage && userMessage.trim()) {
    return extractSongName(userMessage);
  }
  // fallback：用 AI 回應前幾個字
  const words = aiContent.trim().split(/\s+/).slice(0, 6).join(" ");
  return aiContent.trim().split(/\s+/).length > 6 ? `${words}...` : words;
}

export default function MessageActions({ content, messageId, userMessage = "", isToneRecipe = false }: Props) {
  const [copied, setCopied] = useState(false);
  const [showSaveForm, setShowSaveForm] = useState(false);
  const [songName, setSongName] = useState("");
  const [savingToLib, setSavingToLib] = useState(false);
  const [savedToLib, setSavedToLib] = useState(false);

  const clean = (content ?? "").trim();

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(clean);
      setCopied(true);
      setTimeout(() => setCopied(false), 900);
    } catch {
      const textarea = document.createElement("textarea");
      textarea.value = clean;
      textarea.style.position = "fixed";
      textarea.style.left = "-9999px";
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      textarea.remove();
      setCopied(true);
      setTimeout(() => setCopied(false), 900);
    }
  };

  const openSaveForm = () => {
    // ✅ 用用戶問題提取歌名，而不是 AI 回應
    setSongName(defaultSongName(userMessage, clean));
    setShowSaveForm(true);
    setSavedToLib(false);
  };

  const handleSaveToLibrary = async () => {
    if (!songName.trim()) return;
    setSavingToLib(true);
    try {
      await api.post("/songs", {
        raw_text: clean,
        name: songName.trim(),
        message_id: messageId ?? null,
      });
      setSavedToLib(true);
      setShowSaveForm(false);
    } catch (err) {
      console.error("[MessageActions] save to library failed:", err);
    } finally {
      setSavingToLib(false);
    }
  };

  return (
    <div className="msg-actions-wrapper">
      {showSaveForm && (
        <div className="library-save-form">
          <input
            type="text"
            value={songName}
            onChange={(e) => setSongName(e.target.value)}
            placeholder="Song name..."
            autoFocus
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSaveToLibrary();
              if (e.key === "Escape") setShowSaveForm(false);
            }}
          />
          <div className="library-save-form-row">
            <button
              className="primary"
              type="button"
              onClick={handleSaveToLibrary}
              disabled={savingToLib || !songName.trim()}
            >
              {savingToLib ? "Saving..." : "Save"}
            </button>
            <button type="button" onClick={() => setShowSaveForm(false)}>
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="msg-actions">
        <button className="msg-action-btn" onClick={handleCopy} type="button">
          {copied ? "Copied" : "Copy"}
        </button>
        {isToneRecipe && (
          savedToLib ? (
            <button className="msg-action-btn" type="button" disabled>
              Saved to Library ✓
            </button>
          ) : (
            <button className="msg-action-btn" onClick={openSaveForm} type="button">
              Save to Library
            </button>
          )
        )}
      </div>
    </div>
  );
}