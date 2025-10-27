"""
StudyMate AI - Complete Personalized Learning Companion
A cross-platform AI assistant for students with ChatGPT-style interface
"""

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import os
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import uuid

# Import our core modules
from core.ai_engine import AIEngine
from core.voice_handler import VoiceHandler
from core.memory_manager import MemoryManager
from core.analytics_engine import AnalyticsEngine
from core.reminder_system import ReminderSystem
from core.session_manager import SessionManager
from models.api_models import *
from database.db_manager import DatabaseManager

# Initialize FastAPI with metadata
app = FastAPI(
    title="StudyMate AI",
    description="Personalized AI Learning Companion for Students",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global components (initialized on startup)
ai_engine: Optional[AIEngine] = None
voice_handler: Optional[VoiceHandler] = None
memory_manager: Optional[MemoryManager] = None
analytics_engine: Optional[AnalyticsEngine] = None
reminder_system: Optional[ReminderSystem] = None
session_manager: Optional[SessionManager] = None
db_manager: Optional[DatabaseManager] = None

# WebSocket connections for real-time features
active_connections: Dict[str, WebSocket] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize all StudyMate components"""
    global ai_engine, voice_handler, memory_manager, analytics_engine
    global reminder_system, session_manager, db_manager
    
    print("🚀 Initializing StudyMate AI v2.0...")
    
    # Create necessary directories
    for directory in ["static", "templates", "uploads", "exports", "backups", "logs"]:
        Path(directory).mkdir(exist_ok=True)
    
    # Initialize core components
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    ai_engine = AIEngine()
    voice_handler = VoiceHandler()
    memory_manager = MemoryManager(db_manager)
    analytics_engine = AnalyticsEngine(db_manager)
    reminder_system = ReminderSystem(db_manager)
    session_manager = SessionManager(db_manager)
    
    print("✅ StudyMate AI is ready!")
    print("🎓 Features: AI Chat, Voice, Analytics, Reminders, Multi-Sessions")
    # Note: Actual URL will be shown by the startup script

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 StudyMate AI shutting down...")

# ============================================================================
# MAIN WEB INTERFACE
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main StudyMate interface"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/chat/{session_id}", response_class=HTMLResponse)
async def chat_session(request: Request, session_id: str):
    """Load specific chat session"""
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "session_id": session_id
    })

# ============================================================================
# AI CHAT API
# ============================================================================

@app.post("/api/chat")
async def chat_endpoint(request: dict):
    """Main AI chat endpoint with smart routing"""
    try:
        if not ai_engine:
            raise HTTPException(status_code=503, detail="AI engine not ready")
        
        # Extract request data
        message = request.get('message', '')
        user_id = request.get('user_id', 'web_user')
        session_id = request.get('session_id', 'default')
        mode = request.get('mode', 'chat')
        context = request.get('context', {})
        
        # Enhance message based on mode
        enhanced_message = enhance_message_by_mode(message, mode, context)
        
        # Process the query through AI engine
        response = await ai_engine.process_query(
            query=enhanced_message,
            user_id=user_id,
            session_id=session_id,
            mode=mode,
            context=context
        )
        
        # Store interaction in memory
        if memory_manager:
            await memory_manager.store_interaction(
                user_id=user_id,
                session_id=session_id,
                query=message,
                response=response.content,
                mode=mode,
                metadata=response.metadata
            )
        
        # Update analytics
        if analytics_engine:
            await analytics_engine.track_interaction(
                user_id=user_id,
                session_id=session_id,
                query_type=response.source,
                response_time=response.metadata.get("response_time", 0)
            )
        
        # Return response as dict for JSON serialization
        return {
            "content": response.content,
            "source": response.source,
            "session_id": response.session_id,
            "user_id": response.user_id,
            "mode": response.mode,
            "metadata": response.metadata
        }
        
    except Exception as e:
        print(f"❌ Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/chat/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: str):
    """WebSocket for real-time chat features"""
    await websocket.accept()
    active_connections[user_id] = websocket
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process through AI engine
            if ai_engine:
                response = await ai_engine.process_query(
                    query=message_data["message"],
                    user_id=user_id,
                    session_id=message_data.get("session_id", "default"),
                    mode=message_data.get("mode", "chat")
                )
                
                # Send response back
                await websocket.send_text(json.dumps({
                    "type": "response",
                    "content": response.content,
                    "source": response.source,
                    "metadata": response.metadata
                }))
                
    except WebSocketDisconnect:
        if user_id in active_connections:
            del active_connections[user_id]

# ============================================================================
# DOCUMENT MANAGEMENT
# ============================================================================

@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Form("web_user"),
    session_id: str = Form("default")
):
    """Upload and process documents for RAG"""
    try:
        if not ai_engine:
            raise HTTPException(status_code=503, detail="AI engine not ready")
        
        # Validate file
        max_size = int(os.getenv("MAX_FILE_SIZE_MB", 50)) * 1024 * 1024
        content = await file.read()
        
        if len(content) > max_size:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Max size: {max_size // (1024*1024)}MB"
            )
        
        # Save and process file
        result = await ai_engine.process_document(
            file_content=content,
            filename=file.filename,
            user_id=user_id,
            session_id=session_id
        )
        
        return {
            "id": str(uuid.uuid4()),
            "filename": file.filename,
            "file_size": len(content),
            "upload_date": datetime.now().isoformat(),
            "status": "processed" if result["success"] else "error",
            "chunk_count": result.get("chunks_created", 0),
            "message": result["message"]
        }
        
    except Exception as e:
        print(f"❌ Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents")
async def get_documents(user_id: str = "web_user"):
    """Get user's uploaded documents"""
    try:
        if not ai_engine:
            return []
        
        docs = await ai_engine.get_user_documents(user_id)
        return docs.get("documents", [])
        
    except Exception as e:
        print(f"❌ Get documents error: {e}")
        return []

@app.get("/api/documents/{doc_id}/content")
async def get_document_content(doc_id: str, user_id: str = "web_user"):
    """Get document content for viewing"""
    try:
        if not ai_engine:
            raise HTTPException(status_code=503, detail="AI engine not ready")
        
        # For now, return a placeholder since we don't store original content
        # In a full implementation, you'd retrieve the original document content
        return {
            "content": "Document content viewing is not fully implemented yet. The document has been processed and is available for AI queries.",
            "metadata": {
                "doc_id": doc_id,
                "message": "Content extracted and processed for AI analysis"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str, user_id: str = "web_user"):
    """Delete a specific document"""
    try:
        if not ai_engine:
            raise HTTPException(status_code=503, detail="AI engine not ready")
        
        # For now, just return success (implement actual deletion in ai_engine)
        return {"success": True, "message": "Document deleted"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/documents/clear")
async def clear_all_documents(user_id: str = "web_user"):
    """Clear all user documents"""
    try:
        if not ai_engine:
            raise HTTPException(status_code=503, detail="AI engine not ready")
        
        result = await ai_engine.clear_user_documents(user_id)
        return {"success": result, "message": "All documents cleared"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# VOICE FEATURES
# ============================================================================

@app.post("/api/voice/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """Speech-to-text transcription"""
    try:
        if not voice_handler:
            raise HTTPException(status_code=503, detail="Voice handler not ready")
        
        # Save audio temporarily
        temp_path = f"temp_audio_{uuid.uuid4()}.wav"
        with open(temp_path, "wb") as f:
            f.write(await audio.read())
        
        # Transcribe
        transcription = await voice_handler.transcribe_audio(temp_path)
        
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)
        
        return {"transcription": transcription}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/voice/speak")
async def synthesize_speech(request: dict):
    """Text-to-speech synthesis"""
    try:
        if not voice_handler:
            raise HTTPException(status_code=503, detail="Voice handler not ready")
        
        text = request.get("text", "")
        voice_id = request.get("voice_id", "default")
        
        audio_path = await voice_handler.text_to_speech(
            text=text,
            voice_id=voice_id,
            language="en"
        )
        
        return FileResponse(
            path=audio_path,
            media_type="audio/mpeg",
            filename="speech.mp3"
        )
        
    except Exception as e:
        print(f"❌ TTS error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

@app.get("/api/sessions")
async def get_sessions(user_id: str = "web_user"):
    """Get all chat sessions for user"""
    try:
        if not session_manager:
            # Return mock sessions for now
            return [
                {
                    "id": "default",
                    "title": "General Chat",
                    "mode": "chat",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "last_message": "Welcome to StudyMate AI!"
                }
            ]
        
        sessions = await session_manager.get_user_sessions(user_id)
        return sessions
        
    except Exception as e:
        print(f"❌ Get sessions error: {e}")
        return []

@app.post("/api/sessions")
async def create_session(request: dict):
    """Create new chat session"""
    try:
        session_id = str(uuid.uuid4())
        session = {
            "id": session_id,
            "title": request.get("title", "New Chat"),
            "mode": request.get("mode", "chat"),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "last_message": ""
        }
        
        return session
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    """Get messages for a specific session"""
    try:
        if session_manager:
            messages = await session_manager.get_session_messages(session_id)
            return messages
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sessions/{session_id}/messages")
async def save_session_message(session_id: str, request: dict):
    """Save a message to a session"""
    try:
        if session_manager:
            await session_manager.save_message(
                session_id=session_id,
                content=request.get("content", ""),
                role=request.get("role", "user"),
                source=request.get("source", ""),
                metadata=request.get("metadata", {}),
                timestamp=request.get("timestamp")
            )
            return {"success": True}
        return {"success": False, "error": "Session manager not available"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/sessions/{session_id}")
async def update_session(session_id: str, request: dict):
    """Update session details"""
    try:
        # For now, just return success
        return {"success": True}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    try:
        # For now, just return success
        return {"success": True}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ANALYTICS & INSIGHTS
# ============================================================================

@app.get("/api/analytics/{user_id}")
async def get_analytics(user_id: str, days: int = 30):
    """Get comprehensive learning analytics"""
    try:
        if not analytics_engine:
            return {"error": "Analytics not available"}
        
        analytics = await analytics_engine.generate_analytics(user_id, days)
        return analytics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/{user_id}/dashboard")
async def get_dashboard_data(user_id: str):
    """Get dashboard analytics data"""
    try:
        if not analytics_engine:
            return {"error": "Analytics not available"}
        
        dashboard = await analytics_engine.get_dashboard_data(user_id)
        return dashboard
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# REMINDERS & NOTIFICATIONS
# ============================================================================

@app.get("/api/reminders/{user_id}")
async def get_reminders(user_id: str):
    """Get user reminders"""
    try:
        if not reminder_system:
            return {"reminders": []}
        
        reminders = await reminder_system.get_user_reminders(user_id)
        return {"reminders": reminders}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reminders")
async def create_reminder(request: CreateReminderRequest):
    """Create new reminder"""
    try:
        if not reminder_system:
            raise HTTPException(status_code=503, detail="Reminder system not ready")
        
        reminder = await reminder_system.create_reminder(
            user_id=request.user_id,
            title=request.title,
            description=request.description,
            scheduled_time=request.scheduled_time,
            reminder_type=request.reminder_type,
            repeat_pattern=request.repeat_pattern
        )
        
        return {"success": True, "reminder_id": reminder["id"]}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# NOTES & EXPORTS
# ============================================================================

@app.post("/api/notes/generate")
async def generate_notes(request: GenerateNotesRequest):
    """Generate study notes from topic or document"""
    try:
        if not ai_engine:
            raise HTTPException(status_code=503, detail="AI engine not ready")
        
        notes = await ai_engine.generate_notes(
            topic=request.topic,
            user_id=request.user_id,
            format_type=request.format_type,
            detail_level=request.detail_level,
            include_examples=request.include_examples
        )
        
        return {"notes": notes, "format": request.format_type}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export/notes")
async def export_notes(request: ExportNotesRequest):
    """Export notes as PDF or DOCX"""
    try:
        if not ai_engine:
            raise HTTPException(status_code=503, detail="AI engine not ready")
        
        file_path = await ai_engine.export_notes(
            content=request.content,
            format_type=request.format_type,
            filename=request.filename
        )
        
        return FileResponse(
            path=file_path,
            filename=request.filename,
            media_type='application/octet-stream'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# SYSTEM & HEALTH
# ============================================================================

@app.get("/api/health")
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "components": {
            "ai_engine": ai_engine is not None,
            "voice_handler": voice_handler is not None,
            "memory_manager": memory_manager is not None,
            "analytics_engine": analytics_engine is not None,
            "reminder_system": reminder_system is not None,
            "session_manager": session_manager is not None,
            "database": db_manager is not None
        },
        "features": {
            "gemini_available": ai_engine.gemini_available if ai_engine else False,
            "voice_available": voice_handler.available if voice_handler else False,
            "faiss_available": ai_engine.faiss_available if ai_engine else False
        }
    }

@app.get("/api/config")
async def get_config():
    """Get app configuration"""
    return {
        "app_name": "StudyMate AI",
        "version": "2.0.0",
        "features": {
            "voice_enabled": True,
            "analytics_enabled": True,
            "reminders_enabled": True,
            "multi_session": True,
            "themes": True,
            "export": True
        },
        "limits": {
            "max_file_size_mb": int(os.getenv("MAX_FILE_SIZE_MB", 50)),
            "max_sessions": 50,
            "max_reminders": 100
        }
    }

def enhance_message_by_mode(message: str, mode: str, context: dict) -> str:
    """Enhance user message based on the selected mode"""
    
    chat_history = context.get('chat_history', [])
    has_uploads = context.get('has_uploads', False)
    
    # Build context from chat history
    history_context = ""
    if chat_history:
        recent_messages = chat_history[-6:]  # Last 3 exchanges
        history_context = "\n\nPrevious conversation context:\n"
        for msg in recent_messages:
            role = "User" if msg['role'] == 'user' else "Assistant"
            history_context += f"{role}: {msg['content'][:200]}...\n"
    
    mode_instructions = {
        'chat': f"""You are StudyMate AI, a helpful learning companion. Provide clear, informative responses.
{history_context}

User question: {message}""",
        
        'tutor': f"""You are StudyMate AI in Tutor Mode. Provide detailed, step-by-step explanations like an expert teacher.

INSTRUCTIONS:
- Break down complex concepts into simple, understandable parts
- Use examples and analogies to illustrate points
- Provide structured explanations with clear headings
- Include practice questions or exercises when appropriate
- Reference previous conversation context when relevant

{history_context}

Student question: {message}

Please provide a comprehensive tutorial explanation.""",
        
        'notes': f"""You are StudyMate AI in Notes Mode. Create comprehensive, well-structured study notes.

INSTRUCTIONS:
- Format like professional textbook notes with clear headings
- Use bullet points, numbered lists, and proper structure
- Include key concepts, definitions, and important details
- Add examples and practical applications
- Create a summary or conclusion section
- Make notes suitable for studying and review

{history_context}

Based on our conversation and the topic: {message}

Please create comprehensive study notes.""",
        
        'quiz': f"""You are StudyMate AI in Quiz Mode. Create engaging quizzes to test understanding.

INSTRUCTIONS:
- Generate questions based on our previous conversation topics
- Include multiple choice, short answer, and explanation questions
- Vary difficulty levels from basic to advanced
- Provide correct answers and explanations
- Make questions practical and application-focused

{history_context}

Topic for quiz: {message}

Please create an interactive quiz with varied question types."""
    }
    
    enhanced_message = mode_instructions.get(mode, mode_instructions['chat'])
    
    # Add document context if available
    if has_uploads:
        enhanced_message += "\n\nNote: Use information from uploaded documents when relevant to provide accurate, specific answers."
    
    return enhanced_message

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )