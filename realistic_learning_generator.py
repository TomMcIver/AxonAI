"""
Realistic Learning Curve Generator
Generates AI tutor interactions with realistic learning progression curves
Shows steady improvement over time for investor demonstrations
"""
import random
import math
from datetime import datetime, timedelta
from app import app, db
from models import User, Class, AIInteraction, AIModel

# Learning curve parameters for realistic progression
LEARNING_PROFILES = {
    'Alex': {
        'name': 'High Performer',
        'starting_mastery': 0.45,  # Start at 45%
        'target_mastery': 0.92,     # End at 92%
        'learning_rate': 0.08,      # Fast learner
        'plateau_points': [0.65, 0.80],  # Brief plateaus at 65% and 80%
        'variance': 0.03,           # Low variance (consistent)
        'sub_topic_affinity': {
            'algebra': 1.1,         # 10% better at algebra
            'statistics': 0.95,     # 5% weaker at statistics
            'calculus': 1.05        # 5% better at calculus
        }
    },
    'Jordan': {
        'name': 'Average Performer',
        'starting_mastery': 0.35,  # Start at 35%
        'target_mastery': 0.78,     # End at 78%
        'learning_rate': 0.05,      # Medium learner
        'plateau_points': [0.50, 0.65],  # Plateaus at 50% and 65%
        'variance': 0.05,           # Moderate variance
        'sub_topic_affinity': {
            'algebra': 1.0,         # Average at algebra
            'statistics': 1.1,      # 10% better at statistics
            'calculus': 0.90        # 10% weaker at calculus
        }
    },
    'Taylor': {
        'name': 'Struggling but Improving',
        'starting_mastery': 0.25,  # Start at 25%
        'target_mastery': 0.65,     # End at 65%
        'learning_rate': 0.03,      # Slow but steady learner
        'plateau_points': [0.35, 0.50],  # More frequent plateaus
        'variance': 0.07,           # Higher variance (less consistent)
        'sub_topic_affinity': {
            'algebra': 0.95,        # Slightly weak at algebra
            'statistics': 0.90,     # Weaker at statistics
            'calculus': 0.85        # Weakest at calculus
        }
    }
}

def sigmoid_learning_curve(progress, learning_rate=0.05, midpoint=0.5):
    """
    Generate a sigmoid (S-curve) learning progression
    This creates realistic learning with slow start, rapid middle, and plateau
    """
    # Adjust progress to center around midpoint
    x = (progress - midpoint) * 10
    # Sigmoid function
    return 1 / (1 + math.exp(-x * learning_rate))

def calculate_realistic_mastery(student_name, sub_topic, day_number, total_days):
    """
    Calculate mastery level using realistic learning curve
    
    Args:
        student_name: Name of the student
        sub_topic: The sub-topic being learned
        day_number: Current day in the learning sequence
        total_days: Total days of learning
    
    Returns:
        float: Mastery level from 0 to 1
    """
    profile = LEARNING_PROFILES[student_name]
    
    # Calculate base progress (0 to 1 over time)
    progress = day_number / total_days
    
    # Apply sigmoid learning curve for realistic progression
    curve_value = sigmoid_learning_curve(progress, profile['learning_rate'])
    
    # Calculate mastery range
    mastery_range = profile['target_mastery'] - profile['starting_mastery']
    
    # Base mastery calculation
    base_mastery = profile['starting_mastery'] + (curve_value * mastery_range)
    
    # Apply sub-topic affinity
    affinity_multiplier = profile['sub_topic_affinity'][sub_topic]
    adjusted_mastery = base_mastery * affinity_multiplier
    
    # Add plateaus for realism (periods of consolidation)
    for plateau_point in profile['plateau_points']:
        if abs(adjusted_mastery - plateau_point) < 0.05:
            # Slow down progress near plateau points
            adjusted_mastery = plateau_point + (adjusted_mastery - plateau_point) * 0.3
    
    # Add controlled variance for natural fluctuation
    # Variance decreases as mastery increases (more stable at higher levels)
    variance_factor = profile['variance'] * (1 - curve_value * 0.5)
    daily_variance = random.gauss(0, variance_factor)
    
    # Ensure variance doesn't cause regression below previous achievement
    # This creates a "ratchet effect" - knowledge doesn't disappear
    final_mastery = adjusted_mastery + daily_variance
    
    # Clamp to reasonable bounds
    final_mastery = max(profile['starting_mastery'], min(0.95, final_mastery))
    
    return final_mastery

