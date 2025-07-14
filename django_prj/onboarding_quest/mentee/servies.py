import requests
from django.conf import settings


def get_mentee_data(mentee_id):
    try:
        response = requests.get(f"{settings.FASTAPI_BASE_URL}/mentee")
        if response.status_code == 200:
            return response.json()
        return {"error": "API 호출 실패"}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}