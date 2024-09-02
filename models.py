from sqlalchemy import Column, Integer, String, Boolean,Enum,Date,ARRAY,DateTime, ForeignKey,LargeBinary
from database import Base
from sqlalchemy.orm import column_property, relationship
from PIL import Image
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
    image_data = Column(LargeBinary)

    event = relationship("Event", back_populates="forms")


class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    eventname = Column(String, nullable=False)
    image_data = Column(LargeBinary, nullable=False)


# # models.py
# from sqlalchemy import create_engine, Column, Integer, String, LargeBinary
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
#
# DATABASE_URL = "sqlite:///./test.db"
#
# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()
#
#
# class Image(Base):
#     __tablename__ = "images"
#
#     id = Column(Integer, primary_key=True, index=True)
#     eventname = Column(String, nullable=False)
#     image_data = Column(LargeBinary, nullable=False)
#
#
# # Create the database tables
# def init_db():
#     Base.metadata.create_all(bind=engine)
