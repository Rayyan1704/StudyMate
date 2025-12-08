# StudyMate AI

StudyMate is a FastAPI-based learning companion with a dark, modern UI. It combines Gemini-powered chat, retrieval-augmented document Q&A, session-based memory, analytics, and optional voice features to help students learn faster.

## Highlights
- Multi-mode chat (chat, tutor, notes, quiz) with Gemini routing and session context.
- Local document ingestion (PDF, DOCX, PPTX, TXT) with FAISS/embedding search.
- Session-aware memory and analytics backed by SQLite.
- Optional voice pipeline (Whisper STT + ElevenLabs TTS).
- PWA-style dark UI with keyboard shortcuts and customizable themes.

## Tech Stack
- Backend: FastAPI, Uvicorn, SQLite
- AI: Gemini API, sentence-transformers, FAISS (optional)
- Voice: Whisper (optional), ElevenLabs (optional)
- Frontend: Vanilla JS, HTML, CSS (dark-theme), WebSocket/REST

## Project Structure
```
StudyMate/
├── main.py                  # FastAPI app + routes
├── quick_start.py           # Convenience launcher
├── core/                    # AI + domain logic
│   ├── ai_engine.py         # Gemini + routing + RAG orchestration
│   ├── document_processor.py# File parsing
│   ├── rag_engine.py        # Embedding + retrieval
│   ├── voice_handler.py     # Whisper/ElevenLabs integration
│   ├── session_manager.py   # Session persistence helpers
│   ├── memory_manager.py    # Interaction storage
│   ├── analytics_engine.py  # Analytics aggregation
│   └── reminder_system.py   # Reminder scheduling
├── database/db_manager.py   # SQLite schema + helpers
├── models/                  # Pydantic schemas
├── templates/index.html     # Main UI
└── static/                  # JS/CSS/assets
```

## Prerequisites
- Python 3.10+ (3.11 recommended)
- pip / venv
- Gemini API key (required for full AI responses)
- (Optional) FAISS CPU, Whisper, ElevenLabs key for voice/TTS

## Setup
```bash
git clone https://github.com/Rayyan1704/StudyMate.git
cd StudyMate

# Create virtual env (recommended)
python -m venv .venv
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate # macOS/Linux

# Install dependencies (single file)
pip install -r requirements.txt
```

Copy the env template and add your keys:
```bash
cp .env.example .env
# edit .env and set at least GEMINI_API_KEY
```

Key environment variables:
```
GEMINI_API_KEY=<required>
ELEVENLABS_API_KEY=<optional for TTS>
DEBUG=false
HOST=0.0.0.0
PORT=8080
MAX_FILE_SIZE_MB=50
UPLOAD_DIR=uploads
DB_BACKUP_ENABLED=true
```

## Running
```bash
# Development (auto-reload)
uvicorn main:app --reload --host 0.0.0.0 --port 8080

# Production-ish
python main.py
```
Open http://localhost:8080 to use the UI. API docs: http://localhost:8080/api/docs.

## Usage
1. Create a session from the sidebar (Ctrl/Cmd+N).
2. Upload study materials (PDF/DOCX/PPTX/TXT up to 50 MB).
3. Chat in any mode (Chat/Tutor/Notes/Quiz). The model automatically uses uploaded context when relevant.
4. Use keyboard shortcuts: Ctrl/Cmd+Enter to send, Ctrl/Cmd+U to toggle upload, Ctrl+Shift+V for voice input (if enabled).

## Notes on Data & Storage
- Documents and embeddings are stored locally under `rag_storage/`.
- Uploaded files reside in `uploads/` (created automatically).
- SQLite database defaults to `studymate_v2.db`. Backups are optional via env flags.
- No data is sent to third parties except Gemini/ElevenLabs calls you enable.

## Development
- Set `DEBUG=true` in `.env` for auto-reload and verbose logs.
- Core logic entrypoints:
  - Chat flow: `main.py` → `AIEngine.process_query`
  - Document ingestion: `AIEngine.process_document` → `DocumentProcessor` → `RAGEngine`
  - Voice: `VoiceHandler` (requires optional deps)
- Frontend scripts live in `static/js/` and are vanilla JS for easy tweaking.

## Troubleshooting
- “AI engine not ready”: ensure `GEMINI_API_KEY` is set and restart.
- Upload fails: verify file type (PDF/DOCX/PPTX/TXT) and size (<50 MB).
- Voice disabled: install optional deps and set `ELEVENLABS_API_KEY`.
- If embeddings are missing after cleanup, simply re-upload documents.

## Roadmap
- Responsive/mobile refinements
- Collaborative sessions
- Enhanced analytics dashboard
- Plugin system for custom AI models
- Multi-language UI

## License
MIT License. See `LICENSE` for details.
