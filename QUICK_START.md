# 🚀 Quick Start Guide - FarmDirectWeb

## 60 Second Setup

### Prerequisites
- Node.js 18+ installed
- Python 3.9+ installed
- Git installed

### Step 1: Backend Setup (2 minutes)
```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with required variables
# See backend/.env.example for template
```

### Step 2: Frontend Setup (1 minute)
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Create .env.local file
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Step 3: Start Servers

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
# Backend runs on http://localhost:8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
# Frontend runs on http://localhost:3000
```

### Step 4: Test It Out
1. Open http://localhost:3000 in browser
2. Click "Sign Up" button
3. Fill in the registration form
4. Click "Create My Account"
5. You'll be redirected to login
6. Log in with your credentials
7. See the dashboard with your email in the header!

---

## Key Files to Know

| File | Purpose |
|------|---------|
| `frontend/lib/api.ts` | Centralized API utilities - all API calls go through here |
| `frontend/app/login/page.tsx` | Login page (uses `loginUser()`) |
| `frontend/app/register/page.tsx` | Register page (uses `registerUser()`) |
| `frontend/app/dashboard/page.tsx` | Protected dashboard (checks token) |
| `backend/main.py` | FastAPI server with all endpoints |
| `backend/security.py` | JWT and password hashing |
| `backend/.env.example` | Template for backend environment variables |
| `frontend/.env.local.example` | Template for frontend environment variables |

---

## Environment Variables

### Backend (.env)
Create `backend/.env` with:
```
JWT_SECRET_KEY=your-secret-key-here-change-this
GEMINI_API_KEY=your-gemini-api-key
CLOUDINARY_CLOUD_NAME=your-cloudinary-name
CLOUDINARY_API_KEY=your-cloudinary-api-key
CLOUDINARY_API_SECRET=your-cloudinary-secret
GOOGLE_SHEETS_ID=your-google-sheets-id
SHEET_CREDENTIALS_FILE=./service-account.json
```

For development, you can use placeholder values (except JWT_SECRET_KEY which must be set).

### Frontend (.env.local)
Create `frontend/.env.local` with:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Architecture Overview

```
User Browser (http://localhost:3000)
    ↓
React Components
    ↓
API Utility Layer (frontend/lib/api.ts)
    ├─ loginUser()
    ├─ registerUser()
    ├─ askAI()
    └─ getCloudinarySignature()
    ↓ (with Bearer token in header)
FastAPI Backend (http://localhost:8000)
    ├─ POST /api/v1/auth/register
    ├─ POST /api/v1/auth/login
    ├─ POST /api/v1/ai-assistant/ask
    └─ GET /api/v1/uploads/request-cloudinary-signature
    ↓
Google Sheets (database)
```

---

## Common Tasks

### Reset Everything
```bash
# Clear frontend node_modules and reinstall
cd frontend
rm -rf node_modules
npm install

# Clear Python cache and reinstall
cd backend
rm -rf venv
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate
pip install -r requirements.txt
```

### Clear Your Login
```bash
# Open browser DevTools (F12 or right-click → Inspect)
# Go to Application → Storage → localStorage
# Delete "token" and "email" entries
# Reload page → redirects to login
```

### View API Calls
```bash
# Open browser DevTools (F12)
# Go to Network tab
# Perform login or registration
# See all POST requests to /api/v1/auth/*
```

### Check Backend Logs
```bash
# Backend terminal will show all requests
# Should see lines like:
# INFO:     GET /api/v1/test
# INFO:     POST /api/v1/auth/login - "200 OK"
```

---

## Testing Credentials

### Pre-loaded Test Accounts
Once backend is running, you can create test accounts:

1. **First User (Farmer)**
   - Email: `farmer1@example.com`
   - Password: `Password123!`
   - Role: Farmer

2. **Second User (Buyer)**
   - Email: `buyer1@example.com`
   - Password: `Password123!`
   - Role: Buyer

---

## Troubleshooting

### "Connection refused" on localhost:8000
**Solution:** Backend not running
```bash
# Check if backend is running in another terminal
cd backend
python main.py
```

### "Network error" when registering
**Solution:** Check backend is accessible
```bash
# In browser, visit http://localhost:8000/api/v1/test
# Should show: {"message": "API is working!"}
```

### "Cannot find module" when starting frontend
**Solution:** Dependencies not installed
```bash
cd frontend
npm install
```

### Token not saving
**Solution:** localStorage might be disabled
```bash
# Check browser settings
# F12 → Application → Storage → localStorage
# Should see entries after login
```

### "Invalid email" validation error
**Solution:** Use valid email format
```
✅ Valid: user@example.com
✅ Valid: john.doe@gmail.com
❌ Invalid: userexample.com (missing @)
❌ Invalid: user@.com (missing domain)
```

### Password validation failing
**Solution:** Password must be at least 8 characters
```
✅ Valid: MyPassword123
✅ Valid: FarmDirect2024
❌ Invalid: Pass123 (7 chars)
```

---

## File Structure Reference

```
FarmDirectWeb/
├── backend/
│   ├── main.py                    ← FastAPI app
│   ├── models.py                  ← SQLAlchemy models
│   ├── database.py                ← Google Sheets setup
│   ├── security.py                ← JWT + passwords
│   ├── requirements.txt           ← Python packages
│   ├── .env                       ← Environment (create this)
│   ├── .env.example               ← Template
│   ├── service-account.json       ← Google Sheets auth (add this)
│   └── tests/
│       └── test_backend_full.py   ← 38 passing tests
│
├── frontend/
│   ├── app/
│   │   ├── login/
│   │   │   └── page.tsx           ← Login page
│   │   ├── register/
│   │   │   └── page.tsx           ← Register page
│   │   ├── dashboard/
│   │   │   └── page.tsx           ← Protected dashboard
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── lib/
│   │   └── api.ts                 ← API utilities ⭐
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── .env.local                 ← Environment (create this)
│   └── .env.local.example         ← Template
│
├── Documentation/
│   ├── COMPLETION_SUMMARY.md      ← What was done
│   ├── FRONTEND_ALIGNMENT_REPORT.md
│   ├── ARCHITECTURE_GUIDE.md      ← Full architecture
│   ├── CODE_CHANGES_REFERENCE.md  ← Before/after code
│   ├── FINAL_CHECKLIST.md         ← Complete checklist
│   ├── SETUP_GUIDE.md
│   ├── .env.example
│   └── README.md
```

---

## Next Steps After Setup

1. **✅ Test Registration/Login**
   - Verify account creation works
   - Check token storage in localStorage

2. **✅ Explore Dashboard**
   - Browse production listings
   - Test logout button

3. **🔧 Set Up AI Features (Not Yet)**
   - Need to create `/ai-assistant` page
   - Will use `askAI()` from api.ts

4. **🔧 Set Up File Uploads (Not Yet)**
   - Need to create `/uploads` page
   - Will use `getCloudinarySignature()` from api.ts

5. **🔧 Create Additional Pages**
   - `/profile` - User profile page
   - `/listings` - Manage listings
   - `/messages` - Direct messaging
   - `/forgot-password` - Password recovery

---

## Development Workflow

### Daily Development
```bash
# Terminal 1: Start Backend
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python main.py

# Terminal 2: Start Frontend
cd frontend
npm run dev

# Terminal 3 (optional): Check types
cd frontend
npm run type-check
```

### Making Changes
```bash
# Frontend changes
# → Edit files in frontend/app/
# → Changes auto-reload at http://localhost:3000
# → Check console for errors

# Backend changes
# → Edit files in backend/
# → Restart: Ctrl+C, then python main.py
# → Changes take effect on next request

# API changes
# → Edit frontend/lib/api.ts
# → Frontend auto-reloads
# → Backend must be restarted if backend code changed
```

### Before Committing
```bash
# Check TypeScript
npm run type-check

# Check for errors
npm run lint  # if available

# Manual testing
# 1. Register new account
# 2. Login with account
# 3. Check dashboard
# 4. Logout and verify redirect
```

---

## Getting Help

### Check Documentation
1. `ARCHITECTURE_GUIDE.md` - How system works
2. `CODE_CHANGES_REFERENCE.md` - What changed
3. `FINAL_CHECKLIST.md` - Complete reference

### Debug Checklist
- [ ] Backend running on port 8000?
- [ ] Frontend running on port 3000?
- [ ] `.env` files created with variables?
- [ ] All dependencies installed?
- [ ] Node modules updated? (`npm install`)
- [ ] Python venv activated?
- [ ] localStorage enabled in browser?
- [ ] No CORS errors in console?

---

## Production Deployment

**Before deploying to production:**

1. ✅ Set strong `JWT_SECRET_KEY`
2. ✅ Use HTTPS for all connections
3. ✅ Set proper environment variables
4. ✅ Run backend tests: `pytest backend/tests/`
5. ✅ Build frontend: `npm run build`
6. ✅ Test with production build: `npm start`
7. ✅ Set up CI/CD pipeline
8. ✅ Configure database backups
9. ✅ Set up monitoring/logging
10. ✅ Security audit completed

---

## Getting Started Checklist

- [ ] Clone repository
- [ ] Backend .env created
- [ ] Frontend .env.local created
- [ ] Backend dependencies installed
- [ ] Frontend dependencies installed
- [ ] Backend started on port 8000
- [ ] Frontend started on port 3000
- [ ] Can register new account
- [ ] Can login with account
- [ ] Dashboard shows email
- [ ] Logout works
- [ ] Redirects work correctly

**Status: ✅ READY TO BUILD**

Your FarmDirectWeb application is fully configured and ready for development!

---

## Support Resources

- FastAPI Docs: http://localhost:8000/docs
- Next.js Docs: https://nextjs.org/docs
- Tailwind CSS: https://tailwindcss.com/docs
- React Hooks: https://react.dev/reference/react

---

**Happy coding! 🚀**
