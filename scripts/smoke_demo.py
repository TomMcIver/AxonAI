#!/usr/bin/env python3
"""
Smoke Test for AxonAI Demo
Run this to verify the demo loop and P0/P1 features are working
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5000"
DEFAULT_CLASS_ID = 17  # Mathematics - Year 12

def print_json(data, title=None):
    if title:
        print(f"    {title}:")
    print(json.dumps(data, indent=2, default=str)[:500])

def test_login(session, user_type='student'):
    """Test login with a user account"""
    print(f"Testing login as {user_type}...")
    response = session.post(f"{BASE_URL}/login", data={
        'user_type': user_type
    }, allow_redirects=False)
    
    if response.status_code in [200, 302]:
        print(f"  Login as {user_type}: OK")
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

def test_quiz_generate(session, class_id=DEFAULT_CLASS_ID):
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

def test_chat_endpoint(session, class_id=DEFAULT_CLASS_ID):
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

def test_scope_lock(session, class_id=DEFAULT_CLASS_ID):
    """P0: Test scope lock blocks off-topic requests"""
    print("Testing scope lock (P0)...")
    response = session.post(f"{BASE_URL}/api/tutor/chat", json={
        'class_id': class_id,
        'message': 'Give me a recipe for chocolate cake'
    })
    
    if response.status_code == 200:
        data = response.json()
        if data.get('blocked') == True:
            print("  Scope Lock: OK")
            print(f"    Blocked reason: {data.get('blocked_reason', '')[:50]}...")
            return True
        else:
            print("  Scope Lock: FAILED (request was not blocked)")
    else:
        print(f"  Scope Lock: FAILED ({response.status_code})")
    return False

def test_plan_metadata(session, class_id=DEFAULT_CLASS_ID):
    """P2: Test plan metadata in response"""
    print("Testing plan metadata (P2)...")
    response = session.post(f"{BASE_URL}/api/tutor/chat", json={
        'class_id': class_id,
        'message': 'Help me solve 2x + 5 = 15'
    })
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success') and 'plan' in data:
            plan = data['plan']
            print("  Plan Metadata: OK")
            print(f"    Strategy: {plan.get('strategy')}")
            print(f"    Difficulty: {plan.get('difficulty')}")
            print(f"    Sub-topic: {plan.get('sub_topic')}")
            return True
        else:
            print("  Plan Metadata: FAILED (no plan in response)")
    else:
        print(f"  Plan Metadata: FAILED ({response.status_code})")
    return False

def test_unified_chat_fields(session, class_id=DEFAULT_CLASS_ID):
    """P0: Test unified chat has blocked/subject fields"""
    print("Testing unified chat fields (P0)...")
    response = session.post(f"{BASE_URL}/api/chat", json={
        'class_id': class_id,
        'message': 'What is algebra?'
    })
    
    if response.status_code == 200:
        data = response.json()
        if 'blocked' in data and 'subject' in data:
            print("  Unified Chat Fields: OK")
            print(f"    Blocked: {data.get('blocked')}")
            print(f"    Subject: {data.get('subject')}")
            return True
        else:
            print("  Unified Chat Fields: FAILED (missing blocked/subject)")
    else:
        print(f"  Unified Chat Fields: FAILED ({response.status_code})")
    return False

def test_chat_history_format(session, class_id=DEFAULT_CLASS_ID):
    """P0: Test chat history returns JSON-safe dicts"""
    print("Testing chat history format (P0)...")
    response = session.get(f"{BASE_URL}/api/chat/history/{class_id}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            messages = data.get('messages', [])
            if messages:
                first_msg = messages[0]
                if isinstance(first_msg.get('created_at'), str) and 'T' in first_msg.get('created_at', ''):
                    print("  Chat History Format: OK (ISO timestamps)")
                    return True
                else:
                    print("  Chat History Format: PARTIAL (no ISO timestamp)")
            else:
                print("  Chat History Format: OK (empty history)")
                return True
        else:
            print("  Chat History Format: FAILED")
    else:
        print(f"  Chat History Format: FAILED ({response.status_code})")
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
    
    print("\n--- P0/P1/P2 Feature Tests ---")
    
    if not test_scope_lock(session):
        all_passed = False
    
    if not test_plan_metadata(session):
        all_passed = False
    
    if not test_unified_chat_fields(session):
        all_passed = False
    
    if not test_chat_history_format(session):
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
