from rest_framework import serializers
from .models import HandlingUnit, HandlingUnitItem

# ====== INPUT ITEM (admin assign langsung HU) ======
class HUItemInSerializer(serializers.Serializer):
    line_no = serializers.IntegerField(min_value=1)
    sku = serializers.CharField()
    name = serializers.CharField()
    qty = serializers.IntegerField(min_value=1)
    barcode = serializers.CharField(required=False, allow_blank=True, default="")

    category = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    length_cm = serializers.FloatField(required=False, allow_null=True)
    width_cm = serializers.FloatField(required=False, allow_null=True)
    height_cm = serializers.FloatField(required=False, allow_null=True)
    weight_g = serializers.FloatField(required=False, allow_null=True)

# ====== ADMIN: assign HU + items langsung ======
class HUAssignSerializer(serializers.Serializer):
    hu_code = serializers.CharField()
    client_id = serializers.IntegerField()
    items = HUItemInSerializer(many=True)

# ====== OUTPUT HU detail ======
class HUItemOutSerializer(serializers.ModelSerializer):
    volume_cm3 = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = HandlingUnitItem
        fields = (
            "id", "line_no", "sku", "name", "qty", "barcode",
            "verified", "verified_by", "verified_at",
            "category", "length_cm", "width_cm", "height_cm", "weight_g",
            "volume_cm3",
        )

    def get_volume_cm3(self, obj):
        v = getattr(obj, "volume_cm3", None)
        return float(v) if v is not None else None


class HUDetailSerializer(serializers.ModelSerializer):
    items = HUItemOutSerializer(many=True, read_only=True)

    # kirim ID dan nama client sekaligus
    client_id = serializers.IntegerField(source="client.id", read_only=True)
    client_name = serializers.CharField(source="client.name", read_only=True)

    class Meta:
        model = HandlingUnit
        fields = (
            "id",
            "hu_code",
            "client_id",          # integer id
            "client_name",        # nama client (string)
            "status",
            "assigned_packer",
            "assigned_workstation",
            "items",
        )

# ====== PACKER: verify item ======
class VerifyItemSerializer(serializers.Serializer):
    hu_code = serializers.CharField()
    line_no = serializers.IntegerField(required=False)
    sku = serializers.CharField(required=False, allow_blank=True)
    barcode = serializers.CharField(required=False, allow_blank=True)
    qty_verified = serializers.IntegerField(required=False, min_value=1)

    category  = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    length_cm = serializers.FloatField(required=False, allow_null=True)
    width_cm  = serializers.FloatField(required=False, allow_null=True)
    height_cm = serializers.FloatField(required=False, allow_null=True)
    weight_g  = serializers.FloatField(required=False, allow_null=True)

# ====== ADMIN: HU kosong ======
class HUEmptyCreateSerializer(serializers.Serializer):
    hu_code = serializers.CharField()
    client_id = serializers.IntegerField()

# ====== ADMIN: item pool (unassigned) ======
class ItemPoolCreateSerializer(serializers.Serializer):
    sku = serializers.CharField()
    name = serializers.CharField()
    qty = serializers.IntegerField(min_value=1)
    barcode = serializers.CharField(required=False, allow_blank=True, default="")

    category = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    length_cm = serializers.FloatField(required=False, allow_null=True)
    width_cm = serializers.FloatField(required=False, allow_null=True)
    height_cm = serializers.FloatField(required=False, allow_null=True)
    weight_g = serializers.FloatField(required=False, allow_null=True)

class ItemPoolListSerializer(serializers.ModelSerializer):
    class Meta:
        model = HandlingUnitItem
        fields = (
            "id",
            "hu",
            "line_no",
            "sku",
            "name",
            "qty",
            "barcode",
            "verified",
            "category",
            "length_cm",
            "width_cm",
            "height_cm",
            "weight_g",
        )

# ====== ADMIN: assign/unassign pool -> HU ======
class AssignItemsSerializer(serializers.Serializer):
    hu_code = serializers.CharField()
    skus = serializers.ListField(
        child=serializers.CharField(allow_blank=False),
        allow_empty=False
    )
    auto_line = serializers.BooleanField(required=False, default=True)

class UnassignItemsSerializer(serializers.Serializer):
    item_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False
    )
