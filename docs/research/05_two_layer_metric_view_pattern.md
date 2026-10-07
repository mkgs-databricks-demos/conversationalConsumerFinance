# Two-Layer Metric View Pattern: Materialization + Parameterized Security

> **Status:** Draft — Oct 6, 2026
> **Author:** Matthew Giglia
> **File:** docs/research/05_metric_view_two_layer_pattern.md
> **Scope:** Feasibility research for combining pre-computed materialized views with parameterized metric view security

## The Problem

Metric views with parameters **cannot be materialized**. The Databricks docs state: *"You can't create a materialization when the metric view or any of its source tables uses row-level security (RLS), column-level masking (CLM), or ABAC policies. Pre-computed results can bypass per-user access controls that are meant to be enforced at query time."* Parameterized filters fall under the same restriction — invoker-dependent expressions whose result changes based on who runs the query.

But without materialization, every consumer query hits the source tables — too slow for a 50K-user consumer app. We need both speed AND security.

## The Solution: Two Layers

A metric view's source can be **any table-like UC object**, including materialized views. The docs confirm: *"A table-like asset is any Unity Catalog object that exposes a tabular schema and supports SELECT queries, including tables, views, materialized views, streaming tables, foreign tables, system tables, and metric views."*

This means:

```
Layer 1: SDP Materialized View (Enzyme-optimized)
  ├── Source: Silver tables (joins pre-computed)
  ├── NO parameters, NO RLS — pure performance
  ├── Liquid clustering, row tracking, CDF, deletion vectors
  ├── Incremental refresh via Lakeflow pipeline
  └── Contains ALL customers' data

Layer 2: Parameterized Metric View
  ├── Source: Layer 1 materialized view (NOT raw Silver)
  ├── Required consumer_guid parameter (no default)
  ├── filter: customer_id = :consumer_guid
  ├── Fields + measures with locale synonyms
  └── Genie Agent queries THIS layer
```

**Why it works:** The materialization restriction applies to the metric view itself and its source tables. Layer 1 (the materialized view) has no parameters or RLS — it's a pure pre-computation. Layer 2 (the parameterized metric view) has parameters but isn't materialized — it reads from Layer 1. Each layer does what it's good at.

## Feasibility Evidence

### 1. Metric view source can be a materialized view ✅

From the docs: *"A table-like asset is any Unity Catalog object that exposes a tabular schema and supports SELECT queries, including tables, views, **materialized views**, streaming tables..."*

### 2. Parameterized metric views are GA ✅

Parameters let you pass values into a metric view at query time. A parameter without a default value forces the caller to provide it — the query fails otherwise. This is the "required filter" mechanism.

```yaml
parameters:
  - name: consumer_guid
    data_type: STRING
    # NO default — query fails without this parameter
filter: customer_id = :consumer_guid
```

### 3. Materialized views support Enzyme optimization ✅

Lakeflow Declarative Pipelines manage materialized views with:
- **Liquid Clustering (AUTO):** Databricks auto-selects optimal clustering columns
- **Row Tracking:** Required for incremental refresh
- **Change Data Feed:** Enables downstream streaming reads
- **Deletion Vectors:** Efficient deletes without rewriting files
- **Incremental Refresh:** Only processes upstream changes

### 4. Materialization restriction doesn't apply to Layer 1 ✅

Layer 1 has no parameters, no RLS, no ABAC, no invoker-dependent expressions. It's a standard materialized view of pre-joined Silver tables. The restriction only blocks materialization of the metric view itself (Layer 2) — which we don't materialize.

## Performance Characteristics

| Without Two-Layer Pattern | With Two-Layer Pattern |
|---|---|
| Parameterized MV → reads Silver tables → joins at query time | Parameterized MV → reads materialized view → joins pre-computed |
| Every query joins customer + account + holder + transaction + balance | Joins already done in the materialized view |
| No clustering optimization for customer_id | Liquid clustering auto-tunes for customer_id |
| Full table scan on every query | Deletion vectors + liquid clustering = minimal file reads |
| Latency: seconds | Latency: milliseconds |

## Limitation: Materialization Cannot Be Combined with RLS

The docs also state: *"You can't materialize a metric view when the view or any of its source tables uses row-level security."*

This means if you apply UC row filters to the Silver tables (Approach D from the security comparison), you **cannot** use the two-layer pattern — the materialized view would be blocked because its source tables have RLS.

**This is why the Giglia design uses parameterized metric views instead of UC row filters for consumer isolation.** The parameterized filter is applied at Layer 2 (the metric view), not at the source tables. The source tables (Silver) and the materialized view (Layer 1) are RLS-free, enabling materialization.

## Meesho Feedback

Karthik Nandakumar from Meesho (#apa-uc-semantics, Sep 6, 2026) reported the same limitation: *"Metric views has a limitation of materialization not supported for Metric views with parameters. At Meesho, every metric view has parameters to ensure there are no run away queries and ensure users are prompted for missing information."*

The two-layer pattern solves Meesho's problem too — materialize the base data in Layer 1, parameterize in Layer 2.

## Gold Layer Materialized Views

| Materialized View | Source Tables (Silver) | Delta Config |
|---|---|---|
| `gold.mv_customer_transactions` | account_transaction + account + account_holder + customer + account_balance_daily | CLUSTER BY AUTO, row tracking, CDF, deletion vectors |
| `gold.mv_customer_products` | account + product + account_holder + customer | CLUSTER BY AUTO, row tracking, CDF, deletion vectors |
| `gold.mv_customer_behavior` | account_transaction + customer (aggregated by period) | CLUSTER BY AUTO, row tracking, CDF, deletion vectors |

## Open Questions

| Question | Impact | Resolution Path |
|---|---|---|
| Does Genie understand required metric view parameters and include them in generated SQL? | If not: every query fails (secure but bad UX). The SQL validator catches this and can trigger a retry. | POC validation — run 100+ test queries through a Genie Agent backed by a parameterized metric view |
| What's the incremental refresh latency for the Gold materialized views? | Affects data freshness for consumer queries | POC benchmark |
| Does CLUSTER BY AUTO optimize for customer_id given synthetic query patterns? | May need explicit clustering for the POC | POC validation; switch to explicit if AUTO doesn't converge |

## Sources

- Metric view source types: https://learn.microsoft.com/en-us/azure/databricks/uc-semantics/metric-views/basic-modeling/
- Materialization restrictions: https://learn.microsoft.com/en-us/azure/databricks/uc-semantics/metric-views/materialization/
- Parameters: https://learn.microsoft.com/en-us/azure/databricks/uc-semantics/metric-views/use-parameters/
- Lakeflow best practices: https://learn.microsoft.com/en-us/azure/databricks/ldp/best-practices/index/
- Incremental refresh: https://learn.microsoft.com/en-us/azure/databricks/ldp/incremental-refresh/
