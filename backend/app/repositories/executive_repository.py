from datetime import date, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection


LATEST_FACTS_CTE = """
WITH latest_snapshot AS (
    SELECT DISTINCT ON (m.opportunity_id)
        m.opportunity_id, m.snapshot_at, m.unit_cost, m.peer_average_cost,
        m.variance_amount, m.variance_percent, m.annual_volume,
        m.annual_spend, m.potential_savings, m.impact_score,
        m.confidence_score
    FROM opportunity.metric_snapshots m
    WHERE m.snapshot_at <= :as_of_date
    ORDER BY m.opportunity_id, m.snapshot_at DESC
),
primary_product AS (
    SELECT DISTINCT ON (pc.part_id)
        pc.part_id, em.id AS product_id,
        em.equipment_family || ' ' || em.model_code AS product_name,
        em.equipment_family, ec.id AS category_id, ec.name AS category_name
    FROM catalog.part_compatibility pc
    JOIN catalog.equipment_models em ON em.id = pc.equipment_model_id
    JOIN catalog.equipment_categories ec ON ec.id = em.category_id
    ORDER BY pc.part_id,
        CASE pc.compatibility_type WHEN 'PRIMARY' THEN 0 ELSE 1 END,
        em.id
),
facts AS (
    SELECT o.id AS opportunity_id, o.status, o.priority, o.part_id,
        p.component_id, p.name AS component_name, p.category AS part_classification,
        pl.id AS plant_id, pl.plant_code, pl.name AS plant_name,
        pl.country, pl.region, pp.product_id, pp.product_name,
        pp.equipment_family, pp.category_id, pp.category_name,
        m.snapshot_at, m.unit_cost,
        m.peer_average_cost, m.variance_amount, m.variance_percent,
        m.annual_volume, m.annual_spend, m.potential_savings,
        m.impact_score, m.confidence_score
    FROM opportunity.opportunities o
    JOIN latest_snapshot m ON m.opportunity_id = o.id
    JOIN catalog.parts p ON p.id = o.part_id
    JOIN supply.plants pl ON pl.id = o.plant_id
    LEFT JOIN primary_product pp ON pp.part_id = o.part_id
    WHERE (CAST(:region AS text) IS NULL OR pl.region = CAST(:region AS text))
      AND (CAST(:plant_id AS text) IS NULL OR pl.id = CAST(:plant_id AS text))
      AND (CAST(:product_id AS text) IS NULL OR pp.product_id = CAST(:product_id AS text))
      AND (CAST(:category_id AS text) IS NULL OR pp.category_id = CAST(:category_id AS text))
)
"""


