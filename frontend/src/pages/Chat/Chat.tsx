// /src/pages/Chat/Chat.tsx
import React, { useState, useEffect } from "react";

// styles
import "./styles/ChatLayout.css";
import "./styles/ChatTheme.css";
import "./styles/ChatSidebar.css";
import "./styles/MessageActions.css";
import "./styles/ChatBubbleAlign.css";
import "./styles/ChatMessageStyle.css";

// components
import ChatSidebar from "./components/ChatSidebar";
import IngestionBanner from "./components/IngestionBanner";
import MessageActions from "./components/MessageActions";

// ✅ chat logic
import { useChatLogic } from "./useChatLogic";
import { useIngestionJob } from "../../hooks/useIngestionJob";
import { useConversations } from "./hooks/useConversations";

import { AbstractGuitarIcon, MenuIcon } from "../../components/Icons";

// ✅ Settings Panel
import SettingsPanel from "../Setting/SettingsPanel";

export default function Chat() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [settingsOpen, setSettingsOpen] = useState(false);

  const {
    messages, input, setInput, handleSend, loading, scrollRef, displayName,
    conversationId, startNewConversation, loadConversation,
  } = useChatLogic();

  const { conversations, refresh: refreshConversations } = useConversations();

  useEffect(() => {
    if (conversationId) refreshConversations();
  }, [conversationId, refreshConversations]);

  const jobId = localStorage.getItem("ingestion_job_id");
  const { job } = useIngestionJob(jobId);

  const onToggleSidebar = () => setIsSidebarOpen((p) => !p);

  return (
    <div className="chat-layout-root">
      {/* 左側 Sidebar */}
      {isSidebarOpen && (
        <ChatSidebar
          onToggleSidebar={onToggleSidebar}
          displayName={displayName}
          onOpenSettings={() => setSettingsOpen(true)}
          conversations={conversations}
          activeConversationId={conversationId}
          onNewChat={startNewConversation}
          onSelectConversation={loadConversation}
        />
      )}

      {/* 右側主區 */}
      <section className="chat-right-panel">
        {/* Header */}
        <header className="chat-header">
          <div className="chat-header-left">
            {!isSidebarOpen && (
              <button
                type="button"
                className="sidebar-open-trigger"
                onClick={onToggleSidebar}
                aria-label="Open sidebar"
              >
                <MenuIcon size={20} />
              </button>
            )}
            <div className="chat-title">GuitarFX AI Assistant</div>
          </div>

          <div className="chat-header-right">
            <button
              type="button"
              onClick={() => setSettingsOpen(true)}
              aria-label="Open settings"
              className="sidebar-open-trigger"
            >
              <AbstractGuitarIcon size={40} />
            </button>
          </div>
        </header>

        {/* 中間內容區 */}
        <div className="chat-messages" ref={scrollRef}>
          <IngestionBanner job={job} />

          {messages.length === 0 && (
            <div className="welcome-container">
              <h1 className="welcome-text">
                Hi, <span className="highlight-name">{displayName}</span>
              </h1>
              <div className="welcome-sub">How can I help you today?</div>
            </div>
          )}

          {/* ✅ Messages */}
          {messages.map((msg, idx) => {
            const role = (msg as any).role;
            const content = (msg as any).content ?? "";
            const id = (msg as any).id ?? idx;

            const isUser = role === "user";
            const isAI = !isUser;

            // ✅ 找前一條用戶訊息（AI 回應的上一條）
            const prevUserMessage = isAI
              ? messages
                  .slice(0, idx)
                  .reverse()
                  .find((m) => (m as any).role === "user")
              : null;
            const prevUserContent = prevUserMessage
              ? (prevUserMessage as any).content ?? ""
              : "";

            return (
              <div key={id} className={`message-row ${role} ${isAI ? "has-actions" : ""}`}>
                {isAI && <div className="avatar-mini">🤖</div>}

                <div className={`message-bubble ${role}`}>{content}</div>

                {/* ✅ Copy/Save 放在 AI 回覆外面右下 */}
                {isAI && (
                  <div className="msg-actions-outside">
                    <MessageActions
                      content={content}
                      messageId={String(id)}
                      userMessage={prevUserContent}
                      isToneRecipe={(msg as any).isToneRecipe ?? false}
                    />
                  </div>
                )}
              </div>
            );
          })}

          {/* ✅ Loading bubble */}
          {loading && (
            <div className="message-row ai">
              <div className="avatar-mini">🤖</div>
              <div className="message-bubble ai typing">
                <span className="dot">.</span>
                <span className="dot">.</span>
                <span className="dot">.</span>
              </div>
            </div>
          )}
        </div>

        {/* 底部輸入區 */}
        <footer className="chat-input-area">
          <div className="input-wrapper">
            <input
              className="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSend();
              }}
              placeholder="Ask me anything about your gear..."
            />
            <button className="send-btn" onClick={handleSend} disabled={loading || !input.trim()}>
              {loading ? "..." : "Send"}
            </button>
          </div>
        </footer>
      </section>

      <SettingsPanel open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  );
}