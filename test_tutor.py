#!/usr/bin/env python3
"""
Test script for the Main Tutor Agent
"""

from main_tutor_agent import MainTutorAgent

def test_main_tutor():
    print("=" * 60)
    print("Testing Main Tutor Agent")
    print("=" * 60)
    
    agent = MainTutorAgent()
    
    # Test 1: Create students
    print("\n📝 TEST 1: Creating students...")
    student1_id = agent.create_student("Alice Johnson", "Math")
    student2_id = agent.create_student("Bob Smith", "Science")
    
    # Test 2: Generate responses and record interactions
    print("\n📝 TEST 2: Recording interactions...")
    
    # Alice's math session
    response1 = agent.generate_response(student1_id, "I need help with algebra")
    print(f"\nAlice: I need help with algebra")
    print(f"Tutor: {response1}")
    
    response2 = agent.generate_response(student1_id, "How do I solve x + 5 = 10?")
    print(f"\nAlice: How do I solve x + 5 = 10?")
    print(f"Tutor: {response2}")
    
    # Bob's science session
    response3 = agent.generate_response(student2_id, "What is photosynthesis?")
    print(f"\nBob: What is photosynthesis?")
    print(f"Tutor: {response3}")
    
    # Test 3: Get chat history
    print("\n📝 TEST 3: Getting chat history...")
    alice_history = agent.get_chat_history(student1_id)
    print(f"\nAlice's chat history has {len(alice_history)} interactions")
    for i, interaction in enumerate(alice_history, 1):
        print(f"\nInteraction {i}:")
        print(f"  User: {interaction['user']}")
        print(f"  Tutor: {interaction['tutor'][:80]}...")  # Truncate for readability
    
    # Test 4: Get student profile
    print("\n📝 TEST 4: Getting student profiles...")
    alice_profile = agent.get_student_profile(student1_id)
    bob_profile = agent.get_student_profile(student2_id)
    
    print(f"\n👤 Alice's Profile:")
    print(f"   ID: {alice_profile['id']}")
    print(f"   Name: {alice_profile['name']}")
    print(f"   Subject: {alice_profile['subject']}")
    print(f"   Understanding Score: {alice_profile['understanding_score']:.1f}/10.0")
    print(f"   Total Interactions: {len(alice_profile['chat_history'])}")
    print(f"   Last Interaction: {alice_profile['last_interaction']}")
    
    print(f"\n👤 Bob's Profile:")
    print(f"   ID: {bob_profile['id']}")
    print(f"   Name: {bob_profile['name']}")
    print(f"   Subject: {bob_profile['subject']}")
    print(f"   Understanding Score: {bob_profile['understanding_score']:.1f}/10.0")
    print(f"   Total Interactions: {len(bob_profile['chat_history'])}")
    print(f"   Last Interaction: {bob_profile['last_interaction']}")
    
    # Test 5: More interactions to increase understanding score
    print("\n📝 TEST 5: Testing understanding score progression...")
    print(f"Alice's current score: {alice_profile['understanding_score']:.1f}")
    
    for i in range(5):
        agent.generate_response(student1_id, f"Question {i+3}")
    
    alice_updated = agent.get_student_profile(student1_id)
    print(f"Alice's score after 5 more interactions: {alice_updated['understanding_score']:.1f}")
    print(f"Total interactions: {len(alice_updated['chat_history'])}")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    test_main_tutor()
