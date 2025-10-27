"""
StudyMate Memory Manager - Advanced User Memory & Context Management
Handles personalized learning memory, preferences, and context awareness
"""

import os
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import sqlite3

class MemoryManager:
    """Advanced memory management for personalized learning"""
    
    def __init__(self, db_manager):
        print("🧠 Initializing Memory Manager...")
        
        self.db_manager = db_manager
        self.retention_days = int(os.getenv("DATA_RETENTION_DAYS", 365))
        self.privacy_mode = os.getenv("PRIVACY_MODE", "False").lower() == "true"
        
        # Memory categories
        self.memory_types = {
            "interaction": "User interactions and responses",
            "preference": "User preferences and settings", 
            "performance": "Learning performance data",
            "context": "Session and conversation context",
            "achievement": "Learning achievements and milestones"
        }
        
        # Context tracking
        self.active_contexts = {}  # user_id -> context_data
        
        print(f"✅ Memory Manager ready - Privacy mode: {self.privacy_mode}")
    
    async def store_interaction(
        self,
        user_id: str,
        session_id: str,
        query: str,
        response: str,
        mode: str = "chat",
        metadata: Optional[Dict] = None
    ):
        """Store user interaction with context awareness"""
        
        try:
            if self.privacy_mode:
                # In privacy mode, store minimal data
                query = self._anonymize_text(query)
                response = self._anonymize_text(response)
            
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Store interaction
            cursor.execute('''
                INSERT INTO interactions 
                (user_id, session_id, query, response, source, mode, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                session_id, 
                query,
                response,
                metadata.get("source", "unknown") if metadata else "unknown",
                mode,
                datetime.now().isoformat(),
                json.dumps(metadata) if metadata else None
            ))
            
            # Update user context
            await self._update_user_context(user_id, query, response, mode, cursor)
            
            # Track learning patterns
            await self._track_learning_patterns(user_id, query, mode, cursor)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Error storing interaction: {e}")
    
    async def get_user_context(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Get comprehensive user context for personalized responses"""
        
        try:
            # Check active context cache
            if user_id in self.active_contexts:
                return self.active_contexts[user_id]
            
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Get recent interactions
            cursor.execute('''
                SELECT query, response, mode, timestamp, metadata
                FROM interactions
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 20
            ''', (user_id,))
            
            recent_interactions = []
            for row in cursor.fetchall():
                query, response, mode, timestamp, metadata = row
                recent_interactions.append({
                    "query": query,
                    "response": response,
                    "mode": mode,
                    "timestamp": timestamp,
                    "metadata": json.loads(metadata) if metadata else {}
                })
            
            # Get user preferences
            cursor.execute('''
                SELECT preferences FROM user_preferences
                WHERE user_id = ?
            ''', (user_id,))
            
            prefs_row = cursor.fetchone()
            preferences = json.loads(prefs_row[0]) if prefs_row else {}
            
            # Get learning patterns
            learning_patterns = await self._get_learning_patterns(user_id, cursor)
            
            # Get performance metrics
            performance_metrics = await self._get_performance_metrics(user_id, cursor)
            
            conn.close()
            
            # Build context
            context = {
                "user_id": user_id,
                "session_id": session_id,
                "recent_interactions": recent_interactions,
                "preferences": preferences,
                "learning_patterns": learning_patterns,
                "performance_metrics": performance_metrics,
                "context_updated": datetime.now().isoformat()
            }
            
            # Cache context
            self.active_contexts[user_id] = context
            
            return context
            
        except Exception as e:
            print(f"❌ Error getting user context: {e}")
            return {"user_id": user_id, "session_id": session_id}
    
    async def update_user_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> bool:
        """Update user preferences and settings"""
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Upsert preferences
            cursor.execute('''
                INSERT OR REPLACE INTO user_preferences 
                (user_id, preferences, updated_at)
                VALUES (?, ?, ?)
            ''', (
                user_id,
                json.dumps(preferences),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            # Update active context
            if user_id in self.active_contexts:
                self.active_contexts[user_id]["preferences"] = preferences
            
            print(f"✅ Updated preferences for user: {user_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating preferences: {e}")
            return False
    
    async def get_personalized_suggestions(self, user_id: str) -> List[Dict[str, Any]]:
        """Generate personalized learning suggestions based on memory"""
        
        try:
            context = await self.get_user_context(user_id, "suggestions")
            suggestions = []
            
            # Analyze recent interactions
            recent_interactions = context.get("recent_interactions", [])
            learning_patterns = context.get("learning_patterns", {})
            
            # Subject-based suggestions
            frequent_subjects = learning_patterns.get("frequent_subjects", [])
            for subject in frequent_subjects[:3]:
                suggestions.append({
                    "type": "subject_deep_dive",
                    "title": f"Explore Advanced {subject.title()} Topics",
                    "description": f"You've been studying {subject} frequently. Ready for advanced concepts?",
                    "priority": "high",
                    "action": f"generate_notes_{subject}_advanced"
                })
            
            # Time-based suggestions
            last_study_time = learning_patterns.get("last_activity_time")
            if last_study_time:
                hours_since = (datetime.now() - datetime.fromisoformat(last_study_time)).total_seconds() / 3600
                
                if hours_since > 24:
                    suggestions.append({
                        "type": "study_reminder",
                        "title": "Welcome Back! Let's Continue Learning",
                        "description": "It's been a while since your last study session. Ready to dive back in?",
                        "priority": "medium",
                        "action": "resume_last_topic"
                    })
            
            # Performance-based suggestions
            weak_areas = learning_patterns.get("weak_areas", [])
            for area in weak_areas[:2]:
                suggestions.append({
                    "type": "improvement",
                    "title": f"Strengthen Your {area.title()} Skills",
                    "description": f"Let's work on improving your understanding of {area}",
                    "priority": "high",
                    "action": f"practice_{area}"
                })
            
            # Learning streak suggestions
            streak = learning_patterns.get("learning_streak", 0)
            if streak >= 7:
                suggestions.append({
                    "type": "achievement",
                    "title": f"Amazing! {streak}-Day Learning Streak! 🔥",
                    "description": "You're on fire! Keep up the excellent work.",
                    "priority": "celebration",
                    "action": "view_achievements"
                })
            
            return suggestions[:5]  # Limit to 5 suggestions
            
        except Exception as e:
            print(f"❌ Error generating suggestions: {e}")
            return []
    
    async def track_achievement(
        self,
        user_id: str,
        achievement_type: str,
        achievement_data: Dict[str, Any]
    ):
        """Track user achievements and milestones"""
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Store achievement
            cursor.execute('''
                INSERT INTO user_achievements 
                (user_id, achievement_type, achievement_data, earned_at)
                VALUES (?, ?, ?, ?)
            ''', (
                user_id,
                achievement_type,
                json.dumps(achievement_data),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            print(f"🏆 Achievement unlocked for {user_id}: {achievement_type}")
            
        except Exception as e:
            print(f"❌ Error tracking achievement: {e}")
    
    async def get_user_achievements(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's achievements and milestones"""
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT achievement_type, achievement_data, earned_at
                FROM user_achievements
                WHERE user_id = ?
                ORDER BY earned_at DESC
            ''', (user_id,))
            
            achievements = []
            for row in cursor.fetchall():
                achievement_type, achievement_data, earned_at = row
                achievements.append({
                    "type": achievement_type,
                    "data": json.loads(achievement_data),
                    "earned_at": earned_at
                })
            
            conn.close()
            return achievements
            
        except Exception as e:
            print(f"❌ Error getting achievements: {e}")
            return []
    
    async def _update_user_context(
        self,
        user_id: str,
        query: str,
        response: str,
        mode: str,
        cursor
    ):
        """Update user context based on interaction"""
        
        try:
            # Extract topics from query
            topics = self._extract_topics(query)
            
            # Update context tracking
            cursor.execute('''
                INSERT OR REPLACE INTO user_context
                (user_id, last_topics, last_mode, last_activity, interaction_count)
                VALUES (?, ?, ?, ?, 
                    COALESCE((SELECT interaction_count FROM user_context WHERE user_id = ?), 0) + 1)
            ''', (
                user_id,
                json.dumps(topics),
                mode,
                datetime.now().isoformat(),
                user_id
            ))
            
        except Exception as e:
            print(f"❌ Error updating user context: {e}")
    
    async def _track_learning_patterns(
        self,
        user_id: str,
        query: str,
        mode: str,
        cursor
    ):
        """Track and analyze learning patterns"""
        
        try:
            # Get or create learning pattern record
            cursor.execute('''
                SELECT pattern_data FROM learning_patterns
                WHERE user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            if row:
                patterns = json.loads(row[0])
            else:
                patterns = {
                    "total_queries": 0,
                    "modes_used": {},
                    "topics_studied": {},
                    "daily_activity": {},
                    "learning_streak": 0,
                    "last_activity_date": None
                }
            
            # Update patterns
            patterns["total_queries"] += 1
            patterns["modes_used"][mode] = patterns["modes_used"].get(mode, 0) + 1
            
            # Extract and track topics
            topics = self._extract_topics(query)
            for topic in topics:
                patterns["topics_studied"][topic] = patterns["topics_studied"].get(topic, 0) + 1
            
            # Track daily activity
            today = datetime.now().date().isoformat()
            patterns["daily_activity"][today] = patterns["daily_activity"].get(today, 0) + 1
            
            # Update learning streak
            if patterns["last_activity_date"] != today:
                yesterday = (datetime.now().date() - timedelta(days=1)).isoformat()
                if patterns["last_activity_date"] == yesterday:
                    patterns["learning_streak"] += 1
                else:
                    patterns["learning_streak"] = 1
                patterns["last_activity_date"] = today
            
            # Store updated patterns
            cursor.execute('''
                INSERT OR REPLACE INTO learning_patterns
                (user_id, pattern_data, updated_at)
                VALUES (?, ?, ?)
            ''', (
                user_id,
                json.dumps(patterns),
                datetime.now().isoformat()
            ))
            
        except Exception as e:
            print(f"❌ Error tracking learning patterns: {e}")
    
    async def _get_learning_patterns(self, user_id: str, cursor) -> Dict[str, Any]:
        """Get user's learning patterns"""
        
        try:
            cursor.execute('''
                SELECT pattern_data FROM learning_patterns
                WHERE user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            if row:
                patterns = json.loads(row[0])
                
                # Add derived insights
                patterns["frequent_subjects"] = self._get_top_items(patterns.get("topics_studied", {}), 5)
                patterns["preferred_modes"] = self._get_top_items(patterns.get("modes_used", {}), 3)
                patterns["weak_areas"] = self._identify_weak_areas(patterns.get("topics_studied", {}))
                
                return patterns
            
            return {}
            
        except Exception as e:
            print(f"❌ Error getting learning patterns: {e}")
            return {}
    
    async def _get_performance_metrics(self, user_id: str, cursor) -> Dict[str, Any]:
        """Get user's performance metrics"""
        
        try:
            # Calculate various performance metrics
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            
            # Queries per week
            cursor.execute('''
                SELECT COUNT(*) FROM interactions
                WHERE user_id = ? AND timestamp > ?
            ''', (user_id, week_ago))
            
            weekly_queries = cursor.fetchone()[0]
            
            # Average response satisfaction (placeholder - would need user feedback)
            satisfaction_score = 85  # Default good score
            
            # Learning velocity (topics covered per week)
            cursor.execute('''
                SELECT COUNT(DISTINCT query) FROM interactions
                WHERE user_id = ? AND timestamp > ?
            ''', (user_id, week_ago))
            
            unique_queries = cursor.fetchone()[0]
            
            return {
                "weekly_queries": weekly_queries,
                "satisfaction_score": satisfaction_score,
                "learning_velocity": unique_queries,
                "engagement_level": "high" if weekly_queries > 20 else "medium" if weekly_queries > 5 else "low"
            }
            
        except Exception as e:
            print(f"❌ Error getting performance metrics: {e}")
            return {}
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics/subjects from text using keyword matching"""
        
        text_lower = text.lower()
        topics = []
        
        # Subject keywords
        subject_keywords = {
            "mathematics": ["math", "algebra", "calculus", "geometry", "statistics"],
            "physics": ["physics", "force", "energy", "motion", "quantum"],
            "chemistry": ["chemistry", "molecule", "atom", "reaction", "element"],
            "biology": ["biology", "cell", "dna", "organism", "evolution"],
            "computer_science": ["programming", "algorithm", "code", "software"],
            "history": ["history", "war", "ancient", "civilization"],
            "literature": ["literature", "poem", "novel", "author", "book"],
            "language": ["grammar", "vocabulary", "pronunciation", "translation"]
        }
        
        for subject, keywords in subject_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(subject)
        
        return topics
    
    def _get_top_items(self, items_dict: Dict[str, int], limit: int) -> List[str]:
        """Get top items from a frequency dictionary"""
        
        sorted_items = sorted(items_dict.items(), key=lambda x: x[1], reverse=True)
        return [item[0] for item in sorted_items[:limit]]
    
    def _identify_weak_areas(self, topics_dict: Dict[str, int]) -> List[str]:
        """Identify weak areas based on low interaction frequency"""
        
        if not topics_dict:
            return []
        
        avg_frequency = sum(topics_dict.values()) / len(topics_dict)
        weak_areas = [topic for topic, freq in topics_dict.items() if freq < avg_frequency * 0.5]
        
        return weak_areas[:3]  # Return top 3 weak areas
    
    def _anonymize_text(self, text: str) -> str:
        """Anonymize text for privacy mode"""
        
        if not self.privacy_mode:
            return text
        
        # Simple anonymization - replace potential PII
        import re
        
        # Replace email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
        
        # Replace phone numbers
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
        
        # Replace names (simple pattern)
        text = re.sub(r'\bmy name is \w+\b', 'my name is [NAME]', text, flags=re.IGNORECASE)
        
        return text
    
    async def cleanup_old_memory(self) -> int:
        """Clean up old memory data based on retention policy"""
        
        try:
            cutoff_date = (datetime.now() - timedelta(days=self.retention_days)).isoformat()
            
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Clean up old interactions
            cursor.execute('''
                DELETE FROM interactions
                WHERE timestamp < ?
            ''', (cutoff_date,))
            
            deleted_count = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            if deleted_count > 0:
                print(f"🧹 Cleaned up {deleted_count} old memory records")
            
            return deleted_count
            
        except Exception as e:
            print(f"❌ Error cleaning up memory: {e}")
            return 0
    
    async def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export all user data for GDPR compliance"""
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Get all user data
            user_data = {
                "user_id": user_id,
                "export_date": datetime.now().isoformat(),
                "interactions": [],
                "preferences": {},
                "learning_patterns": {},
                "achievements": []
            }
            
            # Export interactions
            cursor.execute('''
                SELECT query, response, mode, timestamp, metadata
                FROM interactions
                WHERE user_id = ?
                ORDER BY timestamp
            ''', (user_id,))
            
            for row in cursor.fetchall():
                query, response, mode, timestamp, metadata = row
                user_data["interactions"].append({
                    "query": query,
                    "response": response,
                    "mode": mode,
                    "timestamp": timestamp,
                    "metadata": json.loads(metadata) if metadata else {}
                })
            
            # Export preferences
            cursor.execute('''
                SELECT preferences FROM user_preferences
                WHERE user_id = ?
            ''', (user_id,))
            
            prefs_row = cursor.fetchone()
            if prefs_row:
                user_data["preferences"] = json.loads(prefs_row[0])
            
            # Export learning patterns
            cursor.execute('''
                SELECT pattern_data FROM learning_patterns
                WHERE user_id = ?
            ''', (user_id,))
            
            patterns_row = cursor.fetchone()
            if patterns_row:
                user_data["learning_patterns"] = json.loads(patterns_row[0])
            
            # Export achievements
            cursor.execute('''
                SELECT achievement_type, achievement_data, earned_at
                FROM user_achievements
                WHERE user_id = ?
            ''', (user_id,))
            
            for row in cursor.fetchall():
                achievement_type, achievement_data, earned_at = row
                user_data["achievements"].append({
                    "type": achievement_type,
                    "data": json.loads(achievement_data),
                    "earned_at": earned_at
                })
            
            conn.close()
            return user_data
            
        except Exception as e:
            print(f"❌ Error exporting user data: {e}")
            return {"error": str(e)}
    
    async def delete_user_data(self, user_id: str) -> bool:
        """Delete all user data for GDPR compliance"""
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Delete from all tables
            tables = [
                "interactions", "user_preferences", "learning_patterns",
                "user_achievements", "user_context", "chat_sessions",
                "messages", "reminders"
            ]
            
            for table in tables:
                cursor.execute(f'DELETE FROM {table} WHERE user_id = ?', (user_id,))
            
            conn.commit()
            conn.close()
            
            # Clear from active contexts
            if user_id in self.active_contexts:
                del self.active_contexts[user_id]
            
            print(f"🗑️ Deleted all data for user: {user_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting user data: {e}")
            return False