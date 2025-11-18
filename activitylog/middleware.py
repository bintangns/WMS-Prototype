import time
import json

from django.utils.deprecation import MiddlewareMixin

from .models import ActivityLog


class ActivityLoggingMiddleware(MiddlewareMixin):
    """
    Middleware ini nge-log SEMUA request/response (ringan),
    supaya ada jejak umum di luar event bisnis spesifik.
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        request._log_start_time = time.monotonic()
        return None

    def process_response(self, request, response):
        try:
            duration = None
            if hasattr(request, "_log_start_time"):
                duration = (time.monotonic() - request._log_start_time) * 1000.0

            user = getattr(request, "user", None)
            if not getattr(user, "is_authenticated", False):
                user = None

            # workstation coba diambil dari atribut user (last_workstation_code) kalau ada
            workstation = None
            try:
                from auth.models import Workstation  # import lokal biar ga circular

                if user is not None and getattr(user, "last_workstation_code", None):
                    workstation = Workstation.objects.filter(
                        workstation_id=user.last_workstation_code
                    ).first()
            except Exception:
                workstation = None

            # IP & UA
            ip = None
            xff = request.META.get("HTTP_X_FORWARDED_FOR")
            if xff:
                ip = xff.split(",")[0].strip()
            else:
                ip = request.META.get("REMOTE_ADDR")

            ua = request.META.get("HTTP_USER_AGENT", "")

            body_data = None
            if request.method in ("POST", "PUT", "PATCH"):
                try:
                    if hasattr(request, "data"):
                        body_data = dict(request.data)
                    elif request.body:
                        body_data = json.loads(request.body.decode() or "{}")
                except Exception:
                    body_data = None

            # masking password sekalian
            if isinstance(body_data, dict):
                for key in ["password", "pass", "pwd"]:
                    if key in body_data:
                        body_data[key] = "***"

            ActivityLog.objects.create(
                user=user,
                workstation=workstation,
                action=f"{request.method} {request.path}",
                method=request.method,
                path=request.path[:255],
                status_code=getattr(response, "status_code", None),
                ip_address=ip,
                user_agent=ua,
                request_body=body_data,
                extra={},
                duration_ms=duration,
            )
        except Exception:
            pass

        return response
