from dataclasses import dataclass

from app.recsys.config import (
    RANKING_WEIGHTS,
)


@dataclass
class RankingComponent:
    feature_name: str

    normalized_value: float
    weight: float
    contribution: float


@dataclass
class RankingScore:
    final_score: float
    components: list[RankingComponent]


def rank_features(
    features: dict[str, float],
) -> RankingScore:

    components: list[
        RankingComponent
    ] = []

    final_score = 0.0

    for (
        feature_name,
        weight,
    ) in RANKING_WEIGHTS.items():

        normalized_value = features[
            feature_name
        ]

        contribution = (
            normalized_value
            * weight
        )

        components.append(
            RankingComponent(
                feature_name=feature_name,
                normalized_value=round(
                    normalized_value,
                    6,
                ),
                weight=weight,
                contribution=round(
                    contribution,
                    6,
                ),
            )
        )

        final_score += contribution

    return RankingScore(
        final_score=round(
            final_score,
            6,
        ),
        components=components,
    )