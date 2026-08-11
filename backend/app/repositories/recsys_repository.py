from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection


class RecSysRepository:

    # ========================================================
    # CANDIDATES
    # ========================================================

    def get_candidates(
        self,
        db: Connection,
    ) -> list[dict[str, Any]]:

        query = text(
            """
            SELECT
                o.id AS opportunity_id,
                o.status,
                o.priority,

                p.part_number,
                p.component_id,
                p.name AS part_name,
                p.category,
                p.part_family,

                pl.plant_code,
                pl.name AS plant_name,
                pl.country,

                m.unit_cost,
                m.peer_average_cost,
                m.variance_amount,
                m.variance_percent,

                m.annual_volume,
                m.annual_spend,

                m.potential_savings,
                m.impact_score,
                m.confidence_score,

                COALESCE(
                    logistics.variance_percent,
                    0
                ) AS logistics_variance_percent,

                COALESCE(
                    tariff.variance_percent,
                    0
                ) AS tariff_variance_percent

            FROM opportunity.opportunities o

            JOIN catalog.parts p
                ON p.id = o.part_id

            JOIN supply.plants pl
                ON pl.id = o.plant_id

            JOIN opportunity.metric_snapshots m
                ON m.opportunity_id = o.id

            LEFT JOIN LATERAL (
                SELECT
                    CASE
                        WHEN
                            SUM(peer_average_cost) > 0
                        THEN
                            (
                                (
                                    SUM(brazil_cost)
                                    -
                                    SUM(peer_average_cost)
                                )
                                /
                                SUM(peer_average_cost)
                            ) * 100
                        ELSE 0
                    END AS variance_percent

                FROM opportunity.logistics_components lc

                WHERE
                    lc.opportunity_id = o.id

            ) logistics
                ON TRUE

            LEFT JOIN LATERAL (
                SELECT
                    CASE
                        WHEN peer_duty_per_unit > 0
                        THEN
                            (
                                (
                                    import_duty_per_unit
                                    -
                                    peer_duty_per_unit
                                )
                                /
                                peer_duty_per_unit
                            ) * 100
                        ELSE 0
                    END AS variance_percent

                FROM opportunity.tariff_details td

                WHERE
                    td.opportunity_id = o.id

                LIMIT 1

            ) tariff
                ON TRUE

            ORDER BY
                m.potential_savings DESC
            """
        )

        result = db.execute(query)

        return [
            dict(row)
            for row
            in result.mappings().all()
        ]

    # ========================================================
    # RANKING RUN
    # ========================================================

    def create_ranking_run(
        self,
        db: Connection,
        *,
        run_id: str,
        model_name: str,
        model_version: str,
        feature_version: str,
    ) -> None:

        db.execute(
            text(
                """
                INSERT INTO recsys.ranking_runs (
                    id,
                    model_name,
                    model_version,
                    feature_version,
                    started_at,
                    completed_at
                )
                VALUES (
                    :id,
                    :model_name,
                    :model_version,
                    :feature_version,
                    NOW(),
                    NOW()
                )
                """
            ),
            {
                "id": run_id,
                "model_name": model_name,
                "model_version": model_version,
                "feature_version": feature_version,
            },
        )

    # ========================================================
    # RESULT
    # ========================================================

    def create_ranking_result(
        self,
        db: Connection,
        *,
        result_id: str,
        run_id: str,
        opportunity_id: str,
        final_score: float,
        confidence_score: float,
        rank_position: int,
    ) -> None:

        db.execute(
            text(
                """
                INSERT INTO recsys.ranking_results (
                    id,
                    ranking_run_id,
                    opportunity_id,
                    base_score,
                    confidence_score,
                    final_score,
                    rank_position
                )
                VALUES (
                    :id,
                    :ranking_run_id,
                    :opportunity_id,
                    :base_score,
                    :confidence_score,
                    :final_score,
                    :rank_position
                )
                """
            ),
            {
                "id": result_id,
                "ranking_run_id": run_id,
                "opportunity_id": (
                    opportunity_id
                ),
                "base_score": final_score,
                "confidence_score": (
                    confidence_score
                ),
                "final_score": final_score,
                "rank_position": rank_position,
            },
        )

    # ========================================================
    # SCORE COMPONENT
    # ========================================================

    def create_score_component(
        self,
        db: Connection,
        *,
        component_id: str,
        result_id: str,
        feature_name: str,
        raw_value: float,
        normalized_value: float,
        weight: float,
        contribution: float,
    ) -> None:

        db.execute(
            text(
                """
                INSERT INTO
                recsys.ranking_score_components (
                    id,
                    ranking_result_id,
                    feature_name,
                    raw_value,
                    normalized_value,
                    weight,
                    contribution
                )
                VALUES (
                    :id,
                    :ranking_result_id,
                    :feature_name,
                    :raw_value,
                    :normalized_value,
                    :weight,
                    :contribution
                )
                """
            ),
            {
                "id": component_id,
                "ranking_result_id": result_id,
                "feature_name": feature_name,
                "raw_value": raw_value,
                "normalized_value": (
                    normalized_value
                ),
                "weight": weight,
                "contribution": contribution,
            },
        )

    # ========================================================
    # EXPLANATION
    # ========================================================

    def create_explanation(
        self,
        db: Connection,
        *,
        explanation_id: str,
        result_id: str,
        reason_code: str,
        reason_rank: int,
        metric_name: str,
        metric_value: float,
        benchmark_value: float,
        explanation_text: str,
    ) -> None:

        db.execute(
            text(
                """
                INSERT INTO
                recsys.recommendation_explanations (
                    id,
                    ranking_result_id,
                    reason_code,
                    reason_rank,
                    metric_name,
                    metric_value,
                    benchmark_value,
                    explanation_text
                )
                VALUES (
                    :id,
                    :ranking_result_id,
                    :reason_code,
                    :reason_rank,
                    :metric_name,
                    :metric_value,
                    :benchmark_value,
                    :explanation_text
                )
                """
            ),
            {
                "id": explanation_id,
                "ranking_result_id": result_id,
                "reason_code": reason_code,
                "reason_rank": reason_rank,
                "metric_name": metric_name,
                "metric_value": metric_value,
                "benchmark_value": (
                    benchmark_value
                ),
                "explanation_text": (
                    explanation_text
                ),
            },
        )

    # ========================================================
    # READ RANKING
    # ========================================================

    def get_ranking_results(
        self,
        db: Connection,
        run_id: str,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:

        query = text(
            """
            SELECT
                    rr.id AS ranking_result_id,
                    rr.ranking_run_id,
                    rr.opportunity_id,
                    rr.final_score,
                    rr.rank_position,

                    o.status,
                    o.priority,

                    p.part_number,
                    p.component_id,
                    p.name AS part_name,

                    pl.plant_code,
                    pl.name AS plant_name,
                    pl.country,

                    m.potential_savings,
                    m.variance_percent,
                    m.confidence_score

                FROM recsys.ranking_results rr

                JOIN opportunity.opportunities o
                    ON o.id = rr.opportunity_id

                JOIN catalog.parts p
                    ON p.id = o.part_id

                JOIN supply.plants pl
                    ON pl.id = o.plant_id

                JOIN opportunity.metric_snapshots m
                    ON m.opportunity_id = o.id

                WHERE
                    rr.ranking_run_id = :run_id

                ORDER BY
                    rr.rank_position
                """
        )

        if limit is not None:
            query = text(f"{query.text} LIMIT :limit")

        result = db.execute(
            query,
            {
                "run_id": run_id,
                **({"limit": limit} if limit is not None else {}),
            },
        )

        return [
            dict(row)
            for row
            in result.mappings().all()
        ]
    def get_latest_run_id(
        self,
        db: Connection,
    ) -> str | None:

        result = db.execute(
            text(
                """
                SELECT id
                FROM recsys.ranking_runs
                ORDER BY completed_at DESC
                LIMIT 1
                """
            )
        )

        row = result.mappings().first()

        if row is None:
            return None

        return row["id"]


recsys_repository = RecSysRepository()