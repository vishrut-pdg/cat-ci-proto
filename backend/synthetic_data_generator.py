from __future__ import annotations

import argparse
import gzip
import json
import math
import random
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_SEED = 42
SNAPSHOT_DATE = date(2026, 6, 12)
MONTH_END = date(2026, 6, 1)


# ============================================================
# GENERAL HELPERS
# ============================================================


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def round2(value: float) -> float:
    return round(value, 2)


def month_sequence(end: date, count: int) -> list[date]:
    result: list[date] = []

    year = end.year
    month = end.month

    for _ in range(count):
        result.append(date(year, month, 1))

        month -= 1
        if month == 0:
            month = 12
            year -= 1

    result.reverse()
    return result


MONTHS = month_sequence(MONTH_END, 12)


def copy_escape(value) -> str:
    """
    Escape a Python value for PostgreSQL COPY TEXT format.
    """
    if value is None:
        return r"\N"

    if isinstance(value, bool):
        return "t" if value else "f"

    if isinstance(value, (date, datetime)):
        value = value.isoformat()

    value = str(value)

    return (
        value.replace("\\", "\\\\")
        .replace("\t", "\\t")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )


def write_copy(
    stream,
    table: str,
    columns: Sequence[str],
    rows: Iterable[Sequence],
) -> int:
    stream.write(
        f"COPY {table} ({', '.join(columns)}) FROM STDIN;\n"
    )

    count = 0

    for row in rows:
        stream.write(
            "\t".join(copy_escape(value) for value in row)
            + "\n"
        )
        count += 1

    stream.write("\\.\n\n")

    return count


def distribute_total(
    rng: random.Random,
    total: int,
    count: int = 12,
) -> list[int]:
    weights = [
        rng.uniform(0.75, 1.25)
        for _ in range(count)
    ]

    weight_sum = sum(weights)

    values = [
        max(1, int(total * weight / weight_sum))
        for weight in weights
    ]

    difference = total - sum(values)
    values[-1] += difference

    return values


# ============================================================
# MASTER DATA
# ============================================================


PLANTS = [
    ("PLANT-PIR", "PIR", "Brazil Plant", "Piracicaba", "Brazil", "LATAM", "BRL"),
    ("PLANT-MAQ", "MAQ", "Mexico Plant", "Monterrey", "Mexico", "LATAM", "MXN"),
    ("PLANT-LLC", "LLC", "USA Plant", "Mossville", "United States", "NA", "USD"),
    ("PLANT-TBG", "TBG", "Germany Plant", "Dortmund", "Germany", "EMEA", "EUR"),
    ("PLANT-TPL", "TPL", "India Plant", "Chennai", "India", "APAC", "INR"),
    ("PLANT-XUZ", "XUZ", "China Plant", "Xuzhou", "China", "APAC", "CNY"),
    ("PLANT-JPN", "JPN", "Japan Plant", "Akashi", "Japan", "APAC", "JPY"),
    ("PLANT-AUS", "AUS", "Australia Plant", "Perth", "Australia", "APAC", "AUD"),
    ("PLANT-FRA", "FRA", "France Plant", "Grenoble", "France", "EMEA", "EUR"),
    ("PLANT-ITA", "ITA", "Italy Plant", "Bologna", "Italy", "EMEA", "EUR"),
    ("PLANT-ESP", "ESP", "Spain Plant", "Madrid", "Spain", "EMEA", "EUR"),
    ("PLANT-GBR", "GBR", "UK Plant", "Leicester", "United Kingdom", "EMEA", "GBP"),
    ("PLANT-POL", "POL", "Poland Plant", "Wroclaw", "Poland", "EMEA", "PLN"),
    ("PLANT-CZE", "CZE", "Czech Plant", "Ostrava", "Czech Republic", "EMEA", "CZK"),
    ("PLANT-TUR", "TUR", "Turkey Plant", "Izmir", "Turkey", "EMEA", "TRY"),
    ("PLANT-ZAF", "ZAF", "South Africa Plant", "Johannesburg", "South Africa", "EMEA", "ZAR"),
    ("PLANT-CHL", "CHL", "Chile Plant", "Santiago", "Chile", "LATAM", "CLP"),
    ("PLANT-ARG", "ARG", "Argentina Plant", "Cordoba", "Argentina", "LATAM", "ARS"),
    ("PLANT-COL", "COL", "Colombia Plant", "Bogota", "Colombia", "LATAM", "COP"),
    ("PLANT-CAN", "CAN", "Canada Plant", "Toronto", "Canada", "NA", "CAD"),
    ("PLANT-KOR", "KOR", "Korea Plant", "Busan", "South Korea", "APAC", "KRW"),
    ("PLANT-IDN", "IDN", "Indonesia Plant", "Jakarta", "Indonesia", "APAC", "IDR"),
    ("PLANT-THA", "THA", "Thailand Plant", "Rayong", "Thailand", "APAC", "THB"),
    ("PLANT-MYS", "MYS", "Malaysia Plant", "Penang", "Malaysia", "APAC", "MYR"),
    ("PLANT-SGP", "SGP", "Singapore Plant", "Singapore", "Singapore", "APAC", "SGD"),
    ("PLANT-UAE", "UAE", "UAE Plant", "Dubai", "United Arab Emirates", "EMEA", "AED"),
    ("PLANT-SWE", "SWE", "Sweden Plant", "Gothenburg", "Sweden", "EMEA", "SEK"),
]


PART_FAMILIES = [
    ("Hydraulics", "Hydraulic Pump"),
    ("Hydraulics", "Hydraulic Cylinder"),
    ("Electronics", "Engine Control Module"),
    ("Drivetrain", "Transmission Assembly"),
    ("Powertrain", "Final Drive Motor"),
    ("Powertrain", "Swing Bearing"),
    ("Cooling", "Cooling Fan Assembly"),
    ("Engine", "Engine Mount"),
    ("Drivetrain", "Gear Assembly"),
    ("Electrical", "Alternator"),
    ("Fuel System", "Fuel Injector"),
    ("Undercarriage", "Track Roller"),
    ("Braking", "Brake Assembly"),
    ("Structures", "Boom Assembly"),
    ("Filtration", "Oil Filter Assembly"),
]


EQUIPMENT_FAMILIES = [
    "Hydraulic Shovel",
    "Excavator",
    "Wheel Loader",
    "Dozer",
    "Motor Grader",
    "Mining Truck",
]


EQUIPMENT_MODELS = [
    ("EQ-001", "Hydraulic Shovel", "6060"),
    ("EQ-002", "Hydraulic Shovel", "6030"),
    ("EQ-003", "Hydraulic Shovel", "6090 FS"),
    ("EQ-004", "Excavator", "336"),
    ("EQ-005", "Excavator", "349"),
    ("EQ-006", "Excavator", "395"),
    ("EQ-007", "Wheel Loader", "988"),
    ("EQ-008", "Wheel Loader", "992"),
    ("EQ-009", "Wheel Loader", "994"),
    ("EQ-010", "Dozer", "D8"),
    ("EQ-011", "Dozer", "D10"),
    ("EQ-012", "Dozer", "D11"),
    ("EQ-013", "Motor Grader", "140"),
    ("EQ-014", "Motor Grader", "150"),
    ("EQ-015", "Motor Grader", "24"),
    ("EQ-016", "Mining Truck", "793"),
    ("EQ-017", "Mining Truck", "794 AC"),
    ("EQ-018", "Mining Truck", "797F"),
]


SUPPLIER_PREFIXES = [
    "Northstar",
    "Apex",
    "Global",
    "Precision",
    "Summit",
    "Atlas",
    "Titan",
    "Prime",
    "Vertex",
    "Advanced",
    "Continental",
    "Pioneer",
    "Heritage",
    "Sterling",
    "Vector",
]


SUPPLIER_SUFFIXES = [
    "Motion Systems",
    "Industrial Components",
    "Hydraulics",
    "Engineering",
    "Precision Parts",
    "Power Systems",
    "Manufacturing",
    "Mobility",
    "Machining",
    "Technologies",
]


COUNTRIES = [
    "Germany",
    "United States",
    "Japan",
    "Brazil",
    "Mexico",
    "China",
    "India",
    "South Korea",
    "Italy",
    "France",
]


FIRST_NAMES = [
    "Sarah",
    "Priya",
    "Michael",
    "Ravi",
    "Olivia",
    "Daniel",
    "James",
    "Lisa",
    "Peter",
    "Aisha",
    "David",
    "Sophia",
    "Emma",
    "Noah",
    "Ethan",
    "Lucas",
    "Maya",
    "Arjun",
    "Emily",
    "Ryan",
]


LAST_NAMES = [
    "Smith",
    "Patel",
    "Chen",
    "Kumar",
    "Lee",
    "Wong",
    "Clark",
    "Brown",
    "Johnson",
    "Sharma",
    "Kim",
    "Miller",
    "Wilson",
    "Garcia",
    "Martin",
]


# ============================================================
# SQL DDL
# ============================================================


