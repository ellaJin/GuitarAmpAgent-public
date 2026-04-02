// src/hooks/useAuthCheck.ts
import { useEffect, useState } from "react";
import { api } from "../lib/api";

export const useAuthCheck = () => {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const check = async () => {
    try {
      const { data } = await api.get("/auth/me");
      setUser(data);
    } catch (err) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  return { user, loading, check };
};