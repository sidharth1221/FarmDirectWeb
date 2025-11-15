import os
import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Import test fixtures from conftest
# conftest.py handles database setup and client creation

from security import hash_password, validate_password_strength, create_access_token, verify_token
from main import app

# Use the test_client fixture which is auto-configured
@pytest.fixture
def client(test_client):
    return test_client

# -------------------------
# Health check
# -------------------------

def test_health_check(client):
    r = client.get("/api/v1/test")
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") == "healthy"
    assert isinstance(body.get("message"), str)

# -------------------------
# Registration success / failure
# -------------------------

def test_register_success(client):
    payload = {
        "fullName": "Test Farmer",
        "email": "farmer1@example.com",
        "password": "StrongPass123",
        "role": "farmer"
    }
    r = client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data.get("email") == payload["email"]
    assert data.get("user_id") is not None

def test_register_duplicate_email(client):
    # Register first user
    payload1 = {
        "fullName": "First User",
        "email": "duplicate@example.com",
        "password": "StrongPass123",
        "role": "farmer"
    }
    r1 = client.post("/api/v1/auth/register", json=payload1)
    assert r1.status_code == 201
    
    # Try to register with same email
    payload2 = {
        "fullName": "Second User",
        "email": "duplicate@example.com",
        "password": "DifferentPass123",
        "role": "farmer"
    }
    r2 = client.post("/api/v1/auth/register", json=payload2)
    assert r2.status_code == 409

# Parameterized weak passwords (length <8)
@pytest.mark.parametrize("pw", ["", "123", "short7"])
def test_register_weak_passwords(pw, client):
    payload = {"fullName":"A","email":"a@example.com","password":pw,"role":"farmer"}
    r = client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 400

# Invalid email formats
@pytest.mark.parametrize("email", ["no-at", "@no-local.com", "user@@example.com"])
def test_register_invalid_email(email, client):
    payload = {"fullName":"A","email":email,"password":"StrongPass123","role":"farmer"}
    r = client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 422

# Missing fields
def test_register_missing_fields(client):
    payload = {"fullName":"A","email":"ok@example.com"}
    r = client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 422

# -------------------------
# Login tests
# -------------------------

def test_login_success(client):
    # First register
    register_payload = {
        "fullName": "Login Test",
        "email": "login@example.com",
        "password": "LoginPass123",
        "role": "farmer"
    }
    client.post("/api/v1/auth/register", json=register_payload)
    
    # Then login
    login_payload = {
        "email": "login@example.com",
        "password": "LoginPass123"
    }
    r = client.post("/api/v1/auth/login", json=login_payload)
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body

def test_login_wrong_password(client):
    # Register first
    register_payload = {
        "fullName": "Wrong Pass Test",
        "email": "wrongpass@example.com",
        "password": "CorrectPassword1",
        "role": "farmer"
    }
    client.post("/api/v1/auth/register", json=register_payload)
    
    # Try with wrong password
    r = client.post("/api/v1/auth/login", json={"email":"wrongpass@example.com","password":"WrongPass"})
    assert r.status_code == 401

def test_login_user_not_found(client):
    r = client.post("/api/v1/auth/login", json={"email":"noone@example.com","password":"x"})
    assert r.status_code == 401

def test_login_missing_fields(client):
    r = client.post("/api/v1/auth/login", json={"email":"nope@example.com"})
    assert r.status_code == 422

# -------------------------
# Cloudinary signature
# -------------------------

