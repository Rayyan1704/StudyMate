# 📁 StudyMate AI - Project Structure

## Overview

StudyMate AI is organized into a clean, modular architecture with clear separation of concerns. This document provides a comprehensive overview of the project structure.

## Root Directory

```
StudyMate/
├── 📄 README.md                 # Main project documentation
├── 📄 USER_GUIDE.txt            # Comprehensive user guide
├── 📄 INSTALLATION.md           # Installation instructions
├── 📄 PROJECT_STRUCTURE.md      # This file
├── 📄 DEPLOYMENT_GUIDE.md       # Production deployment guide
├── 📄 LICENSE                   # MIT License
├── 📄 .gitignore               # Git ignore rules
├── 📄 .env.example             # Environment template
├── 📄 .env                     # Environment variables (create from .env.example)
├── 📄 requirements.txt         # Python dependencies
├── 📄 requirements-core.txt    # Core dependencies only
├── 📄 requirements-optional.txt # Optional features
├── 🚀 main.py                  # FastAPI application entry point
├── 🚀 quick_start.py           # Easy startup script
├── 🚀 run_studymate.py         # Alternative startup script
├── 🚀 start_studymate.py       # Cross-platform startup
├── 🚀 start_studymate.bat      # Windows batch script
├── 🚀 start_studymate.sh       # Linux/Mac shell script
└── 📊 studymate_v2.db          # SQLite database (auto-created)
```

## Core Application (`/core/`)

The heart of StudyMate's AI functionality:

```
core/
├── 🧠 ai_engine.py             # Main AI processing engine
├── 🔍 rag_engine.py            # RAG (Retrieval-Augmented Generation)
├── 🎤 voice_handler.py         # Voice input/output processing
├── 📝 session_manager.py       # Session and conversation management
├── 🧠 memory_manager.py        # User memory and context tracking
├── 📊 analytics_engine.py      # Learning analytics and insights
├── ⏰ reminder_system.py       # Study reminders and notifications
├── 📄 document_processor.py    # File processing and text extraction
├── 📝 notes_generator.py       # Structured note generation
└── 🔧 local_rag.py            # Local RAG implementation
```

### Key Components Explained:

- **`ai_engine.py`**: Central AI coordinator, handles mode switching and response generation
- **`rag_engine.py`**: Document embedding, vector search, and context retrieval
- **`voice_handler.py`**: Speech-to-text and text-to-speech functionality
- **`session_manager.py`**: Manages chat sessions, message storage, and user context
- **`memory_manager.py`**: Tracks learning patterns and user preferences

## Database Layer (`/database/`)

```
database/
└── 🗄️ db_manager.py            # SQLite database operations and schema
```

Handles all database operations including:
- User management
- Session storage
- Message persistence
- Analytics data
- Document metadata

## Data Models (`/models/`)

```
models/
└── 📋 api_models.py            # Pydantic models for API requests/responses
```

Defines data structures for:
- Chat messages and responses
- User sessions
- Document metadata
- API request/response formats

## Web Interface (`/templates/`)

```
templates/
└── 🌐 index.html               # Main web application interface
```

Single-page application with:
- Dark aesthetic design
- Responsive layout
- Real-time chat interface
- Document management UI

## Frontend Assets (`/static/`)

```
static/
├── css/
│   └── 🎨 dark-theme.css       # Dark aesthetic styling
├── js/
│   ├── 🚀 main.js              # Core application logic
│   ├── 💬 sessions.js          # Session management
│   ├── 🎤 voice.js             # Voice features
│   ├── 📄 documents.js         # Document handling
│   ├── 🎨 themes.js            # Theme customization
│   └── 🔧 utils.js             # Utility functions
├── 📱 manifest.json            # PWA manifest
└── ⚙️ sw.js                   # Service worker
```

### Frontend Architecture:

- **`main.js`**: Application initialization, message handling, UI updates
- **`sessions.js`**: Session creation, switching, and management
- **`voice.js`**: Voice input/output, speech recognition
- **`documents.js`**: File upload, document viewer, content management
- **`themes.js`**: Color customization, theme switching
- **`utils.js`**: Common utilities, API helpers, notifications

