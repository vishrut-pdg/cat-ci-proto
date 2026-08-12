from app.services.opportunity_service import opportunity_service


def get_grounded_context(db, opportunity_id: str) -> dict:
    """Structured tool boundary: only this opportunity's evidence is returned."""
    return {
        "summary": opportunity_service.get_opportunity(db, opportunity_id),
        "overview": opportunity_service.get_overview(db, opportunity_id),
        "plants": opportunity_service.get_plants(db, opportunity_id),
        "suppliers": opportunity_service.get_suppliers(db, opportunity_id),
        "logistics": opportunity_service.get_logistics(db, opportunity_id),
        "tariff": opportunity_service.get_tariff(db, opportunity_id),
        "timeseries": opportunity_service.get_timeseries(db, opportunity_id),
    }
