from django.db import transaction, models
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.response import Response
from django.utils import timezone
import pandas as pd
from .ml_service import recommend_box_with_wrap

from core.models import Client
from auth.models import WorkstationSession, Workstation, User
from .models import HandlingUnit, HandlingUnitItem

from activitylog.utils import log_activity

from .serializers import (
    HUAssignSerializer, HUDetailSerializer, VerifyItemSerializer,
    HUEmptyCreateSerializer, ItemPoolCreateSerializer, ItemPoolListSerializer,
    AssignItemsSerializer, UnassignItemsSerializer
)

# ============== ADMIN: buat HU kosong ==============
class HUCreateEmptyView(APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request):
        s = HUEmptyCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        hu_code = s.validated_data["hu_code"]
        client_id = s.validated_data["client_id"]

        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return Response({"client_id": "Client tidak ditemukan"}, status=404)

        hu, created = HandlingUnit.objects.get_or_create(
            hu_code=hu_code,
            defaults={"client": client}
        )
        if not created:
            # update client saja jika HU sudah ada
            if hu.client_id != client.id:
                hu.client = client
                hu.save(update_fields=["client"])

        return Response({
            "status": "success",
            "message": f"HU {hu.hu_code} siap (kosong).",
            "hu": HUDetailSerializer(hu).data
        }, status=201 if created else 200)

# ============== ADMIN: item pool (belum assign HU) ==============
class ItemPoolCreateView(APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request):
        s = ItemPoolCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        item = HandlingUnitItem.objects.create(
            hu=None,
            line_no=None,
            sku=s.validated_data["sku"],
            name=s.validated_data["name"],
            qty=s.validated_data["qty"],
            barcode=s.validated_data.get("barcode", ""),
            category=s.validated_data.get("category"),
            length_cm=s.validated_data.get("length_cm"),
            width_cm=s.validated_data.get("width_cm"),
            height_cm=s.validated_data.get("height_cm"),
            weight_g=s.validated_data.get("weight_g"),
        )
        return Response({
            "status": "success",
            "message": "Item pool dibuat (belum ter-assign HU).",
            "item": ItemPoolListSerializer(item).data
        }, status=201)

class ItemPoolListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        qs = HandlingUnitItem.objects.filter(hu__isnull=True).order_by("id")
        return Response(ItemPoolListSerializer(qs, many=True).data, status=200)

# ============== ADMIN: assign HU + items (langsung, mode A) ==============
class HUAssignView(APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request):
        s = HUAssignSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        hu_code = s.validated_data["hu_code"]
        client_id = s.validated_data["client_id"]
        items = s.validated_data["items"]

        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return Response({"client_id": "Client tidak ditemukan"}, status=404)

        hu, created = HandlingUnit.objects.get_or_create(hu_code=hu_code, defaults={"client": client})
        if not created:
            # reset items jika HU sudah ada
            hu.items.all().delete()
            hu.client = client
            hu.status = "ready_for_packing"
            hu.assigned_packer = None
            hu.assigned_workstation = None
            hu.save()

        HandlingUnitItem.objects.bulk_create([
            HandlingUnitItem(
                hu=hu,
                line_no=it["line_no"],
                sku=it["sku"],
                name=it["name"],
                qty=it["qty"],
                barcode=it.get("barcode", ""),
                category=it.get("category"),
                length_cm=it.get("length_cm"),
                width_cm=it.get("width_cm"),
                height_cm=it.get("height_cm"),
                weight_g=it.get("weight_g"),
            )
            for it in items
        ])

        return Response({
            "status": "success",
            "message": f"HU {hu.hu_code} dibuat/diperbarui dengan {len(items)} item.",
            "hu": HUDetailSerializer(hu).data
        }, status=201)

# ============== ADMIN: assign item pool -> HU (mode B) ==============
class AssignItemsToHUView(APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request):
        s = AssignItemsSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        hu_code = s.validated_data["hu_code"]
        skus = [sku.strip() for sku in s.validated_data["skus"] if sku and sku.strip()]
        auto_line = s.validated_data["auto_line"]

        if not skus:
            return Response({"skus": "Minimal 1 SKU harus dikirim."}, status=400)

        try:
            hu = HandlingUnit.objects.select_for_update().get(hu_code=hu_code)
        except HandlingUnit.DoesNotExist:
            return Response({"hu_code": "HU tidak ditemukan"}, status=404)

        # Ambil SEMUA item pool (hu is null) yang SKU-nya ada dalam daftar
        items_qs = (HandlingUnitItem.objects
                    .select_for_update()
                    .filter(hu__isnull=True, sku__in=skus)
                    .order_by("sku", "id"))
        items = list(items_qs)

        found_skus = {it.sku for it in items}
        missing = sorted(set(skus) - found_skus)
        if missing:
            return Response({
                "error": "Sebagian SKU tidak ditemukan di item pool (belum ter-assign HU).",
                "missing_skus": missing
            }, status=404)

        if not items:
            return Response({"error": "Tidak ada item pool yang cocok dengan SKU yang dikirim."}, status=404)

        # Tentukan line_no awal (lanjut dari max line_no yang ada)
        from django.db import models as dj_models
        max_line = hu.items.aggregate(m=dj_models.Max("line_no"))["m"] or 0
        next_line = max_line + 1

        for it in items:
            it.hu = hu
            if auto_line:
                it.line_no = next_line
                next_line += 1
            it.verified = False
            it.verified_by = None
            it.verified_at = None

        HandlingUnitItem.objects.bulk_update(items, ["hu", "line_no", "verified", "verified_by", "verified_at"])

        return Response({
            "status": "success",
            "message": f"{len(items)} item di-assign ke HU {hu.hu_code} berdasarkan SKU.",
            "assigned_skus": sorted(found_skus),
            "hu": HUDetailSerializer(hu).data
        }, status=200)

