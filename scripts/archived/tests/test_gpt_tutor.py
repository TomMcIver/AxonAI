#!/usr/bin/env python3
"""
Test GPT-powered Main Tutor Agent
"""

from main_tutor_agent import MainTutorAgent

def test_gpt_tutor():
    print("=" * 60)
    print("Testing GPT-Powered Main Tutor Agent")
    print("=" * 60)
    
    tutor = MainTutorAgent()
    
    # Create a student
    print("\n📝 Creating Student...")
    student_id = tutor.create_student("Test Student", "Math")
    
    # Test 1: Ask for help with a math problem
    print("\n📚 Test 1: Math Question")
    print("\nStudent: How do I solve quadratic equations?")
    response = tutor.generate_response(student_id, "How do I solve quadratic equations?")
    print(f"AI Tutor: {response}")
    
    # Test 2: Follow-up question
    print("\n📚 Test 2: Follow-up Question")
    print("\nStudent: Can you give me an example?")
    response = tutor.generate_response(student_id, "Can you give me an example?")
    print(f"AI Tutor: {response}")
    
    # Test 3: Student shows understanding
    print("\n📚 Test 3: Student Understanding")
    print("\nStudent: I understand now! So I use the quadratic formula?")
    response = tutor.generate_response(student_id, "I understand now! So I use the quadratic formula?")
    print(f"AI Tutor: {response}")
    
    # Check profile
    print("\n" + "=" * 60)
    print("Student Profile After AI Chat")
    print("=" * 60)
    profile = tutor.get_student_profile(student_id)
    print(f"\nName: {profile['name']}")
    print(f"Subject: {profile['subject']}")
    print(f"Understanding Score: {profile['understanding_score']:.1f}/10.0")
    print(f"Total Interactions: {len(profile['chat_history'])}")
    
    print("\n✅ GPT-powered tutor is working!")
    print("=" * 60)

if __name__ == "__main__":
    test_gpt_tutor()
