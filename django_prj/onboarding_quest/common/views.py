from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
@csrf_exempt
def doc_upload(request):
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            data = json.loads(request.body)
            title = data.get('name')
            description = data.get('description')
            tags = data.get('tags')
            common_doc = data.get('common_doc', False)
            department = request.user.department
            if not title or not department:
                return JsonResponse({'success': False, 'error': '필수 정보 누락'})
            doc = Docs.objects.create(
                title=title,
                description=description,
                department=department,
                file_path='',  # 파일 업로드 미구현, 경로는 빈 값
                common_doc=common_doc
            )
            # 태그 필드가 있으면 추가 구현 필요
            return JsonResponse({'success': True, 'doc_id': doc.docs_id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': '권한 없음 또는 잘못된 요청'})

from django.shortcuts import render
from core.models import Docs

def chatbot(request):
    return render(request, 'common/chatbot.html')

def doc(request):
    user = request.user
    # 공통문서
    common_docs = Docs.objects.filter(common_doc=True)
    # 유저 부서 문서 (공통문서가 아닌 것)
    dept_docs = Docs.objects.filter(department=user.department, common_doc=False) if user.is_authenticated and user.department else Docs.objects.none()
    # 합치기 (중복 방지)
    all_docs = list(common_docs) + [doc for doc in dept_docs if doc not in common_docs]
    return render(request, 'common/doc.html', {'core_docs': all_docs})

def task_add(request):
    return render(request, 'common/task_add.html')

@csrf_exempt
def doc_delete(request, doc_id):
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            doc = Docs.objects.get(pk=doc_id)
            # 관리부서 체크: 본인 부서만 삭제 가능
            if doc.department != request.user.department:
                return JsonResponse({'success': False, 'error': '권한이 없습니다.'})
            doc.delete()
            return JsonResponse({'success': True})
        except Docs.DoesNotExist:
            return JsonResponse({'success': False, 'error': '문서를 찾을 수 없습니다.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': '권한 없음 또는 잘못된 요청'})