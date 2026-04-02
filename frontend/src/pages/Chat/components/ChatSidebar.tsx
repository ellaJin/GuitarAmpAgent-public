// src/pages/Chat/ChatSidebar.tsx
import React from "react";
import UserSection from "./UserSection";
import { MenuIcon, PenIcon } from "../../../components/Icons";
import type { Conversation } from "../hooks/useConversations";

interface SidebarProps {
  onToggleSidebar: () => void;
  displayName: string;
  onOpenSettings: () => void;
  conversations: Conversation[];
  activeConversationId: string | null;
  onNewChat: () => void;
  onSelectConversation: (id: string) => void;
}

function formatDate(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffDays = Math.floor(diffMs / 86400000);
  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays}d ago`;
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export default function ChatSidebar({
  onToggleSidebar,
  displayName,
  onOpenSettings,
  conversations,
  activeConversationId,
  onNewChat,
  onSelectConversation,
}: SidebarProps) {
  return (
    <aside className="chat-sidebar">
      {/* Top bar */}
      <div className="sidebar-topbar">
        <button
          type="button"
          onClick={onToggleSidebar}
          className="sidebar-icon-btn"
          aria-label="Close sidebar"
          title="Close sidebar"
        >
          <MenuIcon size={20} />
        </button>
      </div>

      {/* New chat */}
      <div className="sidebar-action-area">
        <button type="button" className="sidebar-action-btn" onClick={onNewChat}>
          <span className="sidebar-icon" aria-hidden="true">
            <PenIcon size={18} />
          </span>
          <span className="sidebar-text">New chat</span>
        </button>
      </div>

      {/* Conversation list */}
      <div className="sidebar-conv-list">
        {conversations.map((c) => (
          <button
            key={c.id}
            type="button"
            className={`sidebar-conv-item${c.id === activeConversationId ? " active" : ""}`}
            onClick={() => onSelectConversation(c.id)}
            title={c.title}
          >
            <span className="conv-title">{c.title}</span>
            <span className="conv-meta">{formatDate(c.updated_at)}</span>
          </button>
        ))}
      </div>

      {/* User section (bottom) */}
      <UserSection displayName={displayName} onOpenSettings={onOpenSettings} />
    </aside>
  );
}
