import { apiDownload, apiGet, apiRequest } from "./api";
import type { CategoriesResponse, ComponentDetailResponse, DatedList, ExecutiveAssistantReply, ExecutiveSummary, GeneratedExecutiveReport, PlantExecutiveItem, ProductDetailResponse, ProductsResponse, ProductTrendResponse, QuickWin } from "../types/executive";

export interface ExecutiveFilters {
  period?: string;
  scope?: string;
  region?: string;
  plant_id?: string;
  product_id?: string;
  as_of_date?: string;
  limit?: string;
}

function query(filters: ExecutiveFilters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => { if (value) params.set(key, value); });
  const value = params.toString();
  return value ? `?${value}` : "";
}

export const getExecutiveSummary = (filters?: ExecutiveFilters) => apiGet<ExecutiveSummary>(`/executive/summary${query(filters)}`);
export const getQuickWins = (filters?: ExecutiveFilters, limit = 3) => apiGet<DatedList<QuickWin>>(`/executive/quick-wins${query({ ...filters, limit: String(limit) })}`);
export const getExecutivePlants = (filters?: ExecutiveFilters) => apiGet<DatedList<PlantExecutiveItem>>(`/executive/plants${query(filters)}`);
export const getExecutiveProducts = (filters?: ExecutiveFilters) => apiGet<ProductsResponse>(`/executive/products${query(filters)}`);
export const getExecutiveProduct = (productId: string, filters?: ExecutiveFilters) => apiGet<ProductDetailResponse>(`/executive/products/${encodeURIComponent(productId)}${query(filters)}`);
export const getExecutiveProductTrend = (productId: string, filters?: ExecutiveFilters) => apiGet<ProductTrendResponse>(`/executive/products/${encodeURIComponent(productId)}/trend${query(filters)}`);
export const getExecutiveProductCostDrivers = (productId: string, filters?: ExecutiveFilters) => apiGet<CategoriesResponse>(`/executive/products/${encodeURIComponent(productId)}/cost-drivers${query(filters)}`);
export const getExecutiveCategories = (filters?: ExecutiveFilters) => apiGet<CategoriesResponse>(`/executive/categories${query(filters)}`);
export const getExecutiveComponent = (componentId: string, filters?: ExecutiveFilters) => apiGet<ComponentDetailResponse>(`/executive/components/${encodeURIComponent(componentId)}${query(filters)}`);
export const getExecutiveReport = (filters?: ExecutiveFilters) => apiGet<unknown>(`/executive/report${query(filters)}`);
export const askExecutiveKatty = (message: string, sessionId: string | undefined, filters: ExecutiveFilters) => apiRequest<ExecutiveAssistantReply>("/assistant/executive/chat", "POST", {
  message,
  session_id: sessionId,
  period: filters.period ?? "FY26",
  scope: filters.scope ?? "enterprise",
});
export const generateExecutiveReport = (filters: ExecutiveFilters) => apiRequest<GeneratedExecutiveReport>("/assistant/executive/report", "POST", {
  period: filters.period ?? "FY26",
  scope: filters.scope ?? "enterprise",
  product_id: filters.product_id,
});
export const sendExecutiveOpportunityToTeam = (opportunityId: string) => apiRequest<{ id: string; opportunity_id: string; status: string }>(
  `/opportunities/${encodeURIComponent(opportunityId)}/assign`, "POST", { expert_user_id: "USER-002" },
);
export async function downloadExecutiveReport(report: GeneratedExecutiveReport) {
  const blob = await apiDownload(report.download_url);
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = report.file_name;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
