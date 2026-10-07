# L200-C12: Lakebase Auth + Memory — Detailed Design

> **Status:** Draft v1 — Oct 6, 2026
> **Author:** Matthew Giglia
> **Parent:** L100 — Conversational Consumer Finance: System Overview
> **Component:** C12 — Lakebase Auth + Memory (Layer 6: Consumer Application)
> **Priority:** P2
> **Bundle:** Bundle 1 (Infrastructure — Lakebase project) + Bundle 3 (Application — schema + app code)

## Overview

Lakebase (managed Postgres) provides the **stateful backbone** for the consumer app: session management, conversation memory, consumer preferences, consent state, and proactive insights. It bridges the identity gap between the bank's consumer IdP and the Databricks platform — the consumer authenticates via the bank's IdP, and Lakebase maps that identity to a `consumer_guid` that flows through every Genie Agent call as the required metric view parameter.

### Why Lakebase (Not Delta Tables)

| Concern | Lakebase (Postgres) | Delta Tables |
|---|---|---|
| **Session management** | Sub-millisecond key-value lookups | Not designed for point lookups |
| **Conversation memory** | ACID transactions for message ordering | Append-only; no transactional guarantees for ordered inserts |
| **Consumer auth** | PgBouncer handles 10K concurrent connections | SQL warehouse not designed for 10K concurrent point queries |
| **CDF to Delta** | Lakebase CDF automatically captures all changes as Delta tables | N/A — already Delta |
| **PII storage** | Clear-text PII in Postgres (app-layer access only) | Hashed PII in Delta (analytical layer) |

## Dependencies

| Dependency | Component | What It Provides | Status |
|---|---|---|---|
| **Databricks App** | C11 | App that reads/writes Lakebase | Design complete (L200-C11) |
| **Locale Config** | C1 | Default language preference | Design complete (L200-C1) |

## Design

### Lakebase Project Configuration

```yaml
# Created by Bundle 1 (Infrastructure)
# Lakebase project: ccf-${locale}
# Branches: production, dev, test (copy-on-write)
```

### Schema (from L100, refined)

```sql
-- Schema: app (consumer-facing application state)

-- Consumer identity mapping
CREATE TABLE app.customers (
    customer_id       TEXT PRIMARY KEY,          -- Maps to metric view consumer_guid
    auth_provider     TEXT NOT NULL,             -- Bank's IdP identifier
    auth_subject      TEXT NOT NULL,             -- Subject claim from JWT
    display_name      TEXT,                      -- Consumer's display name
    language_pref     TEXT DEFAULT 'en',         -- Locale language preference
    timezone          TEXT DEFAULT 'UTC',        -- Consumer's timezone
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    last_login_at     TIMESTAMPTZ,
    UNIQUE (auth_provider, auth_subject)         -- One customer per IdP subject
);

-- Session management (JWT validated once, session token for subsequent requests)
CREATE TABLE app.sessions (
    session_id        TEXT PRIMARY KEY,
    customer_id       TEXT NOT NULL REFERENCES app.customers(customer_id),
    session_token     TEXT NOT NULL UNIQUE,       -- Short-lived token for subsequent requests
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    expires_at        TIMESTAMPTZ NOT NULL,       -- Session TTL (e.g., 30 minutes)
    last_active_at    TIMESTAMPTZ DEFAULT NOW(),
    ip_address        INET,
    user_agent        TEXT
);
CREATE INDEX idx_sessions_token ON app.sessions(session_token);
CREATE INDEX idx_sessions_customer ON app.sessions(customer_id);

-- Conversation memory
CREATE TABLE app.conversations (
    conversation_id   TEXT PRIMARY KEY,
    customer_id       TEXT NOT NULL REFERENCES app.customers(customer_id),
    genie_conversation_id TEXT,                   -- Genie Agent conversation ID (for stateful follow-ups)
    title             TEXT,                       -- Auto-generated from first message
    started_at        TIMESTAMPTZ DEFAULT NOW(),
    last_active_at    TIMESTAMPTZ DEFAULT NOW(),
    message_count     INT DEFAULT 0
);
CREATE INDEX idx_conversations_customer ON app.conversations(customer_id);

CREATE TABLE app.messages (
    message_id        TEXT PRIMARY KEY,
    conversation_id   TEXT NOT NULL REFERENCES app.conversations(conversation_id),
    role              TEXT NOT NULL,              -- 'consumer' or 'agent'
    content           TEXT NOT NULL,
    genie_agent_id    TEXT,                       -- Which Genie Agent handled this
    genie_sql         TEXT,                       -- Generated SQL (for audit)
    genie_citations   JSONB,                      -- Citations from Genie response
    mlflow_trace_id   TEXT,                       -- Link to MLflow 3 trace
    validation_result JSONB,                      -- SQL validator + ai_decide results
    created_at        TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_messages_conversation ON app.messages(conversation_id);

-- Consumer consent (GDPR)
CREATE TABLE app.consent (
    customer_id       TEXT NOT NULL REFERENCES app.customers(customer_id),
    consent_type      TEXT NOT NULL,              -- 'transaction_history', 'spending_analysis', 'product_recommendations', 'proactive_insights'
    granted           BOOLEAN NOT NULL,
    granted_at        TIMESTAMPTZ,
    revoked_at        TIMESTAMPTZ,
    PRIMARY KEY (customer_id, consent_type)
);

-- Proactive insights (generated by nightly Lakeflow Jobs)
CREATE TABLE app.insights (
    insight_id        TEXT PRIMARY KEY,
    customer_id       TEXT NOT NULL REFERENCES app.customers(customer_id),
    insight_type      TEXT NOT NULL,              -- 'spending_spike', 'savings_goal', 'product_eligible', 'anomaly'
    title             TEXT NOT NULL,              -- Locale-specific title
    content           TEXT NOT NULL,              -- Locale-specific content
    metric_value      NUMERIC,                   -- The metric that triggered the insight
    baseline_value    NUMERIC,                   -- The baseline for comparison
    surfaced          BOOLEAN DEFAULT FALSE,      -- Has the consumer seen this?
    surfaced_at       TIMESTAMPTZ,
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    expires_at        TIMESTAMPTZ                 -- Insights expire (e.g., 7 days)
);
CREATE INDEX idx_insights_customer ON app.insights(customer_id);
```

