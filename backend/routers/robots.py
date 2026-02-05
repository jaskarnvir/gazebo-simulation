from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import database, schemas, models, auth

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
