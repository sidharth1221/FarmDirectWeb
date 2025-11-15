import pytest
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path so we can import modules  
sys.path.insert(0, str(Path(__file__).parent.parent))

# Create a temporary directory for test database
test_db_dir = tempfile.mkdtemp()
test_db_path = os.path.join(test_db_dir, "test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{test_db_path}"

# Mock ultralytics and torch before importing main to avoid heavy dependencies during testing
sys.modules['ultralytics'] = MagicMock()
sys.modules['torch'] = MagicMock()
sys.modules['torchvision'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['numpy'] = MagicMock()

# Create mock YOLO class
class MockYOLO:
    def __init__(self, *args, **kwargs):
        pass
    def __call__(self, image):
        mock_results = MagicMock()
        mock_results.boxes = None
        return [mock_results]

sys.modules['ultralytics'].YOLO = MockYOLO

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Create test database engine
test_engine = create_engine(
    f"sqlite:///{test_db_path}",
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Import database - will now use our test database path
import database
import models
from main import app
from database import get_db

# Override database module to use test engine
database.engine = test_engine
database.SessionLocal = TestingSessionLocal

# Create all tables
models.Base.metadata.create_all(bind=test_engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture(scope="session")
def test_db_engine():
    """Provides the test database engine"""
    return test_engine

@pytest.fixture(scope="session")
def test_db_session_local():
    """Provides the test session factory"""
    return TestingSessionLocal

@pytest.fixture(scope="session")
def test_client():
    """Create a test client with overridden dependencies"""
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)




