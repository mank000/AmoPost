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
        msg_text = origin_message.get("message") or ""
        interlocutor = origin_message.get("interlocutor") or ""
        url = origin_message.get("url") or ""

        if model_message.uuid_conv:
            model_message.last_message = msg_text[:254]
            # Здесь мы НЕ трогаем is_sended, он отражает именно отправку
            model_message.save(update_fields=["last_message"])
            send_note(msg_text, model_message.uuid_conv)

        uuid_id = str(uuid.uuid4())
        model_message.uuid_conv = uuid_id
        model_message.last_message = msg_text[:254]
        model_message.is_sended = False
        model_message.save(
            update_fields=["uuid_conv", "last_message", "is_sended"]
        )

        payload = {
            "event_type": "new_message",
            "payload": {
                "timestamp": int(time.time()),
                "msec_timestamp": round(time.time() * 1000),
                "msgid": str(uuid.uuid4()),
                "conversation_id": uuid_id,
                "sender": {
                    "id": uuid_id,
                    "name": f"{interlocutor}",
                },
                "message": {
                    "type": "text",
                    "text": f"Сообщение из Farpost!\nСсылка: {url}\nТекст сообщения: {msg_text}",
                },
                "silent": False,
            },
        }
        body_str = json.dumps(payload, separators=(",", ":"))
        headers = build_amojo_headers(body_str)

        resp = session.post(
            URLS[2] + SCOPE_ID,
            timeout=5,
            data=body_str,
            headers=headers,
        )

        if resp.status_code == 200:
            model_message.is_sended = True
            model_message.save(update_fields=["is_sended"])
            return 0

        logger.error(
            "Статус создания сообщения %s err: %s",
            resp.status_code,
            resp.text,
        )
        # Оставляем запись в БД с is_sended=False для ретрая
        return None

    except Exception:
        # Не глотаем стектрейс — так поймаем ошибки БД (например, длина поля)
        logger.exception("Критическая ошибка в catch_message")
        return None
