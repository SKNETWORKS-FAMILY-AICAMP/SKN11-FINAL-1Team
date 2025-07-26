from django.shortcuts import render

from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import requests
import json
from django.conf import settings

# 임시 멘토십 데이터 (FastAPI 서버가 문제일 때 사용)
def get_temp_mentorship_data(mentor_id=None):
    """임시 멘토십 데이터 생성"""
    temp_data = [
        {
            "id": 1,
            "mentor_id": 1,
            "mentee_id": 2,
            "mentee_name": "김멘티",
            "curriculum_title": "백엔드 개발 기초",
            "total_weeks": 12,
            "completed_tasks": 8,
            "total_tasks": 15,
            "start_date": "2024-01-01",
            "end_date": "2024-03-31",
            "tags": ["Python", "Django"]
        },
        {
            "id": 2,
            "mentor_id": 1,
            "mentee_id": 3,
            "mentee_name": "이학습",
            "curriculum_title": "프론트엔드 개발",
            "total_weeks": 10,
            "completed_tasks": 12,
            "total_tasks": 20,
            "start_date": "2024-02-01",
            "end_date": "2024-04-30",
            "tags": ["JavaScript", "React"]
        }
    ]
    
    if mentor_id:
        return [data for data in temp_data if data["mentor_id"] == int(mentor_id)]
    return temp_data

@csrf_exempt
@require_http_methods(["GET"])
def temp_mentorship_api(request):
    """임시 멘토십 API - FastAPI 서버가 작동하지 않을 때 사용"""
    mentor_id = request.GET.get('mentor_id')
    search = request.GET.get('search', '')
    
    data = get_temp_mentorship_data(mentor_id)
    
    # 검색 필터링
    if search:
        data = [item for item in data if search.lower() in item['mentee_name'].lower()]
    
    return JsonResponse(data, safe=False)


@csrf_exempt
@require_http_methods(["GET"])
def debug_mentorship_from_db(request):
    """디버그용: Django DB에서 직접 멘토쉽 조회"""
    try:
        from core.models import Mentorship, User
        mentor_id = request.GET.get('mentor_id')
        
        if mentor_id:
            mentorships = Mentorship.objects.filter(mentor_id=mentor_id, is_active=True)
        else:
            mentorships = Mentorship.objects.filter(is_active=True)
        
        data = []
        for m in mentorships:
            try:
                mentee = User.objects.get(user_id=m.mentee_id)
                mentor = User.objects.get(user_id=m.mentor_id)
                
                data.append({
                    "id": m.mentorship_id,
                    "mentor_id": m.mentor_id,
                    "mentee_id": m.mentee_id,
                    "curriculum_id": None,
                    "start_date": str(m.start_date) if m.start_date else None,
                    "end_date": str(m.end_date) if m.end_date else None,
                    "status": "active" if m.is_active else "inactive",
                    "created_at": None,
                    "updated_at": None,
                    "mentee_name": f"{mentee.first_name} {mentee.last_name}",
                    "mentor_name": f"{mentor.first_name} {mentor.last_name}",
                    "curriculum_title": m.curriculum_title or "기본 커리큘럼",
                    "total_weeks": m.total_weeks or 12,
                    "total_tasks": 0,  # TODO: TaskAssign에서 계산
                    "completed_tasks": 0,
                    "tags": [mentee.department.department_name if mentee.department else "", 
                            mentee.position or ""]
                })
            except User.DoesNotExist:
                continue
                
        print(f"[DEBUG] Django DB에서 찾은 멘토쉽 수: {len(data)}")
        return JsonResponse(data, safe=False)
        
    except Exception as e:
        print(f"[DEBUG] 디버그 조회 중 오류: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST", "PUT", "DELETE", "PATCH"])
def fastapi_proxy(request, path):
    """FastAPI 서버로 요청을 프록시"""
    
    # 멘토십 생성 요청인 경우 FastAPI로 직접 전달
    if path == "mentorship/create" and request.method == "POST":
        print("[DEBUG] 멘토십 생성 요청 - FastAPI로 전달")
        
    # 요청 URL 구성 - /api/ prefix 추가
    url = f"{settings.FASTAPI_BASE_URL}/api/{path}"
    
    # 쿼리 파라미터 전달
    if request.GET:
        url += "?" + request.GET.urlencode()
    
    print(f"[DEBUG] 프록시 요청: {request.method} {url}")  # 디버그 로그
    
    # 헤더 설정
    headers = {
        'Content-Type': 'application/json',
    }
    
    # 요청 바디
    data = None
    if request.method in ['POST', 'PUT', 'PATCH'] and hasattr(request, '_body'):
        data = request._body
    elif request.method in ['POST', 'PUT', 'PATCH'] and request.body:
        data = request.body
    
    try:
        # FastAPI 서버로 요청 전달
        response = requests.request(
            method=request.method,
            url=url,
            data=data,
            headers=headers,
            timeout=10  # 타임아웃을 10초로 설정
        )
        
        print(f"[DEBUG] FastAPI 응답: {response.status_code}")  # 디버그 로그
        
        # 응답 반환
        return HttpResponse(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('content-type', 'application/json')
        )
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] FastAPI 연결 실패: {e}")  # 에러 로그
        print("[INFO] Django DB에서 직접 조회")
        
        # FastAPI 연결 실패 시 멘토십 데이터는 Django DB에서 직접 조회
        if path == "mentorship/" and request.method == "GET":
            return debug_mentorship_from_db(request)
        
        # 멘토십 생성 실패 시 기본 응답
        if path == "mentorship/create" and request.method == "POST":
            return JsonResponse({
                'success': False,
                'message': f'FastAPI 서버 연결 실패: {str(e)}. 잠시 후 다시 시도해주세요.'
            }, status=500)
        
        return JsonResponse({
            'error': f'FastAPI 서버 연결 실패: {str(e)}'
        }, status=500)

# Create your views here.
