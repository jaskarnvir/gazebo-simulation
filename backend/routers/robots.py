from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import time
import io
from .. import database, schemas, models, auth

class RobotCommand(schemas.BaseModel):
    linear_x: float
    angular_z: float

router = APIRouter(
    prefix="/robots",
    tags=["Robots"]
)

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

def generate_mock_camera_feed():
    # Helper to generate a fake MJPEG stream
    # Creates simple colored frames
    from PIL import Image, ImageDraw
    import random
    
    width, height = 640, 480
    while True:
        # Create a new image with random color
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        img = Image.new('RGB', (width, height), color=color)
        d = ImageDraw.Draw(img)
        d.text((10, 10), f"Timestamp: {time.time()}", fill=(255, 255, 255))
        
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_bytes = img_byte_arr.getvalue()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + img_bytes + b'\r\n')
        time.sleep(0.1) # 10 FPS

@router.get("/{robot_id}/camera")
def get_camera_feed(robot_id: int):
    # Returns a multipart MJPEG stream
    return StreamingResponse(generate_mock_camera_feed(), media_type="multipart/x-mixed-replace; boundary=frame")

@router.get("/{robot_id}/camera/snapshot")
def get_camera_snapshot(robot_id: int):
    # Returns a single JPEG frame
    from PIL import Image, ImageDraw
    import random
    import io
    
    width, height = 640, 480
    color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    img = Image.new('RGB', (width, height), color=color)
    d = ImageDraw.Draw(img)
    d.text((10, 10), f"Snapshot: {time.time()}", fill=(255, 255, 255))
        
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    
    return StreamingResponse(io.BytesIO(img_byte_arr.getvalue()), media_type="image/jpeg")
