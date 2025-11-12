# 📦 AKPSI WMS – Admin & QC API Documentation
_Updated: November 2025_

Prototype Warehouse Management System (WMS) built with **Django REST Framework**, integrated with **Machine Learning Box Recommendation** and **Go Lite IoT Bridge**.

---

## 🔐 Authentication
Semua endpoint (kecuali `/auth/token/` dan `/auth/register/`) membutuhkan **Bearer JWT Token** di header:

```
Authorization: Bearer <access_token>
```

### 1️⃣ Obtain JWT Token (Admin)
`POST /auth/token/`

**Request**
```json
{
  "username": "admin",
  "password": "adminpass"
}
```

**Response**
```json
{
  "refresh": "<refresh_token>",
  "access": "<access_token>"
}
```

---

## 🧍‍♂️ Auth Management

### Register Workstation
`POST /auth/register-workstation/`
```json
{
  "workstation_id": "WS01",
  "description": "Packing Station 01"
}
```

### Register Packer User
`POST /auth/register/`
```json
{
  "username": "packer01",
  "password": "12345",
  "email": "packer01@example.com"
}
```

### Workstation Login (Packer)
`POST /auth/workstation-login/`
```json
{
  "username": "packer01",
  "password": "12345",
  "workstation_id": "WS01"
}
```

---

## 🧾 Core – Client Management

### Create Client
`POST /core/clients/`
```json
{
  "name": "Client Alpha",
  "code": "CLA"
}
```

**Response**
```json
{
  "id": 1,
  "name": "Client Alpha",
  "code": "CLA"
}
```

---

## 🧱 QC Admin – Handling Unit & Item Pool

### Create Empty HU
`POST /api/qc/admin/hu-empty/`
```json
{
  "hu_code": "HU-CLA-0001",
  "client_id": 1
}
```

### Create Item Pool (Unassigned)
`POST /api/qc/admin/item-pool/create/`
```json
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
```

### List Item Pool
`GET /api/qc/admin/item-pool/list/`

### Assign Items to HU
`POST /api/qc/admin/assign-items/`
```json
{
  "hu_code": "HU-CLA-0001",
  "skus": ["CLA-001", "CLA-002"],
  "auto_line": true
}
```

---

## ⚙️ QC – Packer Operations

### Scan HU (Assign to Session)
`POST /api/qc/scan-hu/`
```json
{
  "handling_unit_code": "HU-CLA-0001",
  "username": "packer01",
  "workstation_id": "WS01"
}
```

### Verify Item (By Barcode)
`POST /api/qc/verify-item/`
```json
{
  "hu_code": "HU-CLA-0001",
  "barcode": "899000001",
  "username": "packer01",
  "workstation_id": "WS01"
}
```

### Get HU Detail
`GET /api/qc/hu/HU-CLA-0001/`

**Response**
```json
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
```

---

## 🤖 Machine Learning – Box Recommendation

### Recommend Box (ML Prediction)
`POST /api/qc/recommend-box/`

**Request**
```json
{
  "hu_code": "HU-GDN-0001"
}
```

**Response**
```json
{
  "client_name": "BLIBLI",
  "container_code": "010",
  "need_bubble_wrap": false,
  "bubble_wrap_items": []
}
```

---

## 🌐 Go Lite IoT Integration

### Automatic Push (Triggered after ML prediction)
Every successful `/api/qc/recommend-box/` call triggers:

#### 1️⃣ MQTT Publish
**Broker:** `mqtt.goliteiot.com:1883`  
**Topic Pattern:** `wms/{client}/{hu}/reco`  

**Payload Example**
```json
{
  "event": "box_recommendation",
  "ts": 1731438000,
  "hu_code": "HU-GDN-0001",
  "client_name": "BLIBLI",
  "container_code": "010",
  "need_bubble_wrap": false,
  "bubble_wrap_items": [],
  "items_count": 4
}
```

## 🧩 Directory Structure (simplified)
```
AKPSI_Warehouse/
├── qc_scan/
│   ├── views.py
│   ├── ml_service.py          # ML inference logic
│   ├── golite_bridge.py       # MQTT + HTTPS bridge
│   └── serializers.py
├── AKPSI_Warehouse/settings.py
└── ml_artifacts/
    ├── rf_container_code.joblib
    ├── expected_features.json
    └── catalog.json
```

---

## 🧭 Postman Collection
Full collection included in repository:
```
AKPSI WMS API.json
```
Import to Postman to test all endpoints sequentially.
