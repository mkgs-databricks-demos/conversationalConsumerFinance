# L200-C8: Agent Orchestration — Detailed Design

> **Status:** Draft v2 — Oct 7, 2026
> **Author:** Matthew Giglia
> **Parent:** L100 — Conversational Consumer Finance: System Overview
> **Component:** C8 — Agent Orchestration (Layer 4)
> **Priority:** P2
> **Bundle:** Bundle 3 (Application — all environments)

## Overview

The Agent Orchestration layer is a **thin wrapper** in the Databricks App that prepares consumer requests for the single Genie Agent (C7), validates responses, and manages the security pipeline. With the single-agent design, there is **no intent classification or routing** — every consumer question goes to the same agent. The orchestrator's job is: inject `consumer_guid`, call the agent, validate the SQL, run ai_decide in parallel, and stream the response.

### Why No Routing

The original design had three domain-specific agents requiring intent classification. With a single agent holding all 3 metric views (6% of the 50-table limit), Genie handles domain selection internally — it picks the right metric view based on the question. This eliminates:
- Intent classification logic (~20ms latency saved)
- Misrouting risk (cross-domain questions like "credit card spending" no longer ambiguous)
- Conversation state loss on agent switches

### Future Paths (not needed now)

| Option | When to Use |
|---|---|
| **Supervisor Agent** | Enterprise-facing path where users authenticate via UC identity (`current_user()` works) :citation[documentation."https://learn.microsoft.com/en-us/azure/databricks/agents/agent-bricks/multi-agent-supervisor/",Use Supervisor Agent to create a coordinated multi-agent system] |
| **Genie Agent MCP** | External integrations where each call is independent (no conversation history needed) :citation[documentation."https://learn.microsoft.com/en-us/azure/databricks/agents/mcp-tools/genie-agent/",Genie Agent MCP server] |
| **Multi-agent routing** | When metric view count exceeds ~15 and Genie accuracy degrades from context crowding |

## Dependencies

| Dependency | Component | What It Provides | Status |
|---|---|---|---|
| **Genie Agent** | C7 | Single consumer banking agent per locale | Design complete (L200-C7 v2) |
| **SQL Validator** | C15 | Deterministic SQL validation before execution | Design complete (L200-C15) |
| **ai_decide** | C16 | Soft validation (topic, PII, tone, language) | Design complete (L200-C16) |

## Design

### Orchestrator Flow

```javascript
// src/app/orchestrator.js
async function handleConsumerQuestion(question, consumerGuid, session, locale) {
    // 1. Inject consumer_guid into the request context
    const request = {
        content: `[consumer_guid: ${consumerGuid}] ${question}`,
        conversation_id: session.genieConversationId || null
    };

    // 2. Call the single Genie Agent (Chat mode for stateful conversations)
    const response = await genieAPI.createMessage(CONSUMER_AGENT_ID, request);

    // 3. Extract generated SQL
    const sql = response.attachments?.find(a => a.query)?.query?.query;

    // 4. HARD GATE: Validate SQL (deterministic, ~1ms)
    if (sql) {
        const validation = await validateConsumerSQL(sql, consumerGuid);
        if (!validation.is_valid) {
            if (validation.rejection_reason.startsWith('MISSING_CONSUMER_GUID')) {
                // Retry with parameter injection
                const fixedSql = injectConsumerGuid(sql, consumerGuid);
                return handleConsumerQuestion(question, consumerGuid, session, locale);
            }
            // Log rejection + return safe error
            await logRejection(validation, sql, consumerGuid);
            return { success: false, message: getLocalizedError(validation, locale) };
        }
    }

    // 5. SOFT GATE: ai_decide (parallel, ~200ms, doesn't block streaming)
    const softValidation = softValidateResponse(
        response.attachments?.find(a => a.text)?.text?.content,
        locale, consumerGuid
    );  // Fire-and-forget; check result before final delivery

    // 6. Stream response to consumer
    const result = {
        text: response.attachments?.find(a => a.text)?.text?.content,
        sql: sql,
        citations: response.attachments?.filter(a => a.citation),
        traceId: response.trace_id
    };

    // 7. Check soft validation before final delivery
    const softResult = await softValidation;
    if (!softResult.passed && softResult.failure_type === 'FAIL_PII') {
        // PII leak detected — block response
        await logPIIAlert(result, consumerGuid);
        return { success: false, message: getLocalizedError({ rejection_reason: 'PII_DETECTED' }, locale) };
    }

    // 8. Log everything to MLflow 3 + Lakebase
    await Promise.all([
        logToMLflow(result, validation, softResult, consumerGuid),
        logToLakebase(result, session)
    ]);

    return result;
}
```

