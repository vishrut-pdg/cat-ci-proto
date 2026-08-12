// ==========================================================
// OPPORTUNITY LIST
// ==========================================================

export interface OpportunityListItem {
  opportunity_id: string;

  status: string;
  priority: string;

  part_number: string;
  component_id: string;

  part_name: string;
  category: string;
  part_family: string;

  plant_code: string;
  plant_name: string;
  country: string;

  unit_cost: number;
  peer_average_cost: number;

  variance_amount: number;
  variance_percent: number;

  potential_savings: number;
  impact_score: number;
  confidence_score: number;
}


export interface OpportunityListResponse {
  items: OpportunityListItem[];

  count: number;
  limit: number;
  offset: number;
}


// ==========================================================
// RECSYS
// ==========================================================

export interface RankedOpportunity {
  opportunity_id: string;

  part_number: string;
  part_name: string;

  plant_code: string;
  plant_name: string;
  country: string;

  potential_savings: number;
  confidence_score: number;

  final_score: number;
  rank: number;

  reasons: string[];
}


export interface RankingResponse {
  run_id: string | null;

  candidate_count: number;
  eligible_count: number;
  ranked_count: number;

  items: RankedOpportunity[];
}


// ==========================================================
// COMMON OPPORTUNITY METRICS
// ==========================================================

export interface OpportunityMetrics {
  unit_cost: number;
  peer_average_cost: number;

  variance_amount: number;
  variance_percent: number;

  annual_volume: number;
  annual_spend: number;

  potential_savings: number;

  impact_score: number;
  confidence_score: number;
}


// ==========================================================
// OPPORTUNITY DETAIL
// ==========================================================

export interface PartDetail {
  part_id: string;

  part_number: string;
  component_id: string;

  name: string;
  category: string;
  part_family: string;
  part_type: string;

  description: string | null;
}


export interface PlantDetail {
  plant_id: string;

  plant_code: string;
  plant_name: string;

  city: string;
  country: string;
  region: string;

  currency: string;
}


export interface OpportunityDetailResponse {
  opportunity_id: string;
  opportunity_number: string;

  status: string;
  priority: string;

  detection_source: string;

  part: PartDetail;
  plant: PlantDetail;

  metrics: OpportunityMetrics;
}


// ==========================================================
// OVERVIEW
// ==========================================================

export interface CostDriver {
  code: string;
  name: string;

  impact_amount: number;
  impact_percent: number;

  rank: number;
  confidence_score: number;

  explanation: string;
}


export interface OverviewResponse {
  opportunity_id: string;

  metrics: OpportunityMetrics;

  cost_drivers: CostDriver[];
}


// ==========================================================
// PLANT COMPARISON
// ==========================================================

export interface PlantComparison {
  plant_id: string;

  plant_code: string;
  plant_name: string;
  country: string;

  unit_cost: number;
  peer_average_cost: number;

  variance_amount: number;
  variance_percent: number;

  annual_volume: number;
  volume_variance_percent: number;

  rank: number;
}


export interface PlantsResponse {
  opportunity_id: string;

  benchmark_type: string;

  peer_average_cost: number;

  plants: PlantComparison[];
}


// ==========================================================
// SUPPLIER COMPARISON
// ==========================================================

export interface SupplierComparison {
  supplier_id: string;

  supplier_code: string;
  supplier_name: string;

  country: string;

  unit_cost: number;
  peer_average_cost: number;

  variance_amount: number;
  variance_percent: number;

  annual_spend: number;
  annual_volume: number;

  quality_score: number;
  delivery_score: number;
  responsiveness_score: number;
  overall_score: number;

  rank: number;
}


export interface SuppliersResponse {
  opportunity_id: string;

  suppliers: SupplierComparison[];
}


// ==========================================================
// LOGISTICS
// ==========================================================

export interface LogisticsComponent {
  code: string;
  name: string;

  cost: number;
  peer_average: number;

  variance: number;
  variance_percent: number;

  rank: number;
}


export interface LogisticsTrendPoint {
  period: string;

  actual_cost: number;
  peer_average_cost: number;
}


export interface LogisticsResponse {
  opportunity_id: string;

  total_cost: number;
  peer_average: number;

  variance: number;
  variance_percent: number;

  components: LogisticsComponent[];

  trend: LogisticsTrendPoint[];
}


// ==========================================================
// TARIFF
// ==========================================================

export interface TariffPlantComparison {
  plant_id: string;

  plant_code: string;
  plant_name: string;
  country: string;

  duty_rate: number;
}


export interface TariffResponse {
  opportunity_id: string;

  hs_code: string;

  duty_rate: number;
  peer_average_duty_rate: number;

  calculation_basis: string;
  valuation_type: string;

  effective_date: string;

  import_duty_per_unit: number;
  peer_duty_per_unit: number;

  duty_variance_per_unit: number;
  duty_variance_percent: number;

  annual_duty_impact: number;

  plant_comparisons: TariffPlantComparison[];
}