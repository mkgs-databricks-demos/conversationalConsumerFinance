# L200-C5: Metric Views per Locale — Detailed Design

> **Status:** Draft v2 — Oct 7, 2026
> **Author:** Matthew Giglia
> **Parent:** L100 — Conversational Consumer Finance: System Overview
> **Component:** C5 — Metric Views (Layer 3: Semantic Layer)
> **Priority:** P1
> **Bundle:** Bundle 3 (Application — all environments)

## Overview

Metric views are **Layer 2 of the two-layer metric view pattern** — the parameterized semantic interface that Genie Agents query. They source from the Gold materialized views (Layer 1, L200-C14), enforce consumer data isolation via a required `consumer_guid` parameter, and provide locale-specific synonyms, comments, and display names so that Genie understands Dutch, British English, and American English terminology.

This is the component where FIBO definitions become **queryable business semantics** — the bridge between the data platform and the consumer-facing Genie Agent.

### Design Lineage

- **Research 05** — Two-Layer Metric View Pattern (canvas notebooks/308703764881180)
- **Research 06** — Genie Agent + Parameterized MV Interaction (canvas notebooks/308703764921982)
- **L200-C14** — Gold Materialized Views (canvas notebooks/308703764885757) — Layer 1 source
- **Semantics 01** — Consumer Banking Domain (canvas notebooks/308703764881431) — 32 glossary terms

## Dependencies

| Dependency | Component | What It Provides | Status |
|---|---|---|---|
| **Gold Materialized Views** | C14 v2 | Layer 1 source tables: mv_customer_transactions (now joins via party_relationship → party), mv_customer_products, mv_customer_behavior | Design complete (L200-C14 v2) |
| **Locale Config** | C1 | Locale-specific synonyms, comments, display_names, currency format | Design complete |
| **Semantics Doc** | Semantics 01 | 32 glossary terms with locale variants (EN, EN-GB, NL) | Complete |
| **Genie Agent + Param MV Research** | Research 06 | How Genie interacts with parameterized metric views | Complete |

## Design

### Metric View Inventory

Three parameterized metric views, one per Gold MV:

| Metric View | Source (Layer 1 Gold MV) | Required Parameter | Fields | Measures |
|---|---|---|---|---|
| `gold.customer_transaction_metrics` | `gold.mv_customer_transactions` | `consumer_guid` (STRING, no default) | account_type, transaction_month, merchant_category, payment_scheme, direction, channel | total_balance, monthly_spend, transaction_count, avg_transaction_value, total_income |
| `gold.customer_product_metrics` | `gold.mv_customer_products` | `consumer_guid` (STRING, no default) | product_type, account_status, holder_role | active_products, total_accounts, savings_balance |
| `gold.customer_behavior_metrics` | `gold.mv_customer_behavior` | `consumer_guid` (STRING, no default) | period, merchant_category, direction | total_amount, transaction_count, avg_amount, unique_merchants, spending_trend_mom |

### Security: Required Parameter (No Default)

Every metric view defines a `consumer_guid` parameter with **no default value**. This means:

1. Any query without the parameter **fails** — the metric view rejects it
2. The Genie Agent must include the parameter in generated SQL (guided by agent instructions + example SQL)
3. The SQL validator (C15) confirms the parameter is present before execution
4. The app layer injects the parameter if Genie omits it

```yaml
parameters:
  - name: consumer_guid
    data_type: STRING
    # NO default — query fails without this parameter
    # This is the hard enforcement floor for consumer data isolation

filter: customer_id = :consumer_guid
```

### YAML Definitions

#### gold.customer_transaction_metrics

