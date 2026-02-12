import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def test_health():
    try:
        resp = requests.get(f"{BASE_URL}/health")
        if resp.status_code == 200:
            print("✅ Health Check Passed")
        else:
            print(f"❌ Health Check Failed: {resp.status_code}")
    except Exception as e:
        print(f"❌ Health Check Error: {e}")
 
def test_auth():
    # Register
    reg_data = {
        "email": "test@example.com",
        "password": "password123",
        "full_name": "Test User",
        "role": "user"
    }
    # Note: Adjust logic if user already exists
    try:
        resp = requests.post(f"{BASE_URL}/register", json=reg_data)
        if resp.status_code in [200, 201]:
             print("✅ Registration Passed")
        elif resp.status_code == 400 and "already registered" in resp.text:
             print("✅ Registration Skipped (User exists)")
        else:
             print(f"❌ Registration Failed: {resp.status_code} - {resp.text}")

        # Login
        login_data = {
            "username": "test@example.com",
            "password": "password123"
        }
        resp = requests.post(f"{BASE_URL}/token", data=login_data)
        if resp.status_code == 200:
            token = resp.json()["access_token"]
            print("✅ Login Passed")
            return token
        else:
            print(f"❌ Login Failed: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        print(f"❌ Auth Error: {e}")
        return None

def test_emergency(token):
    if not token:
        print("⚠️ Skipping Emergency Test (No Token)")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.post(f"{BASE_URL}/emergency/trigger", headers=headers)
        if resp.status_code == 200:
            print("✅ Emergency Trigger Passed")
        else:
            print(f"❌ Emergency Trigger Failed: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"❌ Emergency Error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Local API Tests...")
    test_health()
    token = test_auth()
    test_emergency(token)
