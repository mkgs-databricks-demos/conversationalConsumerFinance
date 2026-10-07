# L100 v5 — Conversational Consumer Finance: System Overview

> **Status:** Draft v5 — Oct 7, 2026
> **Author:** Matthew Giglia
> **Repo:** https://github.com/mkgs-databricks-demos/conversationalConsumerFinance
> **Classification:** Internal — Reusable Reference Architecture

### Purpose

This document is the **constitution** for the Conversational Consumer Finance reference architecture — a locale-driven, phased platform for building conversational banking applications on Databricks. It proves that FIBO's business definitions are fully expressible as UC Semantics, eliminating the need for a separate ontology or knowledge graph as runtime infrastructure.

The architecture is designed for **incremental expansion** across 5 phases — from retail consumer banking (Phase 1) through commercial banking, lending, investments, and bank operations (Phases 2–5) — without modifying existing components. Phase 1 delivers the NN Bank POC; the full-spectrum design serves any banking customer worldwide.

### Origin

Built for the NN Bank (Netherlands) conversational banking engagement. NN's account team positioned OntoBricks (a knowledge graph builder) for a consumer-facing banking app serving 50K customers. This architecture is the rebuttal: a custom agent built on Databricks that uses Genie Agents as the governed query engine, with Lakebase for consumer auth and memory, and MLflow 3 for observability.

### Design Principles

1. **FIBO as context, not infrastructure** — FIBO 2025 Q4 ontology definitions feed Genie Code to generate metric views; no graph DB needed at runtime
2. **Locale-driven everything** — one codebase, three deployments (US/GB/NL); language and locale are metadata, not architecture
3. **If it's worth building for one customer, it's worth building for all** — designed as a reusable reference architecture for any banking customer worldwide
4. **Phase-gated expansion** — 5 phases from retail consumer to full-service bank; each phase adds state machines, tables, and metric views without changing existing ones
5. **Three-bundle DAB** — Bundle 1 (infra), Bundle 2 (data generator, optional per environment), Bundle 3 (app). The generator is an accelerator for lower environments; in production, the customer's real data replaces it via a Genie Code mapping workflow
6. **Streaming always** — Lakeflow Declarative Pipelines (open-source Spark SDP) for all data movement
7. **Deterministic replay** — seeded RNG hierarchy: `simulate(date, seed, locale, phase)` produces identical output
8. **The design is the pitch** — the architecture itself demonstrates why an ontology isn't needed

## System Architecture

