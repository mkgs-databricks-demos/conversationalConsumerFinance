# L200-C11: Databricks App — Detailed Design

> **Status:** Draft v1 — Oct 6, 2026
> **Author:** Matthew Giglia
> **Parent:** L100 — Conversational Consumer Finance: System Overview
> **Component:** C11 — Databricks App (Layer 6: Consumer Application)
> **Priority:** P2
> **Bundle:** Bundle 3 (Application — all environments)

## Overview

The Databricks App is the **consumer-facing application** — a Node.js backend (AppKit) with a React frontend that serves as the API layer between the bank's mobile app and the Databricks platform. It handles consumer authentication, session management, conversation memory, agent orchestration, SQL validation, and response streaming. :citation[memory.preferences/databricks-apps-stack,Apps stack]

### Stack (Required)

- **Backend:** Node.js (Databricks AppKit) — no exceptions :citation[memory.preferences/databricks-apps-stack,Apps stack]
- **Frontend:** React (for the demo UI; in production, NN's mobile app calls the backend API directly)
- **Database:** Lakebase plugin (consumer auth, conversation memory, session state)
- **Observability:** OpenTelemetry plugin (logs, metrics, traces) → MLflow 3 experiment
- **Data Access:** Data API plugin (read UC tables for customer context)

### Initialization

```bash
# From a serverless notebook terminal (never hand-roll the scaffold)
databricks apps init --plugins lakebase,opentelemetry,data-api
```

:citation[memory.preferences/two-bundle-dab-pattern,Two-bundle DAB]

## Dependencies

| Dependency | Component | What It Provides | Status |
|---|---|---|---|
| **Agent Orchestration** | C8 | Routing logic for consumer questions | Design complete (L200-C8) |
| **Lakebase** | C12 | Consumer auth, memory, session tables | To be designed |
| **MLflow 3 Tracing** | C10 | Trace logging for every request | Design complete (L200-C10) |
| **SQL Validator** | C15 | SQL validation before execution | Design complete (L200-C15) |
| **Genie Agents** | C7 | Domain agents to query | Design complete (L200-C7) |

## Design

### API Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/v1/auth/session` | POST | Create session from JWT claims |
| `/api/v1/auth/refresh` | POST | Refresh expired session |
| `/api/v1/conversations` | GET | List consumer's conversations |
| `/api/v1/conversations` | POST | Start a new conversation |
| `/api/v1/conversations/:id/messages` | POST | Send a message (triggers agent orchestration) |
| `/api/v1/conversations/:id/messages` | GET | Get conversation history |
| `/api/v1/insights` | GET | Get proactive insights for the consumer |
| `/api/v1/health` | GET | Health check |

### Request Flow (recap from L100)

```
Consumer → Mobile App → API Gateway (hyperscaler)
  → Authenticate consumer (customer's IdP)
  → Forward: signed consumer identity headers + M2M Databricks SPN
  → Databricks App (Node.js AppKit)
      → 1. Validate session (Lakebase: ~2ms)
      → 2. Load consumer context (language, consent, conversations)
      → 3. Check consent
      → 4. Input sanitization + rate limiting
      → 5. Build Genie Agent request (prepend consumer_guid)
      → 6. Route to appropriate agent (C8 orchestrator)
      → 7. Call Genie Agent API
      → 8. SQL validator (C15): confirm consumer_guid (~1ms)
      → 9. [Parallel] ai_decide (C16): topic, PII, tone, language
      → 10. Stream response to mobile app
      → 11. Log to Lakebase (message, SQL, citations)
      → 12. Log to MLflow 3 (full trace)
      → 13. Check for proactive insights
```

### Project Structure

```
bundles/bundle3-app/
├── databricks.yml              # DAB bundle definition
├── src/
│   ├── index.js                # App entry point (AppKit)
│   ├── routes/
│   │   ├── auth.js             # Session management
│   │   ├── conversations.js    # Conversation CRUD
│   │   ├── messages.js         # Message handling (orchestration trigger)
│   │   └── insights.js         # Proactive insights
│   ├── orchestrator/
│   │   ├── router.js           # Intent classification + routing (C8)
│   │   ├── genie-client.js     # Genie Agent API client
│   │   └── validator.js        # SQL validator integration (C15)
│   ├── middleware/
│   │   ├── auth.js             # JWT validation + session lookup
│   │   ├── rate-limit.js       # Per-consumer rate limiting
│   │   └── sanitize.js         # Input sanitization
│   ├── services/
│   │   ├── lakebase.js         # Lakebase client (sessions, memory, consent)
│   │   ├── mlflow.js           # MLflow 3 trace logging
│   │   └── locale.js           # Locale config loader
│   └── config/
│       └── locale.js           # Resolved locale config
├── frontend/                   # React demo UI
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── ChatWindow.jsx
│   │   │   ├── MessageBubble.jsx
│   │   │   └── InsightCard.jsx
│   │   └── hooks/
│   │       └── useConversation.js
│   └── public/
└── tests/
    ├── orchestrator.test.js
    ├── validator.test.js
    └── e2e/
        └── consumer-flow.test.js
```

## Non-Functional Requirements

| NFR | Target | Rationale |
|---|---|---|
| **Response latency** | <3s p95 end-to-end (including Genie API call) | Consumer app responsiveness |
| **Concurrent users** | 500 (demo) / 5,000 (load test) | NN Bank's expected peak concurrency |
| **Availability** | 99.9% uptime | Consumer-facing SLA |
| **Security** | All 19 checks from L100 security model enforced | Consumer data protection |

## Testing

| Test | What It Validates |
|---|---|
| **Auth flow** | JWT → session creation → subsequent requests use session token |
| **Conversation lifecycle** | Create → send messages → retrieve history → delete |
| **End-to-end** | Consumer question → agent response → correct data returned |
| **Rate limiting** | Excessive requests from one consumer are throttled |
| **Error handling** | Genie API failure → graceful error message to consumer |
| **Locale switching** | App responds in correct language based on locale config |

## Deployment

**Bundle 3 (Application)** — initialized via `databricks apps init` from a serverless notebook terminal.

## Open Questions

| # | Question | Impact | Resolution Path |
|---|---|---|---|
| Q30 | Should the React frontend be included in the POC, or should NN's mobile app call the API directly? | Scope | Include React demo UI for internal demos; NN's mobile app calls the API in production |
| — | Should the app use streaming responses (SSE) or request-response? | UX | Streaming for the demo UI; request-response for the mobile API |

## References

- **L200-C8** — Agent Orchestration (canvas notebooks/308703764930017)
- **L200-C10** — MLflow 3 Tracing (canvas notebooks/308703764930041)
- **L200-C12** — Lakebase (to be designed)
- **L200-C15** — SQL Validator (canvas notebooks/308703764929885)
