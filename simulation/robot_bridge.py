import requests
import time
import cv2
import threading
import sys
import subprocess
import re
import numpy as np
import argparse
import math

# Configuration
# Use the Cloud Run URL or localhost if testing locally
parser = argparse.ArgumentParser()
parser.add_argument("--local", action="store_true", help="Use local API URL")
parser.add_argument("--ip", type=str, default="40.233.116.73", help="Server IP address")
parser.add_argument("--port", type=str, default="8000", help="Server port")
parser.add_argument("--sim", action="store_true", help="Run in simulation mode (Gazebo)")
parser.add_argument("--topic", type=str, default="/world/diff_drive/pose/info", help="Gazebo topic to subscribe to")
parser.add_argument("--id", type=int, default=3, help="Robot ID to use")
parser.add_argument("--robot_name", type=str, default="", help="Manual override for Gazebo robot name")
parser.add_argument("--cmd_topic", type=str, default="", help="Manual override for Gazebo cmd_vel topic")
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

def quaternion_to_yaw(x, y, z, w):
    """
    Convert quaternion to yaw (rotation around Z axis).
    """
    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)
    return math.atan2(t3, t4)

def parse_gazebo_stream(topic):
    """
    Reads Gazebo topic output line by line and updates sim_objects.
    """
    cmd = ["gz", "topic", "-e", "-t", topic]
    print(f"🔌 Subscribing to Gazebo topic: {topic}", flush=True)
    
    try:
        # Use a new process with default text buffering
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        current_object = {}
        
        # Regex patterns - flexible with whitespace
        name_pattern = re.compile(r'name:\s*\"(.*)\"')
        x_pattern = re.compile(r'x:\s*(.*)')
        y_pattern = re.compile(r'y:\s*(.*)')
        z_pattern = re.compile(r'z:\s*(.*)')
        w_pattern = re.compile(r'w:\s*(.*)')
        
        reading_position = False
        reading_orientation = False
        
        while True:
            # Read line-by-line using readline() to better handle streams
            line = process.stdout.readline()
            if not line:
                break
                
            line = line.strip()
            # print(f"DEBUG: {line}", flush=True) # Uncomment if still stuck
            
            # Check for name (Start of new object usually)
            m_name = name_pattern.search(line)
            if m_name:
                current_object = {'name': m_name.group(1)}
                reading_position = False
                reading_orientation = False
                continue

            # Check for position block
            if "position {" in line:
                reading_position = True
                reading_orientation = False
                continue
                
            # Check for orientation block
            if "orientation {" in line:
                reading_position = False
                reading_orientation = True
                continue
            
            if reading_position:
                m_x = x_pattern.search(line)
                if m_x: current_object['x'] = float(m_x.group(1))
                
                m_y = y_pattern.search(line)
                if m_y: current_object['y'] = float(m_y.group(1))
                
                m_z = z_pattern.search(line)
                if m_z: current_object['z'] = float(m_z.group(1))

            if reading_orientation:
                m_x = x_pattern.search(line)
                if m_x: current_object['qx'] = float(m_x.group(1))
                m_y = y_pattern.search(line)
                if m_y: current_object['qy'] = float(m_y.group(1))
                m_z = z_pattern.search(line)
                if m_z: current_object['qz'] = float(m_z.group(1))
                m_w = w_pattern.search(line)
                if m_w: current_object['qw'] = float(m_w.group(1))
                
                # If we have all pieces, update global state
                if 'name' in current_object and 'x' in current_object and 'qw' in current_object:
                     with sim_lock:
                        sim_objects[current_object['name']] = current_object.copy()

    except FileNotFoundError:
        print("❌ 'gz' command not found. Is Gazebo installed and in PATH?", flush=True)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading Gazebo stream: {e}", flush=True)

cmd_execution_thread = None

def _run_gz_cmd(topic, linear, angular):
    """Helper to run the blocking subprocess call in a thread."""
    # Strict formatting for the protobuf text message
    msg = f"linear: {{x: {linear}}}, angular: {{z: {angular}}}"
    
    cmd = ["gz", "topic", "-t", topic, "-m", "gz.msgs.Twist", "-p", msg]
    
    try:
        # Timeout set to 2s to allow gz some time, but fail if stuck
        result = subprocess.run(cmd, timeout=2.0, capture_output=True, text=True)
        if result.returncode != 0:
             print(f"❌ Gz Error ({topic}): {result.stderr.strip()}", flush=True)
    except subprocess.TimeoutExpired:
        print(f"⚠️ Cmd Timer: {topic}", flush=True)
    except Exception as e:
        print(f"❌ Cmd Exception: {e}", flush=True)

