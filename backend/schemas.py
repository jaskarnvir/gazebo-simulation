from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "user"

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool = True
    created_at: datetime
    
    class Config:
        from_attributes = True

# Robot Schemas
class RobotBase(BaseModel):
    serial_number: str
    name: str
    model_type: str = "MiRo-e"

class RobotCreate(RobotBase):
    pass

class Robot(RobotBase):
    id: int
    is_online: bool
    owner_id: int

    class Config:
        from_attributes = True
