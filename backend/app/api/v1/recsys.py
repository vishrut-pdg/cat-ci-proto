from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Query
)
from sqlalchemy.engine import Connection

from app.db.session import get_db
from app.schemas.recsys import (
    RankingResponse,
)
from app.services.recsys_service import (
    recsys_service,
)


router = APIRouter(
    prefix="/recsys",
    tags=["Recommendation System"],
)


@router.post(
    "/rank",
    response_model=RankingResponse,
)
def run_opportunity_ranking(
    db: Annotated[
        Connection,
        Depends(get_db),
    ],
):
    return recsys_service.run_ranking(
        db
    )

@router.get(
    "/recommendations",
    response_model=RankingResponse,
)
def get_recommendations(
    db: Annotated[
        Connection,
        Depends(get_db),
    ],
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
):
    return (
        recsys_service
        .get_latest_recommendations(
            db,
            limit=limit,
        )
    )