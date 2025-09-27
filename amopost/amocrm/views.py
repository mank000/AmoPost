# views_simple.py
import json
import logging
import urllib.parse

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from farpost.models import LastChatState
from farpost import api as farapi
logger = logging.getLogger(__name__)


@csrf_exempt
def amocrm_webhook_simple(request):
    """Упрощенный обработчик вебхука"""
    if request.method == "POST":
        try:
            raw_body = request.body.decode("utf-8")

            parsed_data = urllib.parse.parse_qs(raw_body)
            simple_data = {}
            for key, value in parsed_data.items():
                clean_key = key.replace("%5B", "[").replace("%5D", "]")
                simple_data[clean_key] = value[0] if len(value) == 1 else value

            if "leads[note][0][note][text]" in simple_data:
                note_text = simple_data["leads[note][0][note][text]"]
                element_id = simple_data.get(
                    "leads[note][0][note][element_id]", "unknown"
                )

                chat = LastChatState.objects.filter(id_amocrm=simple_data.get("leads[note][0][note][element_id]")).first()
                if chat and simple_data.get("leads[note][0][note][created_by]") != "0" and chat.last_out_message != simple_data.get("leads[note][0][note][text]")[:254] and chat.last_message != simple_data.get("leads[note][0][note][text]")[:254]:
                    farapi.send_message_to(
                        chat.id_farpost,
                        simple_data.get("leads[note][0][note][text]")
                    )
                    chat.last_out_message = simple_data.get("leads[note][0][note][text]")[:254]
                    chat.save(update_fields=["last_out_message"])

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
