import sqlite3
import json
from datetime import datetime

class MainTutorAgent:
    """Main Tutor Agent - handles direct student interactions and stores chat history"""
    
    def __init__(self, db_path='school_ai.db'):
        self.db_path = db_path
    
    def _get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def create_student(self, name, subject):
        """
        Create a new student profile
        
        Args:
            name (str): Student's name
            subject (str): Subject they're studying
            
        Returns:
            int: Student ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO student_profiles 
            (name, subject, chat_history, understanding_score, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, subject, '[]', 0.0, now, now))
        
        student_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✓ Created student profile: {name} (ID: {student_id}) - Subject: {subject}")
        return student_id
    
    def record_interaction(self, student_id, user_message, ai_response):
        """
        Record a chat interaction and update student profile
        
        Args:
            student_id (int): Student's ID
            user_message (str): Message from the student
            ai_response (str): Response from the tutor
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get current chat history
        cursor.execute('SELECT chat_history, understanding_score FROM student_profiles WHERE id = ?', (student_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            raise ValueError(f"Student with ID {student_id} not found")
        
        chat_history = json.loads(result[0])
        current_score = result[1]
        
        # Add new interaction to chat history
        now = datetime.now().isoformat()
        chat_history.append({
            'timestamp': now,
            'user': user_message,
            'tutor': ai_response
        })
        
        # Calculate new understanding score (simple placeholder logic)
        # For now: increment by 0.1 for each interaction, max 10.0
        new_score = min(current_score + 0.1, 10.0)
        
        # Update database
        cursor.execute('''
            UPDATE student_profiles 
            SET chat_history = ?, 
                last_interaction = ?, 
                understanding_score = ?,
                updated_at = ?
            WHERE id = ?
        ''', (json.dumps(chat_history), now, new_score, now, student_id))
        
        conn.commit()
        conn.close()
        
        print(f"✓ Recorded interaction for student ID {student_id}")
        print(f"  Understanding score: {current_score:.1f} → {new_score:.1f}")
    
    def get_chat_history(self, student_id):
        """
        Get chat history for a student
        
        Args:
            student_id (int): Student's ID
            
        Returns:
            list: Chat history (list of interaction dictionaries)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT chat_history FROM student_profiles WHERE id = ?', (student_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        if not result:
            raise ValueError(f"Student with ID {student_id} not found")
        
        return json.loads(result[0])
    
    def get_student_profile(self, student_id):
        """
        Get complete student profile
        
        Args:
            student_id (int): Student's ID
            
        Returns:
            dict: Student profile with all fields
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, subject, last_interaction, chat_history, 
                   understanding_score, created_at, updated_at
            FROM student_profiles 
            WHERE id = ?
        ''', (student_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            raise ValueError(f"Student with ID {student_id} not found")
        
        return {
            'id': result[0],
            'name': result[1],
            'subject': result[2],
            'last_interaction': result[3],
            'chat_history': json.loads(result[4]),
            'understanding_score': result[5],
            'created_at': result[6],
            'updated_at': result[7]
        }
    
    def generate_response(self, student_id, user_message):
        """
        Generate a tutor response (currently rule-based, no external AI)
        
        Args:
            student_id (int): Student's ID
            user_message (str): Message from the student
            
        Returns:
            str: Tutor's response
        """
        profile = self.get_student_profile(student_id)
        subject = profile['subject'].lower()
        message_lower = user_message.lower()
        
        # Simple rule-based responses based on subject
        if subject == 'math' or subject == 'mathematics':
            if 'help' in message_lower or 'how' in message_lower:
                response = "I can help you with that! Let's break it down step by step. What specific part are you struggling with?"
            elif '?' in user_message:
                response = "That's a great question! In mathematics, we solve problems by identifying what we know and what we need to find. Can you show me your work so far?"
            else:
                response = "I see you're working on math. Remember to show your work and check each step carefully. What would you like to focus on?"
        
        elif subject == 'science':
            if 'help' in message_lower or 'how' in message_lower:
                response = "Science is all about observation and understanding! Let's explore this concept together. What have you learned so far?"
            elif '?' in user_message:
                response = "Excellent question! In science, we test our ideas through experiments. What do you think might happen and why?"
            else:
                response = "That's an interesting topic in science! Let's think about the key concepts. What observations can we make?"
        
        elif subject == 'english':
            if 'help' in message_lower or 'how' in message_lower:
                response = "I'm here to help with your English! Let's look at grammar, vocabulary, or writing structure. What do you need help with?"
            elif '?' in user_message:
                response = "Good question! In English, we think about meaning, structure, and style. Can you explain what you're trying to understand?"
            else:
                response = "English is about clear communication! Let's work on expressing your ideas effectively. What are you working on?"
        
        elif subject == 'history':
            if 'help' in message_lower or 'how' in message_lower:
                response = "History helps us understand the past! Let's explore the context and connections. What time period or event interests you?"
            elif '?' in user_message:
                response = "Great historical question! Let's consider the causes, effects, and key people involved. What do you already know about this?"
            else:
                response = "History is full of fascinating stories! Let's analyze the events and their significance. What would you like to explore?"
        
        else:
            # Generic response for any subject
            if 'help' in message_lower or 'how' in message_lower:
                response = f"I'm here to help you with {subject}! Let's work through this together. What specifically do you need assistance with?"
            elif '?' in user_message:
                response = f"That's a thoughtful question about {subject}! Let's explore it step by step. What are your initial thoughts?"
            else:
                response = f"I see you're studying {subject}. That's great! What would you like to learn or practice today?"
        
        # Record the interaction
        self.record_interaction(student_id, user_message, response)
        
        return response
