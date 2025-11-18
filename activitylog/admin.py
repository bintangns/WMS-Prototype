from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import ActivityLog

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "workstation", "action", "method", "path", "status_code", "duration_ms")
    list_filter = ("action", "method", "status_code", "workstation")
    search_fields = ("user__username", "path", "action", "ip_address")
