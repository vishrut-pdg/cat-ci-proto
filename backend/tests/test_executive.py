import os
import unittest
from datetime import date
from unittest.mock import patch

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://cat_ci:cat_ci_demo@localhost:5432/cat_ci",
)

from fastapi.testclient import TestClient

from app.agents.prompts import PERSONA_PROMPTS
from app.main import app
from app.repositories.executive_repository import LATEST_FACTS_CTE
from app.services.executive_service import executive_service


class ExecutiveAuthorizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_demo_executive_can_log_in(self):
        response = self.client.post(
            "/api/v1/auth/login",
            json={"user_id": "robert.miller", "password": "1234"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["role"], "EXECUTIVE")

    def test_executive_api_requires_authentication(self):
        response = self.client.get("/api/v1/executive/summary")
        self.assertEqual(response.status_code, 401)

    def test_finance_user_cannot_open_executive_api(self):
        login = self.client.post(
            "/api/v1/auth/login",
            json={"user_id": "sarah.smith", "password": "1234"},
        ).json()
        response = self.client.get(
            "/api/v1/executive/summary",
            headers={"Authorization": f"Bearer {login['token']}"},
        )
        self.assertEqual(response.status_code, 403)


class ExecutiveFilterPolicyTests(unittest.TestCase):
    def test_each_persona_has_a_distinct_prompt(self):
        self.assertEqual(
            set(PERSONA_PROMPTS),
            {"FINANCE_ANALYST", "INVESTIGATION_EXPERT", "EXECUTIVE"},
        )
        self.assertEqual(len(set(PERSONA_PROMPTS.values())), 3)

    def test_nullable_filters_have_explicit_postgres_types(self):
        for parameter in ("region", "plant_id", "product_id"):
            self.assertIn(f"CAST(:{parameter} AS text) IS NULL", LATEST_FACTS_CTE)

    def test_fiscal_period_caps_as_of_date(self):
        expected = date(2026, 6, 12)
        fake_db = object()
        with patch(
            "app.services.executive_service.executive_repository.get_as_of_date",
            return_value=expected,
        ) as get_as_of:
            resolved = executive_service.resolve_as_of_date(
                fake_db, as_of_date=date(2026, 8, 24), period="FY26"
            )
        self.assertEqual(resolved, expected)
        get_as_of.assert_called_once_with(fake_db, date(2026, 6, 30))

    def test_rejects_undefined_scope(self):
        with self.assertRaisesRegex(ValueError, "enterprise scope"):
            executive_service.validate_scope("division")


if __name__ == "__main__":
    unittest.main()