```yaml
version: 1.1
comment: >
  Consumer transaction metrics with locale-specific synonyms.
  Layer 2 of the two-layer metric view pattern.
  Source: gold.mv_customer_transactions (pre-computed, Enzyme-optimized).
  Consumer isolation: required consumer_guid parameter (no default).

source: ${catalog}.gold.mv_customer_transactions

parameters:
  - name: consumer_guid
    data_type: STRING

filter: customer_id = :consumer_guid

fields:
  - name: account_type
    expr: account_type
    comment: ${locale.comments.account_type}
    synonyms: ${locale.synonyms.account_type}
    display_name: ${locale.display_names.account_type}

  - name: transaction_month
    expr: date_trunc('MONTH', transaction_date)
    comment: ${locale.comments.transaction_month}
    synonyms: ${locale.synonyms.transaction_month}
    display_name: ${locale.display_names.transaction_month}

  - name: transaction_week
    expr: date_trunc('WEEK', transaction_date)
    comment: ${locale.comments.transaction_week}

  - name: transaction_date
    expr: transaction_date
    comment: ${locale.comments.transaction_date}

  - name: merchant_category
    expr: merchant_category
    comment: ${locale.comments.merchant_category}
    synonyms: ${locale.synonyms.merchant_category}
    display_name: ${locale.display_names.merchant_category}

  - name: payment_scheme
    expr: payment_scheme
    comment: ${locale.comments.payment_scheme}
    synonyms: ${locale.synonyms.payment_scheme}

  - name: direction
    expr: direction
    comment: ${locale.comments.direction}
    synonyms: ${locale.synonyms.direction}

  - name: channel
    expr: channel_code
    comment: ${locale.comments.channel}

  - name: transaction_status
    expr: transaction_status
    comment: ${locale.comments.transaction_status}
    synonyms: ${locale.synonyms.transaction_status}

measures:
  - name: total_balance
    expr: SUM(balance_on_date)
    comment: ${locale.comments.total_balance}
    display_name: ${locale.display_names.total_balance}
    synonyms: ${locale.synonyms.total_balance}
    format:
      type: number
      prefix: ${locale.currency_symbol}
      decimal_places: 2

  - name: monthly_spend
    expr: SUM(CASE WHEN direction = 'DEBIT' THEN amount END)
    comment: ${locale.comments.monthly_spend}
    display_name: ${locale.display_names.monthly_spend}
    synonyms: ${locale.synonyms.monthly_spend}
    format:
      type: number
      prefix: ${locale.currency_symbol}
      decimal_places: 2

  - name: total_income
    expr: SUM(CASE WHEN direction = 'CREDIT' THEN amount END)
    comment: ${locale.comments.total_income}
    display_name: ${locale.display_names.total_income}
    synonyms: ${locale.synonyms.total_income}
    format:
      type: number
      prefix: ${locale.currency_symbol}
      decimal_places: 2

  - name: transaction_count
    expr: COUNT(DISTINCT transaction_id)
    comment: ${locale.comments.transaction_count}
    display_name: ${locale.display_names.transaction_count}
    synonyms: ${locale.synonyms.transaction_count}

  - name: avg_transaction_value
    expr: AVG(amount)
    comment: ${locale.comments.avg_transaction_value}
    display_name: ${locale.display_names.avg_transaction_value}
    format:
      type: number
      prefix: ${locale.currency_symbol}
      decimal_places: 2
```

#### gold.customer_product_metrics

```yaml
version: 1.1
comment: >
  Consumer product portfolio metrics with locale-specific synonyms.
  Layer 2 of the two-layer metric view pattern.

source: ${catalog}.gold.mv_customer_products

parameters:
  - name: consumer_guid
    data_type: STRING

filter: customer_id = :consumer_guid

fields:
  - name: product_type
    expr: product_type
    comment: ${locale.comments.product_type}
    synonyms: ${locale.synonyms.product_type}
    display_name: ${locale.display_names.product_type}

  - name: account_status
    expr: account_status
    comment: ${locale.comments.account_status}
    synonyms: ${locale.synonyms.account_status}

  - name: holder_role
    expr: holder_role
    comment: ${locale.comments.holder_role}

measures:
  - name: active_products
    expr: COUNT(DISTINCT CASE WHEN account_status = 'OPEN' THEN product_id END)
    comment: ${locale.comments.active_products}
    display_name: ${locale.display_names.active_products}
    synonyms: ${locale.synonyms.active_products}

  - name: total_accounts
    expr: COUNT(DISTINCT account_id)
    comment: ${locale.comments.total_accounts}
    display_name: ${locale.display_names.total_accounts}

  - name: savings_balance
    expr: COUNT(DISTINCT CASE WHEN product_type = 'SAVINGS_ACCOUNT' AND account_status = 'OPEN' THEN account_id END)
    comment: ${locale.comments.savings_accounts}
    display_name: ${locale.display_names.savings_accounts}
```

#### gold.customer_behavior_metrics

