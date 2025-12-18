"""
Interaction simulator for generating realistic learning data.
Simulates student interactions with the AI tutor.
"""

import random
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from skill_taxonomy import TEACHING_STRATEGIES, SKILL_TAXONOMY


class InteractionSimulator:
    """Simulate realistic student-tutor interactions."""
    
    QUESTION_TEMPLATES = {
        'math': [
            "How do I solve {topic} problems?",
            "I don't understand {topic}",
            "Can you help me with {topic}?",
            "What's the formula for {topic}?",
            "I'm stuck on this {topic} problem",
            "Why does {topic} work this way?",
            "Can you explain {topic} step by step?",
            "I keep getting {topic} wrong"
        ],
        'science': [
            "What is {topic}?",
            "How does {topic} work?",
            "Can you explain {topic}?",
            "Why is {topic} important?"
        ]
    }
    
    RESPONSE_TEMPLATES = {
        'correct': [
            "I think I understand now!",
            "Oh, that makes sense!",
            "Got it, thanks!",
            "Yes, I see how that works",
            "That's clearer now"
        ],
        'confused': [
            "I'm still confused",
            "I don't get it",
            "Can you explain differently?",
            "What do you mean?",
            "I need more help"
        ],
        'asking_more': [
            "What about {follow_up}?",
            "How does this relate to {follow_up}?",
            "Can we try another example?",
            "Is there a simpler way?"
        ]
    }
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize interaction simulator."""
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
    
    def simulate_session(self, student: Dict, skill: str,
                         strategy: str, n_interactions: int = 5,
                         start_time: Optional[datetime] = None) -> List[Dict]:
        """
        Simulate a learning session.
        
        Args:
            student: Student data with latent_traits
            skill: Skill being practiced
            strategy: Teaching strategy used
            n_interactions: Number of interactions in session
            start_time: Session start time
            
        Returns:
            List of interaction dictionaries
        """
        if start_time is None:
            start_time = datetime.utcnow() - timedelta(days=random.randint(0, 30))
        
        traits = student.get('latent_traits', {})
        baseline = traits.get('baseline_ability', 0.5)
        engagement_base = traits.get('engagement_tendency', 0.5)
        strategy_boost = traits.get('strategy_sensitivities', {}).get(strategy, 0)
        skill_mod = traits.get('skill_strengths', {}).get(skill, 0)
        skill_mod += traits.get('skill_weaknesses', {}).get(skill, 0)
        
        current_ability = baseline + skill_mod
        current_time = start_time
        
        interactions = []
        
        for i in range(n_interactions):
            time_delta = timedelta(seconds=random.randint(30, 300))
            current_time += time_delta
            
            engagement = np.clip(
                engagement_base + random.uniform(-0.2, 0.2) + strategy_boost * 0.5,
                0.2, 1.0
            )
            
            difficulty = self._get_difficulty(current_ability)
            
            success_prob = current_ability + strategy_boost * 0.3 + random.uniform(-0.1, 0.1)
            success = random.random() < success_prob
            
            prompt = self._generate_prompt(skill, i, success, traits)
            response = self._generate_response(skill, strategy, success)
            
            if success:
                learning_gain = traits.get('learning_rate', 0.05) * (1 + strategy_boost)
                current_ability = min(current_ability + learning_gain, 0.95)
            
            interaction = {
                'created_at': current_time,
                'sub_topic': skill,
                'strategy_used': strategy,
                'prompt': prompt,
                'response': response,
                'success_indicator': success,
                'engagement_score': float(engagement),
                'response_time_ms': random.randint(500, 5000),
                'context_data': json.dumps({
                    'difficulty': difficulty,
                    'session_index': i
                })
            }
            
            interactions.append(interaction)
        
        return interactions
    
    def _get_difficulty(self, ability: float) -> str:
        """Determine difficulty level based on ability."""
        if ability > 0.7:
            return random.choices(['medium', 'hard'], weights=[0.3, 0.7])[0]
        elif ability < 0.4:
            return random.choices(['easy', 'medium'], weights=[0.7, 0.3])[0]
        else:
            return random.choices(['easy', 'medium', 'hard'], weights=[0.2, 0.6, 0.2])[0]
    
    def _generate_prompt(self, skill: str, index: int, 
                         previous_success: bool, traits: Dict) -> str:
        """Generate a student prompt."""
        if index == 0:
            templates = self.QUESTION_TEMPLATES.get('math', ["Help me with {topic}"])
            template = random.choice(templates)
            return template.format(topic=skill)
        
        if previous_success:
            if random.random() < 0.7:
                return random.choice(self.RESPONSE_TEMPLATES['correct'])
            else:
                return random.choice(self.RESPONSE_TEMPLATES['asking_more']).format(
                    follow_up=skill
                )
        else:
            if random.random() < traits.get('help_seeking', 0.5):
                return random.choice(self.RESPONSE_TEMPLATES['confused'])
            else:
                return random.choice(self.RESPONSE_TEMPLATES['asking_more']).format(
                    follow_up='this'
                )
    
    def _generate_response(self, skill: str, strategy: str, 
                           success: bool) -> str:
        """Generate a tutor response."""
        if success:
            return f"Great job understanding {skill}! Let's try another example."
        else:
            return f"Let me explain {skill} using a {strategy.replace('_', ' ')} approach."
    
    def simulate_quiz(self, student: Dict, skills: List[str],
                      n_questions: int = 5,
                      test_time: Optional[datetime] = None) -> Dict:
        """
        Simulate a quiz/mini-test.
        
        Args:
            student: Student data with latent_traits
            skills: Skills being tested
            n_questions: Number of questions
            test_time: Time of test
            
        Returns:
            Quiz response dictionary
        """
        if test_time is None:
            test_time = datetime.utcnow()
        
        traits = student.get('latent_traits', {})
        baseline = traits.get('baseline_ability', 0.5)
        consistency = traits.get('consistency', 0.7)
        
        answers = []
        correct = 0
        skill_scores = {}
        
        for skill in skills:
            skill_mod = traits.get('skill_strengths', {}).get(skill, 0)
            skill_mod += traits.get('skill_weaknesses', {}).get(skill, 0)
            
            effective_ability = baseline + skill_mod + random.uniform(-0.1, 0.1) * (1 - consistency)
            is_correct = random.random() < effective_ability
            
            answers.append({
                'skill': skill,
                'correct': is_correct,
                'time_seconds': random.randint(20, 120)
            })
            
            if is_correct:
                correct += 1
            
            if skill not in skill_scores:
                skill_scores[skill] = {'correct': 0, 'total': 0}
            skill_scores[skill]['total'] += 1
            if is_correct:
                skill_scores[skill]['correct'] += 1
        
        for skill in skill_scores:
            s = skill_scores[skill]
            skill_scores[skill] = s['correct'] / s['total'] if s['total'] > 0 else 0
        
        return {
            'completed_at': test_time,
            'created_at': test_time - timedelta(minutes=n_questions * 2),
            'answers': json.dumps(answers),
            'score': correct / n_questions,
            'time_taken': sum(a['time_seconds'] for a in answers),
            'skill_scores': json.dumps(skill_scores),
            'skills_tested': json.dumps(skills)
        }
    
    def simulate_improvement_curve(self, student: Dict, skill: str,
                                    n_sessions: int = 10,
                                    start_date: Optional[datetime] = None) -> List[Dict]:
        """
        Simulate an improvement curve over multiple sessions.
        
        Args:
            student: Student data
            skill: Skill being practiced
            n_sessions: Number of sessions
            start_date: Starting date
            
        Returns:
            List of session summaries
        """
        if start_date is None:
            start_date = datetime.utcnow() - timedelta(days=n_sessions * 3)
        
        traits = student.get('latent_traits', {})
        learning_rate = traits.get('learning_rate', 0.05)
        baseline = traits.get('baseline_ability', 0.5)
        skill_mod = traits.get('skill_strengths', {}).get(skill, 0)
        skill_mod += traits.get('skill_weaknesses', {}).get(skill, 0)
        
        current_mastery = baseline + skill_mod
        sessions = []
        current_time = start_date
        
        for i in range(n_sessions):
            days_gap = random.randint(1, 5)
            current_time += timedelta(days=days_gap)
            
            strategy = random.choice(TEACHING_STRATEGIES)
            strategy_boost = traits.get('strategy_sensitivities', {}).get(strategy, 0)
            
            n_interactions = random.randint(3, 8)
            
            gain = learning_rate * n_interactions * (1 + strategy_boost)
            noise = random.uniform(-0.02, 0.02) * (1 - traits.get('consistency', 0.7))
            current_mastery = min(0.95, max(0.1, current_mastery + gain + noise))
            
            sessions.append({
                'date': current_time,
                'skill': skill,
                'strategy': strategy,
                'n_interactions': n_interactions,
                'mastery_after': float(current_mastery),
                'engagement': traits.get('engagement_tendency', 0.5) + random.uniform(-0.1, 0.1)
            })
        
        return sessions
    
    def simulate_plateau(self, student: Dict, skill: str,
                         plateau_start: int = 5,
                         n_sessions: int = 10) -> List[Dict]:
        """Simulate a learning plateau pattern."""
        sessions = self.simulate_improvement_curve(student, skill, n_sessions)
        
        plateau_level = sessions[min(plateau_start, len(sessions)-1)]['mastery_after']
        
        for i in range(plateau_start, len(sessions)):
            sessions[i]['mastery_after'] = plateau_level + random.uniform(-0.03, 0.03)
        
        return sessions
    
    def simulate_regression(self, student: Dict, skill: str,
                            regression_start: int = 7,
                            n_sessions: int = 10) -> List[Dict]:
        """Simulate a regression pattern (decline in mastery)."""
        sessions = self.simulate_improvement_curve(student, skill, n_sessions)
        
        for i in range(regression_start, len(sessions)):
            decay = 0.02 * (i - regression_start + 1)
            sessions[i]['mastery_after'] = max(0.2, sessions[i]['mastery_after'] - decay)
        
        return sessions
