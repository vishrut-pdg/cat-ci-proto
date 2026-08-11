from typing import Any
from uuid import uuid4

from sqlalchemy.engine import Connection

from app.recsys.config import (
    FEATURE_VERSION,
    RANKING_MODEL_NAME,
    RANKING_MODEL_VERSION,
)
from app.recsys.explanations import build_explanations
from app.recsys.features import normalize_candidate_features
from app.recsys.filters import is_candidate_eligible
from app.recsys.ranker import rank_features
from app.repositories.recsys_repository import recsys_repository


# Maps the normalized ranking feature name
# back to the raw candidate/database field.
RAW_FEATURE_MAP = {
    "potential_savings": "potential_savings",
    "cost_variance": "variance_percent",
    "impact_score": "impact_score",
    "logistics_variance": "logistics_variance_percent",
    "tariff_variance": "tariff_variance_percent",
    "data_confidence": "confidence_score",
}


class RecSysService:

    # ========================================================
    # RUN A NEW RANKING
    # ========================================================

    def run_ranking(
        self,
        db: Connection,
    ) -> dict[str, Any]:

        # ----------------------------------------------------
        # 1. Load candidates
        # ----------------------------------------------------

        candidates = recsys_repository.get_candidates(
            db
        )

        eligible_candidates: list[
            dict[str, Any]
        ] = []

        rejected_candidates: list[
            dict[str, Any]
        ] = []

        # ----------------------------------------------------
        # 2. Apply eligibility filters
        # ----------------------------------------------------

        for candidate in candidates:

            eligible, reason = (
                is_candidate_eligible(
                    candidate
                )
            )

            if eligible:
                eligible_candidates.append(
                    candidate
                )
            else:
                rejected_candidates.append(
                    {
                        "opportunity_id": (
                            candidate[
                                "opportunity_id"
                            ]
                        ),
                        "reason": reason,
                    }
                )

        # Nothing eligible to rank.
        if not eligible_candidates:
            return {
                "run_id": None,
                "candidate_count": len(
                    candidates
                ),
                "eligible_count": 0,
                "ranked_count": 0,
                "items": [],
            }

        # ----------------------------------------------------
        # 3. Determine normalization ceiling
        # ----------------------------------------------------

        max_potential_savings = max(
            float(
                candidate[
                    "potential_savings"
                ]
            )
            for candidate
            in eligible_candidates
        )

        scored_candidates = []

        # ----------------------------------------------------
        # 4. Build features + calculate score
        # ----------------------------------------------------

        for candidate in eligible_candidates:

            features = (
                normalize_candidate_features(
                    candidate,
                    max_potential_savings=(
                        max_potential_savings
                    ),
                )
            )

            ranking = rank_features(
                features
            )

            explanations = (
                build_explanations(
                    candidate
                )
            )

            scored_candidates.append(
                {
                    "candidate": candidate,
                    "features": features,
                    "ranking": ranking,
                    "explanations": explanations,
                }
            )

        # ----------------------------------------------------
        # 5. Sort highest score first
        # ----------------------------------------------------

        scored_candidates.sort(
            key=lambda item: (
                item[
                    "ranking"
                ].final_score
            ),
            reverse=True,
        )

        # ----------------------------------------------------
        # 6. Create ranking run
        # ----------------------------------------------------

        run_id = (
            f"RANKRUN-"
            f"{uuid4().hex[:16]}"
        )

        response_items: list[
            dict[str, Any]
        ] = []

        try:

            recsys_repository.create_ranking_run(
                db,
                run_id=run_id,
                model_name=(
                    RANKING_MODEL_NAME
                ),
                model_version=(
                    RANKING_MODEL_VERSION
                ),
                feature_version=(
                    FEATURE_VERSION
                ),
            )

            # ------------------------------------------------
            # 7. Persist each ranked result
            # ------------------------------------------------

            for (
                rank_position,
                scored_item,
            ) in enumerate(
                scored_candidates,
                start=1,
            ):

                candidate = scored_item[
                    "candidate"
                ]

                ranking = scored_item[
                    "ranking"
                ]

                explanations = scored_item[
                    "explanations"
                ]

                result_id = (
                    f"RANKRES-"
                    f"{uuid4().hex[:16]}"
                )

                # --------------------------------------------
                # Ranking result
                # --------------------------------------------

                recsys_repository.create_ranking_result(
                    db,
                    result_id=result_id,
                    run_id=run_id,
                    opportunity_id=(
                        candidate[
                            "opportunity_id"
                        ]
                    ),
                    final_score=(
                        ranking.final_score
                    ),
                    confidence_score=float(
                        candidate[
                            "confidence_score"
                        ]
                    ),
                    rank_position=(
                        rank_position
                    ),
                )

                # --------------------------------------------
                # Score components
                # --------------------------------------------

                for component in (
                    ranking.components
                ):

                    raw_field = (
                        RAW_FEATURE_MAP[
                            component.feature_name
                        ]
                    )

                    raw_value = float(
                        candidate.get(
                            raw_field
                        )
                        or 0
                    )

                    component_id = (
                        f"RSCORE-"
                        f"{uuid4().hex[:16]}"
                    )

                    recsys_repository.create_score_component(
                        db,
                        component_id=(
                            component_id
                        ),
                        result_id=result_id,
                        feature_name=(
                            component.feature_name
                        ),
                        raw_value=(
                            raw_value
                        ),
                        normalized_value=(
                            component
                            .normalized_value
                        ),
                        weight=(
                            component.weight
                        ),
                        contribution=(
                            component.contribution
                        ),
                    )

                # --------------------------------------------
                # Explanation reasons
                # --------------------------------------------

                for (
                    reason_rank,
                    explanation,
                ) in enumerate(
                    explanations,
                    start=1,
                ):

                    explanation_id = (
                        f"EXPL-"
                        f"{uuid4().hex[:16]}"
                    )

                    recsys_repository.create_explanation(
                        db,
                        explanation_id=(
                            explanation_id
                        ),
                        result_id=result_id,
                        reason_code=(
                            explanation[
                                "reason_code"
                            ]
                        ),
                        reason_rank=(
                            reason_rank
                        ),
                        metric_name=(
                            explanation[
                                "metric_name"
                            ]
                        ),
                        metric_value=float(
                            explanation[
                                "metric_value"
                            ]
                        ),
                        benchmark_value=float(
                            explanation.get(
                                "benchmark_value"
                            )
                            or 0
                        ),
                        explanation_text=(
                            explanation[
                                "explanation_text"
                            ]
                        ),
                    )

                # --------------------------------------------
                # API response object
                # --------------------------------------------

                response_items.append(
                    {
                        "opportunity_id": (
                            candidate[
                                "opportunity_id"
                            ]
                        ),
                        "part_number": (
                            candidate[
                                "part_number"
                            ]
                        ),
                        "part_name": (
                            candidate[
                                "part_name"
                            ]
                        ),
                        "plant_code": (
                            candidate[
                                "plant_code"
                            ]
                        ),
                        "plant_name": (
                            candidate[
                                "plant_name"
                            ]
                        ),
                        "country": (
                            candidate[
                                "country"
                            ]
                        ),
                        "potential_savings": float(
                            candidate[
                                "potential_savings"
                            ]
                        ),
                        "confidence_score": float(
                            candidate[
                                "confidence_score"
                            ]
                        ),

                        # Database stores 0 -> 1.
                        # API exposes 0 -> 100.
                        "final_score": round(
                            ranking.final_score
                            * 100,
                            2,
                        ),

                        "rank": (
                            rank_position
                        ),

                        "reasons": [
                            explanation[
                                "explanation_text"
                            ]
                            for explanation
                            in explanations
                        ],
                    }
                )

            # Everything in the ranking run should
            # succeed or fail together.
            db.commit()

        except Exception:
            db.rollback()
            raise

        return {
            "run_id": run_id,

            "candidate_count": len(
                candidates
            ),

            "eligible_count": len(
                eligible_candidates
            ),

            "ranked_count": len(
                response_items
            ),

            "items": response_items,
        }

    # ========================================================
    # GET LATEST RANKING
    # ========================================================

    def get_latest_recommendations(
        self,
        db: Connection,
        *,
        limit: int = 50,
    ) -> dict[str, Any]:

        # ----------------------------------------------------
        # 1. Get most recent ranking run
        # ----------------------------------------------------

        run_id = (
            recsys_repository
            .get_latest_run_id(
                db
            )
        )

        if run_id is None:
            return {
                "run_id": None,
                "candidate_count": 0,
                "eligible_count": 0,
                "ranked_count": 0,
                "items": [],
            }

        # ----------------------------------------------------
        # 2. Read ranking results
        # ----------------------------------------------------

        rows = (
            recsys_repository
            .get_ranking_results(
                db,
                run_id,
                limit=limit,
            )
        )

        # ----------------------------------------------------
        # 3. Transform DB rows to API objects
        # ----------------------------------------------------

        items: list[
            dict[str, Any]
        ] = []

        for row in rows:

            reasons = row.get(
                "reasons"
            )

            if reasons is None:
                reasons = []

            items.append(
                {
                    "opportunity_id": (
                        row[
                            "opportunity_id"
                        ]
                    ),

                    "part_number": (
                        row[
                            "part_number"
                        ]
                    ),

                    "part_name": (
                        row[
                            "part_name"
                        ]
                    ),

                    "plant_code": (
                        row[
                            "plant_code"
                        ]
                    ),

                    "plant_name": (
                        row[
                            "plant_name"
                        ]
                    ),

                    "country": (
                        row[
                            "country"
                        ]
                    ),

                    "potential_savings": float(
                        row[
                            "potential_savings"
                        ]
                    ),

                    "confidence_score": float(
                        row[
                            "confidence_score"
                        ]
                    ),

                    # Stored in DB as 0 -> 1.
                    # Returned to frontend as percentage.
                    "final_score": round(
                        float(
                            row[
                                "final_score"
                            ]
                        )
                        * 100,
                        2,
                    ),

                    "rank": int(
                        row[
                            "rank_position"
                        ]
                    ),

                    "reasons": (
                        reasons
                    ),
                }
            )

        return {
            "run_id": run_id,

            "candidate_count": len(
                items
            ),

            "eligible_count": len(
                items
            ),

            "ranked_count": len(
                items
            ),

            "items": items,
        }


recsys_service = RecSysService()