DDL = r"""
SET client_min_messages = warning;
SET timezone = 'UTC';

CREATE SCHEMA IF NOT EXISTS catalog;
CREATE SCHEMA IF NOT EXISTS supply;
CREATE SCHEMA IF NOT EXISTS economics;
CREATE SCHEMA IF NOT EXISTS opportunity;
CREATE SCHEMA IF NOT EXISTS identity_data;
CREATE SCHEMA IF NOT EXISTS recsys;
CREATE SCHEMA IF NOT EXISTS workflow;
CREATE SCHEMA IF NOT EXISTS telemetry;


-- ==========================================================
-- CATALOG
-- ==========================================================

CREATE TABLE catalog.parts (
    id                  text PRIMARY KEY,
    part_number         text NOT NULL UNIQUE,
    component_id        text NOT NULL UNIQUE,
    name                text NOT NULL,
    category            text NOT NULL,
    part_family         text NOT NULL,
    part_type           text NOT NULL,
    status              text NOT NULL,
    created_at          timestamptz NOT NULL
);

CREATE TABLE catalog.part_catalog (
    id                  text PRIMARY KEY,
    part_id             text NOT NULL REFERENCES catalog.parts(id),
    title               text NOT NULL,
    description         text NOT NULL,
    source_system       text NOT NULL,
    source_updated_at   timestamptz NOT NULL,
    raw_payload         jsonb NOT NULL
);

CREATE TABLE catalog.part_attributes (
    id                  text PRIMARY KEY,
    part_id             text NOT NULL REFERENCES catalog.parts(id),
    attribute_type      text NOT NULL,
    attribute_name      text NOT NULL,
    attribute_value     text NOT NULL,
    display_order       integer NOT NULL
);

CREATE TABLE catalog.specification_definitions (
    id                  text PRIMARY KEY,
    code                text NOT NULL UNIQUE,
    name                text NOT NULL,
    data_type           text NOT NULL,
    canonical_unit      text
);

CREATE TABLE catalog.part_specifications (
    id                  text PRIMARY KEY,
    part_id             text NOT NULL REFERENCES catalog.parts(id),
    specification_id    text NOT NULL REFERENCES catalog.specification_definitions(id),
    numeric_value       numeric,
    text_value          text,
    source_unit         text,
    canonical_value     numeric,
    canonical_unit      text
);

CREATE TABLE catalog.equipment_models (
    id                  text PRIMARY KEY,
    equipment_family    text NOT NULL,
    model_code          text NOT NULL,
    manufacturer        text NOT NULL
);

CREATE TABLE catalog.part_compatibility (
    id                  text PRIMARY KEY,
    part_id             text NOT NULL REFERENCES catalog.parts(id),
    equipment_model_id  text NOT NULL REFERENCES catalog.equipment_models(id),
    compatibility_type  text NOT NULL
);


-- ==========================================================
-- SUPPLY
-- ==========================================================

CREATE TABLE supply.plants (
    id              text PRIMARY KEY,
    plant_code      text NOT NULL UNIQUE,
    name            text NOT NULL,
    city            text NOT NULL,
    country         text NOT NULL,
    region          text NOT NULL,
    currency        text NOT NULL,
    status          text NOT NULL
);

CREATE TABLE supply.suppliers (
    id                      text PRIMARY KEY,
    supplier_code           text NOT NULL UNIQUE,
    name                    text NOT NULL,
    country                 text NOT NULL,
    status                  text NOT NULL,
    relationship_since      date NOT NULL,
    quality_score           numeric NOT NULL,
    delivery_score          numeric NOT NULL,
    responsiveness_score    numeric NOT NULL,
    overall_score           numeric NOT NULL
);

CREATE TABLE supply.part_supply (
    id                      text PRIMARY KEY,
    part_id                 text NOT NULL REFERENCES catalog.parts(id),
    plant_id                text NOT NULL REFERENCES supply.plants(id),
    supplier_id             text NOT NULL REFERENCES supply.suppliers(id),
    is_primary_supplier     boolean NOT NULL,
    supplier_share_pct      numeric NOT NULL,
    effective_from          date NOT NULL,
    effective_to            date
);


-- ==========================================================
-- ECONOMICS
-- ==========================================================

CREATE TABLE economics.part_economic_fact (
    id                      text PRIMARY KEY,
    part_id                 text NOT NULL REFERENCES catalog.parts(id),
    plant_id                text NOT NULL REFERENCES supply.plants(id),
    supplier_id             text NOT NULL REFERENCES supply.suppliers(id),
    period_start            date NOT NULL,
    currency                text NOT NULL,
    unit_cost               numeric NOT NULL,
    base_price              numeric NOT NULL,
    ocean_freight           numeric NOT NULL,
    local_transport         numeric NOT NULL,
    import_duty             numeric NOT NULL,
    insurance               numeric NOT NULL,
    packaging               numeric NOT NULL,
    handling_other          numeric NOT NULL,
    purchase_volume         integer NOT NULL,
    total_spend             numeric NOT NULL,
    source_system           text NOT NULL,
    loaded_at               timestamptz NOT NULL
);


-- ==========================================================
-- OPPORTUNITY
-- ==========================================================

CREATE TABLE opportunity.opportunities (
    id                      text PRIMARY KEY,
    opportunity_number      text NOT NULL UNIQUE,
    part_id                 text NOT NULL REFERENCES catalog.parts(id),
    plant_id                text NOT NULL REFERENCES supply.plants(id),
    status                  text NOT NULL,
    priority                text NOT NULL,
    detection_source        text NOT NULL,
    detected_at             timestamptz NOT NULL,
    current_owner_id        text,
    created_at              timestamptz NOT NULL,
    updated_at              timestamptz NOT NULL
);

CREATE TABLE opportunity.metric_snapshots (
    id                      text PRIMARY KEY,
    opportunity_id          text NOT NULL REFERENCES opportunity.opportunities(id),
    snapshot_at             timestamptz NOT NULL,
    unit_cost               numeric NOT NULL,
    peer_average_cost       numeric NOT NULL,
    variance_amount         numeric NOT NULL,
    variance_percent        numeric NOT NULL,
    annual_volume           integer NOT NULL,
    annual_spend            numeric NOT NULL,
    potential_savings       numeric NOT NULL,
    impact_score            numeric NOT NULL,
    confidence_score        numeric NOT NULL,
    benchmark_type          text NOT NULL,
    feature_version         text NOT NULL
);

CREATE TABLE opportunity.cost_drivers (
    id                      text PRIMARY KEY,
    opportunity_id          text NOT NULL REFERENCES opportunity.opportunities(id),
    driver_code             text NOT NULL,
    driver_name             text NOT NULL,
    impact_amount           numeric NOT NULL,
    impact_percent          numeric NOT NULL,
    rank_position           integer NOT NULL,
    confidence_score        numeric NOT NULL,
    explanation             text NOT NULL
);

CREATE TABLE opportunity.plant_comparisons (
    id                      text PRIMARY KEY,
    opportunity_id          text NOT NULL REFERENCES opportunity.opportunities(id),
    plant_id                text NOT NULL REFERENCES supply.plants(id),
    unit_cost               numeric NOT NULL,
    peer_average_cost       numeric NOT NULL,
    variance_amount         numeric NOT NULL,
    variance_percent        numeric NOT NULL,
    annual_volume           integer NOT NULL,
    volume_variance_percent numeric NOT NULL,
    rank_position           integer NOT NULL
);

CREATE TABLE opportunity.supplier_comparisons (
    id                      text PRIMARY KEY,
    opportunity_id          text NOT NULL REFERENCES opportunity.opportunities(id),
    supplier_id             text NOT NULL REFERENCES supply.suppliers(id),
    unit_cost               numeric NOT NULL,
    peer_average_cost       numeric NOT NULL,
    variance_amount         numeric NOT NULL,
    variance_percent        numeric NOT NULL,
    annual_spend            numeric NOT NULL,
    annual_volume           integer NOT NULL,
    rank_position           integer NOT NULL
);

CREATE TABLE opportunity.logistics_components (
    id                      text PRIMARY KEY,
    opportunity_id          text NOT NULL REFERENCES opportunity.opportunities(id),
    component_code          text NOT NULL,
    component_name          text NOT NULL,
    brazil_cost             numeric NOT NULL,
    peer_average_cost       numeric NOT NULL,
    variance_amount         numeric NOT NULL,
    variance_percent        numeric NOT NULL,
    rank_position           integer NOT NULL
);

CREATE TABLE opportunity.logistics_trend (
    id                      text PRIMARY KEY,
    opportunity_id          text NOT NULL REFERENCES opportunity.opportunities(id),
    period_start            date NOT NULL,
    actual_cost             numeric NOT NULL,
    peer_average_cost       numeric NOT NULL,
    ocean_freight           numeric NOT NULL DEFAULT 0,
    import_duty             numeric NOT NULL DEFAULT 0,
    local_transport         numeric NOT NULL DEFAULT 0,
    insurance               numeric NOT NULL DEFAULT 0,
    packaging               numeric NOT NULL DEFAULT 0,
    handling_other          numeric NOT NULL DEFAULT 0
);

CREATE TABLE opportunity.plant_cost_trend (
    id text PRIMARY KEY, opportunity_id text NOT NULL REFERENCES opportunity.opportunities(id),
    plant_id text NOT NULL REFERENCES supply.plants(id), period_start date NOT NULL,
    unit_cost numeric NOT NULL, peer_average_cost numeric NOT NULL,
    variance_percent numeric NOT NULL, purchase_volume integer NOT NULL
);

CREATE TABLE opportunity.supplier_cost_trend (
    id text PRIMARY KEY, opportunity_id text NOT NULL REFERENCES opportunity.opportunities(id),
    supplier_id text NOT NULL REFERENCES supply.suppliers(id), period_start date NOT NULL,
    unit_cost numeric NOT NULL, peer_average_cost numeric NOT NULL, annualized_volume integer NOT NULL,
    annualized_spend numeric NOT NULL, quality_score numeric NOT NULL, delivery_score numeric NOT NULL
);

CREATE TABLE opportunity.tariff_trend (
    id text PRIMARY KEY, opportunity_id text NOT NULL REFERENCES opportunity.opportunities(id),
    plant_id text NOT NULL REFERENCES supply.plants(id), period_start date NOT NULL, hs_code text NOT NULL,
    duty_rate numeric NOT NULL, peer_average_duty_rate numeric NOT NULL,
    import_duty_per_unit numeric NOT NULL, peer_duty_per_unit numeric NOT NULL,
    annualized_duty_impact numeric NOT NULL
);

CREATE TABLE opportunity.opportunity_events (
    id text PRIMARY KEY, opportunity_id text NOT NULL REFERENCES opportunity.opportunities(id),
    event_type text NOT NULL, actor_user_id text, actor_role text NOT NULL,
    entity_type text NOT NULL, entity_id text, payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL
);

CREATE TABLE opportunity.tariff_details (
    id                      text PRIMARY KEY,
    opportunity_id          text NOT NULL REFERENCES opportunity.opportunities(id),
    hs_code                 text NOT NULL,
    duty_rate               numeric NOT NULL,
    peer_average_duty_rate  numeric NOT NULL,
    calculation_basis       text NOT NULL,
    valuation_type          text NOT NULL,
    effective_date          date NOT NULL,
    import_duty_per_unit    numeric NOT NULL,
    peer_duty_per_unit      numeric NOT NULL,
    annual_duty_impact      numeric NOT NULL
);

CREATE TABLE opportunity.tariff_comparisons (
    id                      text PRIMARY KEY,
    opportunity_id          text NOT NULL REFERENCES opportunity.opportunities(id),
    plant_id                text NOT NULL REFERENCES supply.plants(id),
    duty_rate               numeric NOT NULL
);


-- ==========================================================
-- IDENTITY
-- ==========================================================

CREATE TABLE identity_data.roles (
    id              text PRIMARY KEY,
    code            text NOT NULL UNIQUE,
    name            text NOT NULL
);

CREATE TABLE identity_data.users (
    id              text PRIMARY KEY,
    employee_id     text NOT NULL UNIQUE,
    first_name      text NOT NULL,
    last_name       text NOT NULL,
    email           text NOT NULL UNIQUE,
    department      text NOT NULL,
    location        text NOT NULL,
    active          boolean NOT NULL
);

CREATE TABLE identity_data.user_roles (
    user_id         text NOT NULL REFERENCES identity_data.users(id),
    role_id         text NOT NULL REFERENCES identity_data.roles(id),
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE identity_data.expert_profiles (
    user_id                         text PRIMARY KEY REFERENCES identity_data.users(id),
    current_workload                integer NOT NULL,
    max_capacity                    integer NOT NULL,
    years_experience                integer NOT NULL,
    historical_success_score        numeric NOT NULL,
    average_investigation_days      numeric NOT NULL,
    primary_expertise               text NOT NULL
);


-- ==========================================================
-- RECSYS
-- ==========================================================

CREATE TABLE recsys.ranking_runs (
    id                  text PRIMARY KEY,
    model_name          text NOT NULL,
    model_version       text NOT NULL,
    feature_version     text NOT NULL,
    started_at          timestamptz NOT NULL,
    completed_at        timestamptz NOT NULL
);

CREATE TABLE recsys.ranking_results (
    id                  text PRIMARY KEY,
    ranking_run_id      text NOT NULL REFERENCES recsys.ranking_runs(id),
    opportunity_id      text NOT NULL REFERENCES opportunity.opportunities(id),
    base_score          numeric NOT NULL,
    confidence_score    numeric NOT NULL,
    final_score         numeric NOT NULL,
    rank_position       integer NOT NULL
);

CREATE TABLE recsys.ranking_score_components (
    id                  text PRIMARY KEY,
    ranking_result_id   text NOT NULL REFERENCES recsys.ranking_results(id),
    feature_name        text NOT NULL,
    raw_value           numeric NOT NULL,
    normalized_value    numeric NOT NULL,
    weight              numeric NOT NULL,
    contribution        numeric NOT NULL
);

CREATE TABLE recsys.recommendation_explanations (
    id                  text PRIMARY KEY,
    ranking_result_id   text NOT NULL REFERENCES recsys.ranking_results(id),
    reason_code         text NOT NULL,
    reason_rank         integer NOT NULL,
    metric_name         text NOT NULL,
    metric_value        numeric NOT NULL,
    benchmark_value     numeric,
    explanation_text    text NOT NULL
);


-- ==========================================================
-- WORKFLOW
-- ==========================================================

CREATE TABLE workflow.investigations (
    id                  text PRIMARY KEY,
    opportunity_id      text NOT NULL REFERENCES opportunity.opportunities(id),
    owner_user_id       text NOT NULL REFERENCES identity_data.users(id),
    status              text NOT NULL,
    assigned_at         timestamptz NOT NULL,
    due_at              date NOT NULL,
    progress_percent    numeric NOT NULL
);

CREATE TABLE workflow.findings (
    id text PRIMARY KEY, investigation_id text NOT NULL REFERENCES workflow.investigations(id),
    summary text NOT NULL, created_by text NOT NULL REFERENCES identity_data.users(id), created_at timestamptz NOT NULL
);

CREATE TABLE workflow.expert_consultations (
    id text PRIMARY KEY, investigation_id text NOT NULL REFERENCES workflow.investigations(id),
    expert_user_id text NOT NULL REFERENCES identity_data.users(id), notes text, created_at timestamptz NOT NULL
);

CREATE TABLE telemetry.ai_sessions (
    id text PRIMARY KEY, user_id text NOT NULL, opportunity_id text NOT NULL, role text NOT NULL,
    created_at timestamptz NOT NULL, last_activity_at timestamptz NOT NULL
);
CREATE TABLE telemetry.ai_interactions (
    id text PRIMARY KEY, session_id text NOT NULL REFERENCES telemetry.ai_sessions(id), user_message text NOT NULL,
    assistant_message text, model_name text NOT NULL, latency_ms integer, input_tokens integer, output_tokens integer,
    created_at timestamptz NOT NULL, status text NOT NULL, error_message text
);
CREATE TABLE telemetry.agent_tool_calls (
    id text PRIMARY KEY, interaction_id text NOT NULL REFERENCES telemetry.ai_interactions(id), tool_name text NOT NULL,
    arguments jsonb NOT NULL, duration_ms integer NOT NULL, success boolean NOT NULL, created_at timestamptz NOT NULL
);
CREATE TABLE telemetry.api_requests (
    id bigserial PRIMARY KEY, endpoint text NOT NULL, method text NOT NULL, status_code integer NOT NULL,
    duration_ms integer NOT NULL, user_role text, created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE workflow.recommendations (
    id                  text PRIMARY KEY,
    investigation_id    text NOT NULL REFERENCES workflow.investigations(id),
    title               text NOT NULL,
    description         text NOT NULL,
    estimated_savings   numeric NOT NULL,
    priority            text NOT NULL,
    status              text NOT NULL,
    created_at          timestamptz NOT NULL
);

CREATE TABLE workflow.decisions (
    id                  text PRIMARY KEY,
    recommendation_id   text NOT NULL REFERENCES workflow.recommendations(id),
    decision_maker_id   text NOT NULL REFERENCES identity_data.users(id),
    decision_type       text NOT NULL,
    comments            text,
    decided_at          timestamptz
);

CREATE TABLE workflow.executions (
    id                  text PRIMARY KEY,
    decision_id         text NOT NULL REFERENCES workflow.decisions(id),
    owner_user_id       text NOT NULL REFERENCES identity_data.users(id),
    status              text NOT NULL,
    progress_percent    numeric NOT NULL,
    expected_savings    numeric NOT NULL,
    realized_savings    numeric NOT NULL,
    planned_end         date NOT NULL
);

CREATE TABLE workflow.outcomes (
    id                          text PRIMARY KEY,
    execution_id                text NOT NULL REFERENCES workflow.executions(id),
    expected_savings            numeric NOT NULL,
    realized_savings            numeric NOT NULL,
    savings_realization_percent numeric NOT NULL,
    baseline_unit_cost          numeric NOT NULL,
    final_unit_cost             numeric NOT NULL,
    success                     boolean NOT NULL,
    measured_at                 timestamptz NOT NULL
);


-- ==========================================================
-- INDEXES
-- ==========================================================

CREATE INDEX idx_economic_part_plant
    ON economics.part_economic_fact(part_id, plant_id, period_start);

CREATE INDEX idx_opportunity_status
    ON opportunity.opportunities(status);

CREATE INDEX idx_opportunity_part_plant
    ON opportunity.opportunities(part_id, plant_id);

CREATE INDEX idx_metric_opportunity
    ON opportunity.metric_snapshots(opportunity_id);

CREATE INDEX idx_plant_comparison_opportunity
    ON opportunity.plant_comparisons(opportunity_id);

CREATE INDEX idx_supplier_comparison_opportunity
    ON opportunity.supplier_comparisons(opportunity_id);

CREATE INDEX idx_logistics_opportunity
    ON opportunity.logistics_components(opportunity_id);

CREATE INDEX idx_ranking_rank
    ON recsys.ranking_results(ranking_run_id, rank_position);

CREATE INDEX idx_investigation_owner
    ON workflow.investigations(owner_user_id);

"""


