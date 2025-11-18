from django.conf import settings
from django.db import models


class ActivityLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="activity_logs",
    )
    # ambil dari app auth (label-nya custom_auth tapi path model-nya tetap "auth.Workstation")
    workstation = models.ForeignKey(
        "custom_auth.Workstation",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="activity_logs",
    )

    action = models.CharField(max_length=100)    # contoh: "workstation_login", "verify_item"
    method = models.CharField(max_length=10)     # GET/POST/PUT/DELETE
    path = models.CharField(max_length=255)      # request.path
    status_code = models.PositiveIntegerField(null=True, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    request_body = models.JSONField(null=True, blank=True)
    extra = models.JSONField(null=True, blank=True)  # detail tambahan bebas

    duration_ms = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        uname = self.user.username if self.user else "anonymous"
        return f"[{self.created_at:%Y-%m-%d %H:%M:%S}] {uname} {self.action} {self.path}"
