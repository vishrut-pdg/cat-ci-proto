from typing import Any

from app.recsys.config import (
    ELIGIBLE_STATUSES,
    MIN_CONFIDENCE_SCORE,
    MIN_POTENTIAL_SAVINGS,
)


def is_candidate_eligible(
    candidate: dict[str, Any],
) -> tuple[bool, str | None]:

    if candidate["status"] not in ELIGIBLE_STATUSES:
        return (
            False,
            "STATUS_NOT_ELIGIBLE",
        )

    if (
        float(candidate["potential_savings"])
        < MIN_POTENTIAL_SAVINGS
    ):
        return (
            False,
            "SAVINGS_BELOW_THRESHOLD",
        )

    if (
        float(candidate["confidence_score"])
        < MIN_CONFIDENCE_SCORE
    ):
        return (
            False,
            "LOW_DATA_CONFIDENCE",
        )

    if float(candidate["peer_average_cost"]) <= 0:
        return (
            False,
            "INVALID_PEER_BENCHMARK",
        )

    return True, None