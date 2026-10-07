# Research 06: Genie Agent + Parameterized Metric View Interaction

> **Status:** Draft — Oct 6, 2026
> **Author:** Matthew Giglia
> **File:** docs/research/06_genie_parameterized_mv_interaction.md
> **Scope:** How Genie Agents interact with parameterized metric views — Q13 from the L100

## The Question (Q13)

Does Genie Agent automatically generate the table-valued function syntax (`SELECT ... FROM metric_view(consumer_guid => 'abc123')`) when querying a parameterized metric view? If not, every consumer query fails — secure but unusable.

## Findings

### 1. Metric Views Are Queried as Table-Valued Functions ✅

From the docs: *"To query a metric view that defines parameters, call the metric view as a table-valued function and pass parameters as arguments. You can pass arguments by name or by position."* :citation[documentation."https://learn.microsoft.com/en-us/azure/databricks/uc-semantics/metric-views/use-parameters/",Use parameters with metric views]

```sql
-- Named argument syntax
SELECT customer_id, MEASURE(total_balance)
FROM gold.customer_transaction_metrics(consumer_guid => 'cust_abc123')
GROUP BY customer_id;

-- Positional argument syntax
SELECT customer_id, MEASURE(total_balance)
FROM gold.customer_transaction_metrics('cust_abc123')
GROUP BY customer_id;
```

### 2. Genie Agents Import Metric View Synonyms Automatically ✅

From the docs: *"Synonyms are automatically imported to help Genie better discover and understand available fields and measures from the metric view."* :citation[documentation."https://learn.microsoft.com/en-us/azure/databricks/uc-semantics/agent-metadata/",Agent metadata in metric views]

This means our locale-specific synonyms (`betaalrekening`, `saldo`, `overschrijving`) will be available to the Genie Agent without manual configuration.

### 3. Genie Supports Table-Valued Functions ✅

From the docs: *"Genie supports both scalar functions, which return a single value, and table-valued functions, which return a table of rows."* :citation[documentation."https://learn.microsoft.com/en-us/azure/databricks/genie-agents/tune-quality/",Tune Genie Agent quality]

Since parameterized metric views are queried as table-valued functions, and Genie supports table-valued functions, the mechanism exists.

### 4. Materialization Cannot Coexist with Parameters ✅ (confirmed)

From the docs: *"You can't materialize a metric view that defines parameters."* :citation[documentation."https://learn.microsoft.com/en-us/azure/databricks/uc-semantics/metric-views/materialization/",Materialization for metric views]

Also: *"You can't create a materialization when the metric view or any of its source tables uses row-level security (RLS), column-level masking (CLM), or ABAC policies."* :citation[documentation."https://learn.microsoft.com/en-us/azure/databricks/uc-semantics/metric-views/materialization/",Materialization for metric views]

**This confirms the two-layer pattern is the only viable approach** for combining materialization (speed) with parameterized filtering (security).

### 5. Metric View Source Can Be a Materialized View ✅ (confirmed)

From the docs: *"A table-like asset is any Unity Catalog object that exposes a tabular schema and supports SELECT queries, including tables, views, materialized views, streaming tables, foreign tables, system tables, and metric views."* :citation[documentation."https://learn.microsoft.com/en-us/azure/databricks/uc-semantics/metric-views/basic-modeling/",Model metric views]

### 6. The Open Risk: Does Genie Auto-Generate the Parameter?

The docs confirm Genie supports table-valued functions and metric view synonyms. What's **not explicitly documented** is whether Genie automatically includes the `consumer_guid` parameter when generating SQL against a parameterized metric view.

**Three scenarios:**

| Scenario | Behavior | Mitigation |
|---|---|---|
| **A: Genie auto-includes parameter** | Genie sees the required parameter in the metric view definition and includes it in generated SQL | Best case — no mitigation needed |
| **B: Genie omits parameter, query fails** | The metric view has no default for `consumer_guid`, so the query fails with a clear error | The SQL validator (C15) catches this and triggers a retry with the parameter injected by the app layer |
| **C: Genie includes parameter but wrong value** | Genie hallucinates a customer_id value | The SQL validator (C15) validates that the parameter value matches the authenticated consumer's GUID |

