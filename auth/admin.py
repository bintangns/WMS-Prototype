from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    filter_horizontal = ("roles", "client_scope")

admin.site.register(Role)
