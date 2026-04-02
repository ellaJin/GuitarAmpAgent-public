// src/pages/Chat/hooks/useConversations.ts
import { useState, useEffect, useCallback } from "react";
import { api } from "../../../lib/api";

export type Conversation = {
  id: string;
  title: string;
  brand: string | null;
  model: string | null;
  updated_at: string | null;
  message_count: number;
};

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([]);

  const refresh = useCallback(async () => {
    try {
      const { data } = await api.get<Conversation[]>("/conversations");
      setConversations(data ?? []);
    } catch (err) {
      console.error("[useConversations] fetch failed:", err);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { conversations, refresh };
}
