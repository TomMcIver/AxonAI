"""
Bulk Interaction Generator
Generates 1000 realistic AI tutor interactions across multiple math sub-topics
Distributes them over time (45-60 days) for realistic progression visualization
"""
import random
from datetime import datetime, timedelta
from app import app, db
from models import User, Class, AIInteraction, AIModel

# Math sub-topics with difficulty progression
SUB_TOPICS = {
    'algebra': {
        'topics': [
            'basic equations', 'linear equations', 'quadratic equations',
            'polynomials', 'factoring', 'systems of equations',
            'inequalities', 'functions', 'exponential functions'
        ],
        'difficulty_range': (0.3, 0.9)
    },
    'statistics': {
        'topics': [
            'mean and median', 'mode and range', 'probability basics',
            'data visualization', 'normal distribution', 'standard deviation',
            'hypothesis testing', 'correlation', 'regression analysis'
        ],
        'difficulty_range': (0.4, 0.85)
    },
    'calculus': {
        'topics': [
            'limits', 'basic derivatives', 'derivative rules',
            'chain rule', 'integration basics', 'definite integrals',
            'applications of derivatives', 'optimization', 'related rates'
        ],
        'difficulty_range': (0.5, 0.95)
    }
}

# Student learning profiles
STUDENT_PROFILES = {
    'Alex': {
        'base_engagement': 0.85,
        'success_rate': 0.80,
        'learning_speed': 'fast',  # moves through topics quickly
        'strong_in': ['algebra', 'calculus'],
        'weak_in': ['statistics']
    },
    'Jordan': {
        'base_engagement': 0.70,
        'success_rate': 0.65,
        'learning_speed': 'medium',
        'strong_in': ['statistics'],
        'weak_in': ['calculus']
    },
    'Taylor': {
        'base_engagement': 0.55,
        'success_rate': 0.50,
        'learning_speed': 'slow',  # needs more repetition
        'strong_in': [],
        'weak_in': ['algebra', 'calculus', 'statistics']
    }
}

# Teaching strategies
STRATEGIES = [
    'direct_instruction',
    'socratic_questioning',
    'worked_examples',
    'visual_demonstrations',
    'real_world_applications',
    'scaffolding',
    'conceptual_understanding',
    'practice_problems'
]

def generate_prompt(sub_topic, topic, difficulty):
    """Generate a realistic student prompt for the topic"""
    prompts = {
        'algebra': [
            f"Can you help me solve this {topic} problem?",
            f"I'm confused about {topic}. Can you explain it?",
            f"How do I approach {topic}?",
            f"What's the best way to solve {topic} problems?",
            f"Can you walk me through {topic} step by step?"
        ],
        'statistics': [
            f"What is {topic} and why is it important?",
            f"Can you explain {topic} with an example?",
            f"I don't understand {topic}. Can you help?",
            f"How do I calculate {topic}?",
            f"What's the difference between {topic} and other concepts?"
        ],
        'calculus': [
            f"I'm struggling with {topic}. Can you explain?",
            f"How do I find {topic} in this problem?",
            f"What are the rules for {topic}?",
            f"Can you show me how to apply {topic}?",
            f"Why do we use {topic}?"
        ]
    }
    return random.choice(prompts[sub_topic])

def generate_response(sub_topic, topic, difficulty):
    """Generate a realistic AI tutor response"""
    responses = {
        'algebra': f"Let me help you understand {topic}. We'll start with the basics and build up from there...",
        'statistics': f"Great question about {topic}! This concept is fundamental to understanding data...",
        'calculus': f"I can see why {topic} might be confusing. Let's break it down step by step..."
    }
    base_response = responses[sub_topic]
    
    # Add more detail for higher difficulty
    if difficulty > 0.7:
        base_response += " This is an advanced concept that builds on what we learned earlier."
    
    return base_response

def calculate_engagement(student_profile, sub_topic, attempt_number):
    """Calculate engagement score based on student profile and progress"""
    base = student_profile['base_engagement']
    
    # Adjust for strong/weak areas
    if sub_topic in student_profile.get('strong_in', []):
        base += 0.1
    elif sub_topic in student_profile.get('weak_in', []):
        base -= 0.15
    
    # Add some randomness and learning fatigue
    variation = random.uniform(-0.1, 0.15)
    fatigue_factor = max(0.5, 1 - (attempt_number * 0.005))  # Slight decline over many attempts
    
    return min(10, max(1, (base + variation) * fatigue_factor * 10))

def calculate_success(student_profile, sub_topic, difficulty, attempt_number):
    """Determine if the interaction was successful"""
    base_rate = student_profile['success_rate']
    
    # Adjust for topic strength
    if sub_topic in student_profile.get('strong_in', []):
        base_rate += 0.15
    elif sub_topic in student_profile.get('weak_in', []):
        base_rate -= 0.20
    
    # Harder topics = lower success
    difficulty_penalty = difficulty * 0.3
    
    # Improvement over time (learning effect)
    learning_bonus = min(0.15, attempt_number * 0.002)
    
    final_rate = base_rate - difficulty_penalty + learning_bonus
    return random.random() < final_rate

