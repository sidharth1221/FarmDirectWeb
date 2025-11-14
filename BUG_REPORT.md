# FarmerDirect Bug Analysis & Test Report
## Generated: November 14, 2025

---

## BACKEND BUGS IDENTIFIED

### BUG #1: Missing Google Sheets Client Initialization
**Severity:** CRITICAL  
**File:** `backend/main.py` (Line 28)  
**Issue:** The code references `client.open_by_key()` but `client` is never defined. The Credentials import exists but the actual client initialization is missing.
```python
# CURRENT (BROKEN):
try:
    SHEET_ID = "1yGobTLtugfFNVdUlhIiiCVyr-nlx7eN3h_AEr9VCvpE"
    spreadsheet = client.open_by_key(SHEET_ID)  # ❌ 'client' is not defined
```
**Impact:** Application will crash on startup with `NameError: name 'client' is not defined`

---

### BUG #2: Incomplete Pydantic Schema Definitions
**Severity:** CRITICAL  
**File:** `backend/main.py` (Lines 20-25)  
**Issue:** Pydantic model classes are defined with `...` (ellipsis) but no actual fields.
```python
# CURRENT (BROKEN):
class UserCreate(BaseModel): ...
class UserLogin(BaseModel): ...
class Token(BaseModel): ...
```
**Impact:** Registration and login will fail because request bodies can't be validated.

---

### BUG #3: Incomplete Endpoint Implementations
**Severity:** CRITICAL  
**File:** `backend/main.py` (Lines 82-88)  
**Issue:** All endpoint handlers use `...` placeholder with no actual implementation.
```python
# CURRENT (BROKEN):
@app.get("/api/v1/test")
def get_test_message(): ...

@app.post("/api/v1/auth/register", status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate): ...

@app.post("/api/v1/auth/login", response_model=Token)
def login_for_access_token(form_data: UserLogin): ...
```
**Impact:** All auth endpoints return `None` instead of expected responses.

---

### BUG #4: Incomplete AI System Prompt
**Severity:** MEDIUM  
**File:** `backend/main.py` (Line 43)  
**Issue:** AI_SYSTEM_PROMPT is incomplete - just shows the beginning and cutoff.
```python
AI_SYSTEM_PROMPT = """You are "FarmerDirect AI"... (your prompt)"""
```
**Impact:** AI responses will be incomplete or inconsistent.

---

### BUG #5: Missing Error Handling for Password Hashing
**Severity:** MEDIUM  
**File:** `backend/security.py`  
**Issue:** No validation that passwords meet minimum strength requirements (length, complexity).
**Impact:** Weak passwords like "123" will be accepted.

---

### BUG #6: Hardcoded JWT Secret Key
**Severity:** CRITICAL  
**File:** `backend/security.py` (Line 6)  
**Issue:** JWT secret is hardcoded in source code instead of environment variable.
```python
JWT_SECRET_KEY = "your-super-secret-key-please-change-me"
```
**Impact:** Security vulnerability - anyone with source code can forge tokens.

---

### BUG #7: Missing Database Initialization
**Severity:** CRITICAL  
**File:** `backend/main.py`  
**Issue:** SQLAlchemy models are defined but never used. Google Sheets is used instead. Models should either:
- Be removed if using Sheets only, OR  
- Actually be used if using SQLite/Postgres
**Impact:** Confused architecture - mix of two database systems.

---

### BUG #8: Incomplete AI Image Handling
**Severity:** HIGH  
**File:** `backend/main.py` (Lines 138-155)  
**Issue:** Image upload handling is incomplete - just sends image URL as text.
```python
# CURRENT (INCOMPLETE):
image_data = {"mime_type": "image/jpeg", "data": query.image_url}
# ... but then just concatenates as string
f"The user has uploaded an image for review at: {query.image_url}"
```
**Impact:** Plant disease diagnosis won't actually see the image.

---

### BUG #9: Missing Input Validation for Weak Passwords
**Severity:** MEDIUM  
**File:** `backend/main.py` - register endpoint  
**Issue:** No validation that password meets minimum requirements (e.g., 8+ chars, mixed case, numbers).
**Impact:** Security risk - weak passwords accepted.

---

