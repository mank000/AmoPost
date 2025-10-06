# views_simple.py
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

            parsed_data = urllib.parse.parse_qs(body)

            # Приводим ключи к читаемому виду
            simple_data = {}
            for key, value in parsed_data.items():
                clean_key = key.replace("%5B", "[").replace("%5D", "]")
                simple_data[clean_key] = (
                    value[0] if len(value) == 1 else value
                )

            # Забираем текст сообщения
            message_text = simple_data.get(
                "unsorted[update][0][source_data][data][0][text]"
            )
            message_chat_id = simple_data.get(
                "unsorted[update][0][source_data][origin][chat_id]"
            )

            if message_text:
                chat = LastChatState.objects.filter(
                    uuid_conv=message_chat_id
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
                {"status": "ignored", "message": "No text message found"}
            )

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return JsonResponse(
                {"status": "error", "message": str(e)}, status=500
            )

    return JsonResponse({"error": "Method not allowed"}, status=405)
