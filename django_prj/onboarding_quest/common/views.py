from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

def home(request):
    """홈 페이지 - 로그인 상태에 따라 리다이렉트"""
    if request.user.is_authenticated:
        # 역할에 따른 리다이렉트
        if request.user.role == 'admin':
            return redirect('account:supervisor')
        elif request.user.role == 'mentor':
            return redirect('mentor:mentor')
        elif request.user.role == 'mentee':
            return redirect('mentee:mentee')
        else:
            return redirect('common:dashboard')
    else:
        return redirect('account:login')

@login_required
def dashboard(request):
    """통합 대시보드"""
    return render(request, 'common/integrated_dashboard.html')

@login_required
def chatbot(request):
    return render(request, 'common/chatbot.html')

@login_required
def doc(request):
    return render(request, 'common/doc.html')

@login_required
@require_http_methods(["POST"])
def doc_upload(request):
    """문서 업로드 처리 - FastAPI로 프록시"""
    try:
        # FormData에서 데이터 가져오기
        uploaded_file = request.FILES.get('file')
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        tags = request.POST.get('tags', '')
        common_doc = request.POST.get('common_doc', 'false').lower() == 'true'
        
        if not name:
            return JsonResponse({
                'success': False,
                'error': '파일명이 필요합니다.'
            }, status=400)
        
        # FastAPI로 파일 업로드 요청 전송
        import requests
        
        files = {'file': (uploaded_file.name, uploaded_file.read(), uploaded_file.content_type)} if uploaded_file else {}
        data = {
            'name': name,
            'description': description,
            'tags': tags,
            'common_doc': common_doc
        }
        
        response = requests.post(
            f'{settings.FASTAPI_BASE_URL}/api/v1/common/doc/upload',
            files=files,
            data=data,
            headers={
                'Authorization': f'Bearer {request.user.email}'
            }
        )
        
        if response.status_code == 200:
            return JsonResponse(response.json())
        else:
            error_data = response.json() if response.headers.get('content-type') == 'application/json' else {'detail': response.text}
            return JsonResponse({
                'success': False,
                'error': error_data.get('detail', '문서 업로드 중 오류가 발생했습니다.')
            }, status=500)
        
    except Exception as e:
        logger.error(f"문서 업로드 API 에러: {e}")
        return JsonResponse({
            'success': False,
            'error': f'문서 업로드 중 오류가 발생했습니다: {str(e)}'
        }, status=500)

 
@login_required
def task_add(request):
    return render(request, 'common/task_add.html')
