from sqlalchemy import Column, Integer, String, Boolean,Enum,Date,ARRAY,DateTime, ForeignKey
from database import Base
from sqlalchemy.orm import column_property, relationship
import enum

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

    events = relationship("Event", back_populates="owner")  # Corrected relationship

# Event model
class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    event_name = Column(String, index=True)
    venue_address = Column(String, index=True)
    event_date = Column(Date)
    audience = Column(Boolean, default=False)
    delegates = Column(Boolean, default=False)
    speaker = Column(Boolean, default=False)
    nri = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="events")  # Corrected relationship
    forms = relationship("EventForm", back_populates="event")  # Ensure this is defined if referenced

# EventForm model
class EventForm(Base):
    __tablename__ = "event_forms"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    name = Column(String, index=True)
    email = Column(String, index=True)
    phoneno = Column(String)
    Dropdown = Column(String)

    event = relationship("Event", back_populates="forms")
