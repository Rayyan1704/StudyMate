"""
StudyMate Database Manager - Enhanced Database Management
Handles all database operations with comprehensive schema and optimization
"""

import os
import sqlite3
import asyncio
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import json

class DatabaseManager:
    """Enhanced database manager with comprehensive schema"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.getenv("DATABASE_FILE", "studymate_v2.db")
        
        self.db_path = db_path
        self.db_dir = Path(db_path).parent
        self.db_dir.mkdir(exist_ok=True)
        
        # Database configuration
        self.backup_enabled = os.getenv("DB_BACKUP_ENABLED", "True").lower() == "true"
        self.backup_interval_hours = int(os.getenv("DB_BACKUP_INTERVAL_HOURS", 24))
        
        print(f"🗄️ Database Manager initialized - Path: {db_path}")
    
    async def initialize(self):
        """Initialize database with comprehensive schema"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Enable foreign keys and performance optimizations
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("PRAGMA journal_mode = WAL")
            cursor.execute("PRAGMA synchronous = NORMAL")
            cursor.execute("PRAGMA cache_size = 10000")
            cursor.execute("PRAGMA temp_store = MEMORY")
            
            # Core tables
            await self._create_core_tables(cursor)
            
            # Memory and analytics tables
            await self._create_memory_tables(cursor)
            
            # Session and interaction tables
            await self._create_session_tables(cursor)
            
            # Document and RAG tables
            await self._create_document_tables(cursor)
            
            # Reminder and notification tables
            await self._create_reminder_tables(cursor)
            
            # Create indexes for performance
            await self._create_indexes(cursor)
            
            # Create triggers for data integrity
            await self._create_triggers(cursor)
            
            conn.commit()
            conn.close()
            
            print("✅ Database initialized with comprehensive schema")
            
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            raise
    
    async def _create_core_tables(self, cursor):
        """Create core user and system tables"""
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE,
                email TEXT UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_active DATETIME DEFAULT CURRENT_TIMESTAMP,
                preferences TEXT DEFAULT '{}',
                is_active BOOLEAN DEFAULT 1,
                subscription_tier TEXT DEFAULT 'free'
            )
        ''')
        
        # User preferences table (enhanced)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id TEXT PRIMARY KEY,
                preferences TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # System configuration table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                description TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    async def _create_memory_tables(self, cursor):
        """Create memory and learning pattern tables"""
        
        # User interactions table (enhanced)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                query TEXT NOT NULL,
                response TEXT NOT NULL,
                source TEXT NOT NULL,
                mode TEXT DEFAULT 'chat',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT DEFAULT '{}',
                response_time REAL DEFAULT 0.0,
                satisfaction_rating INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Learning patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_patterns (
                user_id TEXT PRIMARY KEY,
                pattern_data TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # User context table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_context (
                user_id TEXT PRIMARY KEY,
                last_topics TEXT,
                last_mode TEXT,
                last_activity DATETIME,
                interaction_count INTEGER DEFAULT 0,
                context_data TEXT DEFAULT '{}',
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # User achievements table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                achievement_type TEXT NOT NULL,
                achievement_data TEXT NOT NULL,
                earned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Analytics interactions table (for detailed analytics)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                query_type TEXT NOT NULL,
                response_time REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
    
    async def _create_session_tables(self, cursor):
        """Create session and message tables"""
        
        # Chat sessions table (enhanced)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT,
                mode TEXT DEFAULT 'chat',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                message_count INTEGER DEFAULT 0,
                archived BOOLEAN DEFAULT 0,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Messages table (enhanced)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                content TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                source TEXT DEFAULT 'unknown',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT DEFAULT '{}',
                edited_at DATETIME,
                parent_message_id INTEGER,
                FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (parent_message_id) REFERENCES messages (id)
            )
        ''')
    
    async def _create_document_tables(self, cursor):
        """Create document and RAG-related tables"""
        
        # Documents table (enhanced)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER,
                upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                processed BOOLEAN DEFAULT 0,
                chunk_count INTEGER DEFAULT 0,
                processing_status TEXT DEFAULT 'pending',
                error_message TEXT,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Document chunks table (for RAG)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_chunks (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding_vector TEXT,
                metadata TEXT DEFAULT '{}',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
    
    async def _create_reminder_tables(self, cursor):
        """Create reminder and notification tables"""
        
        # Reminders table (enhanced)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                scheduled_time DATETIME NOT NULL,
                reminder_type TEXT DEFAULT 'study',
                repeat_pattern TEXT,
                is_completed BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                snooze_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Notifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                notification_type TEXT DEFAULT 'info',
                is_read BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                read_at DATETIME,
                action_url TEXT,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
    
    async def _create_indexes(self, cursor):
        """Create database indexes for performance optimization"""
        
        # User-related indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_last_active ON users(last_active)')
        
        # Interaction indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_interactions_user ON interactions(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_interactions_session ON interactions(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_interactions_timestamp ON interactions(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_interactions_source ON interactions(source)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_interactions_mode ON interactions(mode)')
        
        # Session indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user ON chat_sessions(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_updated ON chat_sessions(updated_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_archived ON chat_sessions(archived)')
        
        # Message indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role)')
        
        # Document indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_user ON documents(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(file_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_processed ON documents(processed)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_upload_date ON documents(upload_date)')
        
        # Chunk indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_chunks_document ON document_chunks(document_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_chunks_user ON document_chunks(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_chunks_index ON document_chunks(chunk_index)')
        
        # Reminder indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reminders_user ON reminders(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reminders_scheduled ON reminders(scheduled_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reminders_type ON reminders(reminder_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reminders_active ON reminders(is_active)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reminders_completed ON reminders(is_completed)')
        
        # Analytics indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_user ON analytics_interactions(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_timestamp ON analytics_interactions(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_type ON analytics_interactions(query_type)')
        
        # Notification indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at)')
    
    async def _create_triggers(self, cursor):
        """Create database triggers for data integrity and automation"""
        
        # Update user last_active on interaction
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS update_user_last_active
            AFTER INSERT ON interactions
            BEGIN
                UPDATE users SET last_active = NEW.timestamp WHERE id = NEW.user_id;
            END
        ''')
        
        # Update session updated_at on new message
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS update_session_on_message
            AFTER INSERT ON messages
            BEGIN
                UPDATE chat_sessions 
                SET updated_at = NEW.timestamp, message_count = message_count + 1
                WHERE id = NEW.session_id;
            END
        ''')
        
        # Auto-complete reminders when scheduled time passes
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS auto_complete_past_reminders
            AFTER UPDATE ON reminders
            WHEN NEW.scheduled_time < datetime('now') AND NEW.is_completed = 0
            BEGIN
                UPDATE reminders 
                SET is_completed = 1, completed_at = datetime('now')
                WHERE id = NEW.id;
            END
        ''')
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with optimizations"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        
        # Set connection optimizations
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        
        return conn
    
    async def create_user(self, user_id: str, username: Optional[str] = None, 
                         email: Optional[str] = None, preferences: Optional[Dict] = None) -> bool:
        """Create a new user with enhanced data"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO users (id, username, email, preferences)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, email, json.dumps(preferences or {})))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if success:
                print(f"👤 Created user: {user_id}")
            
            return success
            
        except Exception as e:
            print(f"❌ Error creating user: {e}")
            return False
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user statistics"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Basic user info
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user_row = cursor.fetchone()
            
            if not user_row:
                return {}
            
            # Interaction stats
            cursor.execute('SELECT COUNT(*) FROM interactions WHERE user_id = ?', (user_id,))
            total_interactions = cursor.fetchone()[0]
            
            # Session stats
            cursor.execute('SELECT COUNT(*) FROM chat_sessions WHERE user_id = ? AND archived = 0', (user_id,))
            active_sessions = cursor.fetchone()[0]
            
            # Document stats
            cursor.execute('SELECT COUNT(*) FROM documents WHERE user_id = ?', (user_id,))
            total_documents = cursor.fetchone()[0]
            
            # Reminder stats
            cursor.execute('SELECT COUNT(*) FROM reminders WHERE user_id = ? AND is_active = 1', (user_id,))
            active_reminders = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "user_id": user_id,
                "username": user_row["username"],
                "email": user_row["email"],
                "created_at": user_row["created_at"],
                "last_active": user_row["last_active"],
                "total_interactions": total_interactions,
                "active_sessions": active_sessions,
                "total_documents": total_documents,
                "active_reminders": active_reminders,
                "subscription_tier": user_row["subscription_tier"]
            }
            
        except Exception as e:
            print(f"❌ Error getting user stats: {e}")
            return {}
    
    async def cleanup_old_data(self, days_to_keep: int = None):
        """Enhanced cleanup with configurable retention"""
        try:
            days_to_keep = days_to_keep or int(os.getenv("DB_CLEANUP_OLD_DATA_DAYS", 90))
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Clean up old interactions
            cursor.execute('DELETE FROM interactions WHERE timestamp < ?', (cutoff_date,))
            interactions_deleted = cursor.rowcount
            
            # Clean up old analytics
            cursor.execute('DELETE FROM analytics_interactions WHERE timestamp < ?', (cutoff_date,))
            analytics_deleted = cursor.rowcount
            
            # Clean up completed reminders older than 30 days
            reminder_cutoff = (datetime.now() - timedelta(days=30)).isoformat()
            cursor.execute('DELETE FROM reminders WHERE is_completed = 1 AND completed_at < ?', (reminder_cutoff,))
            reminders_deleted = cursor.rowcount
            
            # Clean up read notifications older than 7 days
            notification_cutoff = (datetime.now() - timedelta(days=7)).isoformat()
            cursor.execute('DELETE FROM notifications WHERE is_read = 1 AND read_at < ?', (notification_cutoff,))
            notifications_deleted = cursor.rowcount
            
            # Vacuum database to reclaim space
            cursor.execute('VACUUM')
            
            conn.commit()
            conn.close()
            
            total_deleted = interactions_deleted + analytics_deleted + reminders_deleted + notifications_deleted
            
            if total_deleted > 0:
                print(f"🧹 Cleaned up {total_deleted} old records ({interactions_deleted} interactions, {analytics_deleted} analytics, {reminders_deleted} reminders, {notifications_deleted} notifications)")
            
            return total_deleted
            
        except Exception as e:
            print(f"❌ Error cleaning up old data: {e}")
            return 0
    
    async def backup_database(self, backup_path: str = None):
        """Create database backup with timestamp"""
        try:
            if not self.backup_enabled:
                return False
            
            if backup_path is None:
                backup_dir = Path("backups")
                backup_dir.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = backup_dir / f"studymate_backup_{timestamp}.db"
            
            import shutil
            shutil.copy2(self.db_path, backup_path)
            
            print(f"💾 Database backed up to: {backup_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error backing up database: {e}")
            return False
    
    async def get_database_info(self) -> Dict[str, Any]:
        """Get database information and statistics"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Database file info
            db_path = Path(self.db_path)
            db_size = db_path.stat().st_size if db_path.exists() else 0
            
            # Table counts
            tables = [
                "users", "interactions", "chat_sessions", "messages", 
                "documents", "reminders", "notifications", "user_achievements"
            ]
            
            table_counts = {}
            for table in tables:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                table_counts[table] = cursor.fetchone()[0]
            
            # Database settings
            cursor.execute('PRAGMA journal_mode')
            journal_mode = cursor.fetchone()[0]
            
            cursor.execute('PRAGMA synchronous')
            synchronous = cursor.fetchone()[0]
            
            cursor.execute('PRAGMA cache_size')
            cache_size = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "database_path": str(self.db_path),
                "database_size_bytes": db_size,
                "database_size_mb": round(db_size / (1024 * 1024), 2),
                "table_counts": table_counts,
                "total_records": sum(table_counts.values()),
                "settings": {
                    "journal_mode": journal_mode,
                    "synchronous": synchronous,
                    "cache_size": cache_size
                },
                "backup_enabled": self.backup_enabled,
                "last_checked": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error getting database info: {e}")
            return {"error": str(e)}
    
    async def optimize_database(self):
        """Optimize database performance"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Analyze tables for query optimization
            cursor.execute('ANALYZE')
            
            # Rebuild indexes
            cursor.execute('REINDEX')
            
            # Update table statistics
            cursor.execute('PRAGMA optimize')
            
            conn.commit()
            conn.close()
            
            print("⚡ Database optimized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error optimizing database: {e}")
            return False