def execute_gz_command(linear, angular):
    global cmd_execution_thread
    
    # Priority 1: Manual Topic Override
    if args.cmd_topic:
        topic = args.cmd_topic
    else:
        # Priority 2: Manual Robot Name Override
        robot_name = args.robot_name
        
        # Priority 3: Auto-Discovery
        if not robot_name:
             with sim_lock:
                keys = sim_objects.keys()
                # Prefer 'vehicle_blue' by default for this specific user scenario
                if "vehicle_blue" in keys:
                    robot_name = "vehicle_blue"
                else:
                    # Pick the first one containing 'vehicle'
                    for name in keys:
                        if "vehicle" in name:
                            robot_name = name
                            break
        
        if not robot_name:
            robot_name = "vehicle_blue" # Final Fallback
            
        topic = f"/model/{robot_name}/cmd_vel"

    # Only start a new thread if the previous one is done (throttle + non-blocking)
    if cmd_execution_thread is None or not cmd_execution_thread.is_alive():
        cmd_execution_thread = threading.Thread(
            target=_run_gz_cmd, 
            args=(topic, linear, angular),
            daemon=True
        )
        cmd_execution_thread.start()

last_command = (0.0, 0.0)
last_cmd_send_time = 0

def fetch_and_execute_command():
    global last_command, last_cmd_send_time
    try:
        url = f"{API_URL}/robots/{ROBOT_ID}/command"
        resp = requests.get(url, timeout=1)
        if resp.status_code == 200:
            data = resp.json()
            linear = data.get('linear_x', 0.0)
            angular = data.get('angular_z', 0.0)
            
            # Send duplicate commands every 200ms to keep robot alive
            # But only print if changed
            if (linear, angular) != last_command:
                print(f"🚗 Moving: Linear={linear}, Angular={angular}")
                last_command = (linear, angular)
            
            # Always send to persistent process
            execute_gz_command(linear, angular)
                
    except Exception as e:
        print(f"Command fetch error: {e}")

def draw_simulation_frame():

    # Create black canvas
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    with sim_lock:
        objects = sim_objects.copy()
        
    scale = 20 # Pixels per meter (Zoom level)
    center_x, center_y = 320, 240
    
    # Debug: Print object count on screen
    cv2.putText(frame, f"Objects: {len(objects)}", (10, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # Draw logic
    for name, data in objects.items():
        if 'x' not in data or 'y' not in data:
            continue
            
        # Map Gazebo (X,Y) to Screen (Right, Up)
        # Gazebo X+ is Forward (Screen Right default)
        # Gazebo Y+ is Left (Screen Up default)
        
        px = int(center_x + data['x'] * scale)
        py = int(center_y - data['y'] * scale) # Invert Y for image coords
        
        # Color based on name
        color = (200, 200, 200) # Default white-ish
        if "vehicle" in name or "blue" in name: color = (0, 215, 255) # Gold/Orange
        elif "box" in name: color = (0, 0, 255) # Red
        elif "cylinder" in name: color = (255, 0, 0) # Blue
        elif "sphere" in name: color = (0, 255, 0) # Green
        elif "ground" in name: continue # Don't draw ground plane
        
        # Draw circle for object
        cv2.circle(frame, (px, py), 15, color, -1)
        
        # Draw Orientation (Heading)
        if 'qw' in data:
            # We assume qx, qy, qz exist if qw exists based on parser logic
            yaw = quaternion_to_yaw(data.get('qx',0), data.get('qy',0), data.get('qz',0), data['qw'])
            
            # Draw sticking out line
            end_x = int(px + 25 * math.cos(yaw))
            end_y = int(py - 25 * math.sin(yaw)) # Y inverted
            
            cv2.line(frame, (px, py), (end_x, end_y), (0, 0, 0), 2)
            
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
            
            # Fetch pending commands and execute
            fetch_and_execute_command()
            
            # Upload
            upload_frame(frame)
            print("s", end="", flush=True) # 's' for sim frame
            
            # Heartbeat
            if time.time() - last_heartbeat > 10:
                with sim_lock:
                    obj_names = list(sim_objects.keys())
                print(f"\n💓 Heartbeat sent. Visible Objects: {obj_names}")
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
                with sim_lock:
                    obj_names = list(sim_objects.keys())
                print(f"\n💓 Heartbeat sent. Visible Objects: {obj_names}")
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