## Data Directories

These directories are created automatically during runtime:

```
StudyMate/
├── 📁 uploads/                 # Uploaded documents (auto-created)
├── 📁 rag_storage/            # Vector embeddings and indices (auto-created)
├── 📁 backups/                # Database backups (auto-created)
└── 📁 exports/                # Exported notes and sessions (auto-created)
```

## Configuration Files

### Environment Configuration (`.env`)
```env
# Required
GEMINI_API_KEY=your_key_here

# Optional
ELEVENLABS_API_KEY=your_key_here
DEBUG=True
PORT=8080
MAX_FILE_SIZE_MB=50
```

### Dependencies (`requirements.txt`)
- **Core**: FastAPI, Uvicorn, Pydantic
- **AI/ML**: Google Generative AI, Sentence Transformers, FAISS
- **Document Processing**: PyMuPDF, python-docx, python-pptx
- **Voice**: OpenAI Whisper, ElevenLabs
- **Database**: SQLAlchemy, Alembic

## API Architecture

### RESTful Endpoints
- `/api/chat` - Chat messaging
- `/api/sessions/*` - Session management
- `/api/documents/*` - Document operations
- `/api/voice/*` - Voice processing
- `/api/notes/*` - Note generation

### WebSocket Connections
- `/ws/chat/{user_id}` - Real-time chat communication

## Data Flow

```
User Input → Frontend (JS) → FastAPI Backend → AI Engine → Response
                ↓                    ↓              ↓
            Local Storage ← Database ← Session Manager
                ↓                    ↓              ↓
            Documents → RAG Engine → Vector Store → Context
```

## Security Architecture

### Data Protection
- **Local Processing**: Documents processed locally using RAG
- **API Key Security**: Environment variables, never in code
- **Session Isolation**: Each session maintains separate context
- **Input Validation**: Pydantic models validate all inputs

### Privacy Features
- **No Data Sharing**: Documents never leave your system
- **Local Storage**: All data stored in local SQLite database
- **Minimal Cloud Usage**: Only AI API calls go external

## Development Workflow

### Adding New Features

1. **Backend Changes**:
   - Add models to `models/api_models.py`
   - Implement logic in appropriate `core/` module
   - Add API endpoints to `main.py`

2. **Frontend Changes**:
   - Add UI elements to `templates/index.html`
   - Implement logic in appropriate `static/js/` file
   - Update styles in `static/css/dark-theme.css`

3. **Database Changes**:
   - Update schema in `database/db_manager.py`
   - Add migration logic if needed

### Testing Strategy
- **Unit Tests**: Test individual components
- **Integration Tests**: Test API endpoints
- **UI Tests**: Test frontend functionality
- **Performance Tests**: Test with large documents

## Deployment Architecture

### Development
```
Local Machine → Python Process → SQLite → Local Files
```

### Production Options
```
Server → Docker Container → External Database → Cloud Storage
   ↓           ↓                    ↓              ↓
Nginx → Load Balancer → Multiple Instances → Shared Storage
```

## Performance Considerations

### Optimization Points
- **Document Processing**: Chunking strategy, embedding caching
- **Database**: Indexing, query optimization
- **Frontend**: Lazy loading, virtual scrolling
- **Memory**: Garbage collection, resource cleanup

### Scalability
- **Horizontal**: Multiple FastAPI instances
- **Vertical**: Increase server resources
- **Database**: PostgreSQL for production
- **Storage**: Cloud storage for documents

## Monitoring & Logging

### Log Locations
- **Application Logs**: Console output
- **Error Logs**: Exception tracking
- **Access Logs**: API request logging
- **Performance Logs**: Response time tracking

### Metrics to Monitor
- **Response Times**: API endpoint performance
- **Memory Usage**: Application resource consumption
- **Document Processing**: Upload and processing times
- **User Activity**: Session creation and usage patterns

---

This structure provides a solid foundation for an AI-powered learning assistant while maintaining clean separation of concerns and scalability for future enhancements.