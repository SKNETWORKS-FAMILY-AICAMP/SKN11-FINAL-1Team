import sqlite3
import random
from datetime import datetime, timedelta

def create_database():
    # 데이터베이스 연결
    conn = sqlite3.connect('task_management.db')
    cursor = conn.cursor()
    
    # 기존 테이블 삭제 (있다면)
    cursor.execute('DROP TABLE IF EXISTS memo')
    cursor.execute('DROP TABLE IF EXISTS subtask')
    cursor.execute('DROP TABLE IF EXISTS task_assign')
    cursor.execute('DROP TABLE IF EXISTS users')
    
    # users 테이블 생성
    cursor.execute('''
    CREATE TABLE users (
        user_id INTEGER PRIMARY KEY,
        username VARCHAR NOT NULL UNIQUE,
        email VARCHAR NOT NULL UNIQUE,
        created_at DATE DEFAULT CURRENT_DATE
    )
    ''')
    
    # task_assign 테이블 생성
    cursor.execute('''
    CREATE TABLE task_assign (
        task_assign_id INTEGER PRIMARY KEY,
        title VARCHAR NOT NULL,
        start_date DATE,
        end_date DATE,
        status INTEGER DEFAULT 0,
        difficulty VARCHAR,
        guide VARCHAR,
        exp NUMERIC DEFAULT 0,
        order_num INTEGER DEFAULT 0,
        mentorship_id INTEGER,
        user_id INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')
    
    # subtask 테이블 생성
    cursor.execute('''
    CREATE TABLE subtask (
        subtask_id INTEGER PRIMARY KEY,
        task_assign_id INTEGER NOT NULL,
        subtask_title VARCHAR NOT NULL,
        guide VARCHAR,
        content VARCHAR,
        FOREIGN KEY (task_assign_id) REFERENCES task_assign(task_assign_id)
    )
    ''')
    
    # memo 테이블 생성
    cursor.execute('''
    CREATE TABLE memo (
        memo_id INTEGER PRIMARY KEY,
        create_date DATE DEFAULT CURRENT_DATE,
        comment VARCHAR,
        task_assign_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        FOREIGN KEY (task_assign_id) REFERENCES task_assign(task_assign_id),
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')
    
    return conn, cursor

def get_detailed_task_data():
    """각 작업별 상세한 subtask와 memo 데이터를 정의"""
    
    task_details = {
        '성능 최적화': {
            'guide': '시스템 성능 병목점을 찾아 개선하는 전체적인 접근 방법',
            'subtasks': [
                ('성능 측정 도구 설정', '프로파일링 도구 설치 및 설정', 'New Relic, DataDog 등의 APM 도구를 설정하여 실시간 성능 모니터링 환경 구축'),
                ('병목점 식별', '시스템에서 가장 느린 부분 찾기', 'CPU, 메모리, 디스크 I/O, 네트워크 등 각 구간별 성능 측정하여 bottleneck 구간 파악'),
                ('데이터베이스 쿼리 최적화', 'SQL 쿼리 성능 개선', '인덱스 추가, N+1 쿼리 문제 해결, 쿼리 실행계획 분석을 통한 최적화'),
                ('캐싱 전략 구현', '자주 사용되는 데이터 캐싱', 'Redis를 활용한 세션 캐시, API 응답 캐시, 페이지 캐시 구현')
            ],
            'memos': [
                '1단계: 성능 측정 도구 설정 완료. New Relic APM을 프로덕션 서버에 적용하여 baseline 성능 데이터 수집 시작. 평균 응답시간 2.3초로 측정됨.',
                '2단계: 병목점 분석 결과 - 데이터베이스 쿼리가 전체 응답시간의 65%를 차지함을 확인. 특히 사용자 목록 조회 API에서 평균 1.5초 소요.',
                '3단계: 가장 느린 쿼리 TOP 5 식별. users 테이블 JOIN 쿼리에서 인덱스 누락 발견. email 컬럼과 created_at 컬럼에 복합 인덱스 생성 예정.',
                '4단계: 인덱스 추가 후 쿼리 성능 70% 향상. 1.5초 → 0.45초로 단축. 다음은 Redis 캐시 적용 단계로 진행.',
                '5단계: Redis 캐시 구현 완료. 자주 조회되는 사용자 프로필 데이터를 30분간 캐싱. 전체 응답시간 2.3초 → 0.8초로 개선 (65% 향상).'
            ]
        },
        
        '코드 리뷰': {
            'guide': '팀 코드 품질 향상을 위한 체계적인 리뷰 프로세스',
            'subtasks': [
                ('리뷰 가이드라인 수립', '코드 리뷰 체크리스트 작성', '네이밍 컨벤션, 함수 복잡도, 보안 이슈, 테스트 커버리지 등을 포함한 리뷰 기준 문서화'),
                ('정적 분석 도구 도입', '자동화된 코드 품질 검사', 'SonarQube, ESLint, Prettier 등을 CI/CD 파이프라인에 통합'),
                ('Pull Request 템플릿 개선', 'PR 설명 표준화', '변경사항 요약, 테스트 방법, 스크린샷 등을 포함한 템플릿 작성'),
                ('리뷰 프로세스 자동화', '리뷰어 자동 할당 시스템', 'GitHub Actions를 활용한 코드 오너십 기반 리뷰어 자동 배정')
            ],
            'memos': [
                '리뷰 가이드라인 초안 작성 완료. 주요 항목: 1) 함수는 50줄 이하 2) 복잡도 10 이하 3) 테스트 커버리지 80% 이상 4) 하드코딩 금지. 팀 검토 예정.',
                '정적 분석 도구 검토 중. SonarQube Community 버전 설치하여 기존 코드베이스 스캔. 총 247개 이슈 발견 (Critical: 12, Major: 89, Minor: 146).',
                '실제 코드 리뷰 사례: UserService.js의 getUserProfile() 함수에서 발견된 문제점들 - 1) try-catch 누락으로 에러 핸들링 부재 2) SQL Injection 취약점 존재 3) 불필요한 nested loop로 O(n²) 복잡도',
                'PR #156 리뷰 완료: 결제 모듈 리팩토링. 개선사항 - PaymentProcessor 클래스 단일책임원칙 적용, 5개 메소드로 분리, 유닛테스트 추가로 커버리지 45% → 87% 향상.',
                '주간 리뷰 통계: 총 23개 PR 리뷰, 평균 리뷰 시간 25분, 발견된 버그 8개 (배포 전 수정), 코드 품질 점수 7.2/10 → 8.1/10 향상.'
            ]
        },
        
        '프론트엔드 개발': {
            'guide': 'React 기반 모던 웹 애플리케이션 UI/UX 개발',
            'subtasks': [
                ('컴포넌트 아키텍처 설계', '재사용 가능한 컴포넌트 구조', 'Atomic Design 패턴을 적용한 Button, Input, Card 등 기본 컴포넌트부터 복합 컴포넌트까지 체계적 설계'),
                ('상태 관리 시스템 구축', 'Redux Toolkit 기반 상태 관리', '사용자 인증, 장바구니, 알림 등 전역 상태를 효율적으로 관리하는 스토어 구조 설계'),
                ('반응형 디자인 구현', '모바일 퍼스트 반응형 레이아웃', 'CSS Grid와 Flexbox를 활용한 다양한 디바이스 대응 레이아웃'),
                ('성능 최적화', '번들 사이즈 및 렌더링 최적화', 'Code Splitting, Lazy Loading, 메모이제이션을 통한 성능 개선')
            ],
            'memos': [
                '컴포넌트 라이브러리 초기 설정. Storybook 도입하여 컴포넌트 문서화 진행. Button 컴포넌트 8가지 variant (primary, secondary, danger 등) 구현 완료.',
                'Redux Toolkit 스토어 구조 설계. 슬라이스별 분리: authSlice (로그인/로그아웃), cartSlice (장바구니), notificationSlice (알림). RTK Query로 API 호출 최적화.',
                '반응형 디자인 구현 중. Breakpoint 설정: mobile(320px), tablet(768px), desktop(1024px). Grid 시스템 12 컬럼 기반으로 통일.',
                '성능 측정 결과 - Lighthouse 점수: 성능 78점. 개선점: 1) 이미지 최적화 필요 2) 미사용 CSS 제거 3) 폰트 preload 적용.',
                '최종 성능 개선 완료. React.lazy()로 페이지별 코드 스플리팅, 이미지 WebP 포맷 적용, CSS-in-JS 런타임 제거. Lighthouse 성능 점수 78점 → 94점 달성!'
            ]
        },
        
        '백엔드 API 개발': {
            'guide': 'Node.js Express 기반 RESTful API 서버 구축',
            'subtasks': [
                ('API 명세서 작성', 'OpenAPI 3.0 스펙 문서화', 'Swagger를 활용한 엔드포인트별 요청/응답 스키마, 에러 코드 정의'),
                ('인증 시스템 구현', 'JWT 기반 사용자 인증', 'Access Token과 Refresh Token을 활용한 보안 강화된 인증 시스템'),
                ('데이터 검증 미들웨어', '입력값 유효성 검사', 'Joi 스키마를 활용한 요청 데이터 검증 및 에러 핸들링'),
                ('API 테스트 자동화', '통합 테스트 구현', 'Jest와 Supertest를 활용한 엔드포인트별 자동화 테스트')
            ],
            'memos': [
                'API 설계 1차 완료. 총 32개 엔드포인트 정의: 사용자 관리(8개), 상품 관리(12개), 주문 관리(8개), 결제(4개). Swagger UI로 문서 자동 생성.',
                'JWT 인증 시스템 구현. Access Token 만료 15분, Refresh Token 7일. Redis를 활용한 토큰 블랙리스트 관리로 로그아웃 시 즉시 무효화.',
                '데이터 검증 미들웨어 적용. 사용자 등록 API에서 이메일 형식, 비밀번호 복잡도, 필수 필드 검증. 잘못된 요청 시 400 에러와 상세 메시지 반환.',
                'API 응답 시간 측정: 평균 120ms, 최대 340ms. 가장 느린 API는 상품 검색(평균 280ms). 데이터베이스 인덱스 최적화와 캐싱 적용 예정.',
                '통합 테스트 완료. 총 89개 테스트 케이스, 커버리지 92%. CI/CD 파이프라인에 통합하여 배포 전 자동 테스트 실행. 모든 테스트 통과!'
            ]
        },
        
        '데이터베이스 설계': {
            'guide': 'MySQL 기반 확장 가능한 데이터베이스 스키마 설계',
            'subtasks': [
                ('ERD 설계', '엔티티 관계도 작성', '비즈니스 요구사항을 반영한 테이블 간 관계 정의 및 정규화'),
                ('인덱스 전략 수립', '쿼리 성능 최적화를 위한 인덱스 설계', '자주 사용되는 검색 조건과 JOIN 컬럼에 대한 인덱스 계획'),
                ('파티셔닝 적용', '대용량 데이터 처리를 위한 테이블 분할', '날짜 기반 파티셔닝으로 쿼리 성능 향상'),
                ('백업 및 복구 전략', '데이터 안정성 확보', '일별 풀백업, 시간별 증분백업, Point-in-time 복구 시스템 구축')
            ],
            'memos': [
                'ERD 1차 설계 완료. 주요 테이블: users(회원), products(상품), orders(주문), payments(결제), reviews(리뷰). 총 12개 테이블, 정규화 3NF 적용.',
                '인덱스 설계 진행. users 테이블의 email, phone 컬럼에 UNIQUE 인덱스, orders 테이블의 user_id + created_at 복합 인덱스 생성 예정.',
                '성능 테스트 결과 - 100만 건 데이터에서 사용자별 주문 조회 쿼리: 인덱스 적용 전 2.3초 → 적용 후 0.08초 (96% 향상)',
                'orders 테이블 월별 파티셔닝 적용. 2024년 1월부터 월별로 분할하여 과거 데이터 조회 성능 향상. 현재 월 데이터만 조회 시 응답 시간 80% 단축.',
                '백업 시스템 구축 완료. 매일 새벽 2시 풀백업(약 30분 소요), 4시간마다 증분백업. AWS S3에 자동 저장, 30일 보관 정책 적용. 복구 테스트 성공!'
            ]
        }
    }
    
    return task_details

def insert_sample_data(cursor):
    # 5명의 사용자 데이터 삽입
    users_data = [
        ('김민수', 'minsu.kim@email.com'),
        ('이영희', 'younghee.lee@email.com'),
        ('박정호', 'jungho.park@email.com'),
        ('최수진', 'sujin.choi@email.com'),
        ('정태현', 'taehyun.jung@email.com')
    ]
    
    for username, email in users_data:
        cursor.execute('INSERT INTO users (username, email) VALUES (?, ?)', (username, email))
    
    # 상세한 작업 데이터 가져오기
    detailed_tasks = get_detailed_task_data()
    
    # 추가 작업들 (간단한 버전)
    additional_tasks = [
        ('테스트 케이스 작성', '단위 테스트 및 통합 테스트 코드 작성', '상'),
        ('문서화 작업', '기술 문서 및 API 문서 작성', '중'),
        ('보안 점검', 'OWASP 기반 보안 취약점 분석', '상'),
        ('배포 자동화', 'Docker와 Kubernetes 기반 CI/CD 구축', '중'),
        ('사용자 피드백 분석', 'GA4와 Mixpanel을 활용한 사용자 행동 분석', '하'),
        ('모바일 앱 개발', 'React Native 기반 크로스플랫폼 앱', '상'),
        ('마케팅 전략 수립', 'SEO 최적화 및 콘텐츠 마케팅 전략', '중'),
        ('프로젝트 관리', 'Agile/Scrum 방법론 적용 프로젝트 운영', '중'),
        ('고객 지원 시스템', 'Zendesk 기반 헬프데스크 시스템 구축', '하'),
        ('데이터 분석', 'Python Pandas를 활용한 비즈니스 데이터 분석', '상'),
        ('인프라 구축', 'AWS ECS 기반 마이크로서비스 아키텍처', '상'),
        ('AI 모델 개발', 'TensorFlow를 활용한 추천 시스템 개발', '상'),
        ('블록체인 개발', 'Solidity 스마트 컨트랙트 개발', '상'),
        ('게임 개발', 'Unity 3D를 활용한 모바일 게임 제작', '중'),
        ('웹 크롤링', 'Scrapy를 활용한 대용량 데이터 수집', '하'),
        ('챗봇 개발', 'OpenAI API를 활용한 고객 상담 챗봇', '중'),
        ('이커머스 구축', 'Next.js 기반 온라인 쇼핑몰 풀스택 개발', '상'),
        ('소셜 미디어 분석', 'Twitter API를 활용한 감정 분석 시스템', '중'),
        ('IoT 시스템 개발', 'Arduino와 AWS IoT Core 연동 시스템', '상'),
        ('VR/AR 콘텐츠 제작', 'Unity AR Foundation 기반 증강현실 앱', '상')
    ]
    
    # 모든 작업 목록 생성 (상세 작업 + 추가 작업)
    all_tasks = []
    
    # 상세 작업들 추가
    for task_title, task_data in detailed_tasks.items():
        all_tasks.append((task_title, task_data['guide'], '상'))
    
    # 추가 작업들 추가
    all_tasks.extend(additional_tasks)
    
    # 각 사용자에게 5개씩 고유한 작업 할당
    task_id = 1
    base_date = datetime.now()
    
    for user_id in range(1, 6):  # 5명의 사용자
        start_idx = (user_id - 1) * 5
        end_idx = start_idx + 5
        user_tasks = all_tasks[start_idx:end_idx]
        
        for i, (title, guide, difficulty) in enumerate(user_tasks):
            start_date = base_date + timedelta(days=random.randint(0, 30))
            end_date = start_date + timedelta(days=random.randint(7, 21))
            status = random.randint(0, 2)
            exp_points = random.randint(50, 200)
            mentorship_id = random.choice([None, random.randint(1, 5)])
            
            cursor.execute('''
            INSERT INTO task_assign 
            (task_assign_id, title, start_date, end_date, status, difficulty, guide, exp, order_num, mentorship_id, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (task_id, title, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), 
                  status, difficulty, guide, exp_points, i+1, mentorship_id, user_id))
            
            # 상세 데이터가 있는 작업의 경우 상세 subtask와 memo 사용
            if title in detailed_tasks:
                task_detail = detailed_tasks[title]
                
                # 상세 subtask 추가
                for subtask_title, guide, content in task_detail['subtasks']:
                    cursor.execute('''
                    INSERT INTO subtask (task_assign_id, subtask_title, guide, content)
                    VALUES (?, ?, ?, ?)
                    ''', (task_id, subtask_title, guide, content))
                
                # 상세 memo 추가 (시간 순서대로)
                for idx, memo_text in enumerate(task_detail['memos']):
                    memo_date = start_date + timedelta(days=idx * 2 + 1)
                    cursor.execute('''
                    INSERT INTO memo (create_date, comment, task_assign_id, user_id)
                    VALUES (?, ?, ?, ?)
                    ''', (memo_date.strftime('%Y-%m-%d'), memo_text, task_id, user_id))
            
            else:
                # 기본 subtask와 memo (다른 작업들)
                default_subtasks = [
                    ('요구사항 분석', '프로젝트 목표와 범위 정의', '비즈니스 요구사항과 기술적 제약사항 파악'),
                    ('기술 스택 선정', '최적의 기술 조합 결정', '성능, 확장성, 유지보수성을 고려한 기술 선택'),
                    ('개발 및 구현', '실제 기능 개발', '설계된 아키텍처를 바탕으로 코드 구현'),
                    ('테스트 및 검증', '품질 보증', '단위 테스트, 통합 테스트를 통한 기능 검증')
                ]
                
                selected_subtasks = random.sample(default_subtasks, random.randint(2, 4))
                for subtask_title, guide, content in selected_subtasks:
                    cursor.execute('''
                    INSERT INTO subtask (task_assign_id, subtask_title, guide, content)
                    VALUES (?, ?, ?, ?)
                    ''', (task_id, subtask_title, guide, content))
                
                # 기본 메모들
                default_memos = [
                    f'{title} 프로젝트 킥오프 미팅 완료. 주요 이해관계자들과 목표 및 일정 공유.',
                    f'기술 조사 완료. {random.choice(["React", "Vue", "Angular", "Node.js", "Python", "Java"])} 기반으로 개발 진행 예정.',
                    f'1차 프로토타입 완성. 핵심 기능 {random.randint(60, 85)}% 구현 완료, 예상보다 {random.choice(["순조롭게", "다소 지연되어"])} 진행 중.',
                    f'코드 리뷰 및 테스트 진행 중. 발견된 이슈 {random.randint(3, 12)}개 수정 완료.',
                    f'{title} 최종 테스트 완료. 성능 목표 달성, 배포 준비 완료.'
                ]
                
                selected_memos = random.sample(default_memos, random.randint(2, 4))
                for idx, memo_text in enumerate(selected_memos):
                    memo_date = start_date + timedelta(days=idx * 3 + 1)
                    cursor.execute('''
                    INSERT INTO memo (create_date, comment, task_assign_id, user_id)
                    VALUES (?, ?, ?, ?)
                    ''', (memo_date.strftime('%Y-%m-%d'), memo_text, task_id, user_id))
            
            task_id += 1

def print_database_summary(cursor):
    """데이터베이스 내용 요약 출력"""
    print("=" * 80)
    print("상세한 프로젝트 데이터베이스 생성 완료!")
    print("=" * 80)
    
    # 상세 작업 예시 출력
    print("\n📋 상세 작업 예시 (성능 최적화):")
    print("-" * 60)
    
    cursor.execute('''
    SELECT t.title, s.subtask_title, s.guide, s.content
    FROM task_assign t
    JOIN subtask s ON t.task_assign_id = s.task_assign_id
    WHERE t.title = '성능 최적화'
    LIMIT 2
    ''')
    
    for title, subtask_title, guide, content in cursor.fetchall():
        print(f"서브태스크: {subtask_title}")
        print(f"가이드: {guide}")
        print(f"내용: {content}")
        print()
    
    print("📝 관련 메모 예시:")
    print("-" * 40)
    
    cursor.execute('''
    SELECT m.create_date, m.comment
    FROM task_assign t
    JOIN memo m ON t.task_assign_id = m.task_assign_id
    WHERE t.title = '성능 최적화'
    ORDER BY m.create_date
    LIMIT 3
    ''')
    
    for create_date, comment in cursor.fetchall():
        print(f"[{create_date}] {comment}")
        print()
    
    # 사용자별 통계
    cursor.execute('''
    SELECT u.user_id, u.username, 
           COUNT(DISTINCT t.task_assign_id) as task_count,
           COUNT(DISTINCT s.subtask_id) as subtask_count,
           COUNT(DISTINCT m.memo_id) as memo_count,
           ROUND(AVG(t.exp), 1) as avg_exp
    FROM users u
    LEFT JOIN task_assign t ON u.user_id = t.user_id
    LEFT JOIN subtask s ON t.task_assign_id = s.task_assign_id
    LEFT JOIN memo m ON t.task_assign_id = m.task_assign_id
    GROUP BY u.user_id, u.username
    ORDER BY u.user_id
    ''')
    
    results = cursor.fetchall()
    print(f"\n📊 사용자별 데이터 통계:")
    print("-" * 60)
    for user_id, username, task_count, subtask_count, memo_count, avg_exp in results:
        print(f"👤 {username} (ID: {user_id})")
        print(f"   ├─ 할당된 작업: {task_count}개")
        print(f"   ├─ 서브태스크: {subtask_count}개") 
        print(f"   ├─ 작성된 메모: {memo_count}개")
        print(f"   └─ 평균 경험치: {avg_exp}점")
        print()
    
    # 전체 통계
    cursor.execute('SELECT COUNT(*) FROM task_assign')
    task_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM subtask')
    subtask_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM memo')
    memo_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT AVG(LENGTH(comment)) FROM memo')
    avg_memo_length = cursor.fetchone()[0]
    
    print("📈 전체 통계:")
    print("-" * 30)
    print(f"총 작업: {task_count}개")
    print(f"총 서브태스크: {subtask_count}개")
    print(f"총 메모: {memo_count}개")
    print(f"평균 메모 길이: {avg_memo_length:.0f}자")
    
    # 작업 중복 확인
    cursor.execute('''
    SELECT title, COUNT(*) as count 
    FROM task_assign 
    GROUP BY title 
    HAVING COUNT(*) > 1
    ''')
    
    duplicates = cursor.fetchall()
    if duplicates:
        print(f"\n❌ 중복된 작업 발견:")
        for title, count in duplicates:
            print(f"  - {title}: {count}명에게 할당됨")
    else:
        print(f"\n✅ 모든 사용자가 고유한 작업을 할당받았습니다!")
    
    print(f"\n💡 특징:")
    print("- 성능 최적화, 코드 리뷰 등 주요 작업에는 실제 개발 과정이 단계별로 상세 기록")
    print("- 각 서브태스크는 실제 작업의 하위 단계로 구성")
    print("- 메모에는 구체적인 수치, 도구명, 기술 스택이 포함된 현실적 내용")
    print("- 작업 진행 과정과 결과가 시간 순서대로 메모에 기록됨")

def main():
    # 데이터베이스 생성
    conn, cursor = create_database()
    
    try:
        # 샘플 데이터 삽입
        insert_sample_data(cursor)
        
        # 변경사항 커밋
        conn.commit()
        
        # 결과 출력
        print_database_summary(cursor)
        
        print(f"\n🎉 데이터베이스 파일 'task_management.db'가 생성되었습니다.")
        print("상세한 프로젝트 데이터로 실제 개발 환경을 시뮬레이션할 수 있습니다!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        conn.rollback()
    
    finally:
        # 연결 종료
        conn.close()

if __name__ == "__main__":
    main()