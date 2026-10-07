# L200-C17: Phased Expansion Roadmap — Detailed Design

> **Status:** Draft v1 — Oct 7, 2026
> **Author:** Matthew Giglia
> **Parent:** L100 — Conversational Consumer Finance: System Overview
> **Component:** C17 — Phased Expansion Roadmap (Cross-cutting)
> **Priority:** P1
> **Bundle:** All bundles (expansion is additive per phase)

## Overview

The Conversational Consumer Finance architecture is designed for **incremental expansion** — each phase adds new state machines, Silver tables, Gold MVs, metric views, UC Pages, and Genie Agent capabilities without modifying existing components. This L200 is the **expansion playbook** — it specifies exactly what changes in every other L200 when a new phase is activated, so an FDE can pick up any phase and know precisely what to build.

The existing L200s (C1–C16) are complete and correct for **Phase 1 (Retail Consumer)**. This document defines the delta for Phases 2–5.

## Phase Summary

| Phase | Scope | New SMs | New Silver Tables | New Gold MVs | New Metric Views | New UC Pages | Timeline |
|---|---|---|---|---|---|---|---|
| **1** | Retail Consumer | 5 (SM-1,3,4,5 + behavioral) | 8 (party→product + identifiers, statements) | 3 | 3 | 60 | 12 weeks |
| **2** | Retail Lending + Cards | 3 (SM-6,7,8) | 8 (loan→credit_card_statement) | 3 | 3 | 32 | 6 weeks |
| **3** | Commercial Banking | 2 (SM-2,9) | 2 (organization expanded, commercial_facility) | 2 | 2 | 6 | 4 weeks |
| **4** | Investments & Wealth | 2 (SM-10,11) | 6 (investment_account→market_data) | 1 | 1 | 12 | 6 weeks |
| **5** | Bank Operations | 1 (SM-12) | 4 (gl→interest_rate_reference) | 1 | 1 | 6 | 4 weeks |
| **Total** | Full-Spectrum Bank | **12** + behavioral | **32** | **10** | **10** | **\~108** | **\~32 weeks** |

## Phase 2: Retail Lending + Cards

**Trigger:** Phase 1 complete and validated. Customer wants lending and credit card capabilities.

### L200 Impact Matrix

