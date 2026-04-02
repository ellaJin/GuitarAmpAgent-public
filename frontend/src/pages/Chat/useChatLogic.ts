// src/pages/Chat/useChatLogic.ts
import { useState, useEffect, useRef } from "react";
import { api } from "../../lib/api";

export interface Message {
  role: "user" | "ai";
  content: string;
  id?: string; // DB UUID — present on AI messages after server response
}

export const useChatLogic = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [displayName, setDisplayName] = useState("Guitarist");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Fetch display name on mount
  useEffect(() => {
    const fetchUser = async () => {
      try {
        const { data } = await api.get("/auth/me");
        if (data?.display_name) {
          setDisplayName(data.display_name);
          return;
        }
        const fromStorage =
          localStorage.getItem("displayName") ||
          localStorage.getItem("userName") ||
          localStorage.getItem("name");
        if (fromStorage) setDisplayName(fromStorage);
      } catch (e) {
        console.error("Failed to fetch user info:", e);
        const fromStorage =
          localStorage.getItem("displayName") ||
          localStorage.getItem("userName") ||
          localStorage.getItem("name");
        if (fromStorage) setDisplayName(fromStorage);
      }
    };
    fetchUser();
  }, []);

  // Auto-scroll on new messages
  useEffect(() => {
    if (!scrollRef.current) return;
    scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, loading]);

  // Handle seed message from device onboarding
  useEffect(() => {
    const seed = localStorage.getItem("chat_seed_message");
    if (seed) {
      localStorage.removeItem("chat_seed_message");
      setInput(seed);
    }
  }, []);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMsg: Message = { role: "user", content: input.trim() };
    const nextHistory = [...messages, userMsg];
    setMessages(nextHistory);
    setInput("");
    setLoading(true);

    try {
      const { data } = await api.post("/chat/query", {
        message: userMsg.content,
        history: nextHistory.map((m) => ({
          role: m.role === "ai" ? "assistant" : "user",
          content: m.content,
        })),
        conversation_id: conversationId,
      });

      const aiMsg: Message = {
        role: "ai",
        content: data?.answer ?? "",
        id: data?.ai_message_id ?? undefined,
      };
      setMessages((prev) => [...prev, aiMsg]);

      if (data?.conversation_id) {
        setConversationId(data.conversation_id);
      }
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => [
        ...prev,
        { role: "ai", content: "抱歉，我现在无法处理您的请求，请检查后端 Agent 状态。" },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const startNewConversation = () => {
    setMessages([]);
    setConversationId(null);
    setInput("");
  };

  const loadConversation = async (id: string) => {
    try {
      const { data } = await api.get(`/conversations/${id}`);
      const msgs: Message[] = (data.messages ?? []).map((m: any) => ({
        id: m.id,
        role: (m.role === "assistant" ? "ai" : "user") as "user" | "ai",
        content: m.content,
      }));
      setMessages(msgs);
      setConversationId(id);
    } catch (err) {
      console.error("[chat] load conversation error:", err);
    }
  };

  return {
    messages,
    input,
    setInput,
    handleSend,
    loading,
    scrollRef,
    displayName,
    conversationId,
    startNewConversation,
    loadConversation,
  };
};
