import json
from typing import Optional, Dict, Any
from django.utils import timezone
from .models import ActivityLog


def _get_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_activity(
    request,
    action: str,
    *,
    user=None,
    workstation=None,
    extra: Optional[Dict[str, Any]] = None,
    status_code: Optional[int] = None,
):

    if user is None and hasattr(request, "user"):
        if request.user.is_authenticated:
            user = request.user

    ip = _get_ip(request)
    ua = request.META.get("HTTP_USER_AGENT", "")

    # ambil body request tapi jangan simpan password
    body_data = None
    try:
        if hasattr(request, "data"):
            body_data = dict(request.data)
        else:
            if request.body:
                body_data = json.loads(request.body.decode() or "{}")
    except Exception:
        body_data = None

    # masking password kalau ada
    if isinstance(body_data, dict):
        for key in ["password", "pass", "pwd"]:
            if key in body_data:
                body_data[key] = "***"

    ActivityLog.objects.create(
        user=user,
        workstation=workstation,
        action=action,
        method=request.method,
        path=request.path[:255],
        status_code=status_code,
        ip_address=ip,
        user_agent=ua,
        request_body=body_data,
        extra=extra or {},

    )
