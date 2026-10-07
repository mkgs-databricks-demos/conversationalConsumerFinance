# L200-C14: Gold Materialized Views (Enzyme) — Detailed Design

> **Status:** Draft v2 — Oct 7, 2026
> **Author:** Matthew Giglia
> **Parent:** L100 — Conversational Consumer Finance: System Overview
> **Component:** C14 — Gold Materialized Views (Layer 2: Data Platform — Gold)
> **Priority:** P0
> **Bundle:** Bundle 1 (Infrastructure — all environments)

## Overview

The Gold Materialized Views are **Layer 1 of the two-layer metric view pattern** — pre-computed joins across Silver tables that provide millisecond-latency reads for consumer queries. They are Enzyme-optimized, incrementally refreshed by the SDP pipeline, and contain **all customers' data** (no parameters, no RLS). Consumer data isolation is enforced at Layer 2 (parameterized metric views in L200-C5), not here.

This design codifies the research from **Research 05 — Two-Layer Metric View Pattern** (canvas notebooks/308703764881180) and the Gold layer section of **L200-C3 — Lakeflow Pipelines** (canvas notebooks/308703764885010).

### The Two-Layer Pattern (recap)

```
Silver Tables (FIBO-aligned canonical model)
  │
  ▼
Layer 1: Gold Materialized Views (THIS L200)
  ├── Pre-computed joins across Silver tables
  ├── Enzyme-optimized: liquid clustering, row tracking, CDF, deletion vectors
  ├── Incremental refresh via SDP pipeline
  ├── NO parameters, NO RLS — pure performance layer
  └── Contains ALL customers' data
  │
  ▼
Layer 2: Parameterized Metric Views (L200-C5)
  ├── Source: Layer 1 materialized views (not raw Silver)
  ├── Required consumer_guid parameter (no default)
  ├── filter: customer_id = :consumer_guid
  ├── Fields + measures with locale synonyms
  └── Genie Agent queries THIS layer
```

**Why this works:** Metric views with parameters cannot be materialized (Databricks restriction). But a metric view's source can be any table-like UC object, including materialized views. Layer 1 has no parameters — it can be materialized. Layer 2 has parameters but isn't materialized — it reads from Layer 1's pre-computed results. Each layer does what it's good at.

## Dependencies

| Dependency | Component | What It Provides | Status |
|---|---|---|---|
| **FIBO-Aligned Silver Model** | C4 v2 | Source tables: party, person, account, party_relationship, account_balance, account_transaction, product (14 Phase 1 tables) | Design complete (L200-C4 v2) |
| **Lakeflow Pipelines** | C3 | SDP pipeline that manages MV lifecycle (create, incremental refresh) | Design complete (L200-C3) |
| **Locale Config** | C1 | Catalog name (`ccf_${locale}`) | Design complete |

## Design

### Materialized View Inventory

Three Gold materialized views, each pre-computing a specific join pattern that consumer queries need:

| Materialized View | Purpose | Source Silver Tables | Grain |
|---|---|---|---|
| `gold.mv_customer_transactions` | Transaction history with customer and balance context | account_transaction + account + party_relationship + party + account_balance | One row per transaction per customer |
| `gold.mv_customer_products` | Product portfolio with customer context | account + product + party_relationship + party | One row per account-product per customer |
| `gold.mv_customer_behavior` | Behavioral aggregations by period | account_transaction + party_relationship + party (aggregated) | One row per customer per period per category |

### Delta Best Practices (all Gold MVs)

```sql
-- Applied to all Gold materialized views
CLUSTER BY AUTO
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.enableRowTracking' = 'true',
    'delta.enableDeletionVectors' = 'true',
    'quality' = 'gold',
    'domain' = 'consumer_banking',
    'data_classification' = 'confidential'
)
```

| Property | Why |
|---|---|
| **Liquid Clustering (AUTO)** | Databricks auto-selects optimal clustering columns based on query workload — likely `customer_id` + `transaction_date` for transactions |
| **Row Tracking** | Required for incremental refresh of materialized views |
| **Change Data Feed** | Enables downstream streaming reads and audit pipelines |
| **Deletion Vectors** | Efficient deletes without rewriting data files — critical for GDPR `RIGHT TO ERASURE` |

### gold.mv_customer_transactions

