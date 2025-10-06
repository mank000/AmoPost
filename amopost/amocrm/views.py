# views_simple.py
import json
import logging
import urllib.parse

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from farpost import api as farapi
from farpost.models import LastChatState

logger = logging.getLogger(__name__)


@csrf_exempt
def amocrm_webhook_simple(request):
    """Упрощенный обработчик вебхука (только текстовые сообщения)"""
    if request.method == "POST":
        try:
            body = request.body.decode("utf-8")
            logger.info(body)

            hook_body = json.loads(body)

            message = hook_body.get("message", {}).get("message", {})
            conversation = hook_body.get("message", {}).get(
                "conversation", {}
            )
            receiver = hook_body.get("message", {}).get("receiver", {})

            message_id = message.get("id")
            message_type = message.get("type")
            message_text = message.get("text")
            message_chat_id = conversation.get("client_id")
            message_amocrm_chat_id = conversation.get("id")

            if message_type == "text" and message_text:
                chat = LastChatState.objects.filter(
                    id_amocrm=message_amocrm_chat_id
                ).first()
                if (
                    chat
                    and message_text[:254] != chat.last_out_message
                    and message_text[:254] != chat.last_message
                ):
                    farapi.send_message_to(chat.id_farpost, message_text)
                    chat.last_out_message = message_text[:254]
                    chat.save(update_fields=["last_out_message"])

                return JsonResponse(
                    {
                        "status": "success",
                        "message": "Text message processed",
                        "chat_id": message_chat_id,
                        "text": message_text,
                    }
                )

            return JsonResponse(
                {
                    "status": "ignored",
                    "message": "Only text messages are processed",
                }
            )

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return JsonResponse(
                {"status": "error", "message": str(e)}, status=500
            )

    return JsonResponse({"error": "Method not allowed"}, status=405)
