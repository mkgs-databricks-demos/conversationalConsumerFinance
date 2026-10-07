# L200-C15: Deterministic SQL Predicate Validator — Detailed Design

> **Status:** Draft v1 — Oct 6, 2026
> **Author:** Matthew Giglia
> **Parent:** L100 — Conversational Consumer Finance: System Overview
> **Component:** C15 — Deterministic SQL Predicate Validator (Cross-cutting: Security)
> **Priority:** P1
> **Bundle:** Bundle 1 (Infrastructure — all environments)

## Overview

The Deterministic SQL Predicate Validator is a **Unity Catalog SQL UDF** that inspects every Genie-generated SQL query before execution to confirm the `consumer_guid` parameter is present and not bypassed. It is the **hard security gate** in the layered enforcement model — check #11 in the L100's 19-check security architecture.

This is not an AI-based check. It is a **deterministic regex/pattern-matching function** that runs in ~1ms and returns a boolean: safe or unsafe. It catches structural bypass patterns that the parameterized metric view alone cannot prevent (e.g., `OR 1=1`, `UNION SELECT`, subqueries that reference other customers).

### Why Not Just Rely on the Parameterized Metric View?

The required `consumer_guid` parameter (no default) ensures the metric view always filters by customer. But Genie generates the SQL that calls the metric view — and Genie could theoretically generate SQL that:

1. **Omits the parameter** — query fails (safe but bad UX)
2. **Includes the parameter but adds `OR 1=1`** — bypasses the filter
3. **Uses a UNION to append another customer's data** — cross-customer leakage
4. **Uses a subquery that references the base table directly** — bypasses the metric view entirely

The SQL validator catches cases 2–4. Case 1 is caught by the metric view itself (query fails without the parameter).

## Dependencies

| Dependency | Component | What It Provides | Status |
|---|---|---|---|
| **Metric Views** | C5 | The SQL that the validator inspects is generated against these metric views | Design complete (L200-C5) |
| **Locale Config** | C1 | Catalog name for UDF registration | Design complete |

## Design

### UC SQL UDF Definition

```sql
CREATE OR REPLACE FUNCTION ${catalog}.security.validate_consumer_sql(
    sql_text STRING,
    expected_consumer_guid STRING
)
RETURNS STRUCT<
    is_valid BOOLEAN,
    rejection_reason STRING,
    risk_level STRING
>
LANGUAGE SQL
DETERMINISTIC
COMMENT 'Deterministic SQL predicate validator for consumer data isolation. '
        'Confirms consumer_guid parameter is present and not bypassed. '
        'Returns is_valid=TRUE if safe, FALSE with rejection_reason if unsafe. '
        'Latency: ~1ms. No AI — pure pattern matching.'
RETURN
    CASE
        -- Check 1: consumer_guid parameter must be present
        WHEN NOT regexp_like(sql_text, '(?i)consumer_guid\\s*=>\\s*[''"]' || expected_consumer_guid || '[''"]')
             AND NOT regexp_like(sql_text, '(?i)consumer_guid\\s*=>\\s*:consumer_guid')
        THEN named_struct(
            'is_valid', FALSE,
            'rejection_reason', 'MISSING_CONSUMER_GUID: Query does not include the expected consumer_guid parameter',
            'risk_level', 'CRITICAL'
        )

        -- Check 2: OR conditions that could bypass the filter
        WHEN regexp_like(sql_text, '(?i)\\bOR\\b\\s+(?:1\\s*=\\s*1|TRUE|''[^'']*''\\s*=\\s*''[^'']*'')')
        THEN named_struct(
            'is_valid', FALSE,
            'rejection_reason', 'OR_BYPASS: Query contains OR condition that could bypass consumer filter',
            'risk_level', 'CRITICAL'
        )

        -- Check 3: UNION that could append other customers' data
        WHEN regexp_like(sql_text, '(?i)\\bUNION\\b')
        THEN named_struct(
            'is_valid', FALSE,
            'rejection_reason', 'UNION_DETECTED: UNION queries are not permitted for consumer isolation',
            'risk_level', 'CRITICAL'
        )

        -- Check 4: Subqueries referencing Silver/Bronze tables directly
        WHEN regexp_like(sql_text, '(?i)\\b(silver|bronze)\\.')
        THEN named_struct(
            'is_valid', FALSE,
            'rejection_reason', 'DIRECT_TABLE_ACCESS: Query references Silver/Bronze tables directly, bypassing metric view',
            'risk_level', 'HIGH'
        )

        -- Check 5: Multiple different consumer_guid values
        WHEN regexp_like(sql_text, '(?i)consumer_guid\\s*=>\\s*[''"][^''"]+[''"].*consumer_guid\\s*=>\\s*[''"][^''"]+[''"]')
        THEN named_struct(
            'is_valid', FALSE,
            'rejection_reason', 'MULTIPLE_CONSUMERS: Query references multiple consumer_guid values',
            'risk_level', 'CRITICAL'
        )

        -- Check 6: DELETE, UPDATE, INSERT, DROP, ALTER, CREATE
        WHEN regexp_like(sql_text, '(?i)^\\s*(DELETE|UPDATE|INSERT|DROP|ALTER|CREATE|TRUNCATE|MERGE)')
        THEN named_struct(
            'is_valid', FALSE,
            'rejection_reason', 'WRITE_OPERATION: Only SELECT queries are permitted',
            'risk_level', 'CRITICAL'
        )

        -- Check 7: Information schema or system table access
        WHEN regexp_like(sql_text, '(?i)\\b(information_schema|system\\.|pg_catalog)')
        THEN named_struct(
            'is_valid', FALSE,
            'rejection_reason', 'SYSTEM_ACCESS: System table access is not permitted',
            'risk_level', 'HIGH'
        )

        -- All checks passed
        ELSE named_struct(
            'is_valid', TRUE,
            'rejection_reason', CAST(NULL AS STRING),
            'risk_level', 'NONE'
        )
    END;
```

