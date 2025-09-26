from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path("amountnotifications/", views.getAmountNotifications),
    path("readnotifications/", views.getMessagesView),
    # path("sendmessage/", viws.sendMessage)
]
