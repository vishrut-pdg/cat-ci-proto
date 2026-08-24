import os
import unittest
from datetime import date, datetime, time, timezone
from unittest.mock import patch

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://cat_ci:cat_ci_demo@localhost:5432/cat_ci",
)

from fastapi.testclient import TestClient

from app.agents.prompts import EXECUTIVE_PROMPT, PERSONA_PROMPTS
from app.db.connection import psycopg_connection_kwargs
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
    def test_startup_connection_preserves_literal_password_characters(self):
        password = "$" + "(openssl rand -hex 24)"
        params = psycopg_connection_kwargs(
            f"postgresql+psycopg://cat_ci:{password}@postgres:5432/cat_ci"
        )
        self.assertEqual(params["password"], password)
        self.assertEqual(params["dbname"], "cat_ci")

    def test_each_persona_has_a_distinct_prompt(self):
        self.assertEqual(
            set(PERSONA_PROMPTS),
            {"FINANCE_ANALYST", "INVESTIGATION_EXPERT", "EXECUTIVE"},
        )
        self.assertEqual(len(set(PERSONA_PROMPTS.values())), 3)

    def test_nullable_filters_have_explicit_postgres_types(self):
        for parameter in ("region", "plant_id", "product_id", "category_id"):
            self.assertIn(f"CAST(:{parameter} AS text) IS NULL", LATEST_FACTS_CTE)

    def test_executive_prompt_separates_category_from_cost_driver(self):
        self.assertIn("Category is a broad CAT equipment family", EXECUTIVE_PROMPT)
        self.assertIn("Never describe a cost", EXECUTIVE_PROMPT)
        self.assertIn("attributed_opportunity_count", EXECUTIVE_PROMPT)
        self.assertIn("high_priority_opportunities", EXECUTIVE_PROMPT)

    def test_explicit_as_of_date_includes_the_full_day(self):
        expected = datetime(2026, 8, 24, 10, 30, tzinfo=timezone.utc)
        fake_db = object()
        with patch(
            "app.services.executive_service.executive_repository.get_as_of_date",
            return_value=expected,
        ) as get_as_of:
            resolved = executive_service.resolve_as_of_date(
                fake_db, as_of_date=date(2026, 8, 24), period="FY26"
            )
        self.assertEqual(resolved, expected)
        get_as_of.assert_called_once_with(
            fake_db, datetime.combine(date(2026, 8, 24), time.max, tzinfo=timezone.utc)
        )

    def test_rejects_undefined_scope(self):
        with self.assertRaisesRegex(ValueError, "enterprise scope"):
            executive_service.validate_scope("division")

    def test_product_cost_driver_report_ignores_category_filter(self):
        fake_db = object()
        with (
            patch.object(executive_service, "resolve_as_of_date", return_value=date(2026, 6, 12)),
            patch("app.services.executive_service.executive_repository.get_product_detail", return_value={"product_id": "EQ-010"}) as detail,
            patch("app.services.executive_service.executive_repository.get_cost_drivers", return_value={"drivers": []}) as drivers,
        ):
            result = executive_service.product_cost_drivers(
                fake_db,
                product_id="EQ-010",
                as_of_date=None,
                period="FY26",
                scope="enterprise",
                region=None,
                plant_id=None,
                category_id="dozers",
            )
        self.assertEqual(result["product_id"], "EQ-010")
        self.assertNotIn("category_id", detail.call_args.kwargs)
        self.assertNotIn("category_id", drivers.call_args.kwargs)


if __name__ == "__main__":
    unittest.main()
