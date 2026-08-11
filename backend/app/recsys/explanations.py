from typing import Any


def build_explanations(
    candidate: dict[str, Any],
) -> list[dict]:

    explanations: list[dict] = []

    variance_percent = float(
        candidate["variance_percent"]
    )

    if variance_percent >= 10:
        explanations.append(
            {
                "reason_code": (
                    "HIGH_UNIT_COST"
                ),
                "metric_name": (
                    "variance_percent"
                ),
                "metric_value": (
                    variance_percent
                ),
                "benchmark_value": 0,
                "explanation_text": (
                    f"Unit cost is "
                    f"{variance_percent:.1f}% "
                    "above the peer benchmark."
                ),
            }
        )

    logistics_variance = float(
        candidate[
            "logistics_variance_percent"
        ]
        or 0
    )

    if logistics_variance >= 20:
        explanations.append(
            {
                "reason_code": (
                    "HIGH_LOGISTICS_COST"
                ),
                "metric_name": (
                    "logistics_variance_percent"
                ),
                "metric_value": (
                    logistics_variance
                ),
                "benchmark_value": 0,
                "explanation_text": (
                    "Logistics cost is "
                    f"{logistics_variance:.1f}% "
                    "above the peer benchmark."
                ),
            }
        )

    tariff_variance = float(
        candidate[
            "tariff_variance_percent"
        ]
        or 0
    )

    if tariff_variance >= 25:
        explanations.append(
            {
                "reason_code": (
                    "HIGH_IMPORT_DUTY"
                ),
                "metric_name": (
                    "tariff_variance_percent"
                ),
                "metric_value": (
                    tariff_variance
                ),
                "benchmark_value": 0,
                "explanation_text": (
                    "Import duty cost is "
                    f"{tariff_variance:.1f}% "
                    "above the peer benchmark."
                ),
            }
        )

    potential_savings = float(
        candidate["potential_savings"]
    )

    if potential_savings >= 250_000:
        explanations.append(
            {
                "reason_code": (
                    "HIGH_SAVINGS_POTENTIAL"
                ),
                "metric_name": (
                    "potential_savings"
                ),
                "metric_value": (
                    potential_savings
                ),
                "benchmark_value": 250_000,
                "explanation_text": (
                    "Estimated annual savings "
                    f"potential is "
                    f"${potential_savings:,.0f}."
                ),
            }
        )

    return explanations[:3]