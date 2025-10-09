#!/usr/bin/env python3
"""
Quiz/Exam Builder Agent - Generates quizzes based on student weaknesses
"""

import sqlite3
import json
from datetime import datetime
import random

class QuizBuilderAgent:
    """Generates quizzes targeting student's weakest topics"""
    
    def __init__(self, db_path='school_ai.db'):
        self.db_path = db_path
        
        # Hardcoded question templates for different topics
        self.question_bank = {
            'math': {
                'algebra': [
                    {'q': 'Solve for x: 2x + 5 = 13', 'a': '4', 'choices': ['3', '4', '5', '6']},
                    {'q': 'Solve for x: 3x - 7 = 8', 'a': '5', 'choices': ['3', '4', '5', '6']},
                    {'q': 'Solve for x: x/2 + 3 = 7', 'a': '8', 'choices': ['6', '7', '8', '9']},
                    {'q': 'What is x if 4x = 20?', 'a': '5', 'choices': ['4', '5', '6', '7']},
                    {'q': 'Solve: 5x - 10 = 15', 'a': '5', 'choices': ['3', '4', '5', '6']},
                    {'q': 'If 2x + 3 = 11, what is x?', 'a': '4', 'choices': ['2', '3', '4', '5']},
                    {'q': 'Solve for x: x + 7 = 15', 'a': '8', 'choices': ['6', '7', '8', '9']},
                ],
                'geometry': [
                    {'q': 'Area of a rectangle with length 5 and width 3?', 'a': '15', 'choices': ['12', '13', '15', '16']},
                    {'q': 'Perimeter of a square with side 4?', 'a': '16', 'choices': ['12', '14', '16', '18']},
                    {'q': 'Sum of angles in a triangle?', 'a': '180', 'choices': ['90', '180', '270', '360']},
                    {'q': 'Area of a triangle: base=6, height=4?', 'a': '12', 'choices': ['10', '12', '14', '16']},
                    {'q': 'Circumference formula uses which constant?', 'a': 'pi', 'choices': ['e', 'pi', 'phi', 'tau']},
                    {'q': 'A circle has how many sides?', 'a': '0', 'choices': ['0', '1', 'infinite', 'undefined']},
                ],
                'arithmetic': [
                    {'q': '12 + 15 = ?', 'a': '27', 'choices': ['25', '26', '27', '28']},
                    {'q': '8 × 7 = ?', 'a': '56', 'choices': ['54', '56', '58', '60']},
                    {'q': '100 - 37 = ?', 'a': '63', 'choices': ['61', '62', '63', '64']},
                    {'q': '144 ÷ 12 = ?', 'a': '12', 'choices': ['10', '11', '12', '13']},
                    {'q': '1/2 + 1/4 = ?', 'a': '3/4', 'choices': ['1/2', '2/3', '3/4', '1']},
                    {'q': '0.5 × 0.4 = ?', 'a': '0.2', 'choices': ['0.1', '0.2', '0.3', '0.4']},
                ],
                'general': [
                    {'q': 'What is 5 squared?', 'a': '25', 'choices': ['20', '25', '30', '35']},
                    {'q': 'What is the square root of 49?', 'a': '7', 'choices': ['6', '7', '8', '9']},
                    {'q': 'What is 10% of 200?', 'a': '20', 'choices': ['15', '20', '25', '30']},
                    {'q': 'What is 2 to the power of 3?', 'a': '8', 'choices': ['6', '7', '8', '9']},
                ]
            },
            'science': {
                'biology': [
                    {'q': 'What is the powerhouse of the cell?', 'a': 'mitochondria', 'choices': ['nucleus', 'mitochondria', 'ribosome', 'vacuole']},
                    {'q': 'What process do plants use to make food?', 'a': 'photosynthesis', 'choices': ['respiration', 'photosynthesis', 'digestion', 'fermentation']},
                    {'q': 'DNA stands for?', 'a': 'deoxyribonucleic acid', 'choices': ['deoxyribonucleic acid', 'ribonucleic acid', 'amino acid', 'nucleic acid']},
                    {'q': 'What carries oxygen in blood?', 'a': 'red blood cells', 'choices': ['white blood cells', 'red blood cells', 'platelets', 'plasma']},
                    {'q': 'How many chromosomes in human cells?', 'a': '46', 'choices': ['23', '46', '48', '92']},
                ],
                'chemistry': [
                    {'q': 'What is H2O?', 'a': 'water', 'choices': ['oxygen', 'hydrogen', 'water', 'peroxide']},
                    {'q': 'Atomic number of Carbon?', 'a': '6', 'choices': ['4', '6', '8', '12']},
                    {'q': 'What is NaCl?', 'a': 'salt', 'choices': ['sugar', 'salt', 'acid', 'base']},
                    {'q': 'pH of pure water?', 'a': '7', 'choices': ['0', '7', '14', 'varies']},
                    {'q': 'Gold symbol on periodic table?', 'a': 'Au', 'choices': ['Go', 'Gd', 'Au', 'Ag']},
                ],
                'physics': [
                    {'q': 'Speed of light is approximately?', 'a': '300000 km/s', 'choices': ['3000 km/s', '30000 km/s', '300000 km/s', '3000000 km/s']},
                    {'q': 'Newton\'s first law is about?', 'a': 'inertia', 'choices': ['gravity', 'inertia', 'force', 'energy']},
                    {'q': 'Unit of force?', 'a': 'Newton', 'choices': ['Joule', 'Newton', 'Watt', 'Pascal']},
                    {'q': 'What is F = ma?', 'a': 'Newton\'s second law', 'choices': ['Newton\'s first law', 'Newton\'s second law', 'Newton\'s third law', 'Law of gravity']},
                ],
                'general': [
                    {'q': 'What is the study of living things?', 'a': 'biology', 'choices': ['chemistry', 'physics', 'biology', 'geology']},
                    {'q': 'Boiling point of water (Celsius)?', 'a': '100', 'choices': ['0', '50', '100', '212']},
                    {'q': 'How many planets in our solar system?', 'a': '8', 'choices': ['7', '8', '9', '10']},
                ]
            },
            'english': {
                'grammar': [
                    {'q': 'Which is a verb: run, happy, quickly?', 'a': 'run', 'choices': ['run', 'happy', 'quickly', 'none']},
                    {'q': 'Which is an adjective: beautiful, run, quickly?', 'a': 'beautiful', 'choices': ['beautiful', 'run', 'quickly', 'none']},
                    {'q': 'Plural of "child"?', 'a': 'children', 'choices': ['childs', 'children', 'childrens', 'child']},
                    {'q': 'Past tense of "go"?', 'a': 'went', 'choices': ['goed', 'went', 'gone', 'going']},
                    {'q': 'What is a noun?', 'a': 'person, place, or thing', 'choices': ['action word', 'describing word', 'person, place, or thing', 'connecting word']},
                ],
                'writing': [
                    {'q': 'A paragraph should have at least how many sentences?', 'a': '3', 'choices': ['1', '2', '3', '5']},
                    {'q': 'The main idea of an essay is in the?', 'a': 'thesis', 'choices': ['introduction', 'thesis', 'conclusion', 'body']},
                    {'q': 'Which punctuation ends a statement?', 'a': 'period', 'choices': ['comma', 'period', 'question mark', 'exclamation']},
                    {'q': 'A comma is used to?', 'a': 'separate items', 'choices': ['end sentence', 'separate items', 'show ownership', 'indicate question']},
                ],
                'literature': [
                    {'q': 'A story\'s main character is the?', 'a': 'protagonist', 'choices': ['antagonist', 'protagonist', 'narrator', 'author']},
                    {'q': 'The turning point in a story is the?', 'a': 'climax', 'choices': ['exposition', 'rising action', 'climax', 'resolution']},
                    {'q': 'Comparing using "like" or "as" is a?', 'a': 'simile', 'choices': ['metaphor', 'simile', 'personification', 'hyperbole']},
                    {'q': 'The lesson of a story is the?', 'a': 'theme', 'choices': ['plot', 'setting', 'theme', 'conflict']},
                ],
                'general': [
                    {'q': 'How many letters in the alphabet?', 'a': '26', 'choices': ['24', '25', '26', '27']},
                    {'q': 'A sentence must have a subject and a?', 'a': 'predicate', 'choices': ['object', 'predicate', 'adjective', 'adverb']},
                    {'q': 'Which is a vowel?', 'a': 'e', 'choices': ['b', 'c', 'e', 'f']},
                ]
            },
            'history': {
                'ancient': [
                    {'q': 'Ancient Egypt\'s writing system?', 'a': 'hieroglyphics', 'choices': ['cuneiform', 'hieroglyphics', 'alphabetic', 'pictographic']},
                    {'q': 'Roman Empire capital?', 'a': 'Rome', 'choices': ['Athens', 'Rome', 'Alexandria', 'Constantinople']},
                    {'q': 'Greek philosopher who taught Alexander?', 'a': 'Aristotle', 'choices': ['Socrates', 'Plato', 'Aristotle', 'Homer']},
                    {'q': 'The Great Wall was built in?', 'a': 'China', 'choices': ['Egypt', 'Rome', 'China', 'Greece']},
                ],
                'modern': [
                    {'q': 'World War I began in which year?', 'a': '1914', 'choices': ['1914', '1918', '1939', '1945']},
                    {'q': 'The Industrial Revolution started in?', 'a': 'England', 'choices': ['France', 'England', 'America', 'Germany']},
                    {'q': 'Who invented the telephone?', 'a': 'Alexander Graham Bell', 'choices': ['Edison', 'Tesla', 'Alexander Graham Bell', 'Marconi']},
                    {'q': 'The Cold War was between USA and?', 'a': 'USSR', 'choices': ['China', 'USSR', 'Germany', 'Japan']},
                ],
                'american': [
                    {'q': 'Declaration of Independence year?', 'a': '1776', 'choices': ['1765', '1776', '1789', '1800']},
                    {'q': 'First US President?', 'a': 'George Washington', 'choices': ['Thomas Jefferson', 'George Washington', 'John Adams', 'Benjamin Franklin']},
                    {'q': 'US Civil War was in which century?', 'a': '19th', 'choices': ['17th', '18th', '19th', '20th']},
                    {'q': 'The Constitution has how many articles?', 'a': '7', 'choices': ['5', '7', '10', '27']},
                ],
                'general': [
                    {'q': 'The Renaissance began in?', 'a': 'Italy', 'choices': ['France', 'Italy', 'England', 'Spain']},
                    {'q': 'What year did Columbus sail?', 'a': '1492', 'choices': ['1492', '1500', '1520', '1607']},
                    {'q': 'The printing press was invented by?', 'a': 'Gutenberg', 'choices': ['Da Vinci', 'Gutenberg', 'Luther', 'Galileo']},
                ]
            }
        }
    
    def _get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def get_weakest_topics(self, student_id, limit=3):
        """
        Get student's weakest topics from mastery_levels
        
        Args:
            student_id (int): Student's ID
            limit (int): Number of weak topics to return
            
        Returns:
            list: List of (topic, percentage) tuples
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT name, subject, mastery_levels 
            FROM student_profiles 
            WHERE id = ?
        ''', (student_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            raise ValueError(f"Student with ID {student_id} not found")
        
        name, subject, mastery_json = result
        
        if not mastery_json or mastery_json == '{}':
            # No mastery data, return general topic
            return [('general', 0.0)]
        
        mastery_levels = json.loads(mastery_json)
        
        # Sort by percentage (ascending) to get weakest topics
        sorted_topics = sorted(
            mastery_levels.items(),
            key=lambda x: x[1]['percentage']
        )
        
        # Return weakest topics
        weakest = [(topic, data['percentage']) for topic, data in sorted_topics[:limit]]
        
        return weakest if weakest else [('general', 0.0)]
    
    def generate_quiz(self, student_id, num_questions=5):
        """
        Generate a quiz for the student based on their weakest topics
        
        Args:
            student_id (int): Student's ID
            num_questions (int): Number of questions to generate
            
        Returns:
            int: Quiz ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get student info
        cursor.execute('SELECT name, subject FROM student_profiles WHERE id = ?', (student_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            raise ValueError(f"Student with ID {student_id} not found")
        
        name, subject = result
        subject_lower = subject.lower()
        
        # Get weakest topics
        weak_topics = self.get_weakest_topics(student_id, limit=3)
        
        # Get question bank for the subject
        if subject_lower not in self.question_bank:
            subject_lower = 'math'  # Default to math if subject not found
        
        subject_questions = self.question_bank[subject_lower]
        
        # Select questions from weak topics
        selected_questions = []
        
        for topic, percentage in weak_topics:
            if topic in subject_questions:
                topic_questions = subject_questions[topic]
                # Randomly select 2-3 questions from this topic
                count = min(len(topic_questions), max(2, num_questions // len(weak_topics)))
                selected_questions.extend(random.sample(topic_questions, count))
        
        # If not enough questions, add from general or random topics
        if len(selected_questions) < num_questions:
            all_questions = []
            for topic_q in subject_questions.values():
                all_questions.extend(topic_q)
            
            remaining = num_questions - len(selected_questions)
            available = [q for q in all_questions if q not in selected_questions]
            
            if available:
                selected_questions.extend(random.sample(available, min(remaining, len(available))))
        
        # Limit to requested number
        selected_questions = selected_questions[:num_questions]
        
        # Determine primary topic for the quiz
        primary_topic = weak_topics[0][0] if weak_topics else 'general'
        
        # Store quiz in database
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO quizzes (student_id, topic, questions, answers, score, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (student_id, primary_topic, json.dumps(selected_questions), '[]', 0.0, now))
        
        quiz_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✓ Generated quiz {quiz_id} for {name}")
        print(f"  Topic: {primary_topic}")
        print(f"  Questions: {len(selected_questions)}")
        print(f"  Based on weak topics: {', '.join([t[0] for t in weak_topics])}")
        
        return quiz_id
    
    def get_quiz(self, quiz_id):
        """Get quiz details"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, student_id, topic, questions, answers, score, created_at
            FROM quizzes WHERE id = ?
        ''', (quiz_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            raise ValueError(f"Quiz with ID {quiz_id} not found")
        
        return {
            'id': result[0],
            'student_id': result[1],
            'topic': result[2],
            'questions': json.loads(result[3]),
            'answers': json.loads(result[4]) if result[4] else [],
            'score': result[5],
            'created_at': result[6]
        }
    
    def submit_quiz(self, quiz_id, student_answers):
        """
        Submit quiz answers and compute score
        
        Args:
            quiz_id (int): Quiz ID
            student_answers (list): List of student's answers
        """
        quiz = self.get_quiz(quiz_id)
        questions = quiz['questions']
        
        # Calculate score
        correct = 0
        for i, question in enumerate(questions):
            if i < len(student_answers):
                if student_answers[i].lower().strip() == question['a'].lower().strip():
                    correct += 1
        
        score = (correct / len(questions)) * 100 if questions else 0
        
        # Update quiz in database
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE quizzes 
            SET answers = ?, score = ?
            WHERE id = ?
        ''', (json.dumps(student_answers), score, quiz_id))
        
        # Update student's understanding score based on quiz performance
        # Get current understanding score
        cursor.execute('''
            SELECT understanding_score 
            FROM student_profiles 
            WHERE id = ?
        ''', (quiz['student_id'],))
        
        current_score = cursor.fetchone()[0]
        
        # Calculate new understanding score (weighted average)
        # 70% current score + 30% quiz score (normalized to 0-10 scale)
        quiz_contribution = (score / 100) * 10  # Convert percentage to 0-10 scale
        new_score = (current_score * 0.7) + (quiz_contribution * 0.3)
        new_score = min(new_score, 10.0)  # Cap at 10
        
        # Update student profile
        now = datetime.now().isoformat()
        cursor.execute('''
            UPDATE student_profiles 
            SET understanding_score = ?, updated_at = ?
            WHERE id = ?
        ''', (new_score, now, quiz['student_id']))
        
        conn.commit()
        conn.close()
        
        print(f"✓ Quiz {quiz_id} submitted and scored")
        print(f"  Correct: {correct}/{len(questions)}")
        print(f"  Score: {score:.1f}%")
        print(f"  Understanding score updated: {current_score:.1f} → {new_score:.1f}")
        
        return {
            'correct': correct,
            'total': len(questions),
            'score': score,
            'old_understanding': current_score,
            'new_understanding': new_score
        }
    
    def get_student_quizzes(self, student_id):
        """Get all quizzes for a student"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, topic, score, created_at
            FROM quizzes
            WHERE student_id = ?
            ORDER BY created_at DESC
        ''', (student_id,))
        
        quizzes = []
        for row in cursor.fetchall():
            quizzes.append({
                'id': row[0],
                'topic': row[1],
                'score': row[2],
                'created_at': row[3]
            })
        
        conn.close()
        return quizzes
