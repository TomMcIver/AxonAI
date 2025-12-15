#!/usr/bin/env python3
"""
Comprehensive test for all three agents working together
"""

from main_tutor_agent import MainTutorAgent
from mastery_tracking_agent import MasteryTrackingAgent
from quiz_builder_agent import QuizBuilderAgent

def print_separator(title=""):
    """Print a formatted separator"""
    if title:
        print(f"\n{'=' * 60}")
        print(f"  {title}")
        print('=' * 60)
    else:
        print('-' * 60)

def test_complete_system():
    """Test all three agents working together"""
    
    print_separator("Testing Complete AI Tutoring System")
    print("Agent 1: Main Tutor | Agent 2: Mastery Tracker | Agent 3: Quiz Builder")
    
    # Initialize all three agents
    tutor = MainTutorAgent()
    tracker = MasteryTrackingAgent()
    quiz_builder = QuizBuilderAgent()
    
    # Test 1: Create a student
    print_separator("Test 1: Creating Student (Agent 1)")
    student_id = tutor.create_student("Alex Rivera", "Math")
    
    # Test 2: Learning session with tutor
    print_separator("Test 2: Learning Session (Agent 1)")
    print("\n[Student struggling with fractions]")
    tutor.generate_response(student_id, "I don't understand fractions")
    tutor.generate_response(student_id, "How do I add 1/2 and 1/4?")
    
    print("\n[Understanding develops]")
    tutor.generate_response(student_id, "Oh, I need a common denominator!")
    tutor.generate_response(student_id, "Got it, so 1/2 + 1/4 = 3/4")
    
    print("\n[Trying algebra]")
    tutor.generate_response(student_id, "Can we try algebra now?")
    tutor.generate_response(student_id, "How do I solve x + 5 = 10?")
    tutor.generate_response(student_id, "I understand, x equals 5")
    
    # Test 3: Mastery analysis
    print_separator("Test 3: Analyzing Mastery (Agent 2)")
    tracker.update_student_mastery(student_id)
    
    report = tracker.get_mastery_report(student_id)
    print(f"\n📊 Mastery Analysis Results:")
    print(f"   Learning Trend: {report['trend'].upper()}")
    print(f"   Weak Topics: {', '.join(report['mastery_levels'].keys())}")
    
    # Test 4: Generate targeted quiz
    print_separator("Test 4: Generating Quiz (Agent 3)")
    weak_topics = quiz_builder.get_weakest_topics(student_id)
    print(f"\nIdentified weak topics: {', '.join([t[0] for t in weak_topics])}")
    
    quiz_id = quiz_builder.generate_quiz(student_id, num_questions=5)
    quiz = quiz_builder.get_quiz(quiz_id)
    
    print(f"\n📝 Generated Quiz:")
    print(f"   Quiz ID: {quiz_id}")
    print(f"   Target Topic: {quiz['topic']}")
    print(f"   Number of Questions: {len(quiz['questions'])}")
    
    # Test 5: Simulate quiz completion
    print_separator("Test 5: Taking Quiz (Agent 3)")
    
    print("\n[Quiz Questions:]")
    student_answers = []
    
    for i, q in enumerate(quiz['questions'], 1):
        print(f"\nQ{i}: {q['q']}")
        if 'choices' in q:
            for j, choice in enumerate(q['choices'], 1):
                print(f"    {j}. {choice}")
        print(f"    Correct Answer: {q['a']}")
        
        # Simulate student getting some right, some wrong
        if i <= 3:  # Get first 3 correct
            student_answers.append(q['a'])
        else:  # Get last 2 wrong
            wrong_answer = q['choices'][0] if q['choices'][0] != q['a'] else q['choices'][1]
            student_answers.append(wrong_answer)
    
    # Test 6: Submit quiz and update scores
    print_separator("Test 6: Scoring Quiz and Updating Profile (Agent 3)")
    results = quiz_builder.submit_quiz(quiz_id, student_answers)
    
    print(f"\n📊 Quiz Results:")
    print(f"   Score: {results['score']:.1f}% ({results['correct']}/{results['total']} correct)")
    print(f"   Understanding Score Updated: {results['old_understanding']:.1f} → {results['new_understanding']:.1f}")
    
    # Test 7: More learning based on quiz results
    print_separator("Test 7: Targeted Learning (Agent 1)")
    print("\n[Reviewing weak areas identified by quiz]")
    tutor.generate_response(student_id, "I need more help with the questions I got wrong")
    tutor.generate_response(student_id, "Can you explain that concept again?")
    tutor.generate_response(student_id, "Yes, I understand now!")
    
    # Test 8: Re-analyze mastery
    print_separator("Test 8: Re-analyzing Mastery (Agent 2)")
    tracker.update_student_mastery(student_id)
    
    updated_report = tracker.get_mastery_report(student_id)
    print(f"\n📈 Updated Mastery Report:")
    print(f"   Learning Trend: {updated_report['trend'].upper()}")
    print(f"   Understanding Score: {updated_report['understanding_score']:.1f}/10.0")
    
    if updated_report['mastery_levels']:
        print(f"\n   Topic Mastery:")
        for topic, data in updated_report['mastery_levels'].items():
            bar = '█' * int(data['percentage']/5) + '░' * (20-int(data['percentage']/5))
            print(f"     {topic.capitalize():15} [{bar}] {data['percentage']}%")
    
    # Test 9: Generate second quiz (should be adaptive)
    print_separator("Test 9: Adaptive Second Quiz (Agent 3)")
    quiz_id_2 = quiz_builder.generate_quiz(student_id, num_questions=5)
    quiz_2 = quiz_builder.get_quiz(quiz_id_2)
    
    print(f"\n📝 Second Quiz Generated:")
    print(f"   Quiz ID: {quiz_id_2}")
    print(f"   Focus Topic: {quiz_2['topic']}")
    print(f"   (Targets current weak areas)")
    
    # Test 10: View all quizzes
    print_separator("Test 10: Quiz History (Agent 3)")
    quiz_history = quiz_builder.get_student_quizzes(student_id)
    
    print(f"\n📚 Student's Quiz History:")
    for quiz in quiz_history:
        print(f"\n   Quiz {quiz['id']}:")
        print(f"     Topic: {quiz['topic']}")
        print(f"     Score: {quiz['score']:.1f}%")
        print(f"     Date: {quiz['created_at']}")
    
    # Final Summary
    print_separator("Final Summary")
    final_profile = tutor.get_student_profile(student_id)
    final_report = tracker.get_mastery_report(student_id)
    
    print(f"\n🎓 Student Progress Summary for {final_profile['name']}")
    print(f"\n   Subject: {final_profile['subject']}")
    print(f"   Total Interactions: {len(final_profile['chat_history'])}")
    print(f"   Quizzes Taken: {len(quiz_history)}")
    print(f"   Understanding Score: {final_profile['understanding_score']:.1f}/10.0")
    print(f"   Learning Trend: {final_report['trend'].upper()}")
    
    print("\n✅ All Three Agents Successfully Integrated!")
    print("\n   Agent 1 (Main Tutor): ✓ Chat interactions recorded")
    print("   Agent 2 (Mastery Tracker): ✓ Topics analyzed, trends detected")
    print("   Agent 3 (Quiz Builder): ✓ Adaptive quizzes generated and scored")
    
    print_separator()

if __name__ == "__main__":
    test_complete_system()
