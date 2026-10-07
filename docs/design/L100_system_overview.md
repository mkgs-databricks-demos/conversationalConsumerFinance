# L100 — Conversational Consumer Finance: System Overview

> Following your workflow, this is the markdown canvas companion to `docs/design/L100_system_overview.html`.
>
> Note: this markdown was reconstructed from the Session 4 design artifacts already in the repo (`docs/diagrams/`, pitch deck, and L100 HTML companion), because the original Genie One v5 canvas was not directly readable from this workspace.

## Overview

Conversational Consumer Finance is a governed AI agent that answers consumers' banking questions — accurately, securely, and in their language.

This document defines the system overview and constitution:

* 6 architecture layers
* 3 deployment bundles
* 12 measures / 14 dimensions
* 3 locales: US, GB, NL
* 12-week path to production

## Constitution

These principles govern every component, query, and deployment decision in the system.

### 1. Security is enforced, not implied

Every metric view requires a `consumer_guid` parameter with no default. A query without it fails — it does not return empty and does not fall back. Consumer isolation is enforced at the SQL layer, below the agent and the application.

### 2. Determinism over probability

Every metric has an exact SQL definition generated and tested from FIBO-informed semantics. There is no probabilistic graph traversal between a customer's question and their number.

### 3. One agent, not a swarm

A single Genie agent per locale serves every question from three metric views plus a Knowledge Assistant. No routing layer, no agent-to-agent handoffs, and no cross-agent governance gaps.

### 4. One codebase, any market

Locales are YAML configurations, not forks. The same components deploy as an American, British, or Dutch bank with a single variable.

### 5. The ontology is input

FIBO definitions feed Genie Code, which generates deterministic, tested UC Semantics. The ontology's value is captured; its complexity is not inherited.

### 6. Every answer is auditable

Each question produces an immutable MLflow 3 trace with 8 spans, streamed OpenTelemetry metrics, and automated alert rules. Any answer can be replayed for a regulator.

### 7. Fast at conversation speed

Enzyme-optimized materialized views keep query latency under 200ms and end-to-end response under 3s p99.

## Six-Layer Architecture

Each layer has a single responsibility and a single consumer above it. Governance happens once, at the platform, and every layer inherits it.

* **L6 — Consumer Application**: Databricks App, Lakebase, API Gateway
* **L5 — Observability**: MLflow 3, OpenTelemetry, Genie Code trace analysis
* **L4 — Agent Orchestration**: Single consumer agent per locale, Knowledge Assistant, MCP tools, Vector Search memory, SQL validator
* **L3 — Semantic Layer**: 3 parameterized metric views, 60 UC Pages, consumer banking domain semantics
* **L2 — Data Platform**: Bronze, Silver, Gold medallion architecture with Enzyme optimization
* **L1 — Data Generation**: Full-spectrum simulator and locale configuration, or real banking source systems

```mermaid
block-beta
    columns 1

    block:L6["Layer 6: Consumer Application"]:1
        App["Databricks App\n(Node.js AppKit + React)"]
        Lakebase["Lakebase\nSession · Memory · Consent"]
        Gateway["API Gateway\nJWT · M2M SPN"]
    end

    block:L5["Layer 5: Observability"]:1
        MLflow["MLflow 3 Tracing\nOpenTelemetry Spans"]
        GenieCode["Genie Code\nTrace Analysis"]
    end

    block:L4["Layer 4: Agent Orchestration"]:1
        SingleAgent["Single Consumer Agent\n(per locale · 3 MVs + KA)"]
        KA["Knowledge\nAssistant"]
        MCP["MCP Tools\nBanking APIs"]
        VectorSearch["Vector Search\nLong-term Memory"]
        Validator["SQL Validator\n+ ai_decide"]
    end

    block:L3["Layer 3: Semantic Layer (UC Semantics)"]:1
        MetricViews["3 Parameterized Metric Views\nconsumer_guid required · 12 measures"]
        Pages["60 UC Pages (Phase 1)\nFIBO-sourced · 12 subdomains"]
        Domains["Domain: Consumer Banking\n12 Subdomains · 108 terms"]
    end

    block:L2["Layer 2: Data Platform (Medallion)"]:1
        Gold["Gold: 3 Enzyme MVs\nLiquid Cluster · CDF · Row Tracking"]
        Silver["Silver: 14 FIBO-Aligned Tables (Phase 1)\nSCD2 · DECIMAL(20,4) · party_relationship"]
        Bronze["Bronze: Streaming Tables\nRaw Events · VARIANT"]
    end

    block:L1["Layer 1: Data Generation"]:1
        StateMachine["Full-Spectrum Simulator\n12 SMs × 40+ Episodes × 5 Tiers"]
        LocaleConfig["Locale Config\nUS · GB · NL"]
    end

    L6 --> L5
    L5 --> L4
    L4 --> L3
    L3 --> L2
    L2 --> L1
```