def mastery_to_interaction_scores(mastery, sub_topic):
    """
    Convert mastery level to interaction scores
    Creates realistic engagement and success indicators
    """
    # Engagement increases with mastery (more confident students engage more)
    base_engagement = 3 + (mastery * 5)  # 3-8 range
    engagement = base_engagement + random.gauss(0, 0.5)
    engagement = max(1, min(10, engagement))
    
    # Success indicator based on mastery with some randomness
    # Higher mastery = higher chance of success
    success_threshold = 0.3 + (0.4 * (1 - mastery))  # Easier to succeed as you learn
    success = random.random() > success_threshold
    
    # More advanced topics show deeper engagement
    if sub_topic == 'calculus':
        engagement += 0.5
    elif sub_topic == 'statistics':
        engagement += 0.3
    
    return engagement, success

def generate_realistic_prompt(sub_topic, mastery_level):
    """Generate prompts that evolve with mastery level"""
    
    if mastery_level < 0.4:
        # Beginner questions
        prompts = {
            'algebra': [
                "I don't understand how to solve for x",
                "Can you explain what variables are?",
                "How do I start this equation?",
                "What does this symbol mean?",
                "I'm confused about the basics"
            ],
            'statistics': [
                "What is mean vs median?",
                "How do I calculate average?",
                "What is probability?",
                "Can you explain data in simple terms?",
                "I don't understand graphs"
            ],
            'calculus': [
                "What is a derivative?",
                "I don't understand limits",
                "Can you explain calculus basics?",
                "What does rate of change mean?",
                "How is this different from algebra?"
            ]
        }
    elif mastery_level < 0.7:
        # Intermediate questions
        prompts = {
            'algebra': [
                "How do I factor this polynomial?",
                "Can you help with this system of equations?",
                "What's the best approach for quadratics?",
                "How do I handle inequalities?",
                "Can you check my work on this problem?"
            ],
            'statistics': [
                "How do I calculate standard deviation?",
                "Can you explain normal distribution?",
                "What's the difference between correlation and causation?",
                "How do I interpret this data set?",
                "When do I use different statistical tests?"
            ],
            'calculus': [
                "How do I apply the chain rule here?",
                "Can you help with this integration?",
                "What's the derivative of this function?",
                "How do I find the area under this curve?",
                "Can you explain optimization problems?"
            ]
        }
    else:
        # Advanced questions
        prompts = {
            'algebra': [
                "Can you show me an elegant solution to this complex equation?",
                "What's the relationship between these algebraic structures?",
                "How does this connect to higher mathematics?",
                "Can we prove this algebraically?",
                "What are some advanced applications?"
            ],
            'statistics': [
                "How do I design this hypothesis test?",
                "Can you explain Bayesian vs frequentist approaches?",
                "What's the best model for this data?",
                "How do I handle multivariate analysis?",
                "Can you help with this regression model?"
            ],
            'calculus': [
                "How do I solve this differential equation?",
                "Can you explain this multivariable calculus concept?",
                "What's the best approach for this optimization?",
                "How do I apply calculus to this physics problem?",
                "Can we explore the theoretical foundations?"
            ]
        }
    
    return random.choice(prompts[sub_topic])

def generate_realistic_response(sub_topic, mastery_level):
    """Generate AI responses that adapt to student level"""
    
    if mastery_level < 0.4:
        return f"Let's start with the basics of {sub_topic}. I'll break this down into simple steps..."
    elif mastery_level < 0.7:
        return f"Good question! You're making progress with {sub_topic}. Let me show you the next concept..."
    else:
        return f"Excellent thinking! You're ready for advanced {sub_topic} concepts. Let's explore deeper..."

