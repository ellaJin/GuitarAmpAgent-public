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
  const [searchQuery, setSearchQuery] = useState("");

  // 根據 searchQuery 過濾歌曲列表
  const filteredSongs = songs.filter((s) =>
    s.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

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
    async (id: string, patch: { name?: string; notes?: string; raw_text?: string }) => {
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

  // 下載歌曲為 .txt 檔案
  const downloadSong = useCallback((song: SongDetail) => {
    const content = [
      `Song: ${song.name}`,
      song.brand && song.model ? `Device: ${song.brand} ${song.model}` : "",
      song.notes ? `\nNotes:\n${song.notes}` : "",
      `\n---\n`,
      song.raw_text,
    ]
      .filter(Boolean)
      .join("\n");

    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${song.name.replace(/[^a-z0-9]/gi, "_")}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }, []);

  return {
    songs,
    filteredSongs,
    searchQuery,
    setSearchQuery,
    selectedSong,
    loading,
    detailLoading,
    fetchSongs,
    selectSong,
    deleteSong,
    updateSong,
    downloadSong,
  };
}