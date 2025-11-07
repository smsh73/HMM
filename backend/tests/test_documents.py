"""
문서 관리 테스트
"""
import pytest
from fastapi.testclient import TestClient
import os
import tempfile

from app.main import app


@pytest.fixture
def auth_token():
    """인증 토큰 생성"""
    client = TestClient(app)
    
    # 테스트 사용자 등록
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123"
        }
    )
    
    # 로그인
    response = client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "testpass123"
        }
    )
    return response.json()["access_token"]


def test_upload_document(auth_token):
    """문서 업로드 테스트"""
    client = TestClient(app)
    
    # 테스트 파일 생성
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("테스트 문서 내용")
        temp_file = f.name
    
    try:
        with open(temp_file, 'rb') as file:
            response = client.post(
                "/api/documents/upload",
                headers={"Authorization": f"Bearer {auth_token}"},
                files={"file": ("test.txt", file, "text/plain")}
            )
        
        assert response.status_code == 200
        assert response.json()["filename"] == "test.txt"
    finally:
        os.unlink(temp_file)


def test_list_documents(auth_token):
    """문서 목록 조회 테스트"""
    client = TestClient(app)
    response = client.get(
        "/api/documents",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)

