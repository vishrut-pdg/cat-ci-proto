import {
  apiGet,
} from "./api";

import type {
  LogisticsResponse,
  OpportunityDetailResponse,
  OpportunityListResponse,
  OverviewResponse,
  PlantsResponse,
  RankingResponse,
  SuppliersResponse,
  TariffResponse,
} from "../types/opportunity";


// ==========================================================
// OPPORTUNITY LIST
// ==========================================================

export async function getOpportunities(
  status?: string,
  limit = 200,
  offset = 0,
): Promise<OpportunityListResponse> {

  const params =
    new URLSearchParams();

  if (status) {
    params.set(
      "status",
      status,
    );
  }

  params.set(
    "limit",
    String(limit),
  );

  params.set(
    "offset",
    String(offset),
  );

  return apiGet<OpportunityListResponse>(
    `/opportunities?${params.toString()}`,
  );
}


// ==========================================================
// RECSYS
// ==========================================================

export async function getRecommendations(
  limit = 200,
): Promise<RankingResponse> {

  const params =
    new URLSearchParams();

  params.set(
    "limit",
    String(limit),
  );

  return apiGet<RankingResponse>(
    `/recsys/recommendations?${params.toString()}`,
  );
}


// ==========================================================
// OPPORTUNITY DETAIL
// ==========================================================

export async function getOpportunity(
  opportunityId: string,
): Promise<OpportunityDetailResponse> {

  return apiGet<OpportunityDetailResponse>(
    `/opportunities/${encodeURIComponent(
      opportunityId,
    )}`,
  );
}


// ==========================================================
// OVERVIEW
// ==========================================================

export async function getOpportunityOverview(
  opportunityId: string,
): Promise<OverviewResponse> {

  return apiGet<OverviewResponse>(
    `/opportunities/${encodeURIComponent(
      opportunityId,
    )}/overview`,
  );
}


// ==========================================================
// PLANTS
// ==========================================================

export async function getOpportunityPlants(
  opportunityId: string,
): Promise<PlantsResponse> {

  return apiGet<PlantsResponse>(
    `/opportunities/${encodeURIComponent(
      opportunityId,
    )}/plants`,
  );
}


// ==========================================================
// SUPPLIERS
// ==========================================================

export async function getOpportunitySuppliers(
  opportunityId: string,
): Promise<SuppliersResponse> {

  return apiGet<SuppliersResponse>(
    `/opportunities/${encodeURIComponent(
      opportunityId,
    )}/suppliers`,
  );
}


// ==========================================================
// LOGISTICS
// ==========================================================

export async function getOpportunityLogistics(
  opportunityId: string,
): Promise<LogisticsResponse> {

  return apiGet<LogisticsResponse>(
    `/opportunities/${encodeURIComponent(
      opportunityId,
    )}/logistics`,
  );
}


// ==========================================================
// TARIFF
// ==========================================================

export async function getOpportunityTariff(
  opportunityId: string,
): Promise<TariffResponse> {

  return apiGet<TariffResponse>(
    `/opportunities/${encodeURIComponent(
      opportunityId,
    )}/tariff`,
  );
}