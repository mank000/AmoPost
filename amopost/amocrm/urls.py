from django.urls import path

from . import views

urlpatterns = [
    path(
        "msg_webhook/",
        views.amocrm_webhook_simple,
        name="amocrm-webhook",
    ),
    # path("webhooks/amocrm/", views.amocrm_webhook, name="amocrm_webhook"),
    # path('amocrm/auth/', views.AmoCRMAuthView.as_view(), name='amocrm-auth'),
    # path('amocrm/callback/', views.AmoCRMCallbackView.as_view(), name='amocrm-callback'),
]
