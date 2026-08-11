from pydantic import BaseModel


class RankedOpportunity(BaseModel):
    opportunity_id: str

    part_number: str
    part_name: str

    plant_code: str
    plant_name: str
    country: str

    potential_savings: float
    confidence_score: float

    final_score: float
    rank: int

    reasons: list[str]


class RankingResponse(BaseModel):
    run_id: str | None

    candidate_count: int
    eligible_count: int
    ranked_count: int

    items: list[RankedOpportunity]