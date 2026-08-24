from datetime import date
import re

from sqlalchemy.engine import Connection

from app.repositories.executive_repository import executive_repository


class ExecutiveService:
    def resolve_as_of_date(self, db: Connection, *, as_of_date: date | None,
                           period: str | None) -> date:
        requested = as_of_date or date.today()
        if period:
            match = re.fullmatch(r"FY(\d{2}|\d{4})", period.upper())
            if not match:
                raise ValueError("period must use FY26 or FY2026 format")
            value = int(match.group(1))
            year = value + 2000 if value < 100 else value
            requested = min(requested, date(year, 6, 30))
        return executive_repository.get_as_of_date(db, requested)

    @staticmethod
    def validate_scope(scope: str) -> str:
        normalized = scope.lower()
        if normalized != "enterprise":
            raise ValueError("Only enterprise scope is supported by the current data model")
        return normalized

    def summary(self, db: Connection, **filters):
        resolved = self.resolve_as_of_date(db, as_of_date=filters.pop("as_of_date"), period=filters.pop("period"))
        self.validate_scope(filters.pop("scope"))
        result = executive_repository.get_summary(db, as_of_date=resolved, **filters)
        return {"as_of_date": resolved, **result}

    def quick_wins(self, db: Connection, *, limit: int, **filters):
        resolved = self.resolve_as_of_date(db, as_of_date=filters.pop("as_of_date"), period=filters.pop("period"))
        self.validate_scope(filters.pop("scope"))
        return {"as_of_date": resolved, "items": executive_repository.get_quick_wins(
            db, as_of_date=resolved, limit=limit, **filters)}

    def plants(self, db: Connection, **filters):
        resolved = self.resolve_as_of_date(db, as_of_date=filters.pop("as_of_date"), period=filters.pop("period"))
        self.validate_scope(filters.pop("scope"))
        return {"as_of_date": resolved, "items": executive_repository.get_plants(db, as_of_date=resolved, **filters)}

    def products(self, db: Connection, **filters):
        resolved = self.resolve_as_of_date(db, as_of_date=filters.pop("as_of_date"), period=filters.pop("period"))
        self.validate_scope(filters.pop("scope"))
        return {"as_of_date": resolved, "items": executive_repository.get_products(db, as_of_date=resolved, **filters)}

    def product_detail(self, db: Connection, *, product_id: str, **filters):
        filters.pop("product_id", None)
        resolved = self.resolve_as_of_date(db, as_of_date=filters.pop("as_of_date"), period=filters.pop("period"))
        self.validate_scope(filters.pop("scope"))
        result = executive_repository.get_product_detail(
            db, product_id=product_id, as_of_date=resolved, **filters,
        )
        return {"as_of_date": resolved, **result} if result else None

    def product_trend(self, db: Connection, *, product_id: str, **filters):
        filters.pop("product_id", None)
        resolved = self.resolve_as_of_date(db, as_of_date=filters.pop("as_of_date"), period=filters.pop("period"))
        self.validate_scope(filters.pop("scope"))
        detail = executive_repository.get_product_detail(
            db, product_id=product_id, as_of_date=resolved, **filters,
        )
        if not detail:
            return None
        return {"as_of_date": resolved, "product_id": product_id, "series": executive_repository.get_product_trend(
            db, product_id=product_id, as_of_date=resolved, **filters,
        )}

    def product_cost_drivers(self, db: Connection, *, product_id: str, **filters):
        filters.pop("product_id", None)
        resolved = self.resolve_as_of_date(db, as_of_date=filters.pop("as_of_date"), period=filters.pop("period"))
        self.validate_scope(filters.pop("scope"))
        detail = executive_repository.get_product_detail(
            db, product_id=product_id, as_of_date=resolved, **filters,
        )
        if not detail:
            return None
        return {"as_of_date": resolved, **executive_repository.get_categories(
            db, as_of_date=resolved, product_id=product_id, **filters,
        )}

    def component_detail(self, db: Connection, *, component_id: str, **filters):
        resolved = self.resolve_as_of_date(db, as_of_date=filters.pop("as_of_date"), period=filters.pop("period"))
        self.validate_scope(filters.pop("scope"))
        result = executive_repository.get_component_detail(
            db, component_id=component_id, as_of_date=resolved, **filters,
        )
        return {"as_of_date": resolved, **result} if result else None

    def categories(self, db: Connection, **filters):
        resolved = self.resolve_as_of_date(db, as_of_date=filters.pop("as_of_date"), period=filters.pop("period"))
        self.validate_scope(filters.pop("scope"))
        return {"as_of_date": resolved, **executive_repository.get_categories(
            db, as_of_date=resolved, **filters)}

    def report(self, db: Connection, **filters):
        original = dict(filters)
        summary = self.summary(db, **dict(filters))
        resolved = summary["as_of_date"]
        query_filters = {key: value for key, value in original.items()
                         if key not in {"as_of_date", "period", "scope"}}
        return {
            "as_of_date": resolved,
            "period": original["period"],
            "scope": self.validate_scope(original["scope"]),
            "summary": summary,
            "plants": executive_repository.get_plants(db, as_of_date=resolved, **query_filters),
            "products": executive_repository.get_products(db, as_of_date=resolved, **query_filters),
            "quick_wins": executive_repository.get_quick_wins(db, as_of_date=resolved, limit=5, **query_filters),
        }


executive_service = ExecutiveService()