# ============================================================
# GENERATION
# ============================================================


def generate_dataset(
    rng: random.Random,
    part_count: int,
    supplier_count: int,
):
    # --------------------------------------------------------
    # Plants
    # --------------------------------------------------------

    plants = [
        (
            plant_id,
            code,
            name,
            city,
            country,
            region,
            currency,
            "ACTIVE",
        )
        for (
            plant_id,
            code,
            name,
            city,
            country,
            region,
            currency,
        ) in PLANTS
    ]

    plant_by_id = {
        row[0]: row
        for row in plants
    }

    plant_ids = list(plant_by_id)

    # --------------------------------------------------------
    # Suppliers
    # --------------------------------------------------------

    suppliers = []

    # Fixed suppliers used by the Hydraulic Pump demo
    fixed_supplier_names = [
        ("Supplier A", "SA001", "Germany"),
        ("Supplier B", "SA002", "United States"),
        ("Supplier C", "SA003", "Japan"),
        ("Supplier D", "SA004", "Mexico"),
        ("Supplier E", "SA005", "Brazil"),
    ]

    for index in range(1, supplier_count + 1):
        supplier_id = f"SUP-{index:04d}"

        if index <= len(fixed_supplier_names):
            name, code, country = fixed_supplier_names[index - 1]
        else:
            name = (
                f"{rng.choice(SUPPLIER_PREFIXES)} "
                f"{rng.choice(SUPPLIER_SUFFIXES)}"
            )
            code = f"SUP{index:04d}"
            country = rng.choice(COUNTRIES)

        quality = round2(rng.uniform(3.4, 4.8))
        delivery = round2(rng.uniform(3.2, 4.8))
        responsiveness = round2(rng.uniform(3.1, 4.8))
        overall = round2(
            (quality + delivery + responsiveness) / 3
        )

        suppliers.append(
            (
                supplier_id,
                code,
                name,
                country,
                "ACTIVE",
                date(rng.randint(2008, 2022), 1, 1),
                quality,
                delivery,
                responsiveness,
                overall,
            )
        )

    # Force Supplier A's dashboard values
    suppliers[0] = (
        "SUP-0001",
        "SA001",
        "Supplier A",
        "Germany",
        "ACTIVE",
        date(2018, 1, 1),
        4.2,
        4.0,
        4.1,
        4.1,
    )

    supplier_ids = [
        row[0]
        for row in suppliers
    ]

    # --------------------------------------------------------
    # Parts
    # --------------------------------------------------------

    parts = []
    part_catalog = []
    part_attributes = []

    created_at = datetime(2025, 1, 1, 8, 0)

    for index in range(1, part_count + 1):
        part_id = f"PART-{index:06d}"

        if index == 1:
            part_number = "20R-2009"
            component_id = "HP-100045"
            category = "Hydraulics"
            family = "Hydraulic Pump"
            part_type = "Remanufactured"
            name = "Cat Reman Hydraulic Pump"
        else:
            category, family = rng.choice(PART_FAMILIES)
            prefix = rng.choice(
                ["10R", "20R", "30R", "4P", "7X", "9Y", "1T"]
            )
            part_number = (
                f"{prefix}-{rng.randint(1000, 9999)}-{index:03d}"
            )
            component_id = f"CP-{100000 + index}"
            part_type = rng.choice(
                [
                    "New",
                    "Remanufactured",
                    "Service Replacement",
                ]
            )
            name = family

        parts.append(
            (
                part_id,
                part_number,
                component_id,
                name,
                category,
                family,
                part_type,
                "ACTIVE",
                created_at,
            )
        )

        if index == 1:
            description = (
                "Cat Reman hydraulic pumps such as part # 20R-2009 "
                "supply oil flow and pressure to operate actuators and "
                "motors. Durable high-capacity bearings and bushings "
                "enable high power density for peak on-demand hydraulic "
                "system performance. High-performance seals and gaskets "
                "withstand high hydraulic pressures and temperatures to "
                "reduce leaks and improve reliability. Each unit includes "
                "critical engineering updates and is tested against "
                "original specifications."
            )
        else:
            description = (
                f"{name} {part_number} is designed for heavy-duty "
                f"Caterpillar equipment applications. The component is "
                f"engineered for reliability, serviceability and "
                f"consistent operation in demanding environments. "
                f"The part belongs to the {category} product category "
                f"and is supplied through the global service network."
            )

        raw_payload = json.dumps(
            {
                "part_number": part_number,
                "component_id": component_id,
                "category": category,
                "family": family,
                "part_type": part_type,
            },
            separators=(",", ":"),
        )

        part_catalog.append(
            (
                f"CATALOG-{index:06d}",
                part_id,
                name,
                description,
                "Synthetic Product Catalog",
                datetime(2026, 6, 10, 12, 0),
                raw_payload,
            )
        )

        attrs = [
            (
                "BENEFIT",
                "Reliability",
                "Designed for reliable operation in demanding applications.",
            ),
            (
                "WARRANTY",
                "Warranty",
                "Covered by applicable Caterpillar Limited Warranty terms.",
            ),
            (
                "AVAILABILITY",
                "Availability",
                "Availability varies by model, dealer and location.",
            ),
        ]

        if part_type == "Remanufactured":
            attrs.append(
                (
                    "SUSTAINABILITY",
                    "Remanufacturing",
                    "Remanufactured product reduces material consumption compared with replacement by a new unit.",
                )
            )

        for position, (
            attribute_type,
            attribute_name,
            attribute_value,
        ) in enumerate(attrs, start=1):
            part_attributes.append(
                (
                    f"ATTR-{index:06d}-{position:02d}",
                    part_id,
                    attribute_type,
                    attribute_name,
                    attribute_value,
                    position,
                )
            )

    part_by_id = {
        row[0]: row
        for row in parts
    }

    part_ids = list(part_by_id)

    # --------------------------------------------------------
    # Specifications
    # --------------------------------------------------------

    specification_definitions = [
        ("SPEC-LENGTH", "LENGTH", "Length", "NUMBER", "mm"),
        ("SPEC-HEIGHT", "HEIGHT", "Height", "NUMBER", "mm"),
        ("SPEC-WEIGHT", "WEIGHT", "Weight", "NUMBER", "kg"),
        ("SPEC-PRESSURE", "RATED_PRESSURE", "Rated Pressure", "NUMBER", "bar"),
        ("SPEC-VOLTAGE", "VOLTAGE", "Voltage", "NUMBER", "V"),
        ("SPEC-MATERIAL", "MATERIAL", "Material", "TEXT", None),
    ]

    part_specifications = []
    spec_counter = 1

    for part in parts:
        part_id = part[0]
        category = part[4]

        if part_id == "PART-000001":
            rows = [
                ("SPEC-LENGTH", 48.6, None, "in", 1234.44, "mm"),
                ("SPEC-HEIGHT", 23.0, None, "in", 584.2, "mm"),
                (
                    "SPEC-MATERIAL",
                    None,
                    "Sealants / Adhesives Adhesive",
                    None,
                    None,
                    None,
                ),
                ("SPEC-PRESSURE", 5000, None, "psi", 344.74, "bar"),
            ]
        elif category == "Hydraulics":
            rows = [
                (
                    "SPEC-LENGTH",
                    round2(rng.uniform(300, 1400)),
                    None,
                    "mm",
                    None,
                    "mm",
                ),
                (
                    "SPEC-PRESSURE",
                    round2(rng.uniform(180, 420)),
                    None,
                    "bar",
                    None,
                    "bar",
                ),
                (
                    "SPEC-MATERIAL",
                    None,
                    rng.choice(
                        [
                            "Alloy Steel",
                            "Cast Iron",
                            "Steel / Elastomer",
                        ]
                    ),
                    None,
                    None,
                    None,
                ),
            ]
        elif category in {"Electronics", "Electrical"}:
            rows = [
                (
                    "SPEC-VOLTAGE",
                    rng.choice([12, 24, 48]),
                    None,
                    "V",
                    None,
                    "V",
                ),
                (
                    "SPEC-WEIGHT",
                    round2(rng.uniform(2, 35)),
                    None,
                    "kg",
                    None,
                    "kg",
                ),
            ]
        else:
            rows = [
                (
                    "SPEC-WEIGHT",
                    round2(rng.uniform(5, 650)),
                    None,
                    "kg",
                    None,
                    "kg",
                ),
                (
                    "SPEC-MATERIAL",
                    None,
                    rng.choice(
                        [
                            "Alloy Steel",
                            "Forged Steel",
                            "Cast Iron",
                            "Aluminum Alloy",
                        ]
                    ),
                    None,
                    None,
                    None,
                ),
            ]

        for row in rows:
            part_specifications.append(
                (
                    f"PSPEC-{spec_counter:07d}",
                    part_id,
                    *row,
                )
            )
            spec_counter += 1

    # --------------------------------------------------------
    # Equipment compatibility
    # --------------------------------------------------------

    equipment_models = [
        (
            model_id,
            family,
            model_code,
            "Caterpillar",
        )
        for model_id, family, model_code in EQUIPMENT_MODELS
    ]

    part_compatibility = []
    compatibility_counter = 1

    for part_id in part_ids:
        if part_id == "PART-000001":
            compatible = ["EQ-001", "EQ-004"]
        else:
            compatible = rng.sample(
                [row[0] for row in equipment_models],
                k=rng.randint(1, 3),
            )

        for equipment_id in compatible:
            part_compatibility.append(
                (
                    f"COMPAT-{compatibility_counter:07d}",
                    part_id,
                    equipment_id,
                    "COMPATIBLE",
                )
            )
            compatibility_counter += 1

    # --------------------------------------------------------
    # Part supply relationships
    # --------------------------------------------------------

    part_supply = []

    supply_counter = 1

    special_supply = [
        ("PLANT-PIR", "SUP-0001"),
        ("PLANT-MAQ", "SUP-0002"),
        ("PLANT-LLC", "SUP-0003"),
        ("PLANT-TPL", "SUP-0004"),
        ("PLANT-XUZ", "SUP-0005"),
        ("PLANT-TBG", "SUP-0002"),
    ]

    for plant_id, supplier_id in special_supply:
        part_supply.append(
            (
                f"PSUP-{supply_counter:07d}",
                "PART-000001",
                plant_id,
                supplier_id,
                plant_id == "PLANT-PIR",
                100.0,
                date(2023, 1, 1),
                None,
            )
        )
        supply_counter += 1

    for part_id in part_ids[1:]:
        selected_plants = rng.sample(
            plant_ids,
            k=rng.randint(2, 4),
        )

        for position, plant_id in enumerate(selected_plants):
            supplier_id = rng.choice(supplier_ids)

            part_supply.append(
                (
                    f"PSUP-{supply_counter:07d}",
                    part_id,
                    plant_id,
                    supplier_id,
                    position == 0,
                    round2(
                        rng.uniform(55, 100)
                        if position == 0
                        else rng.uniform(10, 45)
                    ),
                    date(rng.randint(2021, 2025), 1, 1),
                    None,
                )
            )

            supply_counter += 1

    # --------------------------------------------------------
    # Economics
    # --------------------------------------------------------

    economic_facts = []

    facts_by_part_plant: dict[
        tuple[str, str], list[tuple]
    ] = defaultdict(list)

    annual_volume_by_pair = defaultdict(int)

    economic_counter = 1

    special_latest_cost = {
        "PLANT-PIR": 421.32,
        "PLANT-MAQ": 362.11,
        "PLANT-LLC": 358.79,
        "PLANT-TPL": 348.22,
        "PLANT-XUZ": 351.47,
        "PLANT-TBG": 366.23,
    }

    special_annual_volume = {
        "PLANT-PIR": 1452,
        "PLANT-MAQ": 2186,
        "PLANT-LLC": 2974,
        "PLANT-TPL": 1921,
        "PLANT-XUZ": 3421,
        "PLANT-TBG": 2510,
    }

    special_brazil_trend = [
        405.20,
        408.60,
        410.10,
        413.70,
        412.50,
        416.80,
        419.40,
        421.00,
        418.20,
        419.30,
        420.50,
        421.32,
    ]

    for supply_row in part_supply:
        (
            _,
            part_id,
            plant_id,
            supplier_id,
            _,
            _,
            _,
            _,
        ) = supply_row

        currency = plant_by_id[plant_id][6]

        if part_id == "PART-000001":
            latest = special_latest_cost[plant_id]
            annual_volume = special_annual_volume[plant_id]
        else:
            latest = round2(
                rng.lognormvariate(
                    math.log(180),
                    0.55,
                )
            )
            latest = clamp(latest, 25, 1800)

            annual_volume = rng.randint(500, 9000)

        monthly_volumes = distribute_total(
            rng,
            annual_volume,
            12,
        )

        for month_index, period in enumerate(MONTHS):
            if (
                part_id == "PART-000001"
                and plant_id == "PLANT-PIR"
            ):
                unit_cost = special_brazil_trend[month_index]
            else:
                month_factor = (
                    0.94
                    + month_index * 0.004
                    + rng.uniform(-0.025, 0.025)
                )
                unit_cost = round2(latest * month_factor)

            if (
                part_id == "PART-000001"
                and plant_id == "PLANT-PIR"
                and period == MONTHS[-1]
            ):
                ocean = 18.60
                import_duty = 21.30
                local = 7.20
                insurance = 3.40
                packaging = 2.80
                handling = 1.10

                base_price = round2(
                    unit_cost
                    - ocean
                    - import_duty
                    - local
                    - insurance
                    - packaging
                    - handling
                )
            else:
                logistics_ratio = rng.uniform(0.045, 0.12)

                ocean = round2(
                    unit_cost
                    * logistics_ratio
                    * rng.uniform(0.25, 0.4)
                )
                local = round2(
                    unit_cost
                    * logistics_ratio
                    * rng.uniform(0.08, 0.17)
                )
                import_duty = round2(
                    unit_cost
                    * rng.uniform(0.015, 0.08)
                )
                insurance = round2(unit_cost * 0.007)
                packaging = round2(unit_cost * 0.006)
                handling = round2(unit_cost * 0.004)

                base_price = round2(
                    unit_cost
                    - ocean
                    - local
                    - import_duty
                    - insurance
                    - packaging
                    - handling
                )

            volume = monthly_volumes[month_index]

            total_spend = round2(
                unit_cost * volume
            )

            fact = (
                f"FACT-{economic_counter:09d}",
                part_id,
                plant_id,
                supplier_id,
                period,
                currency,
                round2(unit_cost),
                base_price,
                ocean,
                local,
                import_duty,
                insurance,
                packaging,
                handling,
                volume,
                total_spend,
                "Synthetic ERP",
                datetime(2026, 6, 12, 3, 0),
            )

            economic_facts.append(fact)
            facts_by_part_plant[
                (part_id, plant_id)
            ].append(fact)

            annual_volume_by_pair[
                (part_id, plant_id)
            ] += volume

            economic_counter += 1

    # --------------------------------------------------------
    # Opportunity candidates
    # --------------------------------------------------------

    available_pairs = list(
        facts_by_part_plant.keys()
    )

    special_pair = (
        "PART-000001",
        "PLANT-PIR",
    )

    available_pairs.remove(special_pair)
    rng.shuffle(available_pairs)

    selected_pairs = [
        special_pair,
        *available_pairs[:127],
    ]

    status_distribution = (
        ["AWAITING_REVIEW"] * 32
        + ["IDENTIFIED"] * 30
        + ["SHORTLISTED"] * 20
        + ["ASSIGNED"] * 12
        + ["UNDER_INVESTIGATION"] * 12
        + ["SUBMITTED_FOR_DECISION"] * 8
        + ["APPROVED"] * 7
        + ["IN_EXECUTION"] * 7
    )

    opportunities = []
    metric_snapshots = []
    cost_drivers = []
    plant_comparisons = []
    supplier_comparisons = []
    logistics_components = []
    logistics_trend = []
    tariff_details = []
    tariff_comparisons = []

    opportunity_meta = {}

    cost_driver_counter = 1
    plant_comparison_counter = 1
    supplier_comparison_counter = 1
    logistics_counter = 1
    logistics_trend_counter = 1
    tariff_comparison_counter = 1

    latest_fact_by_pair = {
        key: rows[-1]
        for key, rows in facts_by_part_plant.items()
    }

    latest_cost_by_pair = {
        key: float(rows[-1][6])
        for key, rows in facts_by_part_plant.items()
    }

    # First 18 opportunities should be high impact
    high_impact_cutoff = 18

    for index, (
        part_id,
        plant_id,
    ) in enumerate(selected_pairs, start=1):
        opportunity_id = f"OPP-{index:06d}"

        same_part_costs = [
            cost
            for (candidate_part, candidate_plant), cost
            in latest_cost_by_pair.items()
            if candidate_part == part_id
            and candidate_plant != plant_id
        ]

        unit_cost = latest_cost_by_pair[
            (part_id, plant_id)
        ]

        if same_part_costs:
            peer_average = round2(
                sum(same_part_costs)
                / len(same_part_costs)
            )
        else:
            peer_average = round2(
                unit_cost
                * rng.uniform(0.83, 0.96)
            )

        if index == 1:
            unit_cost = 421.32
            peer_average = 366.23
            variance_amount = 55.09
            variance_percent = 15.0
            potential_savings = 720_000
            impact_score = 92
            confidence = 0.92
            priority = "HIGH"
        else:
            if unit_cost <= peer_average:
                peer_average = round2(
                    unit_cost
                    * rng.uniform(0.80, 0.96)
                )

            variance_amount = round2(
                unit_cost - peer_average
            )

            variance_percent = round2(
                100
                * variance_amount
                / peer_average
            )

            volume = annual_volume_by_pair[
                (part_id, plant_id)
            ]

            potential_savings = round2(
                max(variance_amount, unit_cost * 0.02)
                * volume
                * rng.uniform(1.8, 4.5)
            )

            if index <= high_impact_cutoff:
                impact_score = rng.randint(81, 96)
            else:
                impact_score = rng.randint(48, 79)

            confidence = round2(
                rng.uniform(0.68, 0.95)
            )

            priority = (
                "HIGH"
                if impact_score >= 80
                else "MEDIUM"
                if impact_score >= 60
                else "LOW"
            )

        status = status_distribution[index - 1]

        opportunities.append(
            (
                opportunity_id,
                opportunity_id,
                part_id,
                plant_id,
                status,
                priority,
                "RECSYS",
                datetime(2026, 6, 12, 7, 30),
                None,
                datetime(2026, 6, 12, 7, 30),
                datetime(2026, 6, 12, 7, 30),
            )
        )

        annual_volume = annual_volume_by_pair[
            (part_id, plant_id)
        ]

        annual_spend = round2(
            sum(
                float(row[15])
                for row in facts_by_part_plant[
                    (part_id, plant_id)
                ]
            )
        )

        # Smooth monthly history; the final point always matches the current snapshot.
        for month_index, period in enumerate(MONTHS):
            distance = 11 - month_index
            historical_unit = round2(unit_cost * (1 - distance * 0.0025) + math.sin(month_index / 2) * unit_cost * 0.003)
            historical_peer = round2(peer_average * (1 - distance * 0.0015))
            historical_variance = round2(historical_unit - historical_peer)
            historical_pct = round2(historical_variance / historical_peer * 100) if historical_peer else 0
            metric_snapshots.append((
                f"METRIC-{index:06d}-{month_index + 1:02d}", opportunity_id,
                datetime(period.year, period.month, 12, 7, 45),
                unit_cost if month_index == 11 else historical_unit,
                peer_average if month_index == 11 else historical_peer,
                variance_amount if month_index == 11 else historical_variance,
                variance_percent if month_index == 11 else historical_pct,
                annual_volume, annual_spend,
                potential_savings if month_index == 11 else round2(potential_savings * (0.88 + month_index * 0.01)),
                impact_score, confidence, "SIMILAR_PLANTS", "features-v2",
            ))

        opportunity_meta[opportunity_id] = {
            "part_id": part_id,
            "plant_id": plant_id,
            "unit_cost": unit_cost,
            "peer_average": peer_average,
            "variance_amount": variance_amount,
            "variance_percent": variance_percent,
            "potential_savings": potential_savings,
            "impact_score": impact_score,
            "confidence": confidence,
            "annual_volume": annual_volume,
        }

        # ----------------------------------------------------
        # Cost drivers
        # ----------------------------------------------------

        if index == 1:
            drivers = [
                (
                    "LOGISTICS_DUTIES",
                    "Logistics & Duties",
                    22.77,
                    6.2,
                ),
                (
                    "SUPPLIER_PRICE",
                    "Supplier Price",
                    14.69,
                    4.0,
                ),
                (
                    "LOWER_VOLUME",
                    "Lower Volume",
                    10.28,
                    2.8,
                ),
                (
                    "SPECIFICATION_DIFF",
                    "Specification Difference",
                    7.35,
                    2.0,
                ),
            ]
        else:
            total_pct = abs(variance_percent)

            driver_weights = [
                rng.uniform(0.30, 0.45),
                rng.uniform(0.20, 0.30),
                rng.uniform(0.12, 0.22),
            ]

            fourth = max(
                0.05,
                1 - sum(driver_weights),
            )

            driver_weights.append(fourth)

            driver_names = [
                (
                    "LOGISTICS_DUTIES",
                    "Logistics & Duties",
                ),
                (
                    "SUPPLIER_PRICE",
                    "Supplier Price",
                ),
                (
                    "LOWER_VOLUME",
                    "Lower Volume",
                ),
                (
                    "SPECIFICATION_DIFF",
                    "Specification Difference",
                ),
            ]

            drivers = []

            for (
                driver_code,
                driver_name,
            ), weight in zip(
                driver_names,
                driver_weights,
            ):
                driver_pct = round2(
                    total_pct * weight
                )

                driver_amount = round2(
                    abs(variance_amount) * weight
                )

                drivers.append(
                    (
                        driver_code,
                        driver_name,
                        driver_amount,
                        driver_pct,
                    )
                )

        for rank, driver in enumerate(
            drivers,
            start=1,
        ):
            (
                driver_code,
                driver_name,
                impact_amount,
                impact_percent,
            ) = driver

            cost_drivers.append(
                (
                    f"DRIVER-{cost_driver_counter:08d}",
                    opportunity_id,
                    driver_code,
                    driver_name,
                    impact_amount,
                    impact_percent,
                    rank,
                    confidence,
                    (
                        f"{driver_name} contributes "
                        f"{impact_percent}% to the observed "
                        f"cost variance."
                    ),
                )
            )

            cost_driver_counter += 1

        # ----------------------------------------------------
        # Plant comparisons
        # ----------------------------------------------------

        if index == 1:
            special_comparisons = [
                ("PLANT-PIR", 421.32, 366.23, 55.09, 15.0, 1452, -32.0),
                ("PLANT-MAQ", 362.11, 366.23, -4.12, -1.0, 2186, -8.0),
                ("PLANT-LLC", 358.79, 366.23, -7.44, -2.0, 2974, 5.0),
                ("PLANT-TPL", 348.22, 366.23, -18.01, -5.0, 1921, -15.0),
                ("PLANT-XUZ", 351.47, 366.23, -14.76, -4.0, 3421, 12.0),
            ]

            for rank, row in enumerate(
                special_comparisons,
                start=1,
            ):
                plant_comparisons.append(
                    (
                        f"PCOMP-{plant_comparison_counter:08d}",
                        opportunity_id,
                        *row,
                        rank,
                    )
                )
                plant_comparison_counter += 1
        else:
            peer_pairs = [
                pair
                for pair in latest_cost_by_pair
                if pair[0] == part_id
            ]

            if (part_id, plant_id) not in peer_pairs:
                peer_pairs.insert(
                    0,
                    (part_id, plant_id),
                )

            peer_pairs = peer_pairs[:5]

            for rank, pair in enumerate(
                peer_pairs,
                start=1,
            ):
                peer_plant = pair[1]
                cost = latest_cost_by_pair[pair]

                delta = round2(
                    cost - peer_average
                )

                delta_pct = round2(
                    100 * delta / peer_average
                )

                volume = annual_volume_by_pair[pair]

                volume_avg = sum(
                    annual_volume_by_pair[p]
                    for p in peer_pairs
                ) / max(len(peer_pairs), 1)

                volume_delta_pct = round2(
                    100
                    * (volume - volume_avg)
                    / max(volume_avg, 1)
                )

                plant_comparisons.append(
                    (
                        f"PCOMP-{plant_comparison_counter:08d}",
                        opportunity_id,
                        peer_plant,
                        cost,
                        peer_average,
                        delta,
                        delta_pct,
                        volume,
                        volume_delta_pct,
                        rank,
                    )
                )

                plant_comparison_counter += 1

        # ----------------------------------------------------
        # Supplier comparisons
        # ----------------------------------------------------

        if index == 1:
            supplier_rows = [
                ("SUP-0001", 421.32, 366.23, 55.09, 15.0, 612_540, 1452),
                ("SUP-0002", 404.18, 365.21, 38.97, 11.0, 480_000, 1188),
                ("SUP-0003", 389.24, 362.15, 27.09, 7.0, 330_000, 848),
                ("SUP-0004", 365.11, 361.02, 4.09, 1.0, 390_000, 1068),
                ("SUP-0005", 342.75, 358.44, -15.69, -4.0, 210_000, 613),
            ]
        else:
            selected_suppliers = rng.sample(
                supplier_ids,
                k=5,
            )

            supplier_rows = []

            for supplier_position, supplier_id in enumerate(
                selected_suppliers
            ):
                factor = rng.uniform(0.90, 1.08)

                supplier_cost = round2(
                    unit_cost * factor
                )

                supplier_peer = round2(
                    peer_average
                    * rng.uniform(0.98, 1.02)
                )

                delta = round2(
                    supplier_cost
                    - supplier_peer
                )

                delta_pct = round2(
                    100
                    * delta
                    / supplier_peer
                )

                volume = rng.randint(
                    400,
                    max(500, annual_volume),
                )

                spend = round2(
                    supplier_cost * volume
                )

                supplier_rows.append(
                    (
                        supplier_id,
                        supplier_cost,
                        supplier_peer,
                        delta,
                        delta_pct,
                        spend,
                        volume,
                    )
                )

        for rank, row in enumerate(
            supplier_rows,
            start=1,
        ):
            supplier_comparisons.append(
                (
                    f"SCOMP-{supplier_comparison_counter:08d}",
                    opportunity_id,
                    *row,
                    rank,
                )
            )

            supplier_comparison_counter += 1

        # ----------------------------------------------------
        # Logistics
        # ----------------------------------------------------

        if index == 1:
            logistics_rows = [
                ("OCEAN_FREIGHT", "Ocean Freight", 18.60, 12.90, 5.70, 44.0),
                ("IMPORT_DUTY", "Import Duty", 21.30, 15.10, 6.20, 41.0),
                ("LOCAL_TRANSPORT", "Local Transport", 7.20, 4.60, 2.60, 57.0),
                ("INSURANCE", "Insurance", 3.40, 2.30, 1.10, 48.0),
                ("PACKAGING", "Packaging", 2.80, 1.80, 1.00, 56.0),
                ("HANDLING_OTHER", "Handling & Other", 1.10, 0.80, 0.30, 38.0),
            ]

            actual_trend = [
                48.2,
                49.1,
                50.3,
                52.7,
                51.6,
                53.8,
                55.2,
                56.1,
                54.3,
                53.6,
                54.7,
                54.4,
            ]

            peer_trend = [
                33.1,
                33.4,
                34.0,
                35.2,
                35.6,
                36.1,
                36.8,
                37.0,
                36.5,
                36.8,
                37.2,
                37.5,
            ]
        else:
            actual_total = round2(
                unit_cost
                * rng.uniform(0.07, 0.16)
            )

            peer_total = round2(
                actual_total
                * rng.uniform(0.62, 0.87)
            )

            weights = [
                0.34,
                0.28,
                0.15,
                0.08,
                0.07,
                0.08,
            ]

            names = [
                ("OCEAN_FREIGHT", "Ocean Freight"),
                ("IMPORT_DUTY", "Import Duty"),
                ("LOCAL_TRANSPORT", "Local Transport"),
                ("INSURANCE", "Insurance"),
                ("PACKAGING", "Packaging"),
                ("HANDLING_OTHER", "Handling & Other"),
            ]

            logistics_rows = []

            for (
                component_code,
                component_name,
            ), weight in zip(names, weights):
                actual = round2(
                    actual_total * weight
                )
                peer = round2(
                    peer_total * weight
                )
                delta = round2(
                    actual - peer
                )
                delta_pct = round2(
                    100 * delta / max(peer, 0.01)
                )

                logistics_rows.append(
                    (
                        component_code,
                        component_name,
                        actual,
                        peer,
                        delta,
                        delta_pct,
                    )
                )

            actual_trend = [
                round2(
                    actual_total
                    * (
                        0.91
                        + month_index * 0.009
                        + rng.uniform(-0.025, 0.025)
                    )
                )
                for month_index in range(12)
            ]

            peer_trend = [
                round2(
                    peer_total
                    * (
                        0.94
                        + month_index * 0.006
                        + rng.uniform(-0.02, 0.02)
                    )
                )
                for month_index in range(12)
            ]

        for rank, row in enumerate(
            logistics_rows,
            start=1,
        ):
            logistics_components.append(
                (
                    f"LOG-{logistics_counter:08d}",
                    opportunity_id,
                    *row,
                    rank,
                )
            )

            logistics_counter += 1

        for period, actual, peer in zip(
            MONTHS,
            actual_trend,
            peer_trend,
        ):
            logistics_trend.append(
                (
                    f"LOGT-{logistics_trend_counter:08d}",
                    opportunity_id,
                    period,
                    actual,
                    peer,
                )
            )

            logistics_trend_counter += 1

        # ----------------------------------------------------
        # Tariff
        # ----------------------------------------------------

        if index == 1:
            tariff_details.append(
                (
                    "TARIFF-000001",
                    opportunity_id,
                    "8413.91.90",
                    10.0,
                    5.8,
                    "CIF Value",
                    "Transaction Value",
                    date(2024, 4, 1),
                    42.13,
                    18.40,
                    145_000,
                )
            )

            tariff_rates = [
                ("PLANT-TPL", 5.0),
                ("PLANT-MAQ", 6.0),
                ("PLANT-LLC", 7.0),
                ("PLANT-TBG", 8.0),
                ("PLANT-PIR", 10.0),
            ]
        else:
            duty_rate = round2(
                rng.uniform(2.5, 12.5)
            )

            peer_duty_rate = round2(
                rng.uniform(2.0, max(2.1, duty_rate - 0.5))
            )

            import_unit = round2(
                unit_cost * duty_rate / 100
            )

            peer_import_unit = round2(
                peer_average
                * peer_duty_rate
                / 100
            )

            tariff_details.append(
                (
                    f"TARIFF-{index:06d}",
                    opportunity_id,
                    rng.choice(
                        [
                            "8413.91.90",
                            "8708.99.90",
                            "8483.90.00",
                            "8537.10.90",
                        ]
                    ),
                    duty_rate,
                    peer_duty_rate,
                    "CIF Value",
                    "Transaction Value",
                    date(2024, 4, 1),
                    import_unit,
                    peer_import_unit,
                    round2(
                        max(
                            import_unit - peer_import_unit,
                            0,
                        )
                        * annual_volume
                    ),
                )
            )

            comparison_plants = rng.sample(
                plant_ids,
                k=5,
            )

            tariff_rates = [
                (
                    comparison_plant,
                    round2(
                        rng.uniform(2.0, 12.0)
                    ),
                )
                for comparison_plant
                in comparison_plants
            ]

        for comparison_plant, rate in tariff_rates:
            tariff_comparisons.append(
                (
                    f"TCOMP-{tariff_comparison_counter:08d}",
                    opportunity_id,
                    comparison_plant,
                    rate,
                )
            )

            tariff_comparison_counter += 1

    # --------------------------------------------------------
    # Identity
    # --------------------------------------------------------

    roles = [
        ("ROLE-FA", "FINANCE_ANALYST", "Finance Analyst"),
        ("ROLE-IE", "INVESTIGATION_EXPERT", "Investigation Expert"),
        ("ROLE-DM", "DECISION_MAKER", "Decision Maker"),
        ("ROLE-EX", "EXECUTION", "Execution"),
        ("ROLE-PA", "PROCESS_ADMIN", "Process Admin"),
    ]

    users = [
        (
            "USER-001",
            "E10001",
            "Sarah",
            "Smith",
            "sarah.smith@example.local",
            "Finance",
            "USA",
            True,
        ),
        (
            "USER-002",
            "E10002",
            "Priya",
            "Patel",
            "priya.patel@example.local",
            "Cost Analytics",
            "India",
            True,
        ),
        (
            "USER-003",
            "E10003",
            "Michael",
            "Chen",
            "michael.chen@example.local",
            "Procurement",
            "USA",
            True,
        ),
        (
            "USER-004",
            "E10004",
            "Ravi",
            "Kumar",
            "ravi.kumar@example.local",
            "Manufacturing",
            "India",
            True,
        ),
        (
            "USER-005",
            "E10005",
            "John",
            "Miller",
            "john.miller@example.local",
            "Finance",
            "USA",
            True,
        ),
        (
            "USER-006",
            "E10006",
            "Olivia",
            "Lee",
            "olivia.lee@example.local",
            "Operations",
            "USA",
            True,
        ),
        (
            "USER-007",
            "E10007",
            "Process",
            "Admin",
            "process.admin@example.local",
            "Enterprise Systems",
            "USA",
            True,
        ),
    ]

    existing_emails = {
        row[4]
        for row in users
    }

    for index in range(8, 31):
        while True:
            first = rng.choice(FIRST_NAMES)
            last = rng.choice(LAST_NAMES)

            email = (
                f"{first.lower()}.{last.lower()}"
                f"{index}@example.local"
            )

            if email not in existing_emails:
                existing_emails.add(email)
                break

        users.append(
            (
                f"USER-{index:03d}",
                f"E{10000 + index}",
                first,
                last,
                email,
                rng.choice(
                    [
                        "Finance",
                        "Procurement",
                        "Cost Analytics",
                        "Supply Chain",
                        "Operations",
                        "Manufacturing",
                    ]
                ),
                rng.choice(
                    [
                        "USA",
                        "Brazil",
                        "Germany",
                        "India",
                        "China",
                        "Mexico",
                    ]
                ),
                True,
            )
        )

    user_roles = [
        ("USER-001", "ROLE-FA"),
        ("USER-002", "ROLE-IE"),
        ("USER-003", "ROLE-IE"),
        ("USER-004", "ROLE-IE"),
        ("USER-005", "ROLE-DM"),
        ("USER-006", "ROLE-EX"),
        ("USER-007", "ROLE-PA"),
    ]

    for index in range(8, 31):
        role_id = rng.choice(
            [
                "ROLE-FA",
                "ROLE-IE",
                "ROLE-IE",
                "ROLE-EX",
            ]
        )

        user_roles.append(
            (
                f"USER-{index:03d}",
                role_id,
            )
        )

    expert_profiles = []

    expert_user_ids = [
        user_id
        for user_id, role_id
        in user_roles
        if role_id == "ROLE-IE"
    ]

    for user_id in sorted(set(expert_user_ids)):
        expert_profiles.append(
            (
                user_id,
                rng.randint(1, 7),
                rng.randint(8, 12),
                rng.randint(3, 22),
                round2(rng.uniform(0.68, 0.94)),
                round2(rng.uniform(8, 19)),
                rng.choice(
                    [
                        "Logistics",
                        "Procurement",
                        "Hydraulics",
                        "Manufacturing",
                        "Tax & Customs",
                        "Supplier Management",
                    ]
                ),
            )
        )

    # --------------------------------------------------------
    # RecSys
    # --------------------------------------------------------

    ranking_runs = [
        (
            "RANKRUN-20260612-01",
            "weighted-opportunity-ranker",
            "v1.0.0",
            "features-v1",
            datetime(2026, 6, 12, 6, 0),
            datetime(2026, 6, 12, 6, 2),
        )
    ]

    raw_ranking = []

    max_savings = max(
        meta["potential_savings"]
        for meta in opportunity_meta.values()
    )

    for opportunity_id, meta in opportunity_meta.items():
        savings_norm = clamp(
            meta["potential_savings"]
            / max_savings,
            0,
            1,
        )

        impact_norm = (
            meta["impact_score"] / 100
        )

        confidence = meta["confidence"]

        base_score = (
            0.45 * impact_norm
            + 0.35 * savings_norm
            + 0.20 * confidence
        )

        final_score = clamp(
            base_score,
            0,
            1,
        )

        raw_ranking.append(
            (
                opportunity_id,
                base_score,
                confidence,
                final_score,
                savings_norm,
                impact_norm,
            )
        )

    raw_ranking.sort(
        key=lambda item: item[3],
        reverse=True,
    )

    # Force demo opportunity to first place
    raw_ranking.sort(
        key=lambda item: (
            item[0] != "OPP-000001",
            -item[3],
        )
    )

    ranking_results = []
    ranking_components = []
    explanations = []

    component_counter = 1
    explanation_counter = 1

    for rank_position, item in enumerate(
        raw_ranking,
        start=1,
    ):
        (
            opportunity_id,
            base_score,
            confidence,
            final_score,
            savings_norm,
            impact_norm,
        ) = item

        if opportunity_id == "OPP-000001":
            final_score = 0.92
            base_score = 0.91
            confidence = 0.92

        result_id = (
            f"RANKRES-{rank_position:06d}"
        )

        ranking_results.append(
            (
                result_id,
                "RANKRUN-20260612-01",
                opportunity_id,
                round2(base_score),
                round2(confidence),
                round2(final_score),
                rank_position,
            )
        )

        component_values = [
            (
                "potential_savings",
                opportunity_meta[
                    opportunity_id
                ]["potential_savings"],
                savings_norm,
                0.35,
            ),
            (
                "impact_score",
                opportunity_meta[
                    opportunity_id
                ]["impact_score"],
                impact_norm,
                0.45,
            ),
            (
                "data_confidence",
                confidence,
                confidence,
                0.20,
            ),
        ]

        for (
            feature_name,
            raw_value,
            normalized,
            weight,
        ) in component_values:
            ranking_components.append(
                (
                    f"RSCORE-{component_counter:08d}",
                    result_id,
                    feature_name,
                    round2(raw_value),
                    round2(normalized),
                    weight,
                    round2(normalized * weight),
                )
            )

            component_counter += 1

        meta = opportunity_meta[
            opportunity_id
        ]

        if opportunity_id == "OPP-000001":
            reasons = [
                (
                    "HIGH_LOGISTICS_COST",
                    "logistics_cost",
                    54.40,
                    37.50,
                    (
                        "Logistics and duties cost $54.40 per unit, "
                        "45% above the peer average."
                    ),
                ),
                (
                    "HIGH_IMPORT_DUTY",
                    "import_duty",
                    21.30,
                    15.10,
                    (
                        "Import duty is $21.30 per unit compared with "
                        "$15.10 for peer plants."
                    ),
                ),
                (
                    "HIGH_UNIT_COST",
                    "unit_cost",
                    421.32,
                    366.23,
                    (
                        "Brazil unit cost is 15% higher than the "
                        "peer plant average."
                    ),
                ),
            ]
        else:
            reasons = [
                (
                    "HIGH_UNIT_COST",
                    "unit_cost",
                    meta["unit_cost"],
                    meta["peer_average"],
                    (
                        f"Unit cost is {meta['variance_percent']:.1f}% "
                        f"above the peer benchmark."
                    ),
                ),
                (
                    "SAVINGS_OPPORTUNITY",
                    "potential_savings",
                    meta["potential_savings"],
                    0,
                    (
                        "The part has a material annualized "
                        "cost-saving opportunity."
                    ),
                ),
            ]

        for reason_rank, reason in enumerate(
            reasons,
            start=1,
        ):
            (
                reason_code,
                metric_name,
                metric_value,
                benchmark,
                text,
            ) = reason

            explanations.append(
                (
                    f"EXPL-{explanation_counter:08d}",
                    result_id,
                    reason_code,
                    reason_rank,
                    metric_name,
                    round2(metric_value),
                    round2(benchmark),
                    text,
                )
            )

            explanation_counter += 1

    # --------------------------------------------------------
    # Workflow
    # --------------------------------------------------------

    investigations = []
    recommendations = []
    decisions = []
    executions = []
    outcomes = []

    workflow_opportunities = [
        item[0]
        for item in raw_ranking[:12]
    ]

    for index, opportunity_id in enumerate(
        workflow_opportunities,
        start=1,
    ):
        investigation_id = (
            f"INV-{index:05d}"
        )

        owner_id = expert_user_ids[
            (index - 1) % len(expert_user_ids)
        ]

        progress = [
            65,
            42,
            55,
            80,
            35,
            70,
            48,
            61,
            72,
            30,
            88,
            52,
        ][index - 1]

        investigations.append(
            (
                investigation_id,
                opportunity_id,
                owner_id,
                "IN_PROGRESS"
                if progress < 80
                else "RECOMMENDATION_READY",
                datetime(2026, 6, 8, 9, 0),
                date(2026, 6, 16 + index),
                progress,
            )
        )

        rec_id = f"REC-{index:05d}"

        recommendations.append(
            (
                rec_id,
                investigation_id,
                rng.choice(
                    [
                        "Renegotiate logistics contract",
                        "Increase local sourcing",
                        "Consolidate purchase volume",
                        "Renegotiate supplier pricing",
                        "Optimize inbound freight lane",
                    ]
                ),
                (
                    "Recommended action based on cost variance, "
                    "supplier, logistics and peer benchmark analysis."
                ),
                round2(
                    opportunity_meta[
                        opportunity_id
                    ]["potential_savings"]
                    * rng.uniform(0.35, 0.8)
                ),
                "HIGH"
                if index <= 4
                else "MEDIUM",
                "DRAFT"
                if index > 8
                else "SUBMITTED",
                datetime(2026, 6, 12, 10, 0),
            )
        )

        if index <= 8:
            decision_id = (
                f"DEC-{index:05d}"
            )

            decision_type = (
                "APPROVE"
                if index <= 6
                else "SEND_BACK_TO_EXPERT"
            )

            decisions.append(
                (
                    decision_id,
                    rec_id,
                    "USER-005",
                    decision_type,
                    (
                        "Approved for execution."
                        if decision_type == "APPROVE"
                        else "Additional analysis required."
                    ),
                    datetime(2026, 6, 12, 14, 0),
                )
            )

            if decision_type == "APPROVE":
                execution_id = (
                    f"EXEC-{index:05d}"
                )

                expected = recommendations[-1][4]

                realized = (
                    round2(
                        expected
                        * rng.uniform(0.15, 0.65)
                    )
                    if index <= 4
                    else 0
                )

                executions.append(
                    (
                        execution_id,
                        decision_id,
                        "USER-006",
                        "IN_PROGRESS",
                        rng.randint(20, 75),
                        expected,
                        realized,
                        date(2026, 7, 15),
                    )
                )

                if index <= 3:
                    realization = round2(
                        100
                        * realized
                        / max(expected, 1)
                    )

                    meta = opportunity_meta[
                        opportunity_id
                    ]

                    outcomes.append(
                        (
                            f"OUT-{index:05d}",
                            execution_id,
                            expected,
                            realized,
                            realization,
                            meta["unit_cost"],
                            round2(
                                meta["unit_cost"]
                                * rng.uniform(
                                    0.88,
                                    0.96,
                                )
                            ),
                            True,
                            datetime(
                                2026,
                                7,
                                30,
                                12,
                                0,
                            ),
                        )
                    )

    return {
        "plants": plants,
        "suppliers": suppliers,
        "parts": parts,
        "part_catalog": part_catalog,
        "part_attributes": part_attributes,
        "specification_definitions": specification_definitions,
        "part_specifications": part_specifications,
        "equipment_models": equipment_models,
        "part_compatibility": part_compatibility,
        "part_supply": part_supply,
        "economic_facts": economic_facts,
        "opportunities": opportunities,
        "metric_snapshots": metric_snapshots,
        "cost_drivers": cost_drivers,
        "plant_comparisons": plant_comparisons,
        "supplier_comparisons": supplier_comparisons,
        "logistics_components": logistics_components,
        "logistics_trend": logistics_trend,
        "tariff_details": tariff_details,
        "tariff_comparisons": tariff_comparisons,
        "roles": roles,
        "users": users,
        "user_roles": user_roles,
        "expert_profiles": expert_profiles,
        "ranking_runs": ranking_runs,
        "ranking_results": ranking_results,
        "ranking_components": ranking_components,
        "explanations": explanations,
        "investigations": investigations,
        "recommendations": recommendations,
        "decisions": decisions,
        "executions": executions,
        "outcomes": outcomes,
    }


