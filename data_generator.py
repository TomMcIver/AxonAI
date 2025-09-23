"""
Realistic Data Generator for TMC Learning System
Generates 100+ students with authentic interactions to showcase dual-AI architecture
"""
import random
import json
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from app import app, db
from models import (
    User, Class, Assignment, AssignmentSubmission, Grade, AIModel, 
    AIInteraction, FailedStrategy, OptimizedProfile, MiniTest, 
    MiniTestResponse, ChatMessage
)
from ai_service import AIService
from ai_coordinator import BigAICoordinator

class RealisticDataGenerator:
    """Generate realistic student data and AI interactions"""
    
    def __init__(self):
        self.subjects = ["Mathematics", "English", "Science", "History", "Art"]
        self.teaching_strategies = [
            "socratic_method", "direct_instruction", "example_based", 
            "problem_solving", "visual_learning", "storytelling", 
            "gamification", "step_by_step", "collaborative", "inquiry_based"
        ]
        
        # Realistic student names and backgrounds
        self.first_names = [
            "Emma", "Liam", "Olivia", "Noah", "Ava", "Oliver", "Isabella", "Elijah",
            "Sophia", "Lucas", "Charlotte", "Mason", "Amelia", "Logan", "Mia", "Jacob",
            "Harper", "Ethan", "Evelyn", "Alexander", "Abigail", "Michael", "Emily", 
            "Benjamin", "Elizabeth", "William", "Sofia", "James", "Avery", "Henry",
            "Ella", "Owen", "Madison", "Sebastian", "Scarlett", "Jackson", "Victoria",
            "Aiden", "Aria", "Matthew", "Grace", "Samuel", "Chloe", "David", "Camila",
            "Joseph", "Penelope", "Carter", "Riley", "Wyatt", "Layla", "John", "Lillian"
        ]
        
        self.last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", 
            "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
            "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
            "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
            "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
            "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
            "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
            "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz"
        ]
        
        self.learning_styles = ["visual", "auditory", "kinesthetic", "reading"]
        self.ethnicities = ["European", "Māori", "Pasifika", "Asian", "African", "Mixed"]
        self.languages = ["English", "Spanish", "Mandarin", "Te Reo Māori", "Samoan", "Hindi", "Arabic"]
        self.difficulties = [None, "Dyslexia", "ADHD", "Autism Spectrum", "Processing Disorder"]
        
        # Academic goal templates
        self.academic_goals = [
            "Pass NCEA Level 3 with Excellence endorsements",
            "Improve mathematical reasoning and problem-solving skills", 
            "Develop strong essay writing and critical analysis abilities",
            "Master scientific method and experimental design",
            "Build confidence in public speaking and presentations",
            "Achieve university entrance requirements for STEM",
            "Develop creative writing and storytelling skills",
            "Improve time management and study organization",
            "Master algebra and prepare for calculus",
            "Understand historical context and cause-effect relationships"
        ]
        
        # Sample conversation starters for different subjects
        self.conversation_starters = {
            "Mathematics": [
                "I'm struggling with quadratic equations. Can you help me understand the vertex form?",
                "What's the difference between mean, median, and mode? I keep mixing them up.",
                "How do I solve this system of linear equations?",
                "I don't understand why we need to find the derivative. What does it actually mean?",
                "Can you explain how to calculate compound interest?",
                "Why do we flip the inequality sign when dividing by a negative number?",
                "I'm confused about trigonometric ratios. Which one do I use when?",
                "How do you factor polynomials? I always get stuck.",
                "What's the purpose of logarithms? When would I use them?",
                "I need help with probability. How do I calculate combinations vs permutations?"
            ],
            "English": [
                "I'm writing an essay on themes in Romeo and Juliet. Where should I start?",
                "How do I make my writing more engaging? My essays feel boring.",
                "What's the difference between metaphor and simile?",
                "I need help analyzing this poem. How do I identify literary devices?",
                "How do I write a strong thesis statement?",
                "What makes a good introduction paragraph?",
                "I'm struggling with grammar. When do I use 'who' vs 'whom'?",
                "How do I cite sources properly in my research paper?",
                "Can you help me understand the difference between active and passive voice?",
                "I need to write a persuasive speech. What techniques should I use?"
            ],
            "Science": [
                "I don't understand the difference between mitosis and meiosis.",
                "How does photosynthesis actually work at the molecular level?",
                "Can you explain Newton's three laws of motion with examples?",
                "I'm confused about the periodic table. How are elements organized?",
                "What's the difference between ionic and covalent bonds?",
                "How do I balance chemical equations?",
                "Can you help me understand genetics and inheritance patterns?",
                "What causes different phases of the moon?",
                "How does evolution work? I need examples of natural selection.",
                "I'm struggling with physics problems involving momentum and energy."
            ],
            "History": [
                "What were the main causes of World War I?",
                "How did the Industrial Revolution change society?",
                "Can you explain the significance of the Treaty of Waitangi?",
                "What led to the fall of the Roman Empire?",
                "How did colonialism affect indigenous peoples worldwide?",
                "What were the major battles and turning points of WWII?",
                "Can you help me understand the causes of the American Civil War?",
                "How did the Renaissance change European culture?",
                "What was life like during the Great Depression?",
                "How did women's rights movements develop over time?"
            ],
            "Art": [
                "What are the key characteristics of Impressionist painting?",
                "How do I improve my drawing proportions?",
                "What's the difference between oil paints and acrylics?",
                "Can you explain color theory and how to mix colors?",
                "How do I create depth and perspective in my artwork?",
                "What makes a photograph compositionally strong?",
                "How do different art movements reflect their time periods?",
                "What techniques did Renaissance masters use?",
                "How do I develop my own artistic style?",
                "What are the principles of good design?"
            ]
        }
        
        # AI response templates for different strategies
        self.response_templates = {
            "socratic_method": [
                "That's a great question! What do you think might happen if we approach it this way: {}? What patterns do you notice?",
                "Let me ask you something to help you think through this: {} What's your reasoning behind that?",
                "Interesting point! What if we considered {}? How does that change your perspective?"
            ],
            "direct_instruction": [
                "Here's how to solve this step by step: {}. The key concept is understanding that {}.",
                "Let me explain this clearly: {}. This works because {}.",
                "The important thing to remember is: {}. Here's the method: {}"
            ],
            "example_based": [
                "Let me show you with a concrete example: {}. Notice how {}?",
                "Here's a similar problem we can work through: {}. See the pattern?",
                "Think of it like this everyday example: {}. The same principle applies here."
            ],
            "visual_learning": [
                "Imagine this visually: {}. Picture how {} would look on a graph.",
                "Let's draw this out. If you sketch {}, you'll see that {}.",
                "Visualize it this way: {}. The relationship becomes clear when you see it."
            ],
            "gamification": [
                "Let's turn this into a challenge! Can you {} in under 3 steps? Here's your hint: {}",
                "Think of this like a puzzle game. Your mission is to {} by using {}.",
                "You've unlocked a new skill! Now that you understand {}, let's level up to {}"
            ]
        }
    
    def generate_students(self, count=100):
        """Generate realistic student profiles"""
        print(f"Generating {count} realistic students...")
        students = []
        
        for i in range(count):
            # Create realistic profile
            first_name = random.choice(self.first_names)
            last_name = random.choice(self.last_names)
            age = random.randint(11, 18)
            
            student = User(
                email=f"{first_name.lower()}.{last_name.lower()}.{i+1}@school.edu",
                password_hash=generate_password_hash("student123"),
                role="student",
                first_name=first_name,
                last_name=last_name,
                age=age,
                gender=random.choice(["Male", "Female", "Other"]),
                ethnicity=random.choice(self.ethnicities),
                year_level=f"Year {min(13, max(9, age-2))}",
                primary_language=random.choice(self.languages),
                secondary_language=random.choice([None] + self.languages),
                learning_difficulty=random.choice(self.difficulties) if random.random() < 0.15 else None,
                learning_style=random.choice(self.learning_styles),
                academic_goals=random.choice(self.academic_goals),
                preferred_difficulty=random.choice(["beginner", "intermediate", "advanced"]),
                attendance_rate=random.uniform(0.75, 0.98),
                extracurricular_activities=json.dumps(random.sample([
                    "Rugby", "Netball", "Drama Club", "Chess Club", "Debate Team",
                    "Art Club", "Music Band", "Science Fair", "Student Council",
                    "Environmental Club", "Photography", "Basketball"
                ], random.randint(1, 3))),
                interests=json.dumps(random.sample([
                    "Technology", "Sports", "Music", "Reading", "Gaming", 
                    "Art", "Science", "History", "Travel", "Cooking",
                    "Environment", "Social Justice", "Photography"
                ], random.randint(2, 5)))
            )
            
            students.append(student)
        
        # Bulk add students
        db.session.add_all(students)
        db.session.commit()
        
        print(f"✓ Generated {count} students with diverse profiles")
        return students
    
    def generate_classes_and_assignments(self):
        """Create classes with teachers and assignments"""
        print("Creating classes and assignments...")
        
        # Check if teacher exists, if not create one
        teacher = User.query.filter_by(email="teacher@school.edu").first()
        if not teacher:
            teacher = User(
                email="teacher@school.edu",
                password_hash=generate_password_hash("teacher123"),
                role="teacher",
                first_name="Sarah",
                last_name="Mitchell"
            )
            db.session.add(teacher)
            db.session.commit()
        else:
            print("Using existing teacher account")
        
        classes = []
        for subject in self.subjects:
            # Check if class already exists
            class_name = f"{subject} - Year 12"
            existing_class = Class.query.filter_by(name=class_name).first()
            
            if existing_class:
                classes.append(existing_class)
                print(f"Using existing class: {class_name}")
            else:
                # Create AI model for each subject
                ai_model = AIModel(
                    subject=subject,
                    model_name="gpt-4o-mini",
                    prompt_template=f"You are a specialized {subject} AI tutor. Help students learn {subject} concepts.",
                    max_tokens=800,
                    temperature=0.7
                )
                db.session.add(ai_model)
                db.session.flush()
                
                # Create class
                class_obj = Class(
                    name=class_name,
                    subject=subject,
                    description=f"Comprehensive {subject} course covering NCEA Level 2",
                    teacher_id=teacher.id,
                    ai_model_id=ai_model.id
                )
                db.session.add(class_obj)
                classes.append(class_obj)
        
        db.session.commit()
        
        # Create assignments
        for class_obj in classes:
            for i in range(8):  # 8 assignments per class
                assignment = Assignment(
                    title=f"{class_obj.subject} Assignment {i+1}",
                    description=f"Complete tasks related to {class_obj.subject} concepts",
                    due_date=datetime.utcnow() + timedelta(days=random.randint(1, 30)),
                    max_points=100,
                    class_id=class_obj.id
                )
                db.session.add(assignment)
        
        db.session.commit()
        print("✓ Created classes, AI models, and assignments")
        return classes
    
    def generate_ai_interactions(self, students, classes):
        """Generate realistic AI chat interactions"""
        print("Generating AI interactions and conversations...")
        
        ai_service = AIService()
        interactions_count = 0
        
        for student in students:
            student_classes = student.classes
            
            # Generate very few interactions to avoid timeout (2-3 per student)
            for _ in range(random.randint(2, 3)):
                class_obj = random.choice(student_classes)
                subject = class_obj.subject
                
                # Choose a conversation starter
                starter = random.choice(self.conversation_starters.get(subject, ["I need help with this topic."]))
                
                # Choose strategy and success rate based on student profile
                strategy = random.choice(self.teaching_strategies)
                
                # Success rates vary by student learning style and strategy match
                base_success = 0.7
                if student.learning_style == "visual" and strategy == "visual_learning":
                    success_rate = 0.9
                elif student.learning_style == "auditory" and strategy in ["socratic_method", "direct_instruction"]:
                    success_rate = 0.85
                elif student.learning_difficulty and strategy == "step_by_step":
                    success_rate = 0.8
                else:
                    success_rate = random.uniform(0.5, 0.9)
                
                success = random.random() < success_rate
                
                # Generate appropriate response
                response_template = random.choice(self.response_templates.get(strategy, [
                    "Let me help you understand this concept: {}. The key is to remember that {}."
                ]))
                
                concept = f"{subject} concept"
                explanation = f"this relates to your {student.learning_style} learning style"
                response = response_template.format(concept, explanation)[:500]
                
                # Calculate engagement based on response quality and student interest
                engagement = random.uniform(0.4, 1.0) if success else random.uniform(0.2, 0.6)
                
                # Create interaction
                interaction = AIInteraction(
                    user_id=student.id,
                    class_id=class_obj.id,
                    ai_model_id=class_obj.ai_model_id,
                    prompt=starter,
                    response=response,
                    strategy_used=strategy,
                    engagement_score=engagement,
                    tokens_in=len(starter.split()) * 1.3,
                    tokens_out=len(response.split()) * 1.3,
                    response_time_ms=random.randint(1000, 3000),
                    temperature=0.7,
                    success_indicator=success,
                    user_feedback=random.randint(1, 5) if random.random() < 0.3 else None,
                    context_data=json.dumps({
                        "time_of_day": random.choice(["morning", "afternoon", "evening"]),
                        "session_length": random.randint(5, 30)
                    }),
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 90))
                )
                
                db.session.add(interaction)
                
                # Create corresponding chat message
                chat = ChatMessage(
                    user_id=student.id,
                    class_id=class_obj.id,
                    ai_model_id=class_obj.ai_model_id,
                    message=starter,
                    response=response,
                    message_type="student",
                    context_data=json.dumps({"generated": True}),
                    created_at=interaction.created_at
                )
                db.session.add(chat)
                
                interactions_count += 1
                
                # Log failed strategies occasionally
                if not success and random.random() < 0.3:
                    failed_strategy = FailedStrategy(
                        user_id=student.id,
                        class_id=class_obj.id,
                        strategy_name=strategy,
                        failure_reason="Low engagement and poor comprehension",
                        failure_count=random.randint(1, 3),
                        last_attempted=interaction.created_at
                    )
                    db.session.add(failed_strategy)
        
        db.session.commit()
        print(f"✓ Generated {interactions_count} realistic AI interactions")
    
    def generate_quick_demo_interactions(self, students, classes):
        """Generate quick demo interactions without calling OpenAI"""
        print("Generating quick demo interactions...")
        interactions_count = 0
        
        # Ensure AI model exists
        ai_model = AIModel.query.filter_by(model_name='gpt-4o-mini').first()
        if not ai_model:
            ai_model = AIModel(
                subject='General',  # General purpose model
                model_name='gpt-4o-mini',
                prompt_template='You are a helpful AI tutor.',
                max_tokens=1000,
                temperature=0.7,
                is_active=True
            )
            db.session.add(ai_model)
            db.session.commit()
        
        for student in students:
            student_classes = student.classes
            
            # Generate 2-3 quick interactions per student
            for i in range(random.randint(2, 3)):
                class_obj = random.choice(student_classes)
                subject = class_obj.subject
                
                # Create demo interaction without API call
                interaction = AIInteraction(
                    user_id=student.id,
                    class_id=class_obj.id,
                    ai_model_id=ai_model.id,  # Use the created AI model
                    prompt=f"Help me with {subject.lower()}",
                    response=f"Here's help with your {subject.lower()} question...",
                    strategy_used=random.choice(self.teaching_strategies),
                    success_indicator=random.choice([True, True, True, False]),  # 75% success
                    engagement_score=random.uniform(0.6, 1.0),
                    response_time_ms=random.randint(500, 2000),
                    tokens_in=random.randint(50, 200),
                    tokens_out=random.randint(100, 400),
                    created_at=datetime.utcnow() - timedelta(hours=random.randint(0, 72))
                )
                db.session.add(interaction)
                interactions_count += 1
        
        db.session.commit()
        print(f"✓ Generated {interactions_count} quick demo interactions")
    
    def build_simple_profiles(self, students):
        """Build simple profiles for quick demo"""
        print("Building simple student profiles...")
        
        for student in students:
            # Calculate basic metrics
            interactions = AIInteraction.query.filter_by(user_id=student.id).all()
            if not interactions:
                continue
                
            success_rate = len([i for i in interactions if i.success_indicator]) / len(interactions) * 100
            avg_engagement = sum([i.engagement_score or 0 for i in interactions]) / len(interactions)
            
            # Create simple profile
            profile = OptimizedProfile(
                user_id=student.id,
                current_pass_rate=success_rate,
                predicted_pass_rate=min(100, success_rate + random.uniform(5, 15)),  # AI improvement
                engagement_level=avg_engagement,
                mastery_scores=json.dumps({"Math": 75, "English": 80, "Science": 70}),
                best_time_of_day=random.choice(["morning", "afternoon", "evening"]),
                optimal_session_length=random.randint(20, 40),
                preferred_strategies=json.dumps(self.teaching_strategies[:3]),
                avoided_strategies=json.dumps([]),
                recent_topics=json.dumps(["algebra", "essay writing", "chemistry"]),
                struggle_areas=json.dumps(["complex equations", "grammar"]),
                strength_areas=json.dumps(["reading comprehension", "basic math"])
            )
            db.session.add(profile)
        
        db.session.commit()
        print("✓ Built simple profiles for demo students")
    
    def build_optimized_profiles(self, students):
        """Create optimized profiles based on interactions"""
        print("Building optimized student profiles...")
        
        # Pre-fetch all classes to avoid repeated queries
        all_classes = {c.id: c for c in Class.query.all()}
        
        for student in students:
            
            # Get student's interactions
            interactions = AIInteraction.query.filter_by(user_id=student.id).all()
            
            if not interactions:
                continue
            
            # Calculate metrics
            avg_engagement = sum([i.engagement_score or 0 for i in interactions]) / len(interactions)
            successful_interactions = [i for i in interactions if i.success_indicator]
            success_rate = len(successful_interactions) / len(interactions) * 100
            
            # Find best strategies
            strategy_success = {}
            for interaction in interactions:
                if interaction.strategy_used:
                    if interaction.strategy_used not in strategy_success:
                        strategy_success[interaction.strategy_used] = {"success": 0, "total": 0}
                    strategy_success[interaction.strategy_used]["total"] += 1
                    if interaction.success_indicator:
                        strategy_success[interaction.strategy_used]["success"] += 1
            
            # Get top strategies
            sorted_strategies = sorted(
                strategy_success.items(),
                key=lambda x: x[1]["success"] / max(x[1]["total"], 1),
                reverse=True
            )
            top_strategies = [s[0] for s in sorted_strategies[:3]]
            
            # Identify struggle and strength areas
            subject_performance = {}
            for interaction in interactions:
                class_obj = all_classes.get(interaction.class_id)
                if not class_obj:
                    continue
                subject = class_obj.subject
                if subject not in subject_performance:
                    subject_performance[subject] = {"success": 0, "total": 0}
                subject_performance[subject]["total"] += 1
                if interaction.success_indicator:
                    subject_performance[subject]["success"] += 1
            
            struggle_areas = []
            strength_areas = []
            for subject, perf in subject_performance.items():
                rate = perf["success"] / max(perf["total"], 1)
                if rate < 0.6:
                    struggle_areas.append(subject)
                elif rate > 0.8:
                    strength_areas.append(subject)
            
            # Create optimized profile
            profile = OptimizedProfile(
                user_id=student.id,
                current_pass_rate=success_rate,
                predicted_pass_rate=min(100, success_rate + random.uniform(-5, 10)),
                engagement_level=avg_engagement,
                mastery_scores=json.dumps(subject_performance),
                best_time_of_day=random.choice(["morning", "afternoon", "evening"]),
                optimal_session_length=random.randint(15, 45),
                preferred_strategies=json.dumps(top_strategies),
                avoided_strategies=json.dumps([]),
                recent_topics=json.dumps([i.prompt[:30] for i in interactions[-5:]]),
                struggle_areas=json.dumps(struggle_areas),
                strength_areas=json.dumps(strength_areas)
            )
            
            db.session.add(profile)
        
        db.session.commit()
        print("✓ Built optimized profiles for all students")
    
    def generate_complete_dataset(self, student_count=100):
        """Generate complete realistic dataset"""
        print(f"🚀 Starting complete dataset generation for {student_count} students...")
        
        try:
            # Clear existing data (optional)
            print("Clearing existing student data...")
            
            # First, clear many-to-many relationships (class enrollments)
            students = User.query.filter_by(role='student').all()
            for student in students:
                student.classes.clear()
            db.session.commit()
            
            # Now clear the related data
            AIInteraction.query.delete()
            OptimizedProfile.query.delete()
            FailedStrategy.query.delete()
            ChatMessage.query.delete()
            User.query.filter_by(role='student').delete()
            db.session.commit()
            
            # Generate all components
            students = self.generate_students(student_count)
            classes = self.generate_classes_and_assignments()
            
            # Enroll all students in classes first (after generating both students and classes)
            print("Enrolling students in classes...")
            for student in students:
                # Refresh student in session
                db.session.add(student)
                enrolled_classes = random.sample(classes, random.randint(3, 5))
                student.classes.extend(enrolled_classes)
            db.session.commit()
            print("✓ Students enrolled in classes")
            
            # Process only first 10 students to avoid timeout
            sample_students = students[:10]  # Only process 10 students for demo
            print(f"Processing {len(sample_students)} students for quick demo...")
            
            # Generate minimal AI interactions (don't call OpenAI, just create demo data)
            self.generate_quick_demo_interactions(sample_students, classes)
            
            # Build simple profiles 
            self.build_simple_profiles(sample_students)
            
            # Commit changes
            db.session.commit()
            print(f"✓ Quick demo data generated for {len(sample_students)} students")
            
            # Run Big AI Coordinator analysis
            from ai_coordinator import BigAICoordinator, PatternInsight
            coordinator = BigAICoordinator()
            coordinator.analyze_global_patterns()
            
            print("🎉 Dataset generation complete!")
            print(f"Generated:")
            print(f"  • {len(students)} students with diverse profiles")
            print(f"  • {len(classes)} classes with AI models")
            print(f"  • {AIInteraction.query.count()} AI interactions")
            print(f"  • {OptimizedProfile.query.count()} optimized profiles")
            print(f"  • {PatternInsight.query.count()} AI insights discovered!")
            
            return {
                'students': len(students),
                'interactions': AIInteraction.query.count(),
                'profiles': OptimizedProfile.query.count(),
                'insights': PatternInsight.query.count()
            }
        except Exception as e:
            db.session.rollback()
            print(f"Error during data generation: {str(e)}")
            raise

# CLI interface for easy generation
if __name__ == "__main__":
    with app.app_context():
        generator = RealisticDataGenerator()
        generator.generate_complete_dataset(100)