class ExecutiveRepository:
    def get_as_of_date(self, db: Connection, requested: datetime) -> datetime:
        value = db.execute(text("""
            SELECT COALESCE(MAX(snapshot_at), :as_of_date)
            FROM opportunity.metric_snapshots
            WHERE snapshot_at <= :as_of_date
        """), {"as_of_date": requested}).scalar_one()
        return value

    @staticmethod
    def _params(as_of_date: date, region: str | None = None,
                plant_id: str | None = None, product_id: str | None = None,
                category_id: str | None = None) -> dict[str, Any]:
        return {"as_of_date": as_of_date, "region": region,
                "plant_id": plant_id, "product_id": product_id,
                "category_id": category_id}

    def get_summary(self, db: Connection, *, as_of_date: date,
                    region: str | None = None, plant_id: str | None = None,
                    product_id: str | None = None,
                    category_id: str | None = None) -> dict[str, Any]:
        params = self._params(as_of_date, region, plant_id, product_id, category_id)
        row = db.execute(text(LATEST_FACTS_CTE + """
            SELECT COALESCE(SUM(potential_savings), 0) AS total_potential_savings,
                   COUNT(*)::int AS opportunity_count
            FROM facts
        """), params).mappings().one()

        dimensions = {
            "top_plant": ("plant_id", "plant_name"),
            "top_product": ("product_id", "product_name"),
            "top_category": ("category_id", "category_name"),
            "top_component": ("component_id", "component_name"),
        }
        result = dict(row)
        for key, (id_col, name_col) in dimensions.items():
            result[key] = db.execute(text(LATEST_FACTS_CTE + f"""
                SELECT {id_col} AS id, {name_col} AS name,
                    SUM(potential_savings) AS potential_savings,
                    CASE WHEN SUM(peer_average_cost * annual_volume) = 0 THEN 0
                         ELSE SUM(variance_amount * annual_volume)
                              / SUM(peer_average_cost * annual_volume) * 100 END AS variance_percent,
                    COUNT(*)::int AS opportunity_count
                FROM facts
                WHERE {id_col} IS NOT NULL
                GROUP BY {id_col}, {name_col}
                ORDER BY potential_savings DESC, {id_col}
                LIMIT 1
            """), params).mappings().first()
        return result

    def get_quick_wins(self, db: Connection, *, as_of_date: date, limit: int,
                       region: str | None = None, plant_id: str | None = None,
                       product_id: str | None = None,
                       category_id: str | None = None) -> list[dict[str, Any]]:
        params = self._params(as_of_date, region, plant_id, product_id, category_id) | {"limit": limit}
        rows = db.execute(text(LATEST_FACTS_CTE + """
            SELECT ROW_NUMBER() OVER (
                       ORDER BY potential_savings DESC, confidence_score DESC, opportunity_id
                   )::int AS rank,
                   component_name || ' at ' || plant_name AS title,
                   potential_savings,
                   CASE WHEN confidence_score >= .85 AND variance_percent <= 20 THEN 'HIGH'
                        WHEN confidence_score >= .70 THEN 'MEDIUM' ELSE 'LOW' END AS ease,
                   confidence_score AS confidence,
                   CASE priority WHEN 'HIGH' THEN 'HIGH' WHEN 'MEDIUM' THEN 'MEDIUM' ELSE 'LOW' END AS urgency,
                   CASE priority
                       WHEN 'HIGH' THEN 'High-priority value with a current, validated cost gap.'
                       WHEN 'MEDIUM' THEN 'Material savings supported by current benchmark evidence.'
                       ELSE 'Savings are available with a lower immediate decision pressure.'
                   END AS why_now,
                   opportunity_id
            FROM facts
            WHERE status NOT IN ('REJECTED', 'COMPLETED')
            ORDER BY rank
            LIMIT :limit
        """), params).mappings().all()
        return [dict(row) for row in rows]

    def get_plants(self, db: Connection, *, as_of_date: date,
                   region: str | None = None, plant_id: str | None = None,
                   product_id: str | None = None,
                   category_id: str | None = None) -> list[dict[str, Any]]:
        params = self._params(as_of_date, region, plant_id, product_id, category_id)
        rows = db.execute(text(LATEST_FACTS_CTE + """
            , driver_totals AS (
                SELECT f.plant_id, cd.driver_name, SUM(cd.impact_amount * f.annual_volume) AS impact
                FROM facts f
                JOIN opportunity.cost_drivers cd ON cd.opportunity_id = f.opportunity_id
                GROUP BY f.plant_id, cd.driver_name
            ), primary_drivers AS (
                SELECT DISTINCT ON (plant_id) plant_id, driver_name
                FROM driver_totals ORDER BY plant_id, impact DESC, driver_name
            )
            SELECT f.plant_id, f.plant_code, f.plant_name, f.country,
                SUM(f.unit_cost * f.annual_volume) / NULLIF(SUM(f.annual_volume), 0) AS unit_cost,
                SUM(f.variance_amount * f.annual_volume)
                    / NULLIF(SUM(f.peer_average_cost * f.annual_volume), 0) * 100 AS variance_percent,
                SUM(f.potential_savings) AS potential_savings,
                CASE WHEN MAX(f.variance_percent) >= 20 THEN 'HIGH'
                     WHEN MAX(f.variance_percent) >= 10 THEN 'WATCH' ELSE 'STABLE' END AS attention_level,
                pd.driver_name AS primary_driver,
                CASE WHEN SUM(f.variance_amount * f.annual_volume) > 0 THEN 'ABOVE_BENCHMARK'
                     WHEN SUM(f.variance_amount * f.annual_volume) < 0 THEN 'BELOW_BENCHMARK'
                     ELSE 'AT_BENCHMARK' END AS benchmark_status,
                COUNT(*)::int AS opportunity_count
            FROM facts f
            LEFT JOIN primary_drivers pd ON pd.plant_id = f.plant_id
            GROUP BY f.plant_id, f.plant_code, f.plant_name, f.country, pd.driver_name
            ORDER BY potential_savings DESC, f.plant_id
        """), params).mappings().all()
        return [dict(row) for row in rows]

    def get_products(self, db: Connection, *, as_of_date: date,
                     region: str | None = None, plant_id: str | None = None,
                     product_id: str | None = None,
                     category_id: str | None = None) -> list[dict[str, Any]]:
        params = self._params(as_of_date, region, plant_id, product_id, category_id)
        rows = db.execute(text(LATEST_FACTS_CTE + """
            , plant_costs AS (
                SELECT product_id, plant_name,
                    SUM(unit_cost * annual_volume) / NULLIF(SUM(annual_volume), 0) AS unit_cost
                FROM facts WHERE product_id IS NOT NULL
                GROUP BY product_id, plant_name
            ), product_extremes AS (
                SELECT DISTINCT product_id,
                    FIRST_VALUE(plant_name) OVER (PARTITION BY product_id ORDER BY unit_cost DESC, plant_name) AS highest_cost_plant,
                    FIRST_VALUE(plant_name) OVER (PARTITION BY product_id ORDER BY unit_cost ASC, plant_name) AS lowest_cost_plant
                FROM plant_costs
            )
            SELECT f.product_id, f.product_name, f.equipment_family,
                f.category_id, f.category_name,
                SUM(f.unit_cost * f.annual_volume) / NULLIF(SUM(f.annual_volume), 0) AS average_unit_cost,
                pe.highest_cost_plant, pe.lowest_cost_plant,
                SUM(f.variance_amount * f.annual_volume)
                    / NULLIF(SUM(f.peer_average_cost * f.annual_volume), 0) * 100 AS variance_percent,
                SUM(f.potential_savings) AS potential_savings,
                CASE WHEN MAX(f.priority) FILTER (WHERE f.priority = 'HIGH') IS NOT NULL THEN 'HIGH'
                     WHEN MAX(f.priority) FILTER (WHERE f.priority = 'MEDIUM') IS NOT NULL THEN 'MEDIUM'
                     ELSE 'LOW' END AS priority,
                COUNT(*)::int AS opportunity_count
            FROM facts f
            JOIN product_extremes pe ON pe.product_id = f.product_id
            WHERE f.product_id IS NOT NULL
            GROUP BY f.product_id, f.product_name, f.equipment_family,
                     f.category_id, f.category_name,
                     pe.highest_cost_plant, pe.lowest_cost_plant
            ORDER BY potential_savings DESC, f.product_id
        """), params).mappings().all()
        return [dict(row) for row in rows]

    def get_product_detail(self, db: Connection, *, product_id: str,
                           as_of_date: date, region: str | None = None,
                           plant_id: str | None = None) -> dict[str, Any] | None:
        params = self._params(as_of_date, region, plant_id, product_id)
        product = db.execute(text(LATEST_FACTS_CTE + """
            SELECT product_id, product_name, equipment_family, category_id, category_name,
                SUM(unit_cost * annual_volume) / NULLIF(SUM(annual_volume), 0) AS average_unit_cost,
                SUM(peer_average_cost * annual_volume) / NULLIF(SUM(annual_volume), 0) AS benchmark_unit_cost,
                SUM(variance_amount * annual_volume) / NULLIF(SUM(annual_volume), 0) AS variance_amount,
                SUM(variance_amount * annual_volume)
                    / NULLIF(SUM(peer_average_cost * annual_volume), 0) * 100 AS variance_percent,
                SUM(annual_volume)::int AS annual_volume,
                SUM(annual_spend) AS annual_spend,
                SUM(potential_savings) AS potential_savings,
                AVG(confidence_score) AS confidence_score,
                CASE WHEN BOOL_OR(priority = 'HIGH') THEN 'HIGH'
                     WHEN BOOL_OR(priority = 'MEDIUM') THEN 'MEDIUM' ELSE 'LOW' END AS priority,
                COUNT(*)::int AS opportunity_count,
                (ARRAY_AGG(opportunity_id ORDER BY potential_savings DESC, opportunity_id))[1]
                    AS lead_opportunity_id,
                MAX(snapshot_at) AS snapshot_at
            FROM facts
            WHERE product_id = :product_id
            GROUP BY product_id, product_name, equipment_family, category_id, category_name
        """), params).mappings().first()
        if not product:
            return None

        plants = db.execute(text(LATEST_FACTS_CTE + """
            SELECT plant_id, plant_code, plant_name, country,
                SUM(unit_cost * annual_volume) / NULLIF(SUM(annual_volume), 0) AS unit_cost,
                SUM(peer_average_cost * annual_volume) / NULLIF(SUM(annual_volume), 0) AS benchmark_cost,
                SUM(variance_amount * annual_volume)
                    / NULLIF(SUM(peer_average_cost * annual_volume), 0) * 100 AS variance_percent,
                SUM(potential_savings) AS potential_savings,
                COUNT(*)::int AS opportunity_count
            FROM facts
            WHERE product_id = :product_id
            GROUP BY plant_id, plant_code, plant_name, country
            ORDER BY potential_savings DESC, plant_id
        """), params).mappings().all()

        components = db.execute(text(LATEST_FACTS_CTE + """
            SELECT component_id, component_name, part_classification,
                SUM(potential_savings) AS potential_savings,
                SUM(variance_amount * annual_volume)
                    / NULLIF(SUM(peer_average_cost * annual_volume), 0) * 100 AS variance_percent,
                AVG(confidence_score) AS confidence_score,
                COUNT(*)::int AS opportunity_count,
                (ARRAY_AGG(opportunity_id ORDER BY potential_savings DESC, opportunity_id))[1]
                    AS lead_opportunity_id
            FROM facts
            WHERE product_id = :product_id
            GROUP BY component_id, component_name, part_classification
            ORDER BY potential_savings DESC, component_id
        """), params).mappings().all()

        result = dict(product)
        result["plants"] = [dict(row) for row in plants]
        result["components"] = [dict(row) for row in components]
        result["highest_cost_plant"] = max(
            plants, key=lambda row: row["unit_cost"], default=None
        )["plant_name"] if plants else None
        result["lowest_cost_plant"] = min(
            plants, key=lambda row: row["unit_cost"], default=None
        )["plant_name"] if plants else None
        return result

    def get_product_trend(self, db: Connection, *, product_id: str,
                          as_of_date: date, region: str | None = None,
                          plant_id: str | None = None) -> list[dict[str, Any]]:
        params = self._params(as_of_date, region, plant_id, product_id)
        rows = db.execute(text("""
            WITH primary_product AS (
                SELECT DISTINCT ON (pc.part_id)
                    pc.part_id, em.id AS product_id
                FROM catalog.part_compatibility pc
                JOIN catalog.equipment_models em ON em.id = pc.equipment_model_id
                ORDER BY pc.part_id,
                    CASE pc.compatibility_type WHEN 'PRIMARY' THEN 0 ELSE 1 END,
                    em.id
            )
            SELECT pl.id AS plant_id, pl.name AS plant_name,
                date_trunc('month', m.snapshot_at)::date AS period_start,
                SUM(m.unit_cost * m.annual_volume) / NULLIF(SUM(m.annual_volume), 0) AS unit_cost,
                SUM(m.peer_average_cost * m.annual_volume)
                    / NULLIF(SUM(m.annual_volume), 0) AS benchmark_cost
            FROM opportunity.metric_snapshots m
            JOIN opportunity.opportunities o ON o.id = m.opportunity_id
            JOIN primary_product pp ON pp.part_id = o.part_id
            JOIN supply.plants pl ON pl.id = o.plant_id
            WHERE pp.product_id = :product_id
              AND m.snapshot_at <= :as_of_date
              AND (CAST(:region AS text) IS NULL OR pl.region = CAST(:region AS text))
              AND (CAST(:plant_id AS text) IS NULL OR pl.id = CAST(:plant_id AS text))
            GROUP BY pl.id, pl.name, date_trunc('month', m.snapshot_at)::date
            ORDER BY pl.id, period_start
        """), params).mappings().all()
        series: dict[str, dict[str, Any]] = {}
        for row in rows:
            current = series.setdefault(row["plant_id"], {
                "plant_id": row["plant_id"], "plant_name": row["plant_name"], "points": [],
            })
            current["points"].append({
                "period_start": row["period_start"], "unit_cost": row["unit_cost"],
                "benchmark_cost": row["benchmark_cost"],
            })
        return list(series.values())

    def get_component_detail(self, db: Connection, *, component_id: str,
                             as_of_date: date, region: str | None = None,
                             plant_id: str | None = None,
                             product_id: str | None = None,
                             category_id: str | None = None) -> dict[str, Any] | None:
        params = self._params(as_of_date, region, plant_id, product_id, category_id) | {"component_id": component_id}
        component = db.execute(text(LATEST_FACTS_CTE + """
            , snapshot_bounds AS (
                SELECT o.id AS opportunity_id,
                    (ARRAY_AGG(ms.annual_volume ORDER BY ms.snapshot_at))[1] AS opening_volume
                FROM opportunity.opportunities o
                JOIN opportunity.metric_snapshots ms ON ms.opportunity_id = o.id
                JOIN catalog.parts part ON part.id = o.part_id
                WHERE part.component_id = :component_id
                  AND ms.snapshot_at <= :as_of_date
                GROUP BY o.id
            ), tariff AS (
                SELECT o.id AS opportunity_id,
                    td.import_duty_per_unit, td.peer_duty_per_unit, td.annual_duty_impact,
                    td.duty_rate, td.peer_average_duty_rate, td.hs_code
                FROM opportunity.opportunities o
                JOIN catalog.parts part ON part.id = o.part_id
                JOIN opportunity.tariff_details td ON td.opportunity_id = o.id
                WHERE part.component_id = :component_id
            )
            SELECT f.component_id, f.component_name, f.part_classification,
                SUM(f.potential_savings) AS annual_opportunity,
                SUM(f.annual_spend) AS annual_spend,
                SUM(f.annual_volume)::int AS annual_volume,
                (SUM(f.annual_volume) - SUM(sb.opening_volume))
                    / NULLIF(SUM(sb.opening_volume), 0) * 100 AS volume_change_percent,
                AVG(f.confidence_score) AS confidence_score,
                SUM(f.variance_amount * f.annual_volume)
                    / NULLIF(SUM(f.peer_average_cost * f.annual_volume), 0) * 100 AS variance_percent,
                SUM(t.annual_duty_impact) AS annual_tariff_impact,
                SUM(t.import_duty_per_unit * f.annual_volume)
                    / NULLIF(SUM(f.annual_volume), 0) AS tariff_per_unit,
                AVG(t.duty_rate) AS duty_rate,
                AVG(t.peer_average_duty_rate) AS peer_duty_rate,
                MIN(t.hs_code) AS hs_code,
                COUNT(*)::int AS opportunity_count,
                (ARRAY_AGG(f.opportunity_id ORDER BY f.potential_savings DESC, f.opportunity_id))[1]
                    AS lead_opportunity_id,
                (ARRAY_AGG(f.plant_name ORDER BY f.potential_savings DESC, f.plant_name))[1]
                    AS lead_plant,
                (ARRAY_AGG(f.priority ORDER BY f.potential_savings DESC, f.opportunity_id))[1]
                    AS priority
            FROM facts f
            JOIN snapshot_bounds sb ON sb.opportunity_id = f.opportunity_id
            LEFT JOIN tariff t ON t.opportunity_id = f.opportunity_id
            WHERE f.component_id = :component_id
            GROUP BY f.component_id, f.component_name, f.part_classification
        """), params).mappings().first()
        if not component:
            return None

        suppliers = db.execute(text("""
            WITH latest_economic AS (
                SELECT DISTINCT ON (ef.part_id, ef.plant_id, ef.supplier_id)
                    ef.part_id, ef.plant_id, ef.supplier_id, ef.unit_cost,
                    ef.purchase_volume, ef.total_spend, ef.period_start
                FROM economics.part_economic_fact ef
                WHERE ef.period_start <= :as_of_date
                ORDER BY ef.part_id, ef.plant_id, ef.supplier_id, ef.period_start DESC
            )
            SELECT s.id AS supplier_id, s.name AS supplier_name, s.country,
                BOOL_OR(ps.is_primary_supplier) AS is_primary_supplier,
                SUM(le.unit_cost * le.purchase_volume)
                    / NULLIF(SUM(le.purchase_volume), 0) AS unit_cost,
                SUM(le.purchase_volume)::int AS annual_volume,
                SUM(le.total_spend) AS annual_spend,
                AVG(s.quality_score) AS quality_score,
                AVG(s.delivery_score) AS delivery_score,
                AVG(s.overall_score) AS overall_score
            FROM catalog.parts p
            JOIN supply.part_supply ps ON ps.part_id = p.id
            JOIN supply.suppliers s ON s.id = ps.supplier_id
            JOIN latest_economic le ON le.part_id = ps.part_id
                AND le.plant_id = ps.plant_id AND le.supplier_id = ps.supplier_id
            JOIN supply.plants pl ON pl.id = ps.plant_id
            WHERE p.component_id = :component_id
              AND (CAST(:region AS text) IS NULL OR pl.region = CAST(:region AS text))
              AND (CAST(:plant_id AS text) IS NULL OR pl.id = CAST(:plant_id AS text))
            GROUP BY s.id, s.name, s.country
            ORDER BY is_primary_supplier DESC, unit_cost, s.id
        """), params).mappings().all()

        products = db.execute(text("""
            SELECT DISTINCT em.id AS product_id,
                em.equipment_family || ' ' || em.model_code AS product_name
            FROM catalog.parts p
            JOIN catalog.part_compatibility pc ON pc.part_id = p.id
            JOIN catalog.equipment_models em ON em.id = pc.equipment_model_id
            WHERE p.component_id = :component_id
            ORDER BY product_name
        """), params).mappings().all()

        result = dict(component)
        result["suppliers"] = [dict(row) for row in suppliers]
        result["products"] = [dict(row) for row in products]
        primary = next((row for row in suppliers if row["is_primary_supplier"]), None)
        alternate = min((row for row in suppliers if not row["is_primary_supplier"]),
                        key=lambda row: row["unit_cost"], default=None)
        result["current_supplier"] = primary["supplier_name"] if primary else None
        result["benchmark_supplier"] = alternate["supplier_name"] if alternate else None
        result["current_supplier_unit_cost"] = primary["unit_cost"] if primary else None
        result["benchmark_supplier_unit_cost"] = alternate["unit_cost"] if alternate else None
        result["supplier_delta_percent"] = (
            (primary["unit_cost"] - alternate["unit_cost"]) / alternate["unit_cost"] * 100
            if primary and alternate and alternate["unit_cost"] else None
        )
        result["commercial_delta"] = (
            primary["unit_cost"] - alternate["unit_cost"]
            if primary and alternate else None
        )
        return result

    def get_equipment_categories(self, db: Connection, *, as_of_date: date,
                                 region: str | None = None,
                                 plant_id: str | None = None,
                                 product_id: str | None = None,
                                 category_id: str | None = None) -> list[dict[str, Any]]:
        params = self._params(as_of_date, region, plant_id, product_id, category_id)
        rows = db.execute(text(LATEST_FACTS_CTE + """
            , driver_totals AS (
                SELECT f.category_id, cd.driver_name,
                    SUM(cd.impact_amount * f.annual_volume) AS impact
                FROM facts f
                JOIN opportunity.cost_drivers cd ON cd.opportunity_id = f.opportunity_id
                GROUP BY f.category_id, cd.driver_name
            ), primary_drivers AS (
                SELECT DISTINCT ON (category_id) category_id, driver_name
                FROM driver_totals
                ORDER BY category_id, impact DESC, driver_name
            ), category_model_counts AS (
                SELECT category_id, COUNT(*)::int AS product_count
                FROM catalog.equipment_models
                GROUP BY category_id
            )
            SELECT f.category_id, f.category_name,
                cmc.product_count,
                SUM(f.annual_spend) AS annual_spend,
                SUM(f.potential_savings) AS potential_savings,
                SUM(f.variance_amount * f.annual_volume)
                    / NULLIF(SUM(f.peer_average_cost * f.annual_volume), 0) * 100
                    AS cost_variance_percent,
                COUNT(*) FILTER (WHERE f.priority = 'HIGH')::int
                    AS high_priority_opportunities,
                AVG(f.confidence_score) AS confidence,
                pd.driver_name AS primary_opportunity_driver,
                CASE WHEN COUNT(*) FILTER (WHERE f.priority = 'HIGH') > 0 THEN 'HIGH'
                     WHEN MAX(f.variance_percent) >= 10 THEN 'MEDIUM' ELSE 'WATCH' END AS priority
            FROM facts f
            JOIN category_model_counts cmc ON cmc.category_id = f.category_id
            LEFT JOIN primary_drivers pd ON pd.category_id = f.category_id
            WHERE f.category_id IS NOT NULL
            GROUP BY f.category_id, f.category_name, cmc.product_count, pd.driver_name
            ORDER BY potential_savings DESC, f.category_id
        """), params).mappings().all()
        return [dict(row) for row in rows]

    def get_cost_drivers(self, db: Connection, *, as_of_date: date,
                         region: str | None = None, plant_id: str | None = None,
                         product_id: str | None = None,
                         category_id: str | None = None) -> dict[str, Any]:
        params = self._params(as_of_date, region, plant_id, product_id, category_id)
        rows = db.execute(text(LATEST_FACTS_CTE + """
            , portfolio AS (
                SELECT
                    SUM(peer_average_cost * annual_volume)
                        / NULLIF(SUM(annual_volume), 0) AS benchmark_cost,
                    SUM(variance_amount * annual_volume)
                        / NULLIF(SUM(annual_volume), 0) AS overall_gap,
                    SUM(annual_volume) AS total_volume
                FROM facts
            ), driver_totals AS (
                SELECT cd.driver_code, cd.driver_name,
                    SUM(cd.impact_amount * f.annual_volume) AS annualized_gap
                FROM facts f
                JOIN opportunity.cost_drivers cd
                    ON cd.opportunity_id = f.opportunity_id
                GROUP BY cd.driver_code, cd.driver_name
            ), explained AS (
                SELECT SUM(annualized_gap) AS total_gap FROM driver_totals
            )
            SELECT dt.driver_code,
                dt.driver_name,
                p.benchmark_cost,
                p.benchmark_cost
                    + dt.annualized_gap / NULLIF(p.total_volume, 0) AS comparison_cost,
                dt.annualized_gap / NULLIF(p.total_volume, 0) AS gap,
                dt.annualized_gap / NULLIF(e.total_gap, 0) * 100 AS contribution_percent
            FROM driver_totals dt
            CROSS JOIN portfolio p
            CROSS JOIN explained e
            ORDER BY dt.annualized_gap DESC, dt.driver_code
        """), params).mappings().all()
        items = [dict(row) for row in rows]
        return {
            "overall_gap": sum((row["gap"] for row in items), 0),
            "contribution_total": sum((row["contribution_percent"] for row in items), 0),
            "drivers": items,
        }

    def get_products_awaiting_decision(self, db: Connection, *, as_of_date: date,
                                       region: str | None = None,
                                       plant_id: str | None = None,
                                       product_id: str | None = None,
                                       category_id: str | None = None,
                                       limit: int = 5) -> list[dict[str, Any]]:
        params = self._params(as_of_date, region, plant_id, product_id, category_id) | {"limit": limit}
        rows = db.execute(text(LATEST_FACTS_CTE + """
            SELECT product_id, product_name,
                SUM(potential_savings) AS potential_savings,
                COUNT(*)::int AS opportunity_count,
                MAX(confidence_score) AS confidence
            FROM facts
            WHERE product_id IS NOT NULL
              AND status IN ('AWAITING_REVIEW', 'SUBMITTED_FOR_DECISION')
            GROUP BY product_id, product_name
            ORDER BY potential_savings DESC, product_id
            LIMIT :limit
        """), params).mappings().all()
        return [dict(row) for row in rows]


executive_repository = ExecutiveRepository()
