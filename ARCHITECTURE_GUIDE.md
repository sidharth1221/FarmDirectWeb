# FarmDirectWeb - Frontend/Backend Architecture

## Authentication Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND (Next.js)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [Login Page]  ──┐                                              │
│  [Register]    ──┤─→ [API Utility Layer]                       │
│  [Dashboard]   ──┘   frontend/lib/api.ts                       │
│                                                                  │
│                      ↓ (with Bearer token)                      │
│                                                                  │
│              localStorage.setItem('token', ...)                │
│              localStorage.setItem('email', ...)                │
│                                                                  │
└────────────────────────┬───────────────────────────────────────┘
                         │ HTTP POST /api/v1/auth/login
                         │ HTTP POST /api/v1/auth/register
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  backend/main.py                                               │
│  ├─ @app.post("/api/v1/auth/register")                        │
│  │  └─ Validates email, hashes password, creates Google       │
│  │     Sheet user                                              │
│  │                                                              │
│  ├─ @app.post("/api/v1/auth/login")                           │
│  │  └─ Verifies credentials, creates JWT token                │
│  │     (expires in 24 hours)                                   │
│  │                                                              │
│  ├─ backend/security.py                                        │
│  │  ├─ create_jwt_token(data: dict)                           │
│  │  ├─ verify_jwt_token(token: str)                           │
│  │  └─ hash_password() / verify_password()                    │
│  │                                                              │
│  └─ backend/database.py                                        │
│     └─ Google Sheets integration (gspread)                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Models

### Login Request
```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

### Login Response
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "email": "user@example.com"
}
```

### Register Request
```json
{
  "fullName": "John Farmer",
  "email": "john@example.com",
  "password": "securePassword123",
  "role": "farmer"  // or "buyer"
}
```

### Register Response
```json
{
  "id": "user123",
  "email": "john@example.com",
  "fullName": "John Farmer",
  "role": "Farmer",
  "created_at": "2024-01-15T10:30:00Z"
}
```

## API Utility Layer Architecture

```
frontend/lib/api.ts
│
├─ apiCall<T>(endpoint, options)
│  ├─ Constructs full URL with NEXT_PUBLIC_API_URL
│  ├─ Injects Authorization header with Bearer token
│  ├─ Handles JSON serialization
│  └─ Catches and properly formats errors
│
├─ loginUser(email, password)
│  └─ Calls: POST /api/v1/auth/login
│
├─ registerUser(fullName, email, password, role)
│  └─ Calls: POST /api/v1/auth/register
│
├─ askAI(query, includeImage?)
│  └─ Calls: POST /api/v1/ai-assistant/ask
│
├─ getCloudinarySignature()
│  └─ Calls: GET /api/v1/uploads/request-cloudinary-signature
│
└─ checkHealth()
   └─ Calls: GET /api/v1/test
```

## Component Integration

### Login Page Flow
```
User Input
    ↓
Validation (email format, password required)
    ↓
loginUser(email, password)
    ↓
API Utility injects Bearer token (if exists)
    ↓
Backend validates credentials
    ↓
Backend returns { access_token, token_type, email }
    ↓
localStorage.setItem('token', access_token)
    ↓
router.push('/dashboard')
    ↓
Dashboard checks token existence and renders
```

### Register Page Flow
```
User Input (name, email, password, role)
    ↓
Validation (email format, password ≥8 chars, terms agreed)
    ↓
registerUser(fullName, email, password, role)
    ↓
API Utility calls backend
    ↓
Backend checks for duplicate email
    ↓
Backend hashes password and creates Google Sheet row
    ↓
Backend returns user data
    ↓
router.push('/login') - user logs in manually
```

### Dashboard Page Flow
```
Page Load
    ↓
Check localStorage for token
    ↓
No token? → router.push('/login')
    ↓
Token exists? → setIsAuthenticated(true)
    ↓
Display user email in header
    ↓
Show listings and offer buttons
    ↓
Logout button → clears localStorage → redirects to /login
```

## Security Features

1. **JWT Tokens**
   - Stored in localStorage (client-side)
   - 24-hour expiration (backend enforcement)
   - Automatically injected in Authorization header

2. **Password Security**
   - Hashed with bcrypt (backend)
   - Salted automatically
   - Never stored in plaintext

3. **Environment Variables**
   - `JWT_SECRET_KEY` - kept secret on backend
   - `GEMINI_API_KEY` - kept secret on backend
   - `CLOUDINARY_*` - kept secret on backend
   - `NEXT_PUBLIC_API_URL` - can be public (contains URL only)

4. **HTTPS (Production)**
   - Tokens should only be sent over HTTPS
   - localStorage is domain-specific (no cross-site access)

## File Structure

```
frontend/
├── app/
│   ├── login/
│   │   └── page.tsx          ← Login with centralized API
│   ├── register/
│   │   └── page.tsx          ← Register with centralized API
│   ├── dashboard/
│   │   └── page.tsx          ← Protected route with auth check
│   ├── layout.tsx            ← App root
│   └── page.tsx              ← Home page
├── lib/
│   └── api.ts                ← Centralized API utilities
└── public/

backend/
├── main.py                   ← FastAPI app with all endpoints
├── models.py                 ← SQLAlchemy models
├── database.py               ← Google Sheets connection
├── security.py               ← JWT & password hashing
└── requirements.txt          ← Dependencies
```

## Environment Configuration

### Backend (.env)
```
JWT_SECRET_KEY=your-secret-key-here
GEMINI_API_KEY=your-gemini-key
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
GOOGLE_SHEETS_ID=your-sheets-id
SHEET_CREDENTIALS_FILE=./service-account.json
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Testing the Integration

### 1. Start Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### 2. Start Frontend
```bash
cd frontend
npm install
npm run dev
```

### 3. Test Registration
- Navigate to http://localhost:3000/register
- Fill in all fields
- Click "Create My Account"
- Should redirect to login page

### 4. Test Login
- Use credentials from registration
- Click "Log In"
- Should redirect to dashboard
- Email should display in header
- Token should be in localStorage (check DevTools → Application → Storage)

### 5. Test Logout
- Click "Log Out" button
- Should redirect to login page
- localStorage should be cleared
- Dashboard access should redirect to login

## Known Issues & TODOs

### Current
- ✅ Frontend uses centralized API utilities
- ✅ Auth pages have loading states
- ✅ Dashboard has auth protection
- ✅ No TypeScript errors
- ✅ Backend tests passing (38/38)

### Not Yet Implemented
- ⏳ Forgot password page
- ⏳ Token refresh logic (auto-refresh on expiry)
- ⏳ User profile page
- ⏳ AI assistant page (API ready, UI needed)
- ⏳ File upload page (API ready, UI needed)
- ⏳ Listings management page
- ⏳ Terms & Privacy pages
- ⏳ Global user state management (Context API)
- ⏳ 60-70 test cases (38 backend tests created)

## Quick Debugging

### Issue: Login fails with "Network error"
- Check if backend is running: `python main.py`
- Check NEXT_PUBLIC_API_URL env var
- Check browser console for CORS errors

### Issue: Token not persisting
- Check if localStorage is enabled in browser
- Check DevTools → Application → Storage → localStorage
- Token key should be "token"

### Issue: Dashboard redirects to login
- localStorage token might be expired (24-hour TTL)
- Clear localStorage and re-login
- Check backend JWT_SECRET_KEY is consistent

### Issue: Logout not working
- Check if logout button is clicked
- Verify localStorage is cleared in DevTools
- Check if router.push('/login') executes