**Our architecture handles all three scenarios:**

1. **Genie Agent instruction** — the agent's curated instruction explicitly tells Genie to include the `consumer_guid` parameter: *"Always query metric views using the consumer_guid parameter. Example: `SELECT ... FROM gold.customer_transaction_metrics(consumer_guid => '{consumer_guid}') ...`"*

2. **Example SQL** — the agent includes example queries that demonstrate the table-valued function syntax with the parameter

3. **SQL validator (C15)** — the deterministic SQL predicate validator confirms the `consumer_guid` parameter is present in the generated SQL before execution. If missing, the app layer injects it and retries.

4. **Required parameter (no default)** — even if all else fails, the metric view itself rejects queries without the parameter. This is the hard enforcement floor.

## Architecture Decision

**Use Genie Agent instructions + example SQL to guide parameter inclusion, with the SQL validator as the safety net.**

The app layer flow:
```
1. Consumer asks: "Wat is mijn saldo?" (What is my balance?)
2. App prepends consumer_guid to the Genie API request context
3. Genie Agent generates SQL:
   SELECT MEASURE(total_balance) FROM gold.customer_transaction_metrics(consumer_guid => '{guid}')
4. SQL validator confirms consumer_guid parameter is present
5. If missing: app injects parameter and re-executes
6. If present: execute and return results
```

## Metric View Materialization Strategy

Given the two-layer pattern and the materialization restrictions, the metric views (Layer 2) should **not** use the built-in `materialization:` block in their YAML. Instead:

- **Layer 1 (Gold MVs):** Materialized by the SDP pipeline as standalone `@dp.materialized_view()` — managed outside the metric view definition
- **Layer 2 (Metric Views):** No materialization block. Source is the Layer 1 Gold MV. Parameters enforce consumer isolation.

This avoids the restriction entirely — the metric view doesn't try to materialize itself because its source is already materialized.

## New Capability: Metric View Built-In Materialization

The docs also reveal that metric views now support a **built-in `materialization:` block** with `unaggregated` and `aggregated` types, scheduled refresh, and query rewrite. :citation[documentation."https://learn.microsoft.com/en-us/azure/databricks/uc-semantics/metric-views/materialization/",Materialization for metric views]

This is relevant for **enterprise-facing** metric views (no parameters, no consumer isolation needed) — e.g., internal dashboards. For the consumer-facing path, we still need the two-layer pattern because of the parameter restriction.

**Potential optimization:** If we later add enterprise-facing metric views (same data, no consumer filter), those CAN use the built-in materialization block directly — no two-layer pattern needed.

## Resolution of Q13

**Q13 is resolved (mitigated).** Genie supports table-valued functions and imports metric view synonyms. The parameter inclusion is guided by agent instructions + example SQL, with the SQL validator as a hard safety net. The metric view's required parameter (no default) is the enforcement floor. POC validation will confirm which scenario (A, B, or C) applies in practice.

## Sources

- Metric view parameters: https://learn.microsoft.com/en-us/azure/databricks/uc-semantics/metric-views/use-parameters/
- Agent metadata in metric views: https://learn.microsoft.com/en-us/azure/databricks/uc-semantics/agent-metadata/
- Genie Agent table-valued functions: https://learn.microsoft.com/en-us/azure/databricks/genie-agents/tune-quality/
- Materialization restrictions: https://learn.microsoft.com/en-us/azure/databricks/uc-semantics/metric-views/materialization/
- Metric view YAML syntax: https://learn.microsoft.com/en-us/azure/databricks/uc-semantics/metric-views/yaml-reference/
- Model metric views (source types): https://learn.microsoft.com/en-us/azure/databricks/uc-semantics/metric-views/basic-modeling/
