# auth/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200, blank=True)
    def __str__(self): return self.name

class User(AbstractUser):
    roles = models.ManyToManyField(Role, blank=True, related_name="users")
    client_scope = models.ManyToManyField(
        "core.Client", blank=True, related_name="scoped_users"
    )
    last_workstation_code = models.CharField(max_length=50, blank=True)

    def has_role(self, *role_names) -> bool:
        return self.roles.filter(name__in=role_names).exists()

class Workstation(models.Model):
    workstation_id = models.CharField(max_length=50, unique=True)
    area = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    def __str__(self): return self.workstation_id

class WorkstationSession(models.Model):
    picker = models.ForeignKey(User, on_delete=models.CASCADE)
    workstation = models.ForeignKey(Workstation, on_delete=models.CASCADE)
    login_time = models.DateTimeField(auto_now_add=True)
    # ⬇️ PERBAIKAN
    logout_time = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    # ⬇️ KONTEKS HU (opsional, dipakai saat scan HU)
    current_hu_code = models.CharField(max_length=64, blank=True, default="")
    current_client_code = models.CharField(max_length=64, blank=True, default="")
    current_items = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.picker.username} @ {self.workstation.workstation_id}"
