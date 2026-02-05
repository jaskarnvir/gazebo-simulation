from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import database, schemas, models, auth

router = APIRouter(
    prefix="/emergency",
    tags=["Emergency"]
)

class EmergencyContactCreate(schemas.BaseModel):
    name: str
    phone_number: str
    relation: str

class EmergencyContact(EmergencyContactCreate):
    id: int
    user_id: int
    class Config:
        from_attributes = True

@router.post("/", response_model=EmergencyContact)
def create_contact(contact: EmergencyContactCreate, current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    db_contact = models.EmergencyContact(**contact.dict(), user_id=current_user.id)
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

@router.get("/", response_model=List[EmergencyContact])
def read_contacts(current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    return db.query(models.EmergencyContact).filter(models.EmergencyContact.user_id == current_user.id).all()

@router.post("/trigger")
def trigger_emergency(current_user: schemas.User = Depends(auth.get_current_user)):
    # Mock emergency trigger
    print(f"EMERGENCY TRIGGERED for User {current_user.id} ({current_user.email})!")
    # Logic to notify contacts/services would go here
    return {"status": "alert_sent", "message": "Emergency services and contacts have been notifed."}