# ============== ADMIN: unassign item dari HU ==============
class UnassignItemsFromHUView(APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request):
        s = UnassignItemsSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        item_ids = s.validated_data["item_ids"]

        items = list(HandlingUnitItem.objects.select_for_update().filter(id__in=item_ids))
        if not items:
            return Response({"item_ids": "Tidak ada item ditemukan"}, status=404)

        for it in items:
            it.hu = None
            it.line_no = None
            it.verified = False
            it.verified_by = None
            it.verified_at = None

        HandlingUnitItem.objects.bulk_update(items, ["hu", "line_no", "verified", "verified_by", "verified_at"])

        return Response({
            "status": "success",
            "message": f"{len(items)} item di-unassign (kembali ke pool)."
        }, status=200)

# ============== PACKER: scan HU (assign ke session + tampilkan item) ==============
class HandlingUnitScanView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        hu_code = (request.data.get("handling_unit_code") or "").strip()
        ws_id   = (request.data.get("workstation_id") or "").strip()
        user    = request.user  # ✅ pakai user dari JWT

        if not hu_code:
            return Response({"handling_unit_code": "Harus diisi"}, status=400)

        # validasi WS jika dikirim
        ws = None
        if ws_id:
            try:
                ws = Workstation.objects.get(workstation_id=ws_id, is_active=True)
            except Workstation.DoesNotExist:
                return Response({"workstation_id": "Workstation tidak ditemukan / nonaktif"}, status=404)

        # cari sesi aktif user
        qs = WorkstationSession.objects.filter(picker=user, is_active=True).order_by("-login_time")
        if ws:
            session = qs.filter(workstation=ws).first()
        else:
            session = qs.first()

        if not session:
            msg = f"Tidak ada sesi aktif untuk user '{user.username}'"
            if ws_id:
                msg += f" di workstation '{ws_id}'"
            msg += ". Lakukan workstation-login dulu."
            return Response({"error": msg}, status=400)

        # kalau ws belum di-body, gunakan dari sesi
        if not ws:
            ws = session.workstation

        # ambil HU
        try:
            hu = HandlingUnit.objects.select_for_update().get(hu_code=hu_code)
        except HandlingUnit.DoesNotExist:
            return Response({"handling_unit_code": "HU tidak ditemukan, hubungi admin"}, status=404)

        # assign HU ke konteks sesi (packer + ws)
        hu.assigned_packer = user
        hu.assigned_workstation = ws
        if hu.status == "ready_for_packing":
            hu.status = "in_progress"
        hu.save(update_fields=["assigned_packer", "assigned_workstation", "status"])

        # update context sesi
        session.current_hu_code = hu.hu_code
        session.current_client_code = getattr(hu.client, "code", "")
        session.current_items = []  # jangan simpan payload besar
        session.last_activity = timezone.now() if hasattr(session, "last_activity") else session.login_time
        session.save(update_fields=["current_hu_code", "current_client_code", "current_items"])

        return Response({
            "status": "success",
            "message": "HU di-assign & item ditampilkan",
            "workstation_used": ws.workstation_id,
            "hu": HUDetailSerializer(hu).data
        }, status=200)

