import json
import os
import re
import requests
import tiktoken
from datetime import datetime, date
from models import (
    AIModel, ChatMessage, User, Class, StudentProfile, ContentFile, TokenUsage,
    AIInteraction, FailedStrategy, OptimizedProfile, MiniTest, MiniTestResponse,
    PredictedGrade
)
from app import db

SUBJECT_KEYWORDS = {
    'math': ['equation', 'solve', 'calculate', 'algebra', 'geometry', 'calculus', 'number', 'fraction', 
             'graph', 'function', 'derivative', 'integral', 'statistics', 'probability', 'triangle',
             'circle', 'angle', 'formula', 'x', 'y', 'variable', 'coefficient', 'polynomial', 'factor',
             'quadratic', 'linear', 'exponent', 'logarithm', 'matrix', 'vector', 'arithmetic', 'addition',
             'subtraction', 'multiplication', 'division', 'percent', 'ratio', 'proportion', 'prime'],
    'mathematics': ['equation', 'solve', 'calculate', 'algebra', 'geometry', 'calculus', 'number'],
    'science': ['experiment', 'hypothesis', 'biology', 'chemistry', 'physics', 'atom', 'molecule',
                'cell', 'organism', 'evolution', 'force', 'energy', 'matter', 'element', 'reaction',
                'gravity', 'motion', 'wave', 'light', 'electricity', 'magnet', 'ecosystem', 'photosynthesis',
                'dna', 'gene', 'protein', 'acid', 'base', 'periodic', 'newton', 'velocity', 'acceleration'],
    'english': ['grammar', 'essay', 'write', 'read', 'literature', 'poem', 'novel', 'sentence',
                'paragraph', 'vocabulary', 'spelling', 'punctuation', 'verb', 'noun', 'adjective',
                'adverb', 'pronoun', 'conjunction', 'preposition', 'metaphor', 'simile', 'theme',
                'character', 'plot', 'setting', 'narrative', 'dialogue', 'thesis', 'argument'],
    'history': ['war', 'civilization', 'ancient', 'modern', 'revolution', 'empire', 'king', 'queen',
                'president', 'democracy', 'government', 'treaty', 'battle', 'colonial', 'industrial',
                'renaissance', 'medieval', 'century', 'era', 'dynasty', 'independence', 'constitution',
                'amendment', 'civil', 'rights', 'movement', 'historical', 'archaeology'],
    'general': []
}

BLOCKED_TOPICS = [
    'hack', 'cheat', 'answers to test', 'do my homework', 'write my essay for me',
    'give me the answers', 'bypass', 'jailbreak', 'ignore instructions', 'ignore previous',
    'pretend you are', 'act as if', 'forget your rules', 'new instructions',
    'violence', 'weapons', 'drugs', 'alcohol', 'inappropriate', 'explicit',
    'dating', 'relationship advice', 'personal problems', 'gossip', 'celebrity',
    'gambling', 'betting', 'lottery', 'crypto trading', 'stock picks',
    'recipe', 'cooking', 'food', 'restaurant', 'movie review', 'game walkthrough',
    'sports scores', 'weather forecast', 'horoscope', 'zodiac'
]

EDUCATION_KEYWORDS = [
    'explain', 'help', 'understand', 'learn', 'study', 'homework', 'assignment',
    'practice', 'example', 'problem', 'question', 'answer', 'solve', 'how to',
    'what is', 'why', 'define', 'describe', 'compare', 'analyze', 'evaluate',
    'teach', 'tutor', 'class', 'lesson', 'topic', 'subject', 'concept'
]

# AI Provider Configuration
# Change this variable to switch between AI providers:
# "openai" - Use OpenAI GPT models
# "aws" - Use AWS-hosted custom models
# "local" - Use locally hosted models
AI_PROVIDER = "openai"  # Force OpenAI provider for this implementation