| L200 | Component | Change Type | What's Added |
|---|---|---|---|
| **C2** | State Machine Simulator | **Add** | SM-6 (Consumer Loan), SM-7 (Mortgage), SM-8 (Credit Card). 10 new episodes (#15–24). Set `phase: 2` in Bundle 2 config. |
| **C3** | Lakeflow Pipelines | **Add** | 4 new Bronze streaming tables: `bronze.loan_events`, `bronze.mortgage_events`, `bronze.credit_card_events`, `bronze.loan_payment_events`. 4 new archive tables. 8 new YAML event definitions. |
| **C4** | Silver Model | **Add** | 8 new Silver tables: `loan`, `loan_payment`, `loan_event`, `mortgage`, `mortgage_property`, `credit_card`, `credit_card_statement`, `commercial_facility` (schema only, populated in Phase 3). |
| **C14** | Gold MVs | **Add** | 3 new Gold MVs: `mv_customer_loans` (loan + payment + party), `mv_customer_mortgage` (mortgage + property + payment + party), `mv_customer_cards` (credit_card + statement + transaction + party). |
| **C5** | Metric Views | **Add** | 3 new parameterized metric views: `consumer_loan_metrics`, `consumer_mortgage_metrics`, `consumer_card_metrics`. Same `consumer_guid` parameter pattern. |
| **C6** | UC Pages | **Add** | 32 new terms from Semantics 02 subdomains 8 (Consumer Lending), 9 (Mortgage), 10 (Credit Cards). |
| **C7** | Genie Agent | **Modify** | Add 3 new metric views to the single consumer agent (now 6 of 50 sources). Add 10+ new example SQL queries for lending/mortgage/card questions. |
| **C1** | Locale Config | **Add** | Locale-specific lending terms: mortgage types per locale (NL: annuïteitenhypotheek, lineaire hypotheek; US: 30-year fixed, 5/1 ARM; GB: fixed rate, tracker). Card networks per locale. |
| **C8** | Orchestration | **No change** | Single agent handles all domains. |
| **C9** | Knowledge Assistant | **Add** | New volumes: `/Volumes/${catalog}/knowledge/lending_docs/`, `/Volumes/${catalog}/knowledge/mortgage_docs/`, `/Volumes/${catalog}/knowledge/card_docs/`. |
| **C10–C16** | All others | **No change** | Tracing, app, Lakebase, mapping, validators work unchanged. |

### Phase 2 Deployment Checklist

```
□ Set phase: 2 in Bundle 2 config
□ Add 4 Bronze streaming tables + 4 archive tables (C3 YAML configs)
□ Add 8 Silver table DDL (C4)
□ Add 3 Gold MVs to SDP pipeline (C14)
□ Create 3 new metric views with locale synonyms (C5)
□ Create 32 UC Pages in locale language (C6)
□ Update Genie Agent: add 3 metric views + 10 example queries (C7)
□ Add lending locale terms to locale YAML (C1)
□ Upload lending/mortgage/card docs to knowledge volumes (C9)
□ Run backfill for Phase 2 episodes
□ Run 100-question benchmark for lending/mortgage/card queries
```

## Phase 3: Commercial Banking

**Trigger:** Phase 2 complete. Customer wants business banking capabilities.

### L200 Impact Matrix

| L200 | Component | Change Type | What's Added |
|---|---|---|---|
| **C2** | State Machine | **Add** | SM-2 (Business Party), SM-9 (Commercial Loan). 4 new episodes (#2, #4, #13, #14, #23, #24). Set `phase: 3`. |
| **C3** | Lakeflow Pipelines | **Add** | 2 new Bronze tables: `bronze.business_party_events`, `bronze.commercial_loan_events`. 2 new archive tables. |
| **C4** | Silver Model | **Populate** | `silver.organization` (already created in Phase 1 schema, now populated). `silver.commercial_facility` (already created in Phase 2 schema, now populated). Account types OPERATING, PAYROLL, ESCROW now generated. |
| **C14** | Gold MVs | **Add** | 2 new Gold MVs: `mv_business_accounts` (org + account + transaction + balance), `mv_business_loans` (org + commercial_facility + loan_payment). |
| **C5** | Metric Views | **Add** | 2 new metric views: `business_account_metrics`, `business_loan_metrics`. **Different parameter:** `business_guid` (not `consumer_guid`) — business users authenticate differently. |
| **C6** | UC Pages | **Add** | 6 new terms from Semantics 02 (Legal Entity, Beneficial Owner, Authorized Signer, Operating Account, Payroll Account, Escrow Account). |
| **C7** | Genie Agent | **Add agent** | **New Genie Agent: Business Banking Agent** (1 per locale). Separate from the consumer agent because business users have different permissions, different metric views, and different authentication. This is the point where multi-agent becomes justified — consumer and business are genuinely different audiences. |
| **C8** | Orchestration | **Modify** | Add routing: consumer requests → consumer agent, business requests → business agent. Authentication determines which agent. |
| **C12** | Lakebase | **Add** | New tables: `app.business_users`, `app.business_sessions`. Business users authenticate via the bank's corporate IdP (not consumer IdP). |
| **C1** | Locale Config | **Add** | Business-specific locale terms: legal forms per locale (NL: BV, NV; US: LLC, Corp; GB: Ltd, PLC). Registration authorities (KVK, Companies House, SEC). |
| **C10–C11, C13–C16** | Others | **No change** | |

### Phase 3 Architecture Decision: Multi-Agent

Phase 3 is where the single-agent design splits into **2 agents per locale**:

| Agent | Audience | Metric Views | Authentication |
|---|---|---|---|
| **Consumer Banking Agent** | Individual consumers | consumer_transaction_metrics, consumer_product_metrics, consumer_behavior_metrics, consumer_loan_metrics, consumer_mortgage_metrics, consumer_card_metrics | Consumer IdP → consumer_guid |
| **Business Banking Agent** | Business users | business_account_metrics, business_loan_metrics | Corporate IdP → business_guid |

This split is justified because:
- Different authentication paths (consumer IdP vs. corporate IdP)
- Different parameter names (`consumer_guid` vs. `business_guid`)
- Different permission models (consumer sees own data; business user may see company-wide data)
- Different terminology (consumer: "my balance"; business: "our operating account balance")

## Phase 4: Investments & Wealth

**Trigger:** Phase 3 complete. Customer wants investment/wealth management capabilities.

### L200 Impact Matrix

| L200 | Component | Change Type | What's Added |
|---|---|---|---|
| **C2** | State Machine | **Add** | SM-10 (Investment Account), SM-11 (Securities). 8 new episodes (#25–32). Set `phase: 4`. |
| **C3** | Lakeflow Pipelines | **Add** | 3 new Bronze tables: `bronze.investment_events`, `bronze.trade_events`, `bronze.corporate_action_events`. Plus reference data ingestion for `bronze.market_data` and `bronze.securities_reference`. |
| **C4** | Silver Model | **Add** | 6 new Silver tables: `investment_account`, `security`, `holding`, `trade`, `corporate_action`, `market_data_daily`. |
| **C14** | Gold MVs | **Add** | 1 new Gold MV: `mv_customer_investments` (investment_account + holding + security + market_data + trade + party). |
| **C5** | Metric Views | **Add** | 1 new metric view: `consumer_investment_metrics` (portfolio_value, gain_loss, dividend_income, allocation). Same `consumer_guid` parameter. |
| **C6** | UC Pages | **Add** | 12 new terms from Semantics 02 subdomain 11 (Security, ISIN, Portfolio, Holding, Trade, Dividend, etc.). |
| **C7** | Genie Agent | **Modify** | Add `consumer_investment_metrics` to the consumer agent (now 7 of 50 sources). Add 8+ example SQL queries for investment questions. |
| **C9** | Knowledge Assistant | **Add** | New volume: `/Volumes/${catalog}/knowledge/investment_docs/` (fund prospectuses, investment guides). |
| **C1** | Locale Config | **Add** | Exchange codes per locale (NL: AEX; US: NYSE, NASDAQ; GB: LSE). Currency pairs for FX. |
| **C2 reference data** | State Machine | **Add** | Securities universe YAML: ~100 synthetic securities (equities, bonds, funds) with realistic price patterns. |

### Phase 4 Special Consideration: Market Data

Phase 4 introduces **reference data feeds** that don't come from state machines:

| Feed | Source | Frequency | Silver Table |
|---|---|---|---|
| Daily security prices | Generated (synthetic) or loaded (real) | Daily | `silver.market_data_daily` |
| Securities reference | Static YAML | On change | `silver.security` |
| Corporate actions | Generated (synthetic) | Event-driven | `silver.corporate_action` |

The generator creates synthetic price series with realistic patterns (trends, volatility, mean reversion). For production, real market data replaces the synthetic feed via the same Genie Code mapping workflow (C13).

## Phase 5: Bank Operations

**Trigger:** Phase 4 complete. Customer wants internal operations visibility.

### L200 Impact Matrix

| L200 | Component | Change Type | What's Added |
|---|---|---|---|
| **C2** | State Machine | **Add** | SM-12 (General Ledger — reactive). 8 new episodes (#33–40). Set `phase: 5`. |
| **C3** | Lakeflow Pipelines | **Add** | 2 new Bronze tables: `bronze.gl_events`, `bronze.reference_rate_events`. |
| **C4** | Silver Model | **Add** | 4 new Silver tables: `gl_journal_entry`, `gl_account`, `regulatory_report`, `interest_rate_reference`. |
| **C14** | Gold MVs | **Add** | 1 new Gold MV: `mv_bank_gl` (gl_journal_entry + gl_account). |
| **C5** | Metric Views | **Add** | 1 new metric view: `bank_operations_metrics` (daily_postings, period_close_status, exceptions). **No consumer_guid parameter** — this is an internal-facing metric view. |
| **C6** | UC Pages | **Add** | 6 new terms from Semantics 02 subdomain 12 (General Ledger, Journal Entry, Chart of Accounts, Reference Rate, etc.). |
| **C7** | Genie Agent | **Add agent** | **New Genie Agent: Internal Operations Agent** (1 per locale). For bank analysts and operations staff. Uses UC identity (`current_user()`) — no consumer_guid needed. |
| **C8** | Orchestration | **Modify** | 3 agents per locale: consumer, business, internal. Internal agent uses Supervisor Agent (managed) rather than custom orchestrator. |
| **C2 reference data** | State Machine | **Add** | GL chart of accounts YAML. Reference interest rate history YAML. |

### Phase 5 Architecture Decision: Three Agents

| Agent | Audience | Authentication | Metric Views |
|---|---|---|---|
| **Consumer Agent** | Individual consumers | Consumer IdP → consumer_guid | 7 consumer metric views |
| **Business Agent** | Business users | Corporate IdP → business_guid | 2 business metric views |
| **Internal Agent** | Bank analysts/ops | UC identity (current_user()) | 1 operations metric view + all others (read-only) |

The internal agent can use **Supervisor Agent** (Databricks-managed) because it authenticates via UC identity — `current_user()` works, so no custom consumer_guid injection is needed.

## Cumulative Component Growth by Phase

### Silver Tables

| Phase | New Tables | Cumulative | New Columns |
|---|---|---|---|
| 1 | 8 (party, person, org, account, account_id, balance, transaction, statement, product, party_address, party_contact, party_identifier, party_relationship, party_kyc) | 14 | ~140 |
| 2 | 8 (loan, loan_payment, loan_event, mortgage, mortgage_property, credit_card, credit_card_statement, commercial_facility) | 22 | ~80 |
| 3 | 0 (populate existing) | 22 | 0 |
| 4 | 6 (investment_account, security, holding, trade, corporate_action, market_data_daily) | 28 | ~55 |
| 5 | 4 (gl_journal_entry, gl_account, regulatory_report, interest_rate_reference) | 32 | ~35 |

### Gold MVs + Metric Views

| Phase | New Gold MVs | New Metric Views | Cumulative MVs | Cumulative Metrics |
|---|---|---|---|---|
| 1 | 3 | 3 | 3 | 3 |
| 2 | 3 | 3 | 6 | 6 |
| 3 | 2 | 2 | 8 | 8 |
| 4 | 1 | 1 | 9 | 9 |
| 5 | 1 | 1 | 10 | 10 |

### Genie Agents

| Phase | Agents per Locale | Total (3 locales) |
|---|---|---|
| 1 | 1 (consumer) | 3 |
| 2 | 1 (consumer — expanded) | 3 |
| 3 | 2 (consumer + business) | 6 |
| 4 | 2 (consumer expanded + business) | 6 |
| 5 | 3 (consumer + business + internal) | 9 |

### UC Pages

| Phase | New Pages | Cumulative |
|---|---|---|
| 1 | 60 | 60 |
| 2 | 32 | 92 |
| 3 | 6 | 98 |
| 4 | 12 | 110 |
| 5 | 6 | 116 |

## Phase Activation Protocol

When a new phase is greenlit, the FDE follows this protocol:

### Step 1: Update Bundle 2 (Generator)

```yaml
# Set the phase variable
variables:
  phase:
    default: 2  # or 3, 4, 5
```

Run backfill for the new episodes. Existing data is untouched — new episodes generate additional events alongside the existing ones.

### Step 2: Update Bundle 1 (Infrastructure)

Add the new Bronze streaming tables, Silver table DDL, and Gold MV definitions to the SDP pipeline. The pipeline's YAML-driven architecture means this is adding new YAML config files, not modifying existing code.

### Step 3: Update Bundle 3 (Application)

Create new metric views with locale synonyms. Create new UC Pages. Update the Genie Agent(s) with new metric views and example SQL. If the phase introduces a new agent (Phase 3: business, Phase 5: internal), create it via the Management API.

### Step 4: Validate

Run the phase-specific benchmark questions (100+ per locale per phase). Verify metric view accuracy, Genie Agent comprehension, and SQL validator coverage.

## What Does NOT Change Between Phases

| Component | Why It's Phase-Independent |
|---|---|
| **SQL Validator (C15)** | Validates `consumer_guid` / `business_guid` parameter presence — works regardless of which metric view |
| **ai_decide (C16)** | Soft validation is content-agnostic — topic, PII, tone, language checks work on any response |
| **MLflow 3 Tracing (C10)** | Traces work the same regardless of table count or agent count |
| **Genie Code Mapping (C13)** | Mapping workflow is table-agnostic — maps any source to any canonical Silver table |
| **Lakebase schema (C12)** | Consumer auth and memory tables are phase-independent (business tables added in Phase 3 only) |
| **Databricks App (C11)** | API endpoints are phase-independent; new agents are added as configuration, not code changes |

## Open Questions

| # | Question | Impact | Resolution Path |
|---|---|---|---|
| Q36 | Should phases be deployable independently (e.g., Phase 4 without Phase 3)? | Flexibility vs. complexity | Current design: phases are cumulative (1→2→3→4→5). Independent phases would require decoupling the SM coupling points. Defer. |
| Q37 | Should the Genie Agent 50-table limit drive when to split into domain agents, or should audience (consumer/business/internal) be the only split criterion? | Agent architecture | Current design: split by audience only. If a single consumer agent exceeds ~15 metric views, split by domain within the consumer audience. |
| Q38 | Should Phase 5 (GL) be available to the consumer and business agents, or internal only? | Data access | Internal only — consumers and businesses don't need GL visibility. The internal agent can see all metric views. |

## References

- **L200-C2 v2** — Full-Spectrum State Machine Simulator (notebooks/308703765066430)
- **Research 07** — Full-Spectrum FIBO Generator (notebooks/308703765046744)
- **Semantics 02** — 108 glossary terms (notebooks/308703765065096)
- **L100 v4** — System Overview (notebooks/1987168172366090)
- All L200s: C1–C16 (Phase 1 designs)
