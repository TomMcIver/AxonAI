import json
import os
import requests
import tiktoken
from datetime import datetime, date
from models import AIModel, ChatMessage, User, Class, StudentProfile, ContentFile, TokenUsage
from app import db

# AI Provider Configuration
# Change this variable to switch between AI providers:
# "openai" - Use OpenAI GPT models
# "aws" - Use AWS-hosted custom models
# "local" - Use locally hosted models
AI_PROVIDER = "openai"  # Force OpenAI provider for this implementation

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
                # Using gpt-4o-mini for cost optimization as requested by user
                self.default_model = "gpt-4o-mini"
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
    
    def count_tokens(self, text):
        """Count tokens in text using tiktoken"""
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model("gpt-4o-mini")
            return len(encoding.encode(text))
        except:
            # Fallback: approximate token count
            return int(len(text.split()) * 1.3)
    
    def check_token_limit(self, user_id):
        """Check if user has exceeded daily token limit"""
        today = date.today()
        usage = TokenUsage.query.filter_by(user_id=user_id, date=today).first()
        
        if not usage:
            return True, 0  # No usage today, within limit
        
        return usage.tokens_used < 10000, usage.tokens_used
    
    def update_token_usage(self, user_id, tokens_used):
        """Update daily token usage for user"""
        today = date.today()
        usage = TokenUsage.query.filter_by(user_id=user_id, date=today).first()
        
        if not usage:
            usage = TokenUsage(user_id=user_id, date=today, tokens_used=0, requests_made=0)
            db.session.add(usage)
        
        usage.tokens_used += tokens_used
        usage.requests_made += 1
        db.session.commit()
    
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
            
            # Use enhanced AI profile summary for token efficiency
            profile_summary = student.get_ai_profile_summary()
            
            context = {
                'profile_summary': profile_summary,
                'recent_topics': [chat.message[:40] + '...' for chat in recent_chats] if recent_chats else [],
                'subject': class_obj.subject,
                'learning_accommodations': self._get_learning_accommodations(student),
                'available_content': [cf.name for cf in class_content[:3]]  # Limit for tokens
            }
            
            if student_profile:
                context['learning_profile'] = student_profile.to_dict()
            
            return context
            
        except Exception as e:
            print(f"Error getting student context: {e}")
            return {}
    
    def _get_learning_accommodations(self, student):
        """Generate learning accommodations based on student profile"""
        accommodations = []
        
        if student.learning_difficulty:
            difficulty = student.learning_difficulty.lower()
            if 'dyslexia' in difficulty:
                accommodations.append("Use clear, simple language and break down complex concepts")
            elif 'adhd' in difficulty:
                accommodations.append("Keep responses concise and use bullet points")
            elif 'autism' in difficulty:
                accommodations.append("Provide structured, step-by-step explanations")
            else:
                accommodations.append(f"Consider learning support needs for {student.learning_difficulty}")
        
        if student.primary_language and student.primary_language != 'English':
            accommodations.append(f"Student's primary language is {student.primary_language}, use clear English")
        
        if student.learning_style:
            style = student.learning_style.lower()
            if 'visual' in style:
                accommodations.append("Use visual examples and descriptions")
            elif 'auditory' in style:
                accommodations.append("Use clear explanations with examples")
            elif 'kinesthetic' in style:
                accommodations.append("Suggest hands-on activities and practical examples")
        
        return accommodations
    
    def generate_response(self, message, student_id, class_id):
        """Generate AI response based on student context and message"""
        try:
            # Get class AI model
            class_obj = Class.query.get(class_id)
            if not class_obj:
                return "Class not found."
            
            ai_model = class_obj.ai_model
            if not ai_model:
                # Get default AI model for this subject
                ai_model = AIModel.query.filter_by(subject=class_obj.subject).first()
                if not ai_model:
                    # Create a default model if none exists
                    ai_model = AIModel(
                        subject=class_obj.subject or 'general',
                        model_name='gpt-4o-mini',
                        prompt_template=f'You are an AI tutor for {class_obj.subject or "general"} ONLY.',
                        max_tokens=800,
                        temperature=0.7
                    )
                    db.session.add(ai_model)
                    db.session.commit()
            context = self.get_student_context(student_id, class_id)
            
            # Use the optimized profile summary
            subject = context.get('subject', 'general')
            profile_summary = context.get('profile_summary', 'Student profile not available')
            recent_topics = context.get('recent_topics', [])
            accommodations = context.get('learning_accommodations', [])
            
            system_prompt = f"""You are a specialized {subject} AI tutor. You can ONLY discuss topics related to {subject}.

STRICT RULES:
1. ONLY answer questions about {subject}
2. If asked about other subjects, politely redirect: "I can only help with {subject}. Please ask your teacher about other subjects."

STUDENT PROFILE:
{profile_summary}

RECENT LEARNING CONTEXT:
Recent topics: {', '.join(recent_topics) if recent_topics else 'First interaction'}

AVAILABLE MATERIALS: 
{', '.join(context.get('available_content', []))}

LEARNING ACCOMMODATIONS:
{chr(10).join(f'- {acc}' for acc in accommodations) if accommodations else 'No specific accommodations'}

Provide personalized {subject} help based on this student's learning style, current performance, and goals. Keep responses concise and educational."""
            
            # Count tokens before sending
            prompt_tokens = self.count_tokens(system_prompt + message)
            
            # Generate response based on provider
            if self.provider == "openai":
                ai_response = self._generate_openai_response(system_prompt, message, ai_model)
            elif self.provider == "aws":
                ai_response = self._generate_aws_response(system_prompt, message, ai_model)
            else:  # local
                ai_response = self._generate_local_response(system_prompt, message, ai_model)
            
            # Count response tokens and update usage
            response_tokens = self.count_tokens(ai_response)
            total_tokens = prompt_tokens + response_tokens
            self.update_token_usage(student_id, total_tokens)
            
            # Store chat message
            try:
                chat_message = ChatMessage(
                    user_id=student_id,
                    class_id=class_id,
                    ai_model_id=ai_model.id if ai_model else 1,  # Default AI model ID
                    message=message,
                    response=ai_response,
                    message_type='student',
                    context_data=json.dumps(context) if context else '{}'
                )
                db.session.add(chat_message)
                db.session.commit()
                print(f"Successfully saved chat message to database")
            except Exception as db_error:
                print(f"Database error saving chat: {db_error}")
                db.session.rollback()
                # Continue anyway, just log the error
            
            return ai_response
            
        except Exception as e:
            print(f"Error generating AI response: {e}")
            import traceback
            traceback.print_exc()
            return "Sorry, I encountered an error. Please try again."
    
    def generate_teacher_response(self, message, teacher_id, class_id):
        """Generate AI response for teacher inquiries about students and teaching"""
        try:
            from models import Class, User
            
            # Check daily token limit
            if not self.check_token_limit(teacher_id):
                return "Daily token limit reached. Please try again tomorrow."
            
            # Get class and students context
            class_obj = Class.query.get(class_id)
            if not class_obj:
                return "Class not found."
            
            students = class_obj.get_students()
            student_profiles = []
            class_insights = {}
            
            # Collect student information
            for student in students:
                profile_summary = student.get_ai_profile_summary()
                chat_count = ChatMessage.query.filter_by(user_id=student.id, class_id=class_id).count()
                
                student_profiles.append({
                    'name': student.get_full_name(),
                    'profile': profile_summary,
                    'chat_interactions': chat_count,
                    'average_grade': student.get_class_average(class_id)
                })
            
            # Get class insights
            insights = self.get_teacher_insights(teacher_id, class_id)
            
            system_prompt = f"""You are an AI teaching assistant helping a teacher understand their students and improve their teaching methods.

CLASS INFORMATION:
Subject: {class_obj.subject}
Class: {class_obj.name}
Total Students: {len(students)}

STUDENT PROFILES:
{chr(10).join([f"- {s['name']}: {s['profile'][:200]}..." for s in student_profiles])}

CLASS INSIGHTS:
{json.dumps(insights.get(f'class_{class_id}', {}), indent=2) if insights else 'No insights available'}

INSTRUCTIONS:
- Provide thoughtful, practical teaching advice
- Reference specific students when relevant (use names if mentioned)
- Suggest evidence-based teaching strategies
- Consider individual learning needs and class dynamics
- Focus on student engagement, learning outcomes, and support

Answer the teacher's question with specific, actionable advice based on the student data provided."""

            # Generate response based on provider
            if self.provider == "openai":
                ai_response = self._generate_openai_response(system_prompt, message, None)
            elif self.provider == "aws":
                ai_response = self._generate_aws_response(system_prompt, message, None)
            else:  # local
                ai_response = self._generate_local_response(system_prompt, message, None)
            
            # Count tokens and update usage
            total_tokens = self.count_tokens(system_prompt + message + ai_response)
            self.update_token_usage(teacher_id, total_tokens)
            
            # Store teacher chat message
            try:
                chat_message = ChatMessage(
                    user_id=teacher_id,
                    class_id=class_id,
                    ai_model_id=1,  # Default AI model for teachers
                    message=message,
                    response=ai_response,
                    message_type='teacher',
                    context_data=json.dumps({
                        'student_count': len(students),
                        'subject': class_obj.subject,
                        'insights_available': bool(insights)
                    })
                )
                db.session.add(chat_message)
                db.session.commit()
                print(f"Successfully saved teacher chat message to database")
            except Exception as db_error:
                print(f"Database error saving teacher chat: {db_error}")
                db.session.rollback()
            
            return ai_response
            
        except Exception as e:
            print(f"Error generating teacher AI response: {e}")
            import traceback
            traceback.print_exc()
            return "Sorry, I encountered an error. Please try again."
    
    def _create_student_summary(self, context):
        """Create a concise student summary to optimize token usage"""
        student_info = context.get('student_info', {})
        return f"""Student: {student_info.get('name', 'Student')} (Age {student_info.get('age', 'Unknown')})
Learning: {student_info.get('learning_style', 'Mixed')} learner, {student_info.get('preferred_difficulty', 'intermediate')} level
Performance: Grade average {student_info.get('average_grade', 'N/A')}, trend {student_info.get('grade_trend', 'stable')}
Goals: {student_info.get('academic_goals', 'General improvement')[:100]}..."""
    
    def _summarize_recent_chats(self, student_id, class_id, limit=5):
        """Summarize recent chat history to optimize memory usage"""
        try:
            recent_chats = ChatMessage.query.filter_by(
                user_id=student_id, 
                class_id=class_id
            ).order_by(ChatMessage.created_at.desc()).limit(limit).all()
            
            if not recent_chats:
                return "No previous interactions"
            
            topics = []
            for chat in recent_chats:
                # Extract key topics from message (first 50 chars)
                topic = chat.message[:50].replace('\n', ' ')
                topics.append(topic)
            
            return f"Recent topics: {', '.join(topics[:3])}..." if topics else "No recent topics"
            
        except Exception as e:
            print(f"Error summarizing chats: {e}")
            return "Recent chat history unavailable"
    
    def _generate_openai_response(self, system_prompt, message, ai_model):
        """Generate response using OpenAI"""
        try:
            # Use GPT-4o-mini for cost optimization (most affordable GPT-4 model)
            model_name = "gpt-4o-mini"
            
            response = self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=800,  # Reduced for cost optimization
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API error: {e}")
            import traceback
            traceback.print_exc()
            return f"Sorry, I encountered an error. Please try again."
    
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
        # Always use OpenAI if available, even in "demo mode"
        if self.provider == "openai" and self.client:
            subject = ai_model.subject if ai_model else "general"
            system_prompt = f"You are an AI tutor for {subject} ONLY. Only answer questions about {subject}."
            return self._generate_openai_response(system_prompt, message, ai_model)
        
        # Fallback only if truly no AI service
        subject = ai_model.subject if ai_model else "general"
        return f"I'm sorry, but I need to be connected to an AI service to help you with {subject} questions. Please ask your teacher to configure the AI settings."
    
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
            return messages  # Return actual model objects, not dictionaries
            
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