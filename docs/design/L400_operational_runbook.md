# L400: Operational Runbook & Deployment

> **Status:** Draft v1 — Oct 7, 2026
> **Author:** Matthew Giglia
> **Parent:** L100 v5 — Conversational Consumer Finance: System Overview (canvas notebooks/308703765111130)
> **Scope:** All 17 components across 3 bundles, 3 locales, 4 environments
> **Audience:** Platform engineers, SREs, on-call rotation, NN Bank DevOps

## 1. Environment Architecture

### 1.1 Catalog Naming Convention

| Environment | Catalog Pattern | Schema Personalization | Workspace Binding |
|---|---|---|---|
| **Dev** | `ccf_<locale>_dev` (e.g., `ccf_us_dev`) | DAB `dev_<user>_` prefix on schemas | Dev/interactive workspace |
| **Test** | `ccf_<locale>_tst` (e.g., `ccf_us_tst`) | None — exact schema names match prod | Test workspace |
| **UAT** | `ccf_<locale>_uat` (e.g., `ccf_us_uat`) | None — exact schema names match prod | UAT workspace |
| **Prod** | `ccf_<locale>` (e.g., `ccf_us`) | None — canonical names | Prod workspace |

**Per locale, per environment:** 4 catalogs × 3 locales = 12 catalogs total. Each contains `bronze`, `silver`, `gold` schemas.

### 1.2 Promotion Path

```
dev (personalized schemas, iterate fast)
  ↓  target_catalog changes, schema prefix drops
tst (exact schema names, integration test)
  ↓  target_catalog changes only
uat (exact schema names, business validation)
  ↓  target_catalog changes only
prd (exact schema names, canonical)
```

Schema name discontinuity happens exactly once — dev → tst — which is the natural boundary where code goes from sandbox to shared validated artifact.

### 1.3 Lakebase Branching

| Branch | Purpose | Parent | Reset Policy |
|---|---|---|---|
| `production` | Live consumer sessions, memory, consent | — | Never reset |
| `dev` | Developer testing | production | Reset weekly (copy-on-write) |
| `test` | Integration testing | production | Reset per CI run |

## 2. CI/CD Pipeline

### 2.1 Three-Bundle Deployment Order

```
Bundle 1 (Infrastructure) → Bundle 2 (Data Generator) → Bundle 3 (Application)
         ↓ must complete              ↓ optional                ↓ depends on B1
    All environments              Dev/Demo only            All environments
```

### 2.2 DAB Configuration

```yaml
# databricks.yml (root)
bundle:
  name: conversational-consumer-finance

variables:
  locale:
    description: "Deployment locale (us, gb, nl)"
    default: us
  environment:
    description: "Target environment"
    default: dev

targets:
  dev:
    mode: development
    default: true
    variables:
      catalog: ccf_${var.locale}_dev
  tst:
    variables:
      catalog: ccf_${var.locale}_tst
  uat:
    variables:
      catalog: ccf_${var.locale}_uat
  prd:
    variables:
      catalog: ccf_${var.locale}
    run_as:
      service_principal_name: ccf-prod-deployer
```

### 2.3 GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: CCF Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: databricks/setup-cli@main
      - name: Validate Bundle 1
        run: databricks bundle validate -t tst --var locale=us
      - name: Validate Bundle 3
        run: databricks bundle validate -t tst --var locale=us

  deploy-tst:
    needs: validate
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    strategy:
      matrix:
        locale: [us, gb, nl]
    steps:
      - uses: actions/checkout@v4
      - uses: databricks/setup-cli@main
      - name: Deploy Bundle 1 (Infra)
        run: databricks bundle deploy -t tst --var locale=${{ matrix.locale }}
      - name: Deploy Bundle 3 (App)
        run: databricks bundle deploy -t tst --var locale=${{ matrix.locale }}
      - name: Run Smoke Tests
        run: databricks bundle run smoke_tests -t tst --var locale=${{ matrix.locale }}

  deploy-uat:
    needs: deploy-tst
    runs-on: ubuntu-latest
    environment: uat
    strategy:
      matrix:
        locale: [us, gb, nl]
    steps:
      - uses: actions/checkout@v4
      - uses: databricks/setup-cli@main
      - name: Deploy Bundle 1
        run: databricks bundle deploy -t uat --var locale=${{ matrix.locale }}
      - name: Deploy Bundle 3
        run: databricks bundle deploy -t uat --var locale=${{ matrix.locale }}
      - name: Run Benchmark (100 questions)
        run: databricks bundle run benchmark -t uat --var locale=${{ matrix.locale }}

  deploy-prd:
    needs: deploy-uat
    runs-on: ubuntu-latest
    environment: production
    strategy:
      matrix:
        locale: [us, gb, nl]
    steps:
      - uses: actions/checkout@v4
      - uses: databricks/setup-cli@main
      - name: Deploy Bundle 1
        run: databricks bundle deploy -t prd --var locale=${{ matrix.locale }}
      - name: Deploy Bundle 3
        run: databricks bundle deploy -t prd --var locale=${{ matrix.locale }}
      - name: Canary Validation
        run: databricks bundle run canary_validation -t prd --var locale=${{ matrix.locale }}
