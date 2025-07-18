from core.models import Mentorship

def mentorship_context(request):
    """
    로그인한 사용자의 멘토쉽 정보를 모든 템플릿에서 사용할 수 있도록 제공
    """
    context = {}
    
    if request.user.is_authenticated and hasattr(request.user, 'role'):
        if request.user.role == 'mentee':
            # 멘티인 경우 자신이 참여한 활성 멘토쉽 찾기
            try:
                mentorship = Mentorship.objects.filter(
                    mentee_id=request.user.user_id,
                    is_active=True
                ).first()
                context['user_mentorship'] = mentorship
            except Exception:
                context['user_mentorship'] = None
        elif request.user.role == 'mentor':
            # 멘토인 경우 자신이 담당한 활성 멘토쉽들 찾기
            try:
                mentorships = Mentorship.objects.filter(
                    mentor_id=request.user.user_id,
                    is_active=True
                )
                context['user_mentorships'] = mentorships
            except Exception:
                context['user_mentorships'] = []
    
    return context