```yaml
version: 1.1
comment: >
  Consumer behavioral metrics with locale-specific synonyms.
  Layer 2 of the two-layer metric view pattern.
  Pre-aggregated at customer x month x category x direction grain.

source: ${catalog}.gold.mv_customer_behavior

parameters:
  - name: consumer_guid
    data_type: STRING

filter: customer_id = :consumer_guid

fields:
  - name: period
    expr: period
    comment: ${locale.comments.period}
    synonyms: ${locale.synonyms.period}

  - name: merchant_category
    expr: merchant_category
    comment: ${locale.comments.merchant_category}
    synonyms: ${locale.synonyms.merchant_category}

  - name: direction
    expr: direction
    comment: ${locale.comments.direction}

measures:
  - name: total_amount
    expr: SUM(total_amount)
    comment: ${locale.comments.total_amount}
    format:
      type: number
      prefix: ${locale.currency_symbol}
      decimal_places: 2

  - name: transaction_count
    expr: SUM(transaction_count)
    comment: ${locale.comments.transaction_count}

  - name: avg_amount
    expr: AVG(avg_amount)
    comment: ${locale.comments.avg_amount}
    format:
      type: number
      prefix: ${locale.currency_symbol}
      decimal_places: 2

  - name: unique_merchants
    expr: SUM(unique_merchants)
    comment: ${locale.comments.unique_merchants}
```

### Locale Synonym Files

Each locale has a YAML file with synonyms, comments, and display names:

```yaml
# src/semantic_layer/metric_views/locales/nl.yaml
synonyms:
  account_type: ["rekeningtype", "soort rekening", "type rekening"]
  total_balance: ["saldo", "rekeningsaldo", "totaal saldo"]
  monthly_spend: ["maandelijkse uitgaven", "uitgaven deze maand", "maanduitgaven"]
  total_income: ["maandelijks inkomen", "bijschrijvingen", "inkomsten"]
  transaction_count: ["aantal transacties", "transactietelling"]
  merchant_category: ["categorie", "bestedingscategorie", "winkelcategorie"]
  direction: ["afschrijving", "bijschrijving", "richting"]
  payment_scheme: ["betaalschema", "betaalmethode"]
  transaction_month: ["maand", "transactiemaand"]
  active_products: ["actieve producten", "lopende producten"]
  product_type: ["producttype", "soort product"]
  account_status: ["rekeningsstatus", "status"]
  period: ["periode", "maand"]

comments:
  account_type: "Type bankrekening: betaalrekening, spaarrekening, termijndeposito of creditcard"
  total_balance: "Totaal beschikbaar saldo op alle rekeningen van de klant"
  monthly_spend: "Totale uitgaven (afschrijvingen) in een kalendermaand"
  total_income: "Totale inkomsten (bijschrijvingen) in een kalendermaand"
  merchant_category: "Categorie van de winkel of dienstverlener"
  # ... (all 32 terms from Semantics 01)

display_names:
  account_type: "Rekeningtype"
  total_balance: "Totaal Saldo"
  monthly_spend: "Maandelijkse Uitgaven"
  total_income: "Maandelijks Inkomen"
  transaction_count: "Aantal Transacties"
  merchant_category: "Categorie"
  active_products: "Actieve Producten"
  product_type: "Producttype"

currency_symbol: "€"
```

### Metric View Creation (SQL DDL)

Metric views are created via `CREATE OR REPLACE VIEW ... WITH METRICS LANGUAGE YAML`:

```sql
CREATE OR REPLACE VIEW ${catalog}.gold.customer_transaction_metrics
WITH METRICS LANGUAGE YAML AS
$$
${resolved_yaml_content}
$$;
```

The YAML is resolved at deployment time by substituting `${locale.*}` variables from the locale config. This is a **build-time** operation — the deployed metric view contains the resolved synonyms, not the template variables.

### File Structure

```
src/semantic_layer/
├── metric_views/
│   ├── customer_transaction_metrics.yaml.tmpl   # Template with ${locale.*} vars
│   ├── customer_product_metrics.yaml.tmpl
│   ├── customer_behavior_metrics.yaml.tmpl
│   └── locales/
│       ├── en.yaml       # US English synonyms, comments, display_names
│       ├── en-GB.yaml    # British English synonyms, comments, display_names
│       └── nl.yaml       # Dutch synonyms, comments, display_names
└── deploy_metric_views.py  # Resolves templates + executes CREATE VIEW DDL
```

