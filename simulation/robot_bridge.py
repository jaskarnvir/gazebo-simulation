import requests
import time
import cv2
import threading
import sys
import subprocess
import re
import numpy as np
import argparse

# Configuration
# Use the Cloud Run URL or localhost if testing locally
parser = argparse.ArgumentParser()
parser.add_argument("--local", action="store_true", help="Use local API URL")
parser.add_argument("--ip", type=str, default="40.233.116.73", help="Server IP address")
parser.add_argument("--port", type=str, default="8000", help="Server port")
parser.add_argument("--sim", action="store_true", help="Run in simulation mode (Gazebo)")
parser.add_argument("--topic", type=str, default="/world/shapes/pose/info", help="Gazebo topic to subscribe to")
parser.add_argument("--id", type=int, default=3, help="Robot ID to use")
args = parser.parse_args()

if args.local:
    API_URL = "http://127.0.0.1:8000"
else:
    API_URL = f"http://{args.ip}:{args.port}"

ROBOT_ID = args.id 
SERIAL_NUMBER = "MIRO-12345"

# Global state for simulation objects
sim_objects = {}
sim_lock = threading.Lock()

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

def parse_gazebo_stream(topic):
    """
    Reads Gazebo topic output line by line and updates sim_objects.
    Output format example:
    pose {
      name: "box"
      id: 8
      position {
        x: -0.5
        y: 2.7
        z: 0.1
      }
      ...
    }
    """
    cmd = ["gz", "topic", "-e", "-t", topic]
    print(f"🔌 Subscribing to Gazebo topic: {topic}")
    
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        current_object = {}
        
        # Regex patterns
        name_pattern = re.compile(r'name: "(.*)"')
        pos_point_pattern = re.compile(r'position\s*{')
        x_pattern = re.compile(r'x: (.*)')
        y_pattern = re.compile(r'y: (.*)')
        z_pattern = re.compile(r'z: (.*)')
        
        reading_position = False
        
        for line in process.stdout:
            line = line.strip()
            
            # Start of a new pose block usually implied, but here we scan for fields
            # Check name
            m_name = name_pattern.search(line)
            if m_name:
                # Save previous object if complete (simplified logic)
                current_object = {'name': m_name.group(1)}
                reading_position = False
                continue
                
            if "position {" in line:
                reading_position = True
                continue
                
            if "orientation {" in line:
                reading_position = False
                # End of position block for this object
                if 'name' in current_object and 'x' in current_object:
                    with sim_lock:
                        sim_objects[current_object['name']] = current_object.copy()
                continue
                
            if reading_position:
                m_x = x_pattern.search(line)
                if m_x: current_object['x'] = float(m_x.group(1))
                
                m_y = y_pattern.search(line)
                if m_y: current_object['y'] = float(m_y.group(1))
                
                m_z = z_pattern.search(line)
                if m_z: current_object['z'] = float(m_z.group(1))

    except FileNotFoundError:
        print("❌ 'gz' command not found. Is Gazebo installed and in PATH?")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading Gazebo stream: {e}")

def draw_simulation_frame():
    """
    Draws a 2D top-down map of the simulation objects.
    """
    # Create a black background 640x480
    height, width = 480, 640
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Scale factor (pixels per meter)
    scale = 50
    center_x, center_y = width // 2, height // 2
    
    with sim_lock:
        objects = sim_objects.copy()
    
    # Draw logic
    for name, data in objects.items():
        if 'x' not in data or 'y' not in data:
            continue
            
        # Convert world pos to pixel pos
        # Gazebo: X right, Y up (usually). OpenCV: X right, Y down.
        # We'll map Gazebo (0,0) to center.
        px = int(center_x + data['x'] * scale)
        py = int(center_y - data['y'] * scale) # Invert Y for image coords
        
        # Color based on name
        color = (200, 200, 200) # Default white-ish
        if "box" in name: color = (0, 0, 255) # Red
        elif "cylinder" in name: color = (255, 0, 0) # Blue
        elif "sphere" in name: color = (0, 255, 0) # Green
        elif "ground" in name: continue # Don't draw ground plane
        
        # Draw circle for object
        cv2.circle(frame, (px, py), 15, color, -1)
        # Draw label
        cv2.putText(frame, name, (px + 10, py), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
    return frame

def run_simulation_bridge():
    print(f"🚀 Starting Simulation Bridge for Robot {ROBOT_ID} to {API_URL}")
    
    # Start Gazebo listener thread
    t = threading.Thread(target=parse_gazebo_stream, args=(args.topic,), daemon=True)
    t.start()
    
    send_heartbeat(True)
    last_heartbeat = 0
    
    try:
        while True:
            # Generate frame from simulation state
            frame = draw_simulation_frame()
            
            # Add timestamp / overlay
            cv2.putText(frame, "SIMULATION FEED", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            # Upload
            upload_frame(frame)
            print("s", end="", flush=True) # 's' for sim frame
            
            # Heartbeat
            if time.time() - last_heartbeat > 10:
                print("\n💓 Heartbeat sent")
                send_heartbeat(True)
                last_heartbeat = time.time()
                
            time.sleep(0.1) # 10 FPS
            
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        send_heartbeat(False)
        print("Simulation Bridge Disconnected.")

def run_camera_bridge():
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

            # Resize to reduce bandwidth
            frame = cv2.resize(frame, (320, 240))
            
            # Upload Frame
            upload_frame(frame)
            print(".", end="", flush=True) # visual feedback
            
            # Heartbeat
            if time.time() - last_heartbeat > 10:
                print("\n💓 Heartbeat sent")
                send_heartbeat(True)
                last_heartbeat = time.time()
            
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        cap.release()
        send_heartbeat(False)
        print("Robot Disconnected.")

def main():
    if args.sim:
        run_simulation_bridge()
    else:
        run_camera_bridge()

if __name__ == "__main__":
    main()
