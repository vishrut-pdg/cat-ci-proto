from app.repositories.executive_repository import executive_repository
from app.services.executive_service import executive_service


def get_executive_context(db, *, period: str = "FY26", scope: str = "enterprise",
                          product_id: str | None = None) -> dict:
    """Return calculated portfolio evidence; the model only explains these backend facts."""
    filters = {
        "as_of_date": None,
        "period": period,
        "scope": scope,
        "region": None,
        "plant_id": None,
        "product_id": product_id,
    }
    summary = executive_service.summary(db, **filters)
    as_of_date = summary["as_of_date"]
    return {
        "as_of_date": as_of_date,
        "period": period,
        "scope": scope,
        "product_id": product_id,
        "summary": summary,
        "top_products": executive_service.products(db, **filters)["items"][:10],
        "top_plants": executive_service.plants(db, **filters)["items"][:10],
        "quick_wins": executive_service.quick_wins(db, limit=5, **filters)["items"],
        "cost_drivers": executive_service.categories(db, **filters)["items"],
        "products_awaiting_decision": executive_repository.get_products_awaiting_decision(
            db, as_of_date=as_of_date, product_id=product_id, limit=5,
        ),
    }