## Three-Bundle Deployment

Bundle 1 is the infrastructure and ships to every environment. Bundle 2 is the full-spectrum generator for dev/demo and is optional in production. Bundle 3 is the consumer application and semantic surface.

```mermaid
graph TB
    subgraph B1["Bundle 1: Infrastructure<br/>(All Environments)"]
        B1_UC["UC Catalog + Schemas<br/>bronze · silver · gold"]
        B1_LB["Lakebase Project<br/>+ Branches (prod/dev/test)"]
        B1_SDP["Lakeflow Pipeline (SDP)<br/>Bronze → Silver → Gold"]
        B1_Jobs["Lakeflow Jobs<br/>Proactive Insights · Mapping"]
        B1_Vol["UC Volumes<br/>KA Documents · Mapping Specs"]
    end

    subgraph B2["Bundle 2: Data Generator<br/>(Dev/Demo ONLY — Optional)"]
        B2_SM["Full-Spectrum Simulator<br/>12 SMs × 40+ Episodes × 5 Tiers"]
        B2_Daily["Daily Simulation Job<br/>Lakeflow Job @ 6 AM"]
        B2_Back["Backfill Job<br/>On-demand · 6 months"]
        B2_Locale["Locale Configs<br/>US · GB · NL"]
    end

    subgraph B3["Bundle 3: Application<br/>(All Environments)"]
        B3_App["Databricks App<br/>Node.js AppKit + React"]
        B3_GA["Single Genie Agent<br/>Per Locale (3 MVs + KA)"]
        B3_MV["3 Metric Views<br/>Parameterized · Per Locale"]
        B3_Pages["60 UC Pages (Phase 1)<br/>Per Locale · 12 Subdomains"]
        B3_Domain["UC Domain + 12 Subdomains<br/>Consumer Banking"]
    end

    B2_SM -->|"writes events"| B1_UC
    B3_App -->|"depends on"| B1_LB
    B3_App -->|"queries via"| B3_GA
    B3_GA -->|"queries"| B3_MV
    B3_MV -->|"sources from"| B1_UC

    style B2_SM fill:#ffd700,stroke:#333
    style B2_Daily fill:#ffd700,stroke:#333
    style B2_Back fill:#ffd700,stroke:#333
    style B2_Locale fill:#ffd700,stroke:#333
```

## Consumer Request Flow

A consumer question enters through the API Gateway, passes session and consent checks in Lakebase, then reaches a single agent. The agent queries a parameterized metric view with the required `consumer_guid`; a post-query SQL validator confirms the consumer predicate, while `ai_decide` checks topic, PII, appropriateness, and language in parallel. The full trace lands in MLflow 3.

```mermaid
sequenceDiagram
    participant Consumer
    participant MobileApp as Mobile App
    participant Gateway as API Gateway
    participant App as Databricks App<br/>(Node.js)
    participant LB as Lakebase<br/>(Session Store)
    participant Agent as Single Genie Agent<br/>(3 MVs + KA)
    participant MV as Parameterized<br/>Metric View
    participant Validator as SQL Validator<br/>(Regex/AST UDF)
    participant AiDecide as ai_decide<br/>(Parallel)
    participant MLflow as MLflow 3

    Consumer->>MobileApp: "Hoeveel heb ik uitgegeven?"
    MobileApp->>Gateway: Request + consumer JWT
    Gateway->>Gateway: Validate JWT (~5ms)
    Gateway->>App: Signed headers + M2M SPN

    App->>LB: Session lookup (~2ms)
    alt First request
        LB-->>App: Create session (consumer_guid, token, consent)
    else Existing session
        LB-->>App: Return session (consumer_guid, language, consent)
    end

    App->>App: Check consent ✓
    App->>App: Input sanitization ✓
    App->>App: Rate limit check ✓

    Note over App,Agent: Single agent — no routing needed
    App->>Agent: Question + consumer_guid<br/>+ language instruction + context
    Agent->>MV: SELECT MEASURE(monthly_spend)<br/>FROM customer_transaction_metrics<br/>(consumer_guid => 'abc-123')
    MV->>MV: Required parameter enforced ✓
    MV-->>Agent: Results (consumer's data only)
    Agent-->>App: SQL + results + citations

    App->>Validator: Validate SQL predicate (~1ms)
    Validator-->>App: ✓ consumer_guid present

    par Parallel soft validation
        App->>AiDecide: Topic + PII + Tone + Language
        AiDecide-->>App: All checks passed
    end

    App->>Consumer: Stream Dutch response
    App->>LB: Log message + SQL + citations
    App->>MLflow: Full trace (all spans)
```

