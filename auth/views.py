# auth/views.py

from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    WorkstationLoginSerializer,
    RegisterSerializer,
)
from .models import WorkstationSession, Workstation, User
from .token import WmsTokenObtainPairSerializer

# ========================
# JWT Login User
# ========================
class WmsTokenView(TokenObtainPairView):
    serializer_class = WmsTokenObtainPairSerializer

# ========================
# REGISTER PACKER (ADMIN ONLY)
# ========================
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        s = RegisterSerializer(data=request.data)
        if s.is_valid():
            user = s.save()
            return Response({
                "status": "success",
                "message": f"User {user.username} (PACKER) berhasil dibuat.",
                "user_id": user.id
            }, status=status.HTTP_201_CREATED)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

# ========================
# WORKSTATION LOGIN (PACKER)
class WorkstationLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        s = WorkstationLoginSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        user = s.validated_data["user"]
        ws   = s.validated_data["workstation"]

        # 1) Close Session if login again
        WorkstationSession.objects.filter(
            picker=user, is_active=True
        ).update(is_active=False, logout_time=timezone.now())

        # 2) Set last workstation
        user.last_workstation_code = ws.workstation_id
        user.save(update_fields=["last_workstation_code"])

        # Buat sesi baru
        session = WorkstationSession.objects.create(
            picker=user,
            workstation=ws,
            is_active=True,
            login_time=timezone.now(),
        )

        refresh = RefreshToken.for_user(user)
        refresh["workstation"] = ws.workstation_id
        refresh["roles"] = list(user.roles.values_list("name", flat=True))

        return Response({
            "status": "success",
            "message": f"Workstation {ws.workstation_id} berhasil didaftarkan.",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "session_id": session.id,  # dijamin ACTIVE
        }, status=status.HTTP_200_OK)
# ========================
# WORKSTATION LOGOUT (PACKER)
# ========================
class WorkstationLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        # tutup semua sesi aktif milik user
        updated = WorkstationSession.objects.filter(
            picker=user, is_active=True
        ).update(is_active=False, logout_time=timezone.now())

        # (opsional) blacklist refresh kalau dikirim
        refresh_token = request.data.get("refresh")
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                pass

        return Response({
            "status": "success",
            "message": f"Logout selesai (closed_sessions={updated})"
        }, status=status.HTTP_200_OK)


class RegisterWorkstationView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        workstation_id = request.data.get("workstation_id")
        description = request.data.get("description", "")
        if not workstation_id:
            return Response({"workstation_id": "Harus diisi"}, status=400)
        if Workstation.objects.filter(workstation_id=workstation_id).exists():
            return Response({"workstation_id": "Sudah terdaftar"}, status=400)
        ws = Workstation.objects.create(
            workstation_id=workstation_id, description=description, is_active=True
        )
        return Response({
            "status": "success",
            "message": f"Workstation {ws.workstation_id} berhasil dibuat",
            "workstation_id": ws.workstation_id
        }, status=201)