### Layer Model

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 6: Consumer Application                                  │
│  Databricks App (Node.js AppKit + React + Lakebase)             │
│  Consumer auth, conversation memory, prompting, guardrails      │
├─────────────────────────────────────────────────────────────────┤
│  Layer 5: Observability                                         │
│  MLflow 3 tracing (OpenTelemetry spans) + Genie Code analysis   │
├─────────────────────────────────────────────────────────────────┤
│  Layer 4: Agent Orchestration                                   │
│  Thin wrapper: inject consumer_guid, call single Genie Agent,   │
│  validate SQL, run ai_decide in parallel, stream response       │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: Semantic Layer (UC Semantics)                         │
│  Metric Views (locale synonyms) + UC Pages (locale language)    │
│  + Genie Agent (locale instructions) + Domains/Subdomains       │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: Data Platform (Medallion)                             │
│  Bronze (6 streaming tables) → Silver (14 FIBO-aligned tables)  │
│  → Gold (3 Enzyme MVs + 3 parameterized metric views)           │
├─────────────────────────────────────────────────────────────────┤
│  Layer 1: Data Generation (State Machine Simulator)             │
│  12 state machines × 40+ episode types × locale config          │
│  Phase-gated: Phase 1 activates 5 SMs; Phases 2–5 add 7 more   │
│  Daily batch via Lakeflow Jobs → Bronze streaming tables        │
└─────────────────────────────────────────────────────────────────┘
```

### Locale Abstraction

A single YAML config file (`locales/{locale}.yaml`) drives all locale-specific behavior. Deploy with `--var locale=nl` (or `us`, `gb`).

| Dimension | US | GB | NL |
|---|---|---|---|
| Currency | USD | GBP | EUR |
| Account ID | Routing + Account | Sort Code + Account | IBAN |
| Payment schemes | ACH, WIRE, ZELLE | BACS, CHAPS, FPS | SCT, SCT_INST, SDD_CORE |
| Salary day | 1st/15th | 25th/28th | 25th |
| Language | en | en-GB | nl |
| Key holiday | Thanksgiving/Black Friday | Boxing Day/January Sales | Sinterklaas/Koningsdag |
| Metric view synonyms | checking account, balance | current account, balance | betaalrekening, saldo |

## Component Inventory (17 components)

| # | Component | Layer | L200 | Status |
|---|---|---|---|---|
| C1 | Locale Config Engine | Cross-cutting | L200-C1 | ✅ Design complete |
| C2 | State Machine Simulator (12 SMs, phase-gated) | Layer 1 | L200-C2 v2 | ✅ Design complete |
| C3 | Lakeflow Pipelines (SDP) | Layer 2 | L200-C3 v2 | ✅ Design complete |
| C4 | FIBO-Aligned Silver Model (14 Phase 1 + 18 future) | Layer 2 | L200-C4 v2 | ✅ Design complete |
| C5 | Metric Views (per locale) | Layer 3 | L200-C5 v2 | ✅ Design complete |
| C6 | UC Pages (per locale, 60 Phase 1 terms) | Layer 3 | L200-C6 v2 | ✅ Design complete |
| C7 | Genie Agent (one per locale) | Layer 3 | L200-C7 v2 | ✅ Design complete |
| C8 | Agent Orchestration (thin wrapper) | Layer 4 | L200-C8 v2 | ✅ Design complete |
| C9 | Knowledge Assistant (Genie Agent volumes) | Layer 4 | L200-C9 | ✅ Design complete |
| C10 | MLflow 3 Tracing | Layer 5 | L200-C10 | ✅ Design complete |
| C11 | Databricks App | Layer 6 | L200-C11 | ✅ Design complete |
| C12 | Lakebase (auth + memory) | Layer 6 | L200-C12 | ✅ Design complete |
| C13 | Genie Code Data Mapping | Cross-cutting | L200-C13 | ✅ Design complete |
| C14 | Gold Materialized Views (Enzyme) | Layer 2 (Gold) | L200-C14 v2 | ✅ Design complete |
| C15 | Deterministic SQL Predicate Validator | Cross-cutting (security) | L200-C15 | ✅ Design complete |
| C16 | ai_decide Soft Validation | Cross-cutting (security) | L200-C16 | ✅ Design complete |
| C17 | Phased Expansion Roadmap | Cross-cutting | L200-C17 | ✅ Design complete |

## Cross-Cutting Patterns

### Governance

All data assets are governed by Unity Catalog. There is **one governance plane** — no separate ontology governance, no graph database ACLs, no parallel permission model.

- **Tables:** UC schemas with `GRANT SELECT` per role
- **Metric Views:** UC-managed, version-controlled via `ALTER VIEW`
- **UC Pages:** Governed definitions with certification/deprecation signals; domain renamed to **Banking** (from Consumer Banking)
- **Genie Agent:** UC permissions scope what data the agent can access
- **Lakebase:** Native Postgres roles for app-level auth; CDF captures all state changes as Delta tables
- **MLflow 3:** Traces stored in UC tables — same audit infrastructure as the data platform

### Observability

Every component emits telemetry to a unified observability stack:

| Component | Telemetry | Destination |
|---|---|---|
| State Machine Simulator | Job metrics, event counts, simulation clock | Lakeflow Job logs |
| Lakeflow Pipelines | Pipeline metrics, data quality, latency | Pipeline monitoring |
| Genie Agent API calls | Request/response, generated SQL, citations | MLflow 3 traces (UC) |
| Lakebase reads/writes | Session state, memory retrieval, auth events | MLflow 3 traces (UC) |
| Knowledge Assistant | Retrieval results, relevance scores | MLflow 3 traces (UC) |
| Databricks App | HTTP requests, errors, latency | OpenTelemetry (logs, metrics, traces) |
| End-to-end consumer request | Full span tree: app → auth → memory → Genie → response | MLflow 3 root trace |

Genie Code provides natural-language analysis of all MLflow 3 traces — "show me the slowest consumer requests this week" or "which Genie Agent queries are failing most often."

### Security: Layered Enforcement Model (19 Checks)

Consumer-facing apps on Databricks face a fundamental identity gap: the platform's `current_user()` returns the app's service principal, not the individual consumer. This design bridges that gap with a layered model that separates **hard enforcement** (deterministic, \~8ms overhead) from **soft validation** (AI-assisted, parallel) and **audit** (asynchronous). See the standalone comparative analysis for how this compares to Barracuda, ADP, Juniper Square, and community patterns.

**Primary enforcement (hard — \~8ms total):**

| # | Check | Mechanism | Enforcement | Latency |
|---|---|---|---|---|
| 1 | JWT validation | API Gateway (assumed for all B2C) | Hard | \~5ms |
| 2 | Session validation | Lakebase session lookup (not per-request JWT) | Hard | \~2ms |
| 3 | Consumer existence | Lakebase lookup | Hard | Included in #2 |
| 4 | Consent check | Lakebase lookup | Hard | Included in #2 |
| 5 | Rate limiting | App layer (per consumer) | Hard | <1ms |
| 6 | Input sanitization | App layer | Hard | <1ms |
| 8 | Required parameter | Parameterized metric view (no default) | Hard | 0ms |
| 9 | Customer_id filter | `filter: customer_id = :consumer_guid` | Hard | 0ms |
| 11 | SQL predicate validation | Deterministic regex/AST UC UDF (C15) | Hard | \~1ms |

**Soft validation (AI-assisted — parallel, doesn't block happy path):**

| # | Check | Mechanism | Enforcement | Latency |
|---|---|---|---|---|
| 7 | Topic guardrails | ai_decide (C16) — "Is this on-topic?" | Soft | \~200ms (parallel) |
| 12 | Result row count sanity | App layer | Soft | <1ms |
| 13 | PII cross-consumer check | ai_decide — "Does response contain other consumer's PII?" | Soft | \~200ms (parallel) |
| 14 | Response appropriateness | ai_decide — "Is this appropriate for consumer-facing?" | Soft | Included in #13 |
| 15 | Language consistency | ai_decide — "Is this in the expected language?" | Soft | Included in #13 |

**Audit (asynchronous — zero latency):**

| # | Check | Mechanism | Enforcement | Latency |
|---|---|---|---|---|
| 16 | Full trace logging | MLflow 3 | Audit | 0ms (async) |
| 17 | Anomaly detection | Lakeflow Job (nightly) | Audit | 0ms (async) |
| 18 | Cross-consumer correlation | Lakeflow Job (nightly) | Audit | 0ms (async) |
| 19 | SQL pattern analysis | Genie Code over MLflow traces | Audit | 0ms (async) |

### Error Handling

| Error Class | Pattern |
|---|---|
| Genie Agent returns no result | App responds with "I couldn't find that information" + logs to MLflow 3 for review |
| Genie Agent returns incorrect language | App-layer language check; re-prompt with explicit language instruction if needed |
| Lakebase connection failure | PgBouncer retry with exponential backoff; circuit breaker after 3 failures |
| Customer not found | Return "account not recognized" without leaking whether the account exists |
| Rate limiting | Genie Agent API rate limits respected; queue excess requests in Lakebase |
| Simulation engine failure | Lakeflow Job retry policy; gap detection on next run; automatic catch-up |

## Technology Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Semantic layer | UC Semantics (Metric Views, Pages, Domains) | One governance plane; same layer serves consumer and enterprise; no separate ontology to maintain |
| Query engine | Genie Agent API (Chat mode + Agent mode) | Managed service; streaming reasoning + citations; stateful conversations; programmatic access |
| App backend | Node.js (Databricks AppKit) | Required stack; AppKit provides Lakebase, OpenTelemetry, Data API plugins |
| App frontend | React | Required stack; NN's mobile app calls the backend API |
| App database | Lakebase (Postgres) | Consumer auth, conversation memory, session state; PgBouncer for 10K concurrent connections |
| Data pipeline | Lakeflow Declarative Pipelines (SDP) | Open-source Spark; portable transformation code; streaming + batch |
| Observability | MLflow 3 + OpenTelemetry | Traces in UC tables; Genie Code for natural-language analysis |
| Data generation | Hierarchical state machine + event sourcing | Deterministic replay; episode-driven longitudinal coherence; locale-driven; phase-gated |
| Deployment | Three-bundle DAB | Bundle 1 (infra), Bundle 2 (data generator, optional), Bundle 3 (app); generator is dev/demo only |
| Data mapping | Genie Code workflow task | Maps customer's source data model to the canonical FIBO-aligned Silver model; replaces the generator in production |
| Version control | GitHub (mkgs-databricks-demos/conversationalConsumerFinance) | Public repo; reusable reference architecture |
| FIBO alignment | FIBO 2025 Q4 (FBC, FND, LOAN, BE, SEC, DER, IND, MD, CAE) | 9 FIBO modules mapped to 32 Silver tables across 5 tiers |

## Data Generation: State Machine Simulator

The simulator generates hyper-realistic synthetic banking data by advancing **12 coupled state machines** through **40+ episode types**, driven by a locale configuration. It is **phase-gated** — Phase 1 activates 5 SMs for retail consumer banking; Phases 2–5 add 7 more for lending, commercial, investments, and operations.

### Phase 1 State Machines (5 active)

| SM | Name | FIBO Concept | States | Transitions |
|---|---|---|---|---|
| SM-1 | Consumer Party Lifecycle | cmns-pts:Party | 7 | 10 |
| SM-3 | Party Relationship | fibo-fbc-pas-caa:AccountHolder | 7 | 9 |
| SM-4 | Deposit Account Lifecycle | fibo-fbc-pas-caa:CustomerAccount | 8 | 10 |
| SM-5 | Transaction Processing | fibo-fbc-pas-caa:IndividualTransaction | 9 | 10 |
| — | Behavioral State Overlay | Extension | 5 | 8 |

### Full-Spectrum State Machines (Phases 2–5)

| SM | Name | Phase | FIBO Concept |
|---|---|---|---|
| SM-2 | Business Party Lifecycle | 3 | fibo-be-le-fbo:FormalOrganization |
| SM-6 | Consumer Loan Lifecycle | 2 | fibo-loan-spc-cns:ConsumerLoan |
| SM-7 | Mortgage Lifecycle | 2 | fibo-loan-reln-mtg:LoanSecuredByRealEstate |
| SM-8 | Credit Card Lifecycle | 2 | fibo-loan-spc-crd:CreditCardAccount |
| SM-9 | Commercial Loan Lifecycle | 3 | fibo-loan-ln-ln:Loan |
| SM-10 | Investment Account Lifecycle | 4 | fibo-sec-sec-ast:InvestmentAccount |
| SM-11 | Securities Lifecycle | 4 | fibo-sec-sec-ast:Security |
| SM-12 | General Ledger (reactive) | 5 | fibo-fbc-pas-caa:AccountingTransaction |

Full transition tables, coupling points, and episode definitions are in **L200-C2 v2**.

### Population Design (Phase 1)

| Entity | Count | Notes |
|---|---|---|
| Consumers | 500 (demo) / 50,000 (load test) | Configurable via locale |
| Accounts per consumer | 1.5 avg | Mix of payment + savings |
| Products | 8–12 | Locale-specific product catalog |
| Daily events per 100 consumers | \~70–140 | Varies by day type |
| Historical backfill | 6 months | For trend analysis |

## Data Platform: Medallion Architecture

### Bronze Layer (6 Phase 1 Streaming Tables)

| Table | Source | Silver Tables Fed |
|---|---|---|
| `bronze.account_events` | SM-1, SM-3, SM-4 transitions | party, person, account, party_relationship, party_kyc |
| `bronze.party_events` | Party attribute changes | party_address, party_contact, party_identifier |
| `bronze.transaction_events` | SM-5 transitions | account_transaction |
| `bronze.product_events` | Product SM transitions | product, account_identifier |
| `bronze.balance_snapshots` | End-of-day balance calculations | account_balance |
| `bronze.statement_events` | Monthly statement generation | account_statement |

### Silver Layer: FIBO-Aligned Canonical Model (14 Phase 1 Tables)

**Tier 1: Party & Relationship (8 tables)**

| Table | FIBO Concept | Key Columns |
|---|---|---|
| `silver.party` | cmns-pts:Party | party_id, party_type, legal_name, party_status, customer_segment |
| `silver.person` | cmns-pts:Person | party_id, first_name, last_name, date_of_birth, nationality |
| `silver.organization` | fibo-be-le-fbo:FormalOrganization | party_id, legal_form, registration_number (schema only in Phase 1) |
| `silver.party_address` | fibo-fnd-plc-adr:PhysicalAddress | party_id, address_type, address_lines, city, postal_code, country_code |
| `silver.party_contact` | fibo-fnd-plc-vrt:VirtualAddress | party_id, contact_type, contact_value, is_verified |
| `silver.party_identifier` | cmns-id:Identifier | party_id, identifier_type, identifier_value_hash |
| `silver.party_relationship` | fibo-fbc-pas-caa:AccountHolder | party_id, related_entity_type, related_entity_id, relationship_type |
| `silver.party_kyc` | Extension (AML/KYC) | party_id, kyc_status, verification_date, risk_score |

**Tier 2: Accounts & Deposits (6 tables)**

| Table | FIBO Concept | Key Columns |
|---|---|---|
| `silver.account` | fibo-fbc-pas-caa:CustomerAccount | account_id, account_type, product_id, currency_code, account_status |
| `silver.account_identifier` | fibo-fbc-pas-caa:AccountIdentifier | account_id, identifier_type (IBAN/sort code/routing), identifier_value |
| `silver.account_balance` | fibo-fbc-pas-caa:Balance | account_id, balance_date, balance_type (LEDGER/AVAILABLE/PENDING/OVERDRAFT), amount |
| `silver.account_transaction` | fibo-fbc-pas-caa:IndividualTransaction | transaction_id, account_id, transaction_status, direction, amount |
| `silver.account_statement` | fibo-fbc-pas-caa:AccountStatement | account_id, period_start, period_end, opening_balance, closing_balance |
| `silver.product` | fibo-fbc-pas-fpas:FinancialProduct | product_id, product_type, credit_limit, interest_rate_type |

All Silver tables use `DECIMAL(20,4)` for monetary amounts, enable Delta CDF, and include `valid_from` / `valid_to` / `is_current` for SCD2 on dimension tables. Full DDL in **L200-C4 v2**.

**Future phase tables:** 18 additional Silver table schemas are created empty in Phase 1 (loan, mortgage, credit_card, investment, GL, etc.) so no DDL changes are needed when a phase is activated. See **L200-C17** for the full expansion roadmap.

### Gold Layer: Two-Layer Metric View Pattern (Speed + Security)

```
Silver Tables (14 FIBO-aligned)
  │
  ▼
