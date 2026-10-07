# L200-C10: MLflow 3 Tracing — Detailed Design

> **Status:** Draft v1 — Oct 6, 2026
> **Author:** Matthew Giglia
> **Parent:** L100 — Conversational Consumer Finance: System Overview
> **Component:** C10 — MLflow 3 Tracing (Layer 5: Observability)
> **Priority:** P2
> **Bundle:** Bundle 3 (Application — all environments)

## Overview

MLflow 3 provides **full observability** for every consumer interaction — from the initial HTTP request through authentication, Genie Agent API calls, SQL validation, ai_decide checks, and response delivery. Every trace is stored in UC tables, enabling Genie Code analysis ("show me the slowest consumer requests this week") and compliance auditing.

MLflow tracing is built on **OpenTelemetry** — every trace is a set of OTel spans that can be exported to external observability platforms (Datadog, Grafana, Splunk) via OTLP. :citation[documentation."https://learn.microsoft.com/en-us/azure/databricks/mlflow3/genai/tracing/otel-export/",Export MLflow traces to OpenTelemetry]

## Dependencies

| Dependency | Component | What It Provides | Status |
|---|---|---|---|
| **Agent Orchestration** | C8 | The agent calls that generate traces | Design complete (L200-C8) |
| **SQL Validator** | C15 | Validation results to include in traces | Design complete (L200-C15) |
| **Databricks App** | C11 | AppKit OpenTelemetry plugin for HTTP-level traces | To be designed |

## Design

### Trace Structure (per consumer request)

```
ROOT SPAN: consumer_request
├── auth_span: session_validation (~2ms)
│   ├── lakebase_lookup: session + consent
│   └── result: authenticated / rejected
├── orchestrator_span: intent_classification (~20ms)
│   ├── intent: TRANSACTIONS
│   └── routed_to: transactions_agent
├── genie_span: genie_agent_call (~500-2000ms)
│   ├── agent_id: {transactions_agent_id}
│   ├── question: "Hoeveel heb ik deze maand uitgegeven?"
│   ├── generated_sql: "SELECT MEASURE(monthly_spend) FROM ..."
│   ├── consumer_guid: {guid}
│   └── citations: [...]
├── validation_span: sql_validator (~1ms)
│   ├── is_valid: true
│   └── risk_level: NONE
├── soft_validation_span: ai_decide (~200ms, parallel)
│   ├── topic_relevant: true
│   ├── pii_safe: true
│   ├── language_correct: true
│   └── tone_appropriate: true
├── response_span: stream_response (~50ms)
│   └── response_length: 245 chars
└── persistence_span: lakebase_log (~5ms)
    ├── message_id: {id}
    └── conversation_id: {id}
```

### MLflow Experiment Configuration

```python
# In the Databricks App startup
import mlflow

mlflow.set_experiment(f"/ccf-{locale}/consumer-traces")

# Every consumer request creates a trace
with mlflow.start_span(name="consumer_request") as root:
    root.set_attributes({
        "consumer_guid": consumer_guid,
        "locale": locale,
        "session_id": session_id,
        "request_timestamp": timestamp
    })
    # ... nested spans for each step
```

### Genie Code Analysis Queries

MLflow 3 traces stored in UC tables enable natural-language analysis via Genie Code:

| Question | What It Reveals |
|---|---|
| "Show me the slowest consumer requests this week" | Performance bottlenecks |
| "Which Genie Agent queries are failing most often?" | Agent quality issues |
| "How many SQL validations were rejected today?" | Security event monitoring |
| "What's the average response time by agent?" | Per-agent performance |
| "Show me all requests where ai_decide flagged PII" | PII leak detection |
| "What are the most common consumer questions?" | Product insight |

### Dual Export (MLflow + External)

```python
# Export to both MLflow (UC tables) and external observability
# via OpenTelemetry OTLP protocol
import mlflow

mlflow.tracing.set_destination("databricks")  # UC tables
# Additionally configure OTLP exporter for external platforms
```

## Non-Functional Requirements

| NFR | Target | Rationale |
|---|---|---|
| **Trace completeness** | 100% of consumer requests traced | Compliance and debugging |
| **Async logging** | Trace persistence doesn't block response delivery | Consumer latency |
| **Retention** | 90 days in UC tables; archive to cold storage after | Cost management |
| **Queryable** | Traces queryable via Genie Code and SQL | Operational analysis |

## Testing

| Test | What It Validates |
|---|---|
| **Trace creation** | Every consumer request produces a complete trace |
| **Span hierarchy** | Nested spans correctly represent the request flow |
| **Attribute capture** | consumer_guid, locale, agent_id, SQL, validation results all captured |
| **Genie Code analysis** | Natural-language queries over traces return correct results |
| **Dual export** | Traces appear in both MLflow UI and external platform |

## Deployment

Part of **Bundle 3 (Application)** — configured in the Databricks App's OpenTelemetry plugin. :citation[memory.preferences/databricks-apps-stack,Apps stack]

## References

- MLflow 3 OTel export: https://learn.microsoft.com/en-us/azure/databricks/mlflow3/genai/tracing/otel-export/
- **L200-C8** — Agent Orchestration (canvas notebooks/308703764930017)
- **L200-C15** — SQL Validator (canvas notebooks/308703764929885)
