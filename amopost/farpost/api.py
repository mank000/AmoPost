import datetime
import html
import json
import logging
import os
from typing import Any, Dict, Optional

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.cache import cache
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

token = os.getenv("FARPOST_TOKEN")
session = requests.Session()
session.headers.update({"Cookie": f"boobs={token}"})
URLS = [
    "https://www.farpost.ru/personal/messaging/inbox-config/",
    "https://www.farpost.ru/personal/messaging/inbox-list/",
]


def extract_message_text(html_string):
    """Извлечение текста сообщения из HTML"""
    decoded_html = html.unescape(html_string)

    soup = BeautifulSoup(decoded_html, "html.parser")
    message_element = soup.find("div", class_="dialog-brief__latest_msg")

    if message_element:
        return message_element.get_text(strip=True)
    return None


def amountNotification():
    response = session.get(URLS[0])
    if response.status_code == 200:
        try:
            data = response.json()
            return {
                "HasNotifications": data.get("hasNotifications", 0),
                "unreadDialogs": data.get("eventCounts", {}).get(
                    "unreadDialogs", 0
                ),
            }
        except Exception as e:
            logger.error(f"Ошибка при получении количества нотификаций. {e}")
    logger.critical(
        f"При получении количества нотификаций статус код: {response.code}"
    )


def getTextInMessage():
    try:
        response = session.get(URLS[1])

        if response.status_code == 200:
            try:
                data = response.json()
                briefs: list = data.get("briefs", [])

                logger.info(f"Получено briefs: {len(briefs)}")

                if not briefs:
                    logger.info("Нет новых сообщений")
                    return []

                messages = []
                for index, brief in enumerate(briefs):
                    try:
                        dialog_id = brief.get("dialogId")
                        if not dialog_id:
                            logger.warning(
                                f"Пропущен brief без dialogId: индекс {index}"
                            )
                            continue

                        interlocutor = brief.get("interlocutor", "Неизвестный")

                        last_message_timestamp = brief.get("lastMessageDate")
                        if last_message_timestamp:
                            last_message_date = (
                                datetime.datetime.fromtimestamp(
                                    last_message_timestamp
                                )
                            )
                        else:
                            last_message_date = None

                        html_content = brief.get("html")
                        message_text = (
                            extract_message_text(html_content)
                            if html_content
                            else None
                        )

                        message_data = {
                            "dialogId": dialog_id,
                            "interlocutor": interlocutor,
                            "lastMessageDate": last_message_date,
                            "message": message_text,
                            "hasMessage": message_text is not None,
                            "timestamp": last_message_timestamp,
                        }

                        messages.append(message_data)
                        logger.debug(
                            f"Обработан диалог {dialog_id} с {interlocutor}"
                        )

                    except Exception as e:
                        logger.error(
                            f"Ошибка при обработке brief {index}: {e}"
                        )
                        continue

                logger.info(f"Успешно обработано сообщений: {len(messages)}")
                return messages

            except ValueError as e:
                logger.error(f"Ошибка парсинга JSON: {e}")
                return None
            except Exception as e:
                logger.error(f"Неожиданная ошибка при обработке данных: {e}")
                return None
        else:
            logger.critical(
                f"Ошибка HTTP при получении сообщений. Статус код: {response.status_code}"
            )
            logger.debug(
                f"Ответ сервера: {response.text[:500]}"
            )  # Логируем первые 500 символов
            return None

    except requests.exceptions.ConnectionError as e:
        logger.critical(f"Ошибка соединения: {e}")
        return None
    except requests.exceptions.Timeout as e:
        logger.critical(f"Таймаут соединения: {e}")
        return None
    except Exception as e:
        logger.critical(f"Критическая ошибка в getTextInMessage: {e}")
        return None
    

def addToDb(dialogId, time):
    



def check_and_fetch_messages():
    notification_data = amountNotification()
    if not notification_data:
        logger.error("Не удалось получить данные о нотификациях")
        return None

    unread_dialogs = notification_data.get("unreadDialogs", 0)
    if unread_dialogs == 0:
        logger.info("Новых сообщений нет")
        return []

    # Если есть непрочитанные сообщения, получаем их
    messages = getTextInMessage()
    if messages is None:
        logger.error("Не удалось получить сообщения")
        return None

    if messages:
        logger.info(f"Получено {len(messages)} новых сообщений")
        # Здесь можно добавить вызов функции из другого приложения
        # Например: some_external_function(messages)
    else:
        logger.info("Сообщения отсутствуют или пусты")

    return messages
