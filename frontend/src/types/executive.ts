export interface ExecutiveEntitySummary {
  id: string;
  name: string;
  potential_savings: number;
  variance_percent: number;
  opportunity_count: number;
}

export interface ExecutiveSummary {
  as_of_date: string;
  top_plant: ExecutiveEntitySummary | null;
  top_product: ExecutiveEntitySummary | null;
  top_category: ExecutiveEntitySummary | null;
  top_component: ExecutiveEntitySummary | null;
  total_potential_savings: number;
  opportunity_count: number;
}

export interface QuickWin {
  rank: number;
  title: string;
  potential_savings: number;
  ease: "HIGH" | "MEDIUM" | "LOW";
  confidence: number;
  urgency: "HIGH" | "MEDIUM" | "LOW";
  why_now: string;
  opportunity_id: string;
}

export interface PlantExecutiveItem {
  plant_id: string;
  plant_code: string;
  plant_name: string;
  country: string;
  unit_cost: number;
  variance_percent: number;
  potential_savings: number;
  attention_level: "HIGH" | "WATCH" | "STABLE";
  primary_driver: string | null;
  benchmark_status: string;
  opportunity_count: number;
}

export interface ProductExecutiveItem {
  product_id: string;
  product_name: string;
  equipment_family: string;
  average_unit_cost: number;
  highest_cost_plant: string | null;
  lowest_cost_plant: string | null;
  variance_percent: number;
  potential_savings: number;
  priority: "HIGH" | "MEDIUM" | "LOW";
  opportunity_count: number;
}

export interface CategoryExecutiveItem {
  category_code: string;
  category: string;
  benchmark_cost: number;
  comparison_cost: number;
  gap: number;
  contribution_percent: number;
}

export interface CategoriesResponse extends DatedList<CategoryExecutiveItem> {
  overall_gap: number;
  contribution_total: number;
}

export interface ExecutiveAssistantReply {
  answer: string;
  session_id: string;
  model: string;
  provider: "vertex_ai" | "local_grounded_fallback";
  provider_note?: string | null;
  sources: { type: string; label: string }[];
}

export interface DatedList<T> { as_of_date: string; items: T[] }
export interface ProductsResponse extends DatedList<ProductExecutiveItem> { attribution_policy: string }

export interface ProductPlantItem {
  plant_id: string;
  plant_code: string;
  plant_name: string;
  country: string;
  unit_cost: number;
  benchmark_cost: number;
  variance_percent: number;
  potential_savings: number;
  opportunity_count: number;
}

export interface ProductComponentItem {
  component_id: string;
  component_name: string;
  category: string;
  potential_savings: number;
  variance_percent: number;
  confidence_score: number;
  opportunity_count: number;
  lead_opportunity_id: string;
}

export interface ProductDetailResponse {
  as_of_date: string;
  product_id: string;
  product_name: string;
  equipment_family: string;
  average_unit_cost: number;
  benchmark_unit_cost: number;
  variance_amount: number;
  variance_percent: number;
  annual_volume: number;
  annual_spend: number;
  potential_savings: number;
  confidence_score: number;
  priority: "HIGH" | "MEDIUM" | "LOW";
  opportunity_count: number;
  lead_opportunity_id: string;
  snapshot_at: string;
  highest_cost_plant: string | null;
  lowest_cost_plant: string | null;
  plants: ProductPlantItem[];
  components: ProductComponentItem[];
}

export interface ProductTrendPoint {
  period_start: string;
  unit_cost: number;
  benchmark_cost: number;
}

export interface ProductTrendSeries {
  plant_id: string;
  plant_name: string;
  points: ProductTrendPoint[];
}

export interface ProductTrendResponse {
  as_of_date: string;
  product_id: string;
  series: ProductTrendSeries[];
}

export interface ComponentSupplierItem {
  supplier_id: string;
  supplier_name: string;
  country: string;
  is_primary_supplier: boolean;
  unit_cost: number;
  annual_volume: number;
  annual_spend: number;
  quality_score: number;
  delivery_score: number;
  overall_score: number;
}

export interface ComponentDetailResponse {
  as_of_date: string;
  component_id: string;
  component_name: string;
  category: string;
  annual_opportunity: number;
  annual_spend: number;
  annual_volume: number;
  volume_change_percent: number;
  confidence_score: number;
  variance_percent: number;
  annual_tariff_impact: number;
  tariff_per_unit: number;
  duty_rate: number;
  peer_duty_rate: number;
  hs_code: string;
  opportunity_count: number;
  lead_opportunity_id: string;
  lead_plant: string;
  priority: "HIGH" | "MEDIUM" | "LOW";
  current_supplier: string | null;
  benchmark_supplier: string | null;
  current_supplier_unit_cost: number | null;
  benchmark_supplier_unit_cost: number | null;
  supplier_delta_percent: number | null;
  commercial_delta: number | null;
  suppliers: ComponentSupplierItem[];
  products: { product_id: string; product_name: string }[];
}

export interface GeneratedExecutiveReport {
  as_of_date: string;
  period: string;
  scope: string;
  narrative: string;
  provider: "vertex_ai" | "local_grounded_fallback";
  provider_note?: string | null;
  model: string;
  session_id: string;
  product_id?: string | null;
  file_name: string;
  report_id: string;
  download_url: string;
  storage: "minio";
}
