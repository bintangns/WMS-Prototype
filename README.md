📦 AKPSI WMS – Admin & QC API Documentation

Updated: November 2025

Prototype Warehouse Management System (WMS) built with Django REST Framework, integrated with Machine Learning Box Recommendation and Go Lite IoT Bridge.

🔐 Authentication

Semua endpoint (kecuali /auth/token/ dan /auth/register/) membutuhkan Bearer JWT Token di header:

Authorization: Bearer <access_token>

1️⃣ Obtain JWT Token (Admin)

POST /auth/token/

Request

{
  "username": "admin",
  "password": "adminpass"
}


Response

{
  "refresh": "<refresh_token>",
  "access": "<access_token>"
}

🧍‍♂️ Auth Management
Register Workstation

POST /auth/register-workstation/

{
  "workstation_id": "WS01",
  "description": "Packing Station 01"
}

Register Packer User

POST /auth/register/

{
  "username": "packer01",
  "password": "12345",
  "email": "packer01@example.com"
}

Workstation Login (Packer)

POST /auth/workstation-login/

{
  "username": "packer01",
  "password": "12345",
  "workstation_id": "WS01"
}

🧾 Core – Client Management
Create Client

POST /core/clients/

{
  "name": "Client Alpha",
  "code": "CLA"
}


Response

{
  "id": 1,
  "name": "Client Alpha",
  "code": "CLA"
}

🧱 QC Admin – Handling Unit & Item Pool
Create Empty HU

POST /api/qc/admin/hu-empty/

{
  "hu_code": "HU-CLA-0001",
  "client_id": 1
}

Create Item Pool (Unassigned)

POST /api/qc/admin/item-pool/create/

{
  "sku": "CLA-001",
  "name": "Gelas 250ml",
  "qty": 2,
  "barcode": "899000001",
  "category": "Fragile",
  "length_cm": 10,
  "width_cm": 8,
  "height_cm": 8,
  "weight_g": 300
}

List Item Pool

GET /api/qc/admin/item-pool/list/

Assign Items to HU

POST /api/qc/admin/assign-items/

{
  "hu_code": "HU-CLA-0001",
  "skus": ["CLA-001", "CLA-002"],
  "auto_line": true
}

⚙️ QC – Packer Operations
Scan HU (Assign to Session)

POST /api/qc/scan-hu/

{
  "handling_unit_code": "HU-CLA-0001",
  "username": "packer01",
  "workstation_id": "WS01"
}

Verify Item (By Barcode)

POST /api/qc/verify-item/

{
  "hu_code": "HU-CLA-0001",
  "barcode": "899000001",
  "username": "packer01",
  "workstation_id": "WS01"
}

Get HU Detail

GET /api/qc/hu/HU-CLA-0001/

Response

{
  "id": 2,
  "hu_code": "HU-CLA-0001",
  "client": 1,
  "status": "ready_for_packing",
  "items": [
    {
      "line_no": 1,
      "sku": "CLA-001",
      "category": "Fragile",
      "length_cm": 10,
      "width_cm": 8,
      "height_cm": 8,
      "weight_g": 300,
      "verified": false
    }
  ]
}

🤖 Machine Learning – Box Recommendation
Recommend Box (ML Prediction)

POST /api/qc/recommend-box/

Request

{
  "hu_code": "HU-GDN-0001"
}


Response

{
  "client_name": "BLIBLI",
  "container_code": "010",
  "need_bubble_wrap": false,
  "bubble_wrap_items": []
}
