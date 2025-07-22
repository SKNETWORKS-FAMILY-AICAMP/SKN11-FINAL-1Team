# fast_api/Dockerfile
# 1. Base Image
FROM python:3.11-slim
# 2. Set Environment Variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# 3. Set Work Directory
WORKDIR /app
# 4. Install Dependencies
COPY ./requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt
# 5. Copy Project Code
COPY . /app/
# 6. Expose Port
EXPOSE 8000
# 7. Run Uvicorn
# main:app 은 main.py 파일의 app 객체를 의미합니다.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]