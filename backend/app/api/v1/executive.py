from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.engine import Connection

from app.auth.demo_auth import require_role
from app.db.session import get_db
from app.schemas.executive import (
    CategoriesExecutiveResponse, ComponentDetailResponse, ExecutiveReportResponse, ExecutiveSummaryResponse, PlantsExecutiveResponse,
    ProductDetailResponse, ProductsExecutiveResponse, ProductTrendResponse, QuickWinsResponse,
)
from app.services.executive_service import executive_service
from app.services.report_storage import report_storage


router = APIRouter(
    prefix="/executive",
    tags=["Executive Guidance"],
    dependencies=[Depends(require_role("EXECUTIVE"))],
)


def common_filters(
    as_of_date: date | None = Query(default=None),
    period: str | None = Query(default=None),
    scope: str = Query(default="enterprise"),
    region: str | None = Query(default=None),
    plant_id: str | None = Query(default=None),
    product_id: str | None = Query(default=None),
) -> dict:
    return {"as_of_date": as_of_date, "period": period, "scope": scope,
            "region": region, "plant_id": plant_id, "product_id": product_id}


Filters = Annotated[dict, Depends(common_filters)]
Database = Annotated[Connection, Depends(get_db)]


def product_filters(
    as_of_date: date | None = Query(default=None),
    period: str | None = Query(default=None),
    scope: str = Query(default="enterprise"),
    region: str | None = Query(default=None),
    plant_id: str | None = Query(default=None),
) -> dict:
    return {"as_of_date": as_of_date, "period": period, "scope": scope,
            "region": region, "plant_id": plant_id}


ProductFilters = Annotated[dict, Depends(product_filters)]


def handle(call):
    try:
        return call()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/summary", response_model=ExecutiveSummaryResponse)
def summary(db: Database, filters: Filters):
    return handle(lambda: executive_service.summary(db, **filters))


@router.get("/quick-wins", response_model=QuickWinsResponse)
def quick_wins(db: Database, filters: Filters,
               limit: int = Query(default=3, ge=1, le=25)):
    return handle(lambda: executive_service.quick_wins(db, limit=limit, **filters))


@router.get("/plants", response_model=PlantsExecutiveResponse)
def plants(db: Database, filters: Filters):
    return handle(lambda: executive_service.plants(db, **filters))


@router.get("/products", response_model=ProductsExecutiveResponse)
def products(db: Database, filters: Filters):
    return handle(lambda: executive_service.products(db, **filters))


@router.get("/products/{product_id}", response_model=ProductDetailResponse)
def product_detail(product_id: str, db: Database, filters: ProductFilters):
    result = handle(lambda: executive_service.product_detail(db, product_id=product_id, **filters))
    if result is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return result


@router.get("/products/{product_id}/trend", response_model=ProductTrendResponse)
def product_trend(product_id: str, db: Database, filters: ProductFilters):
    result = handle(lambda: executive_service.product_trend(db, product_id=product_id, **filters))
    if result is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return result


@router.get("/products/{product_id}/cost-drivers", response_model=CategoriesExecutiveResponse)
def product_cost_drivers(product_id: str, db: Database, filters: ProductFilters):
    result = handle(lambda: executive_service.product_cost_drivers(db, product_id=product_id, **filters))
    if result is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return result


@router.get("/categories", response_model=CategoriesExecutiveResponse)
def categories(db: Database, filters: Filters):
    return handle(lambda: executive_service.categories(db, **filters))


@router.get("/components/{component_id}", response_model=ComponentDetailResponse)
def component_detail(component_id: str, db: Database, filters: Filters):
    result = handle(lambda: executive_service.component_detail(db, component_id=component_id, **filters))
    if result is None:
        raise HTTPException(status_code=404, detail="Component not found")
    return result


@router.get("/report", response_model=ExecutiveReportResponse)
def report(db: Database, filters: Filters):
    return handle(lambda: executive_service.report(db, **filters))


@router.get("/reports/{report_id}/download")
def download_report(report_id: str):
    try:
        content, file_name = report_storage.get_pdf(report_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Report not found") from exc
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )
