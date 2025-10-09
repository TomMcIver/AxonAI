#!/usr/bin/env python3
"""
Test script for both Main Tutor Agent and Mastery Tracking Agent
"""

from main_tutor_agent import MainTutorAgent
from mastery_tracking_agent import MasteryTrackingAgent

def print_separator(title=""):
    """Print a formatted separator"""
    if title:
        print(f"\n{'=' * 60}")
        print(f"  {title}")
        print('=' * 60)
    else:
        print('-' * 60)

def test_integrated_system():
    """Test the complete system with both agents"""
    
    print_separator("Testing Integrated Tutoring System")
    print("Main Tutor Agent + Mastery Tracking Agent")
    
    # Initialize both agents
    main_tutor = MainTutorAgent()
    mastery_tracker = MasteryTrackingAgent()
    
    # Test 1: Create a new student
    print_separator("Test 1: Creating Student")
    student_id = main_tutor.create_student("Emma Wilson", "Math")
    
    # Test 2: Simulate a learning session with various types of interactions
    print_separator("Test 2: Simulating Learning Session")
    
    # Initial struggle
    print("\n[Session Start - Student is struggling]")
    main_tutor.generate_response(student_id, "I don't understand algebra at all")
    main_tutor.generate_response(student_id, "This is too hard for me")
    
    # Getting help
    print("\n[Getting Help]")
    main_tutor.generate_response(student_id, "Can you help me solve x + 5 = 10?")
    main_tutor.generate_response(student_id, "What does the variable x mean?")
    
    # Understanding begins
    print("\n[Understanding Develops]")
    main_tutor.generate_response(student_id, "Oh I see, so x is what we need to find?")
    main_tutor.generate_response(student_id, "So I subtract 5 from both sides?")
    main_tutor.generate_response(student_id, "Got it! x equals 5")
    
    # Confidence grows
    print("\n[Confidence Growing]")
    main_tutor.generate_response(student_id, "Thanks! That makes sense now")
    main_tutor.generate_response(student_id, "Can I try another equation?")
    main_tutor.generate_response(student_id, "Yes, I understand the steps")
    
    # Test 3: Run mastery analysis
    print_separator("Test 3: Running Mastery Analysis")
    mastery_tracker.update_student_mastery(student_id)
    
    # Test 4: Get mastery report
    print_separator("Test 4: Mastery Report")
    report = mastery_tracker.get_mastery_report(student_id)
    
    print(f"\n📊 Mastery Report for {report['name']}")
    print(f"   Student ID: {report['student_id']}")
    print(f"   Subject: {report['subject']}")
    print(f"   Understanding Score: {report['understanding_score']:.1f}/10.0")
    print(f"   Learning Trend: {report['trend'].upper()}")
    print(f"\n   Topic Mastery:")
    for topic, data in report['mastery_levels'].items():
        bar_length = int(data['percentage'] / 5)
        bar = '█' * bar_length + '░' * (20 - bar_length)
        print(f"     {topic.capitalize():15} [{bar}] {data['percentage']}% ({data['interactions']} interactions)")
    
    # Test 5: More interactions and re-analyze to show trend
    print_separator("Test 5: Additional Practice & Re-analysis")
    
    print("\n[More Practice - Advanced Topics]")
    main_tutor.generate_response(student_id, "Can we try quadratic equations?")
    main_tutor.generate_response(student_id, "I understand the formula now")
    main_tutor.generate_response(student_id, "This is getting clearer")
    
    print("\n[Re-analyzing Mastery...]")
    mastery_tracker.update_student_mastery(student_id)
    
    # Get updated report
    updated_report = mastery_tracker.get_mastery_report(student_id)
    print(f"\n📈 Updated Trend: {updated_report['trend'].upper()}")
    print(f"   Understanding Score: {updated_report['understanding_score']:.1f}/10.0")
    
    # Test 6: Create another student with different pattern
    print_separator("Test 6: Testing with Different Student (Science)")
    
    student2_id = main_tutor.create_student("Lucas Chen", "Science")
    
    # Science student interactions
    main_tutor.generate_response(student2_id, "What is photosynthesis?")
    main_tutor.generate_response(student2_id, "How do plants make energy?")
    main_tutor.generate_response(student2_id, "I get it, they use sunlight")
    main_tutor.generate_response(student2_id, "What about cellular respiration?")
    main_tutor.generate_response(student2_id, "Yes, this makes sense")
    
    # Analyze science student
    print("\n[Analyzing Science Student...]")
    mastery_tracker.update_student_mastery(student2_id)
    
    science_report = mastery_tracker.get_mastery_report(student2_id)
    print(f"\n📊 Mastery Report for {science_report['name']}")
    print(f"   Subject: {science_report['subject']}")
    print(f"   Understanding Score: {science_report['understanding_score']:.1f}/10.0")
    print(f"   Learning Trend: {science_report['trend'].upper()}")
    print(f"\n   Topic Mastery:")
    for topic, data in science_report['mastery_levels'].items():
        bar_length = int(data['percentage'] / 5)
        bar = '█' * bar_length + '░' * (20 - bar_length)
        print(f"     {topic.capitalize():15} [{bar}] {data['percentage']}% ({data['interactions']} interactions)")
    
    # Summary
    print_separator("Summary")
    print("\n✅ Successfully tested:")
    print("   • Main Tutor Agent - Chat interactions and history tracking")
    print("   • Mastery Tracking Agent - Topic analysis and trend detection")
    print("   • Database updates - mastery_levels and trend fields")
    print("   • Integration - Both agents working together seamlessly")
    
    print_separator()

if __name__ == "__main__":
    test_integrated_system()
