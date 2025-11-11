from django.urls import path
from .views import (
    # ADMIN
    HUCreateEmptyView, ItemPoolCreateView, ItemPoolListView,
    HUAssignView, AssignItemsToHUView, UnassignItemsFromHUView,
    # PACKER
    HandlingUnitScanView, VerifyItemView,
    HUDetailByCodeView, RecommendBoxView
)

urlpatterns = [
    # ===== ADMIN =====
    path("admin/hu-empty/", HUCreateEmptyView.as_view(), name="hu_create_empty"),
    path("admin/item-pool/create/", ItemPoolCreateView.as_view(), name="item_pool_create"),
    path("admin/item-pool/list/", ItemPoolListView.as_view(), name="item_pool_list"),
    path("admin/hu-assign/", HUAssignView.as_view(), name="hu_assign"),  # create HU + items langsung
    path("admin/assign-items/", AssignItemsToHUView.as_view(), name="assign_items_to_hu"),
    path("admin/unassign-items/", UnassignItemsFromHUView.as_view(), name="unassign_items_from_hu"),

    # ===== PACKER =====
    path("scan-hu/", HandlingUnitScanView.as_view(), name="scan_hu"),
    path("verify-item/", VerifyItemView.as_view(), name="verify_item"),

    # ===== COMMON =====
    path("hu/<str:hu_code>/", HUDetailByCodeView.as_view(), name="hu_detail_by_code"),

    path("recommend-box/", RecommendBoxView.as_view(), name="qc_recommend_box"),
]
