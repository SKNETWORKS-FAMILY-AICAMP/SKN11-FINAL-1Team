# PostgreSQL 완전 가이드 - Django 프로젝트용

## 목차
1. [PostgreSQL 설치](#1-postgresql-설치)
2. [설치 후 설정](#2-설치-후-설정)
3. [인증 문제 해결](#3-인증-문제-해결)
4. [Django 마이그레이션](#4-django-마이그레이션)
5. [데이터 확인 및 관리](#5-데이터-확인-및-관리)
6. [문제 해결](#6-문제-해결)

---

## 1. PostgreSQL 설치

### 방법 1: 공식 PostgreSQL 설치 (권장)

#### 1.1 PostgreSQL 다운로드
1. https://www.postgresql.org/download/windows/ 접속
2. "Download the installer" 클릭
3. Windows x86-64 17 버전 다운로드

#### 1.2 설치 진행
1. 다운로드한 파일을 관리자 권한으로 실행
2. 설치 중 설정:
   - **설치 경로**: 기본값 사용 (C:\Program Files\PostgreSQL\17\)
   - **구성 요소**: 모두 선택 (PostgreSQL Server, pgAdmin 4, Stack Builder, Command Line Tools)
   - **데이터 디렉토리**: 기본값 사용
   - **비밀번호**: postgres 사용자 비밀번호 설정 (.env 파일에 추가)
   - **포트**: 5432 (기본값)
   - **로케일**: 기본값 사용

#### 1.3 환경 변수 설정 (자동으로 안 된 경우)
1. 시스템 속성 > 고급 > 환경 변수
2. 시스템 변수의 Path에 추가:
   - C:\Program Files\PostgreSQL\17\bin
   - C:\Program Files\PostgreSQL\17\lib

### 방법 2: Chocolatey 사용 (개발자용)

#### 2.1 Chocolatey 설치 (없는 경우)
PowerShell을 관리자 권한으로 실행:
```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

#### 2.2 PostgreSQL 설치
```cmd
choco install postgresql
```

### 방법 3: Docker 사용 (가장 간단)

#### 3.1 Docker Desktop 설치
https://www.docker.com/products/docker-desktop에서 다운로드

#### 3.2 PostgreSQL 컨테이너 실행
```cmd
docker run --name postgres-db -e POSTGRES_PASSWORD=your_password -p 5432:5432 -d postgres:15
```

#### 3.3 컨테이너에 접속
```cmd
docker exec -it postgres-db psql -U postgres
```

---

## 2. 설치 후 설정

### 2.1 설치 확인
```cmd
psql --version
```

### 2.2 PostgreSQL 서비스 시작 (Windows)
```cmd
# 서비스 관리자에서 PostgreSQL 서비스 시작하거나:
net start postgresql-x64-17

# 서비스 상태 확인
services.msc
# postgresql-x64-17 서비스가 실행 중인지 확인
```

### 2.3 데이터베이스 생성
```cmd
# 방법 1: 명령줄에서 직접
createdb -U postgres onboarding_quest_db

# 방법 2: psql 접속 후
psql -U postgres
CREATE DATABASE onboarding_quest_db;
\l
\q
```

---

## 3. 인증 문제 해결

### 3.1 기본 접속 시도
```cmd
psql -U postgres                    # postgres 사용자로 접속
psql -U postgres -h localhost       # 호스트 지정하여 접속
psql -U postgres -h localhost -p 5432  # 포트까지 지정
```

### 3.2 "사용자 인증 실패" 오류 해결

#### 방법 1: 환경 변수 설정
```cmd
set PGUSER=postgres
set PGPASSWORD=your_postgres_password
psql
```

#### 방법 2: pg_hba.conf 수정 (고급)

**1단계: pg_hba.conf 파일 찾기**
일반적인 위치:
- C:\Program Files\PostgreSQL\17\data\pg_hba.conf

**2단계: 파일 백업**
```cmd
copy "C:\Program Files\PostgreSQL\17\data\pg_hba.conf" "C:\Program Files\PostgreSQL\17\data\pg_hba.conf.backup"
```

**3단계: 메모장으로 편집 (관리자 권한 필요)**
다음 줄을 찾아서:
```
# IPv4 local connections:
host    all             all             127.0.0.1/32            scram-sha-256
```

다음과 같이 변경:
```
# IPv4 local connections:
host    all             all             127.0.0.1/32            trust
```

**4단계: PostgreSQL 서비스 재시작**
```cmd
net stop postgresql-x64-17
net start postgresql-x64-17
```

#### 방법 3: 새 사용자 생성
postgres로 접속 후 새 사용자 생성:
```sql
CREATE USER playdata WITH PASSWORD 'your_password';
ALTER USER playdata CREATEDB;
GRANT ALL PRIVILEGES ON DATABASE postgres TO playdata;
```

### 3.3 비밀번호 재설정 (trust 모드에서)
```sql
ALTER USER postgres PASSWORD 'new_password';
```

---

## 4. Django 마이그레이션

### 4.1 Django 설정 업데이트
settings.py에서 DATABASES 설정을 PostgreSQL로 변경:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'onboarding_quest_db',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 4.2 필수 패키지 설치
```cmd
pip install psycopg2-binary
```

### 4.3 기존 마이그레이션 파일 삭제 (선택사항)
완전히 새로 시작하려면:
```cmd
# Windows에서:
for /d /r . %d in (*migrations*) do @if exist "%d" for %f in ("%d\*.py") do @if not "%~nxf"=="__init__.py" del "%f"
```

### 4.4 마이그레이션 실행
```cmd
# 새로운 마이그레이션 생성
python manage.py makemigrations

# 마이그레이션 적용
python manage.py migrate

# 샘플 데이터 생성
python manage.py make_sample

# 슈퍼유저 생성
python manage.py createsuperuser

# 개발 서버 실행
python manage.py runserver
```

---

## 5. 데이터 확인 및 관리

### 5.1 기본 접속
```bash
psql -U postgres                    # postgres 사용자로 접속
psql -U postgres -d onboarding_quest_db   # 특정 데이터베이스에 접속
```

### 5.2 데이터베이스 관련 명령어
```sql
-- 모든 데이터베이스 목록 확인
\l

-- 현재 데이터베이스 확인
SELECT current_database();

-- 데이터베이스 연결
\c onboarding_quest_db

-- 현재 연결 정보
\conninfo
```

### 5.3 테이블 관련 명령어
```sql
-- 현재 데이터베이스의 모든 테이블 목록
\dt

-- 스키마 포함 모든 테이블 목록
\dt *.*

-- 특정 테이블 구조 확인
\d table_name

-- 테이블 상세 정보 (컬럼, 타입, 제약조건 등)
\d+ table_name

-- Django 관련 테이블들 확인
\dt django_*
\dt core_*
\dt account_*
\dt mentor_*
\dt mentee_*
```

### 5.4 데이터 조회 명령어
```sql
-- 테이블의 모든 데이터 조회
SELECT * FROM table_name;

-- 테이블의 행 개수 확인
SELECT COUNT(*) FROM table_name;

-- 테이블의 처음 5개 행 확인
SELECT * FROM table_name LIMIT 5;

-- Django 마이그레이션 상태 확인
SELECT * FROM django_migrations;

-- Django 사용자 테이블 확인 (User 모델)
SELECT * FROM core_user;
```

### 5.5 사용자 및 권한 확인
```sql
-- 모든 사용자 목록
\du

-- 현재 사용자 확인
SELECT current_user;

-- 데이터베이스 소유자 확인
SELECT datname, datdba FROM pg_database;
```

### 5.6 데이터베이스 상태 확인
```sql
-- 활성 연결 확인
SELECT * FROM pg_stat_activity;

-- 데이터베이스 크기 확인
SELECT pg_size_pretty(pg_database_size('onboarding_quest_db'));

-- 테이블 크기 확인
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 5.7 유용한 psql 명령어
```sql
-- 도움말
\?

-- SQL 명령어 도움말
\h

-- 실행 시간 표시 토글
\timing

-- 결과를 파일로 저장
\o filename.txt
SELECT * FROM table_name;
\o

-- psql 종료
\q
```

### 5.8 Django에서 PostgreSQL 데이터 확인
```python
# Django shell에서
python manage.py shell

# Python 코드에서
from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT * FROM core_user LIMIT 5;")
results = cursor.fetchall()
print(results)
```

---

## 6. 문제 해결

### 6.1 psql 명령어가 안 될 때
1. PostgreSQL이 설치되었는지 확인
2. 환경 변수 PATH에 PostgreSQL bin 폴더 추가
3. 명령 프롬프트 재시작

### 6.2 연결 오류가 날 때
1. PostgreSQL 서비스가 실행 중인지 확인
2. 포트 5432가 사용 중인지 확인: `netstat -an | findstr 5432`
3. 방화벽 설정 확인

### 6.3 Django 설정 주의사항
- settings.py의 PASSWORD를 실제 PostgreSQL 비밀번호로 변경하세요
- PostgreSQL이 localhost:5432에서 실행 중인지 확인하세요
- 방화벽에서 5432 포트가 열려있는지 확인하세요

### 6.4 빠른 확인 순서
1. `\l` - 데이터베이스 목록 확인
2. `\c onboarding_quest_db` - 대상 데이터베이스 연결
3. `\dt` - 테이블 목록 확인
4. `SELECT * FROM table_name LIMIT 5;` - 데이터 확인

### 6.5 추천 해결 순서 (인증 문제)
1. `psql -U postgres` 시도
2. postgres 비밀번호가 기억나지 않으면 pg_hba.conf를 trust로 변경
3. trust로 접속 후 비밀번호 재설정
4. 다시 scram-sha-256로 되돌리기

---

## 추천사항

### Docker 방법이 가장 간단합니다!
특히 개발 환경에서는 Docker를 사용하는 것이 가장 간단하고 깔끔합니다.

### 프로덕션 환경에서는
- 공식 PostgreSQL 설치를 권장합니다
- 적절한 보안 설정을 해주세요
- 정기적인 백업을 설정하세요
