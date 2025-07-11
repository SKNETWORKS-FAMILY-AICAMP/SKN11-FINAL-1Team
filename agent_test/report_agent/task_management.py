import sqlite3
import random
from datetime import datetime, timedelta

'''
멘토-멘티 관계 기반 DB 생성용 코드
'''

def create_database():
    # 데이터베이스 연결
    conn = sqlite3.connect('task_management.db')
    cursor = conn.cursor()
    
    # 기존 테이블 삭제 (있다면)
    cursor.execute('DROP TABLE IF EXISTS memo')
    cursor.execute('DROP TABLE IF EXISTS subtask')
    cursor.execute('DROP TABLE IF EXISTS task_assign')
    cursor.execute('DROP TABLE IF EXISTS users')
    
    # users 테이블 생성 (role 컬럼 추가)
    cursor.execute('''
    CREATE TABLE users (
        user_id INTEGER PRIMARY KEY,
        username VARCHAR NOT NULL UNIQUE,
        email VARCHAR NOT NULL UNIQUE,
        role VARCHAR NOT NULL CHECK (role IN ('mentor', 'mentee')),
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
        mentorship_id INTEGER NOT NULL,
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
    """각 작업별 상세한 subtask와 mentor/mentee memo 데이터를 정의"""
    
    task_details = {
        '성능 최적화': {
            'guide': '시스템 성능 병목점을 찾아 개선하는 전체적인 접근 방법',
            'subtasks': [
                ('성능 측정 도구 설정', '프로파일링 도구 설치 및 설정', 'New Relic, DataDog 등의 APM 도구를 설정하여 실시간 성능 모니터링 환경 구축'),
                ('병목점 식별', '시스템에서 가장 느린 부분 찾기', 'CPU, 메모리, 디스크 I/O, 네트워크 등 각 구간별 성능 측정하여 bottleneck 구간 파악'),
                ('데이터베이스 쿼리 최적화', 'SQL 쿼리 성능 개선', '인덱스 추가, N+1 쿼리 문제 해결, 쿼리 실행계획 분석을 통한 최적화'),
                ('캐싱 전략 구현', '자주 사용되는 데이터 캐싱', 'Redis를 활용한 세션 캐시, API 응답 캐시, 페이지 캐시 구현')
            ],
            'mentor_memos': [
                '[멘토] 성능 최적화 작업 시작합니다. 먼저 현재 시스템의 baseline을 측정해보세요. New Relic이나 DataDog 같은 APM 도구를 추천합니다.',
                '[멘토] 병목점 분석 결과를 잘 정리해주셨네요. 데이터베이스 쿼리가 주요 원인인 것 같습니다. 다음 단계로 EXPLAIN 명령어로 쿼리 실행 계획을 분석해보세요.',
                '[멘토] 인덱스 최적화 방향이 좋습니다. 다만 너무 많은 인덱스는 INSERT 성능에 영향을 줄 수 있으니 실제 사용 패턴을 고려해서 선별적으로 적용하세요.',
                '[멘토] Redis 캐싱 구현이 인상적입니다. TTL 설정과 캐시 무효화 전략도 함께 고려해보세요. 특히 데이터 일관성 문제를 주의해야 합니다.',
                '[멘토] 전체적으로 65% 성능 향상은 훌륭한 성과입니다. 이제 모니터링 대시보드를 구축해서 지속적으로 성능을 추적할 수 있도록 해보세요.'
            ],
            'mentee_memos': [
                '[멘티] New Relic APM 설정 완료했습니다. 현재 평균 응답시간이 2.3초로 측정되네요. 예상보다 느린 것 같아서 개선이 필요할 것 같습니다.',
                '[멘티] 병목점 분석 결과 데이터베이스 쿼리가 전체 응답시간의 65%를 차지합니다. 특히 사용자 목록 조회 API가 1.5초나 걸려서 가장 문제가 되는 것 같습니다.',
                '[멘티] email 컬럼과 created_at 컬럼에 복합 인덱스 추가했더니 쿼리 시간이 1.5초에서 0.45초로 70% 개선되었습니다! 효과가 정말 큽니다.',
                '[멘티] Redis 캐시를 적용해서 자주 조회되는 사용자 프로필 데이터를 30분간 캐싱하도록 했습니다. 전체 응답시간이 0.8초까지 줄어들었어요.',
                '[멘티] 최종 성능 테스트 완료! 초기 2.3초에서 0.8초로 65% 향상되었습니다. 사용자 경험이 확실히 개선될 것 같습니다. 감사합니다!'
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
            'mentor_memos': [
                '[멘토] 코드 리뷰 가이드라인을 작성할 때는 팀의 현재 수준을 고려해야 합니다. 너무 엄격하면 개발 속도가 느려질 수 있어요. 점진적으로 기준을 높여가세요.',
                '[멘토] SonarQube 도입은 좋은 선택입니다. 하지만 초기에는 기존 코드의 많은 이슈가 발견될 것입니다. 신규 코드부터 적용해서 점진적으로 개선하는 것을 추천합니다.',
                '[멘토] PR 템플릿이 잘 구성되었네요. 다만 개발자들이 형식적으로 작성하지 않도록 실제 도움이 되는 항목들로 구성하는 것이 중요합니다.',
                '[멘토] 리뷰 통계를 보니 평균 리뷰 시간이 25분 정도네요. 적절한 수준입니다. 너무 길면 개발자들이 부담스러워하고, 너무 짧으면 제대로 리뷰가 안 될 수 있어요.',
                '[멘토] 코드 품질 점수가 꾸준히 향상되고 있어서 좋습니다. 이제 리뷰 문화가 정착되었으니 더 고급 주제들(아키텍처, 성능 등)도 리뷰에 포함해보세요.'
            ],
            'mentee_memos': [
                '[멘티] 리뷰 가이드라인 초안을 작성했습니다. 함수는 50줄 이하, 복잡도 10 이하, 테스트 커버리지 80% 이상 등의 기준을 정했어요. 팀 피드백을 받아보겠습니다.',
                '[멘티] SonarQube 설치해서 기존 코드를 스캔해봤는데 247개 이슈가 발견되었습니다. Critical 12개는 바로 수정이 필요할 것 같아요.',
                '[멘티] UserService.js 리뷰에서 SQL Injection 취약점을 발견했습니다. try-catch 누락과 불필요한 중첩 루프도 문제였어요. 이런 걸 미리 찾을 수 있어서 다행입니다.',
                '[멘티] 결제 모듈 리팩토링 PR 리뷰 완료했습니다. PaymentProcessor 클래스를 5개 메소드로 분리하고 테스트 커버리지도 87%까지 올렸어요.',
                '[멘티] 이번 주 리뷰 통계입니다. 23개 PR을 리뷰했고 8개 버그를 배포 전에 발견했어요. 코드 품질 점수도 8.1점으로 향상되었습니다!'
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
            'mentor_memos': [
                '[멘토] Atomic Design 패턴은 좋은 선택입니다. 다만 처음에는 너무 세분화하지 말고 실제 필요에 따라 점진적으로 컴포넌트를 분리하는 것을 추천합니다.',
                '[멘토] Redux Toolkit 스토어 구조가 잘 설계되었네요. 다만 모든 상태를 전역으로 관리할 필요는 없습니다. 컴포넌트 지역 상태와 전역 상태를 적절히 분리하세요.',
                '[멘토] 반응형 디자인의 브레이크포인트가 적절합니다. 모바일 퍼스트 접근법도 좋아요. 이제 실제 디바이스에서 테스트해보는 것이 중요합니다.',
                '[멘토] Lighthouse 점수가 78점이면 나쁘지 않지만 더 개선할 여지가 있습니다. 이미지 최적화와 미사용 CSS 제거부터 시작해보세요.',
                '[멘토] 성능 최적화 결과가 훌륭합니다! 94점은 매우 좋은 점수입니다. 이제 실제 사용자 환경에서의 성능도 모니터링해보세요.'
            ],
            'mentee_memos': [
                '[멘티] Storybook으로 컴포넌트 문서화를 시작했습니다. Button 컴포넌트에 8가지 variant를 만들었어요. primary, secondary, danger 등 다양한 스타일을 준비했습니다.',
                '[멘티] Redux Toolkit으로 스토어 구조를 설계했습니다. authSlice, cartSlice, notificationSlice로 분리하고 RTK Query로 API 호출을 최적화했어요.',
                '[멘티] 반응형 디자인 구현 중입니다. mobile(320px), tablet(768px), desktop(1024px) 브레이크포인트로 설정하고 12컬럼 그리드 시스템을 적용했어요.',
                '[멘티] Lighthouse로 성능 측정해봤는데 78점이 나왔습니다. 이미지 최적화와 미사용 CSS 제거, 폰트 preload가 필요한 것 같아요.',
                '[멘티] 성능 최적화 완료! React.lazy()로 코드 스플리팅하고 이미지를 WebP로 변환했더니 Lighthouse 점수가 94점까지 올랐습니다!'
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
            'mentor_memos': [
                '[멘토] OpenAPI 명세서 작성이 중요합니다. 프론트엔드 개발자와의 협업을 위해 상세하고 정확한 문서를 작성하세요. Swagger UI로 실시간 테스트도 가능하게 하면 좋겠어요.',
                '[멘토] JWT 토큰 전략이 보안을 잘 고려했네요. Access Token 만료시간 15분은 적절합니다. Refresh Token 로테이션도 고려해보세요.',
                '[멘토] Joi를 활용한 데이터 검증이 체계적으로 구현되었습니다. 에러 메시지도 사용자 친화적으로 작성되어 있어서 좋아요.',
                '[멘토] API 응답시간 120ms는 매우 좋은 성능입니다. 다만 상품 검색 API가 280ms로 상대적으로 느리니 이 부분을 집중적으로 최적화해보세요.',
                '[멘토] 테스트 커버리지 92%는 훌륭합니다. CI/CD 파이프라인 통합도 잘 되어 있어서 안정적인 배포가 가능할 것 같습니다.'
            ],
            'mentee_memos': [
                '[멘티] API 설계를 완료했습니다. 사용자 관리 8개, 상품 관리 12개, 주문 관리 8개, 결제 4개로 총 32개 엔드포인트를 정의했어요. Swagger UI로 문서화도 했습니다.',
                '[멘티] JWT 인증 시스템을 구현했습니다. Access Token은 15분, Refresh Token은 7일로 설정했고 Redis로 블랙리스트 관리도 추가했어요.',
                '[멘티] Joi로 데이터 검증 미들웨어를 만들었습니다. 이메일 형식, 비밀번호 복잡도, 필수 필드를 검증하고 잘못된 요청시 상세한 에러 메시지를 반환합니다.',
                '[멘티] API 성능을 측정해봤습니다. 평균 120ms, 최대 340ms인데 상품 검색 API가 평균 280ms로 가장 느려서 최적화가 필요할 것 같아요.',
                '[멘티] 통합 테스트를 완료했습니다! 89개 테스트 케이스로 커버리지 92%를 달성했고 CI/CD 파이프라인에 통합해서 자동 테스트가 실행됩니다.'
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
            'mentor_memos': [
                '[멘토] ERD 설계에서 정규화를 3NF까지 적용한 것이 좋습니다. 다만 성능이 중요한 부분은 의도적으로 비정규화를 고려해볼 수도 있어요.',
                '[멘토] 인덱스 전략이 체계적으로 수립되었네요. 복합 인덱스의 컬럼 순서가 중요하니 실제 쿼리 패턴을 분석해서 최적화하세요.',
                '[멘토] 성능 테스트 결과가 인상적입니다. 96% 향상은 인덱스 효과가 정말 크다는 것을 보여주네요. 인덱스 유지비용도 모니터링해보세요.',
                '[멘토] 월별 파티셔닝 전략이 좋습니다. 과거 데이터 조회가 적다면 성능상 큰 이점이 있을 것입니다. 파티션 프루닝이 제대로 작동하는지 확인해보세요.',
                '[멘토] 백업 시스템이 체계적으로 구축되었습니다. 복구 테스트까지 완료한 것이 훌륭해요. 정기적으로 복구 테스트를 반복하는 것을 권장합니다.'
            ],
            'mentee_memos': [
                '[멘티] ERD 1차 설계를 완료했습니다. users, products, orders, payments, reviews 등 12개 테이블로 구성하고 3NF 정규화를 적용했어요.',
                '[멘티] 인덱스 설계를 진행했습니다. users 테이블의 email, phone 컬럼에 UNIQUE 인덱스, orders 테이블에 user_id + created_at 복합 인덱스 생성 예정입니다.',
                '[멘티] 성능 테스트 결과가 놀랍습니다! 100만 건 데이터에서 사용자별 주문 조회가 인덱스 적용 전 2.3초에서 적용 후 0.08초로 96% 향상되었어요.',
                '[멘티] orders 테이블에 월별 파티셔닝을 적용했습니다. 2024년 1월부터 월별 분할해서 현재 월 데이터 조회시 응답시간이 80% 단축되었어요.',
                '[멘티] 백업 시스템 구축을 완료했습니다. 매일 새벽 2시 풀백업, 4시간마다 증분백업으로 설정하고 AWS S3에 30일 보관합니다. 복구 테스트도 성공했어요!'
            ]
        }
    }
    
    return task_details

def create_mentorship_pairs():
    """멘토-멘티 페어 생성 (10명의 사용자를 5개 멘토쉽으로 구성)"""
    mentorship_data = [
        # 멘토쉽 1: 시니어 백엔드 개발자 - 주니어 풀스택 개발자
        (1, '김민수', 'minsu.kim@email.com', 'mentor'),
        (2, '이영희', 'younghee.lee@email.com', 'mentee'),
        
        # 멘토쉽 2: 시니어 프론트엔드 개발자 - 주니어 프론트엔드 개발자  
        (3, '박정호', 'jungho.park@email.com', 'mentor'),
        (4, '최수진', 'sujin.choi@email.com', 'mentee'),
        
        # 멘토쉽 3: 데이터베이스 전문가 - 백엔드 개발자
        (5, '정태현', 'taehyun.jung@email.com', 'mentor'),
        (6, '강지연', 'jiyeon.kang@email.com', 'mentee'),
        
        # 멘토쉽 4: DevOps 엔지니어 - 백엔드 개발자
        (7, '윤서준', 'seojun.yoon@email.com', 'mentor'),
        (8, '한소영', 'soyoung.han@email.com', 'mentee'),
        
        # 멘토쉽 5: 테크리드 - 주니어 개발자
        (9, '조현우', 'hyunwoo.cho@email.com', 'mentor'),
        (10, '신미래', 'mirae.shin@email.com', 'mentee')
    ]
    
    return mentorship_data

def insert_sample_data(cursor):
    # 멘토-멘티 페어 데이터
    mentorship_pairs = create_mentorship_pairs()
    
    # 사용자 데이터 삽입
    for user_id, username, email, role in mentorship_pairs:
        cursor.execute('INSERT INTO users (user_id, username, email, role) VALUES (?, ?, ?, ?)', 
                      (user_id, username, email, role))
    
    # 상세한 작업 데이터 가져오기
    detailed_tasks = get_detailed_task_data()
    
    # 추가 작업들 (멘토쉽별로 특화)
    additional_tasks_by_mentorship = {
        1: [  # 백엔드 멘토쉽
            ('API 문서화', 'Swagger를 활용한 API 문서 자동화', '상'),
            ('마이크로서비스 아키텍처', 'Docker와 Kubernetes 기반 MSA 구현', '상'),
            ('메시지 큐 시스템', 'RabbitMQ를 활용한 비동기 처리', '중'),
            ('로그 시스템 구축', 'ELK Stack 기반 로그 수집 및 분석', '중'),
            ('서버 모니터링', 'Prometheus와 Grafana 모니터링 대시보드', '하')
        ],
        2: [  # 프론트엔드 멘토쉽
            ('UI 컴포넌트 라이브러리', 'Design System 기반 컴포넌트 구축', '중'),
            ('웹 접근성 개선', 'WCAG 2.1 기준 접근성 최적화', '하'),
            ('PWA 구현', 'Progressive Web App 기능 구현', '중'),
            ('크로스 브라우저 테스트', '다양한 브라우저 호환성 검증', '하'),
            ('웹팩 최적화', '번들 사이즈 최적화 및 빌드 성능 개선', '상')
        ],
        3: [  # 데이터베이스 멘토쉽
            ('데이터 마이그레이션', '레거시 DB에서 신규 스키마로 이전', '상'),
            ('쿼리 최적화 가이드', '성능 개선을 위한 SQL 튜닝', '중'),
            ('데이터 웨어하우스 구축', 'BigQuery 기반 분석 시스템', '상'),
            ('실시간 데이터 파이프라인', 'Kafka와 Spark를 활용한 스트리밍', '상'),
            ('DB 보안 강화', '암호화 및 접근 권한 관리', '중')
        ],
        4: [  # DevOps 멘토쉽  
            ('CI/CD 파이프라인 구축', 'Jenkins와 GitLab CI 자동화', '중'),
            ('컨테이너 오케스트레이션', 'Kubernetes 클러스터 운영', '상'),
            ('인프라 as 코드', 'Terraform을 활용한 클라우드 자원 관리', '상'),
            ('보안 스캔 자동화', 'SAST/DAST 도구 통합', '중'),
            ('서버리스 아키텍처', 'AWS Lambda 기반 이벤트 처리', '하')
        ],
        5: [  # 테크리드 멘토쉽
            ('아키텍처 설계', '확장 가능한 시스템 아키텍처 설계', '상'),
            ('코드 품질 관리', '정적 분석 도구와 코드 리뷰 프로세스', '중'),
            ('팀 개발 프로세스', 'Agile/Scrum 방법론 적용', '중'),
            ('기술 스택 선정', '프로젝트 요구사항에 맞는 기술 선택', '하'),
            ('멘토링 스킬', '주니어 개발자 성장 지원 방법론', '하')
        ]
    }
    
    # 멘토쉽별 작업 할당
    task_id = 1
    base_date = datetime.now()
    
    for mentorship_id in range(1, 6):  # 5개 멘토쉽
        # 멘토와 멘티 ID 가져오기
        mentor_id = (mentorship_id - 1) * 2 + 1
        mentee_id = (mentorship_id - 1) * 2 + 2
        
        # 상세 작업 1개 + 추가 작업 4개 할당 (멘티에게만 할당)
        detailed_task_names = list(detailed_tasks.keys())
        assigned_detailed_task = detailed_task_names[mentorship_id - 1]
        additional_tasks = additional_tasks_by_mentorship[mentorship_id]
        
        all_tasks = [(assigned_detailed_task, detailed_tasks[assigned_detailed_task]['guide'], '상')] + additional_tasks
        
        for i, (title, guide, difficulty) in enumerate(all_tasks):
            start_date = base_date + timedelta(days=random.randint(0, 30))
            end_date = start_date + timedelta(days=random.randint(7, 21))
            status = random.randint(0, 2)
            exp_points = random.randint(50, 200)
            
            # 작업은 멘티에게만 할당
            cursor.execute('''
            INSERT INTO task_assign 
            (task_assign_id, title, start_date, end_date, status, difficulty, guide, exp, order_num, mentorship_id, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (task_id, title, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), 
                  status, difficulty, guide, exp_points, i+1, mentorship_id, mentee_id))
            
            # 상세 데이터가 있는 작업의 경우
            if title in detailed_tasks:
                task_detail = detailed_tasks[title]
                
                # 상세 subtask 추가
                for subtask_title, guide, content in task_detail['subtasks']:
                    cursor.execute('''
                    INSERT INTO subtask (task_assign_id, subtask_title, guide, content)
                    VALUES (?, ?, ?, ?)
                    ''', (task_id, subtask_title, guide, content))
                
                # 멘토와 멘티의 메모를 번갈아가며 추가
                mentor_memos = task_detail['mentor_memos']
                mentee_memos = task_detail['mentee_memos']
                
                for idx in range(min(len(mentor_memos), len(mentee_memos))):
                    # 멘티 메모 먼저
                    mentee_memo_date = start_date + timedelta(days=idx * 4 + 1)
                    cursor.execute('''
                    INSERT INTO memo (create_date, comment, task_assign_id, user_id)
                    VALUES (?, ?, ?, ?)
                    ''', (mentee_memo_date.strftime('%Y-%m-%d'), mentee_memos[idx], task_id, mentee_id))
                    
                    # 멘토 메모 (2일 후)
                    mentor_memo_date = start_date + timedelta(days=idx * 4 + 3)
                    cursor.execute('''
                    INSERT INTO memo (create_date, comment, task_assign_id, user_id)
                    VALUES (?, ?, ?, ?)
                    ''', (mentor_memo_date.strftime('%Y-%m-%d'), mentor_memos[idx], task_id, mentor_id))
            
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
                
                # 멘토-멘티 관점의 기본 메모들
                mentee_default_memos = [
                    f'[멘티] {title} 프로젝트를 시작합니다. 요구사항을 정리하고 기술 스택을 조사해보겠습니다.',
                    f'[멘티] 기술 조사를 완료했습니다. {random.choice(["React", "Vue", "Angular", "Node.js", "Python", "Java"])} 기반으로 개발하려고 하는데 어떻게 생각하시나요?',
                    f'[멘티] 1차 구현을 완료했습니다. 핵심 기능 {random.randint(60, 85)}% 구현했는데 코드 리뷰 부탁드립니다.',
                    f'[멘티] 테스트 코드를 작성했습니다. 커버리지 {random.randint(70, 90)}% 달성했어요. 추가로 개선할 부분이 있을까요?'
                ]
                
                mentor_default_memos = [
                    f'[멘토] {title} 프로젝트 계획이 체계적으로 정리되었네요. 기술 스택 선정할 때 확장성과 유지보수성을 함께 고려해보세요.',
                    f'[멘토] 기술 선택이 적절합니다. 다만 {random.choice(["성능", "보안", "확장성"])} 측면에서 추가 고려사항이 있으니 함께 검토해보겠습니다.',
                    f'[멘토] 코드 품질이 좋습니다. 네이밍도 명확하고 구조도 잘 짜여져 있어요. 다음 단계로 {random.choice(["성능 최적화", "에러 핸들링", "보안 강화"])}를 진행해보세요.',
                    f'[멘토] 테스트 커버리지가 높아서 좋습니다. 이제 통합 테스트와 E2E 테스트도 고려해볼 시점인 것 같아요.'
                ]
                
                # 멘토-멘티 메모를 번갈아가며 추가
                for idx in range(min(len(mentee_default_memos), len(mentor_default_memos))):
                    # 멘티 메모
                    mentee_memo_date = start_date + timedelta(days=idx * 5 + 1)
                    cursor.execute('''
                    INSERT INTO memo (create_date, comment, task_assign_id, user_id)
                    VALUES (?, ?, ?, ?)
                    ''', (mentee_memo_date.strftime('%Y-%m-%d'), mentee_default_memos[idx], task_id, mentee_id))
                    
                    # 멘토 메모 (2일 후)
                    mentor_memo_date = start_date + timedelta(days=idx * 5 + 3)
                    cursor.execute('''
                    INSERT INTO memo (create_date, comment, task_assign_id, user_id)
                    VALUES (?, ?, ?, ?)
                    ''', (mentor_memo_date.strftime('%Y-%m-%d'), mentor_default_memos[idx], task_id, mentor_id))
            
            task_id += 1

