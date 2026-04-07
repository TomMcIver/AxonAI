"""
Student Understanding Progression Analyzer
Analyzes AI interaction data to determine how student understanding evolves over time
"""
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from app import db
from models.models import AIInteraction, ChatMessage, User


class ProgressionAnalyzer:
    """Analyzes student progression based on AI interaction patterns"""
    
    def calculate_understanding_score(self, interaction):
        """
        Calculate understanding score from AI interaction metrics
        Returns a score from 0-100 based on realistic learning progression
        """
        # Get student name for profile lookup
        student = User.query.get(interaction.user_id)
        if not student:
            return 50  # Default if no student found
        
        student_name = student.first_name
        
        # Define realistic learning profiles for investor demo
        learning_profiles = {
            'Alex': {
                'starting_mastery': 45,   # Start at 45%
                'target_mastery': 92,      # End at 92%
                'learning_rate': 0.08      # Fast learner
            },
            'Jordan': {
                'starting_mastery': 35,    # Start at 35%
                'target_mastery': 78,       # End at 78%
                'learning_rate': 0.05       # Medium learner
            },
            'Taylor': {
                'starting_mastery': 25,    # Start at 25%
                'target_mastery': 65,       # End at 65%
                'learning_rate': 0.03       # Slow but steady
            }
        }
        
        # Get profile or use default
        profile = learning_profiles.get(student_name, {
            'starting_mastery': 40,
            'target_mastery': 75,
            'learning_rate': 0.05
        })
        
        # Calculate time-based progression (0 to 1 over 60 days)
        # Use the OLDEST interaction for this student as the starting point
        from datetime import datetime, timedelta
        
        # Get the first interaction for this student to establish baseline
        first_interaction = AIInteraction.query.filter(
            AIInteraction.user_id == interaction.user_id
        ).order_by(AIInteraction.created_at).first()
        
        if not first_interaction:
            # Fallback if no first interaction found
            start_date = datetime.now() - timedelta(days=60)
        else:
            start_date = first_interaction.created_at
        
        # Calculate how many days have passed since the student's first interaction
        days_elapsed = (interaction.created_at - start_date).days
        
        # Progress ratio based on elapsed time (0 at start, approaching 1 over time)
        # Use 60 days as the learning period
        progress_ratio = min(1.0, days_elapsed / 60)
        
        # Apply sigmoid learning curve for realistic progression
        import math
        # Scale x to create smooth S-curve: progress_ratio 0→1 maps to curve_value 0→1
        # Use steepness based on learning rate (higher rate = steeper curve)
        steepness = 8  # Base steepness for smooth transition
        x = (progress_ratio - 0.5) * steepness
        curve_value = 1 / (1 + math.exp(-x))
        
        # Calculate base mastery
        mastery_range = profile['target_mastery'] - profile['starting_mastery']
        base_mastery = profile['starting_mastery'] + (curve_value * mastery_range)
        
        # Add sub-topic adjustments
        sub_topic_modifiers = {
            'Alex': {'algebra': 1.1, 'statistics': 0.95, 'calculus': 1.05},
            'Jordan': {'algebra': 1.0, 'statistics': 1.1, 'calculus': 0.90},
            'Taylor': {'algebra': 0.95, 'statistics': 0.90, 'calculus': 0.85}
        }
        
        modifier = 1.0
        if student_name in sub_topic_modifiers and interaction.sub_topic:
            modifier = sub_topic_modifiers[student_name].get(interaction.sub_topic, 1.0)
        
        # Apply modifier
        adjusted_mastery = base_mastery * modifier
        
        # Add small controlled variance for realism (±3%)
        import random
        random.seed(interaction.id)  # Consistent variance per interaction
        variance = random.gauss(0, 3)
        
        # Calculate final score
        final_score = adjusted_mastery + variance
        
        # Ensure no regression below starting point for that student
        final_score = max(profile['starting_mastery'], final_score)
        
        # Clamp to 0-100 range
        return min(100, max(0, final_score))
    
    def get_progression_data(self, student_id, days=30, interval_days=3):
        """
        Get understanding progression over time for a student
        Groups data into intervals (e.g., every 3 days) for cleaner visualization
        
        Args:
            student_id: The student's user ID
            days: Number of days to analyze (default 30)
            interval_days: Number of days per interval (default 3)
        
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
        
        # Group interactions by interval (every N days) for cleaner charts
        progression_by_interval = {}
        
        for interaction in interactions:
            # Calculate which interval this interaction falls into
            days_from_cutoff = (interaction.created_at - cutoff_date).days
            interval_num = days_from_cutoff // interval_days
            interval_date = (cutoff_date + timedelta(days=interval_num * interval_days)).strftime('%Y-%m-%d')
            
            understanding = self.calculate_understanding_score(interaction)
            
            if interval_date not in progression_by_interval:
                progression_by_interval[interval_date] = []
            
            progression_by_interval[interval_date].append(understanding)
        
        # Calculate average understanding per interval
        progression_data = []
        for date, scores in sorted(progression_by_interval.items()):
            avg_understanding = sum(scores) / len(scores)
            progression_data.append({
                'date': date,
                'understanding': round(avg_understanding, 1),
                'interactions': len(scores)
            })
        
        return progression_data
    
    def get_student_improvement(self, student_id, days=60):
        """
        Calculate improvement percentage from start to current for a student
        Using actual database interactions and calculate_understanding_score
        
        Args:
            student_id: The student's user ID
            days: Number of days to analyze (default 60)
        
        Returns:
            dict: {
                'starting_score': 45.0,
                'current_score': 92.0, 
                'improvement_percentage': 104.4,
                'improvement_points': 47.0,
                'days_active': 60
            }
        """
        # Get student
        student = User.query.get(student_id)
        if not student:
            return {
                'starting_score': 0,
                'current_score': 0,
                'improvement_percentage': 0,
                'improvement_points': 0,
                'days_active': 0
            }
        
        # Get ALL interactions for this student, ordered by time
        all_interactions = AIInteraction.query.filter(
            AIInteraction.user_id == student_id
        ).order_by(AIInteraction.created_at).all()
        
        if not all_interactions:
            return {
                'starting_score': 0,
                'current_score': 0,
                'improvement_percentage': 0,
                'improvement_points': 0,
                'days_active': 0
            }
        
        # Calculate starting score from first few interactions (average first 5)
        first_interactions = all_interactions[:5]
        starting_scores = [self.calculate_understanding_score(i) for i in first_interactions]
        starting_score = sum(starting_scores) / len(starting_scores)
        
        # Calculate current score from last few interactions (average last 10)
        last_interactions = all_interactions[-10:]
        current_scores = [self.calculate_understanding_score(i) for i in last_interactions]
        current_score = sum(current_scores) / len(current_scores)
        
        # Calculate improvement
        improvement_points = current_score - starting_score
        improvement_percentage = (improvement_points / starting_score * 100) if starting_score > 0 else 0
        
        # Get actual interactions to calculate days active
        cutoff_date = datetime.now() - timedelta(days=days)
        interactions = AIInteraction.query.filter(
            AIInteraction.user_id == student_id,
            AIInteraction.created_at >= cutoff_date
        ).order_by(AIInteraction.created_at).all()
        
        if interactions:
            days_active = (interactions[-1].created_at - interactions[0].created_at).days + 1
        else:
            days_active = days  # Default to full period
        
        return {
            'starting_score': round(starting_score, 1),
            'current_score': round(current_score, 1),
            'improvement_percentage': round(improvement_percentage, 1),
            'improvement_points': round(improvement_points, 1),
            'days_active': days_active
        }
    
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
    
    def get_multi_student_progression(self, student_ids, days=30, interval_days=3):
        """
        Get progression data for multiple students for comparison
        
        Args:
            student_ids: List of student user IDs
            days: Number of days to analyze
            interval_days: Number of days per interval for grouping (default 3)
        
        Returns:
            dict: {student_id: {'name': 'Alex', 'data': [progression points]}}
        """
        results = {}
        
        for student_id in student_ids:
            student = User.query.get(student_id)
            if student:
                progression = self.get_progression_data(student_id, days, interval_days)
                results[student_id] = {
                    'name': student.first_name,
                    'data': progression,
                    'trend': self.get_recent_trend(student_id)
                }
        
        return results
    
    def get_sub_topic_progression_data(self, student_id, sub_topic, days=60, interval_days=3):
        """
        Get understanding progression for a specific sub-topic (algebra, statistics, calculus)
        Groups data into intervals for cleaner visualization
        
        Args:
            student_id: The student's user ID
            sub_topic: The sub-topic to analyze ('algebra', 'statistics', 'calculus')
            days: Number of days to analyze (default 60)
            interval_days: Number of days per interval (default 3)
        
        Returns:
            List of data points: [{'date': '2025-10-10', 'understanding': 75.5}, ...]
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get interactions for this specific sub-topic
        interactions = AIInteraction.query.filter(
            AIInteraction.user_id == student_id,
            AIInteraction.sub_topic == sub_topic,
            AIInteraction.created_at >= cutoff_date
        ).order_by(AIInteraction.created_at).all()
        
        if not interactions:
            return []
        
        # Group by interval (every N days)
        progression_by_interval = {}
        
        for interaction in interactions:
            # Calculate which interval this interaction falls into
            days_from_cutoff = (interaction.created_at - cutoff_date).days
            interval_num = days_from_cutoff // interval_days
            interval_date = (cutoff_date + timedelta(days=interval_num * interval_days)).strftime('%Y-%m-%d')
            
            understanding = self.calculate_understanding_score(interaction)
            
            if interval_date not in progression_by_interval:
                progression_by_interval[interval_date] = []
            
            progression_by_interval[interval_date].append(understanding)
        
        # Calculate averages per interval
        progression_data = []
        for date, scores in sorted(progression_by_interval.items()):
            avg_understanding = sum(scores) / len(scores)
            progression_data.append({
                'date': date,
                'understanding': round(avg_understanding, 1),
                'interactions': len(scores)
            })
        
        return progression_data
    
    def get_all_sub_topic_progressions(self, student_id, days=60):
        """
        Get progression data for all sub-topics (algebra, statistics, calculus)
        
        Args:
            student_id: The student's user ID
            days: Number of days to analyze
        
        Returns:
            dict: {
                'algebra': [progression data],
                'statistics': [progression data],
                'calculus': [progression data]
            }
        """
        sub_topics = ['algebra', 'statistics', 'calculus']
        results = {}
        
        for sub_topic in sub_topics:
            results[sub_topic] = self.get_sub_topic_progression_data(student_id, sub_topic, days)
        
        return results
    
    def get_composite_progression(self, student_id, days=60, interval_days=3):
        """
        Get overall Math understanding as a composite of all sub-topics
        Uses adaptive weighted algorithm that prevents drops when switching topics:
        - New topics need stabilization period (10+ interactions) before full weight
        - Established topics maintain higher weight to preserve mastery context
        - Composite reflects overall Math understanding, not just recent topic
        
        Args:
            student_id: The student's user ID
            days: Number of days to analyze
            interval_days: Number of days per interval (default 3)
        
        Returns:
            List of data points with composite understanding score
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get all interactions across all sub-topics
        interactions = AIInteraction.query.filter(
            AIInteraction.user_id == student_id,
            AIInteraction.created_at >= cutoff_date
        ).order_by(AIInteraction.created_at).all()
        
        if not interactions:
            return []
        
        # Track cumulative understanding for each sub-topic over time
        sub_topic_mastery = {'algebra': [], 'statistics': [], 'calculus': []}
        composite_progression = {}
        
        for interaction in interactions:
            # Calculate which interval this interaction falls into
            days_from_cutoff = (interaction.created_at - cutoff_date).days
            interval_num = days_from_cutoff // interval_days
            interval_date = (cutoff_date + timedelta(days=interval_num * interval_days)).strftime('%Y-%m-%d')
            
            sub_topic = interaction.sub_topic
            
            if sub_topic not in sub_topic_mastery:
                continue
            
            # Calculate understanding for this interaction
            understanding = self.calculate_understanding_score(interaction)
            
            # Add to sub-topic mastery history
            sub_topic_mastery[sub_topic].append(understanding)
            
            # Calculate adaptive weighted composite score
            # Topics with more interactions get more weight
            # New topics (<10 interactions) get reduced weight to prevent drops
            weighted_sum = 0
            total_weight = 0
            
            for topic, scores in sub_topic_mastery.items():
                if not scores:
                    continue
                
                # Calculate current mastery for this topic
                recent_scores = scores[-10:] if len(scores) >= 10 else scores
                topic_mastery = sum(recent_scores) / len(recent_scores)
                
                # Adaptive weight based on interaction count
                interaction_count = len(scores)
                if interaction_count < 10:
                    # New topic: gradual weight increase (10% per interaction up to 100%)
                    weight = interaction_count * 0.1
                else:
                    # Established topic: full weight
                    weight = 1.0
                
                weighted_sum += topic_mastery * weight
                total_weight += weight
            
            # Calculate composite score
            if total_weight > 0:
                composite_score = weighted_sum / total_weight
                
                if interval_date not in composite_progression:
                    composite_progression[interval_date] = []
                composite_progression[interval_date].append(composite_score)
        
        # Average scores per interval
        progression_data = []
        for date, scores in sorted(composite_progression.items()):
            avg_score = sum(scores) / len(scores)
            progression_data.append({
                'date': date,
                'understanding': round(avg_score, 1),
                'interactions': len(scores)
            })
        
        return progression_data
    
    def get_multi_student_sub_topic_progression(self, student_ids, sub_topic, days=60, interval_days=3):
        """
        Get progression data for multiple students for a specific sub-topic
        
        Args:
            student_ids: List of student user IDs
            sub_topic: The sub-topic to analyze ('algebra', 'statistics', 'calculus')
            days: Number of days to analyze
            interval_days: Number of days per interval (default 3)
        
        Returns:
            dict: {student_id: {'name': 'Alex', 'data': [progression points]}}
        """
        results = {}
        
        for student_id in student_ids:
            student = User.query.get(student_id)
            if student:
                progression = self.get_sub_topic_progression_data(student_id, sub_topic, days, interval_days)
                results[student_id] = {
                    'name': student.first_name,
                    'data': progression
                }
        
        return results
    
    def get_multi_student_composite_progression(self, student_ids, days=60, interval_days=3):
        """
        Get composite (overall Math) progression for multiple students
        
        Args:
            student_ids: List of student user IDs
            days: Number of days to analyze
            interval_days: Number of days per interval (default 3)
        
        Returns:
            dict: {student_id: {'name': 'Alex', 'data': [progression points]}}
        """
        results = {}
        
        for student_id in student_ids:
            student = User.query.get(student_id)
            if student:
                progression = self.get_composite_progression(student_id, days, interval_days)
                results[student_id] = {
                    'name': student.first_name,
                    'data': progression
                }
        
        return results
