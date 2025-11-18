# auth/serializers.py

from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Role, Workstation, WorkstationSession

User = get_user_model()

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ("id", "name", "description")

class UserMeSerializer(serializers.ModelSerializer):
    roles = RoleSerializer(many=True, read_only=True)
    client_scope = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id","username","email","first_name","last_name","roles","client_scope","last_workstation_code")

    def get_client_scope(self, obj):
        return list(obj.client_scope.values_list("id", flat=True))

# =========================
# REGISTER PACKER ONLY
# =========================
class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=False, allow_blank=True)

    def validate_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value

    def create(self, validated_data):
        username = validated_data["username"]
        password = validated_data["password"]
        email = validated_data.get("email", "")

        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({"username": "Username sudah digunakan"})

        user = User(username=username, email=email)
        user.set_password(password)
        user.save()

        packer_role, _ = Role.objects.get_or_create(name="PACKER")
        user.roles.set([packer_role.id])
        return user

# =========================
# WORKSTATION LOGIN
# - kompatibel dengan test: pakai picker_id + workstation_id
# - password opsional (kalau dikirim, kita autentikasi)
# =========================
class WorkstationLoginSerializer(serializers.Serializer):
    picker_id = serializers.CharField(required=False)   # alias ke username
    username = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    workstation_id = serializers.CharField()

    # NOTE: field output (access/refresh/session_id/message) DIBUAT di VIEW, bukan di serializer
    # -> jadi dihapus dari serializer fields agar tidak misleading

    def validate(self, data):
        # username boleh dari picker_id atau username
        username = data.get("username") or data.get("picker_id")
        if not username:
            raise serializers.ValidationError({"picker_id": "picker_id atau username wajib diisi."})

        password = data.get("password")
        ws_id = data.get("workstation_id")
        if not ws_id:
            raise serializers.ValidationError({"workstation_id": "Wajib diisi."})

        # auth: password opsional (untuk prototyping)
        if password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError({"detail": "Username atau password salah."})
        else:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise serializers.ValidationError({"picker_id": "User tidak ditemukan."})

        # role check harus PACKER
        if not user.roles.filter(name__iexact="PACKER").exists():
            raise serializers.ValidationError({"detail": "Hanya PACKER yang dapat login di endpoint ini."})

        # validasi workstation aktif
        try:
            workstation = Workstation.objects.get(workstation_id=ws_id, is_active=True)
        except Workstation.DoesNotExist:
            raise serializers.ValidationError({"workstation_id": "Workstation ID tidak ditemukan / nonaktif."})

        # JANGAN bikin session & token di serializer — cukup kembalikan objek valid
        data["user"] = user
        data["workstation"] = workstation
        return data

class PackerLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError("Username atau password salah.")

        if not user.is_active:
            raise serializers.ValidationError("Akun tidak aktif.")

        # Opsional: pastikan dia punya role PACKER
        # if not user.roles.filter(name="PACKER").exists():
        #     raise serializers.ValidationError("User ini bukan Packer.")

        attrs["user"] = user
        return attrs

    def create(self, validated_data):
        user = validated_data["user"]
        refresh = RefreshToken.for_user(user)

        # Kalau di proyek lama kamu ada roles:
        try:
            refresh["roles"] = list(user.roles.values_list("name", flat=True))
        except Exception:
            refresh["roles"] = []

        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": getattr(user, "full_name", user.username),
            },
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }

class WorkstationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workstation
        fields = [
            "id",
            "workstation_id",
            "area",
            "description",
            "is_active",
            # kalau mau tampilkan waktu dibuat juga:
            # "created_at",
        ]

class AssignWorkstationSerializer(serializers.Serializer):
    workstation_id = serializers.CharField()
    # Optional: kalau mau pakai username/packer id eksplisit
    packer_username = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        ws_id = attrs.get("workstation_id")
        try:
            workstation = Workstation.objects.get(workstation_id=ws_id)
        except Workstation.DoesNotExist:
            raise serializers.ValidationError(
                {"workstation_id": "Workstation tidak ditemukan."}
            )

        attrs["workstation"] = workstation
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user

        # Kalau mau pakai packer_username eksplisit:
        packer_username = validated_data.get("packer_username")
        if packer_username:
            try:
                user = User.objects.get(username=packer_username)
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    {"packer_username": "Packer / username tidak ditemukan."}
                )

        workstation = validated_data["workstation"]

        # Tutup semua sesi aktif packer ini dulu (opsional tapi rapi)
        WorkstationSession.objects.filter(
            picker=user, is_active=True
        ).update(is_active=False)

        session = WorkstationSession.objects.create(
            picker=user,
            workstation=workstation,
            is_active=True,
        )

        return {
            "session_id": session.id,
            "workstation_id": workstation.workstation_id,
            "packer_username": user.username,
        }