### App Layer Integration

The validator is called by the Databricks App (Node.js) after Genie generates SQL and before execution:

```javascript
// In the app's Genie Agent handler (Node.js AppKit)
async function validateAndExecuteGenieSQL(genieSql, consumerGuid, catalog) {
    // Call the UC UDF via SQL warehouse
    const validationResult = await sqlWarehouse.execute(`
        SELECT ${catalog}.security.validate_consumer_sql(
            '${escapeSql(genieSql)}',
            '${consumerGuid}'
        ) AS validation
    `);

    const { is_valid, rejection_reason, risk_level } = validationResult.validation;

    if (!is_valid) {
        // Log the rejection to MLflow 3
        await mlflow.logEvent('sql_validation_rejected', {
            consumer_guid: consumerGuid,
            rejection_reason,
            risk_level,
            original_sql: genieSql
        });

        if (rejection_reason.startsWith('MISSING_CONSUMER_GUID')) {
            // Retry: inject the parameter into the SQL
            const fixedSql = injectConsumerGuid(genieSql, consumerGuid);
            return validateAndExecuteGenieSQL(fixedSql, consumerGuid, catalog);
        }

        // For all other rejections: return safe error to consumer
        return {
            success: false,
            message: getLocalizedErrorMessage(rejection_reason, locale)
        };
    }

    // SQL is valid — execute it
    return await sqlWarehouse.execute(genieSql);
}
```

### Validation Flow

```
Genie Agent generates SQL
  │
  ▼
SQL Validator UDF (~1ms)
  │
  ├── ✅ VALID → Execute SQL → Return results to consumer
  │
  ├── ❌ MISSING_CONSUMER_GUID → Inject parameter → Re-validate → Execute
  │
  ├── ❌ OR_BYPASS → Reject → Log to MLflow 3 → Return safe error
  │
  ├── ❌ UNION_DETECTED → Reject → Log to MLflow 3 → Return safe error
  │
  ├── ❌ DIRECT_TABLE_ACCESS → Reject → Log to MLflow 3 → Return safe error
  │
  ├── ❌ MULTIPLE_CONSUMERS → Reject → Log to MLflow 3 → Return safe error
  │
  ├── ❌ WRITE_OPERATION → Reject → Log to MLflow 3 → Return safe error
  │
  └── ❌ SYSTEM_ACCESS → Reject → Log to MLflow 3 → Return safe error
```

### What This Validator Does NOT Do

The validator is **deterministic pattern matching only**. It does NOT:

1. **Parse SQL into an AST** — regex is sufficient for the known bypass patterns; AST parsing adds latency and complexity
2. **Evaluate semantic meaning** — that's ai_decide's job (C16, soft validation)
3. **Check topic relevance** — that's ai_decide's job
4. **Detect PII in results** — that's ai_decide's job (runs in parallel with response streaming)
5. **Replace the parameterized metric view** — the metric view is the primary enforcement; the validator is the safety net