```

### 2.4 Deployment Checklist (per locale)

| Step | Command | Validation | Rollback |
|---|---|---|---|
| 1. Deploy infra | `databricks bundle deploy -t prd` | UC schemas exist, Lakebase project healthy | `databricks bundle destroy -t prd` |
| 2. Run SDP pipeline | Pipeline auto-starts on deploy | Bronze → Silver → Gold populated | Pause pipeline, revert bundle |
| 3. Deploy metric views | Part of Bundle 3 job | `DESCRIBE` all 3 MVs, parameter test | Redeploy previous bundle version |
| 4. Deploy UC Pages | Part of Bundle 3 job | Page count = 60, certification status | Redeploy previous bundle version |
| 5. Deploy Genie Agent | Part of Bundle 3 job | Agent responds to test question | Delete agent, redeploy |
| 6. Deploy App | Part of Bundle 3 | Health check endpoint returns 200 | Roll back app version |
| 7. Canary validation | 10 questions per locale | ≥90% correct, 0% cross-consumer | Hold deployment, investigate |

## 3. Observability Configuration

### 3.1 MLflow 3 Tracing

Every consumer interaction produces a full MLflow 3 trace with these spans:

| Span | Parent | Duration Target | What It Captures |
|---|---|---|---|
| `consumer_request` | root | <3s p99 | Full request lifecycle |
| `session_lookup` | consumer_request | <5ms p99 | Lakebase session validation |
| `input_sanitization` | consumer_request | <1ms p99 | PII detection, rate limit check |
| `genie_agent_call` | consumer_request | <2s p99 | Question → SQL → results |
| `sql_validation` | genie_agent_call | <2ms p99 | Predicate validator result |
| `ai_decide` | consumer_request | <500ms p99 | Topic, PII, tone, language checks |
| `response_stream` | consumer_request | <500ms p99 | Token streaming to consumer |
| `trace_persist` | consumer_request | async | MLflow + Lakebase logging |

**Experiment:** `ccf-<locale>-consumer-traces` (one per locale)

**Trace attributes (required on every trace):**
- `consumer_guid` — the authenticated consumer
- `locale` — us, gb, nl
- `session_id` — Lakebase session token
- `agent_space_id` — Genie Agent space ID
- `sql_generated` — the SQL Genie produced
- `parameter_included` — boolean: did the SQL include consumer_guid?
- `measures_used` — list of MEASURE() calls in the SQL
- `response_language` — detected language of the response

### 3.2 OpenTelemetry (App Layer)

The Databricks App emits OTel signals via the AppKit OpenTelemetry plugin:

**Metrics (Prometheus-compatible):**

| Metric | Type | Labels | Alert Threshold |
|---|---|---|---|
| `ccf_request_total` | Counter | locale, status_code | — |
| `ccf_request_duration_seconds` | Histogram | locale, span_name | p99 > 3s |
| `ccf_session_active` | Gauge | locale | > 10K concurrent |
| `ccf_parameter_inclusion_rate` | Gauge | locale | < 95% |
| `ccf_genie_error_rate` | Gauge | locale | > 5% |
| `ccf_ai_decide_flag_rate` | Gauge | locale, check_type | > 10% |
| `ccf_cross_consumer_violations` | Counter | locale | > 0 |

**Logs (structured JSON):**
- Every request: `{timestamp, consumer_guid, locale, session_id, question_hash, response_time_ms, status}`
- Errors: `{timestamp, error_type, stack_trace, consumer_guid, locale, request_id}`
- Security events: `{timestamp, event_type, consumer_guid, details}` — rate limit hit, consent denied, parameter missing, ai_decide flag

**Traces:**
- OpenTelemetry traces exported to MLflow 3 experiment (not a separate trace backend)
- Span context propagated from API Gateway → App → Genie Agent → Metric View

### 3.3 Alerting Rules

| Alert | Condition | Severity | Channel | Runbook Section |
|---|---|---|---|---|
| **Cross-consumer violation** | `ccf_cross_consumer_violations > 0` | P0 — Critical | PagerDuty + Slack | §6.1 |
| **Parameter inclusion drop** | `ccf_parameter_inclusion_rate < 95%` for 5 min | P1 — High | Slack | §6.2 |
| **Latency spike** | `ccf_request_duration_seconds p99 > 3s` for 5 min | P1 — High | Slack | §6.3 |
| **Genie error rate** | `ccf_genie_error_rate > 5%` for 5 min | P1 — High | Slack | §6.4 |
| **App unhealthy** | Health check fails 3 consecutive times | P0 — Critical | PagerDuty | §6.5 |
| **SDP pipeline failure** | Pipeline status = FAILED | P2 — Medium | Slack | §6.6 |
| **Lakebase connection pool** | Active connections > 80% of pool | P2 — Medium | Slack | §6.7 |

## 4. Cost Governance

### 4.1 Compute Resources

| Resource | SKU | Scaling | Estimated Monthly Cost |
|---|---|---|---|
| **Databricks App** | Serverless (auto-scaled) | 0 → N based on request volume | ~$200–$800/locale |
| **Genie Agent** | Serverless SQL (per-query) | Per consumer question | ~$0.01–$0.05/question |
| **SDP Pipeline** | Serverless (streaming) | Continuous, micro-batch | ~$100–$300/locale |
| **Lakebase** | Managed Postgres | Fixed instance + auto-scale | ~$50–$150/locale |
| **MLflow 3** | Included in platform | Per-trace storage | Minimal |
| **State Machine Simulator** | Serverless Job (daily) | 1 run/day, dev/demo only | ~$5–$20/day |

**Total estimated cost per locale:** $400–$1,300/month (50K consumers)

### 4.2 Cost Controls

| Control | Implementation | Threshold |
|---|---|---|
| **Rate limiting** | App-layer per-consumer rate limit | 60 requests/min/consumer |
| **Conversation lifecycle** | Auto-delete conversations > 30 days | Lakebase cron job |
| **Trace retention** | MLflow experiment retention policy | 90 days (configurable) |
| **Pipeline trigger** | SDP trigger interval | 5 min (not continuous) for non-prod |
| **Dev cleanup** | `databricks bundle destroy` in CI | Weekly for inactive dev schemas |
| **Budget alerts** | Databricks budget policies | Alert at 80%, hard stop at 120% |

### 4.3 Tagging Strategy

All resources tagged for cost attribution:

```yaml
tags:
  project: conversational-consumer-finance
  locale: ${var.locale}
  environment: ${var.environment}
  bundle: ${bundle.name}
  owner: matthew.giglia@databricks.com
  cost_center: field-engineering