The primary materialized view for consumer transaction queries. Pre-joins transactions with account, holder, customer, and daily balance.

```python
@dp.materialized_view(
    name="${catalog}.gold.mv_customer_transactions",
    comment="Pre-computed customer transaction view with balance context. "
            "Layer 1 of the two-layer metric view pattern. "
            "Source for parameterized metric views (Layer 2). "
            "Contains ALL customers — consumer isolation enforced at Layer 2."
)
def mv_customer_transactions():
    parties = spark.read.table(f"{catalog}.silver.party").filter("is_current = TRUE")
    accounts = spark.read.table(f"{catalog}.silver.account").filter("is_current = TRUE")
    relationships = spark.read.table(f"{catalog}.silver.party_relationship").filter(
        "is_current = TRUE AND related_entity_type = 'ACCOUNT'"
    )
    transactions = spark.read.table(f"{catalog}.silver.account_transaction")
    balances = spark.read.table(f"{catalog}.silver.account_balance")

    return (
        transactions
        .join(accounts, "account_id")
        .join(relationships, transactions.account_id == relationships.related_entity_id)
        .join(parties, relationships.party_id == parties.party_id)
        .join(
            balances,
            (transactions.account_id == balances.account_id) &
            (transactions.transaction_date == balances.balance_date) &
            (balances.balance_type == "AVAILABLE"),
            "left"
        )
        .select(
            # Customer dimensions (via party_relationship → party)
            parties.party_id.alias("customer_id"),
            parties.customer_segment,
            # Account dimensions
            accounts.account_id,
            accounts.account_type,
            accounts.currency_code.alias("account_currency"),
            # Transaction facts
            transactions.transaction_id,
            transactions.transaction_date,
            transactions.posting_date,
            transactions.transaction_type,
            transactions.transaction_status,
            transactions.direction,
            transactions.amount,
            transactions.currency_code.alias("transaction_currency"),
            transactions.merchant_name,
            transactions.merchant_category,
            transactions.payment_scheme,
            transactions.counterparty_iban,
            transactions.channel_code,
            # Balance context (as of transaction date)
            balances.amount.alias("balance_on_date"),
        )
    )
```

**Output columns:** 20 columns. The metric view (Layer 2) selects from these and defines measures (SUM, COUNT, AVG) with locale-specific synonyms.

**Join logic:**
- `transactions → accounts` on `account_id` (inner join — every transaction has an account)
- `accounts → holders` on `account_id` (inner join — every account has a holder)
- `holders → customers` on `customer_id` (inner join — every holder is a customer)
- `transactions → balances` on `account_id + transaction_date = balance_date` (left join — balance may not exist for every date)
- SCD2 filter: `is_current = TRUE` on dimension tables (customer, account, holder)

### gold.mv_customer_products

Product portfolio view for product-related consumer queries ("What products do I have?", "Am I eligible for an upgrade?").

```python
@dp.materialized_view(
    name="${catalog}.gold.mv_customer_products",
    comment="Pre-computed customer product portfolio. "
            "Layer 1 of the two-layer metric view pattern. "
            "Contains ALL customers — consumer isolation enforced at Layer 2."
)
def mv_customer_products():
    parties = spark.read.table(f"{catalog}.silver.party").filter("is_current = TRUE")
    accounts = spark.read.table(f"{catalog}.silver.account").filter("is_current = TRUE")
    relationships = spark.read.table(f"{catalog}.silver.party_relationship").filter(
        "is_current = TRUE AND related_entity_type = 'ACCOUNT'"
    )
    products = spark.read.table(f"{catalog}.silver.product")

    return (
        accounts
        .join(products, "product_id")
        .join(relationships, accounts.account_id == relationships.related_entity_id)
        .join(parties, relationships.party_id == parties.party_id)
        .select(
            # Customer dimensions (via party_relationship → party)
            parties.party_id.alias("customer_id"),
            parties.customer_segment,
            # Account dimensions
            accounts.account_id,
            accounts.account_type,
            accounts.account_status,
            accounts.currency_code,
            accounts.opened_date,
            accounts.closed_date,
            # Product dimensions
            products.product_id,
            products.product_code,
            products.product_name,
            products.product_type,
            products.interest_rate_type,
            products.overdraft_allowed,
            products.credit_limit,
            # Holder context
            relationships.relationship_type.alias("holder_role")
        )
    )
```

