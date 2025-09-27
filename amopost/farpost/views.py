import logging
from datetime import datetime

from django.http import JsonResponse

from . import api, services

logger = logging.getLogger(__name__)
