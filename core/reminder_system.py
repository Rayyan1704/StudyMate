"""
StudyMate Reminder System - Smart Study Reminders & Notifications
Handles study reminders, deadlines, and learning pattern notifications
"""

import os
import uuid
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import json

class ReminderType(Enum):
    STUDY = "study"
    REVISION = "revision"
    DEADLINE = "deadline"
    BREAK = "break"
    QUIZ = "quiz"

class ReminderSystem:
    """Advanced reminder system with smart notifications"""
    
    def __init__(self, db_manager):
        print("🔔 Initializing Reminder System...")
        
        self.db_manager = db_manager
        self.max_reminders_per_user = int(os.getenv("MAX_REMINDERS_PER_USER", 50))
        self.check_interval_minutes = int(os.getenv("REMINDER_CHECK_INTERVAL_MINUTES", 5))
        self.default_snooze_minutes = int(os.getenv("DEFAULT_SNOOZE_MINUTES", 15))
        
        # Active reminders cache
        self.active_reminders = {}  # reminder_id -> reminder_data
        
        # Smart reminder patterns
        self.smart_patterns = {
            "daily": {"interval_hours": 24, "description": "Every day"},
            "weekly": {"interval_hours": 168, "description": "Every week"},
            "weekdays": {"interval_hours": 24, "description": "Monday to Friday", "skip_weekends": True},
            "custom": {"interval_hours": 0, "description": "Custom pattern"}
        }
        
        print(f"✅ Reminder System ready - Max reminders: {self.max_reminders_per_user}")
    
    async def create_reminder(
        self,
        user_id: str,
        title: str,
        description: Optional[str] = None,
        scheduled_time: datetime = None,
        reminder_type: str = "study",
        repeat_pattern: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create a new reminder"""
        
        try:
            # Check reminder limit
            user_reminder_count = await self._get_user_reminder_count(user_id)
            if user_reminder_count >= self.max_reminders_per_user:
                raise Exception(f"Maximum {self.max_reminders_per_user} reminders per user")
            
            # Generate unique reminder ID
            reminder_id = str(uuid.uuid4())
            
            # Validate scheduled time
            if scheduled_time and scheduled_time <= datetime.now():
                raise Exception("Scheduled time must be in the future")
            
            # Create reminder data
            reminder_data = {
                "id": reminder_id,
                "user_id": user_id,
                "title": title,
                "description": description or "",
                "scheduled_time": scheduled_time or datetime.now() + timedelta(hours=1),
                "reminder_type": reminder_type,
                "repeat_pattern": repeat_pattern,
                "is_active": True,
                "is_completed": False,
                "snooze_count": 0,
                "created_at": datetime.now(),
                "metadata": metadata or {}
            }
            
            # Save to database
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO reminders 
                (id, user_id, title, description, scheduled_time, reminder_type, 
                 repeat_pattern, is_active, is_completed, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                reminder_id,
                user_id,
                title,
                description or "",
                reminder_data["scheduled_time"].isoformat(),
                reminder_type,
                repeat_pattern,
                True,
                False,
                reminder_data["created_at"].isoformat(),
                json.dumps(metadata or {})
            ))
            
            conn.commit()
            conn.close()
            
            # Add to active cache
            self.active_reminders[reminder_id] = reminder_data
            
            print(f"✅ Created reminder: {title} for user: {user_id}")
            
            return {
                "id": reminder_id,
                "title": title,
                "scheduled_time": reminder_data["scheduled_time"].isoformat(),
                "reminder_type": reminder_type,
                "repeat_pattern": repeat_pattern
            }
            
        except Exception as e:
            print(f"❌ Error creating reminder: {e}")
            raise
    
    async def get_user_reminders(
        self,
        user_id: str,
        include_completed: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all reminders for a user"""
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            query = '''
                SELECT id, title, description, scheduled_time, reminder_type, 
                       repeat_pattern, is_active, is_completed, created_at, metadata
                FROM reminders
                WHERE user_id = ?
            '''
            params = [user_id]
            
            if not include_completed:
                query += ' AND is_completed = 0'
            
            query += ' ORDER BY scheduled_time ASC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            reminders = []
            for row in rows:
                (reminder_id, title, description, scheduled_time, reminder_type,
                 repeat_pattern, is_active, is_completed, created_at, metadata) = row
                
                reminders.append({
                    "id": reminder_id,
                    "title": title,
                    "description": description,
                    "scheduled_time": scheduled_time,
                    "reminder_type": reminder_type,
                    "repeat_pattern": repeat_pattern,
                    "is_active": bool(is_active),
                    "is_completed": bool(is_completed),
                    "created_at": created_at,
                    "metadata": json.loads(metadata) if metadata else {},
                    "time_until": self._calculate_time_until(scheduled_time)
                })
            
            return reminders
            
        except Exception as e:
            print(f"❌ Error getting user reminders: {e}")
            return []
    
    async def update_reminder(
        self,
        reminder_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        scheduled_time: Optional[datetime] = None,
        is_active: Optional[bool] = None,
        is_completed: Optional[bool] = None
    ) -> bool:
        """Update reminder details"""
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Build update query
            updates = []
            params = []
            
            if title is not None:
                updates.append("title = ?")
                params.append(title)
            
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            
            if scheduled_time is not None:
                updates.append("scheduled_time = ?")
                params.append(scheduled_time.isoformat())
            
            if is_active is not None:
                updates.append("is_active = ?")
                params.append(is_active)
            
            if is_completed is not None:
                updates.append("is_completed = ?")
                params.append(is_completed)
            
            params.append(reminder_id)
            
            query = f"UPDATE reminders SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            # Update cache
            if reminder_id in self.active_reminders:
                if title is not None:
                    self.active_reminders[reminder_id]["title"] = title
                if description is not None:
                    self.active_reminders[reminder_id]["description"] = description
                if scheduled_time is not None:
                    self.active_reminders[reminder_id]["scheduled_time"] = scheduled_time
                if is_active is not None:
                    self.active_reminders[reminder_id]["is_active"] = is_active
                if is_completed is not None:
                    self.active_reminders[reminder_id]["is_completed"] = is_completed
            
            return success
            
        except Exception as e:
            print(f"❌ Error updating reminder: {e}")
            return False
    
    async def snooze_reminder(self, reminder_id: str, snooze_minutes: Optional[int] = None) -> bool:
        """Snooze a reminder for specified minutes"""
        
        try:
            snooze_minutes = snooze_minutes or self.default_snooze_minutes
            
            # Get current reminder
            reminder = await self.get_reminder(reminder_id)
            if not reminder:
                return False
            
            # Calculate new scheduled time
            current_time = datetime.fromisoformat(reminder["scheduled_time"])
            new_time = current_time + timedelta(minutes=snooze_minutes)
            
            # Update reminder
            success = await self.update_reminder(reminder_id, scheduled_time=new_time)
            
            if success:
                # Increment snooze count
                conn = self.db_manager.get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE reminders 
                    SET snooze_count = snooze_count + 1
                    WHERE id = ?
                ''', (reminder_id,))
                
                conn.commit()
                conn.close()
                
                print(f"😴 Snoozed reminder {reminder_id} for {snooze_minutes} minutes")
            
            return success
            
        except Exception as e:
            print(f"❌ Error snoozing reminder: {e}")
            return False
    
    async def delete_reminder(self, reminder_id: str) -> bool:
        """Delete a reminder"""
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM reminders WHERE id = ?', (reminder_id,))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            # Remove from cache
            if reminder_id in self.active_reminders:
                del self.active_reminders[reminder_id]
            
            return success
            
        except Exception as e:
            print(f"❌ Error deleting reminder: {e}")
            return False
    
    async def get_reminder(self, reminder_id: str) -> Optional[Dict[str, Any]]:
        """Get specific reminder details"""
        
        try:
            # Check cache first
            if reminder_id in self.active_reminders:
                return self.active_reminders[reminder_id]
            
            # Query database
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, user_id, title, description, scheduled_time, reminder_type,
                       repeat_pattern, is_active, is_completed, created_at, metadata
                FROM reminders
                WHERE id = ?
            ''', (reminder_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            (reminder_id, user_id, title, description, scheduled_time, reminder_type,
             repeat_pattern, is_active, is_completed, created_at, metadata) = row
            
            reminder_data = {
                "id": reminder_id,
                "user_id": user_id,
                "title": title,
                "description": description,
                "scheduled_time": scheduled_time,
                "reminder_type": reminder_type,
                "repeat_pattern": repeat_pattern,
                "is_active": bool(is_active),
                "is_completed": bool(is_completed),
                "created_at": created_at,
                "metadata": json.loads(metadata) if metadata else {}
            }
            
            return reminder_data
            
        except Exception as e:
            print(f"❌ Error getting reminder: {e}")
            return None
    
    async def check_due_reminders(self) -> List[Dict[str, Any]]:
        """Check for reminders that are due"""
        
        try:
            current_time = datetime.now()
            
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Find due reminders
            cursor.execute('''
                SELECT id, user_id, title, description, scheduled_time, reminder_type, repeat_pattern
                FROM reminders
                WHERE is_active = 1 AND is_completed = 0 AND scheduled_time <= ?
                ORDER BY scheduled_time ASC
            ''', (current_time.isoformat(),))
            
            due_reminders = []
            for row in cursor.fetchall():
                (reminder_id, user_id, title, description, scheduled_time, 
                 reminder_type, repeat_pattern) = row
                
                due_reminders.append({
                    "id": reminder_id,
                    "user_id": user_id,
                    "title": title,
                    "description": description,
                    "scheduled_time": scheduled_time,
                    "reminder_type": reminder_type,
                    "repeat_pattern": repeat_pattern
                })
            
            conn.close()
            
            # Process repeating reminders
            for reminder in due_reminders:
                if reminder["repeat_pattern"]:
                    await self._schedule_next_occurrence(reminder)
            
            return due_reminders
            
        except Exception as e:
            print(f"❌ Error checking due reminders: {e}")
            return []
    
    async def create_smart_reminders(self, user_id: str) -> List[Dict[str, Any]]:
        """Create smart reminders based on user's learning patterns"""
        
        try:
            # Analyze user's learning patterns
            patterns = await self._analyze_learning_patterns(user_id)
            
            smart_reminders = []
            
            # Create reminders based on patterns
            if patterns.get("inactive_days", 0) >= 3:
                # User hasn't studied for 3+ days
                reminder = await self.create_reminder(
                    user_id=user_id,
                    title="Time to get back to studying! 📚",
                    description="You haven't studied in a few days. Let's get back on track!",
                    scheduled_time=datetime.now() + timedelta(hours=2),
                    reminder_type="study",
                    metadata={"smart_reminder": True, "reason": "inactive_period"}
                )
                smart_reminders.append(reminder)
            
            # Subject-specific reminders
            weak_subjects = patterns.get("weak_subjects", [])
            for subject in weak_subjects[:2]:  # Limit to 2 subjects
                reminder = await self.create_reminder(
                    user_id=user_id,
                    title=f"Review {subject.title()} concepts 🎯",
                    description=f"You might want to spend more time on {subject}",
                    scheduled_time=datetime.now() + timedelta(days=1),
                    reminder_type="revision",
                    metadata={"smart_reminder": True, "subject": subject}
                )
                smart_reminders.append(reminder)
            
            # Break reminders for intensive users
            if patterns.get("daily_queries", 0) > 50:
                reminder = await self.create_reminder(
                    user_id=user_id,
                    title="Take a study break! 🧘‍♀️",
                    description="You've been studying intensively. Time for a short break!",
                    scheduled_time=datetime.now() + timedelta(hours=4),
                    reminder_type="break",
                    metadata={"smart_reminder": True, "reason": "intensive_study"}
                )
                smart_reminders.append(reminder)
            
            return smart_reminders
            
        except Exception as e:
            print(f"❌ Error creating smart reminders: {e}")
            return []
    
    async def _analyze_learning_patterns(self, user_id: str) -> Dict[str, Any]:
        """Analyze user's learning patterns for smart reminders"""
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Get recent activity
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            
            cursor.execute('''
                SELECT COUNT(*) as queries, MAX(timestamp) as last_activity
                FROM interactions
                WHERE user_id = ? AND timestamp > ?
            ''', (user_id, week_ago))
            
            row = cursor.fetchone()
            recent_queries = row[0] if row else 0
            last_activity = row[1] if row else None
            
            # Calculate inactive days
            inactive_days = 0
            if last_activity:
                last_dt = datetime.fromisoformat(last_activity)
                inactive_days = (datetime.now() - last_dt).days
            
            # Analyze subjects (simplified)
            cursor.execute('''
                SELECT query FROM interactions
                WHERE user_id = ? AND timestamp > ?
                LIMIT 100
            ''', (user_id, week_ago))
            
            queries = [row[0].lower() for row in cursor.fetchall()]
            
            # Simple subject detection
            subject_counts = {}
            for query in queries:
                if "math" in query:
                    subject_counts["mathematics"] = subject_counts.get("mathematics", 0) + 1
                elif "science" in query:
                    subject_counts["science"] = subject_counts.get("science", 0) + 1
                # Add more subject detection logic
            
            # Identify weak subjects (subjects with few queries)
            avg_queries = sum(subject_counts.values()) / max(1, len(subject_counts))
            weak_subjects = [subject for subject, count in subject_counts.items() 
                           if count < avg_queries * 0.5]
            
            conn.close()
            
            return {
                "daily_queries": recent_queries / 7,
                "inactive_days": inactive_days,
                "weak_subjects": weak_subjects,
                "total_subjects": len(subject_counts)
            }
            
        except Exception as e:
            print(f"❌ Error analyzing learning patterns: {e}")
            return {}
    
    async def _schedule_next_occurrence(self, reminder: Dict[str, Any]):
        """Schedule next occurrence for repeating reminders"""
        
        try:
            pattern = reminder["repeat_pattern"]
            current_time = datetime.fromisoformat(reminder["scheduled_time"])
            
            if pattern == "daily":
                next_time = current_time + timedelta(days=1)
            elif pattern == "weekly":
                next_time = current_time + timedelta(weeks=1)
            elif pattern == "weekdays":
                next_time = current_time + timedelta(days=1)
                # Skip weekends
                while next_time.weekday() >= 5:  # Saturday = 5, Sunday = 6
                    next_time += timedelta(days=1)
            else:
                return  # No automatic scheduling for custom patterns
            
            # Update the reminder with new time
            await self.update_reminder(
                reminder["id"],
                scheduled_time=next_time,
                is_completed=False
            )
            
            print(f"📅 Scheduled next occurrence for reminder: {reminder['title']}")
            
        except Exception as e:
            print(f"❌ Error scheduling next occurrence: {e}")
    
    def _calculate_time_until(self, scheduled_time_str: str) -> str:
        """Calculate human-readable time until reminder"""
        
        try:
            scheduled_time = datetime.fromisoformat(scheduled_time_str)
            now = datetime.now()
            
            if scheduled_time <= now:
                return "Due now"
            
            diff = scheduled_time - now
            
            if diff.days > 0:
                return f"In {diff.days} day{'s' if diff.days != 1 else ''}"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"In {hours} hour{'s' if hours != 1 else ''}"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"In {minutes} minute{'s' if minutes != 1 else ''}"
            else:
                return "In less than a minute"
                
        except Exception:
            return "Unknown"
    
    async def _get_user_reminder_count(self, user_id: str) -> int:
        """Get total number of active reminders for user"""
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) FROM reminders 
                WHERE user_id = ? AND is_active = 1 AND is_completed = 0
            ''', (user_id,))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
            
        except Exception as e:
            print(f"❌ Error getting reminder count: {e}")
            return 0
    
    async def get_reminder_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get reminder statistics for user"""
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Total reminders
            cursor.execute('''
                SELECT COUNT(*) FROM reminders WHERE user_id = ?
            ''', (user_id,))
            total_reminders = cursor.fetchone()[0]
            
            # Active reminders
            cursor.execute('''
                SELECT COUNT(*) FROM reminders 
                WHERE user_id = ? AND is_active = 1 AND is_completed = 0
            ''', (user_id,))
            active_reminders = cursor.fetchone()[0]
            
            # Completed reminders
            cursor.execute('''
                SELECT COUNT(*) FROM reminders 
                WHERE user_id = ? AND is_completed = 1
            ''', (user_id,))
            completed_reminders = cursor.fetchone()[0]
            
            # Reminders by type
            cursor.execute('''
                SELECT reminder_type, COUNT(*) FROM reminders
                WHERE user_id = ? AND is_active = 1
                GROUP BY reminder_type
            ''', (user_id,))
            
            reminders_by_type = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                "total_reminders": total_reminders,
                "active_reminders": active_reminders,
                "completed_reminders": completed_reminders,
                "reminders_by_type": reminders_by_type,
                "completion_rate": round((completed_reminders / max(1, total_reminders)) * 100, 1)
            }
            
        except Exception as e:
            print(f"❌ Error getting reminder statistics: {e}")
            return {}