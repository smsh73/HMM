"""
인증 테스트
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.models.database import User
from app.services.auth_service import AuthService

# 테스트 데이터베이스
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """테스트용 데이터베이스 세션"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def setup_database():
    """테스트 데이터베이스 설정"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(setup_database):
    """테스트 사용자 생성"""
    db = TestingSessionLocal()
    auth_service = AuthService(db)
    user = auth_service.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        role="user"
    )
    db.close()
    return user


def test_register_user(setup_database):
    """사용자 등록 테스트"""
    client = TestClient(app)
    response = client.post(
        "/api/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "role": "user"
        }
    )
    assert response.status_code == 200
    assert response.json()["username"] == "newuser"


def test_login(test_user):
    """로그인 테스트"""
    client = TestClient(app)
    response = client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "testpass123"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_invalid_credentials(test_user):
    """잘못된 자격증명 로그인 테스트"""
    client = TestClient(app)
    response = client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401


def test_get_current_user(test_user):
    """현재 사용자 정보 조회 테스트"""
    client = TestClient(app)
    
    # 로그인
    login_response = client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "testpass123"
        }
    )
    token = login_response.json()["access_token"]
    
    # 사용자 정보 조회
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

