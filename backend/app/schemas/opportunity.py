from pydantic import BaseModel


# ============================================================
# LIST
# ============================================================


class OpportunityListItem(BaseModel):
    opportunity_id: str

    status: str
    priority: str

    part_number: str
    component_id: str

    part_name: str
    category: str
    part_family: str

    plant_code: str
    plant_name: str
    country: str

    unit_cost: float
    peer_average_cost: float

    variance_amount: float
    variance_percent: float

    potential_savings: float
    impact_score: float
    confidence_score: float


class OpportunityListResponse(BaseModel):
    items: list[OpportunityListItem]

    count: int
    limit: int
    offset: int


# ============================================================
# OPPORTUNITY DETAIL
# ============================================================


class PartDetail(BaseModel):
    part_id: str
    part_number: str
    component_id: str
    name: str
    category: str
    part_family: str
    part_type: str
    description: str | None = None


class PlantDetail(BaseModel):
    plant_id: str
    plant_code: str
    plant_name: str
    city: str
    country: str
    region: str
    currency: str


class OpportunityMetrics(BaseModel):
    unit_cost: float
    peer_average_cost: float
    variance_amount: float
    variance_percent: float

    annual_volume: int
    annual_spend: float

    potential_savings: float
    impact_score: float
    confidence_score: float


class OpportunityDetailResponse(BaseModel):
    opportunity_id: str
    opportunity_number: str

    status: str
    priority: str
    detection_source: str

    part: PartDetail
    plant: PlantDetail
    metrics: OpportunityMetrics


# ============================================================
# OVERVIEW
# ============================================================


class CostDriver(BaseModel):
    code: str
    name: str

    impact_amount: float
    impact_percent: float

    rank: int
    confidence_score: float

    explanation: str


class OverviewResponse(BaseModel):
    opportunity_id: str

    metrics: OpportunityMetrics

    cost_drivers: list[CostDriver]


# ============================================================
# PLANTS
# ============================================================


class PlantComparison(BaseModel):
    plant_id: str
    plant_code: str
    plant_name: str
    country: str

    unit_cost: float
    peer_average_cost: float

    variance_amount: float
    variance_percent: float

    annual_volume: int
    volume_variance_percent: float

    rank: int


class PlantsResponse(BaseModel):
    opportunity_id: str

    benchmark_type: str

    peer_average_cost: float

    plants: list[PlantComparison]


# ============================================================
# SUPPLIERS
# ============================================================


class SupplierComparison(BaseModel):
    supplier_id: str
    supplier_code: str
    supplier_name: str
    country: str

    unit_cost: float
    peer_average_cost: float

    variance_amount: float
    variance_percent: float

    annual_spend: float
    annual_volume: int

    quality_score: float
    delivery_score: float
    responsiveness_score: float
    overall_score: float

    rank: int


class SuppliersResponse(BaseModel):
    opportunity_id: str

    suppliers: list[SupplierComparison]


# ============================================================
# LOGISTICS
# ============================================================


class LogisticsComponent(BaseModel):
    code: str
    name: str

    cost: float
    peer_average: float

    variance: float
    variance_percent: float

    rank: int


class LogisticsTrendPoint(BaseModel):
    period: str

    actual_cost: float
    peer_average_cost: float


class LogisticsResponse(BaseModel):
    opportunity_id: str

    total_cost: float
    peer_average: float

    variance: float
    variance_percent: float

    components: list[LogisticsComponent]

    trend: list[LogisticsTrendPoint]


# ============================================================
# TARIFF
# ============================================================


class TariffPlantComparison(BaseModel):
    plant_id: str
    plant_code: str
    plant_name: str
    country: str

    duty_rate: float


class TariffResponse(BaseModel):
    opportunity_id: str

    hs_code: str

    duty_rate: float
    peer_average_duty_rate: float

    calculation_basis: str
    valuation_type: str
    effective_date: str

    import_duty_per_unit: float
    peer_duty_per_unit: float

    duty_variance_per_unit: float
    duty_variance_percent: float

    annual_duty_impact: float

    plant_comparisons: list[TariffPlantComparison]