# ============================================================
# SQL OUTPUT
# ============================================================


def write_seed_sql(
    output_path: Path,
    dataset: dict,
):
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with gzip.open(
        output_path,
        mode="wt",
        encoding="utf-8",
        compresslevel=9,
        newline="\n",
    ) as stream:
        stream.write(
            "-- Generated synthetic CAT Cost Intelligence dataset\n"
        )
        stream.write(
            "-- Deterministic prototype dataset. Not production data.\n\n"
        )

        stream.write("BEGIN;\n\n")
        stream.write(DDL)
        stream.write("\n")

        counts = {}

        counts["plants"] = write_copy(
            stream,
            "supply.plants",
            [
                "id",
                "plant_code",
                "name",
                "city",
                "country",
                "region",
                "currency",
                "status",
            ],
            dataset["plants"],
        )

        counts["suppliers"] = write_copy(
            stream,
            "supply.suppliers",
            [
                "id",
                "supplier_code",
                "name",
                "country",
                "status",
                "relationship_since",
                "quality_score",
                "delivery_score",
                "responsiveness_score",
                "overall_score",
            ],
            dataset["suppliers"],
        )

        counts["parts"] = write_copy(
            stream,
            "catalog.parts",
            [
                "id",
                "part_number",
                "component_id",
                "name",
                "category",
                "part_family",
                "part_type",
                "status",
                "created_at",
            ],
            dataset["parts"],
        )

        counts["part_catalog"] = write_copy(
            stream,
            "catalog.part_catalog",
            [
                "id",
                "part_id",
                "title",
                "description",
                "source_system",
                "source_updated_at",
                "raw_payload",
            ],
            dataset["part_catalog"],
        )

        counts["part_attributes"] = write_copy(
            stream,
            "catalog.part_attributes",
            [
                "id",
                "part_id",
                "attribute_type",
                "attribute_name",
                "attribute_value",
                "display_order",
            ],
            dataset["part_attributes"],
        )

        counts["specification_definitions"] = write_copy(
            stream,
            "catalog.specification_definitions",
            [
                "id",
                "code",
                "name",
                "data_type",
                "canonical_unit",
            ],
            dataset["specification_definitions"],
        )

        counts["part_specifications"] = write_copy(
            stream,
            "catalog.part_specifications",
            [
                "id",
                "part_id",
                "specification_id",
                "numeric_value",
                "text_value",
                "source_unit",
                "canonical_value",
                "canonical_unit",
            ],
            dataset["part_specifications"],
        )

        counts["equipment_models"] = write_copy(
            stream,
            "catalog.equipment_models",
            [
                "id",
                "equipment_family",
                "model_code",
                "manufacturer",
            ],
            dataset["equipment_models"],
        )

        counts["part_compatibility"] = write_copy(
            stream,
            "catalog.part_compatibility",
            [
                "id",
                "part_id",
                "equipment_model_id",
                "compatibility_type",
            ],
            dataset["part_compatibility"],
        )

        counts["part_supply"] = write_copy(
            stream,
            "supply.part_supply",
            [
                "id",
                "part_id",
                "plant_id",
                "supplier_id",
                "is_primary_supplier",
                "supplier_share_pct",
                "effective_from",
                "effective_to",
            ],
            dataset["part_supply"],
        )

        counts["economic_facts"] = write_copy(
            stream,
            "economics.part_economic_fact",
            [
                "id",
                "part_id",
                "plant_id",
                "supplier_id",
                "period_start",
                "currency",
                "unit_cost",
                "base_price",
                "ocean_freight",
                "local_transport",
                "import_duty",
                "insurance",
                "packaging",
                "handling_other",
                "purchase_volume",
                "total_spend",
                "source_system",
                "loaded_at",
            ],
            dataset["economic_facts"],
        )

        counts["roles"] = write_copy(
            stream,
            "identity_data.roles",
            [
                "id",
                "code",
                "name",
            ],
            dataset["roles"],
        )

        counts["users"] = write_copy(
            stream,
            "identity_data.users",
            [
                "id",
                "employee_id",
                "first_name",
                "last_name",
                "email",
                "department",
                "location",
                "active",
            ],
            dataset["users"],
        )

        counts["user_roles"] = write_copy(
            stream,
            "identity_data.user_roles",
            [
                "user_id",
                "role_id",
            ],
            dataset["user_roles"],
        )

        counts["expert_profiles"] = write_copy(
            stream,
            "identity_data.expert_profiles",
            [
                "user_id",
                "current_workload",
                "max_capacity",
                "years_experience",
                "historical_success_score",
                "average_investigation_days",
                "primary_expertise",
            ],
            dataset["expert_profiles"],
        )

        counts["opportunities"] = write_copy(
            stream,
            "opportunity.opportunities",
            [
                "id",
                "opportunity_number",
                "part_id",
                "plant_id",
                "status",
                "priority",
                "detection_source",
                "detected_at",
                "current_owner_id",
                "created_at",
                "updated_at",
            ],
            dataset["opportunities"],
        )

        counts["metric_snapshots"] = write_copy(
            stream,
            "opportunity.metric_snapshots",
            [
                "id",
                "opportunity_id",
                "snapshot_at",
                "unit_cost",
                "peer_average_cost",
                "variance_amount",
                "variance_percent",
                "annual_volume",
                "annual_spend",
                "potential_savings",
                "impact_score",
                "confidence_score",
                "benchmark_type",
                "feature_version",
            ],
            dataset["metric_snapshots"],
        )

        counts["cost_drivers"] = write_copy(
            stream,
            "opportunity.cost_drivers",
            [
                "id",
                "opportunity_id",
                "driver_code",
                "driver_name",
                "impact_amount",
                "impact_percent",
                "rank_position",
                "confidence_score",
                "explanation",
            ],
            dataset["cost_drivers"],
        )

        counts["plant_comparisons"] = write_copy(
            stream,
            "opportunity.plant_comparisons",
            [
                "id",
                "opportunity_id",
                "plant_id",
                "unit_cost",
                "peer_average_cost",
                "variance_amount",
                "variance_percent",
                "annual_volume",
                "volume_variance_percent",
                "rank_position",
            ],
            dataset["plant_comparisons"],
        )

        counts["supplier_comparisons"] = write_copy(
            stream,
            "opportunity.supplier_comparisons",
            [
                "id",
                "opportunity_id",
                "supplier_id",
                "unit_cost",
                "peer_average_cost",
                "variance_amount",
                "variance_percent",
                "annual_spend",
                "annual_volume",
                "rank_position",
            ],
            dataset["supplier_comparisons"],
        )

        counts["logistics_components"] = write_copy(
            stream,
            "opportunity.logistics_components",
            [
                "id",
                "opportunity_id",
                "component_code",
                "component_name",
                "brazil_cost",
                "peer_average_cost",
                "variance_amount",
                "variance_percent",
                "rank_position",
            ],
            dataset["logistics_components"],
        )

        counts["logistics_trend"] = write_copy(
            stream,
            "opportunity.logistics_trend",
            [
                "id",
                "opportunity_id",
                "period_start",
                "actual_cost",
                "peer_average_cost",
            ],
            dataset["logistics_trend"],
        )

        counts["tariff_details"] = write_copy(
            stream,
            "opportunity.tariff_details",
            [
                "id",
                "opportunity_id",
                "hs_code",
                "duty_rate",
                "peer_average_duty_rate",
                "calculation_basis",
                "valuation_type",
                "effective_date",
                "import_duty_per_unit",
                "peer_duty_per_unit",
                "annual_duty_impact",
            ],
            dataset["tariff_details"],
        )

        counts["tariff_comparisons"] = write_copy(
            stream,
            "opportunity.tariff_comparisons",
            [
                "id",
                "opportunity_id",
                "plant_id",
                "duty_rate",
            ],
            dataset["tariff_comparisons"],
        )

        counts["ranking_runs"] = write_copy(
            stream,
            "recsys.ranking_runs",
            [
                "id",
                "model_name",
                "model_version",
                "feature_version",
                "started_at",
                "completed_at",
            ],
            dataset["ranking_runs"],
        )

        counts["ranking_results"] = write_copy(
            stream,
            "recsys.ranking_results",
            [
                "id",
                "ranking_run_id",
                "opportunity_id",
                "base_score",
                "confidence_score",
                "final_score",
                "rank_position",
            ],
            dataset["ranking_results"],
        )

        counts["ranking_components"] = write_copy(
            stream,
            "recsys.ranking_score_components",
            [
                "id",
                "ranking_result_id",
                "feature_name",
                "raw_value",
                "normalized_value",
                "weight",
                "contribution",
            ],
            dataset["ranking_components"],
        )

        counts["explanations"] = write_copy(
            stream,
            "recsys.recommendation_explanations",
            [
                "id",
                "ranking_result_id",
                "reason_code",
                "reason_rank",
                "metric_name",
                "metric_value",
                "benchmark_value",
                "explanation_text",
            ],
            dataset["explanations"],
        )

        counts["investigations"] = write_copy(
            stream,
            "workflow.investigations",
            [
                "id",
                "opportunity_id",
                "owner_user_id",
                "status",
                "assigned_at",
                "due_at",
                "progress_percent",
            ],
            dataset["investigations"],
        )

        counts["recommendations"] = write_copy(
            stream,
            "workflow.recommendations",
            [
                "id",
                "investigation_id",
                "title",
                "description",
                "estimated_savings",
                "priority",
                "status",
                "created_at",
            ],
            dataset["recommendations"],
        )

        counts["decisions"] = write_copy(
            stream,
            "workflow.decisions",
            [
                "id",
                "recommendation_id",
                "decision_maker_id",
                "decision_type",
                "comments",
                "decided_at",
            ],
            dataset["decisions"],
        )

        counts["executions"] = write_copy(
            stream,
            "workflow.executions",
            [
                "id",
                "decision_id",
                "owner_user_id",
                "status",
                "progress_percent",
                "expected_savings",
                "realized_savings",
                "planned_end",
            ],
            dataset["executions"],
        )

        counts["outcomes"] = write_copy(
            stream,
            "workflow.outcomes",
            [
                "id",
                "execution_id",
                "expected_savings",
                "realized_savings",
                "savings_realization_percent",
                "baseline_unit_cost",
                "final_unit_cost",
                "success",
                "measured_at",
            ],
            dataset["outcomes"],
        )

        # Useful read-only summary view.
        stream.write(
            """
CREATE OR REPLACE VIEW opportunity.opportunity_summary AS
SELECT
    o.id AS opportunity_id,
    o.status,
    o.priority,
    p.part_number,
    p.component_id,
    p.name AS part_name,
    p.category,
    p.part_family,
    pl.plant_code,
    pl.name AS plant_name,
    pl.country,
    m.unit_cost,
    m.peer_average_cost,
    m.variance_amount,
    m.variance_percent,
    m.potential_savings,
    m.impact_score,
    m.confidence_score
FROM opportunity.opportunities o
JOIN catalog.parts p
    ON p.id = o.part_id
JOIN supply.plants pl
    ON pl.id = o.plant_id
JOIN LATERAL (
    SELECT * FROM opportunity.metric_snapshots ms
    WHERE ms.opportunity_id = o.id
    ORDER BY ms.snapshot_at DESC LIMIT 1
) m ON true;
"""
        )

        stream.write("\nCOMMIT;\n")

    return counts