@patch.dict(os.environ, {"CLOUDINARY_CLOUD_NAME":"c","CLOUDINARY_API_KEY":"k","CLOUDINARY_API_SECRET":"s"})
@patch('main.cloudinary.utils.api_sign_request')
def test_cloudinary_signature_success(mock_sign, client):
    # Register and login first to get auth token
    register_payload = {
        "fullName": "Cloudinary User",
        "email": "cloudinary@example.com",
        "password": "CloudinaryPass123",
        "role": "farmer"
    }
    client.post("/api/v1/auth/register", json=register_payload)
    
    login_r = client.post("/api/v1/auth/login", json={"email":"cloudinary@example.com","password":"CloudinaryPass123"})
    token = login_r.json()["access_token"]
    
    mock_sign.return_value = "sig123"
    r = client.post("/api/v1/uploads/request-cloudinary-signature", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    b = r.json()
    assert "signature" in b and b["signature"] == "sig123"

@patch.dict(os.environ, {"CLOUDINARY_CLOUD_NAME":"","CLOUDINARY_API_KEY":"","CLOUDINARY_API_SECRET":""})
def test_cloudinary_missing_config(client):
    # Register and login first
    register_payload = {
        "fullName": "No Config User",
        "email": "noconfig@example.com",
        "password": "NoConfigPass123",
        "role": "farmer"
    }
    client.post("/api/v1/auth/register", json=register_payload)
    
    login_r = client.post("/api/v1/auth/login", json={"email":"noconfig@example.com","password":"NoConfigPass123"})
    token = login_r.json()["access_token"]
    
    r = client.post("/api/v1/uploads/request-cloudinary-signature", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 503

# -------------------------
# AI assistant (Disabled - now using YOLOv4 for produce grading only)
# -------------------------

def test_ai_text_query(client):
    # Register and login as farmer first
    payload = {
        "fullName": "AI Test Farmer",
        "email": "aifarmer@example.com",
        "password": "AIPass123",
        "role": "farmer"
    }
    client.post("/api/v1/auth/register", json=payload)
    
    login_r = client.post("/api/v1/auth/login", json={"email":"aifarmer@example.com","password":"AIPass123"})
    token = login_r.json()["access_token"]
    
    r = client.post("/api/v1/ai-assistant/ask", json={"query":"How to irrigate?", "image_url": None}, headers={"Authorization": f"Bearer {token}"})
    # AI Assistant is now disabled
    assert r.status_code == 503

def test_ai_image_query(client):
    # Register and login as farmer first
    payload = {
        "fullName": "AI Image Test",
        "email": "aiimage@example.com",
        "password": "AIPass123",
        "role": "farmer"
    }
    client.post("/api/v1/auth/register", json=payload)
    
    login_r = client.post("/api/v1/auth/login", json={"email":"aiimage@example.com","password":"AIPass123"})
    token = login_r.json()["access_token"]
    
    r = client.post("/api/v1/ai-assistant/ask", json={"query":"What's wrong","image_url":"http://x.jpg"}, headers={"Authorization": f"Bearer {token}"})
    # AI Assistant is now disabled
    assert r.status_code == 503

def test_ai_empty_query(client):
    # Register and login first
    payload = {
        "fullName": "Empty Query",
        "email": "emptyquery@example.com",
        "password": "EmptyPass123",
        "role": "farmer"
    }
    client.post("/api/v1/auth/register", json=payload)
    
    login_r = client.post("/api/v1/auth/login", json={"email":"emptyquery@example.com","password":"EmptyPass123"})
    token = login_r.json()["access_token"]
    
    r = client.post("/api/v1/ai-assistant/ask", json={"query":"", "image_url": None}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 400

def test_ai_missing_model(client):
    # Register and login
    payload = {
        "fullName": "No Model",
        "email": "nomodel@example.com",
        "password": "NoModelPass123",
        "role": "farmer"
    }
    client.post("/api/v1/auth/register", json=payload)
    
    login_r = client.post("/api/v1/auth/login", json={"email":"nomodel@example.com","password":"NoModelPass123"})
    token = login_r.json()["access_token"]
    
    # AI Assistant is now disabled
    r = client.post("/api/v1/ai-assistant/ask", json={"query":"How?"}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 503

# -------------------------
# Security helpers tests
# -------------------------

@pytest.mark.parametrize("pw,ok", [
    ("Password1", True),
    ("pass", False),
    ("PASSWORD1", False),
    ("Password", False),
    ("Pass1234", True),
])
def test_validate_password_strength(pw, ok, client):
    valid, msg = validate_password_strength(pw)
    assert valid == ok


def test_create_and_verify_token(client):
    token = create_access_token({"sub":"a@b.com","role":"farmer"})
    payload = verify_token(token)
    assert payload is not None
    assert payload.get("sub") == "a@b.com"

# -------------------------
# Edge cases
# -------------------------

def test_register_then_login(client):
    # Complete flow test
    register_payload = {
        "fullName": "Complete Test",
        "email": "complete@example.com",
        "password": "CompletePass123",
        "role": "farmer"
    }
    reg_r = client.post("/api/v1/auth/register", json=register_payload)
    assert reg_r.status_code == 201
    
    login_r = client.post("/api/v1/auth/login", json={"email":"complete@example.com","password":"CompletePass123"})
    assert login_r.status_code == 200
    assert "access_token" in login_r.json()

# -------------------------
# CORS/middleware presence
# -------------------------

def test_cors_middleware_present(client):
    found = any('CORSMiddleware' in repr(middleware) for middleware in app.user_middleware)
    assert found

# -------------------------
# Additional negative tests
# -------------------------
@pytest.mark.parametrize("payload", [
    {},
    {"email":"x"},
    {"password":"p"},
])
def test_register_various_bad_payloads(payload, client):
    r = client.post("/api/v1/auth/register", json=payload)
    assert r.status_code in (400, 422)

@pytest.mark.parametrize("payload", [
    {},
    {"email":"x@x.com"},
    {"password":"p"},
])
def test_login_various_bad_payloads(payload, client):
    r = client.post("/api/v1/auth/login", json=payload)
    assert r.status_code in (400, 401, 422)

