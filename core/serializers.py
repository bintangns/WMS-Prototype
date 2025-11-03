from rest_framework import serializers
from .models import Client

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ("id", "name", "code")

    def validate(self, attrs):
        if "code" in attrs and attrs["code"]:
            attrs["code"] = attrs["code"].strip().upper()
        if "name" in attrs and attrs["name"]:
            attrs["name"] = attrs["name"].strip()
        return attrs

    def create(self, validated_data):
        code = validated_data["code"]
        name = validated_data["name"]
        if Client.objects.filter(code__iexact=code).exists():
            raise serializers.ValidationError({"code": "Kode client sudah terdaftar"})
        if Client.objects.filter(name__iexact=name).exists():
            raise serializers.ValidationError({"name": "Nama client sudah terdaftar"})
        return super().create(validated_data)
