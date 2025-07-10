import json
import os
import requests
from datetime import datetime
from models import AIModel, ChatMessage, User, Class, StudentProfile, ContentFile
from app import db

# AI Provider Configuration
# Change this variable to switch between AI providers:
# "openai" - Use OpenAI GPT models
# "aws" - Use AWS-hosted custom models
# "local" - Use locally hosted models
AI_PROVIDER = os.environ.get("AI_PROVIDER", "local")  # Default to local for demos

class AIService:
    """Service for handling AI chatbot interactions with multiple providers"""
    
    def __init__(self):
        self.provider = AI_PROVIDER
        self.setup_provider()
    
    def setup_provider(self):
        """Initialize the appropriate AI provider"""
        if self.provider == "openai":
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "demo-key"))
                # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
                # do not change this unless explicitly requested by the user
                self.default_model = "gpt-4o"
                print("Using OpenAI provider")
            except Exception as e:
                print(f"OpenAI setup failed: {e}")
                self.provider = "local"
                self.setup_local_provider()
        
        elif self.provider == "aws":
            self.aws_endpoint = os.environ.get("AWS_AI_ENDPOINT", "https://your-aws-endpoint.amazonaws.com")
            self.aws_api_key = os.environ.get("AWS_AI_API_KEY", "demo-key")
            self.default_model = "custom-model"
            print("Using AWS hosted provider")
        
        else:  # local
            self.setup_local_provider()
    
    def setup_local_provider(self):
        """Setup local AI model provider"""
        self.local_endpoint = os.environ.get("LOCAL_AI_ENDPOINT", "http://localhost:11434")  # Ollama default
        self.default_model = os.environ.get("LOCAL_AI_MODEL", "llama2")  # Default local model
        print(f"Using local provider at {self.local_endpoint}")
        self.provider = "local"
    
    def get_student_context(self, student_id, class_id):
        """Get comprehensive student context for AI personalization"""
        try:
            student = User.query.get(student_id)
            class_obj = Class.query.get(class_id)
            student_profile = StudentProfile.query.filter_by(user_id=student_id).first()
            
            if not student or not class_obj:
                return {}
            
            # Get student's grades in this class
            grades = [g.grade for g in student.grades if g.assignment.class_id == class_id and g.grade is not None]
            avg_grade = sum(grades) / len(grades) if grades else None
            
            # Get recent chat history
            recent_chats = ChatMessage.query.filter_by(
                user_id=student_id,
                class_id=class_id
            ).order_by(ChatMessage.created_at.desc()).limit(5).all()
            
            # Get class content
            class_content = ContentFile.query.filter_by(class_id=class_id).all()
            
            context = {
                'student_info': {
                    'name': student.get_full_name(),
                    'age': student.age,
                    'learning_style': student.learning_style,
                    'interests': student.get_interests_list(),
                    'academic_goals': student.academic_goals,
                    'preferred_difficulty': student.preferred_difficulty,
                    'average_grade': avg_grade,
                    'grade_trend': 'improving' if len(grades) > 1 and grades[-1] > grades[0] else 'stable'
                },
                'class_info': {
                    'name': class_obj.name,
                    'subject': class_obj.subject,
                    'description': class_obj.description,
                    'available_content': [{'name': cf.name, 'type': cf.file_type} for cf in class_content]
                },
                'interaction_history': {
                    'recent_topics': [chat.message[:100] for chat in recent_chats],
                    'engagement_level': student.get_chat_summary(class_id)['engagement_level']
                }
            }
            
            if student_profile:
                context['learning_profile'] = student_profile.to_dict()
            
            return context
            
        except Exception as e:
            print(f"Error getting student context: {e}")
            return {}
    
    def generate_response(self, message, student_id, class_id):
        """Generate AI response based on student context and message"""
        try:
            # Get class AI model
            class_obj = Class.query.get(class_id)
            if not class_obj or not class_obj.ai_model:
                return "I'm sorry, but AI assistance is not available for this class."
            
            ai_model = class_obj.ai_model
            context = self.get_student_context(student_id, class_id)
            
            # Build system prompt with context
            system_prompt = f"""
            {ai_model.prompt_template}
            
            Student Context:
            - Name: {context.get('student_info', {}).get('name', 'Student')}
            - Age: {context.get('student_info', {}).get('age', 'Unknown')}
            - Learning Style: {context.get('student_info', {}).get('learning_style', 'Unknown')}
            - Interests: {', '.join(context.get('student_info', {}).get('interests', []))}
            - Academic Goals: {context.get('student_info', {}).get('academic_goals', 'Not specified')}
            - Preferred Difficulty: {context.get('student_info', {}).get('preferred_difficulty', 'intermediate')}
            - Current Grade Average: {context.get('student_info', {}).get('average_grade', 'No grades yet')}
            - Grade Trend: {context.get('student_info', {}).get('grade_trend', 'stable')}
            
            Class Context:
            - Subject: {context.get('class_info', {}).get('subject', 'Unknown')}
            - Class: {context.get('class_info', {}).get('name', 'Unknown')}
            - Available Materials: {', '.join([item['name'] for item in context.get('class_info', {}).get('available_content', [])])}
            
            Please provide a helpful, personalized response that considers this student's learning style, current performance, and academic goals.
            """
            
            # Generate response based on provider
            if self.provider == "openai":
                ai_response = self._generate_openai_response(system_prompt, message, ai_model)
            elif self.provider == "aws":
                ai_response = self._generate_aws_response(system_prompt, message, ai_model)
            else:  # local
                ai_response = self._generate_local_response(system_prompt, message, ai_model)
            
            # Store chat message
            chat_message = ChatMessage(
                user_id=student_id,
                class_id=class_id,
                ai_model_id=ai_model.id,
                message=message,
                response=ai_response,
                message_type='student',
                context_data=json.dumps(context)
            )
            db.session.add(chat_message)
            db.session.commit()
            
            return ai_response
            
        except Exception as e:
            print(f"Error generating AI response: {e}")
            return "I'm sorry, but I'm having trouble processing your request right now. Please try again later."
    
    def _generate_openai_response(self, system_prompt, message, ai_model):
        """Generate response using OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model=ai_model.model_name or self.default_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=ai_model.max_tokens,
                temperature=ai_model.temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return f"OpenAI service temporarily unavailable. Error: {str(e)}"
    
    def _generate_aws_response(self, system_prompt, message, ai_model):
        """Generate response using AWS-hosted model"""
        try:
            payload = {
                "model": ai_model.model_name or self.default_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                "max_tokens": ai_model.max_tokens,
                "temperature": ai_model.temperature
            }
            
            headers = {
                "Authorization": f"Bearer {self.aws_api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.aws_endpoint}/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                return f"AWS model service error: {response.status_code}"
                
        except Exception as e:
            print(f"AWS API error: {e}")
            return f"AWS model service temporarily unavailable. Error: {str(e)}"
    
    def _generate_local_response(self, system_prompt, message, ai_model):
        """Generate response using local model (Ollama/custom endpoint)"""
        try:
            # Try Ollama API format first
            payload = {
                "model": ai_model.model_name or self.default_model,
                "prompt": f"{system_prompt}\n\nUser: {message}\nAssistant:",
                "stream": False,
                "options": {
                    "temperature": ai_model.temperature,
                    "num_predict": ai_model.max_tokens
                }
            }
            
            response = requests.post(
                f"{self.local_endpoint}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get("response", "No response from local model")
            else:
                # Fallback to demo response
                return self._generate_demo_response(message, ai_model)
                
        except Exception as e:
            print(f"Local model error: {e}")
            return self._generate_demo_response(message, ai_model)
    
    def _generate_demo_response(self, message, ai_model):
        """Generate a demo response when no AI service is available"""
        subject = ai_model.subject if ai_model else "general"
        
        demo_responses = {
            "mathematics": [
                "Great question about math! Let me break this down step by step. In mathematics, it's important to understand the underlying concepts before moving to complex problems.",
                "I can help you with that math problem! Let's start with the basics and work our way up to more advanced concepts.",
                "Mathematics is all about patterns and logical thinking. Let me help you see the pattern in this problem."
            ],
            "science": [
                "Excellent science question! Scientific understanding comes from observation, hypothesis, and testing. Let me explain this concept clearly.",
                "Science is fascinating! This topic connects to many real-world applications. Let me show you how this works.",
                "Great scientific curiosity! Understanding the 'why' behind phenomena is key to scientific thinking."
            ],
            "english": [
                "Wonderful question about language and literature! Effective communication involves understanding both structure and meaning.",
                "English literature offers rich insights into human experience. Let me help you analyze this text.",
                "Great observation about language! Writing and reading are powerful tools for expression and understanding."
            ],
            "history": [
                "Interesting historical question! Understanding the past helps us make sense of the present and future.",
                "History is full of fascinating stories and important lessons. Let me provide some context for this topic.",
                "Excellent historical thinking! It's important to consider multiple perspectives when studying the past."
            ],
            "art": [
                "Wonderful artistic inquiry! Art is a powerful form of expression that reflects culture, emotion, and creativity.",
                "Great question about art! Creative expression takes many forms and serves many purposes in human society.",
                "Artistic exploration is exciting! Let me help you understand the techniques and meanings behind this work."
            ]
        }
        
        responses = demo_responses.get(subject, demo_responses["mathematics"])
        import random
        base_response = random.choice(responses)
        
        return f"{base_response}\n\n[Demo Mode: This is a simulated response. To enable full AI functionality, configure your AI provider settings.]"
    
    def get_teacher_insights(self, teacher_id, class_id=None):
        """Generate insights for teachers about their students"""
        try:
            teacher = User.query.get(teacher_id)
            if not teacher or teacher.role != 'teacher':
                return "Access denied."
            
            # Get teacher's classes
            teacher_classes = Class.query.filter_by(teacher_id=teacher_id).all()
            if class_id:
                teacher_classes = [cls for cls in teacher_classes if cls.id == class_id]
            
            insights = []
            
            for class_obj in teacher_classes:
                students = class_obj.get_students()
                class_insights = {
                    'class_name': class_obj.name,
                    'total_students': len(students),
                    'student_insights': []
                }
                
                for student in students:
                    # Get student's chat history and performance
                    chat_count = ChatMessage.query.filter_by(
                        user_id=student.id,
                        class_id=class_obj.id
                    ).count()
                    
                    avg_grade = student.get_class_average(class_obj.id)
                    
                    student_insight = {
                        'name': student.get_full_name(),
                        'engagement_level': 'high' if chat_count > 10 else 'medium' if chat_count > 3 else 'low',
                        'chat_interactions': chat_count,
                        'average_grade': avg_grade,
                        'learning_style': student.learning_style,
                        'needs_attention': avg_grade and avg_grade < 70,
                        'recent_topics': [
                            chat.message[:50] + "..." if len(chat.message) > 50 else chat.message
                            for chat in ChatMessage.query.filter_by(
                                user_id=student.id,
                                class_id=class_obj.id
                            ).order_by(ChatMessage.created_at.desc()).limit(3).all()
                        ]
                    }
                    class_insights['student_insights'].append(student_insight)
                
                insights.append(class_insights)
            
            return insights
            
        except Exception as e:
            print(f"Error generating teacher insights: {e}")
            return []
    
    def get_chat_history(self, user_id, class_id=None, limit=50):
        """Get chat history for a user and class"""
        try:
            query = ChatMessage.query.filter_by(user_id=user_id)
            if class_id:
                query = query.filter_by(class_id=class_id)
            
            messages = query.order_by(ChatMessage.created_at.desc()).limit(limit).all()
            return [msg.to_dict() for msg in messages]
            
        except Exception as e:
            print(f"Error getting chat history: {e}")
            return []
    
    def get_all_chat_data(self, teacher_id, class_id=None):
        """Get all chat data for teacher analysis"""
        try:
            teacher = User.query.get(teacher_id)
            if not teacher or teacher.role != 'teacher':
                return []
            
            # Get teacher's classes
            teacher_classes = Class.query.filter_by(teacher_id=teacher_id).all()
            if class_id:
                teacher_classes = [cls for cls in teacher_classes if cls.id == class_id]
            
            all_chat_data = []
            
            for class_obj in teacher_classes:
                students = class_obj.get_students()
                for student in students:
                    chat_messages = ChatMessage.query.filter_by(
                        user_id=student.id,
                        class_id=class_obj.id
                    ).order_by(ChatMessage.created_at.desc()).all()
                    
                    for chat in chat_messages:
                        chat_data = chat.to_dict()
                        chat_data['student_name'] = student.get_full_name()
                        chat_data['class_name'] = class_obj.name
                        all_chat_data.append(chat_data)
            
            return all_chat_data
            
        except Exception as e:
            print(f"Error getting all chat data: {e}")
            return []