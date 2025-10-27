"""
Pydantic models for chat and API requests/responses
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class ChatRequest(BaseModel):
    message: str
    user_id: str = "default"
    session_id: str = "default"
    has_uploads: bool = False
    voice_input: bool = False

class ChatResponse(BaseModel):
    content: str
    source: str  # "local_rag" or "gemini"
    session_id: str
    user_id: str
    timestamp: datetime = datetime.now()
    metadata: Optional[Dict[str, Any]] = None

class UploadResponse(BaseModel):
    success: bool
    message: str
    file_info: Optional[Dict[str, Any]] = None

class VoiceRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None
    user_id: str = "default"

class VoiceResponse(BaseModel):
    audio_url: str
    duration: Optional[float] = None

class AnalyticsResponse(BaseModel):
    user_id: str
    total_queries: int
    total_sessions: int
    subjects_studied: List[str]
    time_spent_minutes: float
    learning_streak_days: int
    weak_topics: List[str]
    strong_topics: List[str]
    recent_activity: List[Dict[str, Any]]

class ReminderRequest(BaseModel):
    user_id: str
    title: str
    message: str
    scheduled_time: datetime
    reminder_type: str = "study"  # study, revision, deadline

class ReminderResponse(BaseModel):
    id: str
    title: str
    message: str
    scheduled_time: datetime
    created_at: datetime
    is_active: bool