```

## 5. Disaster Recovery

### 5.1 Recovery Objectives

| Component | RPO (Recovery Point) | RTO (Recovery Time) | Strategy |
|---|---|---|---|
| **Silver/Gold tables** | 0 (CDF + time travel) | <15 min | Delta time travel (30 days) |
| **Metric views** | 0 (DDL in Git) | <5 min | Redeploy from DAB bundle |
| **UC Pages** | 0 (source in Git) | <10 min | Redeploy from DAB bundle |
| **Genie Agent** | 0 (config in Git) | <5 min | Recreate via Management API |
| **Lakebase (sessions)** | <1 hour | <15 min | Postgres point-in-time recovery |
| **Lakebase (memory)** | <1 hour | <15 min | Postgres PITR + Vector Search rebuild |
| **App** | 0 (code in Git) | <5 min | Redeploy from DAB bundle |
| **MLflow traces** | Best effort | N/A (audit, not operational) | Experiment backup |

### 5.2 Recovery Procedures

**Scenario A: Corrupted Silver/Gold data**
1. Identify the corruption timestamp from MLflow traces or SDP pipeline logs
2. `RESTORE TABLE ccf_us.silver.<table> TO TIMESTAMP AS OF '<timestamp>'`
3. Trigger SDP pipeline incremental refresh to rebuild Gold MVs
4. Verify metric views return correct data with test consumer_guid
5. No app restart needed — metric views auto-reflect restored data

**Scenario B: Genie Agent misconfigured or deleted**
1. `databricks bundle deploy -t prd --var locale=<locale>` — redeploys agent from Git config
2. Verify agent responds to benchmark questions
3. If Management API update fails, delete agent and recreate: `DELETE /api/2.0/genie/spaces/<space_id>` then redeploy

**Scenario C: Lakebase data loss**
1. Initiate Postgres point-in-time recovery to last known good state
2. Verify session table integrity: `SELECT COUNT(*) FROM sessions WHERE expires_at > NOW()`
3. Rebuild Vector Search index from conversation history table
4. Active consumer sessions will receive 401 (session expired) — consumers re-authenticate automatically

**Scenario D: Full environment rebuild**
1. `databricks bundle deploy -t prd --var locale=us` (Bundle 1 — infra)
2. Wait for SDP pipeline to populate Silver/Gold from Bronze (Bronze is immutable archive)
3. `databricks bundle deploy -t prd --var locale=us` (Bundle 3 — app)
4. Run full 100-question benchmark per locale
5. Estimated time: <2 hours for full rebuild from Git + Bronze archive

### 5.3 Backup Schedule

| Asset | Backup Method | Frequency | Retention |
|---|---|---|---|
| **Delta tables** | Time travel + CDF | Continuous | 30 days |
| **Bronze archive** | Delta Sink (immutable) | Continuous | Permanent |
| **Lakebase** | Postgres automated backups | Hourly | 7 days |
| **Git repo** | GitHub (source of truth) | Every commit | Permanent |
| **MLflow experiments** | Platform-managed | Continuous | 90 days |

## 6. Incident Response Procedures

### 6.1 P0: Cross-Consumer Data Violation

**Trigger:** `ccf_cross_consumer_violations > 0`

**Severity:** Critical — potential regulatory exposure (GDPR, PSD2)

**Immediate actions (within 5 minutes):**
1. **Kill switch:** Set app environment variable `CCF_MAINTENANCE_MODE=true` — returns 503 to all consumers
2. **Preserve evidence:** Export the MLflow trace for the violating request
3. **Identify scope:** Query MLflow traces for the last 1 hour: `SELECT consumer_guid, sql_generated FROM traces WHERE parameter_included = false`
4. **Notify:** Page on-call + NN Bank security team

**Investigation:**
1. Was the consumer_guid parameter missing from the SQL? → SQL Validator failure
2. Did the metric view return data for wrong consumer? → Parameter enforcement failure
3. Did the app inject the wrong consumer_guid? → Session lookup failure

**Resolution:**
1. Fix the root cause (validator bug, session corruption, agent misconfiguration)
2. Deploy fix to tst → validate → deploy to prd
3. Disable maintenance mode
4. File incident report with affected consumer GUIDs and exposure window

### 6.2 P1: Parameter Inclusion Rate Drop

**Trigger:** `ccf_parameter_inclusion_rate < 95%` for 5 minutes

**Actions:**
1. Check Genie Agent instructions — were they modified outside DAB?
2. Check example SQL — are they still present and correct?
3. Review recent MLflow traces for the failing SQL patterns
4. If agent was modified: redeploy from Git (`databricks bundle deploy`)
5. If Genie behavior changed: add more example SQL to address the failure pattern

### 6.3 P1: Latency Spike

**Trigger:** `ccf_request_duration_seconds p99 > 3s` for 5 minutes

**Actions:**
1. Check which span is slow: `session_lookup`, `genie_agent_call`, `ai_decide`, or `response_stream`
2. If `genie_agent_call`: check Genie Agent API status, check metric view query performance
3. If `session_lookup`: check Lakebase connection pool, check PgBouncer health
4. If `ai_decide`: check Foundation Model API latency
5. If systemic: check Databricks service health page

### 6.4 P1: Genie Error Rate Spike

**Trigger:** `ccf_genie_error_rate > 5%` for 5 minutes

**Actions:**
1. Check Genie Agent API error responses in MLflow traces
2. Common causes: metric view dropped, catalog permissions changed, API rate limit
3. Verify metric views exist: `DESCRIBE ccf_<locale>.gold.customer_transaction_metrics`
4. Verify agent exists: `GET /api/2.0/genie/spaces/<space_id>`
5. If metric view missing: redeploy Bundle 3
6. If API rate limit: implement exponential backoff in app layer

### 6.5 P0: App Unhealthy

**Trigger:** Health check fails 3 consecutive times

**Actions:**
1. Check app logs: `databricks apps get-logs ccf-<locale>-app`
2. Common causes: Lakebase connection failure, OOM, unhandled exception
3. Restart app: `databricks apps restart ccf-<locale>-app`
4. If restart fails: redeploy from Git
5. If persistent: check Lakebase health, check compute quota

### 6.6 P2: SDP Pipeline Failure

**Trigger:** Pipeline status = FAILED

**Actions:**
1. Check pipeline event log for error details
2. Common causes: schema evolution (new column in Bronze), data quality expectation failure, compute timeout
3. If schema evolution: update Silver table DDL, redeploy pipeline
4. If data quality: check Bronze data for anomalies, adjust expectations
5. Restart pipeline: `databricks pipelines start-update <pipeline_id>`
6. **Impact:** Gold MVs become stale until pipeline recovers — metric views still serve last-good data

### 6.7 P2: Lakebase Connection Pool Exhaustion

**Trigger:** Active connections > 80% of pool

**Actions:**
1. Check for connection leaks: long-running queries, unclosed connections
2. Check consumer traffic spike: is this organic growth or an anomaly?
3. Increase PgBouncer pool size if organic growth
4. Kill idle connections: `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND query_start < NOW() - INTERVAL '5 minutes'`

## 7. Nightly Operational Jobs

### 7.1 Job Schedule

| Job | Schedule | Purpose | Alert on Failure |
|---|---|---|---|
| **Daily Simulation** | 06:00 UTC | Generate synthetic data (dev/demo only) | P2 |
| **Nightly Anomaly Detection** | 02:00 UTC | Scan MLflow traces for cross-consumer patterns | P1 |
| **Conversation Cleanup** | 03:00 UTC | Delete Lakebase conversations > 30 days | P3 |
| **Trace Archival** | 04:00 UTC | Archive MLflow traces > 90 days to cold storage | P3 |
| **SQL Pattern Analysis** | 05:00 UTC | Genie Code analysis of generated SQL quality | P3 |
| **Benchmark Regression** | 01:00 UTC (weekly) | Run 100-question benchmark, compare to baseline | P2 |

### 7.2 Nightly Anomaly Detection (Security)

```sql
-- Cross-consumer correlation: flag any consumer_guid that appeared
-- in queries for multiple different consumers
SELECT
    t.consumer_guid AS requesting_consumer,
    regexp_extract(t.sql_generated, "consumer_guid => '([^']+)'") AS queried_consumer,
    COUNT(*) AS violation_count
