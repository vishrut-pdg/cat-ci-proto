# AI Logic in the CAT Cost Intelligence Codebase

This document explains the AI-related logic in simple technical English.

The codebase has two separate intelligent features:

1. An **opportunity ranking system** that uses fixed rules and weights.
2. An **AI assistant** that answers questions about one opportunity using Gemini or a local fallback.

The ranking system is not a trained machine-learning model. Only the assistant calls a generative AI model.

## 1. Opportunity ranking

The ranking system decides which cost-saving opportunities should appear first. Its main code is in `backend/app/recsys/` and `backend/app/services/recsys_service.py`.

### Processing flow

1. `RecSysRepository.get_candidates()` loads opportunity, part, plant, cost, logistics, tariff, savings, impact, and confidence data from PostgreSQL.
2. `is_candidate_eligible()` removes unsuitable opportunities.
3. `normalize_candidate_features()` converts different business values to a common range from `0` to `1`.
4. `rank_features()` multiplies each normalized value by its configured weight and adds the results.
5. Candidates are sorted from the highest score to the lowest score.
6. `build_explanations()` creates up to three readable reasons for each result.
7. The ranking run, final results, score components, and explanations are stored in PostgreSQL in one transaction.

### Eligibility rules

An opportunity is ranked only when all these rules pass:

- Status is `IDENTIFIED` or `AWAITING_REVIEW`.
- Potential savings are at least `USD 50,000`.
- Confidence score is at least `0.65`.
- Peer average cost is greater than zero.

Rejected candidates are not included in the ranking.

### Feature normalization

Normalization makes values with different units comparable.

| Feature | Normalized calculation |
|---|---|
| Potential savings | Candidate savings / highest eligible savings |
| Cost variance | Absolute variance percent / 25 |
| Impact score | Impact score / 100 |
| Logistics variance | Positive logistics variance percent / 60 |
| Tariff variance | Positive tariff variance percent / 100 |
| Data confidence | Confidence score as stored |

Every result is limited to the range `0` to `1`. For example, a cost variance of 25% or more becomes `1`.

### Score calculation

The score is a weighted sum:

```text
score =
    potential_savings     * 0.25
  + cost_variance         * 0.20
  + impact_score          * 0.15
  + logistics_variance    * 0.15
  + tariff_variance       * 0.10
  + data_confidence       * 0.15
```

The internal score is between `0` and `1`. The API multiplies it by 100, so the frontend receives a score between `0` and `100`.

Weights and thresholds are defined in `backend/app/recsys/config.py`. The current model label is `weighted-opportunity-ranker`, version `v1.0.0`, with feature version `features-v1`.

### Explanations

Readable explanation reasons are added when a raw business value crosses a threshold:

- Unit cost is at least 10% above the peer benchmark.
- Logistics cost is at least 20% above the peer benchmark.
- Import duty is at least 25% above the peer benchmark.
- Potential annual savings are at least `USD 250,000`.

These explanations do not change the score. They explain the source data behind a recommendation.

### Ranking API

- `POST /api/v1/recsys/rank` runs and stores a new ranking.
- `GET /api/v1/recsys/recommendations` returns results from the latest stored run.

## 2. Grounded AI assistant

The assistant answers questions about a selected opportunity. Its main code is in `backend/app/services/assistant_service.py`.

### Request flow

1. The frontend sends an opportunity ID, a user message, and optionally a session ID to `POST /api/v1/assistant/chat`.
2. `get_grounded_context()` loads current database evidence for that opportunity:
   - summary and metrics;
   - overview and cost drivers;
   - plants;
   - suppliers;
   - logistics;
   - tariff details;
   - time-series data.
3. The service checks that the opportunity exists and that an existing session belongs to the current user and opportunity.
4. For an existing session, it loads up to eight recent interaction pairs for conversation context.
5. If Vertex AI is configured, the service sends the system prompt, structured evidence, conversation history, and current question to Gemini.
6. If Vertex AI is missing or fails, deterministic local logic builds an answer from the same database evidence.
7. The response and basic telemetry are stored in PostgreSQL.

### Grounding rules

The system prompt tells Gemini to:

- answer only from the supplied opportunity evidence;
- never invent costs, percentages, savings, suppliers, plants, tariffs, or findings;
- separate actual values from peer benchmarks;
- include numerical evidence;
- say when data is unavailable;
- format money as USD;
- treat suggestions as analysis, not approvals.

This is application-level grounding. The model receives a structured snapshot from the database instead of being allowed to search freely or query arbitrary records.

### Gemini configuration

The default model is `gemini-2.5-flash`. It can be changed with `GEMINI_MODEL`.

Vertex AI is used when `GOOGLE_CLOUD_PROJECT` is set. `GOOGLE_CLOUD_LOCATION` defaults to `global`. Authentication is handled by Google Application Default Credentials or the service-account setup described in `README.md`.

### Local fallback

The assistant remains usable without Vertex AI. The local fallback does not generate free-form AI text. It selects a response template by looking for simple keywords in the question:

- `supplier` or `negotiat` selects supplier evidence;
- `logistic`, `freight`, or `component` selects logistics evidence;
- `tariff`, `duty`, or `import` selects tariff evidence;
- `plant` or `volume` selects plant evidence;
- `next`, `recommend`, or `action` returns a suggested validation order;
- other questions return the leading cost drivers.

For a short follow-up such as “compare that,” it also includes the previous user question when choosing a template. All numbers still come from the structured database context.

The API response identifies which path produced the answer:

- `provider: "vertex_ai"` for Gemini;
- `provider: "local_grounded_fallback"` for the local fallback.

If Gemini fails, `provider_note` contains a short failure type. It does not expose a full internal stack trace to the client.

### Sessions and telemetry

Assistant sessions are scoped to both the current user and opportunity. The API supports:

- `GET /api/v1/assistant/sessions/{session_id}` for one session;
- `GET /api/v1/assistant/history/latest/{opportunity_id}` for the user's latest session on an opportunity.

The backend stores:

- session ownership and last activity;
- user and assistant messages;
- model name and latency;
- a record of the `get_grounded_context` tool call.

Telemetry write failure is logged and rolled back, but it does not replace an answer that was already generated.

## Important limitations

- Ranking quality depends on the accuracy of database metrics and configured weights.
- The ranking weights are hand-written business rules and do not learn from outcomes.
- Gemini grounding reduces hallucination risk but cannot guarantee that every generated statement is correct.
- The local fallback understands only its defined keyword topics.
- Conversation history is limited to eight recent interaction pairs when producing a new answer.
- The assistant reads evidence for one opportunity at a time and does not make workflow approvals or database decisions.

## Main files

| File | Responsibility |
|---|---|
| `backend/app/recsys/config.py` | Ranking weights, thresholds, and version labels |
| `backend/app/recsys/filters.py` | Candidate eligibility rules |
| `backend/app/recsys/features.py` | Feature normalization |
| `backend/app/recsys/ranker.py` | Weighted score calculation |
| `backend/app/recsys/explanations.py` | Human-readable ranking reasons |
| `backend/app/services/recsys_service.py` | Full ranking workflow and persistence |
| `backend/app/services/assistant_service.py` | Gemini call, local fallback, sessions, and telemetry |
| `backend/app/agents/prompts.py` | Assistant grounding instructions |
| `backend/app/agents/tools/opportunity_tools.py` | Structured opportunity context boundary |
| `backend/app/api/v1/recsys.py` | Ranking API routes |
| `backend/app/api/v1/assistant.py` | Assistant API routes |
