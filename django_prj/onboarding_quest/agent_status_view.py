# Agent 시스템 상태 조회 및 제어를 위한 뷰
"""
Django에서 Agent 시스템을 모니터링하고 제어하기 위한 뷰
"""

from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import logging
import json

logger = logging.getLogger(__name__)

@login_required
def agent_status_dashboard(request):
    """Agent 시스템 상태 대시보드"""
    try:
        from agent_integration import get_agent_current_status
        status = get_agent_current_status()
        
        context = {
            'agent_status': status,
            'title': 'Agent 시스템 상태'
        }
        
        return render(request, 'agent/status_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"❌ Agent 상태 대시보드 오류: {e}")
        return render(request, 'agent/status_dashboard.html', {
            'error': str(e),
            'title': 'Agent 시스템 상태'
        })

@csrf_exempt
@require_http_methods(["GET"])
def get_agent_status_api(request):
    """Agent 시스템 상태 API (JSON 응답)"""
    try:
        from agent_integration import get_agent_current_status
        status = get_agent_current_status()
        
        return JsonResponse({
            'success': True,
            'status': status,
            'timestamp': str(timezone.now())
        })
        
    except Exception as e:
        logger.error(f"❌ Agent 상태 API 오류: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt 
@require_http_methods(["POST"])
@login_required
def trigger_agent_check_api(request):
    """Agent 즉시 체크 트리거 API"""
    try:
        from agent_integration import trigger_agent_check
        trigger_agent_check()
        
        return JsonResponse({
            'success': True,
            'message': 'Agent 체크가 트리거되었습니다.',
            'timestamp': str(timezone.now())
        })
        
    except Exception as e:
        logger.error(f"❌ Agent 체크 트리거 API 오류: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def restart_agent_system_api(request):
    """Agent 시스템 재시작 API (관리자용)"""
    try:
        # 관리자 권한 체크
        if not request.user.is_staff:
            return JsonResponse({
                'success': False,
                'error': '관리자 권한이 필요합니다.'
            }, status=403)
        
        from agent_integration import stop_agent_system, start_agent_system
        
        # 시스템 중지 후 재시작
        stop_agent_system()
        start_agent_system()
        
        return JsonResponse({
            'success': True,
            'message': 'Agent 시스템이 재시작되었습니다.',
            'timestamp': str(timezone.now())
        })
        
    except Exception as e:
        logger.error(f"❌ Agent 시스템 재시작 API 오류: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def manual_task_status_change(request):
    """수동 태스크 상태 변화 이벤트 트리거 (테스트용)"""
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        old_status = data.get('old_status')
        new_status = data.get('new_status') 
        user_id = data.get('user_id')
        
        if not all([task_id, old_status, new_status, user_id]):
            return JsonResponse({
                'success': False,
                'error': '필수 필드가 누락되었습니다: task_id, old_status, new_status, user_id'
            }, status=400)
        
        from agent_integration import handle_task_status_change
        handle_task_status_change(task_id, old_status, new_status, user_id)
        
        return JsonResponse({
            'success': True,
            'message': f'태스크 상태 변화 이벤트가 처리되었습니다: {old_status} -> {new_status}',
            'task_id': task_id,
            'timestamp': str(timezone.now())
        })
        
    except Exception as e:
        logger.error(f"❌ 수동 태스크 상태 변화 처리 오류: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
