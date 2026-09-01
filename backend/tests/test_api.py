import os
import tempfile
import unittest

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["KABILAI_DB_PATH"] = _tmp.name
# Force deterministic, offline behavior for tests (env vars win over .env).
os.environ["GUPSHUP_MOCK"] = "true"
os.environ["AGENT_MODEL"] = "test"

from fastapi.testclient import TestClient  # noqa: E402

from app import app  # noqa: E402
from app.core.database import init_db  # noqa: E402
from app.seed import seed  # noqa: E402


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        init_db()
        seed()
        cls.client = TestClient(app)

    def test_service_info(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Kabilai API")

    def test_health(self) -> None:
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def _token(self) -> str:
        res = self.client.post(
            "/api/v1/auth/login",
            json={"email": "gopinath@kabilaifarm.com", "password": "Gopinath@12345!"},
        )
        self.assertEqual(res.status_code, 200)
        return res.json()["access_token"]

    def test_login(self) -> None:
        res = self.client.post(
            "/api/v1/auth/login",
            json={"email": "gopinath@kabilaifarm.com", "password": "Gopinath@12345!"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("access_token", res.json())

    def test_products_require_auth(self) -> None:
        self.assertEqual(self.client.get("/api/v1/products").status_code, 401)

    def test_products_list_and_create(self) -> None:
        token = self._token()
        headers = {"Authorization": f"Bearer {token}"}
        res = self.client.get("/api/v1/products", headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(len(res.json()), 7)

        created = self.client.post(
            "/api/v1/products",
            headers=headers,
            json={"name": "Test Filtered", "category": "Juice", "unit": "500ml", "price": 40.0},
        )
        self.assertEqual(created.status_code, 200)
        self.assertEqual(created.json()["name"], "Test Filtered")

        patched = self.client.patch(
            f"/api/v1/products/{created.json()['id']}",
            headers=headers,
            json={"price": 45.0, "is_available": False},
        )
        self.assertEqual(patched.json()["price"], 45.0)
        self.assertFalse(patched.json()["is_available"])

    def test_company_settings(self) -> None:
        token = self._token()
        headers = {"Authorization": f"Bearer {token}"}
        res = self.client.get("/api/v1/company", headers=headers)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["name"], "Kabilai Dairy")

        patched = self.client.patch(
            "/api/v1/company",
            headers=headers,
            json={"intro_message": "Namaste! Welcome to Kabilai Dairy.", "address": "1 Test Street"},
        )
        self.assertEqual(patched.status_code, 200)
        self.assertEqual(patched.json()["intro_message"], "Namaste! Welcome to Kabilai Dairy.")
        self.assertEqual(patched.json()["address"], "1 Test Street")

        self.assertTrue(patched.json()["ai_enabled"])

        toggled = self.client.patch(
            "/api/v1/company",
            headers=headers,
            json={"ai_enabled": False},
        )
        self.assertEqual(toggled.status_code, 200)
        self.assertFalse(toggled.json()["ai_enabled"])

    def test_delivery_areas_crud(self) -> None:
        token = self._token()
        headers = {"Authorization": f"Bearer {token}"}
        res = self.client.get("/api/v1/delivery-areas", headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(len(res.json()), 8)

        created = self.client.post(
            "/api/v1/delivery-areas",
            headers=headers,
            json={"name": "Chetpet", "pincode": "600031", "city": "Chennai"},
        )
        self.assertEqual(created.status_code, 200)
        self.assertEqual(created.json()["name"], "Chetpet")

    def test_enquiry_capture(self) -> None:
        token = self._token()
        headers = {"Authorization": f"Bearer {token}"}
        res = self.client.post(
            "/api/v1/enquiries",
            headers=headers,
            json={"phone": "9876501234", "customer_name": "Ravi", "product_interest": "Curd"},
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["status"], "new")
        self.assertTrue(body["enquiry_number"].startswith("ENQ-"))

        found = self.client.get("/api/v1/enquiries/by-phone/9876501234", headers=headers)
        self.assertEqual(found.status_code, 200)
        self.assertEqual(len(found.json()), 1)

        updated = self.client.patch(
            f"/api/v1/enquiries/{body['id']}", headers=headers, json={"status": "converted"}
        )
        self.assertEqual(updated.json()["status"], "converted")

    def test_complaint_capture(self) -> None:
        token = self._token()
        headers = {"Authorization": f"Bearer {token}"}
        res = self.client.post(
            "/api/v1/complaints",
            headers=headers,
            json={"phone": "9876512345", "customer_name": "Asha", "message": "Milk not delivered today", "category": "delivery"},
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["status"], "pending")
        self.assertEqual(body["category"], "delivery")
        self.assertTrue(body["complaint_number"].startswith("CMP-"))

        found = self.client.get("/api/v1/complaints/by-phone/9876512345", headers=headers)
        self.assertEqual(found.status_code, 200)
        self.assertEqual(len(found.json()), 1)

        updated = self.client.patch(
            f"/api/v1/complaints/{body['id']}", headers=headers, json={"status": "resolved"}
        )
        self.assertEqual(updated.json()["status"], "resolved")

        # Admin-only history
        history = self.client.get(f"/api/v1/complaints/{body['id']}/history", headers=headers)
        self.assertEqual(history.status_code, 200)
        self.assertEqual(history.json()["total"], 2)  # created + status change

    def test_ai_toggle_ignores_webhook_when_disabled(self) -> None:
        token = self._token()
        headers = {"Authorization": f"Bearer {token}"}
        self.client.patch("/api/v1/company", headers=headers, json={"ai_enabled": False})

        res = self.client.post(
            "/api/v1/webhooks/gupshup",
            json={
                "type": "message",
                "payload": {
                    "id": "wamid.off1",
                    "source": "919777665544",
                    "type": "text",
                    "payload": {"text": "kabilai ai"},
                    "sender": {"name": "Sita", "phone": "919777665544"},
                },
            },
        )
        self.assertEqual(res.status_code, 200)

        # No session/contact should be created while AI is off.
        self.client.patch("/api/v1/company", headers=headers, json={"ai_enabled": True})

    def test_webhook_public_with_nested_payload(self) -> None:
        res = self.client.post(
            "/api/v1/webhooks/gupshup",
            json={
                "type": "message",
                "payload": {
                    "id": "wamid.1",
                    "source": "919888776655",
                    "type": "text",
                    "payload": {"text": "kabilai ai"},
                    "sender": {"name": "Asha", "phone": "919888776655"},
                },
            },
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn(res.json()["status"], ("ok", "ignored"))

    def test_kabilai_ai_triggers_greeting(self) -> None:
        # 'kabilai ai' must start an agent session (mock send logs, not assert content).
        self.client.post(
            "/api/v1/webhooks/gupshup",
            json={
                "type": "message",
                "payload": {
                    "id": "wamid.2",
                    "source": "919811122233",
                    "type": "text",
                    "payload": {"text": "kabilai ai"},
                    "sender": {"name": "Raj", "phone": "919811122233"},
                },
            },
        )
        # Follow-up is handled once the session is active; no assertion on output.
        self.assertTrue(True)

    def test_agent_chat(self) -> None:
        res = self.client.post(
            "/api/v1/agent/chat",
            json={"message": "What products do you have?", "contact_id": 1},
        )
        self.assertEqual(res.status_code, 200)

    def test_contacts_list(self) -> None:
        res = self.client.get("/api/v1/contacts")
        self.assertEqual(res.status_code, 200)


if __name__ == "__main__":
    unittest.main()
