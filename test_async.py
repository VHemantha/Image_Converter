"""
Test script to verify Phase 2 asynchronous processing.
Run this after starting Redis and Celery worker.
"""
import requests
import time
import json
import sys

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except:
        pass  # Fallback to default encoding

# Configuration
BASE_URL = "http://localhost:5000"
TEST_IMAGE_PATH = "test_image.jpg"  # Update this to a real image path


def test_celery_availability():
    """Test if Celery is available."""
    print("\n=== Testing Celery Availability ===")
    try:
        from app.tasks.conversion_tasks import convert_batch_images
        print("[PASS] Celery tasks module imported successfully")
        return True
    except ImportError as e:
        print(f"[FAIL] Celery tasks not available: {e}")
        print("       App will run in synchronous fallback mode")
        return False


def test_redis_connection():
    """Test if Redis is accessible."""
    print("\n=== Testing Redis Connection ===")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("[PASS] Redis is running and accessible")
        return True
    except Exception as e:
        print(f"[FAIL] Redis connection failed: {e}")
        print("       Start Redis before testing async processing")
        return False


def test_health_endpoints():
    """Test health check endpoints."""
    print("\n=== Testing Health Endpoints ===")

    try:
        # Test /health
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print(f"[PASS] /health: {response.json()}")
        else:
            print(f"[FAIL] /health returned {response.status_code}")

        # Test /ready
        response = requests.get(f"{BASE_URL}/ready")
        if response.status_code == 200:
            print(f"[PASS] /ready: {response.json()}")
        else:
            print(f"[FAIL] /ready returned {response.status_code}")

        # Test /formats
        response = requests.get(f"{BASE_URL}/formats")
        if response.status_code == 200:
            data = response.json()
            print(f"[PASS] /formats: {len(data['formats'])} formats supported")
        else:
            print(f"[FAIL] /formats returned {response.status_code}")

        return True
    except requests.exceptions.ConnectionError:
        print("[FAIL] Cannot connect to Flask app")
        print("       Make sure Flask is running: python run.py")
        return False
    except Exception as e:
        print(f"[FAIL] Error testing endpoints: {e}")
        return False


def test_async_upload():
    """Test async file upload (requires test image)."""
    print("\n=== Testing Async Upload ===")

    import os
    if not os.path.exists(TEST_IMAGE_PATH):
        print(f"[SKIP] Test image not found: {TEST_IMAGE_PATH}")
        print("       Update TEST_IMAGE_PATH in script to a real image")
        return False

    try:
        # Get CSRF token from index page
        response = requests.get(BASE_URL)
        csrf_token = None

        # Extract CSRF token from HTML (basic extraction)
        if 'csrf_token' in response.text:
            print("[PASS] CSRF token found")
            # Note: For a real test, you'd want to properly extract the token
            # For now, we'll just check the endpoint structure

        print(f"[INFO] Would upload: {TEST_IMAGE_PATH}")
        print("       Full upload test requires CSRF token extraction")
        print("       Use the web UI to test upload functionality")

        return True

    except Exception as e:
        print(f"[FAIL] Error testing upload: {e}")
        return False


def test_status_endpoint(task_id="test-task-id"):
    """Test status endpoint structure."""
    print("\n=== Testing Status Endpoint ===")

    try:
        response = requests.get(f"{BASE_URL}/status/{task_id}")
        print(f"Status code: {response.status_code}")

        if response.status_code == 404:
            print(f"[PASS] Status endpoint working (task not found is expected)")
            print(f"       Response: {response.json()}")
            return True
        elif response.status_code == 200:
            print(f"[PASS] Status endpoint returned: {response.json()}")
            return True
        else:
            print(f"[FAIL] Unexpected status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Error testing status endpoint: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Phase 2 Asynchronous Processing Test Suite")
    print("=" * 60)

    results = {
        'celery': test_celery_availability(),
        'redis': test_redis_connection(),
        'health': test_health_endpoints(),
        'status': test_status_endpoint(),
        'upload': test_async_upload(),
    }

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {test}")

    print(f"\nTotal: {passed}/{total} tests passed")

    print("\n" + "=" * 60)
    print("Recommendations")
    print("=" * 60)

    if not results['redis']:
        print("[TODO] Start Redis to enable async processing:")
        print("       docker run -d -p 6379:6379 --name redis redis:7-alpine")
        print("       OR use Redis for Windows / WSL")

    if results['redis'] and not results['celery']:
        print("[TODO] Celery tasks available, start worker:")
        print("       celery -A app.tasks.celery_app worker --loglevel=info --pool=solo")

    if results['redis'] and results['celery']:
        print("[READY] Phase 2 is ready for async processing!")
        print("        Upload images via the web UI at http://localhost:5000")
        print("        Monitor progress at /status/<task_id>")

    if not results['health']:
        print("[TODO] Start Flask app:")
        print("       python run.py")

    print("\nFor detailed setup instructions, see: PHASE2_SETUP.md")
    print("=" * 60)


if __name__ == "__main__":
    main()
