from pydantic import BaseModel, condate
from typing import Optional, List
from PIL import Image
from fastapi import UploadFile

# Schema for User creation and response
class UserSchema(BaseModel):
    email: str
    password: str

    class Config:
        from_attributes = True  # Updated from 'orm_mode' to 'from_attributes' in Pydantic v2

class EventCreate(BaseModel):
    event_name: str
    venue_address: str
    event_date: condate()  # Ensures proper date format
    audience: bool
    delegates: bool
    speaker: bool
    nri: bool


# Schema for Event response including the user_id to show association
class EventResponse(EventCreate):
    id: int
    user_id: int  # Added user_id to show which user the event belongs to

    class Config:
        from_attributes = True

# Schema for Event Form creation
class EventFormCreate(BaseModel):
    event_id: int
    name: str
    email: str
    phoneno: str
    Dropdown: str
    image: Optional[bytes] = None


# Schema for Event Form response
class EventFormResponse(EventFormCreate):
    id: int

    # class Config:
    #     from_attributes = True
