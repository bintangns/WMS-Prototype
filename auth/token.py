from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User

class WmsTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token: RefreshToken = super().get_token(user)
        # tambah klaim sesuai kebutuhan sidecar/WMS (FR-01, multi-tenant)
        token["uid"] = user.id
        token["username"] = user.username
        token["roles"] = list(user.roles.values_list("name", flat=True))
        token["client_scope"] = list(user.client_scope.values_list("id", flat=True))
        if user.last_workstation_code:
            token["workstation"] = user.last_workstation_code
        return token

class WmsTokenObtainPairView:
    # helper untuk as_view di urls
    serializer_class = WmsTokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        return token
