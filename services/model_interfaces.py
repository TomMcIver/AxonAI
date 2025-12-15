"""
Model Interfaces for AxonAI Demo
Swappable AI model components for different providers
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import os
from openai import OpenAI


class BaseTutorModel(ABC):
    """Interface for AI Tutor models"""
    
    @abstractmethod
    def generate_response(self, prompt: str, context: Dict[str, Any]) -> str:
        """Generate a tutoring response"""
        pass


class BaseQuizModel(ABC):
    """Interface for Quiz generation models"""
    
    @abstractmethod
    def generate_quiz(self, subject: str, difficulty: str, num_questions: int) -> List[Dict]:
        """Generate quiz questions"""
        pass


class BaseGraderModel(ABC):
    """Interface for grading models"""
    
    @abstractmethod
    def grade_response(self, question: str, answer: str, correct_answer: str) -> Dict[str, Any]:
        """Grade a student response"""
        pass


class BaseMasteryModel(ABC):
    """Interface for mastery tracking models"""
    
    @abstractmethod
    def calculate_mastery(self, interactions: List[Dict], current_mastery: Dict) -> Dict:
        """Calculate updated mastery levels"""
        pass


class BaseProfileModel(ABC):
    """Interface for profile summarization models"""
    
    @abstractmethod
    def summarize_profile(self, student_data: Dict, interactions: List[Dict]) -> str:
        """Generate a profile summary for AI context"""
        pass


class GPTTutorModel(BaseTutorModel):
    """OpenAI GPT implementation of tutor model"""
    
    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    def generate_response(self, prompt: str, context: Dict[str, Any]) -> str:
        student_profile = context.get('profile_summary', '')
        subject = context.get('subject', 'general')
        
        system_prompt = f"""You are an adaptive AI tutor for {subject}. 
Student Profile: {student_profile}
Provide clear, encouraging explanations tailored to this student's learning style."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"I'm having trouble responding right now. Error: {str(e)}"


class GPTProfileModel(BaseProfileModel):
    """OpenAI GPT implementation of profile summarizer"""
    
    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    def summarize_profile(self, student_data: Dict, interactions: List[Dict]) -> str:
        name = student_data.get('name', 'Student')
        learning_style = student_data.get('learning_style', 'unknown')
        year_level = student_data.get('year_level', 'unknown')
        interests = student_data.get('interests', [])
        mastery = student_data.get('mastery', {})
        
        recent_topics = []
        for i in interactions[-5:]:
            if 'prompt' in i:
                recent_topics.append(i['prompt'][:50])
        
        summary = f"""Student: {name}
Year Level: {year_level}
Learning Style: {learning_style}
Interests: {', '.join(interests[:3]) if interests else 'not specified'}
Mastery Levels: {', '.join([f"{k}: {v:.0f}%" for k, v in mastery.items()]) if mastery else 'no data yet'}
Recent Topics: {', '.join(recent_topics) if recent_topics else 'none'}"""
        
        return summary


class SimpleMasteryModel(BaseMasteryModel):
    """Simple mastery calculation (no AI needed)"""
    
    def calculate_mastery(self, interactions: List[Dict], current_mastery: Dict) -> Dict:
        new_mastery = current_mastery.copy() if current_mastery else {}
        
        for interaction in interactions:
            skill = interaction.get('skill', 'general')
            score = interaction.get('score', 50)
            
            if skill in new_mastery:
                new_mastery[skill] = new_mastery[skill] * 0.7 + score * 0.3
            else:
                new_mastery[skill] = score
        
        return new_mastery


def get_tutor_model(provider: str = "openai") -> BaseTutorModel:
    """Factory function to get tutor model by provider"""
    if provider == "openai":
        return GPTTutorModel()
    else:
        return GPTTutorModel()


def get_profile_model(provider: str = "openai") -> BaseProfileModel:
    """Factory function to get profile model by provider"""
    if provider == "openai":
        return GPTProfileModel()
    else:
        return GPTProfileModel()


def get_mastery_model() -> BaseMasteryModel:
    """Factory function to get mastery model"""
    return SimpleMasteryModel()
