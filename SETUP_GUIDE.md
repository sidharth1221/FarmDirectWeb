# FarmerDirect Setup Guide

## Backend Setup (Python/FastAPI)

### Prerequisites
- Python 3.10+
- Virtual Environment

### Installation Steps

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On Mac/Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your credentials:
   - `JWT_SECRET_KEY`: Generate a strong random key (min 32 chars)
   - `GEMINI_API_KEY`: Get from https://ai.google.dev/
   - `CLOUDINARY_*`: Get from https://cloudinary.com/

5. **Set up Google Sheets (Alternative to Database)**
   - Download `service-account.json` from Google Cloud Console
   - Place in `backend/` folder
   - Share your Google Sheet with the service account email
   - Update `SHEET_ID` in `main.py` (currently hardcoded)

6. **Run the backend**
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   ✅ Backend running at: http://localhost:8000

### API Endpoints

#### Health Check
```bash
GET /api/v1/test
```

#### Authentication
```bash
POST /api/v1/auth/register
{
  "fullName": "John Farmer",
  "email": "john@example.com",
  "password": "SecurePass123",
  "role": "farmer"
}

POST /api/v1/auth/login
{
  "email": "john@example.com",
  "password": "SecurePass123"
}
```

#### AI Assistant
```bash
POST /api/v1/ai-assistant/ask
{
  "query": "How do I improve my crop yield?",
  "image_url": null
}
```

#### File Upload (Cloudinary)
```bash
POST /api/v1/uploads/request-cloudinary-signature
```

---

## Frontend Setup (Next.js/React)

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation Steps

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.local.example .env.local
   ```
   Edit `.env.local`:
   - `NEXT_PUBLIC_API_URL`: Should match backend URL (http://localhost:8000)

4. **Run the frontend**
   ```bash
   npm run dev
   ```
   ✅ Frontend running at: http://localhost:3000

### Pages

- `/` - Home page (hero, features, testimonials)
- `/login` - User login
- `/register` - User registration (farmer/buyer choice)
- `/dashboard` - User dashboard (create this)
- `/forgot-password` - Password recovery (create this)
- `/terms` - Terms of Service (create this)
- `/privacy` - Privacy Policy (create this)

---

## Backend Architecture

### Database Strategy (Current & Future)

**Current (Development):** Google Sheets
- File: `main.py` lines 38-61
- User data stored in Google Sheet
- Function: `find_user_in_sheet()`
- Good for: Quick testing, no database setup needed

**Future (Production):** PostgreSQL (coming soon)
- Replace Google Sheets with SQLAlchemy models
- Migrate `database.py` to use PostgreSQL
- Keep same API endpoints (no frontend changes needed)

### Authentication Flow

1. **Registration** → Hash password → Save to Sheets → Return user_id
2. **Login** → Find user → Verify password → Create JWT token
3. **Token** → Stored in localStorage on frontend → Sent in Authorization header
4. **Token Expiry** → 24 hours (configured in `security.py`)

### AI Features

- **Text Query** → Gemini API → Advice/Guidance
- **Image Query** → Download image → Send to Gemini → Disease diagnosis
- **Fallback** → If no API key, return mock response

### File Upload

- Frontend requests signature from `/api/v1/uploads/request-cloudinary-signature`
- Frontend uploads directly to Cloudinary with signature
- Cloudinary URL stored in database

---

## Frontend Updates Required

The frontend is already configured to work with the backend changes:

✅ Using `NEXT_PUBLIC_API_URL` environment variable (not hardcoded)
✅ Sending correct payload format: `{ fullName, email, password, role }`
✅ Storing JWT token in localStorage
✅ Redirecting to `/dashboard` after login

### Still Need to Create

- [ ] `/dashboard` page - User profile and main app area
- [ ] `/forgot-password` page - Password recovery form
- [ ] `/terms` page - Terms of Service
- [ ] `/privacy` page - Privacy Policy
- [ ] API error handling utility - Better error messages
- [ ] Token validation utility - Check if token is expired
- [ ] User context/hook - Store user info globally

---

## Environment Variables Summary

### Backend (.env)
```
JWT_SECRET_KEY=<strong-random-key>
GEMINI_API_KEY=<your-api-key>
CLOUDINARY_CLOUD_NAME=<cloud-name>
CLOUDINARY_API_KEY=<api-key>
CLOUDINARY_API_SECRET=<api-secret>
ALLOWED_ORIGINS=http://localhost:3000
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Running Tests

### Backend Tests

```bash
cd backend
pip install pytest pytest-cov httpx
pytest -v tests/test_backend_full.py
```

Currently: **38 tests passing** ✅

---

## Troubleshooting

### "GEMINI_API_KEY not found"
→ Get from https://ai.google.dev/ and add to .env

### "Error connecting to Google Sheet"
→ Ensure `service-account.json` exists and sheet is shared with service account email

### "JWT_SECRET_KEY not set"
→ Add `JWT_SECRET_KEY=<your-key>` to `.env`

### Frontend showing 404 on /dashboard
→ Create `frontend/app/dashboard/page.tsx`

### CORS errors in browser console
→ Ensure `ALLOWED_ORIGINS` in backend .env includes frontend URL

---

## Next Steps

1. ✅ Backend API implemented
2. ✅ Auth endpoints working
3. ✅ AI assistant configured
4. ⏳ Create missing frontend pages
5. ⏳ Implement user dashboard
6. ⏳ Add logout functionality
7. ⏳ Implement password recovery
8. ⏳ Setup production database (PostgreSQL)
9. ⏳ Deploy to production

---

## API Response Examples

### Successful Login
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Registration Error
```json
{
  "detail": "Email already registered"
}
```

### AI Response
```json
{
  "response": "Based on your crop and conditions, I recommend..."
}
```

---

**Last Updated:** November 14, 2025
**Status:** Development (Ready for Testing)
