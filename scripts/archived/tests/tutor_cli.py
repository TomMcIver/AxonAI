#!/usr/bin/env python3
"""
Simple CLI interface for the Main Tutor Agent
"""

from main_tutor_agent import MainTutorAgent
from mastery_tracking_agent import MasteryTrackingAgent
from quiz_builder_agent import QuizBuilderAgent
from database_setup import create_database
import os

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_profile(profile):
    """Print student profile in a formatted way"""
    print(f"\n📚 Student Profile:")
    print(f"   ID: {profile['id']}")
    print(f"   Name: {profile['name']}")
    print(f"   Subject: {profile['subject']}")
    print(f"   Understanding Score: {profile['understanding_score']:.1f}/10.0")
    print(f"   Last Interaction: {profile['last_interaction'] or 'Never'}")
    print(f"   Total Interactions: {len(profile['chat_history'])}")

def print_chat_history(history):
    """Print chat history in a formatted way"""
    if not history:
        print("\n💭 No chat history yet.")
        return
    
    print(f"\n💭 Chat History ({len(history)} interactions):")
    for i, interaction in enumerate(history, 1):
        print(f"\n   --- Interaction {i} ({interaction['timestamp']}) ---")
        print(f"   Student: {interaction['user']}")
        print(f"   Tutor: {interaction['tutor']}")

def print_mastery_report(report):
    """Print mastery report in a formatted way"""
    print(f"\n📊 Mastery Report for {report['name']}")
    print(f"   Student ID: {report['student_id']}")
    print(f"   Subject: {report['subject']}")
    print(f"   Understanding Score: {report['understanding_score']:.1f}/10.0")
    print(f"   Learning Trend: {report['trend'].upper()}")
    
    if report['mastery_levels']:
        print(f"\n   Topic Mastery:")
        for topic, data in report['mastery_levels'].items():
            bar_length = int(data['percentage'] / 5)
            bar = '█' * bar_length + '░' * (20 - bar_length)
            print(f"     {topic.capitalize():15} [{bar}] {data['percentage']}% ({data['interactions']} interactions)")
    else:
        print("\n   No mastery data available yet.")

def print_quiz_results(results):
    """Print quiz results in a formatted way"""
    print(f"\n📝 Quiz Results:")
    print(f"   Correct: {results['correct']}/{results['total']}")
    print(f"   Score: {results['score']:.1f}%")
    print(f"   Understanding Score: {results['old_understanding']:.1f} → {results['new_understanding']:.1f}")

