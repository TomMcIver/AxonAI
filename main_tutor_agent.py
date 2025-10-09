import sqlite3
import json
import os
from datetime import datetime
from openai import OpenAI

class MainTutorAgent:
    """Main Tutor Agent - handles direct student interactions and stores chat history"""
    
    def __init__(self, db_path='school_ai.db'):
        self.db_path = db_path
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
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
        Generate a tutor response using GPT AI
        
        Args:
            student_id (int): Student's ID
            user_message (str): Message from the student
            
        Returns:
            str: Tutor's response
        """
        profile = self.get_student_profile(student_id)
        subject = profile['subject']
        name = profile['name']
        chat_history = profile['chat_history']
        
        # Build system prompt for the AI tutor
        system_prompt = f"""You are an expert {subject} tutor helping a student named {name}. 

Your role:
- Provide clear, helpful explanations tailored to the student's level
- Break down complex concepts into simple steps
- Ask guiding questions to encourage critical thinking
- Be encouraging and patient
- Stay focused on {subject} topics
- Provide examples when helpful
- Check for understanding before moving forward

Keep responses concise but thorough (2-4 sentences typically).
Be friendly and supportive while maintaining educational value."""

        # Build conversation history for context
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent chat history for context (last 5 interactions)
        recent_history = chat_history[-5:] if len(chat_history) > 5 else chat_history
        for interaction in recent_history:
            messages.append({"role": "user", "content": interaction['user']})
            messages.append({"role": "assistant", "content": interaction['tutor']})
        
        # Add current message
        messages.append({"role": "user", "content": user_message})
        
        # Call OpenAI API
        try:
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_tokens=300
            )
            
            response = completion.choices[0].message.content
            
        except Exception as e:
            # Fallback response if API fails
            response = f"I'm here to help with {subject}! Could you please rephrase your question? I want to make sure I understand what you need help with."
            print(f"⚠ OpenAI API error: {e}")
        
        # Record the interaction
        self.record_interaction(student_id, user_message, response)
        
        return response