### Session Flow

```
1. Consumer opens app → bank's IdP issues JWT
2. App receives JWT → validates signature + claims
3. App looks up customer_id from (auth_provider, auth_subject)
   - If not found: create new customer record
4. App creates session: session_id, session_token, expires_at
5. Return session_token to consumer
6. Subsequent requests: consumer sends session_token (not JWT)
7. App validates session_token (~2ms Lakebase lookup)
   - If expired: return 401, consumer re-authenticates
8. Session.customer_id → consumer_guid for metric view parameter
```

### Lakebase CDF → Delta (Audit Trail)

Lakebase CDF automatically captures all changes to Lakebase tables as Delta tables in UC. This provides:

- **Immutable audit trail** of all consumer interactions
- **Queryable via Genie Code** — "show me all consent changes this week"
- **GDPR compliance** — full history of what data was accessed and when

### GDPR Right to Erasure

```sql
-- When a consumer requests deletion:
-- 1. Delete from Lakebase (cascading)
DELETE FROM app.customers WHERE customer_id = ?;
-- Cascades to: sessions, conversations, messages, consent, insights

-- 2. Delete from Silver/Gold Delta tables
DELETE FROM silver.customer WHERE customer_id = ?;
DELETE FROM silver.account_holder WHERE customer_id = ?;
-- Gold MVs: deletion vectors mark rows (no file rewrite)

-- 3. VACUUM to physically remove data
VACUUM silver.customer;
VACUUM gold.mv_customer_transactions;
```

## Non-Functional Requirements

| NFR | Target | Rationale |
|---|---|---|
| **Session lookup** | <3ms p99 | Must not add perceptible delay |
| **Concurrent connections** | 10K (PgBouncer limit) | Supports 50K total customers at ~10% peak concurrency |
| **Conversation retention** | 90 days | Balance between memory and storage |
| **GDPR deletion** | Complete within 72 hours of request | Regulatory requirement |

## Testing

| Test | What It Validates |
|---|---|
| **Session lifecycle** | Create → validate → expire → re-authenticate |
| **Conversation persistence** | Messages stored and retrieved in order |
| **Consent enforcement** | Revoked consent blocks the corresponding query type |
| **GDPR deletion** | Customer deletion cascades to all related records |
| **CDF capture** | All Lakebase changes appear in Delta CDF tables |
| **Concurrent load** | 1000 concurrent session lookups complete in <3ms each |

## Deployment

- **Bundle 1:** Creates Lakebase project + branches (production, dev, test)
- **Bundle 3:** Creates the `app` schema and tables; app code reads/writes Lakebase

## Open Questions

| # | Question | Impact | Resolution Path |
|---|---|---|---|
| Q31 | Should Lakebase AI Search (vector search) be used for long-term conversation memory? | Enables "remember what we discussed last week" | Yes — add vector embeddings of conversation summaries for semantic retrieval :citation[memory.preferences/databricks-apps-stack,Apps stack] |
| — | Should session tokens be JWTs (self-contained) or opaque tokens (Lakebase lookup)? | Latency vs. security | Opaque tokens with Lakebase lookup — simpler, more secure, ~2ms is acceptable |

## References

- **L200-C11** — Databricks App (canvas notebooks/308703764930062)
- **L100 v3** — Lakebase Schema section (canvas notebooks/1987168172366090)
