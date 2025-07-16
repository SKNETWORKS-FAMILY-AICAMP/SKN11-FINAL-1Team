"""
Django에서 FastAPI를 호출하기 위한 API 클라이언트
"""
import httpx
from django.conf import settings
from typing import Optional, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

class FastAPIClient:
    """FastAPI 서버와 통신하기 위한 클라이언트"""
    
    def __init__(self):
        self.base_url = settings.FASTAPI_BASE_URL
        self.api_v1_str = settings.FASTAPI_API_V1_STR
        self.client = httpx.Client(base_url=self.base_url, timeout=30.0)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
    
    def _get_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        """API 호출을 위한 헤더 생성"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers
    
    def get(self, endpoint: str, params: Optional[Dict] = None, token: Optional[str] = None) -> Dict[str, Any]:
        """GET 요청"""
        try:
            url = f"{self.api_v1_str}{endpoint}"
            response = self.client.get(
                url,
                params=params,
                headers=self._get_headers(token)
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"FastAPI GET 요청 실패: {endpoint} - {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"FastAPI GET HTTP 에러: {endpoint} - {e.response.status_code}")
            raise
    
    def post(self, endpoint: str, data: Optional[Dict] = None, token: Optional[str] = None) -> Dict[str, Any]:
        """POST 요청"""
        try:
            url = f"{self.api_v1_str}{endpoint}"
            response = self.client.post(
                url,
                json=data,
                headers=self._get_headers(token)
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"FastAPI POST 요청 실패: {endpoint} - {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"FastAPI POST HTTP 에러: {endpoint} - {e.response.status_code}")
            raise
    
    def put(self, endpoint: str, data: Optional[Dict] = None, token: Optional[str] = None) -> Dict[str, Any]:
        """PUT 요청"""
        try:
            url = f"{self.api_v1_str}{endpoint}"
            response = self.client.put(
                url,
                json=data,
                headers=self._get_headers(token)
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"FastAPI PUT 요청 실패: {endpoint} - {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"FastAPI PUT HTTP 에러: {endpoint} - {e.response.status_code}")
            raise
    
    def delete(self, endpoint: str, token: Optional[str] = None) -> Dict[str, Any]:
        """DELETE 요청"""
        try:
            url = f"{self.api_v1_str}{endpoint}"
            response = self.client.delete(
                url,
                headers=self._get_headers(token)
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"FastAPI DELETE 요청 실패: {endpoint} - {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"FastAPI DELETE HTTP 에러: {endpoint} - {e.response.status_code}")
            raise

# 편의 함수들
def get_fastapi_client() -> FastAPIClient:
    """FastAPI 클라이언트 인스턴스 생성"""
    return FastAPIClient()

def call_fastapi_auth(email: str, password: str) -> Dict[str, Any]:
    """FastAPI 인증 호출"""
    with get_fastapi_client() as client:
        return client.post("/auth/login", {
            "email": email,
            "password": password
        })

def call_fastapi_users(token: str, page: int = 1, size: int = 20) -> Dict[str, Any]:
    """FastAPI 사용자 목록 호출"""
    with get_fastapi_client() as client:
        return client.get("/users/", {
            "page": page,
            "size": size
        }, token=token)

def call_fastapi_user_stats(token: str) -> Dict[str, Any]:
    """FastAPI 사용자 통계 호출"""
    with get_fastapi_client() as client:
        return client.get("/users/stats", token=token)

def call_fastapi_mentorship_stats(token: str) -> Dict[str, Any]:
    """FastAPI 멘토쉽 통계 호출"""
    with get_fastapi_client() as client:
        return client.get("/mentorship/stats", token=token)

def call_fastapi_task_stats(token: str) -> Dict[str, Any]:
    """FastAPI 과제 통계 호출"""
    with get_fastapi_client() as client:
        return client.get("/tasks/stats", token=token) 