# qc_scan/tests.py

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from unittest.mock import patch

from core.models import Client
from qc_scan.models import HandlingUnit, HandlingUnitItem

User = get_user_model()


class BaseWmsTestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.client_api = APIClient()

        #Test Login User
        self.client_obj = Client.objects.create(name="BLIBLI", code="GDN")
        self.user = User.objects.create_user(
            username="packer01",
            password="secret123"
        )
        self.client_api.force_authenticate(user=self.user)


class AdminHUViewsTests(BaseWmsTestCase):
    """
    Test flow admin:
    - create HU kosong
    - create item pool & list
    - assign item pool -> HU
    - unassign item dari HU
    """
    #Test Create Handling Unit
    def test_create_empty_hu(self):
        url = "/api/qc/admin/hu-empty/"
        payload = {
            "hu_code": "HU-GDN-0001",
            "client_id": self.client_obj.id,
        }

        resp = self.client_api.post(url, payload, format="json")
        self.assertEqual(resp.status_code, 201)

        self.assertEqual(HandlingUnit.objects.count(), 1)
        hu = HandlingUnit.objects.get()
        self.assertEqual(hu.hu_code, "HU-GDN-0001")
        self.assertEqual(hu.client, self.client_obj)

    #Test Create Item
    def test_item_pool_create_and_list(self):
        # create item pool
        create_url = "/api/qc/admin/item-pool/create/"
        payload = {
            "sku": "SKU-GLASS-001",
            "name": "Gelas Kaca 250ml",
            "qty": 2,
            "barcode": "GLASS001",
            "category": "Fragile",
            "length_cm": 10,
            "width_cm": 8,
            "height_cm": 8,
            "weight_g": 300,
        }
        resp_create = self.client_api.post(create_url, payload, format="json")
        self.assertEqual(resp_create.status_code, 201)
        self.assertEqual(HandlingUnitItem.objects.count(), 1)

        # list item pool
        list_url = "/api/qc/admin/item-pool/list/"
        resp_list = self.client_api.get(list_url)
        self.assertEqual(resp_list.status_code, 200)

        data = resp_list.json()
        self.assertEqual(len(data), 1)
        self.assertIsNone(data[0]["hu"])

    #Test Scan item to Handling Unit
    def test_assign_items_from_pool_to_hu_and_unassign(self):

        hu = HandlingUnit.objects.create(
            hu_code="HU-GDN-0002",
            client=self.client_obj
        )

        # 2 item di pool
        item1 = HandlingUnitItem.objects.create(
            hu=None, line_no=None, sku="SKU-A", name="Item A", qty=1
        )
        item2 = HandlingUnitItem.objects.create(
            hu=None, line_no=None, sku="SKU-B", name="Item B", qty=2
        )

        # assign item pool -> HU
        assign_url = "/api/qc/admin/assign-items/"
        payload_assign = {
            "hu_code": hu.hu_code,
            "skus": ["SKU-A", "SKU-B"],
            "auto_line": True,
        }
        resp_assign = self.client_api.post(assign_url, payload_assign, format="json")
        self.assertEqual(resp_assign.status_code, 200)

        # cek item sekarang punya HU & line_no
        item1.refresh_from_db()
        item2.refresh_from_db()
        self.assertEqual(item1.hu, hu)
        self.assertEqual(item2.hu, hu)
        self.assertIsNotNone(item1.line_no)
        self.assertIsNotNone(item2.line_no)

        # unassign lagi ke pool
        unassign_url = "/api/qc/admin/unassign-items/"
        payload_unassign = {"item_ids": [item1.id, item2.id]}
        resp_unassign = self.client_api.post(
            unassign_url, payload_unassign, format="json"
        )
        self.assertEqual(resp_unassign.status_code, 200)

        item1.refresh_from_db()
        item2.refresh_from_db()
        self.assertIsNone(item1.hu)
        self.assertIsNone(item2.hu)
        self.assertIsNone(item1.line_no)
        self.assertIsNone(item2.line_no)

#Machine Learning Test
class HUDetailAndRecommendTests(BaseWmsTestCase):


    def _create_hu_with_items(self):
        hu = HandlingUnit.objects.create(
            hu_code="HU-GDN-0003",
            client=self.client_obj
        )
        # dua item dengan dimensi lengkap
        item1 = HandlingUnitItem.objects.create(
            hu=hu,
            line_no=1,
            sku="SKU-GLASS-001",
            name="Gelas Kaca",
            qty=2,
            barcode="GLASS001",
            category="Fragile",
            length_cm=10,
            width_cm=8,
            height_cm=8,
            weight_g=300,
        )
        item2 = HandlingUnitItem.objects.create(
            hu=hu,
            line_no=2,
            sku="SKU-BLENDER-001",
            name="Blender",
            qty=1,
            barcode="BLEND001",
            category="Electronics",
            length_cm=25,
            width_cm=20,
            height_cm=20,
            weight_g=2500,
        )
        return hu, [item1, item2]

    def test_get_hu_detail(self):
        hu, _ = self._create_hu_with_items()
        url = f"/api/qc/hu/{hu.hu_code}/"

        resp = self.client_api.get(url)
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertEqual(data["hu_code"], hu.hu_code)
        self.assertEqual(len(data["items"]), 2)

    @patch("qc_scan.views.recommend_box_with_wrap")
    def test_recommend_box_view_uses_ml_and_returns_payload(self, mock_reco):
        hu, items = self._create_hu_with_items()

        # stub hasil ML supaya tidak perlu artefak joblib beneran
        mock_reco.return_value = {
            "container_code": "010",
            "need_bubble_wrap": True,
            "bubble_wrap_items": [
                {"item_id": items[0].id, "category": "Fragile"}
            ],
        }

        url = "/api/qc/recommend-box/"
        payload = {"hu_code": hu.hu_code}

        resp = self.client_api.post(url, payload, format="json")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertEqual(data["client_name"], self.client_obj.name)
        self.assertEqual(data["container_code"], "010")
        self.assertTrue(data["need_bubble_wrap"])
        self.assertEqual(len(data["bubble_wrap_items"]), 1)

        self.assertTrue(mock_reco.called)
