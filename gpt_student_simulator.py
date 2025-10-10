"""
GPT-Powered Student Simulator
Creates realistic interactions between simulated students and the AI tutor system
Each student is powered by GPT with different learning personas
"""
import os
import sys
import time
import json
from openai import OpenAI
from app import app, db
from models import User, Class
from ai_service import AIService

# Initialize OpenAI client for student personas
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
ai_service = AIService()

# Student Personas - These define how each GPT-powered student behaves
# Note: IDs are looked up dynamically from database
STUDENT_PERSONAS = {
    "Alex": {
        "system_prompt": """You are Alex, a high-performing Year 12 student who:
- Grasps concepts quickly and asks insightful follow-up questions
- Connects new material to previously learned topics
- Seeks deeper understanding beyond the basics
- Uses proper academic language
- Shows genuine curiosity about advanced applications
- Occasionally asks challenging "what if" scenarios

Your goal: Learn efficiently and push yourself to understand complex concepts.
Keep questions concise (1-2 sentences). Show intelligence through question quality, not length.""",
        "topics_of_interest": [
            "quadratic equations",
            "calculus fundamentals", 
            "trigonometric identities",
            "mathematical proofs",
            "real-world applications of math"
        ]
    },
    "Jordan": {
        "system_prompt": """You are Jordan, an average Year 12 student who:
- Needs concepts explained clearly before understanding
- Asks clarifying questions when confused
- Shows gradual improvement over time
- Sometimes forgets previous lessons
- Appreciates step-by-step explanations
- Connects topics to personal interests (sports, music, art)

Your goal: Understand the material well enough to pass exams, build confidence.
Keep questions natural and conversational (1-2 sentences).""",
        "topics_of_interest": [
            "basic algebra",
            "solving equations",
            "fractions and decimals",
            "geometry basics",
            "word problems"
        ]
    },
    "Taylor": {
        "system_prompt": """You are Taylor, a struggling Year 12 student who:
- Finds math challenging and often feels overwhelmed
- Asks basic questions about fundamental concepts
- Needs simpler explanations and more examples
- Sometimes gets frustrated but keeps trying
- Benefits from real-world examples
- Has attention difficulties, so keeps things brief

Your goal: Understand core concepts enough to pass. Don't be afraid to ask "simple" questions.
Keep questions short and direct (1 sentence). Show you're trying but struggling.""",
        "topics_of_interest": [
            "basic addition and multiplication",
            "simple fractions",
            "understanding variables",
            "what math symbols mean",
            "easier ways to remember formulas"
        ]
    }
}

def get_simulated_students():
    """
    Dynamically fetch simulated student IDs from database
    Returns dict with student names mapped to their user objects
    """
    students = {}
    for name in ["Alex", "Jordan", "Taylor"]:
        user = User.query.filter_by(first_name=name, last_name='Simulated', is_active=True).first()
        if user:
            students[name] = user
        else:
            print(f"Warning: {name} Simulated not found in database")
    return students