class AIService:
    """Individual AI Tutor - Self-optimizing AI that learns from each interaction"""
    
    def __init__(self):
        self.provider = AI_PROVIDER
        self.setup_provider()
    
    def setup_provider(self):
        """Initialize the appropriate AI provider"""
        if self.provider == "openai":
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key or api_key == "demo-key":
                print("OpenAI API key not configured, falling back to local provider")
                self.provider = "local"
                self.setup_local_provider()
                return
            
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=api_key)
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
    
    def _is_in_scope(self, subject, message, is_teacher=False):
        """
        Pre-OpenAI gate: Check if message is within subject scope.
        Returns (is_allowed: bool, blocked_reason: str | None)
        """
        message_lower = message.lower().strip()
        subject_lower = subject.lower() if subject else 'general'
        
        for blocked in BLOCKED_TOPICS:
            if blocked in message_lower:
                return False, f"This request is outside the scope of educational tutoring. I can only help with {subject} questions."
        
        if is_teacher:
            has_education_keyword = any(kw in message_lower for kw in EDUCATION_KEYWORDS)
            has_subject_keyword = any(kw in message_lower for kw in SUBJECT_KEYWORDS.get(subject_lower, []))
            if has_education_keyword or has_subject_keyword or 'student' in message_lower or 'class' in message_lower:
                return True, None
            if len(message_lower.split()) < 4:
                return True, None
            return False, "I can only assist with questions about your students, teaching strategies, and class performance."
        
        subject_keywords = SUBJECT_KEYWORDS.get(subject_lower, [])
        if subject_lower == 'mathematics':
            subject_keywords = SUBJECT_KEYWORDS.get('math', [])
        
        has_subject_keyword = any(kw in message_lower for kw in subject_keywords) if subject_keywords else False
        has_education_keyword = any(kw in message_lower for kw in EDUCATION_KEYWORDS)
        
        if has_subject_keyword or has_education_keyword:
            return True, None
        
        if len(message_lower.split()) <= 5:
            return True, None
        
        other_subjects = [s for s in SUBJECT_KEYWORDS.keys() if s != subject_lower and s != 'general']
        for other_subject in other_subjects:
            other_keywords = SUBJECT_KEYWORDS.get(other_subject, [])
            matches = sum(1 for kw in other_keywords if kw in message_lower)
            if matches >= 2:
                return False, f"I'm your {subject} tutor and can only help with {subject}. Please ask your teacher about {other_subject}."
        
        return True, None
    
    def retrieve_relevant_content(self, message, class_id, top_k=3):
        """
        RAG-lite: Retrieve relevant content snippets from class materials.
        Returns list of {source_name, snippet, score}
        """
        try:
            content_files = ContentFile.query.filter_by(class_id=class_id).all()
            if not content_files:
                return []
            
            message_words = set(re.findall(r'\b\w+\b', message.lower()))
            stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                         'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                         'should', 'may', 'might', 'can', 'to', 'of', 'in', 'for', 'on', 'with',
                         'at', 'by', 'from', 'as', 'into', 'through', 'during', 'before', 'after',
                         'above', 'below', 'between', 'under', 'again', 'further', 'then', 'once',
                         'here', 'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few',
                         'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
                         'own', 'same', 'so', 'than', 'too', 'very', 'just', 'and', 'but', 'if',
                         'or', 'because', 'until', 'while', 'this', 'that', 'these', 'those',
                         'what', 'which', 'who', 'whom', 'i', 'me', 'my', 'you', 'your', 'it'}
            message_keywords = message_words - stop_words
            
            if not message_keywords:
                return []
            
            scored_snippets = []
            
            for cf in content_files:
                file_text = self._extract_file_content(cf)
                if not file_text:
                    continue
                
                paragraphs = re.split(r'\n\s*\n|\n{2,}', file_text)
                if not paragraphs:
                    paragraphs = [file_text[:2000]]
                
                for para in paragraphs:
                    para = para.strip()
                    if len(para) < 50:
                        continue
                    
                    para_words = set(re.findall(r'\b\w+\b', para.lower()))
                    overlap = message_keywords & para_words
                    score = len(overlap) / max(len(message_keywords), 1)
                    
                    if score > 0:
                        snippet = para[:500] + ('...' if len(para) > 500 else '')
                        scored_snippets.append({
                            'source_name': cf.name,
                            'snippet': snippet,
                            'score': round(score, 3)
                        })
            
            scored_snippets.sort(key=lambda x: x['score'], reverse=True)
            return scored_snippets[:top_k]
            
        except Exception as e:
            print(f"Error retrieving content: {e}")
            return []
    
    def _extract_file_content(self, content_file):
        """Extract text content from a ContentFile"""
        try:
            file_path = content_file.file_path
            if not file_path or not os.path.exists(file_path):
                return None
            
            file_type = (content_file.file_type or '').lower()
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_type == 'pdf' or file_ext == '.pdf':
                try:
                    import pypdf
                    with open(file_path, 'rb') as f:
                        reader = pypdf.PdfReader(f)
                        text = ''
                        for page in reader.pages[:10]:
                            text += page.extract_text() or ''
                        return text[:10000]
                except ImportError:
                    try:
                        import pdfplumber
                        with pdfplumber.open(file_path) as pdf:
                            text = ''
                            for page in pdf.pages[:10]:
                                text += page.extract_text() or ''
                            return text[:10000]
                    except ImportError:
                        print("No PDF library available (pypdf or pdfplumber)")
                        return None
            
            elif file_type in ['txt', 'text'] or file_ext in ['.txt', '.md', '.text']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()[:10000]
            
            return None
            
        except Exception as e:
            print(f"Error extracting content from {content_file.name}: {e}")
            return None
    
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
            # Note: Don't claim visual learning without image support
            if 'auditory' in style:
                accommodations.append("Use clear verbal explanations with spoken examples")
            elif 'kinesthetic' in style:
                accommodations.append("Suggest hands-on activities and practical examples")
            elif 'reading' in style or 'writing' in style:
                accommodations.append("Provide detailed written explanations and examples")
            # Skip visual learning claims - no image support in current system
        
        return accommodations
    
    def generate_response(self, message, student_id, class_id, return_metadata=False):
        """Generate AI response based on student context and message
        
        If return_metadata=True, returns dict with response and metadata instead of just string.
        """
        try:
            class_obj = Class.query.get(class_id)
            if not class_obj:
                if return_metadata:
                    return {'response': "Class not found.", 'blocked': False, 'blocked_reason': None, 'subject': 'unknown'}
                return "Class not found."
            
            subject = class_obj.subject or 'general'
            
            is_allowed, blocked_reason = self._is_in_scope(subject, message, is_teacher=False)
            if not is_allowed:
                redirect_msg = blocked_reason or f"I can only help with {subject} questions. Please ask something related to {subject}."
                if return_metadata:
                    return {
                        'response': redirect_msg,
                        'blocked': True,
                        'blocked_reason': blocked_reason,
                        'subject': subject,
                        'strategy': None,
                        'difficulty': None
                    }
                return redirect_msg
            
            ai_model = class_obj.ai_model
            if not ai_model:
                ai_model = AIModel.query.filter_by(subject=class_obj.subject).first()
                if not ai_model:
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
            profile_summary = context.get('profile_summary', 'Student profile not available')
            recent_topics = context.get('recent_topics', [])
            accommodations = context.get('learning_accommodations', [])
            
            relevant_content = self.retrieve_relevant_content(message, class_id, top_k=3)
            content_section = ""
            if relevant_content:
                content_section = "\n\nRELEVANT CLASS MATERIAL:\n"
                for item in relevant_content:
                    content_section += f"[From {item['source_name']}]: {item['snippet'][:300]}...\n"
            
            strategy = self.choose_teaching_strategy(student_id, class_id)
            
            profile = OptimizedProfile.query.filter_by(user_id=student_id).first()
            difficulty = 'medium'
            if profile and profile.current_pass_rate:
                if profile.current_pass_rate >= 80:
                    difficulty = 'hard'
                elif profile.current_pass_rate < 60:
                    difficulty = 'easy'
            
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
{content_section}
LEARNING ACCOMMODATIONS:
{chr(10).join(f'- {acc}' for acc in accommodations) if accommodations else 'No specific accommodations'}

