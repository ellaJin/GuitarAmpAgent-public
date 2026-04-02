// src/pages/Songs/useSongLibrary.ts
import { useState, useEffect, useCallback } from "react";
import { api } from "../../lib/api";

export type SongSummary = {
  id: string;
  name: string;
  notes: string | null;
  device_model_id: number | null;
  brand: string | null;
  model: string | null;
  created_at: string;
  updated_at: string;
};

export type SongDetail = SongSummary & {
  raw_text: string;
  structured_config: Record<string, unknown> | null;
};

export function useSongLibrary() {
  const [songs, setSongs] = useState<SongSummary[]>([]);
  const [selectedSong, setSelectedSong] = useState<SongDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);

  const fetchSongs = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get<SongSummary[]>("/songs");
      setSongs(data ?? []);
    } catch (err) {
      console.error("[useSongLibrary] fetch failed:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSongs();
  }, [fetchSongs]);

  const selectSong = useCallback(async (id: string) => {
    setDetailLoading(true);
    try {
      const { data } = await api.get<SongDetail>(`/songs/${id}`);
      setSelectedSong(data);
    } catch (err) {
      console.error("[useSongLibrary] detail fetch failed:", err);
    } finally {
      setDetailLoading(false);
    }
  }, []);

  const deleteSong = useCallback(
    async (id: string) => {
      try {
        await api.delete(`/songs/${id}`);
        setSongs((prev) => prev.filter((s) => s.id !== id));
        if (selectedSong?.id === id) setSelectedSong(null);
      } catch (err) {
        console.error("[useSongLibrary] delete failed:", err);
      }
    },
    [selectedSong]
  );

  const updateSong = useCallback(
    async (id: string, patch: { name?: string; notes?: string }) => {
      try {
        await api.patch(`/songs/${id}`, patch);
        setSongs((prev) => prev.map((s) => (s.id === id ? { ...s, ...patch } : s)));
        setSelectedSong((prev) => (prev?.id === id ? { ...prev, ...patch } : prev));
        return true;
      } catch (err) {
        console.error("[useSongLibrary] update failed:", err);
        return false;
      }
    },
    []
  );

  return { songs, selectedSong, loading, detailLoading, fetchSongs, selectSong, deleteSong, updateSong };
}
