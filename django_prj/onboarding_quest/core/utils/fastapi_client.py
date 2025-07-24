import requests
import json
from django.conf import settings
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class FastAPIClient:
    """FastAPI 서버와 통신하기 위한 클라이언트"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'FASTAPI_BASE_URL', 'http://localhost:8001')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def set_auth_token(self, token: str):
        """JWT 토큰 설정"""
        self.session.headers.update({
            'Authorization': f'Bearer {token}'
        })
    
    def remove_auth_token(self):
        """JWT 토큰 제거"""
        if 'Authorization' in self.session.headers:
            del self.session.headers['Authorization']
    
    def is_server_available(self) -> bool:
        """FastAPI 서버가 사용 가능한지 확인 - 더 안전한 방식"""
        try:
            # 간단한 health check 엔드포인트가 있다면 사용, 없으면 docs 사용
            response = self.session.get(f"{self.base_url}/docs", timeout=2)
            return response.status_code == 200
        except requests.exceptions.Timeout:
            logger.warning("서버 연결 확인 타임아웃")
            return False
        except requests.exceptions.ConnectionError:
            logger.warning("서버 연결 실패")
            return False
        except Exception as e:
            logger.warning(f"서버 연결 확인 중 오류: {e}")
            return False
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """응답 처리 - 더 안전한 에러 처리"""
        try:
            response.raise_for_status()
            
            # 응답이 비어있는 경우 처리
            if not response.content:
                return {"success": True, "message": "요청이 성공적으로 처리되었습니다."}
            
            # Content-Type 확인
            content_type = response.headers.get('content-type', '').lower()
            
            # JSON 응답 파싱 시도
            if 'application/json' in content_type:
                try:
                    return response.json()
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"JSON 파싱 실패: {e}")
                    return {"success": True, "message": "요청이 성공적으로 처리되었습니다."}
            else:
                # JSON이 아닌 응답의 경우
                logger.info(f"Non-JSON response with content-type: {content_type}")
                return {"success": True, "message": "요청이 성공적으로 처리되었습니다."}
                
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error: {e}")
            
            # 응답 본문이 있는 경우 에러 메시지 추출 시도
            error_message = "알 수 없는 오류가 발생했습니다."
            try:
                if response.content:
                    content_type = response.headers.get('content-type', '').lower()
                    if 'application/json' in content_type:
                        error_data = response.json()
                        error_message = error_data.get('detail', error_message)
                    else:
                        error_message = f"HTTP {response.status_code} 오류"
            except (json.JSONDecodeError, ValueError):
                error_message = f"HTTP {response.status_code} 오류"
            
            if response.status_code == 401:
                raise AuthenticationError("인증이 필요합니다.")
            elif response.status_code == 403:
                raise PermissionError("권한이 없습니다.")
            elif response.status_code == 404:
                raise NotFoundError("리소스를 찾을 수 없습니다.")
            else:
                raise APIError(f"API 오류: {error_message}")
                
        except requests.exceptions.Timeout:
            logger.error("Request timeout")
            raise ConnectionError("요청 시간이 초과되었습니다.")
            
        except requests.exceptions.ConnectionError:
            logger.error("Connection error")
            raise ConnectionError("FastAPI 서버에 연결할 수 없습니다.")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request Error: {e}")
            raise ConnectionError("네트워크 오류가 발생했습니다.")
    
    # 인증 관련
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """로그인"""
        url = f"{self.base_url}/api/auth/login"
        data = {"email": email, "password": password}
        response = self.session.post(url, json=data)
        return self._handle_response(response)
    
    def logout(self) -> Dict[str, Any]:
        """로그아웃 - 서버 연결 확인 후 안전한 처리"""
        # 토큰이 없으면 로컬 처리만
        if 'Authorization' not in self.session.headers:
            logger.info("토큰이 없어 로컬 로그아웃만 수행합니다.")
            return {"success": True, "message": "로컬 로그아웃 완료"}
        
        # 서버 연결 확인
        if not self.is_server_available():
            logger.warning("FastAPI 서버가 사용 불가능합니다. 로컬 토큰만 제거합니다.")
            self.remove_auth_token()
            return {"success": True, "message": "로컬 로그아웃 완료"}
        
        # FastAPI 서버 로그아웃 시도
        try:
            url = f"{self.base_url}/api/auth/logout"
            response = self.session.post(url, timeout=5)  # 타임아웃 설정
            
            # 응답 상태 확인
            if response.status_code in [200, 204, 404]:  # 404도 정상으로 처리 (이미 로그아웃됨)
                try:
                    result = response.json() if response.content else {"success": True, "message": "로그아웃 완료"}
                except (json.JSONDecodeError, ValueError):
                    result = {"success": True, "message": "로그아웃 완료"}
            else:
                result = self._handle_response(response)
            
            # 성공적으로 처리되면 토큰 제거
            self.remove_auth_token()
            return result
            
        except (ConnectionError, requests.exceptions.RequestException) as e:
            logger.warning(f"FastAPI 로그아웃 실패: {e}. 로컬 토큰을 제거합니다.")
            self.remove_auth_token()
            return {"success": True, "message": "로컬 로그아웃 완료"}
            
        except Exception as e:
            logger.error(f"예상치 못한 로그아웃 오류: {e}. 로컬 토큰을 제거합니다.")
            self.remove_auth_token()
            return {"success": True, "message": "로컬 로그아웃 완료"}
    
    def get_current_user(self) -> Dict[str, Any]:
        """현재 사용자 정보"""
        url = f"{self.base_url}/api/auth/me"
        response = self.session.get(url)
        return self._handle_response(response)
    
    # 사용자 관리
    def get_users(self, 
                  skip: int = 0, 
                  limit: int = 100,
                  company_id: Optional[str] = None,
                  department_id: Optional[int] = None,
                  search: Optional[str] = None,
                  role: Optional[str] = None,
                  is_active: Optional[bool] = None) -> Dict[str, Any]:
        """사용자 목록 조회"""
        url = f"{self.base_url}/api/users/"
        params = {"skip": skip, "limit": limit}
        if company_id:
            params["company_id"] = company_id
        if department_id:
            params["department_id"] = department_id
        if search:
            params["search"] = search
        if role:
            params["role"] = role
        if is_active is not None:
            params["is_active"] = is_active
        
        response = self.session.get(url, params=params)
        users_list = self._handle_response(response)
        
        # 리스트를 딕셔너리로 래핑
        return {"users": users_list}
    
    def get_user(self, user_id: int) -> Dict[str, Any]:
        """사용자 상세 조회"""
        url = f"{self.base_url}/api/users/{user_id}"
        response = self.session.get(url)
        return self._handle_response(response)
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """사용자 생성"""
        url = f"{self.base_url}/api/users/"
        response = self.session.post(url, json=user_data)
        return self._handle_response(response)
    
    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """사용자 수정"""
        url = f"{self.base_url}/api/users/{user_id}"
        response = self.session.put(url, json=user_data)
        return self._handle_response(response)
    
    def delete_user(self, user_id: int) -> Dict[str, Any]:
        """사용자 삭제"""
        url = f"{self.base_url}/api/users/{user_id}"
        response = self.session.delete(url)
        return self._handle_response(response)
    
    # 부서 관리
    def get_departments(self, company_id: Optional[str] = None) -> Dict[str, Any]:
        """부서 목록 조회"""
        url = f"{self.base_url}/api/departments/"
        params = {}
        if company_id:
            params["company_id"] = company_id
        response = self.session.get(url, params=params)
        departments_list = self._handle_response(response)
        
        # 리스트를 딕셔너리로 래핑
        return {"departments": departments_list}
    
    def get_department(self, department_id: int) -> Dict[str, Any]:
        """부서 상세 조회"""
        url = f"{self.base_url}/api/departments/{department_id}"
        response = self.session.get(url)
        return self._handle_response(response)
    
    def create_department(self, dept_data: Dict[str, Any]) -> Dict[str, Any]:
        """부서 생성"""
        url = f"{self.base_url}/api/departments/"
        response = self.session.post(url, json=dept_data)
        return self._handle_response(response)
    
    def update_department(self, department_id: int, dept_data: Dict[str, Any]) -> Dict[str, Any]:
        """부서 수정"""
        url = f"{self.base_url}/api/departments/{department_id}"
        response = self.session.put(url, json=dept_data)
        return self._handle_response(response)
    
    def delete_department(self, department_id: int) -> Dict[str, Any]:
        """부서 삭제"""
        url = f"{self.base_url}/api/departments/{department_id}"
        response = self.session.delete(url)
        return self._handle_response(response)
    
    # 회사 관리
    def get_companies(self) -> Dict[str, Any]:
        """회사 목록 조회"""
        url = f"{self.base_url}/api/companies/"
        response = self.session.get(url)
        return self._handle_response(response)
    
    def get_company(self, company_id: str) -> Dict[str, Any]:
        """회사 상세 조회"""
        url = f"{self.base_url}/api/companies/{company_id}"
        response = self.session.get(url)
        return self._handle_response(response)
    
    # 태스크 관리
    def get_task_assigns(self, 
                        mentorship_id: Optional[int] = None,
                        user_id: Optional[int] = None,
                        status: Optional[str] = None,
                        week: Optional[int] = None) -> Dict[str, Any]:
        """태스크 할당 목록 조회"""
        url = f"{self.base_url}/api/tasks/assigns"
        params = {}
        if mentorship_id:
            params["mentorship_id"] = mentorship_id
        if user_id:
            params["user_id"] = user_id
        if status:
            params["status"] = status
        if week:
            params["week"] = week
        
        response = self.session.get(url, params=params)
        task_assigns_list = self._handle_response(response)
        
        # 리스트를 딕셔너리로 래핑
        return {"task_assigns": task_assigns_list}
    
    def get_task_assign(self, task_assign_id: int) -> Dict[str, Any]:
        """태스크 할당 상세 조회"""
        url = f"{self.base_url}/api/tasks/assign/{task_assign_id}"
        print(f"DEBUG - FastAPI 태스크 조회 URL: {url}")
        response = self.session.get(url)
        print(f"DEBUG - FastAPI 태스크 조회 응답 상태: {response.status_code}")
        result = self._handle_response(response)
        print(f"DEBUG - FastAPI 태스크 조회 결과: {result}")
        return result
    
    def create_task_assign(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """태스크 할당 생성"""
        url = f"{self.base_url}/api/tasks/assigns"
        response = self.session.post(url, json=task_data)
        return self._handle_response(response)
    
    def update_task_assign(self, task_assign_id: int, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """태스크 할당 수정"""
        url = f"{self.base_url}/api/tasks/assign/{task_assign_id}"
        print(f"DEBUG - FastAPI 태스크 업데이트 URL: {url}")
        print(f"DEBUG - 업데이트 데이터: {task_data}")
        response = self.session.put(url, json=task_data)
        print(f"DEBUG - FastAPI 응답 상태: {response.status_code}")
        return self._handle_response(response)
    
    def delete_task_assign(self, task_assign_id: int) -> Dict[str, Any]:
        """태스크 할당 삭제"""
        url = f"{self.base_url}/api/tasks/assigns/{task_assign_id}"
        response = self.session.delete(url)
        return self._handle_response(response)
    
    # 멘토쉽 관리
    def get_mentorships(self, 
                       mentor_id: Optional[int] = None,
                       mentee_id: Optional[int] = None,
                       is_active: Optional[bool] = None) -> Dict[str, Any]:
        """멘토쉽 목록 조회"""
        url = f"{self.base_url}/api/mentorship/"
        params = {}
        if mentor_id:
            params["mentor_id"] = mentor_id
        elif mentee_id:
            params["mentee_id"] = mentee_id
        if is_active is not None:
            params["is_active"] = is_active
        
        print(f"🔍 FASTAPI_CLIENT - 멘토십 조회 요청:")
        print(f"🔍 FASTAPI_CLIENT - URL: {url}")
        print(f"🔍 FASTAPI_CLIENT - params: {params}")
        
        response = self.session.get(url, params=params)
        print(f"🔍 FASTAPI_CLIENT - 응답 상태: {response.status_code}")
        
        mentorships_list = self._handle_response(response)
        print(f"🔍 FASTAPI_CLIENT - 응답 데이터: {mentorships_list}")
        
        # 리스트를 딕셔너리로 래핑
        result = {"mentorships": mentorships_list}
        print(f"🔍 FASTAPI_CLIENT - 최종 반환 데이터: {result}")
        return result
    
    def get_mentorship(self, mentorship_id: int) -> Dict[str, Any]:
        """멘토쉽 상세 조회"""
        url = f"{self.base_url}/api/mentorship/{mentorship_id}"
        response = self.session.get(url)
        return self._handle_response(response)
    
    def create_mentorship(self, mentorship_data: Dict[str, Any]) -> Dict[str, Any]:
        """멘토쉽 생성"""
        url = f"{self.base_url}/api/mentorship/"
        response = self.session.post(url, json=mentorship_data)
        return self._handle_response(response)
    
    def update_mentorship(self, mentorship_id: int, mentorship_data: Dict[str, Any]) -> Dict[str, Any]:
        """멘토쉽 수정"""
        url = f"{self.base_url}/api/mentorship/{mentorship_id}"
        response = self.session.put(url, json=mentorship_data)
        return self._handle_response(response)
    
    def delete_mentorship(self, mentorship_id: int) -> Dict[str, Any]:
        """멘토쉽 삭제"""
        url = f"{self.base_url}/api/mentorship/{mentorship_id}"
        response = self.session.delete(url)
        return self._handle_response(response)
    
    # 커리큘럼 관리
    def get_curriculums(self, 
                       department_id: Optional[int] = None,
                       common: Optional[bool] = None) -> Dict[str, Any]:
        """커리큘럼 목록 조회 (공통 커리큘럼 + 부서별 커리큘럼 필터링)"""
        url = f"{self.base_url}/api/curriculum/"
        params = {}
        
        # common=True가 명시적으로 요청된 경우 모든 공용 커리큘럼 반환
        if common is True and department_id is None:
            # 공용 커리큘럼만 요청하는 경우, department_id를 None으로 설정
            pass
        elif department_id:
            # department_id가 있으면 공통 + 해당 부서 커리큘럼
            params["department_id"] = department_id
        
        response = self.session.get(url, params=params)
        curriculums_list = self._handle_response(response)
        
        # common=True가 요청되고 department_id가 없는 경우 공용 커리큘럼만 필터링
        if common is True and department_id is None and isinstance(curriculums_list, list):
            curriculums_list = [c for c in curriculums_list if c.get('common', False)]
        
        # 리스트를 딕셔너리로 래핑
        return {"curriculums": curriculums_list}
    
    def get_filtered_curriculums(self, department_id: Optional[int] = None) -> Dict[str, Any]:
        """필터링된 커리큘럼 목록 조회 (공통 커리큘럼 + 특정 부서 커리큘럼)"""
        return self.get_curriculums(department_id=department_id)
    
    def get_curriculum(self, curriculum_id: int) -> Dict[str, Any]:
        """커리큘럼 상세 조회"""
        url = f"{self.base_url}/api/curriculum/{curriculum_id}"
        response = self.session.get(url)
        return self._handle_response(response)
    
    def get_task_manages(self, curriculum_id: Optional[int] = None) -> Dict[str, Any]:
        """태스크 관리 목록 조회"""
        url = f"{self.base_url}/api/tasks/manages"
        params = {}
        if curriculum_id:
            params["curriculum_id"] = curriculum_id
        
        response = self.session.get(url, params=params)
        task_manages_list = self._handle_response(response)
        
        # 리스트를 딕셔너리로 래핑
        return {"task_manages": task_manages_list}
    
    # 태스크 관리 (TaskManage) 메서드들
    def get_task_manage(self, task_manage_id: int) -> Dict[str, Any]:
        """태스크 관리 상세 조회"""
        url = f"{self.base_url}/api/tasks/manages/{task_manage_id}"
        response = self.session.get(url)
        return self._handle_response(response)
    
    def create_task_manage(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """태스크 관리 생성"""
        url = f"{self.base_url}/api/tasks/manages"
        response = self.session.post(url, json=task_data)
        return self._handle_response(response)
    
    def update_task_manage(self, task_manage_id: int, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """태스크 관리 수정"""
        url = f"{self.base_url}/api/tasks/manages/{task_manage_id}"
        response = self.session.put(url, json=task_data)
        return self._handle_response(response)
    
    def delete_task_manage(self, task_manage_id: int) -> Dict[str, Any]:
        """태스크 관리 삭제"""
        url = f"{self.base_url}/api/tasks/manages/{task_manage_id}"
        response = self.session.delete(url)
        return self._handle_response(response)

    def delete_task_manages_by_curriculum(self, curriculum_id: int) -> Dict[str, Any]:
        """커리큘럼별 태스크 관리 일괄 삭제"""
        url = f"{self.base_url}/api/tasks/manages"
        params = {"curriculum_id": curriculum_id, "delete_all": True}
        response = self.session.delete(url, params=params)
        return self._handle_response(response)
    
    # 커리큘럼 관리 추가 메서드들
    def create_curriculum(self, curriculum_data: Dict[str, Any]) -> Dict[str, Any]:
        """커리큘럼 생성"""
        url = f"{self.base_url}/api/curriculum/"
        response = self.session.post(url, json=curriculum_data)
        return self._handle_response(response)
    
    def update_curriculum(self, curriculum_id: int, curriculum_data: Dict[str, Any]) -> Dict[str, Any]:
        """커리큘럼 수정"""
        url = f"{self.base_url}/api/curriculum/{curriculum_id}"
        response = self.session.put(url, json=curriculum_data)
        return self._handle_response(response)
    
    def delete_curriculum(self, curriculum_id: int) -> Dict[str, Any]:
        """커리큘럼 삭제"""
        try:
            url = f"{self.base_url}/api/curriculum/{curriculum_id}"
            logger.info(f"커리큘럼 삭제 요청: {url}")
            response = self.session.delete(url)
            logger.info(f"삭제 응답 상태: {response.status_code}")
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"커리큘럼 삭제 오류: {e}")
            raise APIError(f"커리큘럼 삭제 실패: {str(e)}")

    def copy_curriculum(self, curriculum_id: int, new_data: Dict[str, Any]) -> Dict[str, Any]:
        """커리큘럼 복사"""
        url = f"{self.base_url}/api/curriculum/{curriculum_id}/copy"
        response = self.session.post(url, json=new_data)
        return self._handle_response(response)

    # 메모 관리
    def get_memos(self, task_assign_id: Optional[int] = None, user_id: Optional[int] = None) -> Dict[str, Any]:
        """메모 목록 조회"""
        if task_assign_id:
            # 특정 태스크의 메모 조회
            url = f"{self.base_url}/api/memo/task/{task_assign_id}"
            print(f"DEBUG - 태스크별 메모 조회 URL: {url}")
            response = self.session.get(url)
        elif user_id:
            # 특정 사용자의 메모 조회
            url = f"{self.base_url}/api/memo/user/{user_id}"
            print(f"DEBUG - 사용자별 메모 조회 URL: {url}")
            response = self.session.get(url)
        else:
            # 전체 메모 조회
            url = f"{self.base_url}/api/memo/"
            print(f"DEBUG - 전체 메모 조회 URL: {url}")
            response = self.session.get(url)
        
        print(f"DEBUG - 메모 조회 응답 상태: {response.status_code}")
        memos_list = self._handle_response(response)
        print(f"DEBUG - 조회된 메모: {memos_list}")
        
        # FastAPI가 직접 리스트를 반환하므로, Django views.py와의 호환성을 위해 래핑하지 않고 직접 반환
        return memos_list
    
    def create_memo(self, memo_data: Dict[str, Any]) -> Dict[str, Any]:
        """메모 생성"""
        url = f"{self.base_url}/api/memo/"
        response = self.session.post(url, json=memo_data)
        return self._handle_response(response)
    
    # 문서 관리
    def get_docs(self, department_id: Optional[int] = None, common_doc: Optional[bool] = None) -> Dict[str, Any]:
        """문서 목록 조회"""
        url = f"{self.base_url}/api/docs/"
        params = {}
        if department_id:
            params["department_id"] = department_id
        if common_doc is not None:
            params["common_doc"] = common_doc
        
        response = self.session.get(url, params=params)
        docs_list = self._handle_response(response)
        
        # 리스트를 딕셔너리로 래핑
        return {"docs": docs_list}
    
    def get_doc(self, doc_id: int) -> Dict[str, Any]:
        """문서 상세 조회"""
        url = f"{self.base_url}/api/docs/{doc_id}"
        response = self.session.get(url)
        return self._handle_response(response)
    
    def create_doc(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """문서 생성"""
        url = f"{self.base_url}/api/docs/"
        response = self.session.post(url, json=doc_data)
        return self._handle_response(response)
    
    def delete_doc(self, doc_id: int) -> Dict[str, Any]:
        """문서 삭제"""
        url = f"{self.base_url}/api/docs/{doc_id}"
        response = self.session.delete(url)
        return self._handle_response(response)

    def upload_file(self, file_data, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """파일 업로드"""
        url = f"{self.base_url}/api/docs/upload"
        files = {'file': file_data}
        data = file_info
        
        # 파일 업로드는 multipart/form-data 사용
        response = self.session.post(url, files=files, data=data)
        return self._handle_response(response)


# 커스텀 예외 클래스들
class APIError(Exception):
    """일반적인 API 오류"""
    pass

class AuthenticationError(APIError):
    """인증 오류"""
    pass

class PermissionError(APIError):
    """권한 오류"""
    pass

class NotFoundError(APIError):
    """리소스 없음 오류"""
    pass


# FastAPIClient 클래스에 추가 메소드들
def add_missing_methods():
    """FastAPIClient에 빠진 메소드들 추가"""
    
    def get_curriculum_tasks(self, curriculum_id: int) -> list:
        """커리큘럼의 태스크 목록 조회"""
        try:
            url = f"{self.base_url}/curriculum/{curriculum_id}/tasks"
            logger.info(f"커리큘럼 태스크 조회 요청: {url}")
            response = self.session.get(url)
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"커리큘럼 태스크 조회 오류: {e}")
            raise APIError(f"커리큘럼 태스크 조회 실패: {str(e)}")
    
    def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """태스크 생성"""
        try:
            url = f"{self.base_url}/tasks/"
            logger.info(f"태스크 생성 요청: {url}")
            response = self.session.post(url, json=task_data)
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"태스크 생성 오류: {e}")
            raise APIError(f"태스크 생성 실패: {str(e)}")
    
    def get_mentorships_by_curriculum(self, curriculum_id: int) -> list:
        """커리큘럼을 사용하는 멘토쉽 목록 조회"""
        try:
            url = f"{self.base_url}/mentorship/?curriculum_id={curriculum_id}"
            logger.info(f"멘토쉽 조회 요청: {url}")
            response = self.session.get(url)
            result = self._handle_response(response)
            logger.info(f"멘토쉽 조회 결과: {result}")
            
            # 결과가 리스트인지 확인하고, 아니면 빈 리스트 반환
            if isinstance(result, list):
                return result
            elif isinstance(result, dict) and 'mentorships' in result:
                return result['mentorships']
            else:
                return []
        except Exception as e:
            logger.error(f"멘토쉽 조회 오류: {e}")
            raise APIError(f"멘토쉽 조회 실패: {str(e)}")
    
    # 메소드들을 FastAPIClient 클래스에 동적으로 추가
    FastAPIClient.get_curriculum_tasks = get_curriculum_tasks
    FastAPIClient.create_task = create_task
    FastAPIClient.get_mentorships_by_curriculum = get_mentorships_by_curriculum

# 메소드 추가 실행
add_missing_methods()


# 전역 클라이언트 인스턴스
fastapi_client = FastAPIClient()
