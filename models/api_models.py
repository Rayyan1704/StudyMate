"""
StudyMate API Models - Complete Pydantic models for all endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

# ============================================================================
# ENUMS
# ============================================================================

class ChatMode(str, Enum):
    CHAT = "chat"
    TUTOR = "tutor"
    NOTES = "notes"
    QUIZ = "quiz"

class ReminderType(str, Enum):
    STUDY = "study"
    REVISION = "revision"
    DEADLINE = "deadline"
    BREAK = "break"

class ExportFormat(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    MARKDOWN = "markdown"
    HTML = "html"

# ============================================================================
# CHAT MODELS
# ============================================================================

class ChatRequest(BaseModel):
    message: str = Field(..., description="User's message")
    user_id: str = Field(default="default", description="User identifier")
    session_id: str = Field(default="default", description="Session identifier")
    mode: ChatMode = Field(default=ChatMode.CHAT, description="Chat mode")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    voice_input: bool = Field(default=False, description="Whether input was voice")

class ChatResponse(BaseModel):
    content: str = Field(..., description="AI response content")
    source: str = Field(..., description="Response source (gemini, rag, etc.)")
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    mode: ChatMode = Field(default=ChatMode.CHAT, description="Chat mode used")
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Response metadata")

# ============================================================================
# DOCUMENT MODELS
# ============================================================================

class UploadResponse(BaseModel):
    success: bool = Field(..., description="Upload success status")
    message: str = Field(..., description="Status message")
    file_info: Optional[Dict[str, Any]] = Field(default=None, description="File information")
    chunks_created: int = Field(default=0, description="Number of text chunks created")

class DocumentInfo(BaseModel):
    filename: str
    upload_date: datetime
    file_size: int
    chunks_count: int
    processed: bool

# ============================================================================
# VOICE MODELS
# ============================================================================

class TTSRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize")
    voice_id: Optional[str] = Field(default=None, description="Voice ID for synthesis")
    language: str = Field(default="en", description="Language code")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech speed")

class VoiceResponse(BaseModel):
    audio_url: str = Field(..., description="URL to generated audio")
    duration: Optional[float] = Field(default=None, description="Audio duration in seconds")

# ============================================================================
# SESSION MODELS
# ============================================================================

class CreateSessionRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    title: Optional[str] = Field(default=None, description="Session title")
    mode: ChatMode = Field(default=ChatMode.CHAT, description="Session mode")

class UpdateSessionRequest(BaseModel):
    title: Optional[str] = Field(default=None, description="New session title")
    archived: Optional[bool] = Field(default=None, description="Archive status")

class SessionResponse(BaseModel):
    id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    title: str = Field(..., description="Session title")
    mode: ChatMode = Field(..., description="Session mode")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    message_count: int = Field(default=0, description="Number of messages")
    archived: bool = Field(default=False, description="Archive status")

# ============================================================================
# ANALYTICS MODELS
# ============================================================================

class AnalyticsResponse(BaseModel):
    user_id: str
    total_queries: int
    total_sessions: int
    study_time_minutes: float
    learning_streak_days: int
    subjects_studied: List[str]
    weak_topics: List[str]
    strong_topics: List[str]
    recent_activity: List[Dict[str, Any]]
    performance_trends: Dict[str, Any]
    daily_stats: List[Dict[str, Any]]

class DashboardData(BaseModel):
    today_queries: int
    week_queries: int
    total_study_time: float
    active_sessions: int
    documents_uploaded: int
    learning_streak: int
    top_subjects: List[Dict[str, Any]]
    recent_sessions: List[Dict[str, Any]]
    performance_chart: List[Dict[str, Any]]

# ============================================================================
# REMINDER MODELS
# ============================================================================

class CreateReminderRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    title: str = Field(..., description="Reminder title")
    description: Optional[str] = Field(default=None, description="Reminder description")
    scheduled_time: datetime = Field(..., description="When to trigger reminder")
    reminder_type: ReminderType = Field(default=ReminderType.STUDY, description="Type of reminder")
    repeat_pattern: Optional[str] = Field(default=None, description="Repeat pattern (daily, weekly, etc.)")

class ReminderResponse(BaseModel):
    id: str = Field(..., description="Reminder ID")
    user_id: str = Field(..., description="User ID")
    title: str = Field(..., description="Reminder title")
    description: Optional[str] = Field(default=None, description="Reminder description")
    scheduled_time: datetime = Field(..., description="Scheduled time")
    reminder_type: ReminderType = Field(..., description="Reminder type")
    is_active: bool = Field(default=True, description="Active status")
    created_at: datetime = Field(..., description="Creation timestamp")

# ============================================================================
# NOTES & EXPORT MODELS
# ============================================================================

class GenerateNotesRequest(BaseModel):
    topic: str = Field(..., description="Topic for note generation")
    user_id: str = Field(..., description="User identifier")
    format_type: str = Field(default="markdown", description="Output format")
    detail_level: str = Field(default="medium", description="Detail level (basic, medium, detailed)")
    include_examples: bool = Field(default=True, description="Include examples")
    include_diagrams: bool = Field(default=False, description="Include text diagrams")

class ExportNotesRequest(BaseModel):
    content: str = Field(..., description="Content to export")
    format_type: ExportFormat = Field(..., description="Export format")
    filename: str = Field(..., description="Output filename")
    include_metadata: bool = Field(default=True, description="Include metadata")

class NotesResponse(BaseModel):
    content: str = Field(..., description="Generated notes content")
    format_type: str = Field(..., description="Content format")
    word_count: int = Field(..., description="Word count")
    topics_covered: List[str] = Field(..., description="Topics covered")
    generated_at: datetime = Field(default_factory=datetime.now)

# ============================================================================
# USER PREFERENCES MODELS
# ============================================================================

class UserPreferences(BaseModel):
    theme: str = Field(default="light", description="UI theme")
    language: str = Field(default="en", description="Interface language")
    voice_enabled: bool = Field(default=True, description="Voice features enabled")
    notifications_enabled: bool = Field(default=True, description="Notifications enabled")
    auto_save: bool = Field(default=True, description="Auto-save conversations")
    privacy_mode: bool = Field(default=False, description="Enhanced privacy mode")
    preferred_voice: Optional[str] = Field(default=None, description="Preferred TTS voice")
    study_reminders: bool = Field(default=True, description="Study reminders enabled")

class UpdatePreferencesRequest(BaseModel):
    preferences: UserPreferences = Field(..., description="User preferences to update")

# ============================================================================
# QUIZ MODELS
# ============================================================================

class QuizQuestion(BaseModel):
    question: str = Field(..., description="Question text")
    options: List[str] = Field(..., description="Answer options")
    correct_answer: int = Field(..., description="Index of correct answer")
    explanation: str = Field(..., description="Explanation of correct answer")
    difficulty: str = Field(default="medium", description="Question difficulty")
    topic: str = Field(..., description="Question topic")

class GenerateQuizRequest(BaseModel):
    topic: str = Field(..., description="Quiz topic")
    user_id: str = Field(..., description="User identifier")
    question_count: int = Field(default=5, ge=1, le=20, description="Number of questions")
    difficulty: str = Field(default="medium", description="Quiz difficulty")
    include_explanations: bool = Field(default=True, description="Include explanations")

class QuizResponse(BaseModel):
    quiz_id: str = Field(..., description="Quiz identifier")
    title: str = Field(..., description="Quiz title")
    questions: List[QuizQuestion] = Field(..., description="Quiz questions")
    total_questions: int = Field(..., description="Total number of questions")
    estimated_time: int = Field(..., description="Estimated completion time in minutes")
    created_at: datetime = Field(default_factory=datetime.now)

class SubmitQuizRequest(BaseModel):
    quiz_id: str = Field(..., description="Quiz identifier")
    user_id: str = Field(..., description="User identifier")
    answers: List[int] = Field(..., description="User's answers (indices)")
    time_taken: int = Field(..., description="Time taken in seconds")

class QuizResultResponse(BaseModel):
    quiz_id: str = Field(..., description="Quiz identifier")
    score: float = Field(..., description="Score percentage")
    correct_answers: int = Field(..., description="Number of correct answers")
    total_questions: int = Field(..., description="Total questions")
    time_taken: int = Field(..., description="Time taken in seconds")
    detailed_results: List[Dict[str, Any]] = Field(..., description="Detailed question results")
    recommendations: List[str] = Field(..., description="Study recommendations")

# ============================================================================
# SYSTEM MODELS
# ============================================================================

class SystemStatus(BaseModel):
    status: str = Field(..., description="System status")
    version: str = Field(..., description="Application version")
    uptime: float = Field(..., description="Uptime in seconds")
    components: Dict[str, bool] = Field(..., description="Component status")
    features: Dict[str, bool] = Field(..., description="Feature availability")

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.now)