def generate_student_question(student_name, topic, conversation_history, ai_response=None):
    """
    Use GPT to generate a realistic student question based on their persona
    
    Args:
        student_name: Name of the student (Alex, Jordan, or Taylor)
        topic: Current topic being discussed
        conversation_history: Previous messages in the conversation
        ai_response: The AI tutor's last response (for generating follow-ups)
    
    Returns:
        str: The student's question
    """
    persona = STUDENT_PERSONAS[student_name]
    
    # Build context for the student persona
    if ai_response:
        # Generate a follow-up based on AI's response
        user_prompt = f"""Based on this AI tutor response, generate your next question or comment:

AI Tutor: "{ai_response[:300]}..."

Topic: {topic}
Previous conversation: {json.dumps(conversation_history[-2:] if conversation_history else [])}

Generate ONE natural follow-up question or comment based on your learning style."""
    else:
        # Generate initial question about the topic
        user_prompt = f"""You're starting a new learning session about: {topic}

Generate ONE natural question to ask your AI tutor about this topic, based on your learning level and style."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": persona["system_prompt"]},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=100,
            temperature=0.8
        )
        
        question = response.choices[0].message.content.strip()
        return question
        
    except Exception as e:
        print(f"Error generating question for {student_name}: {e}")
        # Fallback questions
        fallbacks = {
            "Alex": f"Can you explain the advanced concepts behind {topic}?",
            "Jordan": f"I'm trying to understand {topic}. Can you break it down?",
            "Taylor": f"What is {topic}? I'm confused."
        }
        return fallbacks[student_name]

def simulate_conversation(student_user, class_id, topic, num_exchanges=3):
    """
    Simulate a natural conversation between a student and AI tutor
    
    Args:
        student_user: User object for the student
        class_id: The class ID
        topic: The topic to discuss
        num_exchanges: Number of back-and-forth exchanges
    """
    student_name = student_user.first_name
    student_id = student_user.id
    conversation_history = []
    
    print(f"\n{'='*60}")
    print(f"🎓 {student_name} learning about: {topic}")
    print(f"{'='*60}\n")
    
    ai_response = None
    
    for i in range(num_exchanges):
        # Student asks a question
        question = generate_student_question(
            student_name, 
            topic, 
            conversation_history,
            ai_response
        )
        
        print(f"👤 {student_name}: {question}")
        conversation_history.append({"role": "student", "content": question})
        
        # AI tutor responds
        try:
            ai_response = ai_service.generate_response(question, student_id, class_id)
            print(f"🤖 AI Tutor: {ai_response[:200]}...")
            conversation_history.append({"role": "tutor", "content": ai_response})
            
            # Wait a bit to simulate natural conversation pace
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Error getting AI response: {e}")
            break
    
    print(f"\n✅ Completed {len(conversation_history)//2} exchanges for {student_name}\n")
    return conversation_history

def run_simulation(num_topics_per_student=3, exchanges_per_topic=3):
    """
    Run the full simulation for all students
    
    Args:
        num_topics_per_student: How many topics each student should learn about
        exchanges_per_topic: How many Q&A exchanges per topic
    """
    with app.app_context():
        # Dynamically get simulated students from database
        students = get_simulated_students()
        
        if not students:
            print("Error: No simulated students found in database")
            print("Run create_simulated_students.py first")
            return
        
        # Get the class from any enrolled student (they should all be in the same class)
        first_student = next(iter(students.values()))
        if not first_student.classes:
            print("Error: Simulated students not enrolled in any class")
            print("Run create_simulated_students.py first")
            return
        
        class_obj = first_student.classes[0]
        class_id = class_obj.id
        
        print(f"\n🚀 Starting GPT Student Simulation")
        print(f"📚 Class: {class_obj.name}")
        print(f"👥 Students: {', '.join(students.keys())}")
        print(f"📖 Topics per student: {num_topics_per_student}")
        print(f"💬 Exchanges per topic: {exchanges_per_topic}")
        print(f"\n{'='*60}\n")
        
        # Run simulation for each student
        for student_name, student_user in students.items():
            print(f"\n🎯 Simulating {student_name}'s learning journey...")
            
            # Select topics based on student's interests
            persona = STUDENT_PERSONAS[student_name]
            topics = persona["topics_of_interest"][:num_topics_per_student]
            
            for topic in topics:
                try:
                    simulate_conversation(
                        student_user,
                        class_id,
                        topic,
                        exchanges_per_topic
                    )
                    time.sleep(1)  # Brief pause between topics
                except Exception as e:
                    print(f"❌ Error simulating {student_name} on {topic}: {e}")
                    continue
        
        print(f"\n{'='*60}")
        print(f"✨ Simulation Complete!")
        print(f"{'='*60}")
        print(f"\n📊 Check the database for:")
        print(f"   - ChatMessage records")
        print(f"   - AIInteraction records")
        print(f"   - TokenUsage records")
        print(f"\n🎯 Next steps:")
        print(f"   1. View student dashboards to see their interactions")
        print(f"   2. Check teacher AI insights to see pattern detection")
        print(f"   3. Verify AI system adapts to each student's learning style")
        print()

if __name__ == '__main__':
    import sys
    
    # Parse command line arguments
    num_topics = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    num_exchanges = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    
    run_simulation(num_topics_per_student=num_topics, exchanges_per_topic=num_exchanges)
