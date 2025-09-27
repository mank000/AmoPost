# services/amocrm.py
import datetime
import logging
from typing import Any, Dict, Optional, Literal
import uuid
import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from core.misc import get_token_from_db
from farpost.models import LastChatState  # проверь путь

logger = logging.getLogger(__name__)

LONG_TOKEN = get_token_from_db("AMOCRM_LONG_TOKEN")
session = requests.session()
session.headers.update({"Authorization": f"Bearer {LONG_TOKEN}"})

URLS = [
    "https://kozminarti.amocrm.ru/api/v4/leads/unsorted/forms",
    "https://kozminarti.amocrm.ru/api/v4/leads///notes"
]


def send_note(note, id):
    try:
        payload = [{
            "note_type": "common",
            "params": {
                "text": note
            }
        }]
        resp = session.post(URLS[1].replace("///", f"/{id}/"), json=payload)
        if resp.status_code != 200:
            logger.critical(f"Статус создания примечания {resp.status_code} err: {resp.text}")
            return None
    except Exception as e:
        logger.critical(f"Критическая ошибка в catch_message: {e}")
        return None       


def catch_message(origin_message, model_message):
    try:
        logger.info(model_message.id_amocrm)
        if model_message.id_amocrm != None:
            model_message.is_sended = True
            model_message.last_message = origin_message.get("message")[:254]
            model_message.save()
            send_note(origin_message.get("message"), model_message.id_amocrm)
            return 0
        payload = [{
            "source_name": origin_message.get("interlocutor"),
            "source_uid": str(uuid.uuid4()),
            "metadata": {
                "form_id": str(uuid.uuid4()),
                "form_sent_at": int(datetime.datetime.timestamp(datetime.datetime.now())),
                "form_page": origin_message.get("url"),
                "form_name": origin_message.get("interlocutor")
            },
            "_embedded": {
                "companies": [{
                    "name": origin_message.get("interlocutor"),
                    "custom_fields_values": [{
                        "field_code": "WEB",
                        "values": [{
                            "value": origin_message.get("url")
                        }]
                    }]
                }]
            }
        }]
        logger.info(payload)
        resp = session.post(URLS[0], timeout=5, json=payload)
        if resp.status_code != 200:
            logger.critical(f"Статус создания сообщения {resp.status_code} err: {resp.text}")
            return None
        
        data = resp.json()

        uid = data.get("_embedded").get("unsorted")[0].get("_embedded").get("leads")[0].get("id")
        model_message.id_amocrm = uid
        model_message.is_sended = True
        model_message.last_message = origin_message.get("message")[:254]
        model_message.save()
        send_note(origin_message.get("message"), uid)
    except Exception as e:
        logger.critical(f"Критическая ошибка в catch_message: {e}")
        return None       