from core.models import Mentorship

def mentorship_context(request):
    """
    로그인한 사용자의 멘토쉽 정보를 모든 템플릿에서 사용할 수 있도록 제공
    """
    context = {}
    
    if request.user.is_authenticated and hasattr(request.user, 'role'):
        print(f"🔍 CONTEXT_PROCESSORS - 사용자 인증됨: user_id={getattr(request.user, 'user_id', '없음')}, role={getattr(request.user, 'role', '없음')}")
        
        if request.user.role == 'mentee':
            # 멘티인 경우 자신이 참여한 활성 멘토쉽 찾기
            try:
                # session과 request.user에서 user_id 확인
                session_user_data = getattr(request, 'session', {}).get('user_data', {})
                session_user_id = session_user_data.get('user_id')
                request_user_id = getattr(request.user, 'user_id', None)
                
                # request.user.user_id를 우선적으로 사용
                user_id = request_user_id if request_user_id else session_user_id
                
                print(f"🔍 CONTEXT_PROCESSORS - 사용자 ID 검증:")
                print(f"🔍 CONTEXT_PROCESSORS - session user_id: {session_user_id}")
                print(f"🔍 CONTEXT_PROCESSORS - request.user.user_id: {request_user_id}")
                print(f"🔍 CONTEXT_PROCESSORS - 최종 user_id: {user_id}")
                
                if not user_id:
                    print("🔍 CONTEXT_PROCESSORS - user_id가 없음")
                    context['user_mentorship'] = None
                    return context
                
                # 모든 멘토십 확인
                all_mentorships = Mentorship.objects.filter(mentee_id=user_id)
                print(f"🔍 CONTEXT_PROCESSORS - 해당 멘티의 모든 멘토십 수: {all_mentorships.count()}")
                for mentorship_obj in all_mentorships:
                    print(f"🔍 CONTEXT_PROCESSORS - 멘토십: ID={mentorship_obj.mentorship_id}, mentee_id={mentorship_obj.mentee_id}, is_active={mentorship_obj.is_active}")
                
                mentorship = Mentorship.objects.filter(
                    mentee_id=user_id,
                    is_active=True
                ).first()
                
                if mentorship:
                    print(f"🔍 CONTEXT_PROCESSORS - 활성 멘토십 발견: mentorship_id={mentorship.mentorship_id}")
                    
                    # 🔧 멘토십 ID가 1인 경우 특별 경고
                    if mentorship.mentorship_id == 1:
                        print("⚠️  CONTEXT_PROCESSORS WARNING - mentorship_id가 1입니다!")
                        print(f"⚠️  사용자 {user_id}의 실제 멘토십이 1번이 맞는지 확인 필요")
                else:
                    print("🔍 CONTEXT_PROCESSORS - 활성 멘토십 없음")
                
                context['user_mentorship'] = mentorship
            except Exception as e:
                print(f"🔍 CONTEXT_PROCESSORS - 멘토십 조회 실패: {e}")
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
