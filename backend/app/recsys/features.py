from typing import Any


def clamp(
    value: float,
    low: float = 0.0,
    high: float = 1.0,
) -> float:
    return max(
        low,
        min(high, value),
    )


def normalize_candidate_features(
    candidate: dict[str, Any],
    *,
    max_potential_savings: float,
) -> dict[str, float]:

    potential_savings = float(
        candidate["potential_savings"]
    )

    variance_percent = abs(
        float(candidate["variance_percent"])
    )

    impact_score = float(
        candidate["impact_score"]
    )

    confidence_score = float(
        candidate["confidence_score"]
    )

    logistics_variance_percent = max(
        0.0,
        float(
            candidate[
                "logistics_variance_percent"
            ]
            or 0
        ),
    )

    tariff_variance_percent = max(
        0.0,
        float(
            candidate[
                "tariff_variance_percent"
            ]
            or 0
        ),
    )

    return {
        "potential_savings": clamp(
            potential_savings
            / max(max_potential_savings, 1)
        ),

        # 25% cost variance is considered
        # severe enough to saturate the feature.
        "cost_variance": clamp(
            variance_percent / 25
        ),

        "impact_score": clamp(
            impact_score / 100
        ),

        # 60%+ logistics variance saturates.
        "logistics_variance": clamp(
            logistics_variance_percent / 60
        ),

        # 100%+ tariff variance saturates.
        "tariff_variance": clamp(
            tariff_variance_percent / 100
        ),

        "data_confidence": clamp(
            confidence_score
        ),
    }