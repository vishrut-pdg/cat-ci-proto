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
        "category_id": None,
    }
    summary = executive_service.summary(db, **filters)
    as_of_date = summary["as_of_date"]
    # The API contract keeps ``opportunity_count`` for UI consumers. Give the
    # language model a more explicit field name so it cannot confuse the total
    # attributed count with the separate high-priority count on category rows.
    summary_for_ai = dict(summary)
    for key in ("top_plant", "top_category", "top_product", "top_component"):
        if summary_for_ai.get(key):
            item = dict(summary_for_ai[key])
            item["attributed_opportunity_count"] = item.pop("opportunity_count")
            summary_for_ai[key] = item
    return {
        "as_of_date": as_of_date,
        "period": period,
        "scope": scope,
        "product_id": product_id,
        "semantic_definitions": {
            "category": "A broad CAT equipment family, such as Excavators or Dozers.",
            "product": "A specific equipment model within one equipment category.",
            "component": "A part used by one or more products.",
            "cost_driver": "A root cause of cost variance, such as supplier price, logistics, tariff, material, volume, or specification difference.",
            "attributed_opportunity_count": "All opportunities attributed to that ranked portfolio dimension; this is not a high-priority count.",
            "high_priority_opportunities": "Only opportunities whose backend priority is HIGH.",
        },
        "summary": summary_for_ai,
        "categories": executive_service.categories(db, **filters)["categories"],
        "top_products": executive_service.products(db, **filters)["items"][:10],
        "top_plants": executive_service.plants(db, **filters)["items"][:10],
        "quick_wins": executive_service.quick_wins(db, limit=5, **filters)["items"],
        "cost_drivers": (
            executive_service.product_cost_drivers(db, **filters)["drivers"]
            if product_id else []
        ),
        "products_awaiting_decision": executive_repository.get_products_awaiting_decision(
            db, as_of_date=as_of_date, product_id=product_id, limit=5,
        ),
    }
