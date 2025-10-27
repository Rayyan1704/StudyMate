"""
StudyMate Session Manager - Multi-Chat Session Management
Handles ChatGPT-style multiple conversation sessions
"""

import os
import uuid
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path

class SessionManager:
    """Advanced session management for multi-chat functionality"""
    
    def __init__(self, db_manager):
        print("🗂️ Initializing Session Manager...")
        
        self.db_manager = db_manager
        self.max_sessions_per_user = int(os.getenv("MAX_SESSIONS_PER_USER", 100))
        self.session_timeout_minutes = int(os.getenv("SESSION_TIMEOUT_MINUTES", 60))
        self.auto_archive_days = int(os.getenv("AUTO_ARCHIVE_INACTIVE_DAYS", 30))
        
        # In-memory session cache for active sessions
        self.active_sessions = {}  # session_id -> session_data
        
        print(f"✅ Session Manager ready - Max sessions: {self.max_sessions_per_user}")
        
        # Initialize message storage table
        self._init_message_storage()
    
    async def create_session(
        self, 
        user_id: str, 
        title: Optional[str] = None,
        mode: str = "chat"
    ) -> Dict[str, Any]:
        """Create a new chat session"""
        
        try:
            # Generate unique session ID
            session_id = str(uuid.uuid4())
            
            # Auto-generate title if not provided
            if not title:
                session_count = await self._get_user_session_count(user_id)
                title = f"Chat Session {session_count + 1}"
            
            # Check session limit
            if session_count >= self.max_sessions_per_user:
                # Archive oldest inactive session
                await self._archive_oldest_session(user_id)
            
            # Create session record
            session_data = {
                "id": session_id,
                "user_id": user_id,
                "title": title,
                "mode": mode,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "message_count": 0,
                "archived": False,
                "metadata": {
                    "created_from": "web",
                    "initial_mode": mode
                }
            }
            
            # Save to database
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO chat_sessions 
                (id, user_id, title, mode, created_at, updated_at, message_count, archived, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                user_id,
                title,
                mode,
                session_data["created_at"].isoformat(),
                session_data["updated_at"].isoformat(),
                0,
                False,
                json.dumps(session_data["metadata"])
            ))
            
            conn.commit()
            conn.close()
            
            # Add to active sessions cache
            self.active_sessions[session_id] = session_data
            
            print(f"✅ Created session: {session_id} for user: {user_id}")
            
            return {
                "id": session_id,
                "user_id": user_id,
                "title": title,
                "mode": mode,
                "created_at": session_data["created_at"].isoformat(),
                "updated_at": session_data["updated_at"].isoformat(),
                "message_count": 0,
                "archived": False
            }
            
        except Exception as e:
            print(f"❌ Error creating session: {e}")
            raise
    
    async def get_user_sessions(
        self, 
        user_id: str, 
        include_archived: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all sessions for a user"""
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Build query
            query = '''
                SELECT id, title, mode, created_at, updated_at, message_count, archived, metadata
                FROM chat_sessions
                WHERE user_id = ?
            '''
            params = [user_id]
            
            if not include_archived:
                query += ' AND archived = 0'
            
            query += ' ORDER BY updated_at DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            sessions = []
            for row in rows:
                session_id, title, mode, created_at, updated_at, message_count, archived, metadata = row
                
                # Parse metadata
                try:
                    metadata_dict = json.loads(metadata) if metadata else {}
                except:
                    metadata_dict = {}
                
                sessions.append({
                    "id": session_id,
                    "title": title,
                    "mode": mode,
                    "created_at": created_at,
                    "updated_at": updated_at,
                    "message_count": message_count,
                    "archived": bool(archived),
                    "metadata": metadata_dict
                })
            
            return sessions
            
        except Exception as e:
            print(f"❌ Error getting user sessions: {e}")
            return []
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get specific session details"""
        
        try:
            # Check cache first
            if session_id in self.active_sessions:
                return self.active_sessions[session_id]
            
            # Query database
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, user_id, title, mode, created_at, updated_at, message_count, archived, metadata
                FROM chat_sessions
                WHERE id = ?
            ''', (session_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            session_id, user_id, title, mode, created_at, updated_at, message_count, archived, metadata = row
            
            session_data = {
                "id": session_id,
                "user_id": user_id,
                "title": title,
                "mode": mode,
                "created_at": created_at,
                "updated_at": updated_at,
                "message_count": message_count,
                "archived": bool(archived),
                "metadata": json.loads(metadata) if metadata else {}
            }
            
            # Add to cache if active
            if not archived:
                self.active_sessions[session_id] = session_data
            
            return session_data
            
        except Exception as e:
            print(f"❌ Error getting session: {e}")
            return None
    
    async def update_session(
        self, 
        session_id: str, 
        title: Optional[str] = None,
        archived: Optional[bool] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Update session details"""
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Build update query
            updates = []
            params = []
            
            if title is not None:
                updates.append("title = ?")
                params.append(title)
            
            if archived is not None:
                updates.append("archived = ?")
                params.append(archived)
            
            if metadata is not None:
                updates.append("metadata = ?")
                params.append(json.dumps(metadata))
            
            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            
            params.append(session_id)
            
            query = f"UPDATE chat_sessions SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            # Update cache
            if session_id in self.active_sessions:
                if title is not None:
                    self.active_sessions[session_id]["title"] = title
                if archived is not None:
                    self.active_sessions[session_id]["archived"] = archived
                    if archived:
                        # Remove from active cache if archived
                        del self.active_sessions[session_id]
                if metadata is not None:
                    self.active_sessions[session_id]["metadata"].update(metadata)
            
            return success
            
        except Exception as e:
            print(f"❌ Error updating session: {e}")
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages"""
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Delete messages first (foreign key constraint)
            cursor.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
            
            # Delete session
            cursor.execute('DELETE FROM chat_sessions WHERE id = ?', (session_id,))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            # Remove from cache
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            print(f"🗑️ Deleted session: {session_id}")
            return success
            
        except Exception as e:
            print(f"❌ Error deleting session: {e}")
            return False
    
    async def increment_message_count(self, session_id: str) -> bool:
        """Increment message count for a session"""
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE chat_sessions 
                SET message_count = message_count + 1, updated_at = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), session_id))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            # Update cache
            if session_id in self.active_sessions:
                self.active_sessions[session_id]["message_count"] += 1
                self.active_sessions[session_id]["updated_at"] = datetime.now()
            
            return success
            
        except Exception as e:
            print(f"❌ Error incrementing message count: {e}")
            return False
    
    async def get_session_messages(
        self, 
        session_id: str, 
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get messages for a session"""
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, content, role, source, timestamp, metadata
                FROM messages
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            ''', (session_id, limit, offset))
            
            rows = cursor.fetchall()
            conn.close()
            
            messages = []
            for row in rows:
                msg_id, content, role, source, timestamp, metadata = row
                
                messages.append({
                    "id": msg_id,
                    "content": content,
                    "role": role,
                    "source": source,
                    "timestamp": timestamp,
                    "metadata": json.loads(metadata) if metadata else {}
                })
            
            # Reverse to get chronological order
            return list(reversed(messages))
            
        except Exception as e:
            print(f"❌ Error getting session messages: {e}")
            return []
    
    async def save_message(
        self,
        session_id: str,
        content: str,
        role: str,
        source: str = "",
        metadata: Dict[str, Any] = None,
        timestamp: str = None
    ) -> bool:
        """Save a message to a session"""
        
        try:
            if metadata is None:
                metadata = {}
            
            if timestamp is None:
                timestamp = datetime.now().isoformat()
            
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Ensure user exists first
            cursor.execute('''
                INSERT OR IGNORE INTO users (id, username, email, created_at)
                VALUES (?, ?, ?, ?)
            ''', ("web_user", "web_user", "web_user@studymate.ai", timestamp))
            
            # Ensure session exists first - with better error handling
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO chat_sessions 
                    (id, user_id, title, mode, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (session_id, "web_user", f"Chat Session", "chat", timestamp, timestamp))
                
                # Verify session was created/exists
                cursor.execute('SELECT id FROM chat_sessions WHERE id = ?', (session_id,))
                if not cursor.fetchone():
                    print(f"❌ Failed to create/find session: {session_id}")
                    return False
                    
            except Exception as session_error:
                print(f"❌ Session creation error: {session_error}")
                return False
            
            # Save message (let SQLite auto-generate the ID)
            cursor.execute('''
                INSERT INTO messages 
                (session_id, user_id, content, role, source, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                "web_user",  # Add user_id
                content,
                role,
                source,
                timestamp,
                json.dumps(metadata)
            ))
            
            # Update session's updated_at and message count
            cursor.execute('''
                UPDATE chat_sessions 
                SET updated_at = ?, message_count = message_count + 1
                WHERE id = ?
            ''', (timestamp, session_id))
            
            conn.commit()
            conn.close()
            
            print(f"💾 Saved message to session {session_id}: {content[:50]}...")
            return True
            
        except Exception as e:
            print(f"❌ Error saving message: {e}")
            return False
    
    def _init_message_storage(self):
        """Initialize message storage table"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Create messages table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    role TEXT NOT NULL,
                    source TEXT DEFAULT '',
                    timestamp TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE
                )
            ''')
            
            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_messages_session_timestamp 
                ON messages (session_id, timestamp)
            ''')
            
            conn.commit()
            conn.close()
            
            print("✅ Message storage initialized")
            
        except Exception as e:
            print(f"❌ Error initializing message storage: {e}")
    
    async def search_sessions(
        self, 
        user_id: str, 
        query: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search sessions by title or content"""
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Search in session titles and message content
            cursor.execute('''
                SELECT DISTINCT s.id, s.title, s.mode, s.created_at, s.updated_at, s.message_count
                FROM chat_sessions s
                LEFT JOIN messages m ON s.id = m.session_id
                WHERE s.user_id = ? AND s.archived = 0
                AND (s.title LIKE ? OR m.content LIKE ?)
                ORDER BY s.updated_at DESC
                LIMIT ?
            ''', (user_id, f"%{query}%", f"%{query}%", limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            sessions = []
            for row in rows:
                session_id, title, mode, created_at, updated_at, message_count = row
                
                sessions.append({
                    "id": session_id,
                    "title": title,
                    "mode": mode,
                    "created_at": created_at,
                    "updated_at": updated_at,
                    "message_count": message_count
                })
            
            return sessions
            
        except Exception as e:
            print(f"❌ Error searching sessions: {e}")
            return []
    
    async def _get_user_session_count(self, user_id: str) -> int:
        """Get total number of sessions for user"""
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) FROM chat_sessions 
                WHERE user_id = ? AND archived = 0
            ''', (user_id,))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
            
        except Exception as e:
            print(f"❌ Error getting session count: {e}")
            return 0
    
    async def _archive_oldest_session(self, user_id: str) -> bool:
        """Archive the oldest inactive session"""
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Find oldest session
            cursor.execute('''
                SELECT id FROM chat_sessions
                WHERE user_id = ? AND archived = 0
                ORDER BY updated_at ASC
                LIMIT 1
            ''', (user_id,))
            
            row = cursor.fetchone()
            if row:
                oldest_session_id = row[0]
                
                # Archive it
                cursor.execute('''
                    UPDATE chat_sessions 
                    SET archived = 1, updated_at = ?
                    WHERE id = ?
                ''', (datetime.now().isoformat(), oldest_session_id))
                
                conn.commit()
                
                # Remove from cache
                if oldest_session_id in self.active_sessions:
                    del self.active_sessions[oldest_session_id]
                
                print(f"📦 Archived oldest session: {oldest_session_id}")
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error archiving oldest session: {e}")
            return False
    
    async def cleanup_inactive_sessions(self) -> int:
        """Clean up inactive sessions (run periodically)"""
        
        try:
            cutoff_time = datetime.now() - timedelta(days=self.auto_archive_days)
            
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Archive inactive sessions
            cursor.execute('''
                UPDATE chat_sessions 
                SET archived = 1, updated_at = ?
                WHERE archived = 0 AND updated_at < ?
            ''', (datetime.now().isoformat(), cutoff_time.isoformat()))
            
            archived_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            # Clear from cache
            inactive_sessions = [
                session_id for session_id, session_data in self.active_sessions.items()
                if session_data["updated_at"] < cutoff_time
            ]
            
            for session_id in inactive_sessions:
                del self.active_sessions[session_id]
            
            if archived_count > 0:
                print(f"📦 Auto-archived {archived_count} inactive sessions")
            
            return archived_count
            
        except Exception as e:
            print(f"❌ Error cleaning up sessions: {e}")
            return 0
    
    async def get_session_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get session statistics for user"""
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Total sessions
            cursor.execute('''
                SELECT COUNT(*) FROM chat_sessions WHERE user_id = ?
            ''', (user_id,))
            total_sessions = cursor.fetchone()[0]
            
            # Active sessions
            cursor.execute('''
                SELECT COUNT(*) FROM chat_sessions WHERE user_id = ? AND archived = 0
            ''', (user_id,))
            active_sessions = cursor.fetchone()[0]
            
            # Total messages
            cursor.execute('''
                SELECT SUM(message_count) FROM chat_sessions WHERE user_id = ?
            ''', (user_id,))
            total_messages = cursor.fetchone()[0] or 0
            
            # Most active session
            cursor.execute('''
                SELECT id, title, message_count FROM chat_sessions
                WHERE user_id = ? AND archived = 0
                ORDER BY message_count DESC
                LIMIT 1
            ''', (user_id,))
            
            most_active = cursor.fetchone()
            most_active_session = None
            
            if most_active:
                most_active_session = {
                    "id": most_active[0],
                    "title": most_active[1],
                    "message_count": most_active[2]
                }
            
            conn.close()
            
            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "archived_sessions": total_sessions - active_sessions,
                "total_messages": total_messages,
                "avg_messages_per_session": round(total_messages / max(1, total_sessions), 1),
                "most_active_session": most_active_session
            }
            
        except Exception as e:
            print(f"❌ Error getting session statistics: {e}")
            return {}