from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from core.models import Alarm
from django.utils import timezone
import json


@login_required
@require_http_methods(["GET"])
def get_alarms(request):
    """로그인한 사용자의 활성화된 알람 목록을 반환"""
    try:
        alarms = Alarm.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-created_at')[:20]  # 최근 20개만 가져오기
        
        alarm_list = []
        for alarm in alarms:
            alarm_list.append({
                'id': alarm.id,
                'message': alarm.message,
                'created_at': alarm.created_at.isoformat() if alarm.created_at else None,
            })
        
        return JsonResponse({
            'success': True,
            'alarms': alarm_list,
            'count': len(alarm_list)
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_alarm_count(request):
    """로그인한 사용자의 활성화된 알람 개수를 반환"""
    try:
        count = Alarm.objects.filter(
            user=request.user,
            is_active=True
        ).count()
        
        return JsonResponse({
            'success': True,
            'count': count
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def mark_alarm_read(request, alarm_id):
    """특정 알람을 읽음 처리 (비활성화)"""
    try:
        alarm = Alarm.objects.get(
            id=alarm_id,
            user=request.user
        )
        alarm.is_active = False
        alarm.save()
        
        return JsonResponse({
            'success': True,
            'message': '알람이 읽음 처리되었습니다.'
        })
    
    except Alarm.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '알람을 찾을 수 없습니다.'
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def mark_all_alarms_read(request):
    """모든 알람을 읽음 처리 (비활성화)"""
    try:
        updated_count = Alarm.objects.filter(
            user=request.user,
            is_active=True
        ).update(is_active=False)
        
        return JsonResponse({
            'success': True,
            'message': f'{updated_count}개의 알람이 읽음 처리되었습니다.',
            'updated_count': updated_count
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
