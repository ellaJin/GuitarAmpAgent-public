# 🎸 Guitar Effects AI Assistant

An AI-powered assistant that helps guitarists configure effects pedals and multi-effects processors. Upload a device manual, and the system automatically extracts effects, MIDI mappings, and knowledge — then provides personalized setup recommendations through natural conversation.

> *"I want to play Hotel California solo, help me set up my effects"*
> → Device-specific amp models, delay settings, reverb types, and signal chain — all grounded in your actual device's manual.

---

## ✨ Key Features

### 🤖 Intelligent Effects Advisor
Ask natural language questions and receive device-specific recommendations — amp models, delay/reverb settings, signal chain order — all retrieved from your device's ingested manual via RAG.

### 📄 Automated Manual Ingestion Pipeline
Upload a PDF manual and the system automatically:
- **Chunks & embeds** the document for RAG-based retrieval (Qwen embeddings + pgvector)
- **Extracts effects** using a brand-aware LLM pipeline with pluggable strategies (Line 6 Helix, Boss, Mooer, and extensible)
- **Extracts MIDI mappings** (CC numbers, channels, parameter ranges) for supported devices
- Supports multiple document types per device: `User Manual`, `Effects Settings`, and `Mixed`

### 🎵 Song Library
Save AI-generated effect configurations to a personal song library. Each entry preserves the full Markdown response linked to the device it was created for. Rename, annotate, and manage saved presets from a dedicated page.

### 💬 Persistent Chat History
Full conversation persistence with sidebar navigation. Start new chats, revisit past conversations, and continue where you left off.

### 🎛️ Multi-Device Management
Bind multiple devices to your account and switch the active device at any time. The AI automatically adapts its knowledge base and recommendations to the active device.

### 🔧 Admin Dashboard
- Upload and ingest new device manuals with real-time status tracking
- Monitor ingestion, effects extraction, and MIDI extraction progress per document
- Link/unlink additional documents to existing devices (multi-document support)

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│                      Frontend (React)                     │
│   Chat │ Onboarding │ Song Library │ My Devices │ Admin  │
└─────────────────────────┬────────────────────────────────┘
                          │ REST API (JWT Auth)
┌─────────────────────────▼────────────────────────────────┐
│                    Backend (FastAPI)                       │
│                                                           │
│  ┌───────────┐  ┌───────────────┐  ┌──────────────────┐  │
│  │  Chat +   │  │  Ingestion    │  │  Brand Strategy   │  │
│  │  RAG      │  │  Worker       │  │  Router           │  │
│  └───────────┘  └───────┬───────┘  └────────┬─────────┘  │
│                         │                    │            │
│          ┌──────────────▼────────────────────▼────────┐  │
│          │         LLM Extraction Pipelines            │  │
│          │   ┌──────────────┐  ┌───────────────────┐  │  │
│          │   │   Effects    │  │       MIDI        │  │  │
│          │   │   Pipeline   │  │     Pipeline      │  │  │
│          │   └──────────────┘  └───────────────────┘  │  │
│          └────────────────────────────────────────────┘  │
└─────────────────────────┬────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────┐
│               PostgreSQL 16 + pgvector                    │
│                                                           │
│  device_models │ kb_sources │ documents │ chunks (vector) │
│  raw_effect_entries │ raw_midi_entries │ conversations     │
│  messages │ songs │ user_devices │ users                   │
└──────────────────────────────────────────────────────────┘
```

### Ingestion Pipeline

```
PDF Upload
    │
    ▼
 Chunking ──→ Embedding (Qwen) ──→ chunks table (pgvector)
    │
    ├──→ Effect Extraction Pipeline
    │      Brand Router → Strategy (Line6 / Boss / Generic)
    │      Page Gate → LLM Prompt → Post-process → Bulk Upsert
    │
    └──→ MIDI Extraction Pipeline (if device supports MIDI)
           Same brand router → MIDI-specific prompts
           Range validation (0–127 / ch 1–16) → Bulk Upsert
