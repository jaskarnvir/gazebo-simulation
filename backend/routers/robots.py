from fastapi import APIRouter, Depends, HTTPException, Response, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import time
import io
from PIL import Image, ImageDraw
from .. import database, schemas, models, auth

class RobotCommand(schemas.BaseModel):
    linear_x: float
    angular_z: float

router = APIRouter(
    prefix="/robots",
    tags=["Robots"]
)

# In-memory storage for the latest frame of each robot
# robot_id -> bytes
latest_frames = {}

@router.post("/", response_model=schemas.Robot)
def register_robot(robot: schemas.RobotCreate, current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    # Simple logic: User registers a robot. In real app, might verify serial with factory DB.
    db_robot = models.Robot(**robot.dict(), owner_id=current_user.id)
    db.add(db_robot)
    db.commit()
    db.refresh(db_robot)
    return db_robot

@router.get("/", response_model=List[schemas.Robot])
def read_robots(skip: int = 0, limit: int = 100, current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    robots = db.query(models.Robot).filter(models.Robot.owner_id == current_user.id).offset(skip).limit(limit).all()
    return robots

@router.post("/{robot_id}/status")
def update_robot_status(robot_id: int, is_online: bool, db: Session = Depends(database.get_db)):
    # This endpoint might be called by the robot itself (needs API key or cert in real life)
    # For now, we allow it to be open or use a shared secret.
    robot = db.query(models.Robot).filter(models.Robot.id == robot_id).first()
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")
    
    robot.is_online = is_online
    db.commit()
    return {"status": "updated", "is_online": is_online}

@router.post("/{robot_id}/command")
def send_command(robot_id: int, command: RobotCommand, current_user: schemas.User = Depends(auth.get_current_user)):
    # In a real scenario, this would forward via MQTT/ROS bridge
    print(f"COMMAND to Robot {robot_id}: Linear={command.linear_x}, Angular={command.angular_z}")
    return {"status": "sent", "command": command}

@router.post("/{robot_id}/camera")
async def upload_camera_frame(robot_id: int, file: UploadFile = File(...)):
    """Receives a camera frame from the robot and stores it in memory."""
    contents = await file.read()
    latest_frames[robot_id] = contents
    return {"status": "frame_received"}

def get_offline_image():
    """Generates a black 'Camera Offline' placeholder image."""
    width, height = 640, 480
    img = Image.new('RGB', (width, height), color='black')
    d = ImageDraw.Draw(img)
    d.text((width//2 - 40, height//2), "NO SIGNAL", fill=(255, 255, 255))
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    return img_byte_arr.getvalue()

@router.get("/{robot_id}/camera/snapshot")
def get_camera_snapshot(robot_id: int):
    """Returns the latest frame for the robot, or an offline placeholder."""
    frame_data = latest_frames.get(robot_id)
    
    if frame_data is None:
        frame_data = get_offline_image()
        
    return StreamingResponse(io.BytesIO(frame_data), media_type="image/jpeg")
