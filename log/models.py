from django.conf import settings
from django.db import models

class LogEntry(models.Model):
    class Action(models.TextChoices):
        CREATE_INVOICE = "CREATE_INVOICE", "Create Invoice"
        UPDATE_INVOICE = "UPDATE_INVOICE", "Update Invoice"
        DELETE_INVOICE = "DELETE_INVOICE", "Delete Invoice"
        CHANGE_STATUS  = "CHANGE_STATUS",  "Change Invoice Status"
        CREATE_REMARK  = "CREATE_REMARK",  "Create Invoice Remark"
        DELETE_REMARK  = "DELETE_REMARK",  "Delete Invoice Remark"
        REORDER_REMARK = "REORDER_REMARK", "Reorder Invoice Remark"

    class Entity(models.TextChoices):
        INVOICE = "INVOICE", "Invoice"
        REMARK  = "REMARK",  "Invoice Remark"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True, on_delete=models.SET_NULL, related_name="log_entries"
    )
    username_cache = models.CharField(max_length=150, blank=True, default="")
    action = models.CharField(max_length=32, choices=Action.choices)
    entity_type = models.CharField(max_length=16, choices=Entity.choices)
    entity_id = models.IntegerField(null=True, blank=True)
    entity_label = models.CharField(max_length=255, blank=True, default="")
    details = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["action"]),
            models.Index(fields=["entity_type"]),
        ]

    def __str__(self):
        who = self.username_cache or (self.user and self.user.get_username()) or "Unknown"
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {who} - {self.get_action_display()} ({self.entity_type})"
