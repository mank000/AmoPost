# services/amocrm.py
import datetime
import hashlib
import hmac
import json
import logging
import time
import uuid

import requests
from core.misc import get_token_from_db

logger = logging.getLogger(__name__)

LONG_TOKEN = get_token_from_db("AMOCRM_LONG_TOKEN")
session = requests.session()
session.headers.update({"Authorization": f"Bearer {LONG_TOKEN}"})

SCOPE_ID = get_token_from_db("AMOJO_SCOPE_ID")
AMOJO_SECRET = get_token_from_db("AMOJO_SECRET")
URLS = [
    "https://kozminarti.amocrm.ru/api/v4/leads/unsorted/forms",
    "https://kozminarti.amocrm.ru/api/v4/leads///notes",
    "https://amojo.amocrm.ru/v2/origin/custom/",
]
PATH = "/v2/origin/custom/" + str(SCOPE_ID)


def build_amojo_headers(body_str):
    md5sum = hashlib.md5(body_str.encode("utf-8")).hexdigest()
    str_to_sign = "\n".join(
        [
            "POST",
            md5sum,
            "application/json",
            datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT"),
            PATH,
        ]
    )
    signature = hmac.new(
        AMOJO_SECRET.encode("utf-8"),
        str_to_sign.encode("utf-8"),
        hashlib.sha1,
    ).hexdigest()

    return {
        "Date": datetime.datetime.utcnow().strftime(
            "%a, %d %b %Y %H:%M:%S GMT"
        ),
        "Content-Type": "application/json",
        "Content-MD5": md5sum.lower(),
        "X-Signature": signature.lower(),
    }


def send_note(note, id):
    try:
        payload = {
            "event_type": "new_message",
            "payload": {
                "timestamp": int(time.time()),
                "msec_timestamp": round(time.time() * 1000),
                "msgid": str(uuid.uuid4()),  # меняется
                "conversation_id": id,
                "sender": {
                    "id": id,
                },
                "message": {
                    "type": "text",
                    "text": note,
                },
                "silent": False,
            },
        }
        body_str = json.dumps(payload, separators=(",", ":"))
        headers = build_amojo_headers(
            body_str,
        )
        resp = session.post(
            URLS[2] + SCOPE_ID, timeout=5, data=body_str, headers=headers
        )
        if resp.status_code != 200:
            logger.critical(
                f"Статус создания примечания {resp.status_code} err: {resp.text}"
            )
            return None
    except Exception as e:
        logger.critical(f"Критическая ошибка в catch_message: {e}")
        return None


def catch_message(origin_message, model_message):
    try:
        if model_message.uuid_conv is not None:
            model_message.is_sended = True
            model_message.last_message = origin_message.get("message")[:254]
            model_message.save()
            send_note(origin_message.get("message"), model_message.uuid_conv)
            return 0
        uuid_id = str(uuid.uuid4())
        payload = {
            "event_type": "new_message",
            "payload": {
                "timestamp": int(time.time()),
                "msec_timestamp": round(time.time() * 1000),
                "msgid": str(uuid.uuid4()),  # меняется
                "conversation_id": uuid_id,  # В зависимости от сделки! Не рандом!
                "sender": {
                    "id": uuid_id,  # Тоже зависит от сделки по сути рандом
                    "name": f"{origin_message.get('interlocutor')}",
                },
                "message": {
                    "type": "text",
                    "text": f"Сообщение из Farpost!\nСсылка: {origin_message.get('url')}\nТекст сообщения: {origin_message.get('message')}",
                },
                "silent": False,
            },
        }
        body_str = json.dumps(payload, separators=(",", ":"))
        headers = build_amojo_headers(
            body_str,
        )
        resp = session.post(
            URLS[2] + SCOPE_ID, timeout=5, data=body_str, headers=headers
        )
        if resp.status_code != 200:
            logger.critical(
                f"Статус создания сообщения {resp.status_code} err: {resp.text}"
            )
            return None

        data = resp.json()
        logger.error(uuid_id)

        model_message.uuid_conv = uuid_id
        model_message.is_sended = True
        model_message.last_message = origin_message.get("message")[:254]
        model_message.save()
        # send_note(origin_message.get("message"), uuid_id)
    except Exception as e:
        logger.critical(f"Критическая ошибка в catch_message: {e}")
        return None
