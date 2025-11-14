from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uuid 
import os 
import re
import security
import models, database # Import our new SQL files
from dotenv import load_dotenv 
import google.generativeai as genai
import cloudinary
import cloudinary.uploader
import cloudinary.api
import time
import requests
import io
from PIL import Image
import json
from datetime import datetime, timezone

# --- Load all environment variables ---
load_dotenv()

# --- Create database tables ---
# This line tells SQLAlchemy to create all tables defined in models.py
# Only create tables if not in test mode (test mode will set this to False)
_create_tables_on_startup = True
if _create_tables_on_startup:
    models.Base.metadata.create_all(bind=database.engine)
    print("Database tables created successfully.")

def skip_table_creation():
    """Call this during tests to prevent duplicate table creation"""
    global _create_tables_on_startup
    _create_tables_on_startup = False

# --- Pydantic Schemas (No changes needed) ---
class UserCreate(BaseModel):
    fullName: str
    email: str 
    password: str
    role: str

class UserLogin(BaseModel):
    email: str 
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ChatQuery(BaseModel):
    query: str
    image_url: str | None = None

class AiGradingResponse(BaseModel):
    grade: str
    price_range: str
    analysis: str

class ListingCreate(BaseModel):
    title: str
    quantity: float
    quantity_unit: str
    harvest_date: str
    location: str
    image_urls: list[str]

class ListingResponse(ListingCreate):
    id: str # This will be our UUID
    owner_email: str
    status: str
    ai_grading: AiGradingResponse

class ChatInitiateRequest(BaseModel):
    listing_id: str # This will be the Listing UUID

class ChatRoomResponse(BaseModel):
    chat_id: str # This will be the ChatRoom UUID
    listing_id: str
    listing_title: str
    farmer_email: str
    buyer_email: str

class MessageSendRequest(BaseModel):
    message_text: str

class MessageResponse(BaseModel):
    message_id: str # This will be the Message UUID
    chat_id: str
    sender_email: str
    message_text: str
    timestamp: datetime # Changed to datetime for proper sorting

# --- (REMOVED) Local Excel (OpenPyXL) Setup ---
# DB_FILE = "database.xlsx"
# file_lock = Lock()
# def initialize_database(): ...

# --- Database Dependency ---
get_db = database.get_db
    
# --- 3. Gemini AI Setup (No changes) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not found. AI Assistant will be disabled.")
    ai_model = None
else:
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-2.5-flash') 
    
    AI_SYSTEM_PROMPT = """
    You are "FarmerDirect AI," an all-in-one digital companion for Indian farmers. 
    Your tone is helpful, encouraging, and easy to understand.
    You are an expert in three areas:
    1.  **Plant Doctor:** You can diagnose crop diseases from photos.
    2.  **Crop Advisor:** You give advice on what to plant based on location, soil, and weather.
    3.  **Market Expert:** You can provide market price information.
    4.  **Produce Grader:** You can analyze photos of produce (like carrots, tomatoes, etc.), 
        assign a quality grade (e.g., Grade A, B, C), and explain your reasoning.
        
    Always provide actionable, clear solutions.
    """
    
    AI_GRADING_PROMPT_TEMPLATE = """
    You are a "Produce Grader" for FarmerDirect. Your task is to analyze images of a farmer's produce and provide a grade, a price range, and a justification.
    
    **Rules:**
    1.  **Grade:** Assign a simple grade (A, B, C).
    2.  **Price Range:** Give an estimated market price range in Rupees (e.g., "₹1800 - ₹2000 per quintal"). Base this on the item and its quality.
    3.  **Justification:** Write a 1-2 sentence explanation for your grade.
    
    **User's Listing Title:** {title}
    **User's Listing Quantity:** {quantity} {unit}
    **Location:** {location}
    
    Analyze the following images and provide your response *only* in a structured JSON format.
    Do not add any other text or markdown formatting (like ```json) outside the JSON block.
    
    **Required JSON Format:**
    {{
      "grade": "A",
      "price_range": "₹2000 - ₹2200 per quintal",
      "analysis": "The produce appears fresh, uniform in size, and has no visible blemishes."
    }}
    """
    
    print("Gemini AI Model configured successfully.")

# --- 4. Cloudinary (File Upload) Setup (No changes) ---
try:
    cloudinary.config( 
        cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"), 
        api_key = os.getenv("CLOUDINARY_API_KEY"), 
        api_secret = os.getenv("CLOUDINARY_API_SECRET"),
        secure=True
    )
    print("Successfully connected to Cloudinary.")
except Exception as e:
    print(f"Warning: Cloudinary credentials not found. File upload will be disabled. Error: {e}")


# --- 5. FastAPI App Setup (No changes) ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "Authorization"], 
)

# --- 6. Helper Functions (Find User, Find Listing) ---
# --- REPLACED with SQLAlchemy versions ---