## Semantic Layer

The semantic layer is a two-layer pattern:

* **Layer 1**: Enzyme-optimized materialized views for performance only
* **Layer 2**: consumer-facing parameterized metric views with `consumer_guid` required, 12 measures, 14 dimensions, and locale synonyms

The single Genie agent uses 4 of its 50 allowed sources: the three metric views plus the Knowledge Assistant volume.

```mermaid
graph TB
    subgraph Silver["Silver Layer (14 FIBO-Aligned Phase 1 Tables)"]
        S_Cust["silver.customer"]
        S_Acct["silver.account"]
        S_Hold["silver.account_holder"]
        S_Txn["silver.account_transaction"]
        S_Bal["silver.account_balance_daily"]
        S_Prod["silver.product"]
        S_Party["silver.party_relationship"]
        S_Ident["silver.account_identifier"]
        S_Stmt["silver.account_statement"]
        S_More["+ 5 more Phase 1 tables"]
    end

    subgraph Layer1["Layer 1: SDP Materialized Views<br/>(Enzyme-Optimized · NO RLS · NO Parameters)"]
        MV_Txn["gold.mv_customer_transactions<br/>CLUSTER BY AUTO · Row Tracking<br/>CDF · Deletion Vectors"]
        MV_Prod["gold.mv_customer_products"]
        MV_Behav["gold.mv_customer_behavior"]
    end

    subgraph Layer2["Layer 2: Parameterized Metric Views<br/>(Required consumer_guid · Locale Synonyms · 12 Measures)"]
        PM_Txn["gold.customer_transaction_metrics<br/>filter: customer_id = :consumer_guid<br/>5 measures · 8 fields"]
        PM_Prod["gold.customer_product_metrics<br/>filter: customer_id = :consumer_guid<br/>3 measures · 3 fields"]
        PM_Behav["gold.customer_behavior_metrics<br/>filter: customer_id = :consumer_guid<br/>4 measures · 3 fields"]
    end

    subgraph Consumers["Single Genie Agent (per locale)"]
        GA["Consumer Banking Agent<br/>3 MVs + KA · 10+ example SQL<br/>4 of 50 source limit"]
    end

    S_Cust --> MV_Txn
    S_Acct --> MV_Txn
    S_Hold --> MV_Txn
    S_Txn --> MV_Txn
    S_Bal --> MV_Txn
    S_Party --> MV_Txn
    S_Acct --> MV_Prod
    S_Hold --> MV_Prod
    S_Cust --> MV_Prod
    S_Prod --> MV_Prod
    S_Party --> MV_Prod
    S_Txn --> MV_Behav
    S_Cust --> MV_Behav

    MV_Txn --> PM_Txn
    MV_Prod --> PM_Prod
    MV_Behav --> PM_Behav

    PM_Txn --> GA
    PM_Prod --> GA
    PM_Behav --> GA

    style Layer1 fill:#e6f3ff,stroke:#0066cc
    style Layer2 fill:#fff3e6,stroke:#cc6600
```

## Security Model

There are 16 controls across 3 rings:

* **Hard enforcement (~8ms)**: JWT validation, session validation, consent, rate limiting, sanitization, required parameter, customer filter, SQL predicate validator
* **Soft validation (~200ms, parallel)**: topic, cross-consumer PII, response appropriateness, language consistency
* **Audit (async, 0ms)**: MLflow 3 trace, nightly anomaly detection, cross-consumer correlation, SQL pattern analysis