### What the Orchestrator Does (and Doesn't Do)

| Responsibility | Does It? | Notes |
|---|---|---|
| **Inject consumer_guid** | ✅ Yes | Prepends to every Genie API request |
| **Call Genie Agent API** | ✅ Yes | Chat mode for stateful conversations |
| **SQL validation (hard)** | ✅ Yes | C15 — deterministic, blocks execution |
| **ai_decide (soft)** | ✅ Yes | C16 — parallel, doesn't block happy path |
| **Parameter injection retry** | ✅ Yes | If Genie omits consumer_guid, inject and retry |
| **MLflow 3 trace logging** | ✅ Yes | Full span tree for every request |
| **Lakebase persistence** | ✅ Yes | Message, SQL, citations, validation results |
| **Intent classification** | ❌ No | Single agent — Genie handles domain selection |
| **Agent routing** | ❌ No | Single agent — no routing needed |
| **MCP tool calls** | ❌ Not yet | Future: banking API actions (transfers, account opening) |

### Genie Agent MCP Server (Future Enhancement)

The single agent has a pre-configured MCP URL for external integrations:

```
https://<workspace>/api/2.0/mcp/genie/{consumer_agent_id}
```

**Limitation:** No conversation history per MCP call. For stateful consumer conversations, the Chat mode API is required. The MCP path is for enterprise integrations where each call is independent.

## Non-Functional Requirements

| NFR | Target | Rationale |
|---|---|---|
| **Orchestrator latency** | <5ms overhead (excluding Genie API call) | Thin wrapper — no routing logic |
| **Stateful conversations** | Genie conversation_id preserved across turns | Follow-up questions work |
| **Security pipeline** | SQL validator + ai_decide on every request | Consumer data protection |
| **Retry on missing parameter** | Automatic parameter injection + retry (max 1 retry) | Graceful handling of Genie omission |

## Testing

| Test | What It Validates |
|---|---|
| **consumer_guid injection** | Every Genie API request includes the consumer_guid |
| **SQL validation integration** | Genie-generated SQL is validated before execution |
| **Parameter injection retry** | Missing consumer_guid → inject → retry → success |
| **ai_decide parallel execution** | Soft validation completes before response delivery |
| **PII blocking** | ai_decide FAIL_PII blocks the response |
| **Stateful follow-up** | "What's my balance?" → "Show me last month" works |
| **MLflow trace completeness** | Every request produces a complete trace with all spans |
| **End-to-end latency** | <3s p95 from question to response (including Genie API) |

## Deployment

Part of **Bundle 3 (Application)** — the orchestrator is a module within the Databricks App (L200-C11).

## Open Questions

| # | Question | Impact | Resolution Path |
|---|---|---|---|
| ~~Q27~~ | ~~Single vs. multi-agent~~ | ~~Resolved~~ | **Resolved: single agent.** No routing needed. |
| Q28 | Should Supervisor Agent be used for the enterprise-facing path? | Dual-audience architecture | Yes — Supervisor Agent for enterprise, custom orchestrator for consumer |

## References

- Supervisor Agent: https://learn.microsoft.com/en-us/azure/databricks/agents/agent-bricks/multi-agent-supervisor/
- Genie Agent MCP: https://learn.microsoft.com/en-us/azure/databricks/agents/mcp-tools/genie-agent/
- Genie in multi-agent systems: https://learn.microsoft.com/en-us/azure/databricks/agents/custom-agents/model-serving/multi-agent-genie/
- **L200-C7 v2** — Single Genie Agent per Locale (canvas notebooks/308703764929950)
- **L200-C15** — SQL Validator (canvas notebooks/308703764929885)
- **L200-C16** — ai_decide Soft Validation (canvas notebooks/308703764930147)
