import { useEffect, useState } from "react";

type ChatRole = "user" | "assistant";
export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  createdAt: number;
};

function createId() {
  return `${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

export function useChatState(storageKey = "chat_messages_v1") {
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    try {
      const raw = localStorage.getItem(storageKey);
      if (!raw) return [];
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(storageKey, JSON.stringify(messages));
    } catch {}
  }, [messages, storageKey]);

  function addUserMessage(content: string) {
    const msg: ChatMessage = {
      id: createId(),
      role: "user",
      content,
      createdAt: Date.now(),
    };
    setMessages((prev) => [...prev, msg]);
    return msg;
  }

  function addAssistantMessage(content: string) {
    const msg: ChatMessage = {
      id: createId(),
      role: "assistant",
      content,
      createdAt: Date.now(),
    };
    setMessages((prev) => [...prev, msg]);
    return msg;
  }

  function clearMessages() {
    setMessages([]);
  }

  return { messages, setMessages, addUserMessage, addAssistantMessage, clearMessages };
}
