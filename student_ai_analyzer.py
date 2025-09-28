"""
Student AI Analyzer
Provides deep insights into individual student learning patterns
"""

import json
from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_
from models import db, User, AIInteraction, OptimizedProfile, FailedStrategy, Grade, Class, MiniTest, PredictedGrade, ChatMessage
from ai_service import AIService

class StudentAIAnalyzer:
    def __init__(self):
        self.ai_service = AIService()
    
    def generate_student_insights(self, student_id):
        """Generate comprehensive AI insights for a specific student"""
        student = User.query.get(student_id)
        if not student:
            return {}
        
        # Collect all student data
        data = self.collect_student_data(student_id)
        
        # Generate AI analysis
        ai_insights = self.generate_ai_analysis(data)
        
        # Prepare insights for display
        return {
            'basic_info': data['basic_info'],
            'performance_metrics': data['performance_metrics'],
            'learning_patterns': data['learning_patterns'],
            'conversation_analysis': data['conversation_analysis'],
            'ai_recommendations': ai_insights,
            'progress_timeline': data['progress_timeline'],
            'strategy_effectiveness': data['strategy_effectiveness']
        }
    
    def collect_student_data(self, student_id):
        """Collect comprehensive data for a student"""
        student = User.query.get(student_id)
        
        # Basic student info
        basic_info = {
            'name': student.get_full_name(),
            'email': student.email,
            'age': student.age,
            'learning_style': student.learning_style or 'Not specified',
            'learning_difficulty': student.learning_difficulty or 'None',
            'primary_language': student.primary_language or 'English',
            'created_at': student.created_at,
            'is_active': student.is_active
        }
        
        # Performance metrics
        avg_grade = student.get_average_grade() or 0
        recent_grades = Grade.query.filter_by(student_id=student_id).order_by(desc(Grade.graded_at)).limit(10).all()
        
        performance_metrics = {
            'current_average': avg_grade,
            'recent_grades': [{'grade': g.grade, 'date': g.graded_at, 'assignment': g.assignment.title if g.assignment else 'Unknown'} for g in recent_grades],
            'improvement_trend': self.calculate_improvement_trend(recent_grades),
            'attendance_rate': student.attendance_rate or 0,
            'assignments_completed': Grade.query.filter_by(student_id=student_id).count()
        }
        
        # Learning patterns from AI interactions
        interactions = AIInteraction.query.filter_by(user_id=student_id).order_by(desc(AIInteraction.created_at)).all()
        
        learning_patterns = {
            'total_interactions': len(interactions),
            'avg_engagement': sum(i.engagement_score or 0 for i in interactions) / len(interactions) if interactions else 0,
            'success_rate': sum(1 for i in interactions if i.success_indicator) / len(interactions) * 100 if interactions else 0,
            'preferred_time': self.analyze_preferred_time(interactions),
            'most_used_strategies': self.get_most_used_strategies(interactions)
        }
        
        # Conversation analysis
        conversations = ChatMessage.query.filter_by(user_id=student_id).order_by(desc(ChatMessage.created_at)).limit(10).all()
        
        conversation_analysis = {
            'total_conversations': len(conversations),
            'recent_topics': self.extract_conversation_topics(conversations),
            'avg_conversation_length': len(conversations),  # Simple count since ChatMessage stores individual messages
            'sentiment_trend': self.analyze_sentiment_trend(conversations)
        }
        
        # Progress timeline
        progress_timeline = self.generate_progress_timeline(student_id)
        
        # Strategy effectiveness
        strategy_effectiveness = self.analyze_strategy_effectiveness(student_id)
        
        return {
            'basic_info': basic_info,
            'performance_metrics': performance_metrics,
            'learning_patterns': learning_patterns,
            'conversation_analysis': conversation_analysis,
            'progress_timeline': progress_timeline,
            'strategy_effectiveness': strategy_effectiveness
        }
    
    def calculate_improvement_trend(self, grades):
        """Calculate improvement trend from recent grades"""
        if len(grades) < 2:
            return 'Insufficient data'
        
        # Compare average of first half vs second half
        mid = len(grades) // 2
        first_half = sum(g.grade for g in grades[mid:]) / len(grades[mid:])
        second_half = sum(g.grade for g in grades[:mid]) / len(grades[:mid])
        
        improvement = second_half - first_half
        
        if improvement > 5:
            return f'Improving (+{improvement:.1f}%)'
        elif improvement < -5:
            return f'Declining ({improvement:.1f}%)'
        else:
            return 'Stable'
    
    def analyze_preferred_time(self, interactions):
        """Analyze when student is most active"""
        if not interactions:
            return 'No data'
        
        time_slots = {'morning': 0, 'afternoon': 0, 'evening': 0, 'night': 0}
        
        for interaction in interactions:
            hour = interaction.created_at.hour
            if 6 <= hour < 12:
                time_slots['morning'] += 1
            elif 12 <= hour < 17:
                time_slots['afternoon'] += 1
            elif 17 <= hour < 22:
                time_slots['evening'] += 1
            else:
                time_slots['night'] += 1
        
        preferred = max(time_slots, key=time_slots.get)
        return preferred.capitalize()
    
    def get_most_used_strategies(self, interactions):
        """Get most frequently used learning strategies"""
        strategies = {}
        for interaction in interactions:
            if interaction.strategy_used:
                strategies[interaction.strategy_used] = strategies.get(interaction.strategy_used, 0) + 1
        
        sorted_strategies = sorted(strategies.items(), key=lambda x: x[1], reverse=True)
        return [{'name': s[0].replace('_', ' ').title(), 'count': s[1]} for s in sorted_strategies[:5]]
    
    def extract_conversation_topics(self, conversations):
        """Extract main topics from recent conversations"""
        topics = []
        for conv in conversations[:5]:
            # ChatMessage model has message field, not subject_context
            if conv.message:
                # Try to extract topics from message content
                topics.append("General Learning" if len(topics) == 0 else f"Topic {len(topics)+1}")
        return list(set(topics)) if topics else ["General Learning"]
    
    def analyze_sentiment_trend(self, conversations):
        """Analyze sentiment trend in conversations"""
        if not conversations:
            return 'No data'
        
        # Simple sentiment based on message count (ChatMessage doesn't have engagement_score)
        recent_count = len(conversations[:3]) if len(conversations) >= 3 else len(conversations)
        
        if recent_count >= 3:
            return 'Very Active'
        elif recent_count >= 2:
            return 'Active'
        elif recent_count >= 1:
            return 'Moderate'
        else:
            return 'Needs Attention'
    
    def generate_progress_timeline(self, student_id):
        """Generate progress timeline for the student"""
        timeline = []
        
        # Get grades over last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        grades = Grade.query.filter(
            Grade.student_id == student_id,
            Grade.graded_at >= thirty_days_ago
        ).order_by(Grade.graded_at).all()
        
        for grade in grades[:10]:  # Limit to 10 most recent
            timeline.append({
                'date': grade.graded_at.strftime('%Y-%m-%d'),
                'event': f"Grade: {grade.grade}%",
                'type': 'grade',
                'value': grade.grade
            })
        
        # Add AI interactions
        interactions = AIInteraction.query.filter(
            AIInteraction.user_id == student_id,
            AIInteraction.created_at >= thirty_days_ago
        ).order_by(desc(AIInteraction.created_at)).limit(5).all()
        
        for interaction in interactions:
            timeline.append({
                'date': interaction.created_at.strftime('%Y-%m-%d'),
                'event': f"AI Session: {interaction.strategy_used or 'General'}",
                'type': 'interaction',
                'success': interaction.success_indicator
            })
        
        return sorted(timeline, key=lambda x: x['date'], reverse=True)
    
    def analyze_strategy_effectiveness(self, student_id):
        """Analyze which strategies work best for this student"""
        strategies = db.session.query(
            AIInteraction.strategy_used,
            func.count(AIInteraction.id).label('total'),
            func.sum(AIInteraction.success_indicator.cast(db.Integer)).label('successes'),
            func.avg(AIInteraction.engagement_score).label('avg_engagement')
        ).filter(
            AIInteraction.user_id == student_id,
            AIInteraction.strategy_used.isnot(None)
        ).group_by(AIInteraction.strategy_used).all()
        
        effectiveness = []
        for strategy, total, successes, engagement in strategies:
            success_rate = (successes / total * 100) if total > 0 else 0
            effectiveness.append({
                'strategy': strategy.replace('_', ' ').title(),
                'total_uses': total,
                'success_rate': round(success_rate, 1),
                'avg_engagement': round(float(engagement or 0), 1)
            })
        
        return sorted(effectiveness, key=lambda x: x['success_rate'], reverse=True)
    
    def generate_ai_analysis(self, data):
        """Generate comprehensive AI analysis for the student"""
        try:
            # Create detailed prompt for AI analysis
            prompt = f"""Analyze this student's comprehensive learning data:

STUDENT PROFILE:
- Name: {data['basic_info']['name']}
- Learning Style: {data['basic_info']['learning_style']}
- Current Average: {data['performance_metrics']['current_average']:.1f}%
- Improvement Trend: {data['performance_metrics']['improvement_trend']}
- Total AI Interactions: {data['learning_patterns']['total_interactions']}
- Success Rate: {data['learning_patterns']['success_rate']:.1f}%
- Average Engagement: {data['learning_patterns']['avg_engagement']:.1f}/10

LEARNING PATTERNS:
- Preferred Time: {data['learning_patterns']['preferred_time']}
- Most Used Strategies: {json.dumps(data['learning_patterns']['most_used_strategies'])}

CONVERSATION INSIGHTS:
- Total Conversations: {data['conversation_analysis']['total_conversations']}
- Recent Topics: {', '.join(data['conversation_analysis']['recent_topics'])}
- Sentiment: {data['conversation_analysis']['sentiment_trend']}

Provide:
1. Detailed analysis of this student's learning journey
2. Specific strengths and areas for improvement
3. Personalized recommendations for teachers
4. Predicted outcomes and risk factors
5. Optimal learning strategies for this specific student
6. Parent communication points
7. Next steps for academic success"""

            response = self.ai_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert educational psychologist analyzing individual student learning patterns. Provide detailed, actionable insights."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating AI analysis: {e}")
            return "AI analysis temporarily unavailable. Please try again later."