FROM ccf_us.gold.mlflow_traces t
WHERE t.timestamp > current_timestamp() - INTERVAL 24 HOURS
  AND t.consumer_guid != regexp_extract(t.sql_generated, "consumer_guid => '([^']+)'")
GROUP BY 1, 2
HAVING violation_count > 0;

-- SQL pattern analysis: flag queries without MEASURE() syntax
SELECT
    COUNT(*) AS total_queries,
    SUM(CASE WHEN sql_generated NOT LIKE '%MEASURE(%' THEN 1 ELSE 0 END) AS missing_measure,
    SUM(CASE WHEN parameter_included = false THEN 1 ELSE 0 END) AS missing_parameter
FROM ccf_us.gold.mlflow_traces
WHERE timestamp > current_timestamp() - INTERVAL 24 HOURS;
```

## 8. Runbook Quick Reference

### 8.1 Common Commands

| Action | Command |
|---|---|
| Deploy to prod (US) | `databricks bundle deploy -t prd --var locale=us` |
| Deploy to prod (all locales) | `for l in us gb nl; do databricks bundle deploy -t prd --var locale=$l; done` |
| Check app health | `databricks apps get ccf-<locale>-app` |
| View app logs | `databricks apps get-logs ccf-<locale>-app` |
| Restart app | `databricks apps restart ccf-<locale>-app` |
| Check pipeline status | `databricks pipelines get <pipeline_id>` |
| Restart pipeline | `databricks pipelines start-update <pipeline_id>` |
| Check Genie Agent | `GET /api/2.0/genie/spaces/<space_id>` |
| Run benchmark | `databricks bundle run benchmark -t prd --var locale=us` |
| Enable maintenance mode | Set `CCF_MAINTENANCE_MODE=true` in app env |
| Disable maintenance mode | Set `CCF_MAINTENANCE_MODE=false` in app env |
| Destroy dev environment | `databricks bundle destroy -t dev --var locale=us` |
| Restore table | `RESTORE TABLE <table> TO TIMESTAMP AS OF '<ts>'` |

### 8.2 Key Identifiers (per locale)

| Locale | Prod Catalog | Genie Agent Space ID | App Name | SDP Pipeline ID |
|---|---|---|---|---|
| US | `ccf_us` | TBD (created at deploy) | `ccf-us-app` | TBD |
| GB | `ccf_gb` | TBD (created at deploy) | `ccf-gb-app` | TBD |
| NL | `ccf_nl` | TBD (created at deploy) | `ccf-nl-app` | TBD |

*Space IDs and Pipeline IDs are populated after first deployment and stored in the DAB state file.*

### 8.3 Escalation Path

| Severity | Response Time | Escalation |
|---|---|---|
| **P0 — Critical** | 5 min acknowledge, 30 min resolve | On-call → Engineering Lead → NN Bank Security |
| **P1 — High** | 15 min acknowledge, 2 hr resolve | On-call → Engineering Lead |
| **P2 — Medium** | 1 hr acknowledge, next business day | On-call → Backlog |
| **P3 — Low** | Next business day | Backlog |

## 9. Phase-Gated Operational Expansion

As the system expands through Phases 2–5 (per L200-C17), the operational runbook expands:

| Phase | New Operational Concerns | Runbook Additions |
|---|---|---|
| **Phase 2** | Multi-agent routing, Knowledge Assistant volumes, proactive insights job | Agent routing monitoring, KA volume refresh, insight job SLA |
| **Phase 3** | MCP tool integrations (banking APIs), expanded state machines | MCP endpoint health checks, API circuit breakers, SM tier monitoring |
| **Phase 4** | Load testing at scale (50K concurrent), performance tuning | Load test runbook, auto-scaling policies, connection pool tuning |
| **Phase 5** | Production launch, controlled rollout, regulatory compliance | Canary deployment, feature flags, compliance audit schedule |

## References

- **L100 v5** — System Overview (canvas notebooks/308703765111130)
- **L200-C3** — Lakeflow Pipelines (canvas notebooks/308703764885010)
- **L200-C10** — MLflow 3 Tracing (canvas notebooks/308703764930041)
- **L200-C11** — Databricks App (canvas notebooks/308703764930062)
- **L200-C12** — Lakebase Auth + Memory (canvas notebooks/308703764930094)
- **L200-C15** — SQL Predicate Validator (canvas notebooks/308703764929885)
- **L200-C17** — Phased Expansion Roadmap (canvas notebooks/308703765067070)
- **L300-C5** — Genie Code Session: Metric Views (canvas notebooks/308703765115949)
- **L300-C6** — Genie Code Session: UC Pages (canvas notebooks/308703765116317)
- **L300-C7** — Genie Code Session: Genie Agent (canvas notebooks/308703765116403)
- GitHub repo: https://github.com/mkgs-databricks-demos/conversationalConsumerFinance
