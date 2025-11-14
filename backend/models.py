from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from database import Base # Use absolute import
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True) # Added UUID for public reference
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False) # 'farmer' or 'buyer'

class Listing(Base):
    __tablename__ = "listings"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True) # Added UUID
    owner_email = Column(String, ForeignKey("users.email"))
    title = Column(String, index=True)
    quantity = Column(Float)
    quantity_unit = Column(String)
    harvest_date = Column(String) # Storing as string for simplicity
    location = Column(String)
    image_urls = Column(Text) # Store as JSON string
    ai_grade = Column(String)
    ai_price_range = Column(String)
    ai_analysis = Column(Text)
    status = Column(String, default="active")

class ChatRoom(Base):
    __tablename__ = "chat_rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True) # Added UUID
    listing_id = Column(String, ForeignKey("listings.uuid")) # Link to Listing UUID
    listing_title = Column(String)
    farmer_email = Column(String, ForeignKey("users.email"))
    buyer_email = Column(String, ForeignKey("users.email"))

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True) # Added UUID
    chat_room_uuid = Column(String, ForeignKey("chat_rooms.uuid"))
    sender_email = Column(String, ForeignKey("users.email"))
    message_text = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)