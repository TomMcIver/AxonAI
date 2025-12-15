#!/usr/bin/env python3
"""
Smoke Test for AxonAI Demo
Run this to verify the demo loop is working
"""

import requests
import sys

BASE_URL = "http://localhost:5000"

def test_login(session):
    """Test login with a student account"""
    print("Testing login...")
    response = session.post(f"{BASE_URL}/login", data={
        'role': 'student',
        'user_id': '1'
    }, allow_redirects=False)
    
    if response.status_code in [200, 302]:
        print("  Login: OK")
        return True
    else:
        print(f"  Login: FAILED ({response.status_code})")
        return False

def test_mastery_endpoint(session):
    """Test the mastery API endpoint"""
    print("Testing mastery API...")
    response = session.get(f"{BASE_URL}/api/student/mastery")
    
    if response.status_code == 200:
        data = response.json()
        if 'success' in data:
            print("  Mastery API: OK")
            print(f"    Mastery data: {data.get('mastery', {})}")
            return True
    
    print(f"  Mastery API: FAILED ({response.status_code})")
    return False

def test_quiz_generate(session, class_id=1):
    """Test quiz generation endpoint"""
    print("Testing quiz generation...")
    response = session.post(f"{BASE_URL}/api/quiz/generate", json={
        'class_id': class_id,
        'num_questions': 3
    })
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("  Quiz Generation: OK")
            print(f"    Quiz ID: {data.get('quiz_id')}")
            print(f"    Questions: {data.get('num_questions')}")
            return data.get('quiz_id'), data.get('questions', [])
    
    print(f"  Quiz Generation: FAILED ({response.status_code})")
    if response.status_code == 200:
        print(f"    Error: {response.json().get('error')}")
    return None, []

def test_quiz_submit(session, quiz_id, questions):
    """Test quiz submission endpoint"""
    print("Testing quiz submission...")
    
    answers = []
    for q in questions:
        if q.get('choices'):
            answers.append(q['choices'][0])
        else:
            answers.append('')
    
    response = session.post(f"{BASE_URL}/api/quiz/submit", json={
        'quiz_id': quiz_id,
        'answers': answers
    })
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("  Quiz Submission: OK")
            print(f"    Score: {data.get('score', 0):.1f}%")
            print(f"    Correct: {data.get('correct')}/{data.get('total')}")
            return True
    
    print(f"  Quiz Submission: FAILED ({response.status_code})")
    return False

def test_chat_endpoint(session, class_id=1):
    """Test chat endpoint"""
    print("Testing chat API...")
    response = session.post(f"{BASE_URL}/api/chat", json={
        'class_id': class_id,
        'message': 'What is 2+2?'
    })
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success') or data.get('response'):
            print("  Chat API: OK")
            resp_text = data.get('response', '')[:50]
            print(f"    Response preview: {resp_text}...")
            return True
    
    print(f"  Chat API: FAILED ({response.status_code})")
    return False

def run_smoke_test():
    """Run all smoke tests"""
    print("=" * 50)
    print("AxonAI Demo Smoke Test")
    print("=" * 50)
    
    session = requests.Session()
    
    all_passed = True
    
    if not test_login(session):
        print("\nLogin failed - cannot continue tests")
        return False
    
    if not test_mastery_endpoint(session):
        all_passed = False
    
    quiz_id, questions = test_quiz_generate(session)
    if quiz_id:
        if not test_quiz_submit(session, quiz_id, questions):
            all_passed = False
        if not test_mastery_endpoint(session):
            all_passed = False
    else:
        all_passed = False
    
    if not test_chat_endpoint(session):
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
    print("=" * 50)
    
    return all_passed

if __name__ == "__main__":
    success = run_smoke_test()
    sys.exit(0 if success else 1)
