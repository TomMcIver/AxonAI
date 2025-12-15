#!/usr/bin/env python3
"""
Complete end-to-end test of all three agents with GPT integration
"""

from main_tutor_agent import MainTutorAgent
from mastery_tracking_agent import MasteryTrackingAgent
from quiz_builder_agent import QuizBuilderAgent

def test_complete_system():
    print("=" * 70)
    print("COMPLETE AI TUTORING SYSTEM TEST - With GPT Integration")
    print("=" * 70)
    
    # Initialize all three agents
    tutor = MainTutorAgent()
    tracker = MasteryTrackingAgent()
    quiz_builder = QuizBuilderAgent()
    
    # Test 1: Create student
    print("\n📝 STEP 1: Creating Student Profile")
    student_id = tutor.create_student("Emma Watson", "Science")
    
    # Test 2: GPT-powered chat conversation
    print("\n💬 STEP 2: AI-Powered Learning Conversation")
    
    print("\n  Student: What is photosynthesis?")
    response1 = tutor.generate_response(student_id, "What is photosynthesis?")
    print(f"  AI Tutor: {response1[:150]}...")
    
    print("\n  Student: That's helpful! Can you explain the role of chlorophyll?")
    response2 = tutor.generate_response(student_id, "That's helpful! Can you explain the role of chlorophyll?")
    print(f"  AI Tutor: {response2[:150]}...")
    
    print("\n  Student: I understand now! So it's like the green pigment that captures sunlight?")
    response3 = tutor.generate_response(student_id, "I understand now! So it's like the green pigment that captures sunlight?")
    print(f"  AI Tutor: {response3[:150]}...")
    
    # Test 3: Mastery tracking analysis
    print("\n\n📊 STEP 3: Analyzing Student Mastery")
    tracker.update_student_mastery(student_id)
    report = tracker.get_mastery_report(student_id)
    
    print(f"\n  Learning Trend: {report['trend'].upper()}")
    print(f"  Understanding Score: {report['understanding_score']:.1f}/10.0")
    if report['mastery_levels']:
        print(f"  Topics Identified:")
        for topic, data in report['mastery_levels'].items():
            print(f"    - {topic.capitalize()}: {data['percentage']}% mastery ({data['interactions']} interactions)")
    
    # Test 4: Generate adaptive quiz
    print("\n\n🎯 STEP 4: Generating Adaptive Quiz")
    weak_topics = quiz_builder.get_weakest_topics(student_id, limit=3)
    print(f"  Weakest Topics: {[t[0] for t in weak_topics]}")
    
    quiz_id = quiz_builder.generate_quiz(student_id, num_questions=3)
    quiz = quiz_builder.get_quiz(quiz_id)
    
    print(f"\n  Generated Quiz (ID: {quiz_id}) - Topic: {quiz['topic']}")
    print(f"  Questions:")
    for i, q in enumerate(quiz['questions'], 1):
        print(f"    {i}. {q['q']}")
    
    # Test 5: Submit quiz answers
    print("\n\n✅ STEP 5: Submitting Quiz Answers")
    sample_answers = [quiz['questions'][i]['a'] for i in range(len(quiz['questions']))]
    results = quiz_builder.submit_quiz(quiz_id, sample_answers)
    
    print(f"  Score: {results['score']:.1f}%")
    print(f"  Correct: {results['correct']}/{results['total']}")
    print(f"  Understanding Score Updated: {results['old_understanding']:.1f} → {results['new_understanding']:.1f}")
    
    # Test 6: Final profile
    print("\n\n👤 STEP 6: Final Student Profile")
    profile = tutor.get_student_profile(student_id)
    print(f"\n  Name: {profile['name']}")
    print(f"  Subject: {profile['subject']}")
    print(f"  Understanding Score: {profile['understanding_score']:.1f}/10.0")
    print(f"  Total Chat Interactions: {len(profile['chat_history'])}")
    
    print("\n" + "=" * 70)
    print("✅ ALL THREE AGENTS WORKING TOGETHER WITH GPT INTEGRATION!")
    print("=" * 70)

if __name__ == "__main__":
    test_complete_system()