def print_database_summary(cursor):
    """데이터베이스 내용 요약 출력"""
    print("=" * 80)
    print("멘토-멘티 관계 기반 프로젝트 데이터베이스 생성 완료!")
    print("=" * 80)
    
    # 멘토쉽 구조 출력
    print("\n👥 멘토쉽 구조:")
    print("-" * 60)
    
    cursor.execute('''
    SELECT 
        t.mentorship_id,
        mentor.username as mentor_name,
        mentee.username as mentee_name,
        COUNT(DISTINCT t.task_assign_id) as task_count
    FROM task_assign t
    JOIN users mentee ON t.user_id = mentee.user_id
    JOIN users mentor ON mentor.user_id = (
        SELECT user_id FROM users 
        WHERE role = 'mentor' 
        AND user_id BETWEEN (t.mentorship_id-1)*2+1 AND t.mentorship_id*2
    )
    GROUP BY t.mentorship_id, mentor.username, mentee.username
    ORDER BY t.mentorship_id
    ''')
    
    for mentorship_id, mentor_name, mentee_name, task_count in cursor.fetchall():
        print(f"멘토쉽 {mentorship_id}: {mentor_name} (멘토) ↔ {mentee_name} (멘티) - {task_count}개 작업")
    
    # 상세 작업 예시 출력 (성능 최적화)
    print("\n📋 상세 멘토링 대화 예시 (성능 최적화):")
    print("-" * 60)
    
    cursor.execute('''
    SELECT 
        m.create_date, 
        m.comment, 
        u.role,
        u.username
    FROM task_assign t
    JOIN memo m ON t.task_assign_id = m.task_assign_id
    JOIN users u ON m.user_id = u.user_id
    WHERE t.title = '성능 최적화'
    ORDER BY m.create_date
    LIMIT 6
    ''')
    
    for create_date, comment, role, username in cursor.fetchall():
        role_emoji = "🎓" if role == "mentor" else "👨‍💻"
        print(f"[{create_date}] {role_emoji} {username}: {comment}")
        print()
    
    # 멘토쉽별 통계
    cursor.execute('''
    SELECT 
        t.mentorship_id,
        COUNT(DISTINCT t.task_assign_id) as task_count,
        COUNT(DISTINCT s.subtask_id) as subtask_count,
        COUNT(DISTINCT m.memo_id) as memo_count,
        COUNT(DISTINCT CASE WHEN u.role = 'mentor' THEN m.memo_id END) as mentor_memo_count,
        COUNT(DISTINCT CASE WHEN u.role = 'mentee' THEN m.memo_id END) as mentee_memo_count,
        ROUND(AVG(t.exp), 1) as avg_exp
    FROM task_assign t
    LEFT JOIN subtask s ON t.task_assign_id = s.task_assign_id
    LEFT JOIN memo m ON t.task_assign_id = m.task_assign_id
    LEFT JOIN users u ON m.user_id = u.user_id
    GROUP BY t.mentorship_id
    ORDER BY t.mentorship_id
    ''')
    
    results = cursor.fetchall()
    print(f"\n📊 멘토쉽별 데이터 통계:")
    print("-" * 60)
    for mentorship_id, task_count, subtask_count, memo_count, mentor_memo_count, mentee_memo_count, avg_exp in results:
        print(f"🤝 멘토쉽 {mentorship_id}")
        print(f"   ├─ 할당된 작업: {task_count}개")
        print(f"   ├─ 서브태스크: {subtask_count}개") 
        print(f"   ├─ 전체 메모: {memo_count}개")
        print(f"   │  ├─ 멘토 메모: {mentor_memo_count}개")
        print(f"   │  └─ 멘티 메모: {mentee_memo_count}개")
        print(f"   └─ 평균 경험치: {avg_exp}점")
        print()
    
    # 역할별 통계
    cursor.execute('''
    SELECT 
        u.role,
        COUNT(DISTINCT u.user_id) as user_count,
        COUNT(DISTINCT CASE WHEN u.role = 'mentee' THEN t.task_assign_id END) as task_count,
        COUNT(DISTINCT m.memo_id) as memo_count,
        ROUND(AVG(LENGTH(m.comment)), 1) as avg_memo_length
    FROM users u
    LEFT JOIN task_assign t ON u.user_id = t.user_id
    LEFT JOIN memo m ON u.user_id = m.user_id
    GROUP BY u.role
    ''')
    
    print("👥 역할별 통계:")
    print("-" * 30)
    for role, user_count, task_count, memo_count, avg_memo_length in cursor.fetchall():
        role_name = "멘토" if role == "mentor" else "멘티"
        print(f"{role_name}: {user_count}명")
        if role == "mentee":
            print(f"  ├─ 할당된 작업: {task_count}개")
        print(f"  ├─ 작성한 메모: {memo_count}개")
        print(f"  └─ 평균 메모 길이: {avg_memo_length:.0f}자")
        print()
    
    # 전체 통계
    cursor.execute('SELECT COUNT(*) FROM task_assign')
    task_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM subtask')
    subtask_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM memo')
    memo_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE role = "mentor"')
    mentor_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE role = "mentee"')
    mentee_count = cursor.fetchone()[0]
    
    print("📈 전체 통계:")
    print("-" * 30)
    print(f"총 멘토: {mentor_count}명")
    print(f"총 멘티: {mentee_count}명")
    print(f"총 멘토쉽: 5개")
    print(f"총 작업: {task_count}개")
    print(f"총 서브태스크: {subtask_count}개")
    print(f"총 메모: {memo_count}개")
    
    print(f"\n💡 특징:")
    print("- 각 멘토쉽은 1명의 멘토와 1명의 멘티로 구성")
    print("- 작업은 멘티에게만 할당되며, 멘토는 지도와 피드백 제공")
    print("- 메모는 멘토와 멘티가 번갈아가며 작성하여 실제 멘토링 대화 시뮬레이션")
    print("- 상세 작업(성능 최적화 등)에는 구체적인 기술적 조언과 진행상황 포함")
    print("- 각 멘토쉽은 전문 분야별로 특화된 작업들로 구성")

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
        
        print(f"\n🎉 멘토-멘티 관계 기반 데이터베이스 'task_management.db'가 생성되었습니다.")
        print("실제 멘토링 환경을 시뮬레이션할 수 있는 데이터가 준비되었습니다!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        conn.rollback()
    
    finally:
        # 연결 종료
        conn.close()

if __name__ == "__main__":
    main()