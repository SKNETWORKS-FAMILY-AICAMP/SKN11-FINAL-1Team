# django_prj/onboarding_quest/Dockerfile
    # 1. Base Image
FROM python:3.11-slim
# 2. Set Environment Variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# 3. Set Work Directory
WORKDIR /app

# 4. Install Dependencies
# requirements.txt 경로를 정확히 지정해야 합니다.
COPY ./requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt
# Gunicorn은 프로덕션 환경에서 Django를 실행하기 위한 WSGI 서버입니다.
RUN pip install gunicorn

# 5. Copy Project Code
COPY . /app/

# 6. Expose Port
EXPOSE 8000

# 7. Run Gunicorn
# onboarding_quest.wsgi:application 경로는 프로젝트 구조에 맞게 수정해야 할 수있습니다.
CMD ["gunicorn", "onboarding_quest.wsgi:application", "--bind", "0.0.0.0:8000"]