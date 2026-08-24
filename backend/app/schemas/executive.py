from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ExecutiveEntitySummary(BaseModel):
    id: str
    name: str
    potential_savings: Decimal
    variance_percent: Decimal
    opportunity_count: int


class ExecutiveSummaryResponse(BaseModel):
    as_of_date: date
    top_plant: ExecutiveEntitySummary | None
    top_product: ExecutiveEntitySummary | None
    top_category: ExecutiveEntitySummary | None
    top_component: ExecutiveEntitySummary | None
    total_potential_savings: Decimal
    opportunity_count: int


class QuickWin(BaseModel):
    rank: int
    title: str
    potential_savings: Decimal
    ease: str
    confidence: Decimal
    urgency: str
    why_now: str
    opportunity_id: str


class QuickWinsResponse(BaseModel):
    as_of_date: date
    items: list[QuickWin]


class PlantExecutiveItem(BaseModel):
    plant_id: str
    plant_code: str
    plant_name: str
    country: str
    unit_cost: Decimal
    variance_percent: Decimal
    potential_savings: Decimal
    attention_level: str
    primary_driver: str | None
    benchmark_status: str
    opportunity_count: int


class PlantsExecutiveResponse(BaseModel):
    as_of_date: date
    items: list[PlantExecutiveItem]


class ProductExecutiveItem(BaseModel):
    product_id: str
    product_name: str
    equipment_family: str
    average_unit_cost: Decimal
    highest_cost_plant: str | None
    lowest_cost_plant: str | None
    variance_percent: Decimal
    potential_savings: Decimal
    priority: str
    opportunity_count: int


class ProductsExecutiveResponse(BaseModel):
    as_of_date: date
    attribution_policy: str = Field(
        default="PRIMARY_COMPATIBLE_MODEL",
        description="Each part is assigned to one stable equipment model for portfolio aggregation.",
    )
    items: list[ProductExecutiveItem]


class ProductPlantItem(BaseModel):
    plant_id: str
    plant_code: str
    plant_name: str
    country: str
    unit_cost: Decimal
    benchmark_cost: Decimal
    variance_percent: Decimal
    potential_savings: Decimal
    opportunity_count: int


class ProductComponentItem(BaseModel):
    component_id: str
    component_name: str
    category: str
    potential_savings: Decimal
    variance_percent: Decimal
    confidence_score: Decimal
    opportunity_count: int
    lead_opportunity_id: str


class ProductDetailResponse(BaseModel):
    as_of_date: date
    product_id: str
    product_name: str
    equipment_family: str
    average_unit_cost: Decimal
    benchmark_unit_cost: Decimal
    variance_amount: Decimal
    variance_percent: Decimal
    annual_volume: int
    annual_spend: Decimal
    potential_savings: Decimal
    confidence_score: Decimal
    priority: str
    opportunity_count: int
    lead_opportunity_id: str
    snapshot_at: datetime
    highest_cost_plant: str | None
    lowest_cost_plant: str | None
    plants: list[ProductPlantItem]
    components: list[ProductComponentItem]


class ProductTrendPoint(BaseModel):
    period_start: date
    unit_cost: Decimal
    benchmark_cost: Decimal


class ProductTrendSeries(BaseModel):
    plant_id: str
    plant_name: str
    points: list[ProductTrendPoint]


class ProductTrendResponse(BaseModel):
    as_of_date: date
    product_id: str
    series: list[ProductTrendSeries]


class ComponentSupplierItem(BaseModel):
    supplier_id: str
    supplier_name: str
    country: str
    is_primary_supplier: bool
    unit_cost: Decimal
    annual_volume: int
    annual_spend: Decimal
    quality_score: Decimal
    delivery_score: Decimal
    overall_score: Decimal


class ComponentProductItem(BaseModel):
    product_id: str
    product_name: str


class ComponentDetailResponse(BaseModel):
    as_of_date: date
    component_id: str
    component_name: str
    category: str
    annual_opportunity: Decimal
    annual_spend: Decimal
    annual_volume: int
    volume_change_percent: Decimal
    confidence_score: Decimal
    variance_percent: Decimal
    annual_tariff_impact: Decimal
    tariff_per_unit: Decimal
    duty_rate: Decimal
    peer_duty_rate: Decimal
    hs_code: str
    opportunity_count: int
    lead_opportunity_id: str
    lead_plant: str
    priority: str
    current_supplier: str | None
    benchmark_supplier: str | None
    current_supplier_unit_cost: Decimal | None
    benchmark_supplier_unit_cost: Decimal | None
    supplier_delta_percent: Decimal | None
    commercial_delta: Decimal | None
    suppliers: list[ComponentSupplierItem]
    products: list[ComponentProductItem]


class CategoryExecutiveItem(BaseModel):
    category_code: str
    category: str
    benchmark_cost: Decimal
    comparison_cost: Decimal
    gap: Decimal
    contribution_percent: Decimal


class CategoriesExecutiveResponse(BaseModel):
    as_of_date: date
    overall_gap: Decimal
    contribution_total: Decimal
    items: list[CategoryExecutiveItem]


class ExecutiveReportResponse(BaseModel):
    as_of_date: date
    period: str | None
    scope: str
    summary: ExecutiveSummaryResponse
    plants: list[PlantExecutiveItem]
    products: list[ProductExecutiveItem]
    quick_wins: list[QuickWin]
