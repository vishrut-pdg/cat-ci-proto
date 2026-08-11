from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.engine import Connection

from app.db.session import get_db
from app.schemas.opportunity import (
    LogisticsResponse,
    OpportunityDetailResponse,
    OpportunityListItem,
    OpportunityListResponse,
    OverviewResponse,
    PlantsResponse,
    SuppliersResponse,
    TariffResponse,
)
from app.services.opportunity_service import (
    opportunity_service,
)


router = APIRouter(
    prefix="/opportunities",
    tags=["Opportunities"],
)


# ============================================================
# LIST
# ============================================================


@router.get(
    "",
    response_model=OpportunityListResponse,
)
def list_opportunities(
    db: Annotated[
        Connection,
        Depends(get_db),
    ],
    status: str | None = Query(
        default=None,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
):
    rows = opportunity_service.list_opportunities(
        db,
        status=status,
        limit=limit,
        offset=offset,
    )

    return OpportunityListResponse(
        items=[
            OpportunityListItem(
                **row
            )
            for row in rows
        ],
        count=len(rows),
        limit=limit,
        offset=offset,
    )


# ============================================================
# DETAIL
# ============================================================


@router.get(
    "/{opportunity_id}",
    response_model=OpportunityDetailResponse,
)
def get_opportunity(
    opportunity_id: str,
    db: Annotated[
        Connection,
        Depends(get_db),
    ],
):
    result = (
        opportunity_service.get_opportunity(
            db,
            opportunity_id,
        )
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Opportunity not found",
        )

    return result


# ============================================================
# OVERVIEW
# ============================================================


@router.get(
    "/{opportunity_id}/overview",
    response_model=OverviewResponse,
)
def get_opportunity_overview(
    opportunity_id: str,
    db: Annotated[
        Connection,
        Depends(get_db),
    ],
):
    result = (
        opportunity_service.get_overview(
            db,
            opportunity_id,
        )
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Opportunity not found",
        )

    return result


# ============================================================
# PLANTS
# ============================================================


@router.get(
    "/{opportunity_id}/plants",
    response_model=PlantsResponse,
)
def get_opportunity_plants(
    opportunity_id: str,
    db: Annotated[
        Connection,
        Depends(get_db),
    ],
):
    result = (
        opportunity_service.get_plants(
            db,
            opportunity_id,
        )
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Opportunity not found",
        )

    return result


# ============================================================
# SUPPLIERS
# ============================================================


@router.get(
    "/{opportunity_id}/suppliers",
    response_model=SuppliersResponse,
)
def get_opportunity_suppliers(
    opportunity_id: str,
    db: Annotated[
        Connection,
        Depends(get_db),
    ],
):
    result = (
        opportunity_service.get_suppliers(
            db,
            opportunity_id,
        )
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Opportunity not found",
        )

    return result


# ============================================================
# LOGISTICS
# ============================================================


@router.get(
    "/{opportunity_id}/logistics",
    response_model=LogisticsResponse,
)
def get_opportunity_logistics(
    opportunity_id: str,
    db: Annotated[
        Connection,
        Depends(get_db),
    ],
):
    result = (
        opportunity_service.get_logistics(
            db,
            opportunity_id,
        )
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Opportunity not found",
        )

    return result


# ============================================================
# TARIFF
# ============================================================


@router.get(
    "/{opportunity_id}/tariff",
    response_model=TariffResponse,
)
def get_opportunity_tariff(
    opportunity_id: str,
    db: Annotated[
        Connection,
        Depends(get_db),
    ],
):
    result = (
        opportunity_service.get_tariff(
            db,
            opportunity_id,
        )
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Tariff data not found",
        )

    return result