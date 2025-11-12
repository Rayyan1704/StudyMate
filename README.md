# 🎓 StudyMate AI - Your Personal Learning Companion

A modern AI-powered study assistant with dark aesthetic design that helps students learn smarter through intelligent conversation, document analysis, and multi-modal AI interaction.

## ✨ Features

- **📚 Smart Document Processing**: Upload PDFs, DOCX, PPTX, and TXT files and chat with your documents
- **🤖 Multi-Mode AI Chat**: 4 specialized modes - Chat, Tutor, Notes, and Quiz generation
- **🗣️ Voice Interaction**: Full speech-to-text and text-to-speech capabilities
- **🎨 Dark Aesthetic UI**: Beautiful dark theme with customizable colors
- **💾 Session Management**: Organize conversations by topic with persistent storage
- **🔍 Advanced RAG**: Local document processing with FAISS vector search
- **⚡ Real-time Processing**: Fast document analysis and instant AI responses
- **🎯 Context-Aware**: AI remembers your documents and conversation history per session

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/Rayyan1704/StudyMate.git
cd StudyMate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file and add your API keys
# Minimum required: GEMINI_API_KEY
```

### 3. Run StudyMate

**Option 1: Quick Start (Recommended)**
```bash
python quick_start.py
```

**Option 2: Manual Start**
```bash
python main.py
```

**Option 3: Using Start Scripts**
```bash
# Windows
start_studymate.bat

# Linux/Mac
./start_studymate.sh

# Python script
python start_studymate.py
```

Visit `http://localhost:8080` in your browser to start learning!

## 🔧 Configuration

### Required API Keys

1. **Gemini API Key** (Required)
   - Get from: https://makersuite.google.com/app/apikey
   - Add to `.env`: `GEMINI_API_KEY=your_key_here`

2. **ElevenLabs API Key** (Optional - for premium voice)
   - Get from: https://elevenlabs.io/
   - Add to `.env`: `ELEVENLABS_API_KEY=your_key_here`

### Environment Variables (.env)

```env
# Core AI (Required)
GEMINI_API_KEY=your_gemini_api_key_here

# Voice Features (Optional)
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Application Settings
DEBUG=False
HOST=0.0.0.0
PORT=8080

# File Upload Settings
MAX_FILE_SIZE_MB=50
UPLOAD_DIR=uploads

# Database Settings
DB_CLEANUP_OLD_DATA_DAYS=90
DB_BACKUP_ENABLED=True
```

## 📖 How to Use StudyMate

### 1. Create Your First Session
- Click the "+" button next to "Chats" in the sidebar
- Give your session a descriptive name (e.g., "Physics Chapter 5")
- Click "Create Session" or press Enter

### 2. Choose Your AI Mode
- **💬 Chat Mode**: General conversation and Q&A
- **👨‍🏫 Tutor Mode**: Detailed educational explanations with examples
- **📝 Notes Mode**: Generate structured study notes and summaries
- **❓ Quiz Mode**: Create practice questions and tests

