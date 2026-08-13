from typing import Any

from sqlalchemy.engine import Connection

from app.repositories.opportunity_repository import (
    opportunity_repository,
)


class OpportunityService:

    def update_status(self, db: Connection, opportunity_id: str, status: str, actor: dict):
        return opportunity_repository.update_status(db, opportunity_id, status, actor)

    def get_timeseries(self, db: Connection, opportunity_id: str):
        return opportunity_repository.get_timeseries(db, opportunity_id)

    # ========================================================
    # LIST
    # ========================================================

    def list_opportunities(
        self,
        db: Connection,
        *,
        status: str | None,
        limit: int,
        offset: int,
    ) -> list[dict[str, Any]]:

        return opportunity_repository.list_opportunities(
            db,
            status=status,
            limit=limit,
            offset=offset,
        )

    # ========================================================
    # DETAIL
    # ========================================================

    def get_opportunity(
        self,
        db: Connection,
        opportunity_id: str,
    ) -> dict[str, Any] | None:

        row = opportunity_repository.get_opportunity(
            db,
            opportunity_id,
        )

        if row is None:
            return None

        return {
            "opportunity_id": row["opportunity_id"],
            "opportunity_number": row[
                "opportunity_number"
            ],
            "status": row["status"],
            "priority": row["priority"],
            "detection_source": row[
                "detection_source"
            ],

            "part": {
                "part_id": row["part_id"],
                "part_number": row["part_number"],
                "component_id": row["component_id"],
                "name": row["part_name"],
                "category": row["category"],
                "part_family": row["part_family"],
                "part_type": row["part_type"],
                "description": row["description"],
            },

            "plant": {
                "plant_id": row["plant_id"],
                "plant_code": row["plant_code"],
                "plant_name": row["plant_name"],
                "city": row["city"],
                "country": row["country"],
                "region": row["region"],
                "currency": row["currency"],
            },

            "metrics": self._metrics_from_row(row),
        }

    # ========================================================
    # OVERVIEW
    # ========================================================

    def get_overview(
        self,
        db: Connection,
        opportunity_id: str,
    ) -> dict[str, Any] | None:

        opportunity = (
            opportunity_repository.get_opportunity(
                db,
                opportunity_id,
            )
        )

        if opportunity is None:
            return None

        cost_drivers = (
            opportunity_repository.get_cost_drivers(
                db,
                opportunity_id,
            )
        )

        return {
            "opportunity_id": opportunity_id,

            "metrics": self._metrics_from_row(
                opportunity
            ),

            "cost_drivers": cost_drivers,
        }

    # ========================================================
    # PLANTS
    # ========================================================

    def get_plants(
        self,
        db: Connection,
        opportunity_id: str,
    ) -> dict[str, Any] | None:

        opportunity = (
            opportunity_repository.get_opportunity(
                db,
                opportunity_id,
            )
        )

        if opportunity is None:
            return None

        plants = (
            opportunity_repository.get_plant_comparisons(
                db,
                opportunity_id,
            )
        )

        return {
            "opportunity_id": opportunity_id,

            "benchmark_type": "SIMILAR_PLANTS",

            "peer_average_cost": float(
                opportunity["peer_average_cost"]
            ),

            "plants": plants,
        }

    # ========================================================
    # SUPPLIERS
    # ========================================================

    def get_suppliers(
        self,
        db: Connection,
        opportunity_id: str,
    ) -> dict[str, Any] | None:

        opportunity = (
            opportunity_repository.get_opportunity(
                db,
                opportunity_id,
            )
        )

        if opportunity is None:
            return None

        suppliers = (
            opportunity_repository
            .get_supplier_comparisons(
                db,
                opportunity_id,
            )
        )

        return {
            "opportunity_id": opportunity_id,
            "suppliers": suppliers,
        }

    # ========================================================
    # LOGISTICS
    # ========================================================

    def get_logistics(
        self,
        db: Connection,
        opportunity_id: str,
    ) -> dict[str, Any] | None:

        opportunity = (
            opportunity_repository.get_opportunity(
                db,
                opportunity_id,
            )
        )

        if opportunity is None:
            return None

        components = (
            opportunity_repository
            .get_logistics_components(
                db,
                opportunity_id,
            )
        )

        trend = (
            opportunity_repository
            .get_logistics_trend(
                db,
                opportunity_id,
            )
        )

        total_cost = sum(
            float(item["cost"])
            for item in components
        )

        peer_average = sum(
            float(item["peer_average"])
            for item in components
        )

        variance = (
            total_cost
            - peer_average
        )

        if peer_average:
            variance_percent = (
                variance
                / peer_average
                * 100
            )
        else:
            variance_percent = 0

        return {
            "opportunity_id": opportunity_id,

            "total_cost": round(
                total_cost,
                2,
            ),

            "peer_average": round(
                peer_average,
                2,
            ),

            "variance": round(
                variance,
                2,
            ),

            "variance_percent": round(
                variance_percent,
                2,
            ),

            "components": components,

            "trend": trend,
        }

    # ========================================================
    # TARIFF
    # ========================================================

    def get_tariff(
        self,
        db: Connection,
        opportunity_id: str,
    ) -> dict[str, Any] | None:

        opportunity = (
            opportunity_repository.get_opportunity(
                db,
                opportunity_id,
            )
        )

        if opportunity is None:
            return None

        detail = (
            opportunity_repository.get_tariff_detail(
                db,
                opportunity_id,
            )
        )

        if detail is None:
            return None

        plant_comparisons = (
            opportunity_repository
            .get_tariff_comparisons(
                db,
                opportunity_id,
            )
        )

        import_duty = float(
            detail["import_duty_per_unit"]
        )

        peer_duty = float(
            detail["peer_duty_per_unit"]
        )

        variance = (
            import_duty
            - peer_duty
        )

        variance_percent = (
            variance
            / peer_duty
            * 100
            if peer_duty
            else 0
        )

        return {
            "opportunity_id": opportunity_id,

            "hs_code": detail["hs_code"],

            "duty_rate": detail[
                "duty_rate"
            ],

            "peer_average_duty_rate": detail[
                "peer_average_duty_rate"
            ],

            "calculation_basis": detail[
                "calculation_basis"
            ],

            "valuation_type": detail[
                "valuation_type"
            ],

            "effective_date": detail[
                "effective_date"
            ],

            "import_duty_per_unit": import_duty,

            "peer_duty_per_unit": peer_duty,

            "duty_variance_per_unit": round(
                variance,
                2,
            ),

            "duty_variance_percent": round(
                variance_percent,
                2,
            ),

            "annual_duty_impact": detail[
                "annual_duty_impact"
            ],

            "plant_comparisons": plant_comparisons,
        }

    # ========================================================
    # HELPERS
    # ========================================================

    @staticmethod
    def _metrics_from_row(
        row: dict[str, Any],
    ) -> dict[str, Any]:

        return {
            "unit_cost": row["unit_cost"],

            "peer_average_cost": row[
                "peer_average_cost"
            ],

            "variance_amount": row[
                "variance_amount"
            ],

            "variance_percent": row[
                "variance_percent"
            ],

            "annual_volume": row[
                "annual_volume"
            ],

            "annual_spend": row[
                "annual_spend"
            ],

            "potential_savings": row[
                "potential_savings"
            ],

            "impact_score": row[
                "impact_score"
            ],

            "confidence_score": row[
                "confidence_score"
            ],
        }


opportunity_service = OpportunityService()