### Relationship to ai_decide (C16)

| Concern | SQL Validator (C15) | ai_decide (C16) |
|---|---|---|
| **Type** | Deterministic (regex) | AI-assisted (LLM) |
| **Latency** | ~1ms | ~200ms (parallel) |
| **Blocks execution?** | Yes — hard gate | No — soft validation, parallel |
| **What it checks** | Structural SQL patterns (parameter presence, bypass patterns) | Semantic judgment (topic relevance, PII detection, tone, language) |
| **False positive rate** | Near zero (deterministic) | Low but non-zero (AI judgment) |
| **Cost** | Zero (SQL UDF) | ~$0.000042/call (ai_decide) |

## Non-Functional Requirements

| NFR | Target | Rationale |
|---|---|---|
| **Latency** | <2ms per validation | Must not add perceptible delay to consumer queries |
| **Deterministic** | Same input always produces same output | Security gate must be predictable |
| **Zero false negatives** | Never passes an unsafe query | Security — the validator is the hard gate |
| **Low false positives** | Legitimate queries should not be rejected | UX — false rejections frustrate consumers |
| **Auditability** | Every rejection logged to MLflow 3 with full context | Compliance and debugging |

## Testing

| Test | What It Validates |
|---|---|
| **Valid query passes** | `SELECT MEASURE(total_balance) FROM gold.customer_transaction_metrics(consumer_guid => 'abc')` → is_valid = TRUE |
| **Missing parameter rejected** | `SELECT MEASURE(total_balance) FROM gold.customer_transaction_metrics` → MISSING_CONSUMER_GUID |
| **OR bypass rejected** | `... WHERE customer_id = 'abc' OR 1=1` → OR_BYPASS |
| **UNION rejected** | `SELECT ... UNION SELECT ...` → UNION_DETECTED |
| **Direct table access rejected** | `SELECT * FROM silver.account_transaction` → DIRECT_TABLE_ACCESS |
| **Multiple consumers rejected** | Two different consumer_guid values in one query → MULTIPLE_CONSUMERS |
| **Write operation rejected** | `DELETE FROM ...` → WRITE_OPERATION |
| **System access rejected** | `SELECT * FROM information_schema.tables` → SYSTEM_ACCESS |
| **Parameter injection retry** | Missing parameter → inject → re-validate → passes |
| **Latency benchmark** | 1000 validations complete in <2 seconds total |
| **Adversarial test suite** | 50+ known SQL injection patterns all rejected |

## Deployment

Part of **Bundle 1 (Infrastructure)** — the UDF is registered in the `${catalog}.security` schema.

```sql
-- Deployed by Bundle 1 infrastructure setup
CREATE SCHEMA IF NOT EXISTS ${catalog}.security;

CREATE OR REPLACE FUNCTION ${catalog}.security.validate_consumer_sql(...)
-- Full definition above
```

### Upgrade Path

If regex-based validation proves insufficient (e.g., sophisticated bypass patterns that regex can't catch), the UDF can be upgraded to use a lightweight SQL parser without changing the interface. The app layer calls the same UDF — only the implementation changes.

## Open Questions

| # | Question | Impact | Resolution Path |
|---|---|---|---|
| Q24 | Should the validator use a SQL parser (AST) instead of regex for more robust pattern detection? | Catches more sophisticated bypasses but adds latency | Start with regex (simpler, faster); upgrade to AST if adversarial testing reveals gaps |
| Q25 | Should rejected queries trigger an alert to the ops team, or just log to MLflow 3? | Operational awareness | Log to MLflow 3 always; alert only for CRITICAL risk_level rejections (configurable threshold) |
| — | Should the validator be a Python UDF instead of SQL UDF for more complex pattern matching? | Python UDFs have higher latency but more expressive power | Start with SQL UDF; upgrade to Python if regex proves insufficient |

## References

- **L100 v3** — Security: Layered Enforcement Model (canvas notebooks/1987168172366090)
- **L200-C5** — Metric Views (canvas notebooks/308703764929801) — the SQL being validated
- **L200-C16** — ai_decide Soft Validation (to be designed) — the complementary AI-based checks
- Consumer-Facing Security Patterns Comparative Analysis: https://docs.google.com/document/d/1g4QrTZAEZbkBwcALWjiHaTF2Rca809bfLBnOGuKQ4Eg
