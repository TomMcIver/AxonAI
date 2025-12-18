#!/usr/bin/env python3
"""
Smoke Test Script for ML API and Database Connection
Verifies that the application can connect to all required services.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_database_connection():
    """Test database connection."""
    print("\n[1/4] Testing Database Connection...")
    try:
        from app import app, db
        with app.app_context():
            result = db.session.execute(db.text("SELECT 1")).scalar()
            if result == 1:
                print("  ✓ Database connection successful")
                
                from models import User
                user_count = User.query.count()
                print(f"  ✓ Database query successful (found {user_count} users)")
                return True
            else:
                print("  ✗ Database returned unexpected result")
                return False
    except Exception as e:
        print(f"  ✗ Database connection failed: {e}")
        return False


def test_ml_api_health():
    """Test ML API health endpoint."""
    print("\n[2/4] Testing ML API Health...")
    try:
        from services.ml_api_client import get_ml_api_client, is_ml_api_configured
        
        if not is_ml_api_configured():
            print("  ⚠ ML API not configured (ML_API_BASE_URL or AXON_SERVICE_KEY missing)")
            print("    Set these environment variables to enable remote ML services")
            return None
        
        client = get_ml_api_client()
        result = client.health_check()
        
        if result.get('status') == 'healthy':
            print("  ✓ ML API is healthy")
            return True
        else:
            print(f"  ✗ ML API health check failed: {result}")
            return False
    except Exception as e:
        print(f"  ✗ ML API health check error: {e}")
        return False


def test_mastery_prediction():
    """Test mastery prediction endpoint."""
    print("\n[3/4] Testing Mastery Prediction...")
    try:
        from services.ml_api_client import get_ml_api_client, is_ml_api_configured
        
        if not is_ml_api_configured():
            print("  ⚠ Skipped (ML API not configured)")
            return None
        
        client = get_ml_api_client()
        
        result = client.predict_mastery(
            student_id=1,
            skill="algebra",
            class_id=1
        )
        
        if 'p_mastery' in result:
            print(f"  ✓ Mastery prediction successful: p_mastery={result['p_mastery']:.3f}")
            return True
        else:
            print(f"  ✗ Unexpected response format: {result}")
            return False
            
    except Exception as e:
        print(f"  ✗ Mastery prediction failed: {e}")
        return False


def test_risk_scoring():
    """Test risk scoring endpoint."""
    print("\n[4/4] Testing Risk Scoring...")
    try:
        from services.ml_api_client import get_ml_api_client, is_ml_api_configured
        
        if not is_ml_api_configured():
            print("  ⚠ Skipped (ML API not configured)")
            return None
        
        client = get_ml_api_client()
        
        result = client.predict_risk(
            student_id=1,
            class_id=1
        )
        
        if 'p_risk' in result and 'risk_level' in result:
            print(f"  ✓ Risk prediction successful: p_risk={result['p_risk']:.3f}, level={result['risk_level']}")
            return True
        else:
            print(f"  ✗ Unexpected response format: {result}")
            return False
            
    except Exception as e:
        print(f"  ✗ Risk scoring failed: {e}")
        return False


def test_bandit_selection():
    """Test bandit strategy selection endpoint."""
    print("\n[5/5] Testing Bandit Strategy Selection...")
    try:
        from services.ml_api_client import get_ml_api_client, is_ml_api_configured
        
        if not is_ml_api_configured():
            print("  ⚠ Skipped (ML API not configured)")
            return None
        
        client = get_ml_api_client()
        
        result = client.select_strategy(
            student_id=1,
            class_id=1,
            bandit_type="linucb"
        )
        
        if 'strategy' in result:
            print(f"  ✓ Bandit selection successful: strategy={result['strategy']}")
            return True
        else:
            print(f"  ✗ Unexpected response format: {result}")
            return False
            
    except Exception as e:
        print(f"  ✗ Bandit selection failed: {e}")
        return False


def main():
    """Run all smoke tests."""
    print("=" * 60)
    print("AxonAI Smoke Test Suite")
    print("=" * 60)
    
    results = {
        'database': test_database_connection(),
        'ml_health': test_ml_api_health(),
        'mastery': test_mastery_prediction(),
        'risk': test_risk_scoring(),
        'bandit': test_bandit_selection(),
    }
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v is True)
    skipped = sum(1 for v in results.values() if v is None)
    failed = sum(1 for v in results.values() if v is False)
    
    print(f"  Passed:  {passed}")
    print(f"  Skipped: {skipped}")
    print(f"  Failed:  {failed}")
    
    if failed > 0:
        print("\n⚠ Some tests failed. Check the output above for details.")
        return 1
    elif skipped > 0 and passed == 1:
        print("\n✓ Database connection successful. ML API tests skipped (not configured).")
        print("  To enable ML API tests, set ML_API_BASE_URL and AXON_SERVICE_KEY.")
        return 0
    else:
        print("\n✓ All tests passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
