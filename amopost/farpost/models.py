from django.db import models

class LastChatState(models.Model):
    id_farpost = models.CharField(null=False, blank=False)
    id_amocrm = models.CharField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    is_sended = models.BooleanField(default=False)
    last_message = models.CharField(max_length=256, null=True, blank=True)
    last_out_message = models.CharField(max_length=256, null=True, blank=True)
    class Meta:
        verbose_name = "Состояние последнего чата"
        verbose_name_plural = "Состояние последнего чата"

    def __str__(self):
        return f"LastChatState(id_farpost={self.id_farpost}, id_amo={self.id_amocrm})"