Layer 1: SDP Materialized Views (Enzyme-optimized)
  ├── Pre-computed joins via party_relationship → party
  ├── Delta best practices: row tracking, liquid cluster by auto,
  │   change data feed, deletion vectors
  ├── Incremental refresh via Lakeflow pipeline
  ├── NO parameters, NO RLS — pure performance layer
  └── Contains ALL customers' data
  │
  ▼
Layer 2: Parameterized Metric Views (security + semantics)
  ├── Source: Layer 1 materialized views (not raw Silver)
  ├── Parameters: consumer_guid (STRING, no default = REQUIRED)
  ├── Filter: customer_id = :consumer_guid
  ├── Fields + Measures with locale-specific synonyms
  └── Single Genie Agent queries THIS layer
```

**Layer 1: Gold Materialized Views (3 Phase 1)**

| Materialized View | Source Tables | Delta Config |
|---|---|---|
| `gold.mv_customer_transactions` | account_transaction + account + party_relationship + party + account_balance | CLUSTER BY AUTO, row tracking, CDF, deletion vectors |
| `gold.mv_customer_products` | account + product + party_relationship + party | CLUSTER BY AUTO, row tracking, CDF, deletion vectors |
| `gold.mv_customer_behavior` | account_transaction + party_relationship + party (aggregated) | CLUSTER BY AUTO, row tracking, CDF, deletion vectors |

**Layer 2: Parameterized Metric Views (3 Phase 1)**

| Metric View | Source (Layer 1 MV) | Required Parameter | Key Measures |
|---|---|---|---|
| `gold.customer_transaction_metrics` | mv_customer_transactions | consumer_guid (no default) | total_balance, monthly_spend, total_income, transaction_count, avg_transaction_value |
| `gold.customer_product_metrics` | mv_customer_products | consumer_guid (no default) | active_products, total_accounts, savings_balance |
| `gold.customer_behavior_metrics` | mv_customer_behavior | consumer_guid (no default) | total_amount, transaction_count, avg_amount, unique_merchants |

## Semantic Layer: UC Semantics

### Domain & Subdomains

**Domain:** Banking (renamed from Consumer Banking to reflect full-spectrum scope)

**Phase 1 Subdomains (9):** Parties & Identity, Addresses & Contacts, Accounts, Transactions, Balances, Payments, Products & Services, Customer Behavior, Security & Compliance

**Full-spectrum Subdomains (12+):** Phase 1 + Consumer Lending, Mortgage & Real Estate, Credit Cards, Investments & Wealth, Bank Operations

### UC Pages

**60 Phase 1 terms** across 9 subdomains, sourced from FIBO 2025 Q4 with locale variants (EN, EN-GB, NL). 108 total terms across all phases. See **Semantics 02** for the full glossary.

### Genie Agent (one per locale)

A **single Genie Agent per locale** with all 3 metric views + knowledge volume. With only 3 metric views (6% of the 50-table limit), Genie handles domain selection internally — no routing needed.

| Data Source | Type | Purpose |
|---|---|---|
| `gold.customer_transaction_metrics` | Parameterized Metric View | Balances, spending, transactions, categories |
| `gold.customer_product_metrics` | Parameterized Metric View | Product portfolio, account status, eligibility |
| `gold.customer_behavior_metrics` | Parameterized Metric View | Spending trends, anomalies, behavioral patterns |
| `/Volumes/${catalog}/knowledge/` | UC Volume | Product docs, FAQs, fee schedules, regulatory |

Multi-agent split occurs in Phase 3 (consumer + business) and Phase 5 (+ internal). See **L200-C17**.

## Application Layer

### Databricks App (Bundle 3)

**Stack:** Node.js (AppKit) + React + Lakebase + OpenTelemetry + Data API

### Request Flow

```
Consumer → Mobile App → API Gateway (hyperscaler)
  → Authenticate consumer (customer's IdP)
  → Forward: signed consumer identity headers + M2M Databricks SPN
  → Databricks App (Node.js AppKit)
      → 1. Validate session (Lakebase: ~2ms)
      → 2. Load consumer context (language, consent, conversations)
      → 3. Check consent
      → 4. Input sanitization + rate limiting
      → 5. Build Genie Agent request (prepend consumer_guid)
      → 6. Call single Genie Agent (all metric views + knowledge volume)
      → 7. Genie Agent API (Chat mode for stateful conversations)
      → 8. SQL validator (C15): confirm consumer_guid predicate (~1ms)
      → 9. [Parallel] ai_decide (C16): topic, PII, tone, language
      → 10. Stream response to mobile app
      → 11. Log to Lakebase + MLflow 3
      → 12. Check for proactive insights
```

## Deployment: Three-Bundle Architecture

### Bundle 1 — Infrastructure (all environments)

UC catalog + schemas (32 Silver table schemas created), Lakebase project + branches, Lakeflow pipeline (SDP), Lakeflow Jobs, UC Volumes, Genie Code data mapping workflow task.

### Bundle 2 — Data Generator (dev/demo only, optional)

12 state machines (phase-gated), 40+ episode configs, locale merchants, daily simulation job, backfill job. **NOT deployed to production.** Set `phase: 1` for retail consumer; `phase: 2–5` for expansion.

### Bundle 3 — Application (all environments)

Databricks App (Node.js AppKit + React + Lakebase), Genie Agent configs, metric views, UC Pages. Depends on Bundle 1. Does NOT depend on Bundle 2.

## Phased Expansion

The architecture expands incrementally across 5 phases. See **L200-C17** for the full expansion playbook.

| Phase | Scope | SMs | Silver Tables | Gold MVs | Metric Views | UC Pages | Timeline |
|---|---|---|---|---|---|---|---|
| **1** | Retail Consumer | 5 | 14 (+18 empty) | 3 | 3 | 60 | 12 weeks |
| **2** | +Lending & Cards | +3 | +8 | +3 | +3 | +32 | +6 weeks |
| **3** | +Commercial | +2 | +2 (populate) | +2 | +2 | +6 | +4 weeks |
| **4** | +Investments | +2 | +6 | +1 | +1 | +12 | +6 weeks |
| **5** | +Operations | +1 | +4 | +1 | +1 | +6 | +4 weeks |
| **Total** | Full-Spectrum | **12** | **32** | **10** | **10** | **\~116** | **\~32 weeks** |

## L200 Roadmap (all complete)

| L200 | Component | Priority | Status |
|---|---|---|---|
| L200-C1 | Locale Config Engine | P1 | ✅ Complete |
| L200-C2 v2 | State Machine Simulator (12 SMs) | P0 | ✅ Complete |
| L200-C3 v2 | Lakeflow Pipelines (SDP) | P0 | ✅ Complete |
| L200-C4 v2 | FIBO-Aligned Silver Model (32 tables) | P0 | ✅ Complete |
| L200-C5 v2 | Metric Views (per locale) | P1 | ✅ Complete |
| L200-C6 v2 | UC Pages (60 Phase 1 terms) | P1 | ✅ Complete |
| L200-C7 v2 | Genie Agent (one per locale) | P1 | ✅ Complete |
| L200-C8 v2 | Agent Orchestration (thin wrapper) | P2 | ✅ Complete |
| L200-C9 | Knowledge Assistant | P2 | ✅ Complete |
| L200-C10 | MLflow 3 Tracing | P2 | ✅ Complete |
| L200-C11 | Databricks App | P2 | ✅ Complete |
| L200-C12 | Lakebase (auth + memory) | P2 | ✅ Complete |
| L200-C13 | Genie Code Data Mapping | P2 | ✅ Complete |
| L200-C14 v2 | Gold Materialized Views (Enzyme) | P0 | ✅ Complete |
| L200-C15 | SQL Predicate Validator | P1 | ✅ Complete |
| L200-C16 | ai_decide Soft Validation | P2 | ✅ Complete |
| L200-C17 | Phased Expansion Roadmap | P1 | ✅ Complete |

## Proof Points

- **Volta Industrial** — same 5-layer architecture (UC Semantics → Genie Agent → Lakebase → App → AI Gateway) for manufacturing
- **Robinhood Trading Agent** — same state machine + event sourcing pattern for financial data generation; 16 design docs, 54 files
- **RCM Synthetic Data Generator** — same hierarchical state machine + episode architecture for healthcare claims; adapted for pharmacy rebate domain
- **Rx Rebate Horizontal** — dual state machine (Pharmacy Claim SM + Rebate Contract SM) with 5 episode types; 61 glossary terms

## Open Questions

| # | Question | Owner | Status | Resolution |
|---|---|---|---|---|
| 1 | Dutch language support | Architecture | **Resolved** | The Dutch locale deployment is itself the proof point. |
| 2 | NN Bank's IdP | Account team | **Open** | Default assumption: Azure AD B2C. App accepts any OIDC-compliant JWT. |
| 3 | Agent actions in POC scope | Account team | **Open** | Default: no agent actions — Q&A + recommendations only. MCP tools are Phase 3. |
| 4 | PgBouncer connection limit | Architecture | **Resolved** | 10K concurrent connections; 8 CU for POC, 16 CU for production. |
| 5 | Genie API rate limits | Architecture | **Resolved** | 200K conversation limit mitigated by lifecycle policy + request queuing. |

## References

### Research Documents
- Research 01 — FIBO Retail Banking Ontology (notebooks/1987168172322352)
- Research 02 — FIBO-to-Relational Mapping (notebooks/308703764881119)
- Research 05 — Two-Layer Metric View Pattern (notebooks/308703764881180)
- Research 06 — Genie Agent + Parameterized MV Interaction (notebooks/308703764921982)
- Research 07 — Full-Spectrum FIBO Banking Data Generator (notebooks/308703765046744)

### Semantics Documents
- Semantics 01 — Consumer Banking Domain, 32 terms (notebooks/308703764881431) — superseded by Semantics 02
- Semantics 02 — Full-Spectrum Banking Domain, 108 terms (notebooks/308703765065096)

### Visualizations
- FIBO → Silver Model Mapping (interactive HTML, 32 tables, 287 columns)

### External References
- FIBO Ontology: https://spec.edmcouncil.org/fibo/
- FIBO GitHub: https://github.com/edmcouncil/fibo
- FIB-DM Entity List: https://fib-dm.com/
- SEPA Credit Transfer Rulebook: https://www.europeanpaymentscouncil.eu/
- NN Bank OntoBricks Positioning Doc: https://docs.google.com/document/d/1qwe9rEr7pbttZ4Eem77Spm7By-HuERm8u0TiL6aYuNM
- Rebuttal Doc: https://docs.google.com/document/d/1-LnxshVt_wlEhah9K8cX0wA4fBgr5jEgzHH5WBirDXg
- Consumer-Facing Security Patterns Comparative Analysis: https://docs.google.com/document/d/1g4QrTZAEZbkBwcALWjiHaTF2Rca809bfLBnOGuKQ4Eg
