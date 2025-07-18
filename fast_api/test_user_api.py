import requests
import json

# FastAPI 서버가 실행 중인지 확인하고 User API 테스트
try:
    response = requests.get('http://localhost:8000/api/users/')
    if response.status_code == 200:
        users = response.json()
        if users:
            print('첫 번째 사용자 데이터 구조:')
            print(json.dumps(users[0], indent=2, ensure_ascii=False))
            
            # department 필드 확인
            if 'department' in users[0]:
                print('\ndepartment 필드 존재:', users[0]['department'])
            else:
                print('\ndepartment 필드 없음')
        else:
            print('사용자 데이터가 없습니다.')
    else:
        print(f'API 응답 오류: {response.status_code}')
except Exception as e:
    print(f'FastAPI 서버 연결 실패: {e}')
