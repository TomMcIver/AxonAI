#!/usr/bin/env python3
"""
Mastery Tracking Agent - Analyzes student interactions to track mastery and trends
"""

import sqlite3
import json
from datetime import datetime

class MasteryTrackingAgent:
    """Analyzes chat history to determine topic mastery and learning trends"""
    
    def __init__(self, db_path='school_ai.db'):
        self.db_path = db_path
        
        # Keywords for positive understanding indicators
        self.positive_indicators = [
            'yes', 'got it', 'understand', 'thanks', 'clear', 'makes sense',
            'i see', 'oh', 'right', 'correct', 'okay', 'ok', 'great'
        ]
        
        # Keywords for negative understanding indicators
        self.negative_indicators = [
            'no', 'confused', "don't understand", "don't get", 'help',
            'stuck', 'lost', 'what', 'huh', 'difficult', 'hard', 'wrong'
        ]
        
        # Subject-specific topic keywords for mastery tracking
        self.topic_keywords = {
            'math': {
                'algebra': ['x', 'equation', 'solve', 'variable', 'expression'],
                'geometry': ['triangle', 'circle', 'angle', 'area', 'perimeter'],
                'arithmetic': ['add', 'subtract', 'multiply', 'divide', 'fraction'],
                'calculus': ['derivative', 'integral', 'limit', 'slope', 'rate']
            },
            'science': {
                'biology': ['cell', 'organism', 'DNA', 'evolution', 'photosynthesis'],
                'chemistry': ['atom', 'molecule', 'reaction', 'element', 'compound'],
                'physics': ['force', 'energy', 'motion', 'gravity', 'velocity']
            },
            'english': {
                'grammar': ['verb', 'noun', 'sentence', 'punctuation', 'tense'],
                'writing': ['essay', 'paragraph', 'thesis', 'argument', 'structure'],
                'literature': ['theme', 'character', 'plot', 'symbolism', 'metaphor']
            },
            'history': {
                'ancient': ['rome', 'greece', 'egypt', 'civilization', 'empire'],
                'modern': ['war', 'revolution', 'democracy', 'industrial', 'reform'],
                'american': ['constitution', 'president', 'civil war', 'independence']
            }
        }
    
    def _get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def analyze_interaction_quality(self, interaction):
        """
        Analyze a single interaction for understanding quality
        
        Args:
            interaction (dict): Single chat interaction with 'user' and 'tutor' keys
            
        Returns:
            float: Quality score between 0.0 and 1.0
        """
        user_message = interaction.get('user', '').lower()
        tutor_response = interaction.get('tutor', '').lower()
        
        score = 0.5  # Start at neutral
        
        # Check for positive indicators
        positive_count = sum(1 for word in self.positive_indicators if word in user_message)
        score += positive_count * 0.1
        
        # Check for negative indicators
        negative_count = sum(1 for word in self.negative_indicators if word in user_message)
        score -= negative_count * 0.15
        
        # Longer user responses might indicate engagement (cap bonus at 0.2)
        message_length_bonus = min(len(user_message.split()) / 50, 0.2)
        score += message_length_bonus
        
        # Questions from user might indicate curiosity (slightly positive)
        if '?' in user_message:
            score += 0.05
        
        # Clamp score between 0 and 1
        return max(0.0, min(1.0, score))
    
    def identify_topics_in_text(self, text, subject):
        """
        Identify which topics are discussed in the text
        
        Args:
            text (str): Text to analyze
            subject (str): Subject area
            
        Returns:
            list: List of identified topics
        """
        text_lower = text.lower()
        subject_lower = subject.lower()
        identified_topics = []
        
        # Get topic keywords for the subject
        subject_topics = self.topic_keywords.get(subject_lower, {})
        
        # Check each topic's keywords
        for topic, keywords in subject_topics.items():
            if any(keyword in text_lower for keyword in keywords):
                identified_topics.append(topic)
        
        return identified_topics
    
    def calculate_mastery_levels(self, chat_history, subject):
        """
        Calculate topic-wise mastery levels from chat history
        
        Args:
            chat_history (list): List of chat interactions
            subject (str): Student's subject
            
        Returns:
            dict: Topic-wise mastery percentages
        """
        if not chat_history:
            return {}
        
        # Track quality scores per topic
        topic_scores = {}
        topic_counts = {}
        
        for interaction in chat_history:
            # Calculate quality score for this interaction
            quality_score = self.analyze_interaction_quality(interaction)
            
            # Identify topics discussed
            combined_text = interaction.get('user', '') + ' ' + interaction.get('tutor', '')
            topics = self.identify_topics_in_text(combined_text, subject)
            
            # Update topic scores
            if topics:
                for topic in topics:
                    if topic not in topic_scores:
                        topic_scores[topic] = []
                    topic_scores[topic].append(quality_score)
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
            else:
                # If no specific topic identified, use general subject
                general_topic = 'general'
                if general_topic not in topic_scores:
                    topic_scores[general_topic] = []
                topic_scores[general_topic].append(quality_score)
                topic_counts[general_topic] = topic_counts.get(general_topic, 0) + 1
        
        # Calculate average mastery percentage per topic
        mastery_levels = {}
        for topic, scores in topic_scores.items():
            # Average score converted to percentage
            avg_score = sum(scores) / len(scores)
            mastery_percentage = round(avg_score * 100, 1)
            mastery_levels[topic] = {
                'percentage': mastery_percentage,
                'interactions': len(scores)
            }
        
        return mastery_levels
    
    def detect_trend(self, student_id, new_mastery_levels):
        """
        Detect learning trend by comparing current and previous mastery levels
        
        Args:
            student_id (int): Student's ID
            new_mastery_levels (dict): Newly calculated mastery levels
            
        Returns:
            str: "up", "flat", or "down"
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get previous mastery levels
        cursor.execute('SELECT mastery_levels FROM student_profiles WHERE id = ?', (student_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result or not result[0] or result[0] == '{}':
            return 'flat'  # No previous data
        
        previous_mastery = json.loads(result[0])
        
        # Calculate average percentages
        if not new_mastery_levels:
            return 'flat'
        
        new_avg = sum(topic['percentage'] for topic in new_mastery_levels.values()) / len(new_mastery_levels)
        
        if not previous_mastery:
            return 'flat'
        
        prev_avg = sum(topic['percentage'] for topic in previous_mastery.values()) / len(previous_mastery)
        
        # Determine trend
        difference = new_avg - prev_avg
        
        if difference > 2.0:  # Improved by more than 2%
            return 'up'
        elif difference < -2.0:  # Declined by more than 2%
            return 'down'
        else:
            return 'flat'
    
    def update_student_mastery(self, student_id):
        """
        Main method: Analyze student and update mastery tracking fields
        
        Args:
            student_id (int): Student's ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get student data
        cursor.execute('''
            SELECT name, subject, chat_history, mastery_levels 
            FROM student_profiles 
            WHERE id = ?
        ''', (student_id,))
        
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            raise ValueError(f"Student with ID {student_id} not found")
        
        name, subject, chat_history_json, old_mastery_json = result
        
        # Parse chat history
        chat_history = json.loads(chat_history_json) if chat_history_json else []
        
        if not chat_history:
            print(f"⚠ No chat history for student {name} (ID: {student_id})")
            conn.close()
            return
        
        # Calculate new mastery levels
        new_mastery_levels = self.calculate_mastery_levels(chat_history, subject)
        
        # Detect trend
        trend = self.detect_trend(student_id, new_mastery_levels)
        
        # Update database
        now = datetime.now().isoformat()
        cursor.execute('''
            UPDATE student_profiles 
            SET mastery_levels = ?, trend = ?, updated_at = ?
            WHERE id = ?
        ''', (json.dumps(new_mastery_levels), trend, now, student_id))
        
        conn.commit()
        conn.close()
        
        # Print results
        print(f"✓ Updated mastery tracking for {name} (ID: {student_id})")
        print(f"  Subject: {subject}")
        print(f"  Trend: {trend.upper()}")
        print(f"  Mastery Levels:")
        for topic, data in new_mastery_levels.items():
            print(f"    - {topic.capitalize()}: {data['percentage']}% ({data['interactions']} interactions)")
    
    def get_mastery_report(self, student_id):
        """
        Get a formatted mastery report for a student
        
        Args:
            student_id (int): Student's ID
            
        Returns:
            dict: Mastery report with all tracking data
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT name, subject, mastery_levels, trend, understanding_score, last_interaction
            FROM student_profiles 
            WHERE id = ?
        ''', (student_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            raise ValueError(f"Student with ID {student_id} not found")
        
        name, subject, mastery_json, trend, understanding_score, last_interaction = result
        mastery_levels = json.loads(mastery_json) if mastery_json else {}
        
        return {
            'student_id': student_id,
            'name': name,
            'subject': subject,
            'mastery_levels': mastery_levels,
            'trend': trend,
            'understanding_score': understanding_score,
            'last_interaction': last_interaction
        }