# ============== PACKER: verify 1 item (scan barcode/sku) ==============
class VerifyItemView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        s = VerifyItemSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        hu_code = s.validated_data["hu_code"]
        line_no = s.validated_data.get("line_no")
        sku = (s.validated_data.get("sku") or "").strip()
        barcode = (s.validated_data.get("barcode") or "").strip()

        username = (request.data.get("username") or "").strip()
        workstation_id = (request.data.get("workstation_id") or "").strip()
        if not username or not workstation_id:
            return Response({"error": "username dan workstation_id wajib dikirim"}, status=400)

        # validasi user & ws + sesi aktif
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"username": "User tidak ditemukan"}, status=404)

        try:
            ws = Workstation.objects.get(workstation_id=workstation_id, is_active=True)
        except Workstation.DoesNotExist:
            return Response({"workstation_id": "Workstation tidak ditemukan / nonaktif"}, status=404)

        session = WorkstationSession.objects.filter(
            picker=user, workstation=ws, is_active=True
        ).order_by("-login_time").first()
        if not session:
            return Response({"error": f"Tidak ada sesi aktif untuk user '{username}' di workstation '{workstation_id}'"}, status=400)

        # ambil HU
        try:
            hu = HandlingUnit.objects.get(hu_code=hu_code)
        except HandlingUnit.DoesNotExist:
            return Response({"hu_code": "HU tidak ditemukan"}, status=404)

        # cari item
        qs = hu.items.all()
        if line_no is not None:
            qs = qs.filter(line_no=line_no)
        if sku:
            qs = qs.filter(sku=sku)
        if barcode:
            qs = qs.filter(barcode=barcode)
        item = qs.first()

        if not item:
            return Response({"error": "Item tidak ditemukan pada HU (periksa line_no/sku/barcode)."}, status=404)

        for fld in ["category", "length_cm", "width_cm", "height_cm", "weight_g"]:
            if fld in s.validated_data and s.validated_data.get(fld) is not None:
                setattr(item, fld, s.validated_data[fld])

        if item.verified:
            return Response({"message": "Item sudah terverifikasi."}, status=200)

        # verifikasi
        item.verified = True
        item.verified_by = user
        item.verified_at = timezone.now()
        item.save(update_fields=["verified", "verified_by", "verified_at"])

        # jika semua verified → update HU
        if hu.all_items_verified():
            hu.status = "verified"
            hu.save(update_fields=["status"])

        log_activity(
            request,
            action="verify_item",
            user=user,
            workstation=ws,
            extra={
                "hu_code": hu.hu_code,
                "item_id": item.id,
                "line_no": item.line_no,
                "sku": item.sku,
                "barcode": item.barcode,
                "hu_status": hu.status,
            },
            status_code=200,
        )

        return Response({
            "status": "success",
            "message": "Item diverifikasi",
            "hu_code": hu.hu_code,
            "item": {
                "id": item.id,
                "line_no": item.line_no,
                "sku": item.sku,
                "name": item.name,
                "qty": item.qty,
                "barcode": item.barcode,
                "verified": item.verified,
                "verified_at": item.verified_at,
            },
            "hu_status": hu.status,
            "all_verified": (hu.status == "verified")
        }, status=200)

class HUDetailByCodeView(APIView):
    """
    GET /api/qc/hu/<hu_code>/
    Lihat detail HU + daftar item.
    Akses: user login (packer/supervisor/admin) — IsAuthenticated
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, hu_code: str):
        hu_code = (hu_code or "").strip()
        if not hu_code:
            return Response({"hu_code": "Wajib diisi."}, status=400)
        try:
            hu = HandlingUnit.objects.get(hu_code=hu_code)
        except HandlingUnit.DoesNotExist:
            return Response({"detail": "Handling Unit tidak ditemukan."}, status=404)
        return Response(HUDetailSerializer(hu).data, status=200)

class RecommendBoxView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        hu_code = (request.data.get("hu_code") or "").strip()
        if not hu_code:
            return Response({"hu_code": "Wajib diisi."}, status=400)

        try:
            hu = HandlingUnit.objects.select_related("client").get(hu_code=hu_code)
        except HandlingUnit.DoesNotExist:
            return Response({"detail": "Handling Unit tidak ditemukan."}, status=404)

        items = list(HandlingUnitItem.objects.filter(hu=hu).values(
            "id","category","length_cm","width_cm","height_cm","weight_g"
        ))
        if not items:
            return Response({"detail": "HU belum punya item."}, status=400)

        # validasi minimal fitur
        for it in items:
            if not all([it["length_cm"], it["width_cm"], it["height_cm"]]):
                return Response({"detail": "Beberapa item belum memiliki dimensi untuk rekomendasi."}, status=400)

        # bentuk dataframe fitur untuk model
        rows = []
        for it in items:
            L,W,H = it["length_cm"], it["width_cm"], it["height_cm"]
            rows.append({
                "item_id": it["id"],
                "client_name": hu.client.name,
                "category": it["category"] or "Neutral",
                "distance_km": getattr(hu, "distance_km", 25.0),
                "item_length_cm": L,
                "item_width_cm": W,
                "item_height_cm": H,
                "item_weight_g": it["weight_g"] or 0.0,
                "item_volume_cm3": L*W*H,
            })
        df = pd.DataFrame(rows)

        out = recommend_box_with_wrap(df)

        log_activity(
            request,
            action="recommend_box",
            user=request.user if request.user.is_authenticated else None,
            workstation=None,
            extra={
                "hu_code": hu.hu_code,
                "client": hu.client.code if hu.client else None,
                "item_count": len(items),
            },
            status_code=200,
        )

        return Response({
            "client_name": hu.client.name,
            **out
        }, status=200)