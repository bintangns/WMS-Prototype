from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Workstation
from rest_framework.test import APIClient

User = get_user_model()

class WorkstationLoginTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='PCK001', password='12345')
        self.workstation = Workstation.objects.create(workstation_id='WS01')
        self.client = APIClient()

    def test_workstation_login(self):
        response = self.client.post('/auth/workstation-login/', {
            "picker_id": "PCK001",
            "workstation_id": "WS01"
        }, format='json')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