The parameterized metric view is the keystone: `consumer_guid` is required, with no default. A query without it fails.

```mermaid
graph TB
    subgraph Hard["HARD ENFORCEMENT (~8ms)"]
        direction TB
        H1["1. JWT Validation<br/>API Gateway · ~5ms"]
        H2["2. Session Validation<br/>Lakebase Lookup · ~2ms"]
        H3["3. Consent Check<br/>Lakebase · included in #2"]
        H4["4. Rate Limiting<br/>App Layer · <1ms"]
        H5["5. Input Sanitization<br/>App Layer · <1ms"]
        H6["6. Required Parameter<br/>Parameterized MV · 0ms"]
        H7["7. Customer Filter<br/>customer_id = :consumer_guid · 0ms"]
        H8["8. SQL Predicate Validator<br/>Regex/AST UC UDF · ~1ms"]
    end

    subgraph Soft["SOFT VALIDATION (parallel · ~200ms)"]
        direction TB
        S1["9. Topic Guardrails<br/>ai_decide: on-topic?"]
        S2["10. PII Cross-Consumer<br/>ai_decide: other consumer's PII?"]
        S3["11. Response Appropriateness<br/>ai_decide: consumer-safe?"]
        S4["12. Language Consistency<br/>ai_decide: correct language?"]
    end

    subgraph Audit["AUDIT (async · 0ms)"]
        direction TB
        A1["13. MLflow 3 Trace<br/>Full immutable record"]
        A2["14. Nightly Anomaly Detection<br/>Lakeflow Job"]
        A3["15. Cross-Consumer Correlation<br/>Lakeflow Job"]
        A4["16. SQL Pattern Analysis<br/>Genie Code"]
    end

    H1 --> H2 --> H3 --> H4 --> H5
    H5 -->|"Single Agent call"| H6 --> H7
    H7 -->|"Post-query"| H8

    H5 -.->|"parallel"| S1
    H8 -.->|"parallel"| S2

    H8 -->|"async"| A1

    style Hard fill:#d4edda,stroke:#28a745
    style Soft fill:#fff3cd,stroke:#ffc107
    style Audit fill:#d1ecf1,stroke:#17a2b8
```

## Data Platform

Bronze holds raw streaming events. Silver applies the FIBO-aligned model: 14 Phase 1 tables with SCD2, CDF, and precise money types. Gold implements the two-layer metric-view pattern. In production, the simulator is replaced by real source systems mapped through the same event contracts.

```mermaid
graph TB
    subgraph Generator["Bundle 2: Full-Spectrum Simulator (Dev/Demo)"]
        SM["12 Coupled State Machines\n× 40+ Episode Types\n× 5 Tiers × Locale Config"]
    end

    subgraph RealData["Production: Customer Source Systems"]
        Source["Core Banking\nCard Processing\nPayments"]
        GCMap["Genie Code\nMapping Workflow"]
    end

    subgraph Bronze["Bronze Layer (Streaming Tables)"]
        B_Acct["bronze.account_events"]
        B_Txn["bronze.transaction_events"]
        B_Prod["bronze.product_events"]
        B_Bal["bronze.balance_snapshots"]
        B_Party["bronze.party_events"]
    end

    subgraph Silver["Silver Layer (14 FIBO-Aligned Phase 1 Tables)"]
        S_Cust["silver.customer\nSCD2 · CDF"]
        S_Acct["silver.account\nSCD2 · CDF"]
        S_Hold["silver.account_holder\nSCD2 · CDF"]
        S_Txn["silver.account_transaction\nPartitioned · CDF"]
        S_Bal["silver.account_balance_daily\nPartitioned · CDF"]
        S_Prod["silver.product · CDF"]
        S_Party["silver.party_relationship\nJoin path: party → account"]
        S_Ident["silver.account_identifier"]
        S_Stmt["silver.account_statement"]
        S_More["+ 5 more Phase 1 tables"]
    end

    subgraph Gold["Gold Layer: Two-Layer Pattern"]
        subgraph L1["Layer 1: Enzyme Materialized Views"]
            MV1["mv_customer_transactions\nCLUSTER BY AUTO"]
            MV2["mv_customer_products"]
            MV3["mv_customer_behavior"]
        end
        subgraph L2["Layer 2: Parameterized Metric Views"]
            PM1["customer_transaction_metrics\nconsumer_guid REQUIRED"]
            PM2["customer_product_metrics\nconsumer_guid REQUIRED"]
            PM3["customer_behavior_metrics\nconsumer_guid REQUIRED"]
        end
    end

    subgraph Consumers["Single Genie Agent (per locale)"]
        GA["Consumer Banking Agent\n3 MVs + KA · 10+ example SQL"]
    end

    SM -->|"daily events"| Bronze
    Source -->|"real data"| GCMap
    GCMap -->|"mapped events"| Bronze

    Bronze -->|"SDP Pipeline\n(streaming)"| Silver
    Silver -->|"SDP Pipeline\n(incremental refresh)"| L1
    L1 --> L2
    L2 --> GA

    style Generator fill:#ffd700,stroke:#333
    style RealData fill:#e6ffe6,stroke:#333
    style L1 fill:#e6f3ff,stroke:#0066cc
    style L2 fill:#fff3e6,stroke:#cc6600
```

