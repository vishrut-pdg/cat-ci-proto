from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection


class OpportunityRepository:

    def get_timeseries(self, db: Connection, opportunity_id: str) -> list[dict[str, Any]]:
        result = db.execute(text("""
            SELECT snapshot_at::date::text AS period, unit_cost, peer_average_cost,
                   variance_amount, variance_percent, annual_volume,
                   annual_spend, potential_savings, confidence_score, impact_score
            FROM opportunity.metric_snapshots
            WHERE opportunity_id=:opportunity_id ORDER BY snapshot_at
        """), {"opportunity_id": opportunity_id})
        return [dict(row) for row in result.mappings().all()]

    # ========================================================
    # LIST
    # ========================================================

    def list_opportunities(
        self,
        db: Connection,
        *,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:

        query = """
            SELECT
                opportunity_id,
                status,
                priority,

                part_number,
                component_id,
                part_name,
                category,
                part_family,

                plant_code,
                plant_name,
                country,

                unit_cost,
                peer_average_cost,
                variance_amount,
                variance_percent,

                potential_savings,
                impact_score,
                confidence_score

            FROM opportunity.opportunity_summary
        """

        parameters: dict[str, Any] = {
            "limit": limit,
            "offset": offset,
        }

        if status:
            query += """
                WHERE status = :status
            """

            parameters["status"] = status

        query += """
            ORDER BY
                impact_score DESC,
                potential_savings DESC

            LIMIT :limit
            OFFSET :offset
        """

        result = db.execute(
            text(query),
            parameters,
        )

        return [
            dict(row)
            for row in result.mappings().all()
        ]

    # ========================================================
    # OPPORTUNITY DETAIL
    # ========================================================

    def get_opportunity(
        self,
        db: Connection,
        opportunity_id: str,
    ) -> dict[str, Any] | None:

        query = text(
            """
            SELECT
                o.id AS opportunity_id,
                o.opportunity_number,
                o.status,
                o.priority,
                o.detection_source,

                p.id AS part_id,
                p.part_number,
                p.component_id,
                p.name AS part_name,
                p.category,
                p.part_family,
                p.part_type,

                pc.description,

                pl.id AS plant_id,
                pl.plant_code,
                pl.name AS plant_name,
                pl.city,
                pl.country,
                pl.region,
                pl.currency,

                m.unit_cost,
                m.peer_average_cost,
                m.variance_amount,
                m.variance_percent,

                m.annual_volume,
                m.annual_spend,

                m.potential_savings,
                m.impact_score,
                m.confidence_score

            FROM opportunity.opportunities o

            JOIN catalog.parts p
                ON p.id = o.part_id

            LEFT JOIN catalog.part_catalog pc
                ON pc.part_id = p.id

            JOIN supply.plants pl
                ON pl.id = o.plant_id

            JOIN opportunity.metric_snapshots m
                ON m.opportunity_id = o.id

            WHERE o.id = :opportunity_id

            ORDER BY m.snapshot_at DESC

            LIMIT 1
            """
        )

        result = db.execute(
            query,
            {
                "opportunity_id": opportunity_id,
            },
        )

        row = result.mappings().first()

        if row is None:
            return None

        return dict(row)

    # ========================================================
    # COST DRIVERS
    # ========================================================

    def get_cost_drivers(
        self,
        db: Connection,
        opportunity_id: str,
    ) -> list[dict[str, Any]]:

        query = text(
            """
            SELECT
                driver_code AS code,
                driver_name AS name,

                impact_amount,
                impact_percent,

                rank_position AS rank,
                confidence_score,

                explanation

            FROM opportunity.cost_drivers

            WHERE opportunity_id = :opportunity_id

            ORDER BY rank_position
            """
        )

        result = db.execute(
            query,
            {
                "opportunity_id": opportunity_id,
            },
        )

        return [
            dict(row)
            for row in result.mappings().all()
        ]

    # ========================================================
    # PLANT COMPARISONS
    # ========================================================

    def get_plant_comparisons(
        self,
        db: Connection,
        opportunity_id: str,
    ) -> list[dict[str, Any]]:

        query = text(
            """
            SELECT
                pc.plant_id,

                p.plant_code,
                p.name AS plant_name,
                p.country,

                pc.unit_cost,
                pc.peer_average_cost,

                pc.variance_amount,
                pc.variance_percent,

                pc.annual_volume,
                pc.volume_variance_percent,

                pc.rank_position AS rank

            FROM opportunity.plant_comparisons pc

            JOIN supply.plants p
                ON p.id = pc.plant_id

            WHERE pc.opportunity_id = :opportunity_id

            ORDER BY pc.rank_position
            """
        )

        result = db.execute(
            query,
            {
                "opportunity_id": opportunity_id,
            },
        )

        return [
            dict(row)
            for row in result.mappings().all()
        ]

    # ========================================================
    # SUPPLIER COMPARISONS
    # ========================================================

    def get_supplier_comparisons(
        self,
        db: Connection,
        opportunity_id: str,
    ) -> list[dict[str, Any]]:

        query = text(
            """
            SELECT
                sc.supplier_id,

                s.supplier_code,
                s.name AS supplier_name,
                s.country,

                sc.unit_cost,
                sc.peer_average_cost,

                sc.variance_amount,
                sc.variance_percent,

                sc.annual_spend,
                sc.annual_volume,

                s.quality_score,
                s.delivery_score,
                s.responsiveness_score,
                s.overall_score,

                sc.rank_position AS rank

            FROM opportunity.supplier_comparisons sc

            JOIN supply.suppliers s
                ON s.id = sc.supplier_id

            WHERE sc.opportunity_id = :opportunity_id

            ORDER BY sc.rank_position
            """
        )

        result = db.execute(
            query,
            {
                "opportunity_id": opportunity_id,
            },
        )

        return [
            dict(row)
            for row in result.mappings().all()
        ]

    # ========================================================
    # LOGISTICS
    # ========================================================

    def get_logistics_components(
        self,
        db: Connection,
        opportunity_id: str,
    ) -> list[dict[str, Any]]:

        query = text(
            """
            SELECT
                component_code AS code,
                component_name AS name,

                brazil_cost AS cost,
                peer_average_cost AS peer_average,

                variance_amount AS variance,
                variance_percent,

                rank_position AS rank

            FROM opportunity.logistics_components

            WHERE opportunity_id = :opportunity_id

            ORDER BY rank_position
            """
        )

        result = db.execute(
            query,
            {
                "opportunity_id": opportunity_id,
            },
        )

        return [
            dict(row)
            for row in result.mappings().all()
        ]

    def get_logistics_trend(
        self,
        db: Connection,
        opportunity_id: str,
    ) -> list[dict[str, Any]]:

        query = text(
            """
            SELECT
                period_start::text AS period,

                actual_cost,
                peer_average_cost

            FROM opportunity.logistics_trend

            WHERE opportunity_id = :opportunity_id

            ORDER BY period_start
            """
        )

        result = db.execute(
            query,
            {
                "opportunity_id": opportunity_id,
            },
        )

        return [
            dict(row)
            for row in result.mappings().all()
        ]

    # ========================================================
    # TARIFF
    # ========================================================

    def get_tariff_detail(
        self,
        db: Connection,
        opportunity_id: str,
    ) -> dict[str, Any] | None:

        query = text(
            """
            SELECT
                hs_code,

                duty_rate,
                peer_average_duty_rate,

                calculation_basis,
                valuation_type,

                effective_date::text AS effective_date,

                import_duty_per_unit,
                peer_duty_per_unit,

                annual_duty_impact

            FROM opportunity.tariff_details

            WHERE opportunity_id = :opportunity_id

            LIMIT 1
            """
        )

        result = db.execute(
            query,
            {
                "opportunity_id": opportunity_id,
            },
        )

        row = result.mappings().first()

        if row is None:
            return None

        return dict(row)

    def get_tariff_comparisons(
        self,
        db: Connection,
        opportunity_id: str,
    ) -> list[dict[str, Any]]:

        query = text(
            """
            SELECT
                tc.plant_id,

                p.plant_code,
                p.name AS plant_name,
                p.country,

                tc.duty_rate

            FROM opportunity.tariff_comparisons tc

            JOIN supply.plants p
                ON p.id = tc.plant_id

            WHERE tc.opportunity_id = :opportunity_id

            ORDER BY tc.duty_rate
            """
        )

        result = db.execute(
            query,
            {
                "opportunity_id": opportunity_id,
            },
        )

        return [
            dict(row)
            for row in result.mappings().all()
        ]


opportunity_repository = OpportunityRepository()
