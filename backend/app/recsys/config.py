RANKING_MODEL_NAME = "weighted-opportunity-ranker"
RANKING_MODEL_VERSION = "v1.0.0"
FEATURE_VERSION = "features-v1"


RANKING_WEIGHTS = {
    "potential_savings": 0.25,
    "cost_variance": 0.20,
    "impact_score": 0.15,
    "logistics_variance": 0.15,
    "tariff_variance": 0.10,
    "data_confidence": 0.15,
}


ELIGIBLE_STATUSES = {
    "IDENTIFIED",
    "AWAITING_REVIEW",
}


MIN_POTENTIAL_SAVINGS = 50_000
MIN_CONFIDENCE_SCORE = 0.65