## Sessions & Memory

Lakebase owns session state. First request creates a session bound to the consumer GUID with language and consent state. Subsequent requests validate the session token in ~2ms without revalidating the JWT. Expired sessions require reauth. Vector Search provides long-term memory across sessions.

```mermaid
sequenceDiagram
    participant Consumer
    participant Gateway as API Gateway
    participant App as Databricks App
    participant LB as Lakebase<br/>(PgBouncer)
    participant VS as Vector Search<br/>(Memory)

    Note over Consumer,VS: First Request in Session

    Consumer->>Gateway: Request + JWT
    Gateway->>Gateway: Validate JWT<br/>Extract consumer claims
    Gateway->>App: Signed headers<br/>(consumer_guid, language)<br/>+ M2M SPN

    App->>LB: Lookup consumer_guid
    LB-->>App: Consumer record<br/>(language_pref, consent_state)
    App->>LB: Create session<br/>(session_token, expires_at, consumer_guid)
    LB-->>App: session_token
    App->>VS: Retrieve past conversations<br/>(semantic search)
    VS-->>App: Relevant memory fragments
    App-->>Consumer: Response + session_token

    Note over Consumer,VS: Subsequent Requests (Same Session)

    Consumer->>App: Request + session_token
    App->>LB: Validate session_token (~2ms)
    LB-->>App: Valid ✓<br/>(consumer_guid, language, consent)
    Note right of App: No JWT revalidation needed
    App->>LB: Load active conversation
    LB-->>App: conversation_id, recent messages
    App-->>Consumer: Response

    Note over Consumer,VS: Session Expired

    Consumer->>App: Request + expired session_token
    App->>LB: Validate session_token
    LB-->>App: Expired ✗
    App-->>Consumer: 401 — Reauth required
    Consumer->>Gateway: Refresh JWT
    Gateway-->>Consumer: New JWT
    Note right of Consumer: Flow restarts as<br/>"First Request"
```

## Multi-Locale

All components are locale-neutral. Locale YAML files carry currency, payment rails, account naming, holidays, merchant mixes, and language. Deploying a new market is a config file and a bundle variable.