## Non-Functional Requirements

| NFR | Target | Rationale |
|---|---|---|
| **Consumer isolation** | Every query MUST include `consumer_guid` parameter | Security — no cross-customer data leakage |
| **Locale accuracy** | Synonyms match locale language; no English leaking into Dutch | Consumer experience |
| **Query latency** | <200ms p99 (inherited from Layer 1 Gold MV performance) | Consumer app responsiveness |
| **Synonym coverage** | All 32 glossary terms from Semantics 01 have locale synonyms | Genie Agent comprehension |
| **No materialization** | Metric views must NOT use the `materialization:` block | Parameters prevent materialization; Layer 1 handles it |

## Testing

| Test | What It Validates |
|---|---|
| **Parameter enforcement** | Query without `consumer_guid` fails with clear error |
| **Consumer isolation** | Query with consumer_guid=A returns only A's data; no B's data |
| **Locale synonyms** | Genie Agent understands "Wat is mijn saldo?" (NL), "What's my balance?" (EN), "What's my current account balance?" (GB) |
| **Table-valued function syntax** | `SELECT ... FROM gold.customer_transaction_metrics(consumer_guid => 'x')` works |
| **MEASURE() syntax** | `SELECT MEASURE(total_balance) FROM ...` returns correct aggregation |
| **Genie SQL generation** | Genie Agent generates SQL with the `consumer_guid` parameter (guided by instructions + example SQL) |
| **SQL validator integration** | SQL validator (C15) catches queries missing the `consumer_guid` parameter |
| **Locale switching** | Same metric view template deployed with NL synonyms vs. EN synonyms produces correct locale-specific behavior |
| **100-question benchmark** | Run 100+ consumer questions per locale through the Genie Agent; measure accuracy, parameter inclusion rate, and latency |

## Deployment

Part of **Bundle 3 (Application)** — deployed to all environments. Metric views are created after the Gold MVs (Bundle 1) are populated.

```yaml
# bundles/bundle3-app/databricks.yml (metric view deployment)
resources:
  jobs:
    deploy_semantic_layer:
      name: ccf-${var.locale}-deploy-semantics
      tasks:
        - task_key: deploy_metric_views
          notebook_task:
            notebook_path: src/semantic_layer/deploy_metric_views
            base_parameters:
              locale: ${var.locale}
              catalog: ccf_${var.locale}
```

### Deployment Order

1. **Bundle 1** creates Gold MVs (Layer 1) and populates them via SDP pipeline
2. **Bundle 3** creates metric views (Layer 2) that source from the Gold MVs
3. **Bundle 3** creates Genie Agents (C7) that query the metric views

## Open Questions

| # | Question | Impact | Resolution Path |
|---|---|---|---|
| Q13 | Does Genie auto-generate the `consumer_guid` parameter in SQL? | If not: SQL validator catches and app retries | **Resolved (mitigated)** — see Research 06. Agent instructions + example SQL guide Genie; SQL validator is the safety net; required parameter (no default) is the enforcement floor. POC validates which scenario applies. |
| Q22 | Should metric views use the new built-in `materialization:` block for enterprise-facing (non-parameterized) variants? | Could simplify enterprise dashboards | Defer — consumer-facing path uses two-layer pattern. Enterprise variant is a future enhancement. |
| Q23 | How does Genie handle the `MEASURE()` function syntax? Does it generate it automatically for metric view measures? | Affects query correctness | POC validation — Genie should understand MEASURE() when querying metric views. If not, example SQL in agent instructions demonstrates the syntax. |

## References

- **Research 05** — Two-Layer Metric View Pattern (canvas notebooks/308703764881180)
- **Research 06** — Genie Agent + Parameterized MV Interaction (canvas notebooks/308703764921982)
- **L200-C14** — Gold Materialized Views (canvas notebooks/308703764885757)
- **Semantics 01** — Consumer Banking Domain (canvas notebooks/308703764881431)
- Metric view YAML syntax: https://learn.microsoft.com/en-us/azure/databricks/uc-semantics/metric-views/yaml-reference/
- Parameters: https://learn.microsoft.com/en-us/azure/databricks/uc-semantics/metric-views/use-parameters/
- Agent metadata: https://learn.microsoft.com/en-us/azure/databricks/uc-semantics/agent-metadata/