**Output columns:** 15 columns. Enables metric view measures like `active_products` (COUNT WHERE account_status = 'OPEN'), `credit_utilization`, `savings_balance`.

### gold.mv_customer_behavior

Behavioral aggregation view for trend and anomaly queries ("Why is my spending higher this month?", "Show my spending by category").

```python
@dp.materialized_view(
    name="${catalog}.gold.mv_customer_behavior",
    comment="Pre-computed customer behavioral aggregations by period and category. "
            "Layer 1 of the two-layer metric view pattern. "
            "Contains ALL customers — consumer isolation enforced at Layer 2."
)
def mv_customer_behavior():
    parties = spark.read.table(f"{catalog}.silver.party").filter("is_current = TRUE")
    accounts = spark.read.table(f"{catalog}.silver.account").filter("is_current = TRUE")
    relationships = spark.read.table(f"{catalog}.silver.party_relationship").filter(
        "is_current = TRUE AND related_entity_type = 'ACCOUNT'"
    )
    transactions = spark.read.table(f"{catalog}.silver.account_transaction")

    return (
        transactions
        .join(accounts, "account_id")
        .join(relationships, transactions.account_id == relationships.related_entity_id)
        .join(parties, relationships.party_id == parties.party_id)
        .groupBy(
            parties.party_id.alias("customer_id"),
            parties.customer_segment,
            accounts.account_type,
            date_trunc("MONTH", transactions.transaction_date).alias("period"),
            transactions.merchant_category,
            transactions.direction
        )
        .agg(
            F.sum("amount").alias("total_amount"),
            F.count("transaction_id").alias("transaction_count"),
            F.avg("amount").alias("avg_amount"),
            F.min("amount").alias("min_amount"),
            F.max("amount").alias("max_amount"),
            F.countDistinct("merchant_name").alias("unique_merchants")
        )
    )
```

**Output columns:** 12 columns. Pre-aggregated at the customer × month × category × direction grain. Enables metric view measures like `spending_trend_mom`, `category_distribution`, and `anomaly_score` (computed as deviation from rolling average).

### Incremental Refresh

The SDP pipeline manages incremental refresh automatically. When Silver tables change (detected via CDF), only the affected rows in the Gold MVs are recomputed — not the full result set.

```
Silver CDF (change data feed)
  │
  ├── New/changed rows in silver.account_transaction
  │     → Incremental refresh of gold.mv_customer_transactions
  │     → Incremental refresh of gold.mv_customer_behavior
  │
  ├── New/changed rows in silver.party (status change, segment change)
  │     → Incremental refresh of all 3 Gold MVs
  │
  ├── New/changed rows in silver.party_relationship (holder changes)
  │     → Incremental refresh of all 3 Gold MVs
  │
  ├── New/changed rows in silver.account (status change)
  │     → Incremental refresh of all 3 Gold MVs
  │
  └── New/changed rows in silver.product (rate change)
        → Incremental refresh of gold.mv_customer_products
```

### GDPR: Right to Erasure

When a customer exercises their right to erasure:

1. **Lakebase:** `DELETE FROM app.customers WHERE customer_id = ?` (cascades to conversations, messages, consent, insights)
2. **Silver:** `DELETE FROM silver.customer WHERE customer_id = ?` (and account_holder, etc.)
3. **Gold MVs:** Deletion vectors mark the customer's rows as deleted without rewriting data files
4. **VACUUM:** Periodic `VACUUM` physically removes deleted data after retention period

Deletion vectors on Gold MVs are critical — without them, deleting one customer's data would require rewriting entire data files that contain other customers' data.

### Performance Characteristics

| Metric | Without Gold MVs | With Gold MVs |
|---|---|---|
| **Query pattern** | Metric view → joins 5 Silver tables at query time | Metric view → reads pre-joined Gold MV |
| **Join cost** | 5-way join on every consumer query | Joins pre-computed; zero join cost at query time |
| **Clustering** | No optimization for customer_id | Liquid clustering auto-tunes for customer_id |
| **File scanning** | Full table scan on Silver tables | Deletion vectors + liquid clustering = minimal file reads |
| **Expected latency** | Seconds (unacceptable for consumer app) | Milliseconds (target: <200ms p99) |

