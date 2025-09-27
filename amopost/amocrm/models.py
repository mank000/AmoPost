from django.db import models

class ProjectSettings(models.Model):
    FARPOST_TOKEN = models.CharField(max_length=512, null=True, blank=True)
    AMOCRM_LONG_TOKEN = models.CharField(max_length=1200, null=True, blank=True)

    class Meta:
        verbose_name = "Настройки"
        verbose_name_plural = "Настройки"
    
    def __str__(self):
        return f"Настройки проекта"