```mermaid
graph TB
    subgraph Codebase["One Codebase (17 Components)"]
        SM["State Machine<br/>Simulator (12 SMs)"]
        SDP["Lakeflow<br/>Pipeline (SDP)"]
        MV_Template["3 Metric View<br/>YAML Templates"]
        Page_Template["60 UC Page<br/>Templates"]
        Agent_Template["Genie Agent<br/>Template"]
        App["Databricks App"]
        Validator["SQL Validator"]
    end

    subgraph Locales["Locale Config (YAML)"]
        US["locales/us.yaml<br/>USD · ACH · Routing#<br/>Thanksgiving · Walmart<br/>checking account"]
        GB["locales/gb.yaml<br/>GBP · FPS · Sort Code<br/>Boxing Day · Tesco<br/>current account"]
        NL["locales/nl.yaml<br/>EUR · SCT · IBAN<br/>Sinterklaas · Albert Heijn<br/>betaalrekening"]
    end

    subgraph Deployments["Three Deployments"]
        US_Deploy["American Bank<br/>--var locale=us"]
        GB_Deploy["British Bank<br/>--var locale=gb"]
        NL_Deploy["Dutch Bank<br/>--var locale=nl"]
    end

    Codebase -->|"reads"| US --> US_Deploy
    Codebase -->|"reads"| GB --> GB_Deploy
    Codebase -->|"reads"| NL --> NL_Deploy

    subgraph US_Output["US Output"]
        US_Data["USD transactions<br/>ACH/WIRE/ZELLE<br/>Walmart, Starbucks"]
        US_MV["Synonyms: checking<br/>account, balance"]
        US_Agent["Language: English<br/>Holidays: Thanksgiving"]
    end

    subgraph NL_Output["NL Output"]
        NL_Data["EUR transactions<br/>SCT/SCT_INST/SDD<br/>Albert Heijn, NS"]
        NL_MV["Synonyms: betaalrekening<br/>saldo, overschrijving"]
        NL_Agent["Language: Nederlands<br/>Holidays: Sinterklaas"]
    end

    US_Deploy --> US_Output
    NL_Deploy --> NL_Output

    style US fill:#b3d9ff,stroke:#0066cc
    style GB fill:#ffcccc,stroke:#cc0000
    style NL fill:#ffe6b3,stroke:#cc6600
```

## Agent Orchestration

The app layer injects `consumer_guid` into every agent call. The Consumer Banking Agent answers from the three metric views and the Knowledge Assistant volume, then every generated SQL statement passes the predicate validator with `ai_decide` running in parallel. There is deliberately no router, no multi-agent graph, and no fallback path that bypasses the semantic layer.

```mermaid
flowchart TB
    Consumer[Consumer Question]
    subgraph AppLayer[Databricks App Layer]
        Session[Session Lookup]
        Sanitize[Input Sanitization]
        Inject[Inject consumer_guid]
    end
    subgraph SingleAgent[Single Genie Agent per locale]
        Agent[Consumer Banking Agent]
        MV_Txn[customer_transaction_metrics]
        MV_Prod[customer_product_metrics]
        MV_Behav[customer_behavior_metrics]
        KA_Vol[Knowledge Volume]
    end
    subgraph PostQuery[Post-Query Validation]
        SQLVal[SQL Predicate Validator]
        AiDecide[ai_decide parallel]
    end
    Consumer --> Session --> Sanitize --> Inject
    Inject --> Agent
    Agent --> MV_Txn
    Agent --> MV_Prod
    Agent --> MV_Behav
    Agent --> KA_Vol
    Agent --> SQLVal --> AiDecide
    style SingleAgent fill:#e6f3ff,stroke:#0066cc
    style PostQuery fill:#fff3cd,stroke:#ffc107
```

## Delivery

### 12-week path to production

| Phase | Weeks | Focus |
| --- | --- | --- |
| Phase 1 | 1–2 | Foundation — data generation, FIBO mapping, Silver tables, first metric views |
| Phase 2 | 3–5 | App spike — consumer app, security pipeline, first working demo |
| Phase 3 | 6–9 | Expansion — full metric coverage, multi-locale, observability, benchmark suite |
| Phase 4 | 10–12 | Production — load testing, runbooks, alerting, go-live |

Staffing assumptions:

* ~0.75 Databricks FTE
* ~2.5 Bank FTE
* 2 weeks to first working demo

## Diagram Index

Interactive companions live in `docs/diagrams/html/`, with lightweight wrappers in `docs/diagrams/svg/` and sources in `docs/diagrams/mermaid/`.

* `01_six_layer_architecture.md`
* `02_three_bundle_deployment.md`
* `03_consumer_request_flow.md`
* `04_two_layer_metric_view.md`
* `05_layered_security_model.md`
* `06_account_lifecycle_state_machine.md`
* `07_transaction_processing_state_machine.md`
* `08_product_relationship_state_machine.md`
* `09_state_machine_coupling_points.md`
* `10_medallion_architecture.md`
* `11_lakebase_session_lifecycle.md`
* `12_genie_code_data_mapping_workflow.md`
* `13_locale_abstraction.md`
* `14_daily_simulation_execution_flow.md`
* `15_agent_orchestration_routing.md`
* `16_two_layer_metric_view_data_flow.md`
* `17_genie_code_mapping_workflow.md`