def find_user_in_db(db: Session, email: str) -> models.User | None:
    return db.query(models.User).filter(models.User.email == email).first()

def find_listing_in_db(db: Session, listing_uuid: str) -> models.Listing | None:
    return db.query(models.Listing).filter(models.Listing.uuid == listing_uuid).first()

def find_chat_room_in_db(db: Session, chat_uuid: str) -> models.ChatRoom | None:
    return db.query(models.ChatRoom).filter(models.ChatRoom.uuid == chat_uuid).first()


# --- 7. API Endpoints (Auth) & Security ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
create_access_token = security.create_access_token

# This function is correct. It reads from the token, NOT the database.
# This is efficient and avoids DB calls on every request.
def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = security.verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid token"
        )
    
    user_data = {
        "email": payload.get("sub"),
        "role": payload.get("role"),
        "id": payload.get("id"), # This is the User's UUID
    }

    if not user_data["email"] or not user_data["role"] or not user_data["id"]:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid token payload"
        )
    return user_data

@app.get("/api/v1/test")
def get_test_message():
    return {"status": "healthy", "message": "FarmerDirect API (SQLite) is working!"}

@app.post("/api/v1/auth/register", status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    db_user = find_user_in_db(db, user_data.email)
    if db_user:
        raise HTTPException(409, "Email already registered")
    
    # Validate password
    if len(user_data.password.encode('utf-8')) > 72:
         raise HTTPException(422, "Password is too long (max 72 characters).")
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', user_data.email):
        raise HTTPException(422, "Invalid email format")
    valid_pw, msg = security.validate_password_strength(user_data.password)
    if not valid_pw:
        raise HTTPException(400, msg)
    
    # Create new user
    hashed_password = security.hash_password(user_data.password)
    new_user_uuid = str(uuid.uuid4())
    
    new_db_user = models.User(
        uuid=new_user_uuid,
        full_name=user_data.fullName,
        email=user_data.email,
        password_hash=hashed_password,
        role=user_data.role
    )
    
    try:
        db.add(new_db_user)
        db.commit()
        db.refresh(new_db_user)
        return {"message": "User registered successfully", "email": new_db_user.email, "user_id": new_db_user.uuid}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Could not write to database: {e}")

@app.post("/api/v1/auth/login", response_model=Token)
def login_for_access_token(form_data: UserLogin, db: Session = Depends(get_db)):
    user = find_user_in_db(db, form_data.email)
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    
    # Store the user's UUID (not the DB ID) in the token
    access_token = security.create_access_token(
        data={"sub": user.email, "role": user.role, "id": user.uuid}
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- 8. API Endpoint (File Upload) (No changes) ---
@app.post("/api/v1/uploads/request-cloudinary-signature")
def request_cloudinary_signature(current_user: dict = Depends(get_current_user)):
    api_key = os.getenv("CLOUDINARY_API_KEY")
    api_secret = os.getenv("CLOUDINARY_API_SECRET")
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    if not api_key or not api_secret or not cloud_name:
        raise HTTPException(503, "Cloudinary not configured")
    try:
        timestamp = int(time.time())
        params_to_sign = {"timestamp": timestamp, "folder": "farmer_produce_uploads"}
        signature = cloudinary.utils.api_sign_request(params_to_sign, api_secret)
        return {
            "signature": signature, "timestamp": timestamp,
            "api_key": api_key, "cloud_name": cloud_name,
            "folder": "farmer_produce_uploads"
        }
    except Exception as e:
        raise HTTPException(500, f"Could not generate upload signature: {e}")

# --- 9. API Endpoint (AI Assistant) (No changes) ---
@app.post("/api/v1/ai-assistant/ask")
def ask_ai_assistant(query: ChatQuery, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "farmer":
        raise HTTPException(403, "Only farmers can use the AI Assistant.")
    if not query.query or not query.query.strip():
        raise HTTPException(400, "Query cannot be empty")
    if not ai_model:
        raise HTTPException(503, "AI Assistant is not configured.")
    try:
        full_text_prompt = f"{AI_SYSTEM_PROMPT}\n\nUser Question: {query.query}"
        prompt_parts = [full_text_prompt]
        if query.image_url:
            print(f"AI query received with image: {query.image_url}")
            try:
                image_response = requests.get(query.image_url)
                image_response.raise_for_status() 
                img = Image.open(io.BytesIO(image_response.content)).convert("RGB")
                prompt_parts.append(img)
                print("Image successfully downloaded and added to prompt.")
            except Exception as e:
                print(f"Error fetching or processing image from URL: {e}")
                prompt_parts[0] = (f"{full_text_prompt}\n\n[System Note: Image failed to load.]")
        else:
            print(f"AI query received (text-only): {query.query}")
        response = ai_model.generate_content(prompt_parts)
        return {"response": response.text}
    except Exception as e:
        print(f"Gemini API Error: {e}")
        raise HTTPException(503, f"The AI service is currently unavailable. Error: {e}")

# --- 10. API Endpoints (Listings) ---
def extract_json_from_ai_response(text: str) -> dict | None:
    try:
        match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
        if match:
            return json.loads(match.group(1))
        else:
            return json.loads(text)
    except Exception as e:
        print(f"Error parsing AI JSON response: {e}\nRaw response: {text}")
        return None

@app.post("/api/v1/listings/create", response_model=ListingResponse)
def create_listing(
    listing_data: ListingCreate, 
    current_user: dict = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    if current_user["role"] != "farmer":
        raise HTTPException(403, "Only farmers can create listings.")
    
    if len(listing_data.image_urls) < 3:
        raise HTTPException(422, "Please upload at least 3 images.")
        
    # --- AI Grading (no DB change) ---
    prompt = AI_GRADING_PROMPT_TEMPLATE.format(
        title=listing_data.title,
        quantity=listing_data.quantity,
        unit=listing_data.quantity_unit,
        location=listing_data.location
    )
    prompt_parts = [prompt]
    try:
        for url in listing_data.image_urls:
            image_response = requests.get(url)
            image_response.raise_for_status()
            img = Image.open(io.BytesIO(image_response.content)).convert("RGB")
            prompt_parts.append(img)
    except Exception as e:
        raise HTTPException(400, f"Error processing image from URL: {e}")
    try:
        print("Sending request to Gemini for grading...")
        response = ai_model.generate_content(prompt_parts)
        ai_json_data = extract_json_from_ai_response(response.text)
        if not ai_json_data:
            raise Exception("AI did not return valid JSON.")
        ai_grading = AiGradingResponse(**ai_json_data)
        print(f"AI grading successful: Grade {ai_grading.grade}")
    except Exception as e:
        print(f"Gemini API Error during grading: {e}")
        raise HTTPException(503, f"The AI grading service failed. Error: {e}")
    
    # --- Save to DB ---
    new_listing_uuid = str(uuid.uuid4())
    images_json_string = json.dumps(listing_data.image_urls)
    
    new_db_listing = models.Listing(
        uuid=new_listing_uuid,
        owner_email=current_user["email"],
        title=listing_data.title,
        quantity=listing_data.quantity,
        quantity_unit=listing_data.quantity_unit,
        harvest_date=listing_data.harvest_date,
        location=listing_data.location,
        image_urls=images_json_string,
        ai_grade=ai_grading.grade,
        ai_price_range=ai_grading.price_range,
        ai_analysis=ai_grading.analysis,
        status="active"
    )
    
    try:
        db.add(new_db_listing)
        db.commit()
        db.refresh(new_db_listing)
        
        return ListingResponse(
            id=new_db_listing.uuid, # Return the UUID
            owner_email=new_db_listing.owner_email,
            status=new_db_listing.status,
            ai_grading=ai_grading,
            **listing_data.model_dump()
        )
    except Exception as e:
        db.rollback()
        print(f"Error writing to database: {e}")
        raise HTTPException(500, f"Could not save listing to database. Error: {e}")

@app.get("/api/v1/listings", response_model=list[dict])
def get_all_listings(
    current_user: dict = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    try:
        # Query the database for active listings
        db_listings = db.query(models.Listing).filter(models.Listing.status == "active").all()
        
        active_listings = []
        for listing in db_listings:
            try:
                image_urls = json.loads(listing.image_urls)
            except json.JSONDecodeError:
                image_urls = []
            
            # Manually construct the dictionary to match the old format
            active_listings.append({
                "id": listing.uuid, # Use UUID
                "owner_email": listing.owner_email,
                "title": listing.title,
                "quantity": listing.quantity,
                "quantity_unit": listing.quantity_unit,
                "harvest_date": listing.harvest_date,
                "location": listing.location,
                "image_urls": image_urls,
                "ai_grade": listing.ai_grade,
                "ai_price_range": listing.ai_price_range,
                "ai_analysis": listing.ai_analysis,
                "status": listing.status
            })
        return active_listings
    except Exception as e:
        print(f"Error reading from database: {e}")
        raise HTTPException(500, "Could not fetch listings.")

# ==========================================================
# --- 11. API Endpoints (Chat) ---
# ==========================================================

def check_chat_participation(chat_room: models.ChatRoom, user_email: str) -> bool:
    """Helper to verify a user is part of a chat."""
    return user_email == chat_room.farmer_email or user_email == chat_room.buyer_email

@app.post("/api/v1/chat/initiate", response_model=ChatRoomResponse)
def initiate_chat(
    init_data: ChatInitiateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != "buyer":
        raise HTTPException(403, "Only buyers can initiate chats.")

    # 1. Find the listing
    listing = find_listing_in_db(db, init_data.listing_id)
    if not listing:
        raise HTTPException(404, "Listing not found.")
    
    farmer_email = listing.owner_email
    listing_title = listing.title
    buyer_email = current_user["email"]
    
    if farmer_email == buyer_email:
        raise HTTPException(400, "You cannot start a chat on your own listing.")

    # 2. Check if a chat room already exists
    existing_room = db.query(models.ChatRoom).filter(
        models.ChatRoom.listing_id == init_data.listing_id,
        models.ChatRoom.buyer_email == buyer_email
    ).first()
    
    if existing_room:
        print("Found existing chat room.")
        return ChatRoomResponse(
            chat_id=existing_room.uuid,
            listing_id=existing_room.listing_id,
            listing_title=existing_room.listing_title,
            farmer_email=existing_room.farmer_email,
            buyer_email=existing_room.buyer_email
        )

    # 3. Create a new chat room
    try:
        new_chat_uuid = str(uuid.uuid4())
        new_room = models.ChatRoom(
            uuid=new_chat_uuid,
            listing_id=init_data.listing_id,
            listing_title=listing_title,
            farmer_email=farmer_email,
            buyer_email=buyer_email
        )
        db.add(new_room)
        db.commit()
        db.refresh(new_room)
        
        print(f"Created new chat room: {new_chat_uuid}")
        return ChatRoomResponse(
            chat_id=new_room.uuid,
            listing_id=new_room.listing_id,
            listing_title=new_room.listing_title,
            farmer_email=new_room.farmer_email,
            buyer_email=new_room.buyer_email
        )
    except Exception as e:
        db.rollback()
        print(f"Error creating chat room: {e}")
        raise HTTPException(500, "Could not create chat room.")

@app.get("/api/v1/chat/conversations", response_model=list[ChatRoomResponse])
def get_user_conversations(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_email = current_user["email"]
    try:
        # Find all chat rooms where the user is either the farmer OR the buyer
        rooms = db.query(models.ChatRoom).filter(
            (models.ChatRoom.farmer_email == user_email) | 
            (models.ChatRoom.buyer_email == user_email)
        ).all()
        
        # Convert to Pydantic models
        return [
            ChatRoomResponse(
                chat_id=room.uuid,
                listing_id=room.listing_id,
                listing_title=room.listing_title,
                farmer_email=room.farmer_email,
                buyer_email=room.buyer_email
            ) for room in rooms
        ]
    except Exception as e:
        print(f"Error fetching conversations: {e}")
        raise HTTPException(500, "Could not fetch conversations.")

@app.get("/api/v1/chat/{chat_id}/messages", response_model=list[MessageResponse])
def get_chat_messages(
    chat_id: str, 
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Verify user is a participant
    chat_room = find_chat_room_in_db(db, chat_id)
    if not chat_room:
        raise HTTPException(404, "Chat room not found.")
    if not check_chat_participation(chat_room, current_user["email"]):
        raise HTTPException(403, "You are not authorized to view this chat.")
    
    # 2. Get all messages
    try:
        messages = db.query(models.Message).filter(
            models.Message.chat_room_uuid == chat_id
        ).order_by(models.Message.timestamp.asc()).all() # Sort by timestamp
        
        # Convert to Pydantic models
        return [
            MessageResponse(
                message_id=msg.uuid,
                chat_id=msg.chat_room_uuid,
                sender_email=msg.sender_email,
                message_text=msg.message_text,
                timestamp=msg.timestamp
            ) for msg in messages
        ]
    except Exception as e:
        print(f"Error fetching messages: {e}")
        raise HTTPException(500, "Could not fetch messages.")

@app.post("/api/v1/chat/{chat_id}/send", response_model=MessageResponse)
def send_chat_message(
    chat_id: str,
    msg_data: MessageSendRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Verify user is a participant
    chat_room = find_chat_room_in_db(db, chat_id)
    if not chat_room:
        raise HTTPException(404, "Chat room not found.")
    if not check_chat_participation(chat_room, current_user["email"]):
        raise HTTPException(403, "You are not authorized to send messages to this chat.")
    
    # 2. Create and save the message
    try:
        new_msg = models.Message(
            uuid=str(uuid.uuid4()),
            chat_room_uuid=chat_id,
            sender_email=current_user["email"],
            message_text=msg_data.message_text,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(new_msg)
        db.commit()
        db.refresh(new_msg)
        
        return MessageResponse(
            message_id=new_msg.uuid,
            chat_id=new_msg.chat_room_uuid,
            sender_email=new_msg.sender_email,
            message_text=new_msg.message_text,
            timestamp=new_msg.timestamp
        )
    except Exception as e:
        db.rollback()
        print(f"Error sending message: {e}")
        raise HTTPException(500, "Could not send message.")