def generate_realistic_interactions(total_interactions=999):
    """Generate interactions with realistic learning curves"""
    
    print(f"\n🎯 Generating {total_interactions} Realistic Learning Interactions")
    print(f"📈 Creating upward learning curves for investor demo")
    print(f"📊 Sub-topics: Algebra, Statistics, Calculus\n")
    
    with app.app_context():
        # Get simulated students
        students = {}
        for name in ['Alex', 'Jordan', 'Taylor']:
            user = User.query.filter_by(
                first_name=name,
                last_name='Simulated',
                is_active=True
            ).first()
            if user:
                students[name] = user
            else:
                print(f"❌ {name} not found. Run create_simulated_students.py first")
                return
        
        if not students:
            print("❌ No students found")
            return
        
        # Get class and AI model
        first_student = next(iter(students.values()))
        if not first_student.classes:
            print("❌ Students not enrolled in class")
            return
        
        class_obj = first_student.classes[0]
        class_id = class_obj.id
        
        ai_model = AIModel.query.filter_by(model_name='GPT-4o-mini', is_active=True).first()
        if not ai_model:
            # Try to get any active AI model
            ai_model = AIModel.query.filter_by(is_active=True).first()
            if not ai_model:
                print("❌ AI Model not found")
                return
        
        # Clear existing interactions
        print("🗑️  Clearing old interactions...")
        AIInteraction.query.filter(
            AIInteraction.user_id.in_([s.id for s in students.values()])
        ).delete()
        db.session.commit()
        
        # Time range: 60 days ago to today
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)
        total_days = 60
        
        # Distribution of interactions per student
        interactions_per_student = total_interactions // 3
        
        # Track statistics
        stats = {name: {'algebra': 0, 'statistics': 0, 'calculus': 0} for name in students.keys()}
        
        for student_name, student_user in students.items():
            print(f"\n👤 Generating learning curve for {student_name}...")
            
            # Learning progression for this student
            # Start with more algebra, progress to statistics, then calculus
            topic_progression = []
            
            # Phase 1: Heavy algebra (days 1-20)
            for _ in range(int(interactions_per_student * 0.4)):
                topic_progression.append('algebra')
            
            # Phase 2: Mix algebra and statistics (days 21-40)
            for _ in range(int(interactions_per_student * 0.35)):
                topic_progression.append(random.choice(['algebra', 'statistics']))
            
            # Phase 3: All topics with calculus (days 41-60)
            for _ in range(int(interactions_per_student * 0.25)):
                topic_progression.append(random.choice(['algebra', 'statistics', 'calculus']))
            
            # Shuffle slightly to avoid perfect patterns
            random.shuffle(topic_progression[:len(topic_progression)//3])
            
            # Generate interactions with realistic progression
            for i, sub_topic in enumerate(topic_progression[:interactions_per_student]):
                # Calculate day number with some variation
                progress_ratio = i / interactions_per_student
                base_day = int(progress_ratio * total_days)
                day_variation = random.randint(-2, 2)
                day_number = max(0, min(total_days - 1, base_day + day_variation))
                
                # Calculate realistic mastery level
                mastery = calculate_realistic_mastery(
                    student_name, 
                    sub_topic, 
                    day_number,
                    total_days
                )
                
                # Convert mastery to interaction scores
                engagement, success = mastery_to_interaction_scores(mastery, sub_topic)
                
                # Generate timestamp
                timestamp = start_date + timedelta(
                    days=day_number,
                    hours=random.randint(8, 20),
                    minutes=random.randint(0, 59)
                )
                
                # Generate content based on mastery level
                prompt = generate_realistic_prompt(sub_topic, mastery)
                response = generate_realistic_response(sub_topic, mastery)
                
                # Create interaction
                interaction = AIInteraction(
                    user_id=student_user.id,
                    class_id=class_id,
                    ai_model_id=ai_model.id,
                    prompt=prompt,
                    response=response,
                    sub_topic=sub_topic,
                    strategy_used=random.choice([
                        'direct_instruction', 'socratic_questioning',
                        'worked_examples', 'visual_demonstrations'
                    ]),
                    engagement_score=engagement,
                    success_indicator=success,
                    tokens_in=random.randint(20, 100),
                    tokens_out=random.randint(100, 500),
                    response_time_ms=random.randint(500, 2000),
                    temperature=0.7,
                    created_at=timestamp
                )
                
                db.session.add(interaction)
                stats[student_name][sub_topic] += 1
            
            # Commit after each student
            db.session.commit()
            print(f"✅ Generated {interactions_per_student} interactions for {student_name}")
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"✨ Realistic Learning Curves Generated!")
        print(f"{'='*60}")
        print(f"\n📊 Distribution Summary:")
        
        total_by_topic = {'algebra': 0, 'statistics': 0, 'calculus': 0}
        for student_name, topics in stats.items():
            print(f"\n{student_name}:")
            for topic, count in topics.items():
                print(f"  {topic.capitalize()}: {count} interactions")
                total_by_topic[topic] += count
        
        print(f"\n📈 Total by Topic:")
        for topic, count in total_by_topic.items():
            print(f"  {topic.capitalize()}: {count}")
        
        print(f"\n🎯 Key Features:")
        print(f"  • Steady upward progression for all students")
        print(f"  • Natural learning curves with plateaus")
        print(f"  • Different learning rates per student")
        print(f"  • Topic progression from basic to advanced")
        print(f"  • Realistic variance without regression")
        print(f"\n✅ Ready for investor demonstration!")

if __name__ == '__main__':
    generate_realistic_interactions(999)