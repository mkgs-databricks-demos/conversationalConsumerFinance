# L200-C16: ai_decide Soft Validation — Detailed Design

> **Status:** Draft v1 — Oct 6, 2026
> **Author:** Matthew Giglia
> **Parent:** L100 — Conversational Consumer Finance: System Overview
> **Component:** C16 — ai_decide Soft Validation (Cross-cutting: Security)
> **Priority:** P2
> **Bundle:** Bundle 1 (Infrastructure — UDF registration) + Bundle 3 (Application — app integration)

## Overview

ai_decide provides **AI-assisted soft validation** that runs in parallel with response streaming — it handles judgment calls that the deterministic SQL validator (C15) cannot: topic relevance, PII detection in responses, tone/safety, and language consistency. It uses Databricks' `ai_decide()` SQL function with two modes: `noul` (yes/no judgment) and `choice` (multi-option classification).

### Relationship to SQL Validator (C15)

| Concern | SQL Validator (C15) | ai_decide (C16) |
|---|---|---|
| **Type** | Deterministic (regex) | AI-assisted (LLM) |
| **Latency** | ~1ms (blocks execution) | ~200ms (parallel, doesn't block) |
| **What it checks** | Structural SQL patterns | Semantic judgment |
| **Cost** | Zero (SQL UDF) | ~$0.000042/call |
| **False positive rate** | Near zero | Low but non-zero |

**ai_decide does NOT block the happy path.** It runs in parallel with response streaming. If it flags an issue, the app can:
1. **Suppress the response** (if flagged before streaming completes)
2. **Append a warning** (if flagged after partial streaming)
3. **Log for review** (always — every ai_decide result is in the MLflow 3 trace)

## Dependencies

| Dependency | Component | What It Provides | Status |
|---|---|---|---|
| **SQL Validator** | C15 | Hard security gate (ai_decide is the soft complement) | Design complete (L200-C15) |
| **MLflow 3 Tracing** | C10 | Trace logging for ai_decide results | Design complete (L200-C10) |

## Design

### Four Checks in One Call

All four soft validation checks run in a **single ai_decide call** to minimize latency and cost:

```sql
SELECT ai_decide(
    response_text,
    ARRAY(
        'Is this response on-topic for consumer banking (accounts, transactions, products, balances)?',
        'Does this response contain personally identifiable information (PII) of a different consumer than the one who asked?',
        'Is this response appropriate for a consumer-facing banking application (no profanity, no financial advice, no speculation)?',
        'Is this response in the expected language: ${locale.language}?'
    ),
    'choice',
    ARRAY('PASS', 'FAIL_TOPIC', 'FAIL_PII', 'FAIL_TONE', 'FAIL_LANGUAGE')
) AS validation_result
```

### App Layer Integration

```javascript
// Runs in PARALLEL with response streaming — does NOT block
async function softValidateResponse(responseText, locale, consumerGuid) {
    const result = await sqlWarehouse.execute(`
        SELECT ai_decide(
            '${escapeSql(responseText)}',
            ARRAY(
                'Is this on-topic for consumer banking?',
                'Does this contain PII of someone other than the requesting consumer?',
                'Is this appropriate for consumer-facing use?',
                'Is this in ${locale.language}?'
            ),
            'choice',
            ARRAY('PASS', 'FAIL_TOPIC', 'FAIL_PII', 'FAIL_TONE', 'FAIL_LANGUAGE')
        ) AS result
    `);

    return {
        passed: result === 'PASS',
        failure_type: result !== 'PASS' ? result : null,
        cost: 0.000042  // Approximate cost per call
    };
}
```

### Failure Handling

| Failure Type | Action | Consumer Message |
|---|---|---|
| `FAIL_TOPIC` | Log + suppress response | "I can only help with banking questions. Try asking about your accounts, transactions, or products." |
| `FAIL_PII` | **Block immediately** + alert ops | "I encountered an issue processing your request. Please try again." |
| `FAIL_TONE` | Log + rephrase response | Retry with explicit tone instruction |
| `FAIL_LANGUAGE` | Log + retry with language instruction | Retry with `"Respond in ${locale.language}"` prepended |

### Cost Analysis

| Metric | Value |
|---|---|
| Cost per ai_decide call | ~$0.000042 |
| Daily calls (50K DAU × 3 queries) | ~150,000 |
| Daily cost | ~$6.30 |
| Monthly cost | ~$189 |

At $189/month for AI-assisted security validation of every consumer interaction, this is negligible compared to the cost of a single PII leak incident.

## Non-Functional Requirements

| NFR | Target | Rationale |
|---|---|---|
| **Latency** | <300ms (parallel, doesn't block) | Must complete before response streaming finishes |
| **PII detection** | ≥95% recall for cross-consumer PII | Security — PII leaks are the highest-severity failure |
| **False positive rate** | <5% for topic and tone checks | UX — false blocks frustrate consumers |
| **Cost** | <$200/month at 50K DAU | Budget constraint |

## Testing

| Test | What It Validates |
|---|---|
| **On-topic pass** | Banking questions pass topic check |
| **Off-topic fail** | "What's the weather?" fails topic check |
| **PII detection** | Response containing another consumer's name/IBAN is flagged |
| **PII pass** | Response containing only the requesting consumer's data passes |
| **Tone check** | Professional banking responses pass; inappropriate content fails |
| **Language check** | Dutch response passes for NL locale; English response fails for NL locale |
| **Parallel execution** | ai_decide completes before response streaming finishes |
| **Cost tracking** | ai_decide costs logged per request in MLflow 3 trace |

## Deployment

- **Bundle 1:** Registers the ai_decide wrapper UDF in `${catalog}.security` schema (alongside the SQL validator)
- **Bundle 3:** App code calls ai_decide in parallel with response streaming

## Open Questions

| # | Question | Impact | Resolution Path |
|---|---|---|---|
| — | Should ai_decide use `noul` mode (yes/no per question) or `choice` mode (single classification)? | Latency vs. granularity | Start with `choice` (one call, one result); switch to `noul` if we need per-check granularity |
| — | Should FAIL_PII trigger an immediate conversation termination, or just block the current response? | Security vs. UX | Block current response + log + alert. Don't terminate the conversation — the PII leak was in the response, not the consumer's question. |

## References

- **L200-C15** — SQL Validator (canvas notebooks/308703764929885) — the hard complement
- **L200-C10** — MLflow 3 Tracing (canvas notebooks/308703764930041) — trace logging
- **L100 v3** — Security: Layered Enforcement Model (canvas notebooks/1987168172366090)
- Consumer-Facing Security Patterns Comparative Analysis: https://docs.google.com/document/d/1g4QrTZAEZbkBwcALWjiHaTF2Rca809bfLBnOGuKQ4Eg
