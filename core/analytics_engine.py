"""
StudyMate Analytics Engine - Comprehensive Learning Analytics
Tracks user behavior, learning patterns, and generates insights
"""

import os
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
from collections import defaultdict, Counter
import statistics

class AnalyticsEngine:
    """Advanced analytics engine for learning insights"""
    
    def __init__(self, db_manager):
        print("📊 Initializing Analytics Engine...")
        
        self.db_manager = db_manager
        self.retention_days = int(os.getenv("ANALYTICS_RETENTION_DAYS", 365))
        self.enabled = os.getenv("ANALYTICS_ENABLED", "True").lower() == "true"
        
        # Analytics categories
        self.subject_keywords = {
            "mathematics": ["math", "algebra", "calculus", "geometry", "trigonometry", "statistics", "probability"],
            "physics": ["physics", "force", "energy", "motion", "wave", "quantum", "mechanics", "thermodynamics"],
            "chemistry": ["chemistry", "molecule", "atom", "reaction", "element", "compound", "organic", "inorganic"],
            "biology": ["biology", "cell", "dna", "organism", "evolution", "genetics", "anatomy", "ecology"],
            "computer_science": ["programming", "algorithm", "code", "software", "computer", "data", "structure"],
            "history": ["history", "war", "ancient", "civilization", "empire", "revolution", "culture"],
            "literature": ["literature", "poem", "novel", "author", "story", "writing", "essay", "book"],
            "language": ["language", "grammar", "vocabulary", "pronunciation", "translation", "linguistics"],
            "science": ["science", "experiment", "hypothesis", "theory", "research", "method", "analysis"],
            "engineering": ["engineering", "design", "construction", "mechanical", "electrical", "civil"]
        }
        
        print(f"✅ Analytics Engine ready - Enabled: {self.enabled}")
    
    async def track_interaction(
        self, 
        user_id: str, 
        session_id: str,
        query_type: str,
        response_time: float,
        metadata: Optional[Dict] = None
    ):
        """Track user interaction for analytics"""
        
        if not self.enabled:
            return
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Insert interaction record
            cursor.execute('''
                INSERT INTO analytics_interactions 
                (user_id, session_id, query_type, response_time, metadata, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id, 
                session_id, 
                query_type, 
                response_time,
                json.dumps(metadata) if metadata else None,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Error tracking interaction: {e}")
    
    async def generate_analytics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive analytics for user"""
        
        try:
            if not self.enabled:
                return {"error": "Analytics disabled"}
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Gather all analytics data
            basic_stats = await self._get_basic_stats(user_id, start_date, end_date)
            subject_analysis = await self._analyze_subjects(user_id, start_date, end_date)
            performance_trends = await self._get_performance_trends(user_id, start_date, end_date)
            learning_patterns = await self._analyze_learning_patterns(user_id, start_date, end_date)
            session_analytics = await self._get_session_analytics(user_id, start_date, end_date)
            
            return {
                "user_id": user_id,
                "period_days": days,
                "generated_at": datetime.now().isoformat(),
                "basic_stats": basic_stats,
                "subject_analysis": subject_analysis,
                "performance_trends": performance_trends,
                "learning_patterns": learning_patterns,
                "session_analytics": session_analytics,
                "recommendations": await self._generate_recommendations(user_id, basic_stats, subject_analysis)
            }
            
        except Exception as e:
            print(f"❌ Error generating analytics: {e}")
            return {"error": str(e)}
    
    async def _get_basic_stats(self, user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get basic usage statistics"""
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Total queries
            cursor.execute('''
                SELECT COUNT(*) FROM interactions 
                WHERE user_id = ? AND timestamp BETWEEN ? AND ?
            ''', (user_id, start_date.isoformat(), end_date.isoformat()))
            total_queries = cursor.fetchone()[0]
            
            # Total sessions
            cursor.execute('''
                SELECT COUNT(DISTINCT session_id) FROM interactions 
                WHERE user_id = ? AND timestamp BETWEEN ? AND ?
            ''', (user_id, start_date.isoformat(), end_date.isoformat()))
            total_sessions = cursor.fetchone()[0]
            
            # Average response time
            cursor.execute('''
                SELECT AVG(response_time) FROM analytics_interactions 
                WHERE user_id = ? AND timestamp BETWEEN ? AND ?
            ''', (user_id, start_date.isoformat(), end_date.isoformat()))
            avg_response_time = cursor.fetchone()[0] or 0
            
            # Study time estimation (2 minutes per query average)
            study_time_minutes = total_queries * 2
            
            # Learning streak
            learning_streak = await self._calculate_learning_streak(user_id, cursor)
            
            # Daily activity
            cursor.execute('''
                SELECT DATE(timestamp) as date, COUNT(*) as queries
                FROM interactions
                WHERE user_id = ? AND timestamp BETWEEN ? AND ?
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            ''', (user_id, start_date.isoformat(), end_date.isoformat()))
            
            daily_activity = [
                {"date": row[0], "queries": row[1]} 
                for row in cursor.fetchall()
            ]
            
            conn.close()
            
            return {
                "total_queries": total_queries,
                "total_sessions": total_sessions,
                "study_time_minutes": study_time_minutes,
                "avg_response_time": round(avg_response_time, 2),
                "learning_streak_days": learning_streak,
                "daily_activity": daily_activity,
                "queries_per_day": round(total_queries / max(1, (end_date - start_date).days), 1)
            }
            
        except Exception as e:
            print(f"❌ Error getting basic stats: {e}")
            return {}
    
    async def _analyze_subjects(self, user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze subject distribution and performance"""
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Get all queries in period
            cursor.execute('''
                SELECT query, response, timestamp FROM interactions
                WHERE user_id = ? AND timestamp BETWEEN ? AND ?
                ORDER BY timestamp DESC
                LIMIT 1000
            ''', (user_id, start_date.isoformat(), end_date.isoformat()))
            
            interactions = cursor.fetchall()
            conn.close()
            
            # Analyze subjects
            subject_counts = defaultdict(int)
            subject_queries = defaultdict(list)
            
            for query, response, timestamp in interactions:
                query_lower = query.lower()
                detected_subjects = []
                
                for subject, keywords in self.subject_keywords.items():
                    if any(keyword in query_lower for keyword in keywords):
                        subject_counts[subject] += 1
                        subject_queries[subject].append({
                            "query": query,
                            "timestamp": timestamp
                        })
                        detected_subjects.append(subject)
                
                # If no subject detected, categorize as "general"
                if not detected_subjects:
                    subject_counts["general"] += 1
            
            # Calculate subject percentages
            total_queries = sum(subject_counts.values())
            subject_percentages = {}
            
            if total_queries > 0:
                for subject, count in subject_counts.items():
                    subject_percentages[subject] = round((count / total_queries) * 100, 1)
            
            # Get top subjects
            top_subjects = sorted(
                subject_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
            
            return {
                "subjects_studied": list(subject_counts.keys()),
                "subject_distribution": dict(subject_counts),
                "subject_percentages": subject_percentages,
                "top_subjects": [{"subject": s, "count": c} for s, c in top_subjects],
                "total_subjects": len(subject_counts),
                "most_active_subject": top_subjects[0][0] if top_subjects else None
            }
            
        except Exception as e:
            print(f"❌ Error analyzing subjects: {e}")
            return {}
    
    async def _get_performance_trends(self, user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze performance trends over time"""
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Get daily query counts
            cursor.execute('''
                SELECT DATE(timestamp) as date, 
                       COUNT(*) as queries,
                       AVG(LENGTH(query)) as avg_query_length,
                       AVG(LENGTH(response)) as avg_response_length
                FROM interactions
                WHERE user_id = ? AND timestamp BETWEEN ? AND ?
                GROUP BY DATE(timestamp)
                ORDER BY date
            ''', (user_id, start_date.isoformat(), end_date.isoformat()))
            
            daily_data = cursor.fetchall()
            
            # Get response time trends
            cursor.execute('''
                SELECT DATE(timestamp) as date, 
                       AVG(response_time) as avg_response_time,
                       COUNT(*) as interactions
                FROM analytics_interactions
                WHERE user_id = ? AND timestamp BETWEEN ? AND ?
                GROUP BY DATE(timestamp)
                ORDER BY date
            ''', (user_id, start_date.isoformat(), end_date.isoformat()))
            
            response_time_data = cursor.fetchall()
            conn.close()
            
            # Process trends
            trends = []
            query_counts = []
            
            for date, queries, avg_q_len, avg_r_len in daily_data:
                trends.append({
                    "date": date,
                    "queries": queries,
                    "avg_query_length": round(avg_q_len or 0, 1),
                    "avg_response_length": round(avg_r_len or 0, 1)
                })
                query_counts.append(queries)
            
            # Calculate trend direction
            trend_direction = "stable"
            if len(query_counts) >= 7:
                recent_avg = statistics.mean(query_counts[-7:])
                earlier_avg = statistics.mean(query_counts[:7])
                
                if recent_avg > earlier_avg * 1.2:
                    trend_direction = "increasing"
                elif recent_avg < earlier_avg * 0.8:
                    trend_direction = "decreasing"
            
            return {
                "daily_trends": trends,
                "trend_direction": trend_direction,
                "peak_activity_day": max(trends, key=lambda x: x["queries"])["date"] if trends else None,
                "avg_daily_queries": round(statistics.mean(query_counts), 1) if query_counts else 0,
                "consistency_score": self._calculate_consistency_score(query_counts)
            }
            
        except Exception as e:
            print(f"❌ Error getting performance trends: {e}")
            return {}
    
    async def _analyze_learning_patterns(self, user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze learning patterns and habits"""
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Get hourly activity patterns
            cursor.execute('''
                SELECT strftime('%H', timestamp) as hour, COUNT(*) as queries
                FROM interactions
                WHERE user_id = ? AND timestamp BETWEEN ? AND ?
                GROUP BY strftime('%H', timestamp)
                ORDER BY hour
            ''', (user_id, start_date.isoformat(), end_date.isoformat()))
            
            hourly_activity = {f"{int(row[0]):02d}:00": row[1] for row in cursor.fetchall()}
            
            # Get day of week patterns
            cursor.execute('''
                SELECT strftime('%w', timestamp) as dow, COUNT(*) as queries
                FROM interactions
                WHERE user_id = ? AND timestamp BETWEEN ? AND ?
                GROUP BY strftime('%w', timestamp)
                ORDER BY dow
            ''', (user_id, start_date.isoformat(), end_date.isoformat()))
            
            dow_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
            weekly_activity = {}
            
            for row in cursor.fetchall():
                dow_index = int(row[0])
                weekly_activity[dow_names[dow_index]] = row[1]
            
            # Session length analysis
            cursor.execute('''
                SELECT session_id, 
                       MIN(timestamp) as start_time,
                       MAX(timestamp) as end_time,
                       COUNT(*) as queries_in_session
                FROM interactions
                WHERE user_id = ? AND timestamp BETWEEN ? AND ?
                GROUP BY session_id
                HAVING COUNT(*) > 1
            ''', (user_id, start_date.isoformat(), end_date.isoformat()))
            
            session_data = cursor.fetchall()
            session_lengths = []
            
            for session_id, start_time, end_time, query_count in session_data:
                try:
                    start_dt = datetime.fromisoformat(start_time)
                    end_dt = datetime.fromisoformat(end_time)
                    duration_minutes = (end_dt - start_dt).total_seconds() / 60
                    session_lengths.append(duration_minutes)
                except:
                    continue
            
            conn.close()
            
            # Find peak hours and days
            peak_hour = max(hourly_activity.items(), key=lambda x: x[1])[0] if hourly_activity else "N/A"
            peak_day = max(weekly_activity.items(), key=lambda x: x[1])[0] if weekly_activity else "N/A"
            
            return {
                "hourly_activity": hourly_activity,
                "weekly_activity": weekly_activity,
                "peak_hour": peak_hour,
                "peak_day": peak_day,
                "avg_session_length_minutes": round(statistics.mean(session_lengths), 1) if session_lengths else 0,
                "total_sessions_analyzed": len(session_lengths),
                "learning_style": self._determine_learning_style(hourly_activity, weekly_activity, session_lengths)
            }
            
        except Exception as e:
            print(f"❌ Error analyzing learning patterns: {e}")
            return {}
    
    async def _get_session_analytics(self, user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get detailed session analytics"""
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Get session statistics
            cursor.execute('''
                SELECT 
                    session_id,
                    COUNT(*) as message_count,
                    MIN(timestamp) as start_time,
                    MAX(timestamp) as end_time,
                    AVG(LENGTH(query)) as avg_query_length
                FROM interactions
                WHERE user_id = ? AND timestamp BETWEEN ? AND ?
                GROUP BY session_id
                ORDER BY start_time DESC
                LIMIT 20
            ''', (user_id, start_date.isoformat(), end_date.isoformat()))
            
            recent_sessions = []
            total_messages = 0
            
            for row in cursor.fetchall():
                session_id, msg_count, start_time, end_time, avg_q_len = row
                
                try:
                    start_dt = datetime.fromisoformat(start_time)
                    end_dt = datetime.fromisoformat(end_time)
                    duration = (end_dt - start_dt).total_seconds() / 60
                except:
                    duration = 0
                
                recent_sessions.append({
                    "session_id": session_id,
                    "message_count": msg_count,
                    "duration_minutes": round(duration, 1),
                    "start_time": start_time,
                    "avg_query_length": round(avg_q_len or 0, 1)
                })
                
                total_messages += msg_count
            
            conn.close()
            
            return {
                "recent_sessions": recent_sessions,
                "total_sessions": len(recent_sessions),
                "total_messages": total_messages,
                "avg_messages_per_session": round(total_messages / max(1, len(recent_sessions)), 1),
                "most_active_session": max(recent_sessions, key=lambda x: x["message_count"]) if recent_sessions else None
            }
            
        except Exception as e:
            print(f"❌ Error getting session analytics: {e}")
            return {}
    
    async def _calculate_learning_streak(self, user_id: str, cursor) -> int:
        """Calculate consecutive days of learning activity"""
        
        try:
            cursor.execute('''
                SELECT DISTINCT DATE(timestamp) as date
                FROM interactions
                WHERE user_id = ?
                ORDER BY date DESC
                LIMIT 100
            ''', (user_id,))
            
            dates = [row[0] for row in cursor.fetchall()]
            
            if not dates:
                return 0
            
            streak = 1
            current_date = datetime.strptime(dates[0], '%Y-%m-%d').date()
            
            for date_str in dates[1:]:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
                if (current_date - date).days == 1:
                    streak += 1
                    current_date = date
                else:
                    break
            
            return streak
            
        except Exception as e:
            print(f"❌ Error calculating learning streak: {e}")
            return 0
    
    def _calculate_consistency_score(self, query_counts: List[int]) -> float:
        """Calculate consistency score (0-100) based on activity variance"""
        
        if len(query_counts) < 2:
            return 100.0
        
        try:
            mean_queries = statistics.mean(query_counts)
            if mean_queries == 0:
                return 100.0
            
            std_dev = statistics.stdev(query_counts)
            coefficient_of_variation = std_dev / mean_queries
            
            # Convert to 0-100 scale (lower CV = higher consistency)
            consistency = max(0, 100 - (coefficient_of_variation * 50))
            return round(consistency, 1)
            
        except Exception:
            return 50.0
    
    def _determine_learning_style(
        self, 
        hourly_activity: Dict[str, int], 
        weekly_activity: Dict[str, int],
        session_lengths: List[float]
    ) -> str:
        """Determine user's learning style based on patterns"""
        
        try:
            # Analyze time preferences
            morning_hours = sum(hourly_activity.get(f"{h:02d}:00", 0) for h in range(6, 12))
            afternoon_hours = sum(hourly_activity.get(f"{h:02d}:00", 0) for h in range(12, 18))
            evening_hours = sum(hourly_activity.get(f"{h:02d}:00", 0) for h in range(18, 24))
            
            time_preference = "morning"
            if afternoon_hours > morning_hours and afternoon_hours > evening_hours:
                time_preference = "afternoon"
            elif evening_hours > morning_hours and evening_hours > afternoon_hours:
                time_preference = "evening"
            
            # Analyze session patterns
            avg_session_length = statistics.mean(session_lengths) if session_lengths else 0
            
            if avg_session_length > 30:
                session_style = "deep_focus"
            elif avg_session_length > 15:
                session_style = "moderate"
            else:
                session_style = "quick_bursts"
            
            # Analyze weekly patterns
            weekday_activity = sum(weekly_activity.get(day, 0) for day in 
                                 ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
            weekend_activity = sum(weekly_activity.get(day, 0) for day in ["Saturday", "Sunday"])
            
            week_preference = "weekdays" if weekday_activity > weekend_activity else "weekends"
            
            return f"{time_preference}_{session_style}_{week_preference}"
            
        except Exception:
            return "mixed_pattern"
    
    async def _generate_recommendations(
        self, 
        user_id: str, 
        basic_stats: Dict[str, Any],
        subject_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate personalized learning recommendations"""
        
        recommendations = []
        
        try:
            # Activity-based recommendations
            queries_per_day = basic_stats.get("queries_per_day", 0)
            
            if queries_per_day < 2:
                recommendations.append("Try to engage with StudyMate daily for better learning consistency")
            elif queries_per_day > 20:
                recommendations.append("Consider taking breaks between study sessions to improve retention")
            
            # Streak-based recommendations
            streak = basic_stats.get("learning_streak_days", 0)
            
            if streak == 0:
                recommendations.append("Start building a learning streak by studying a little each day")
            elif streak >= 7:
                recommendations.append(f"Great job maintaining a {streak}-day learning streak! Keep it up!")
            
            # Subject diversity recommendations
            subjects_count = subject_analysis.get("total_subjects", 0)
            
            if subjects_count < 2:
                recommendations.append("Try exploring different subjects to broaden your knowledge")
            elif subjects_count >= 5:
                recommendations.append("You're studying diverse subjects - great for well-rounded learning!")
            
            # Performance recommendations
            top_subjects = subject_analysis.get("top_subjects", [])
            
            if top_subjects:
                top_subject = top_subjects[0]["subject"]
                recommendations.append(f"You're doing great in {top_subject}! Consider exploring advanced topics")
            
            # General recommendations
            if not recommendations:
                recommendations.append("Keep up the great work with your studies!")
            
            return recommendations[:5]  # Limit to 5 recommendations
            
        except Exception as e:
            print(f"❌ Error generating recommendations: {e}")
            return ["Keep learning and exploring new topics!"]
    
    async def get_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        """Get dashboard-specific analytics data"""
        
        try:
            # Get data for different time periods
            today_stats = await self._get_basic_stats(user_id, 
                datetime.now().replace(hour=0, minute=0, second=0), 
                datetime.now())
            
            week_stats = await self._get_basic_stats(user_id,
                datetime.now() - timedelta(days=7),
                datetime.now())
            
            month_stats = await self._get_basic_stats(user_id,
                datetime.now() - timedelta(days=30),
                datetime.now())
            
            # Get subject analysis
            subject_analysis = await self._analyze_subjects(user_id,
                datetime.now() - timedelta(days=30),
                datetime.now())
            
            return {
                "today_queries": today_stats.get("total_queries", 0),
                "week_queries": week_stats.get("total_queries", 0),
                "month_queries": month_stats.get("total_queries", 0),
                "total_study_time": month_stats.get("study_time_minutes", 0),
                "active_sessions": week_stats.get("total_sessions", 0),
                "learning_streak": month_stats.get("learning_streak_days", 0),
                "top_subjects": subject_analysis.get("top_subjects", [])[:3],
                "recent_activity": today_stats.get("daily_activity", [])[:7],
                "performance_trend": week_stats.get("trend_direction", "stable")
            }
            
        except Exception as e:
            print(f"❌ Error getting dashboard data: {e}")
            return {}