```

### Brand Strategy Pattern

Extraction pipelines use a **strategy pattern** for brand-specific behavior:

| Strategy | Effects | MIDI | Chunking Profile |
|----------|---------|------|-----------------|
| **Line6 Helix** | Custom keyword gates, chunk-ref linking | Full support, address-based dedup | HELIX_COARSE |
| **Boss** | Standard extraction | Not supported | BOSS_FINE (450 tokens) |
| **Generic** | Default extraction | Not supported | DEFAULT_MED (800 tokens) |

Adding a new brand = one new strategy class. No pipeline code changes required.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React, TypeScript, React Router, React Markdown |
| **Backend** | Python, FastAPI, background task workers |
| **Database** | PostgreSQL 16 + pgvector |
| **Embeddings** | Qwen (document chunk vectorization) |
| **LLM** | Effects/MIDI extraction prompts, chat responses |
| **Auth** | JWT (HS256) |
| **Infrastructure** | Docker Compose |

---

## 🔄 Core User Flows

### New User
```
Register → Login → Select Device (from admin-activated catalog) → Chat
```

### Returning User
```
Login → Bootstrap checks active device → Chat (auto-resume)
```

### Admin: Add Device
```
Upload PDF → Auto-ingest (chunk + embed + extract effects/MIDI) → Device available to users
```

### Save Preset
```
Chat → AI recommends effects setup → "Save to Library" → Song Library (with device context)
```

---

## 📐 Database Schema

| Table | Purpose |
|-------|---------|
| `device_models` | Device catalog (brand, model, variant, image) |
| `kb_sources` | Knowledge base sources linked to devices |
| `documents` | Uploaded PDF manuals |
| `chunks` | Embedded document chunks (pgvector) |
| `raw_effect_entries` | LLM-extracted effects per device |
| `raw_midi_entries` | LLM-extracted MIDI CC mappings |
| `users` | User accounts (email + password hash) |
| `user_devices` | User↔device bindings with `is_active` flag |
| `conversations` | Chat session metadata |
| `messages` | Individual chat messages (user + assistant) |
| `songs` | Saved effect presets (Song Library) |
| `kb_ingestion_jobs` | Async ingestion job status tracking |

---

## 📁 Project Structure

```
GuitarAmpAgent/
├── backend/
│   └── src/app/
│       ├── dao/                  # Data access layer (PostgreSQL)
│       ├── service/              # Business logic
│       ├── routers/              # FastAPI endpoints
│       │   ├── auth.py           # Register, login, JWT
│       │   ├── chat.py           # Chat + RAG retrieval
│       │   ├── devices.py        # Device binding & listing
│       │   ├── conversations.py  # Chat history CRUD
│       │   ├── songs.py          # Song Library CRUD
│       │   └── admin_device.py   # Admin device management
│       └── effects/
│           ├── pipeline.py       # Effects extraction pipeline
│           ├── strategy_router.py
│           ├── strategies/       # Brand-specific strategies
│           │   ├── base.py
│           │   └── line6_helix.py
│           └── midi/
│               └── pipeline.py   # MIDI extraction pipeline
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Chat/             # Chat interface + sidebar
│       │   ├── Onboarding/       # Device selection flow
│       │   ├── Songs/            # Song Library
│       │   ├── MyDevices/        # Multi-device management
│       │   └── Admin/            # Admin dashboard
│       └── lib/
│           └── api.ts            # Axios client with JWT interceptor
└── docker-compose.yml            # PostgreSQL (pgvector/pgvector:pg16)
```

---

## 🚀 Quick Start

```bash
# Start the database
docker compose up -d db

# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

App available at `http://localhost:5173`

### Restore from Database Dump

```bash
docker cp agentdb_dump.dump <container>:/tmp/agentdb_dump.dump
docker exec <container> pg_restore -U <user> -d <dbname> --no-owner --no-privileges /tmp/agentdb_dump.dump
```

---

## 📜 License

This project is part of an academic portfolio. All rights reserved.