def main():
    # Ensure database exists
    if not os.path.exists('school_ai.db'):
        print("📦 Creating database...")
        create_database()
    
    main_tutor = MainTutorAgent()
    mastery_tracker = MasteryTrackingAgent()
    quiz_builder = QuizBuilderAgent()
    
    print_header("🎓 AI Tutoring System - All Three Agents")
    
    while True:
        print("\n" + "-" * 60)
        print("MENU:")
        print("1. Create new student")
        print("2. Chat with student")
        print("3. View student profile")
        print("4. View chat history")
        print("5. Analyze mastery (run Mastery Tracking Agent)")
        print("6. View mastery report")
        print("7. Generate quiz (Quiz Builder Agent)")
        print("8. Take quiz")
        print("9. View quiz history")
        print("10. Exit")
        print("-" * 60)
        
        choice = input("\nEnter your choice (1-10): ").strip()
        
        if choice == '1':
            print_header("Create New Student")
            name = input("Enter student name: ").strip()
            subject = input("Enter subject (e.g., Math, Science, English, History): ").strip()
            
            if name and subject:
                student_id = main_tutor.create_student(name, subject)
                print(f"\n✅ Student created successfully! Student ID: {student_id}")
            else:
                print("\n❌ Name and subject are required!")
        
        elif choice == '2':
            print_header("Chat with Student")
            student_id = input("Enter student ID: ").strip()
            
            try:
                student_id = int(student_id)
                profile = main_tutor.get_student_profile(student_id)
                print_profile(profile)
                
                print("\n💬 Start chatting (type 'done' to finish):")
                
                while True:
                    user_message = input(f"\n{profile['name']}: ").strip()
                    
                    if user_message.lower() == 'done':
                        print("\n👋 Chat session ended.")
                        break
                    
                    if user_message:
                        response = main_tutor.generate_response(student_id, user_message)
                        print(f"Tutor: {response}")
                    else:
                        print("Please enter a message!")
            
            except ValueError as e:
                print(f"\n❌ Error: {e}")
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
        
        elif choice == '3':
            print_header("View Student Profile")
            student_id = input("Enter student ID: ").strip()
            
            try:
                student_id = int(student_id)
                profile = main_tutor.get_student_profile(student_id)
                print_profile(profile)
            except ValueError as e:
                print(f"\n❌ Error: {e}")
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
        
        elif choice == '4':
            print_header("View Chat History")
            student_id = input("Enter student ID: ").strip()
            
            try:
                student_id = int(student_id)
                profile = main_tutor.get_student_profile(student_id)
                print(f"\n📚 Student: {profile['name']} ({profile['subject']})")
                print_chat_history(profile['chat_history'])
            except ValueError as e:
                print(f"\n❌ Error: {e}")
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
        
        elif choice == '5':
            print_header("Analyze Mastery")
            student_id = input("Enter student ID: ").strip()
            
            try:
                student_id = int(student_id)
                mastery_tracker.update_student_mastery(student_id)
                print("\n✅ Mastery analysis completed!")
            except ValueError as e:
                print(f"\n❌ Error: {e}")
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
        
        elif choice == '6':
            print_header("View Mastery Report")
            student_id = input("Enter student ID: ").strip()
            
            try:
                student_id = int(student_id)
                report = mastery_tracker.get_mastery_report(student_id)
                print_mastery_report(report)
            except ValueError as e:
                print(f"\n❌ Error: {e}")
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
        
        elif choice == '7':
            print_header("Generate Quiz")
            student_id = input("Enter student ID: ").strip()
            
            try:
                student_id = int(student_id)
                num_questions = input("Number of questions (default 5): ").strip()
                num_questions = int(num_questions) if num_questions else 5
                
                quiz_id = quiz_builder.generate_quiz(student_id, num_questions)
                print(f"\n✅ Quiz generated! Quiz ID: {quiz_id}")
                print("   Use 'Take quiz' (option 8) to complete it.")
            except ValueError as e:
                print(f"\n❌ Error: {e}")
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
        
        elif choice == '8':
            print_header("Take Quiz")
            quiz_id = input("Enter quiz ID: ").strip()
            
            try:
                quiz_id = int(quiz_id)
                quiz = quiz_builder.get_quiz(quiz_id)
                
                print(f"\n📝 Quiz on {quiz['topic'].capitalize()}")
                print(f"   Questions: {len(quiz['questions'])}")
                print("\n" + "-" * 60)
                
                answers = []
                for i, question in enumerate(quiz['questions'], 1):
                    print(f"\nQuestion {i}: {question['q']}")
                    if 'choices' in question:
                        for j, choice in enumerate(question['choices'], 1):
                            print(f"   {j}. {choice}")
                    
                    answer = input("Your answer: ").strip()
                    answers.append(answer)
                
                # Submit quiz
                print("\n" + "-" * 60)
                print("Submitting quiz...")
                results = quiz_builder.submit_quiz(quiz_id, answers)
                print_quiz_results(results)
                
            except ValueError as e:
                print(f"\n❌ Error: {e}")
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
        
        elif choice == '9':
            print_header("View Quiz History")
            student_id = input("Enter student ID: ").strip()
            
            try:
                student_id = int(student_id)
                quizzes = quiz_builder.get_student_quizzes(student_id)
                
                if not quizzes:
                    print("\n📝 No quizzes found for this student.")
                else:
                    print(f"\n📝 Quiz History ({len(quizzes)} quizzes):")
                    for quiz in quizzes:
                        print(f"\n   Quiz ID: {quiz['id']}")
                        print(f"   Topic: {quiz['topic'].capitalize()}")
                        print(f"   Score: {quiz['score']:.1f}%")
                        print(f"   Date: {quiz['created_at']}")
            except ValueError as e:
                print(f"\n❌ Error: {e}")
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
        
        elif choice == '10':
            print_header("Goodbye!")
            print("Thank you for using the AI Tutoring System! 👋\n")
            break
        
        else:
            print("\n❌ Invalid choice! Please enter 1-10.")

if __name__ == "__main__":
    main()
