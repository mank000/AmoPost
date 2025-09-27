import requests
from django.db import models
from amocrm.models import ProjectSettings 

def get_token_from_db(tokenname):
    """Получение токена из базы данных"""
    try:
        token_record = ProjectSettings.objects.filter(id=1).first()
        if token_record:
            return getattr(token_record, tokenname)
        else:
            raise ValueError("Активный токен не найден в БД")
    except Exception as e:
        print(f"Ошибка получения токена: {e}")
        return None
