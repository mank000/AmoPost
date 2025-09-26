# views_simple.py
import json
import logging
import urllib.parse

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


@csrf_exempt
def amocrm_webhook_simple(request):
    """Упрощенный обработчик вебхука"""
    if request.method == "POST":
        try:
            # Логируем сырые данные
            raw_body = request.body.decode("utf-8")
            logger.info(f"Raw body: {raw_body}")

            # Парсим form-data
            parsed_data = urllib.parse.parse_qs(raw_body)

            # Упрощаем структуру (берем первые значения)
            simple_data = {}
            for key, value in parsed_data.items():
                clean_key = key.replace("%5B", "[").replace("%5D", "]")
                simple_data[clean_key] = value[0] if len(value) == 1 else value

            logger.info("Parsed data:")
            for key, value in simple_data.items():
                logger.info(f"{key}: {value}")

            # Проверяем, что это заметка
            if "leads[note][0][note][text]" in simple_data:
                note_text = simple_data["leads[note][0][note][text]"]
                element_id = simple_data.get(
                    "leads[note][0][note][element_id]", "unknown"
                )

                logger.info(
                    f"✅ Получена заметка для элемента {element_id}: {note_text}"
                )

                # Здесь ваша бизнес-логика
                # Например, сохранение в базу, отправка уведомления и т.д.

                return JsonResponse(
                    {
                        "status": "success",
                        "message": "Note processed",
                        "element_id": element_id,
                        "note_text": note_text,
                    }
                )

            return JsonResponse(
                {
                    "status": "success",
                    "message": "Webhook received",
                    "data_keys": list(simple_data.keys()),
                }
            )

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return JsonResponse(
                {"status": "error", "message": str(e)}, status=500
            )

    return JsonResponse({"error": "Method not allowed"}, status=405)
