"""
FastAPI 애플리케이션 테스트 스크립트

Django에서 FastAPI로 마이그레이션 후 기본 기능을 테스트합니다.
"""
import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def test_health_check():
    """헬스 체크 테스트"""
    print("=== 헬스 체크 테스트 ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_root_endpoint():
    """루트 엔드포인트 테스트"""
    print("=== 루트 엔드포인트 테스트 ===")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_login(email: str, password: str) -> Dict[str, Any]:
    """로그인 테스트"""
    print(f"=== 로그인 테스트 ({email}) ===")
    
    # Form data로 로그인
    form_data = {
        "username": email,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", data=form_data)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Access Token: {result['access_token'][:50]}...")
        print(f"User Info: {result['user']['first_name']} {result['user']['last_name']}")
        print(f"Role: {result['user']['role']}")
        print(f"Is Admin: {result['user']['is_admin']}")
        return result
    else:
        print(f"Login failed: {response.json()}")
        return {}
    
    print()

def test_protected_endpoint(token: str):
    """보호된 엔드포인트 테스트"""
    print("=== 보호된 엔드포인트 테스트 ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 현재 사용자 정보 조회
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    print(f"Current User - Status Code: {response.status_code}")
    if response.status_code == 200:
        user_info = response.json()
        print(f"User: {user_info['first_name']} {user_info['last_name']}")
        print(f"Email: {user_info['email']}")
        print(f"Role: {user_info['role']}")
    print()

def test_users_endpoint(token: str):
    """사용자 관련 엔드포인트 테스트"""
    print("=== 사용자 관련 엔드포인트 테스트 ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 사용자 목록 조회
    response = requests.get(f"{BASE_URL}/users/", headers=headers)
    print(f"Users List - Status Code: {response.status_code}")
    if response.status_code == 200:
        users = response.json()
        print(f"Total Users: {users['total']}")
        print(f"Users: {len(users['users'])}")
        for user in users['users']:
            print(f"  - {user['first_name']} {user['last_name']} ({user['email']}) - {user['role']}")
    print()

def test_departments_endpoint(token: str):
    """부서 관련 엔드포인트 테스트"""
    print("=== 부서 관련 엔드포인트 테스트 ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 부서 목록 조회
    response = requests.get(f"{BASE_URL}/departments/", headers=headers)
    print(f"Departments List - Status Code: {response.status_code}")
    if response.status_code == 200:
        departments = response.json()
        print(f"Total Departments: {departments['total']}")
        for dept in departments['departments']:
            print(f"  - {dept['department_name']}: {dept['description']}")
    print()

def test_curriculums_endpoint(token: str):
    """커리큘럼 관련 엔드포인트 테스트"""
    print("=== 커리큘럼 관련 엔드포인트 테스트 ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 커리큘럼 목록 조회
    response = requests.get(f"{BASE_URL}/tasks/curriculums", headers=headers)
    print(f"Curriculums List - Status Code: {response.status_code}")
    if response.status_code == 200:
        curriculums = response.json()
        print(f"Total Curriculums: {curriculums['total']}")
        for curriculum in curriculums['curriculums']:
            print(f"  - {curriculum['curriculum_title']}: {curriculum['total_weeks']}주")
    print()

def test_task_manages_endpoint(token: str):
    """과제 템플릿 관련 엔드포인트 테스트"""
    print("=== 과제 템플릿 관련 엔드포인트 테스트 ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 과제 템플릿 목록 조회
    response = requests.get(f"{BASE_URL}/tasks/manages", headers=headers)
    print(f"Task Manages List - Status Code: {response.status_code}")
    if response.status_code == 200:
        tasks = response.json()
        print(f"Total Tasks: {tasks['total']}")
        for task in tasks['tasks']:
            print(f"  - {task['title']} (Week {task['week']}) - {task['priority']}")
    print()

def test_mentorships_endpoint(token: str):
    """멘토쉽 관련 엔드포인트 테스트"""
    print("=== 멘토쉽 관련 엔드포인트 테스트 ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 멘토쉽 목록 조회
    response = requests.get(f"{BASE_URL}/mentorships/", headers=headers)
    print(f"Mentorships List - Status Code: {response.status_code}")
    if response.status_code == 200:
        mentorships = response.json()
        print(f"Total Mentorships: {mentorships['total']}")
        for mentorship in mentorships['mentorships']:
            print(f"  - Mentorship ID: {mentorship['mentorship_id']}")
            print(f"    Mentor ID: {mentorship['mentor_id']}")
            print(f"    Mentee ID: {mentorship['mentee_id']}")
            print(f"    Active: {mentorship['is_active']}")
    print()

def main():
    """메인 테스트 함수"""
    print("🚀 FastAPI 애플리케이션 테스트 시작\n")
    
    # 기본 엔드포인트 테스트
    test_health_check()
    test_root_endpoint()
    
    # 로그인 테스트
    login_result = test_login("admin@example.com", "admin123")
    
    if login_result:
        token = login_result["access_token"]
        
        # 보호된 엔드포인트 테스트
        test_protected_endpoint(token)
        test_users_endpoint(token)
        test_departments_endpoint(token)
        test_curriculums_endpoint(token)
        test_task_manages_endpoint(token)
        test_mentorships_endpoint(token)
        
        print("✅ 모든 테스트 완료!")
    else:
        print("❌ 로그인 실패로 인해 테스트 중단")
        
    print("\n📝 테스트 결과:")
    print("- 서버가 실행 중인지 확인하세요: uvicorn app.main:app --reload")
    print("- 데이터베이스가 초기화되었는지 확인하세요: python -m app.init_db")
    print("- API 문서는 http://localhost:8000/docs 에서 확인할 수 있습니다")

if __name__ == "__main__":
    main() 