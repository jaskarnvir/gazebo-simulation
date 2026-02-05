import requests
import time
import random
import sys

# Configuration
API_URL = "http://127.0.0.1:8000"
ROBOT_ID = 1 # Assume we are robot #1
SERIAL_NUMBER = "MIRO-12345"

def register_if_needed():
    # In a real scenario, the robot wouldn't register itself this way, but for simulation:
    # We can't easily register without a user token. 
    # So we assume the user has already paired (registered) the robot via the App.
    print(f"Robot {SERIAL_NUMBER} starting up...")

def send_heartbeat(is_online: bool):
    try:
        url = f"{API_URL}/robots/{ROBOT_ID}/status?is_online={str(is_online).lower()}"
        response = requests.post(url)
        if response.status_code == 200:
            print(f"Heartbeat sent: Online={is_online}")
        else:
            print(f"Failed to send heartbeat: {response.status_code}")
    except Exception as e:
        print(f"Connection error: {e}")

def main():
    print("Starting Robot Simulation Bridge...")
    # Simulate connection to ROS
    print("Connecting to ROS Master... [MOCKED]")
    time.sleep(2)
    print("Connected to ROS.")
    
    # Main Loop
    try:
        while True:
            # Simulate some internal state check
            battery = random.randint(20, 100)
            print(f"Robot Status: Battery={battery}% | Sensors=OK")
            
            # Update Backend
            send_heartbeat(True)
            
            time.sleep(5)
    except KeyboardInterrupt:
        print("Shutting down...")
        send_heartbeat(False)

if __name__ == "__main__":
    main()
