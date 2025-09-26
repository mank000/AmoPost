# app_name/tasks.py
import logging

from celery import shared_task
from django.utils import timezone

from . import api

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_notifications(self):
    try:
        answer = api.check_and_fetch_messages()
        if answer:

            logger.info("Notifications fetched: %s", answer)
        else:
            logger.warning("fetch_notifications: empty answer")
    except Exception as exc:
        logger.exception("Error in fetch_notifications")
        raise self.retry(exc=exc)
