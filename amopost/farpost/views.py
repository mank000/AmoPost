import logging
from datetime import datetime

from django.http import JsonResponse

from . import api, services

logger = logging.getLogger(__name__)


def getAmountNotifications(request):
    answer = api.amountNotification()

    if answer:  # Если ответ получен
        return JsonResponse(
            {
                "success": True,
                "has_notifications": answer.get("HasNotifications", 0),
                "unread_dialogs": answer.get("unreadDialogs", 0),
            }
        )
    else:
        return JsonResponse(
            {"success": False, "error": "Failed to fetch notifications"},
            status=500,
        )


def getMessagesView(request):
    """
    Django view для получения сообщений
    """
    try:
        messages_data = api.getTextInMessage()

        if messages_data is not None:
            # Конвертируем datetime в строку для JSON
            serialized_messages = []
            for message in messages_data:  # messages_data - это список
                if isinstance(message, dict):  # Проверяем, что это словарь
                    serialized_message = message.copy()  # Создаем копию

                    # Конвертируем datetime в строку
                    if serialized_message.get(
                        "lastMessageDate"
                    ) and isinstance(
                        serialized_message["lastMessageDate"],
                        datetime,
                    ):
                        serialized_message["lastMessageDate"] = (
                            serialized_message["lastMessageDate"].isoformat()
                        )

                    serialized_messages.append(serialized_message)

            return JsonResponse(
                {
                    "status": "success",
                    "data": {
                        "messages": serialized_messages,
                        "total_count": len(serialized_messages),
                    },
                    "timestamp": datetime.now().isoformat(),
                }
            )
        else:
            return JsonResponse(
                {
                    "status": "error",
                    "error": "Failed to fetch messages",
                    "timestamp": datetime.now().isoformat(),
                },
                status=500,
            )

    except Exception as e:
        logger.error(f"Ошибка в Django view: {e}")
        return JsonResponse(
            {
                "status": "error",
                "error": "Internal server error",
                "timestamp": datetime.now().isoformat(),
            },
            status=500,
        )
