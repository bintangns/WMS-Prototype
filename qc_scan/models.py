from django.db import models
from django.conf import settings
from django.db.models import Q

class HandlingUnit(models.Model):
    STATUS_CHOICES = [
        ("ready_for_packing", "Ready for Packing"),
        ("in_progress", "In Progress"),
        ("verified", "Verified"),
        ("done", "Done"),
        ("exception", "Exception"),
    ]
    hu_code = models.CharField(max_length=64, unique=True)
    client = models.ForeignKey("core.Client", on_delete=models.PROTECT, related_name="handling_units")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ready_for_packing")

    assigned_packer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="hus_assigned"
    )
    # ⬇️ FIX: gunakan app label yang benar untuk Workstation
    assigned_workstation = models.ForeignKey(
        "custom_auth.Workstation",  # <— ganti dari "auth.Workstation"
        on_delete=models.SET_NULL, null=True, blank=True, related_name="hus_assigned"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def all_items_verified(self) -> bool:
        return not self.items.filter(verified=False).exists()

    def __str__(self):
        return f"{self.hu_code} ({self.client})"


class HandlingUnitItem(models.Model):
    hu = models.ForeignKey("qc_scan.HandlingUnit", on_delete=models.CASCADE, null=True, blank=True, related_name="items")
    line_no = models.PositiveIntegerField(null=True, blank=True)

    sku = models.CharField(max_length=64)
    name = models.CharField(max_length=200)
    barcode = models.CharField(max_length=128, blank=True, default="")
    qty = models.PositiveIntegerField(default=1)

    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="verified_items")
    verified_at = models.DateTimeField(null=True, blank=True)

    category = models.CharField(max_length=30, blank=True, null=True)  # 'Fragile','Liquid',dst.
    length_cm = models.FloatField(blank=True, null=True)
    width_cm = models.FloatField(blank=True, null=True)
    height_cm = models.FloatField(blank=True, null=True)
    weight_g = models.FloatField(blank=True, null=True)

    @property
    def volume_cm3(self):
        if self.length_cm and self.width_cm and self.height_cm:
            return self.length_cm * self.width_cm * self.height_cm
        return None

    class Meta:
        ordering = ["hu_id", "line_no", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["hu", "line_no"],
                condition=Q(hu__isnull=False) & Q(line_no__isnull=False),
                name="uq_qc_item_hu_line",
            ),
        ]
        indexes = [
            models.Index(fields=["sku"], name="idx_qc_item_sku"),
            models.Index(fields=["barcode"], name="idx_qc_item_barcode"),
        ]

    def __str__(self):
        return f"[{self.hu.hu_code if self.hu_id else 'UNASSIGNED'}] #{self.line_no or '-'} {self.sku} x{self.qty}"