### BUG #10: CORS Configuration Too Permissive
**Severity:** MEDIUM  
**File:** `backend/main.py` (Line 73)  
**Issue:** `allow_methods=["*"]` and `allow_headers=["*"]` are too permissive for production.
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],  # ⚠️ Too permissive
    allow_headers=["*"],  # ⚠️ Too permissive
)
```
**Impact:** Security risk in production.

---

## FRONTEND BUGS IDENTIFIED

### BUG #11: Hardcoded Backend URL
**Severity:** MEDIUM  
**File:** `frontend/app/login/page.tsx` (Line 20) and `frontend/app/register/page.tsx` (Line 59)  
**Issue:** Backend URL is hardcoded instead of using environment variable.
```typescript
// CURRENT (PROBLEMATIC):
const response = await fetch('http://localhost:8000/api/v1/auth/login', {
```
**Impact:** Will break in production when backend isn't on localhost:8000.

---

### BUG #12: Missing Dashboard Page
**Severity:** HIGH  
**File:** `frontend/app/login/page.tsx` (Line 40)  
**Issue:** Login redirects to `/dashboard` but page doesn't exist.
```typescript
router.push('/dashboard'); // ❌ Page not created yet
```
**Impact:** Users redirected to 404 page after login.

---

### BUG #13: Missing Forgot Password Page
**Severity:** MEDIUM  
**File:** `frontend/app/login/page.tsx` (Line 56)  
**Issue:** "Forgot Password?" link points to `/forgot-password` which doesn't exist.
```typescript
<Link href="/forgot-password" className="...">  // ❌ Page not created
```
**Impact:** Users can't recover forgotten passwords.

---

### BUG #14: No Token Validation Before Using It
**Severity:** MEDIUM  
**File:** `frontend/app/login/page.tsx` (Line 39)  
**Issue:** Token stored but never validated or decoded to check expiration.
```typescript
localStorage.setItem('token', data.access_token);  // Token never validated
```
**Impact:** Expired tokens won't be detected.

---

### BUG #15: Missing Privacy & Terms Pages
**Severity:** MEDIUM  
**File:** `frontend/app/register/page.tsx` (Lines 204-208)  
**Issue:** Terms and Privacy links point to pages that don't exist.
```typescript
<Link className="..." href="/terms">Terms of Service</Link>
<Link className="..." href="/privacy">Privacy Policy</Link>
```
**Impact:** Users can't review policies before accepting.

---

### BUG #16: No Error Boundary Components
**Severity:** LOW  
**File:** Both pages  
**Issue:** No error boundaries to handle component crashes gracefully.
**Impact:** If any component fails, entire page crashes.

---

### BUG #17: Accessibility Issue - Missing ARIA Labels
**Severity:** LOW  
**File:** `frontend/app/login/page.tsx` and `register/page.tsx`  
**Issue:** Form inputs missing proper ARIA labels for screen readers.
```typescript
<input 
    // Missing aria-label or aria-labelledby
    type="email"
    placeholder="Enter your email address"
/>
```
**Impact:** Not accessible to users with screen readers (WCAG violation).

---

### BUG #18: Missing Loading State
**Severity:** LOW  
**File:** Both auth pages  
**Issue:** Submit button doesn't show loading state while API request is in progress.
```typescript
<button type="submit" className="...">
    <span className="truncate">Log In</span>
    {/* ❌ No loading indicator */}
</button>
```
**Impact:** Users don't know if form is being submitted.

---

### BUG #19: Typo in Accessibility Footer Link
**Severity:** LOW  
**File:** `frontend/app/page.tsx` (Line 312)  
**Issue:** Accessibility styling error in footer.
```tsx
className="text-text-light/7S0 dark:text-text-dark/70"  // ❌ "7S0" should be "70"
```
**Impact:** Footer text will be displayed incorrectly.

---

### BUG #20: Missing Error Handling for Fetch Failures
**Severity:** MEDIUM  
**File:** Both auth pages  
**Issue:** No handling for network errors or fetch failures.
```typescript
try {
    const response = await fetch(...);
    // ❌ Network errors not caught by try-catch
} catch (err: any) {
    setMessage(err.message);
}
```
**Impact:** Network errors will show as empty error messages.

---

## SUMMARY OF ISSUES

| Severity | Count | Issues |
|----------|-------|--------|
| CRITICAL | 5 | Missing client, incomplete schemas, incomplete endpoints, hardcoded JWT, missing DB init |
| HIGH | 2 | Missing dashboard page, incomplete AI image handling |
| MEDIUM | 8 | Hardcoded URLs, no token validation, weak password check, CORS config, error handling, typos |
| LOW | 5 | Missing loading states, ARIA labels, error boundaries |

**Total Bugs Found:** 20

---

## TEST RESULTS SUMMARY

### Backend Tests Status
- ✅ Created comprehensive test suite with 30+ test cases
- ⚠️ Tests won't run until critical bugs are fixed
- 🔴 All endpoints will fail due to incomplete implementations

### Frontend Tests Status  
- ✅ Created 60+ test case specifications
- ⚠️ Jest types need to be installed
- 🔴 Many tests will fail until missing pages are created

---

## PRIORITY FIX ORDER

**PHASE 1 - CRITICAL (Do First)**
1. Fix Google Sheets client initialization
2. Implement complete Pydantic schemas
3. Implement all endpoint handlers
4. Move JWT secret to environment variable
5. Complete AI system prompt

**PHASE 2 - HIGH (Do Soon)**
6. Create dashboard page
7. Fix AI image handling to use actual image data

**PHASE 3 - MEDIUM (Do Before Deploy)**
8. Replace hardcoded backend URLs with env vars
9. Add password strength validation
10. Add token validation/expiration checking
11. Create missing pages (dashboard, forgot-password, terms, privacy)
12. Improve CORS security configuration
13. Add proper error handling for network failures

**PHASE 4 - LOW (Polish)**
14. Add loading states to buttons
15. Add ARIA labels for accessibility
16. Add error boundaries
17. Fix typos in styling
18. Improve error message display

---

## NEXT STEPS

1. Fix all CRITICAL bugs in Phase 1
2. Run backend tests to verify fixes
3. Fix all HIGH severity bugs
4. Set up proper testing infrastructure
5. Deploy with proper environment configuration
