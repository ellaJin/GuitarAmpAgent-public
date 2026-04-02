// src/pages/Songs/SongLibrary.tsx
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import "./SongLibrary.css";
import { useSongLibrary } from "./useSongLibrary";

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

export default function SongLibrary() {
  const navigate = useNavigate();
  const { songs, selectedSong, loading, detailLoading, selectSong, deleteSong, updateSong } =
    useSongLibrary();

  const [editingName, setEditingName] = useState(false);
  const [nameInput, setNameInput] = useState("");
  const [notesInput, setNotesInput] = useState("");
  const [editingNotes, setEditingNotes] = useState(false);

  const handleSelectSong = async (id: string) => {
    setEditingName(false);
    setEditingNotes(false);
    await selectSong(id);
  };

  const handleEditName = () => {
    if (!selectedSong) return;
    setNameInput(selectedSong.name);
    setEditingName(true);
  };

  const handleSaveName = async () => {
    if (!selectedSong) return;
    await updateSong(selectedSong.id, { name: nameInput.trim() || selectedSong.name });
    setEditingName(false);
  };

  const handleEditNotes = () => {
    if (!selectedSong) return;
    setNotesInput(selectedSong.notes ?? "");
    setEditingNotes(true);
  };

  const handleSaveNotes = async () => {
    if (!selectedSong) return;
    await updateSong(selectedSong.id, { notes: notesInput });
    setEditingNotes(false);
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("Delete this song from the library?")) return;
    await deleteSong(id);
  };

  return (
    <div className="songs-root">
      {/* Left: list */}
      <div className="songs-list-panel">
        <div className="songs-list-header">
          <span className="songs-list-title">Song Library</span>
          <button className="songs-back-btn" onClick={() => navigate("/chat")}>
            ← Back to Chat
          </button>
        </div>

        <div className="songs-list-scroll">
          {loading && <div className="songs-empty">Loading...</div>}
          {!loading && songs.length === 0 && (
            <div className="songs-empty">No songs saved yet. Use "Save to Library" on an AI response.</div>
          )}
          {songs.map((s) => (
            <button
              key={s.id}
              className={`song-list-item${selectedSong?.id === s.id ? " active" : ""}`}
              onClick={() => handleSelectSong(s.id)}
              type="button"
            >
              <span className="song-item-name">{s.name}</span>
              <span className="song-item-meta">
                {s.brand && s.model ? `${s.brand} ${s.model} · ` : ""}
                {formatDate(s.created_at)}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Right: detail */}
      <div className="songs-detail-panel">
        {!selectedSong && !detailLoading && (
          <div className="songs-detail-empty">Select a song to view details</div>
        )}

        {detailLoading && (
          <div className="songs-detail-empty">Loading...</div>
        )}

        {selectedSong && !detailLoading && (
          <div className="songs-detail-scroll">
            {/* Header: name + actions */}
            <div className="songs-detail-header">
              <div>
                <div className="songs-detail-name-row">
                  {editingName ? (
                    <>
                      <input
                        className="songs-detail-name-input"
                        value={nameInput}
                        onChange={(e) => setNameInput(e.target.value)}
                        autoFocus
                        onKeyDown={(e) => {
                          if (e.key === "Enter") handleSaveName();
                          if (e.key === "Escape") setEditingName(false);
                        }}
                      />
                      <button className="songs-save-btn" onClick={handleSaveName}>Save</button>
                      <button className="songs-cancel-btn" onClick={() => setEditingName(false)}>Cancel</button>
                    </>
                  ) : (
                    <>
                      <span className="songs-detail-name">{selectedSong.name}</span>
                      <button className="songs-edit-btn" onClick={handleEditName}>Rename</button>
                    </>
                  )}
                </div>
                {selectedSong.brand && selectedSong.model && (
                  <div className="songs-detail-device">{selectedSong.brand} {selectedSong.model}</div>
                )}
                <div className="songs-detail-date">Saved {formatDate(selectedSong.created_at)}</div>
              </div>

              <button
                className="songs-delete-btn"
                onClick={() => handleDelete(selectedSong.id)}
                type="button"
              >
                Delete
              </button>
            </div>

            {/* Notes */}
            <div className="songs-notes-label">Notes</div>
            {editingNotes ? (
              <>
                <textarea
                  className="songs-notes-textarea"
                  value={notesInput}
                  onChange={(e) => setNotesInput(e.target.value)}
                  placeholder="Add your notes..."
                  autoFocus
                />
                <div className="songs-notes-actions">
                  <button className="songs-save-btn" onClick={handleSaveNotes}>Save</button>
                  <button className="songs-cancel-btn" onClick={() => setEditingNotes(false)}>Cancel</button>
                </div>
              </>
            ) : (
              <>
                <textarea
                  className="songs-notes-textarea"
                  value={selectedSong.notes ?? ""}
                  readOnly
                  placeholder="No notes. Click to add..."
                  onClick={handleEditNotes}
                  style={{ cursor: "pointer" }}
                />
              </>
            )}

            {/* AI response rendered as markdown */}
            <div className="songs-markdown-body">
              <ReactMarkdown>{selectedSong.raw_text}</ReactMarkdown>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