# ============================================================
# MAIN
# ============================================================


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate a deterministic synthetic CAT Cost "
            "Intelligence PostgreSQL seed."
        )
    )

    parser.add_argument(
        "--output",
        default="../postgres/init/001_seed.sql.gz",
        
        help="Output .sql.gz path",
    )

    parser.add_argument(
        "--parts",
        type=int,
        default=500,
        help="Number of synthetic parts",
    )

    parser.add_argument(
        "--suppliers",
        type=int,
        default=100,
        help="Number of synthetic suppliers",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Random seed",
    )

    args = parser.parse_args()

    if args.parts < 128:
        raise SystemExit(
            "--parts must be at least 128"
        )

    if args.suppliers < 5:
        raise SystemExit(
            "--suppliers must be at least 5"
        )

    rng = random.Random(args.seed)

    print("Generating synthetic dataset...")

    dataset = generate_dataset(
        rng=rng,
        part_count=args.parts,
        supplier_count=args.suppliers,
    )

    output_path = Path(args.output)

    counts = write_seed_sql(
        output_path,
        dataset,
    )

    file_size_mb = (
        output_path.stat().st_size
        / 1024
        / 1024
    )

    print()
    print("Synthetic dataset generated successfully.")
    print(f"Output: {output_path}")
    print(
        f"Compressed SQL size: "
        f"{file_size_mb:.2f} MB"
    )
    print()
    print("Row counts:")

    for key, value in counts.items():
        print(
            f"  {key:<30} {value:>8,}"
        )

    print()
    print(
        "Reference opportunity:"
    )
    print(
        "  OPP-000001 -> "
        "20R-2009 / HP-100045 / Brazil PIR"
    )
    print(
        "  Unit cost:       $421.32"
    )
    print(
        "  Peer average:    $366.23"
    )
    print(
        "  Cost variance:   15%"
    )
    print(
        "  Potential saving $720K"
    )


if __name__ == "__main__":
    main()
