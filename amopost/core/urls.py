from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("amocrm/", include("amocrm.urls")),
    path("farpost/", include("farpost.urls")),
]
