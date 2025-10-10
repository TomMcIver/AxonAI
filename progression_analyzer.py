"""
Student Understanding Progression Analyzer
Analyzes AI interaction data to determine how student understanding evolves over time
"""
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from app import db
from models import AIInteraction, ChatMessage, User


class ProgressionAnalyzer:
    """Analyzes student progression based on AI interaction patterns"""
    
    def calculate_understanding_score(self, interaction):
        """
        Calculate understanding score from AI interaction metrics
        Returns a score from 0-100 based on engagement and success indicators
        """
        base_score = 50  # Start at 50%
        
        # Engagement score contribution (0-10 scale to 0-30 points)
        if interaction.engagement_score:
            engagement_contribution = (interaction.engagement_score / 10) * 30
            base_score += engagement_contribution
        
        # Success indicator contribution (20 points)
        if interaction.success_indicator:
            base_score += 20
        
        # Message length as proxy for depth of understanding
        # Longer, more detailed questions often indicate deeper thinking
        if interaction.chat_message and interaction.chat_message.message:
            msg_length = len(interaction.chat_message.message)
            # 50-200 chars = normal, 200+ = detailed (bonus points)
            if msg_length > 100:
                base_score += min(10, (msg_length - 100) / 20)
        
        return min(100, max(0, base_score))
    
    def get_progression_data(self, student_id, days=30):
        """
        Get understanding progression over time for a student
        
        Args:
            student_id: The student's user ID
            days: Number of days to analyze (default 30)
        
        Returns:
            List of data points: [{'date': '2025-10-10', 'understanding': 75.5}, ...]
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get all AI interactions for this student, ordered by time
        interactions = AIInteraction.query.filter(
            AIInteraction.user_id == student_id,
            AIInteraction.created_at >= cutoff_date
        ).order_by(AIInteraction.created_at).all()
        
        if not interactions:
            return []
        
        # Group interactions by date and calculate average understanding per day
        progression_by_date = {}
        
        for interaction in interactions:
            date_key = interaction.created_at.strftime('%Y-%m-%d')
            understanding = self.calculate_understanding_score(interaction)
            
            if date_key not in progression_by_date:
                progression_by_date[date_key] = []
            
            progression_by_date[date_key].append(understanding)
        
        # Calculate average understanding per date
        progression_data = []
        for date, scores in sorted(progression_by_date.items()):
            avg_understanding = sum(scores) / len(scores)
            progression_data.append({
                'date': date,
                'understanding': round(avg_understanding, 1),
                'interactions': len(scores)
            })
        
        return progression_data
    
    def get_recent_trend(self, student_id, recent_count=5):
        """
        Get the trend in recent interactions (improving, declining, stable)
        
        Args:
            student_id: The student's user ID
            recent_count: Number of recent interactions to analyze
        
        Returns:
            dict: {'trend': 'improving', 'change': 12.5, 'current_level': 78.3}
        """
        interactions = AIInteraction.query.filter(
            AIInteraction.user_id == student_id
        ).order_by(desc(AIInteraction.created_at)).limit(recent_count * 2).all()
        
        if len(interactions) < 4:
            return {'trend': 'insufficient_data', 'change': 0, 'current_level': 0}
        
        # Split into recent and previous
        recent = interactions[:recent_count]
        previous = interactions[recent_count:recent_count * 2]
        
        # Calculate average understanding for each period
        recent_avg = sum(self.calculate_understanding_score(i) for i in recent) / len(recent)
        previous_avg = sum(self.calculate_understanding_score(i) for i in previous) / len(previous)
        
        change = recent_avg - previous_avg
        
        if change > 5:
            trend = 'improving'
        elif change < -5:
            trend = 'declining'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'change': round(change, 1),
            'current_level': round(recent_avg, 1)
        }
    
    def get_multi_student_progression(self, student_ids, days=30):
        """
        Get progression data for multiple students for comparison
        
        Args:
            student_ids: List of student user IDs
            days: Number of days to analyze
        
        Returns:
            dict: {student_id: {'name': 'Alex', 'data': [progression points]}}
        """
        results = {}
        
        for student_id in student_ids:
            student = User.query.get(student_id)
            if student:
                progression = self.get_progression_data(student_id, days)
                results[student_id] = {
                    'name': student.first_name,
                    'data': progression,
                    'trend': self.get_recent_trend(student_id)
                }
        
        return results
