import datetime
import html
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

import requests
from amocrm import api as amoapi
from bs4 import BeautifulSoup
from core.misc import get_token_from_db
from django.conf import settings
from django.core.cache import cache

from . import models

logger = logging.getLogger(__name__)

token = get_token_from_db("FARPOST_TOKEN")
session = requests.Session()
session.headers.update({"Cookie": f"boobs={token}"})
URLS = [
    "https://www.farpost.ru/personal/messaging/inbox-config/",
    "https://www.farpost.ru/personal/messaging/inbox-list/",
    "https://www.farpost.ru/personal/messaging/view?dialogId=",
]


def extract_message_text(html_string):
    """Извлечение текста сообщения из HTML"""
    decoded_html = html.unescape(html_string)

    soup = BeautifulSoup(decoded_html, "html.parser")
    message_element = soup.find("div", class_="dialog-brief__latest_msg")

    if message_element:
        return message_element.get_text(strip=True)
    return None


def amount_notification():
    """
    True: unreadDialogs > 0
    False: unreadDialgs < 0
    """
    try:
        resp = session.get(URLS[0], timeout=10)
        if resp.status_code != 200:
            logger.critical(
                f"Статус при получении нотификаций: {resp.status_code}"
            )
            return None
        data = resp.json()
        return data.get("eventCounts", {}).get("unreadDialogs", 0) != 0

    except Exception as e:
        logger.exception(f"Ошибка при получении количества нотификаций: {e}")
        return None


def get_text_in_message():
    try:
        resp = session.get(URLS[1], timeout=10)
        if resp.status_code != 200:
            logger.critical(
                f"HTTP {resp.status_code} при получении сообщений"
            )
            return None
        data = resp.json()
        briefs = data.get("briefs", [])

        messages = []

        for index, brief in enumerate(briefs):
            dialog_id = brief.get("dialogId")
            # if not dialog_id or not bool(brief.get("isUnread", False)):
            #     continue

            html_content = brief.get("html")
            message_text = (
                extract_message_text(html_content) if html_content else None
            )

            messages.append(
                {
                    "dialogId": dialog_id,
                    "interlocutor": brief.get("interlocutor", "Неизвестный"),
                    "message": message_text,
                    "hasMessage": message_text is not None,
                    "url": f"https://farpost.ru{brief.get('url')}",
                }
            )
        return messages

    except requests.exceptions.RequestException as e:
        logger.critical(f"Ошибка сети: {e}")
        return None
    except Exception as e:
        logger.critical(f"Критическая ошибка в get_text_in_message: {e}")
        return None


def check_and_fetch_messages():

    if not amount_notification():
        return None

    messages = get_text_in_message()
    if messages is None:
        return None

    if messages:
        for message in messages:
            this_chat, created = models.LastChatState.objects.get_or_create(
                id_farpost=message.get("dialogId")
            )
            if not this_chat.is_sended or (
                this_chat.last_message[:254] != message.get("message")[:254]
            ):
                amoapi.catch_message(message, this_chat)
    else:
        logger.info("Сообщения отсутствуют или пусты")
    return messages


def send_message_to(id, message):
    try:
        resp = session.post(
            f"{URLS[2]}{id}",
            data=f"message={message}",
            headers={
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8"
            },
        )
        pass
        if resp.status_code != 200:
            logger.critical(f"Ошибка в send_message_to {resp.status_code}")
            return None
    except Exception as e:
        logger.critical(f"Критическая ошибка в send_message_to: {e}")
        return None