## Non-Functional Requirements

| NFR | Target | Rationale |
|---|---|---|
| **Query latency** | <200ms p99 for single-customer queries | Consumer app responsiveness |
| **Incremental refresh** | <5 minutes from Silver change to Gold MV update | Data freshness for consumer queries |
| **GDPR deletion** | Deletion vectors; no full file rewrite | Efficient right-to-erasure compliance |
| **No RLS on Gold MVs** | Gold MVs must NOT have row-level security or parameters | Enables materialization (Databricks restriction) |
| **Schema alignment** | Gold MV columns match Layer 2 metric view field expectations | Metric views source from these MVs |

## Testing

| Test | What It Validates |
|---|---|
| **Join correctness** | Gold MV produces correct results for known test customers |
| **SCD2 filter** | Only `is_current = TRUE` dimension rows are included |
| **Balance join** | Left join on transaction_date = balance_date handles missing balances correctly |
| **Incremental refresh** | New Silver rows appear in Gold MV after pipeline refresh |
| **Deletion vectors** | Customer deletion marks rows without rewriting files; VACUUM removes them |
| **Liquid clustering** | Single-customer queries scan minimal files (verify via query profile) |
| **Behavioral aggregation** | Monthly aggregations match raw transaction sums |
| **Metric view compatibility** | Layer 2 metric views can SELECT from Gold MVs with correct column names |
| **Performance benchmark** | Single-customer query on Gold MV completes in <200ms |

## Deployment

Part of **Bundle 1 (Infrastructure)** — deployed to all environments. Managed by the SDP pipeline (L200-C3).

```python
# In src/pipelines/gold/ — one file per materialized view
# These are @dp.materialized_view() definitions read by the SDP pipeline

src/pipelines/gold/
├── mv_customer_transactions.py
├── mv_customer_products.py
└── mv_customer_behavior.py
```

The SDP pipeline creates and refreshes these materialized views as part of the Bronze → Silver → Gold streaming flow. No separate deployment step is needed — they are part of the pipeline definition.

### Refresh Trigger

Gold MVs are refreshed as part of the SDP pipeline run. The pipeline is triggered by:
- **Dev/demo:** Daily simulation job (Bundle 2) writes to Bronze → pipeline processes Bronze → Silver → Gold
- **Production:** Real customer data lands in Bronze → pipeline processes Bronze → Silver → Gold

In both cases, the same pipeline code handles the refresh. The Gold MVs don't know or care whether the data came from the generator or real customer systems.

## Open Questions

| # | Question | Impact | Resolution Path |
|---|---|---|---|
| Q11 | What is the incremental refresh latency for Gold MVs with 50K customers? | Data freshness | POC benchmark with synthetic data at scale |
| Q20 | Does `CLUSTER BY AUTO` converge on `customer_id` as the primary clustering column given consumer query patterns? | Query performance | POC validation; switch to explicit `CLUSTER BY (customer_id)` if AUTO doesn't converge |
| Q21 | Should `gold.mv_customer_behavior` be pre-aggregated (current design) or unaggregated (let the metric view aggregate)? | Flexibility vs. performance | Current design: pre-aggregated at month × category grain. If metric views need finer grain, switch to unaggregated. |
| — | Should there be a 4th Gold MV for balance trends (`gold.mv_customer_balance_trends`)? | Enables "show my balance over time" queries without joining transactions | Defer to POC — the balance join in `mv_customer_transactions` may be sufficient |

## References

- **Research 05** — Two-Layer Metric View Pattern (canvas notebooks/308703764881180)
- **L200-C4** — FIBO-Aligned Silver Model (canvas notebooks/308703764885515) — source tables
- **L200-C3** — Lakeflow Pipelines (canvas notebooks/308703764885010) — pipeline that manages these MVs
- **L100 v3** — System Overview (canvas notebooks/1987168172366090) — Gold layer specification
- Materialization restrictions: https://learn.microsoft.com/en-us/azure/databricks/uc-semantics/metric-views/materialization/
- Lakeflow best practices: https://learn.microsoft.com/en-us/azure/databricks/ldp/best-practices/index/
- Incremental refresh: https://learn.microsoft.com/en-us/azure/databricks/ldp/incremental-refresh/