### 3. Upload Study Materials
- Click the paperclip icon (📎) in the message input
- Upload PDF, DOCX, PPTX, or TXT files (up to 50MB)
- Wait for processing (you'll see progress indicators)
- Ask questions about your uploaded content

### 4. Voice Interaction
- Click the microphone icon (🎤) for voice input
- Use Ctrl+Shift+V keyboard shortcut
- Toggle voice output with the speaker icon in settings

### 5. Customize Your Experience
- Click the palette icon (🎨) to customize colors
- Adjust voice settings in the voice menu
- Switch between different accent colors and themes

## 🏗️ Architecture

### Smart AI Routing
- **Session-Based RAG**: Documents processed per session for better context
- **Multi-Modal Processing**: Text, voice, and document analysis
- **Intelligent Mode Switching**: AI adapts responses based on selected mode

### Core Components
- **FastAPI Backend**: High-performance async API
- **FAISS Vector Store**: Local document embeddings and search
- **SQLite Database**: Session and user data management
- **Sentence Transformers**: Local embedding generation
- **Whisper Integration**: Speech-to-text processing
- **ElevenLabs TTS**: High-quality text-to-speech

## 📁 Project Structure

```
StudyMate/
├── main.py                    # FastAPI application entry point
├── quick_start.py            # Easy startup script
├── requirements.txt          # Python dependencies
├── USER_GUIDE.txt           # Comprehensive user guide
├── .env.example             # Environment template
├── core/                    # Core AI components
│   ├── ai_engine.py         # Main AI processing engine
│   ├── rag_engine.py        # RAG and document processing
│   ├── voice_handler.py     # Voice input/output
│   ├── session_manager.py   # Session management
│   ├── memory_manager.py    # User memory and context
│   ├── analytics_engine.py  # Learning analytics
│   └── reminder_system.py   # Study reminders
├── database/                # Database management
│   └── db_manager.py        # SQLite operations
├── models/                  # Data models
│   └── api_models.py        # Pydantic models
├── templates/               # HTML templates
│   └── index.html           # Main web interface
└── static/                  # Frontend assets
    ├── css/
    │   └── dark-theme.css   # Dark aesthetic styling
    └── js/
        ├── main.js          # Core application logic
        ├── sessions.js      # Session management
        ├── voice.js         # Voice features
        ├── documents.js     # Document handling
        ├── themes.js        # Theme customization
        └── utils.js         # Utility functions
```

## 🔌 API Endpoints

### Chat & AI
- `POST /api/chat` - Send messages to AI
- `WebSocket /ws/chat/{user_id}` - Real-time chat connection

### Document Management
- `POST /api/documents/upload` - Upload documents
- `GET /api/documents` - List user documents
- `GET /api/documents/{doc_id}/content` - View document content
- `DELETE /api/documents/{doc_id}` - Delete document

### Session Management
- `GET /api/sessions` - List user sessions
- `POST /api/sessions` - Create new session
- `PUT /api/sessions/{session_id}` - Update session
- `DELETE /api/sessions/{session_id}` - Delete session
- `GET /api/sessions/{session_id}/messages` - Get session messages

### Voice Features
- `POST /api/voice/transcribe` - Speech-to-text
- `POST /api/voice/synthesize` - Text-to-speech

### Analytics & Notes
- `POST /api/notes/generate` - Generate study notes
- `GET /api/analytics/{user_id}` - Learning analytics

## 🎯 Key Features Explained

### Session-Based Learning
- Each session maintains its own document context
- AI remembers previous conversations within sessions
- Perfect isolation between different study topics

### Advanced Document Processing
- Automatic text extraction from multiple formats
- Intelligent chunking for better context retrieval
- Vector embeddings for semantic search

### Multi-Mode AI Responses
- **Chat**: Conversational and friendly responses
- **Tutor**: Detailed explanations with examples and step-by-step guidance
- **Notes**: Structured, organized study materials
- **Quiz**: Interactive questions and knowledge testing

### Voice Integration
- Browser-based speech recognition
- Optional ElevenLabs integration for premium voice quality
- Keyboard shortcuts for quick voice activation

## 🔒 Privacy & Security

- **Local Processing**: Documents processed locally using RAG
- **Session Isolation**: Each study session maintains separate context
- **Minimal Cloud Usage**: Only AI API calls go to external services
- **Data Control**: All conversations and documents stored locally
- **No Data Sharing**: Your study materials never leave your control

## 🛠️ Development

### Running in Development Mode

```bash
# Set debug mode in .env
DEBUG=True

# Start with auto-reload
python main.py

# View API documentation
http://localhost:8080/docs
```

### Adding New Features

1. **New AI Models**: Extend `core/ai_engine.py`
2. **File Formats**: Update `core/document_processor.py`
3. **Database Schema**: Modify `database/db_manager.py`
4. **Frontend Features**: Add to `static/js/` files

## 📱 Browser Compatibility

- **Chrome/Chromium**: Full feature support including voice
- **Firefox**: Full support with voice features
- **Safari**: Full support (voice features may vary)
- **Edge**: Full feature support

## 🚧 Roadmap

- [ ] Mobile-responsive design improvements
- [ ] Collaborative study sessions
- [ ] Advanced analytics dashboard
- [ ] Plugin system for custom AI models
- [ ] Multi-language interface support
- [ ] Export/import session data
- [ ] Advanced document annotation tools

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🆘 Troubleshooting

### Common Issues

1. **"AI engine not ready"**
   - Check your `GEMINI_API_KEY` in `.env`
   - Ensure internet connection
   - Restart the application

2. **Voice features not working**
   - Check microphone permissions
   - Use HTTPS or localhost
   - Try refreshing the page

3. **Document upload fails**
   - Check file size (max 50MB)
   - Verify file format is supported
   - Ensure sufficient disk space

4. **Sessions not saving**
   - Create a named session (don't use default)
   - Check browser local storage
   - Clear browser cache if needed

See `USER_GUIDE.txt` for detailed troubleshooting steps.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Google Gemini AI** for powerful language processing
- **Sentence Transformers** for local embeddings
- **FAISS** for efficient vector search
- **FastAPI** for the robust backend framework
- **ElevenLabs** for premium voice synthesis

## 📞 Support

- 📖 Read the `USER_GUIDE.txt` for comprehensive usage instructions
- 🐛 Report bugs by creating GitHub issues
- 💡 Request features through GitHub discussions
- 📧 For other inquiries, check the repository contact information

---

**Transform your learning experience with AI-powered assistance! 🎓✨**

*StudyMate AI - Where artificial intelligence meets academic excellence.*