TEACHING STRATEGY: Use {strategy} approach at {difficulty} difficulty level.

Provide personalized {subject} help based on this student's learning style, current performance, and goals. Keep responses concise and educational."""
            
            prompt_tokens = self.count_tokens(system_prompt + message)
            
            if self.provider == "openai":
                ai_response = self._generate_openai_response(system_prompt, message, ai_model)
            elif self.provider == "aws":
                ai_response = self._generate_aws_response(system_prompt, message, ai_model)
            else:
                ai_response = self._generate_local_response(system_prompt, message, ai_model)
            
            # Count response tokens and update usage
            response_tokens = self.count_tokens(ai_response)
            total_tokens = prompt_tokens + response_tokens
            self.update_token_usage(student_id, total_tokens)
            
            # Store chat message and AI interaction
            self.store_interaction(
                user_id=student_id,
                class_id=class_id,
                ai_model_id=ai_model.id,
                message=message,
                response=ai_response,
                tokens_in=prompt_tokens,
                tokens_out=response_tokens,
                context_data=json.dumps(context)
            )
            
            try:
                chat_message = ChatMessage(
                    user_id=student_id,
                    class_id=class_id,
                    ai_model_id=ai_model.id if ai_model else 1,
                    message=message,
                    response=ai_response,
                    message_type='student',
                    context_data=json.dumps(context) if context else '{}'
                )
                db.session.add(chat_message)
                db.session.commit()
            except Exception as db_error:
                print(f"Database error saving chat: {db_error}")
                db.session.rollback()
            
            if return_metadata:
                return {
                    'response': ai_response,
                    'blocked': False,
                    'blocked_reason': None,
                    'subject': subject,
                    'strategy': strategy,
                    'difficulty': difficulty,
                    'tokens_used': total_tokens
                }
            return ai_response
            
        except Exception as e:
            print(f"Error generating AI response: {e}")
            import traceback
            traceback.print_exc()
            if return_metadata:
                return {'response': "Sorry, I encountered an error. Please try again.", 'blocked': False, 'blocked_reason': None, 'subject': 'unknown'}
            return "Sorry, I encountered an error. Please try again."
    
    def generate_teacher_response(self, message, teacher_id, class_id, return_metadata=False):
        """Generate AI response for teacher inquiries about students and teaching"""
        try:
            from models import Class, User
            
            class_obj = Class.query.get(class_id)
            if not class_obj:
                if return_metadata:
                    return {'response': "Class not found.", 'blocked': False, 'blocked_reason': None, 'subject': 'unknown'}
                return "Class not found."
            
            subject = class_obj.subject or 'general'
            
            is_allowed, blocked_reason = self._is_in_scope(subject, message, is_teacher=True)
            if not is_allowed:
                redirect_msg = blocked_reason or "I can only assist with questions about your students, teaching strategies, and class performance."
                if return_metadata:
                    return {'response': redirect_msg, 'blocked': True, 'blocked_reason': blocked_reason, 'subject': subject}
                return redirect_msg
            
            if not self.check_token_limit(teacher_id):
                if return_metadata:
                    return {'response': "Daily token limit reached. Please try again tomorrow.", 'blocked': False, 'blocked_reason': None, 'subject': subject}
                return "Daily token limit reached. Please try again tomorrow."
            
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
            insights_list = self.get_teacher_insights(teacher_id, class_id)
            insights_text = "No insights available"
            if insights_list and len(insights_list) > 0:
                insights_text = json.dumps(insights_list[0], indent=2)
            
            system_prompt = f"""You are an AI teaching assistant helping a teacher understand their students and improve their teaching methods.

CLASS INFORMATION:
Subject: {class_obj.subject}
Class: {class_obj.name}
Total Students: {len(students)}

STUDENT PROFILES:
{chr(10).join([f"- {s['name']}: {s['profile'][:200]}..." for s in student_profiles])}

CLASS INSIGHTS:
{insights_text}

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
            
            try:
                chat_message = ChatMessage(
                    user_id=teacher_id,
                    class_id=class_id,
                    ai_model_id=1,
                    message=message,
                    response=ai_response,
                    message_type='teacher',
                    context_data=json.dumps({
                        'student_count': len(students),
                        'subject': class_obj.subject,
                        'insights_available': bool(insights_list)
                    })
                )
                db.session.add(chat_message)
                db.session.commit()
            except Exception as db_error:
                print(f"Database error saving teacher chat: {db_error}")
                db.session.rollback()
            
            if return_metadata:
                return {
                    'response': ai_response,
                    'blocked': False,
                    'blocked_reason': None,
                    'subject': subject,
                    'tokens_used': total_tokens
                }
            return ai_response
            
        except Exception as e:
            print(f"Error generating teacher AI response: {e}")
            import traceback
            traceback.print_exc()
            if return_metadata:
                return {'response': "Sorry, I encountered an error. Please try again.", 'blocked': False, 'blocked_reason': None, 'subject': 'unknown'}
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
        """Get chat history for a user and class as JSON-safe dicts"""
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
    
    def store_interaction(self, user_id, class_id, ai_model_id, message, response, 
                         tokens_in, tokens_out, context_data=None, strategy_used=None):
        """Store detailed AI interaction for learning and optimization"""
        import time
        start_time = time.time()
        
        # Choose teaching strategy if not provided
        if not strategy_used:
            strategy_used = self.choose_teaching_strategy(user_id, class_id)
        
        # Calculate initial engagement (will be updated based on user response)
        engagement_score = self.calculate_engagement_score(message, response)
        
        interaction = AIInteraction(
            user_id=user_id,
            class_id=class_id,
            ai_model_id=ai_model_id,
            prompt=message,
            response=response,
            strategy_used=strategy_used,
            engagement_score=engagement_score,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            response_time_ms=int((time.time() - start_time) * 1000),
            temperature=0.7,
            context_data=context_data
        )
        
        db.session.add(interaction)
        db.session.commit()
        
        # Update optimized profile
        self.update_optimized_profile(user_id, class_id)
        
        return interaction
    
    def choose_teaching_strategy(self, user_id, class_id):
        """Choose the best teaching strategy based on student profile and history"""
        # Get optimized profile
        profile = OptimizedProfile.query.filter_by(user_id=user_id).first()
        
        if not profile:
            # Create initial profile
            profile = self.create_initial_profile(user_id)
        
        # Get preferred strategies from profile
        if profile.preferred_strategies:
            strategies = json.loads(profile.preferred_strategies)
            if strategies:
                return strategies[0]  # Use top strategy
        
        # Get failed strategies to avoid
        failed = FailedStrategy.query.filter_by(
            user_id=user_id,
            class_id=class_id
        ).order_by(FailedStrategy.failure_count.desc()).all()
        
        failed_names = [f.strategy_name for f in failed]
        
        # Available strategies
        all_strategies = [
            "socratic_method",
            "direct_instruction",
            "example_based",
            "problem_solving",
            "visual_learning",
            "storytelling",
            "gamification",
            "step_by_step",
            "collaborative",
            "inquiry_based"
        ]
        
        # Filter out failed strategies
        available = [s for s in all_strategies if s not in failed_names]
        
        if available:
            # Try a new strategy
            return available[0]
        else:
            # All strategies have failed, retry the least failed one
            if failed:
                return failed[-1].strategy_name
            return "direct_instruction"  # Default
    
    def calculate_engagement_score(self, message, response):
        """Calculate engagement score based on interaction quality"""
        # Simple heuristics for engagement
        score = 0.5  # Base score
        
        # Longer messages indicate more engagement
        if len(message) > 100:
            score += 0.2
        elif len(message) > 50:
            score += 0.1
        
        # Questions indicate engagement
        if '?' in message:
            score += 0.1
        
        # Multiple sentences indicate thoughtful interaction
        if message.count('.') > 1:
            score += 0.1
        
        # Cap at 1.0
        return min(1.0, score)
    
    def create_initial_profile(self, user_id):
        """Create initial optimized profile for a student"""
        student = User.query.get(user_id)
        if not student:
            return None
        
        profile = OptimizedProfile(
            user_id=user_id,
            current_pass_rate=student.get_average_grade() or 0,
            predicted_pass_rate=student.get_average_grade() or 50,
            engagement_level=0.5,
            mastery_scores=json.dumps({}),
            preferred_strategies=json.dumps(["direct_instruction", "example_based"]),
            avoided_strategies=json.dumps([])
        )
        
        db.session.add(profile)
        db.session.commit()
        return profile
    
    def update_optimized_profile(self, user_id, class_id):
        """Update optimized profile based on recent interactions"""
        profile = OptimizedProfile.query.filter_by(user_id=user_id).first()
        
        if not profile:
            profile = self.create_initial_profile(user_id)
        
        # Get recent interactions
        recent = AIInteraction.query.filter_by(
            user_id=user_id,
            class_id=class_id
        ).order_by(AIInteraction.created_at.desc()).limit(10).all()
        
        if recent:
            # Calculate average engagement
            avg_engagement = sum([i.engagement_score or 0 for i in recent]) / len(recent)
            profile.engagement_level = avg_engagement
            
            # Update recent topics
            topics = list(set([i.prompt[:30] for i in recent[:5]]))
            profile.recent_topics = json.dumps(topics)
            
            # Find successful strategies
            successful = [i for i in recent if i.success_indicator]
            if successful:
                strategies = list(set([i.strategy_used for i in successful if i.strategy_used]))
                profile.preferred_strategies = json.dumps(strategies)
        
        # Update pass rate
        student = User.query.get(user_id)
        if student:
            profile.current_pass_rate = student.get_class_average(class_id) or 0
        
        profile.last_updated = datetime.utcnow()
        db.session.commit()
    
    def log_failed_strategy(self, user_id, class_id, strategy_name, reason=None):
        """Log a strategy that didn't work for a student"""
        # Check if already logged
        failed = FailedStrategy.query.filter_by(
            user_id=user_id,
            class_id=class_id,
            strategy_name=strategy_name
        ).first()
        
        if failed:
            failed.failure_count += 1
            failed.last_attempted = datetime.utcnow()
        else:
            failed = FailedStrategy(
                user_id=user_id,
                class_id=class_id,
                strategy_name=strategy_name,
                failure_reason=reason,
                failure_count=1
            )
            db.session.add(failed)
        
        db.session.commit()
        
        # Update optimized profile to avoid this strategy
        profile = OptimizedProfile.query.filter_by(user_id=user_id).first()
        if profile:
            avoided = json.loads(profile.avoided_strategies) if profile.avoided_strategies else []
            if strategy_name not in avoided:
                avoided.append(strategy_name)
                profile.avoided_strategies = json.dumps(avoided)
                db.session.commit()
    
    def generate_mini_test(self, user_id, class_id, test_type="diagnostic"):
        """Generate adaptive mini-test for student assessment"""
        try:
            # Get student profile
            profile = OptimizedProfile.query.filter_by(user_id=user_id).first()
            class_obj = Class.query.get(class_id)
            
            # Determine difficulty based on performance
            if profile and profile.current_pass_rate:
                if profile.current_pass_rate > 80:
                    difficulty = "hard"
                elif profile.current_pass_rate > 60:
                    difficulty = "medium"
                else:
                    difficulty = "easy"
            else:
                difficulty = "medium"
            
            # Get AI model for this class
            ai_model = class_obj.ai_model or AIModel.query.filter_by(subject=class_obj.subject).first()
            
            # Generate questions based on subject
            questions = self._generate_test_questions(class_obj.subject, difficulty, test_type)
            
            # Create mini-test
            test = MiniTest(
                class_id=class_id,
                created_by_ai=ai_model.id if ai_model else 1,
                test_type=test_type,
                difficulty_level=difficulty,
                skills_tested=json.dumps([class_obj.subject]),
                questions=json.dumps(questions)
            )
            
            db.session.add(test)
            db.session.commit()
            
            return test
            
        except Exception as e:
            print(f"Error generating mini-test: {e}")
            return None
    
    def _generate_test_questions(self, subject, difficulty, test_type, num_questions=3):
        """Generate test questions using AI based on parameters"""
        try:
            # Check if OpenAI client is available
            if self.provider != "openai" or not hasattr(self, 'client'):
                # Fallback for non-OpenAI providers or when client is not initialized
                return self._generate_fallback_questions(subject, difficulty, test_type)
            
            # Use AI to generate questions
            prompt = f"""Generate {num_questions} {difficulty} level {subject} questions for a {test_type}.

Requirements:
- Create clear, educational questions appropriate for {difficulty} difficulty
- For multiple choice: provide 4 options with one correct answer
- For open-ended: create thought-provoking questions
- Focus on testing understanding, not memorization

Return ONLY a JSON array in this exact format:
[
  {{
    "question": "Question text here",
    "type": "multiple_choice",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct": "Option A",
    "explanation": "Brief explanation"
  }}
]"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert educational assessment creator. Generate only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            # Parse AI response as JSON
            import json
            questions_text = response.choices[0].message.content.strip()
            
            # Extract JSON if wrapped in markdown code blocks
            if "```json" in questions_text:
                questions_text = questions_text.split("```json")[1].split("```")[0].strip()
            elif "```" in questions_text:
                questions_text = questions_text.split("```")[1].split("```")[0].strip()
            
            questions = json.loads(questions_text)
            return questions
            
        except Exception as e:
            print(f"Error generating AI questions: {e}")
            # Fallback to simple questions
            return self._generate_fallback_questions(subject, difficulty, test_type)
    
    def _generate_fallback_questions(self, subject, difficulty, test_type):
        """Fallback questions when AI generation fails"""
        if test_type == "diagnostic":
            return [
                {
                    "question": f"Describe your current understanding of {subject}",
                    "type": "open_ended"
                },
                {
                    "question": f"What topics in {subject} do you find most challenging?",
                    "type": "open_ended"
                }
            ]
        else:
            return [
                {
                    "question": f"This is a {difficulty} {subject} assessment question",
                    "type": "multiple_choice",
                    "options": ["Answer A", "Answer B", "Answer C", "Answer D"],
                    "correct": "Answer A"
                }
            ]
    
    def get_predicted_pass_rate(self, user_id, class_id):
        """Get AI-predicted pass rate for a student in a class"""
        prediction = PredictedGrade.query.filter_by(
            user_id=user_id,
            class_id=class_id
        ).order_by(PredictedGrade.prediction_date.desc()).first()
        
        if prediction:
            return {
                'current': prediction.current_trajectory,
                'predicted': prediction.predicted_final_grade,
                'confidence': prediction.confidence_level,
                'factors': json.loads(prediction.factors_analyzed) if prediction.factors_analyzed else {}
            }
        
        # Return default if no prediction
        student = User.query.get(user_id)
        if student:
            current = student.get_class_average(class_id) or 0
            return {
                'current': current,
                'predicted': current,  # Same as current if no prediction
                'confidence': 0.5,
                'factors': {}
            }
        
        return None