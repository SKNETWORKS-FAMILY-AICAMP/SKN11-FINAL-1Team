from django.utils.deprecation import MiddlewareMixin
from core.utils.fastapi_client import fastapi_client


class FastAPITokenMiddleware(MiddlewareMixin):
    """JWT 토큰을 자동으로 FastAPI 클라이언트에 설정하는 미들웨어"""
    
    def process_request(self, request):
        # 세션에서 JWT 토큰 가져오기
        jwt_token = request.session.get('jwt_token')
        
        if jwt_token:
            # FastAPI 클라이언트에 토큰 설정
            fastapi_client.set_auth_token(jwt_token)
        else:
            # 토큰이 없으면 인증 헤더 제거
            fastapi_client.remove_auth_token()
        
        return None
    
    def process_response(self, request, response):
        return response
