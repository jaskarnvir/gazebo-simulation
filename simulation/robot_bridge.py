import requests
import time
import cv2
import threading
import sys

# Configuration
# Use the Cloud Run URL or localhost if testing locally
API_URL = "http://34.172.64.198:8000" 
ROBOT_ID = 3 
SERIAL_NUMBER = "MIRO-12345"

def send_heartbeat(is_online: bool):
    try:
        url = f"{API_URL}/robots/{ROBOT_ID}/status?is_online={str(is_online).lower()}"
        response = requests.post(url)
        # print(f"Heartbeat: {response.status_code}") # Verbose
    except Exception as e:
        print(f"Heartbeat error: {e}")

def upload_frame(frame):
    try:
        # Encode frame to JPEG (lower quality 50 for speed)
        _, img_encoded = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
        files = {'file': ('frame.jpg', img_encoded.tobytes(), 'image/jpeg')}
        
        url = f"{API_URL}/robots/{ROBOT_ID}/camera"
        requests.post(url, files=files, timeout=5) # Timeout increased to 5s
    except Exception as e:
        print(f"Frame upload error: {e}")

def main():
    print(f"🚀 Connecting Robot {ROBOT_ID} to {API_URL}")
    
    # 1. Initialize Camera (0 is usually the default webcam)
    print("📷 Initializing Camera...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Could not open webcam. Ensure permission is granted.")
        return

    print("✅ Camera active. Streaming to cloud...")
    
    send_heartbeat(True)
    
    last_heartbeat = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                continue

            # Resize to reduce bandwidth (320x240 is better for cloud HTTP)
            frame = cv2.resize(frame, (320, 240))
            
            # Upload Frame
            upload_frame(frame)
            print(".", end="", flush=True) # visual feedback
            
            # Send Heartbeat every 10 seconds
            if time.time() - last_heartbeat > 10:
                print("\n💓 Heartbeat sent")
                send_heartbeat(True)
                last_heartbeat = time.time()
            
            # Limit FPS (0.05 = ~20 FPS max)
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        cap.release()
        send_heartbeat(False)
        print("Robot Disconnected.")

if __name__ == "__main__":
    main()