def generate_interactions_for_student(student_name, student_id, class_id, ai_model_id, num_interactions, start_date, end_date):
    """Generate interactions for a single student distributed over time"""
    profile = STUDENT_PROFILES[student_name]
    learning_speed = profile['learning_speed']
    
    # Determine how many interactions per sub-topic
    if learning_speed == 'fast':
        sub_topic_distribution = {'algebra': 0.35, 'statistics': 0.30, 'calculus': 0.35}
    elif learning_speed == 'medium':
        sub_topic_distribution = {'algebra': 0.40, 'statistics': 0.35, 'calculus': 0.25}
    else:  # slow
        sub_topic_distribution = {'algebra': 0.50, 'statistics': 0.30, 'calculus': 0.20}
    
    interactions = []
    total_days = (end_date - start_date).days
    
    for sub_topic, percentage in sub_topic_distribution.items():
        num_for_topic = int(num_interactions * percentage)
        topics_list = SUB_TOPICS[sub_topic]['topics']
        difficulty_min, difficulty_max = SUB_TOPICS[sub_topic]['difficulty_range']
        
        for i in range(num_for_topic):
            # Progress through topics over time
            topic_index = min(int((i / num_for_topic) * len(topics_list)), len(topics_list) - 1)
            current_topic = topics_list[topic_index]
            
            # Difficulty increases slightly over time
            difficulty = difficulty_min + ((difficulty_max - difficulty_min) * (i / num_for_topic))
            difficulty += random.uniform(-0.1, 0.1)
            difficulty = max(0.1, min(0.95, difficulty))
            
            # Generate timestamp
            # Distribute interactions unevenly (more recent interactions)
            progress_factor = (i / num_for_topic) ** 0.7  # Biased toward later dates
            days_offset = int(progress_factor * total_days)
            timestamp = start_date + timedelta(days=days_offset, hours=random.randint(8, 20), minutes=random.randint(0, 59))
            
            # Generate interaction data
            prompt = generate_prompt(sub_topic, current_topic, difficulty)
            response = generate_response(sub_topic, current_topic, difficulty)
            engagement = calculate_engagement(profile, sub_topic, i)
            success = calculate_success(profile, sub_topic, difficulty, i)
            strategy = random.choice(STRATEGIES)
            
            interaction = {
                'user_id': student_id,
                'class_id': class_id,
                'ai_model_id': ai_model_id,
                'prompt': prompt,
                'response': response,
                'sub_topic': sub_topic,
                'strategy_used': strategy,
                'engagement_score': engagement,
                'success_indicator': success,
                'tokens_in': random.randint(20, 100),
                'tokens_out': random.randint(100, 500),
                'response_time_ms': random.randint(500, 3000),
                'temperature': 0.7,
                'created_at': timestamp
            }
            
            interactions.append(interaction)
    
    return interactions

def generate_bulk_interactions(total_interactions=1000):
    """Generate all interactions for all students"""
    print(f"\n🚀 Generating {total_interactions} AI Tutor Interactions")
    print(f"📊 Distribution: Algebra, Statistics, Calculus")
    print(f"⏰ Time range: Last 60 days\n")
    
    with app.app_context():
        # Get simulated students
        students = {}
        for name in ['Alex', 'Jordan', 'Taylor']:
            user = User.query.filter_by(first_name=name, last_name='Simulated').first()
            if user:
                students[name] = user
        
        if not students:
            print("❌ Error: No simulated students found")
            return
        
        # Get class and AI model
        first_student = next(iter(students.values()))
        if not first_student.classes:
            print("❌ Error: Students not enrolled in any class")
            return
        
        class_obj = first_student.classes[0]
        ai_model = AIModel.query.first()
        
        if not ai_model:
            print("❌ Error: No AI model found")
            return
        
        # Date range: 60 days ago to now
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)
        
        # Distribution based on student profiles
        alex_count = 400  # High performer - more interactions
        jordan_count = 350  # Average learner
        taylor_count = 250  # Struggling - fewer interactions
        
        # Generate interactions for each student
        all_interactions = []
        
        print(f"👤 Generating {alex_count} interactions for Alex (high performer)...")
        all_interactions.extend(generate_interactions_for_student(
            'Alex', students['Alex'].id, class_obj.id, ai_model.id,
            alex_count, start_date, end_date
        ))
        
        print(f"👤 Generating {jordan_count} interactions for Jordan (average)...")
        all_interactions.extend(generate_interactions_for_student(
            'Jordan', students['Jordan'].id, class_obj.id, ai_model.id,
            jordan_count, start_date, end_date
        ))
        
        print(f"👤 Generating {taylor_count} interactions for Taylor (struggling)...")
        all_interactions.extend(generate_interactions_for_student(
            'Taylor', students['Taylor'].id, class_obj.id, ai_model.id,
            taylor_count, start_date, end_date
        ))
        
        # Sort by timestamp for realistic insertion
        all_interactions.sort(key=lambda x: x['created_at'])
        
        # Batch insert for performance
        print(f"\n💾 Inserting {len(all_interactions)} interactions into database...")
        batch_size = 100
        for i in range(0, len(all_interactions), batch_size):
            batch = all_interactions[i:i+batch_size]
            for interaction_data in batch:
                interaction = AIInteraction(**interaction_data)
                db.session.add(interaction)
            
            db.session.commit()
            print(f"   ✓ Inserted {min(i+batch_size, len(all_interactions))}/{len(all_interactions)}")
        
        print(f"\n✅ Successfully generated {len(all_interactions)} interactions!")
        print(f"\n📈 Summary by sub-topic:")
        for sub_topic in ['algebra', 'statistics', 'calculus']:
            count = sum(1 for x in all_interactions if x['sub_topic'] == sub_topic)
            percentage = (count / len(all_interactions)) * 100
            print(f"   {sub_topic.title()}: {count} ({percentage:.1f}%)")
        
        print(f"\n📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"✨ Data ready for progression visualization!\n")

if __name__ == '__main__':
    generate_bulk_interactions(1000)
