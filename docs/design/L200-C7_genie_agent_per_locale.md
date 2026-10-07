# L200-C7: Genie Agent per Locale — Detailed Design

> **Status:** Draft v2 — Oct 7, 2026
> **Author:** Matthew Giglia
> **Parent:** L100 — Conversational Consumer Finance: System Overview
> **Component:** C7 — Genie Agent per Locale (Layer 3: Semantic Layer)
> **Priority:** P1
> **Bundle:** Bundle 3 (Application — all environments)

## Overview

A **single Genie Agent per locale** serves as the governed query engine for the consumer-facing app. The agent has all 3 parameterized metric views, the knowledge volume, and locale-appropriate instructions with example SQL demonstrating the table-valued function syntax. Created programmatically via the **Genie Agent Management API** (`POST /api/2.0/genie/spaces`) as part of the Bundle 3 deployment.

### Why One Agent, Not Three

The original design split agents by domain (Accounts, Transactions, Products). With only **3 metric views, 12 measures, and 13 fields** — 6% of the 50-table limit — a single agent is optimal:

| Concern | Three Agents | Single Agent (chosen) |
|---|---|---|
| **Routing** | Needs intent classification + risk of misrouting | No routing — Genie handles it |
| **Cross-domain questions** | "Credit card spending this month" — Transactions or Products? | Just works — all metric views in context |
| **Follow-up questions** | Agent switch loses conversation state | Same conversation, stateful follow-ups |
| **Conversation management** | 3× conversations to manage (200K limit per agent) | 1× conversations, simpler lifecycle |
| **Deployment** | 3 agents to create/maintain per locale | 1 agent per locale |
| **Example SQL** | Split across agents — each sees fewer examples | All examples in one agent — richer context |
| **Knowledge volumes** | Attach to which agent? Or all three? | Attach once |

**Multi-agent is the right pattern when** you have 50+ tables, fundamentally different capabilities per agent, or different permission models. None apply here. If the product catalog grows beyond ~15 metric views, split into domain agents at that point.

### Design Lineage

- **Research 06** — Genie Agent + Parameterized MV Interaction (canvas notebooks/308703764921982)
- **L200-C5** — Metric Views (canvas notebooks/308703764929801) — the metric views the agent queries
- **L200-C6** — UC Pages (canvas notebooks/308703764929921) — business term definitions the agent uses
- Genie Agent Management API: `POST /api/2.0/genie/spaces` with `serialized_space` :citation[documentation."https://learn.microsoft.com/en-us/azure/databricks/genie-agents/conversation-api/",Use the Genie Agents API]

## Dependencies

| Dependency | Component | What It Provides | Status |
|---|---|---|---|
| **Metric Views** | C5 | Parameterized metric views the agents query | Design complete (L200-C5) |
| **UC Pages** | C6 | Business term definitions for agent knowledge | Design complete (L200-C6) |
| **Locale Config** | C1 | Language instruction, example questions, synonyms | Design complete (L200-C1) |
| **Gold MVs** | C14 | Layer 1 source for metric views | Design complete (L200-C14) |

## Design

### Single Agent Configuration

One agent per locale with all 3 metric views + knowledge volume:

| Data Source | Type | Purpose |
|---|---|---|
| `gold.customer_transaction_metrics` | Parameterized Metric View | Balances, spending, transactions, categories |
| `gold.customer_product_metrics` | Parameterized Metric View | Product portfolio, account status, eligibility |
| `gold.customer_behavior_metrics` | Parameterized Metric View | Spending trends, anomalies, behavioral patterns |
| `/Volumes/${catalog}/knowledge/` | UC Volume | Product docs, FAQs, fee schedules, regulatory (via Agent mode) |

**Total: 3 metric views + 1 volume = 4 sources** (of 50 max)

### Agent Configuration Template

The agent is defined as a YAML template with locale variables, then serialized to JSON for the Management API:

```yaml
# src/semantic_layer/genie_agents/consumer_agent.yaml.tmpl
title: "${locale.country} Bank — Consumer Banking Agent"
description: "Consumer banking agent for ${locale.country}. Answers questions about accounts, transactions, products, and banking terms. Responds in ${locale.language}."

data_sources:
  tables:
    - identifier: "${catalog}.gold.customer_transaction_metrics"
      description:
        - "Parameterized metric view for customer transaction data, balances, and spending."
        - "MUST be queried as a table-valued function with consumer_guid parameter."
        - "Example: SELECT MEASURE(total_balance) FROM ${catalog}.gold.customer_transaction_metrics(consumer_guid => '{consumer_guid}')"
        - "Measures: total_balance, monthly_spend, total_income, transaction_count, avg_transaction_value"
        - "Fields: account_type, transaction_month, merchant_category, payment_scheme, direction, channel"
    - identifier: "${catalog}.gold.customer_product_metrics"
      description:
        - "Parameterized metric view for customer product portfolio and account status."
        - "MUST be queried as a table-valued function with consumer_guid parameter."
        - "Measures: active_products, total_accounts, savings_balance"
        - "Fields: product_type, account_status, holder_role"
    - identifier: "${catalog}.gold.customer_behavior_metrics"
      description:
        - "Parameterized metric view for customer behavioral aggregations by period and category."
        - "MUST be queried as a table-valued function with consumer_guid parameter."
        - "Measures: total_amount, transaction_count, avg_amount, unique_merchants"
        - "Fields: period, merchant_category, direction"

instructions:
  text_instructions:
    - content:
        - "${locale.genie_agent.language_instruction}"
        - "CRITICAL: Always query metric views using the consumer_guid parameter as a table-valued function."
        - "Example: SELECT ... FROM ${catalog}.gold.customer_transaction_metrics(consumer_guid => '{consumer_guid}') ..."
        - "The consumer_guid is provided in the conversation context. Never omit it."
        - "Use MEASURE() syntax for all metric view measures."
        - "Round all monetary values to 2 decimal places."
        - "When asked about 'last month', use the previous calendar month."
        - "When asked about 'this month', use the current calendar month to date."
        - "For cross-domain questions (e.g., 'spending on my credit card'), join data from multiple metric views as needed."

  example_question_sqls:
    # Accounts domain
    - question: ["${locale.example_questions.whats_my_balance}"]
      sql:
        - "SELECT MEASURE(total_balance) AS balance"
        - "FROM ${catalog}.gold.customer_transaction_metrics(consumer_guid => '{consumer_guid}')"
        - "WHERE balance_type = 'AVAILABLE'"

    - question: ["${locale.example_questions.show_my_accounts}"]
      sql:
        - "SELECT product_type, account_status, MEASURE(total_accounts) AS count"
        - "FROM ${catalog}.gold.customer_product_metrics(consumer_guid => '{consumer_guid}')"
        - "GROUP BY product_type, account_status"

    # Transactions domain
    - question: ["${locale.example_questions.monthly_spending}"]
      sql:
        - "SELECT transaction_month, MEASURE(monthly_spend) AS spend"
        - "FROM ${catalog}.gold.customer_transaction_metrics(consumer_guid => '{consumer_guid}')"
        - "GROUP BY transaction_month"
        - "ORDER BY transaction_month DESC"
        - "LIMIT 6"

    - question: ["${locale.example_questions.spending_by_category}"]
      sql:
        - "SELECT merchant_category, MEASURE(monthly_spend) AS spend, MEASURE(transaction_count) AS txn_count"
        - "FROM ${catalog}.gold.customer_transaction_metrics(consumer_guid => '{consumer_guid}')"
        - "WHERE transaction_month = date_trunc('MONTH', current_date())"
        - "GROUP BY merchant_category"
        - "ORDER BY spend DESC"

    - question: ["${locale.example_questions.recent_transfers}"]
      sql:
        - "SELECT transaction_date, merchant_name, amount, direction"
        - "FROM ${catalog}.gold.customer_transaction_metrics(consumer_guid => '{consumer_guid}')"
        - "WHERE payment_scheme IN (${locale.transfer_schemes})"
        - "ORDER BY transaction_date DESC"
        - "LIMIT 10"

    # Products domain
    - question: ["${locale.example_questions.my_products}"]
      sql:
        - "SELECT product_type, account_status, holder_role"
        - "FROM ${catalog}.gold.customer_product_metrics(consumer_guid => '{consumer_guid}')"
        - "WHERE account_status = 'OPEN'"

    # Behavioral / trend domain
    - question: ["${locale.example_questions.spending_trend}"]
      sql:
        - "SELECT period, MEASURE(total_amount) AS spend"
        - "FROM ${catalog}.gold.customer_behavior_metrics(consumer_guid => '{consumer_guid}')"
        - "WHERE direction = 'DEBIT'"
        - "GROUP BY period"
        - "ORDER BY period DESC"
        - "LIMIT 6"
```

### Locale-Specific Example Questions

```yaml
# In locales/nl.yaml
example_questions:
  whats_my_balance: "Wat is mijn saldo?"
  show_my_accounts: "Laat mijn rekeningen zien"
  monthly_spending: "Hoeveel heb ik deze maand uitgegeven?"
  spending_by_category: "Laat mijn uitgaven per categorie zien"
  recent_transfers: "Laat mijn laatste overschrijvingen zien"
transfer_schemes: "'SCT', 'SCT_INST'"

# In locales/us.yaml
example_questions:
  whats_my_balance: "What's my balance?"
  show_my_accounts: "Show my accounts"
  monthly_spending: "How much did I spend this month?"
  spending_by_category: "Show my spending by category"
  recent_transfers: "Show my recent transfers"
transfer_schemes: "'ACH', 'WIRE', 'ZELLE'"

# In locales/gb.yaml
example_questions:
  whats_my_balance: "What's my current account balance?"
  show_my_accounts: "Show my accounts"
  monthly_spending: "How much have I spent this month?"
  spending_by_category: "Show my spending by category"
  recent_transfers: "Show my recent bank transfers"
transfer_schemes: "'BACS', 'CHAPS', 'FPS'"
```

### Programmatic Deployment via Management API

```python
# src/semantic_layer/deploy_genie_agents.py
import requests
import json
import yaml

def deploy_agent(agent_template_path: str, locale: dict, catalog: str, workspace_url: str, token: str):
    """Deploy a Genie Agent via the Management API"""

    # 1. Load and resolve the template
    resolved_yaml = resolve_template(agent_template_path, locale)
    agent_config = yaml.safe_load(resolved_yaml)

    # 2. Build the serialized_space JSON
    serialized_space = build_serialized_space(agent_config)

    # 3. Call the Management API
    response = requests.post(
        f"{workspace_url}/api/2.0/genie/spaces",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": agent_config["title"],
            "description": agent_config["description"],
            "parent_path": f"/Workspace/Users/service-principal/ccf-{locale['locale']}/",
            "serialized_space": json.dumps(serialized_space)
        }
    )

    return response.json()["space_id"]
```

### Agent Best Practices Applied :citation[documentation."https://learn.microsoft.com/en-us/azure/databricks/genie-agents/best-practices/",Curate an effective Genie Agent]

| Best Practice | How We Apply It |
|---|---|
| **Stay focused (≤5 tables)** | 3 metric views + 1 volume = 4 sources (well under 50) |
| **Well-annotated data** | Metric views have locale-specific comments and synonyms |
| **≥5 example SQL queries** | 7+ locale-specific example queries covering all domains |
| **Use metric views** | All queries go through parameterized metric views, not raw tables |
| **Start small, iterate** | Deploy with 7 examples; add more based on POC testing |

## Non-Functional Requirements

| NFR | Target | Rationale |
|---|---|---|
| **Programmatic deployment** | Agent created via Management API, not manually | Reproducible, locale-driven deployment |
| **Locale accuracy** | Agent responds in the correct language; uses locale-specific terminology | Consumer experience |
| **Parameter inclusion** | ≥95% of generated SQL includes the `consumer_guid` parameter | Security — SQL validator catches the remaining ≤5% |
| **Source count** | 3 metric views + 1 volume = 4 sources (of 50 max) | Headroom for future expansion |
| **200K conversation limit** | Conversation lifecycle policy: create per session, delete after 30 days | API constraint |

## Testing

| Test | What It Validates |
|---|---|
| **API creation** | Agent created successfully via `POST /api/2.0/genie/spaces` |
| **Locale language** | NL agent responds in Dutch; US agent in English; GB agent in British English |
| **Parameter inclusion** | Generated SQL includes `consumer_guid` parameter (100-question benchmark) |
| **MEASURE() syntax** | Generated SQL uses `MEASURE()` for metric view measures |
| **Example SQL accuracy** | All 7+ example queries execute successfully and return correct results |
| **Synonym recognition** | Agent understands "betaalrekening" (NL), "current account" (GB), "checking account" (US) |
| **Cross-domain questions** | "How much did I spend on my credit card?" correctly queries both transaction and product metric views |
| **Knowledge volume** | "What are the fees for my savings account?" retrieves content from the knowledge volume |
| **Stateful follow-ups** | "What's my balance?" → "Show me last month" works in the same conversation |

## Deployment

Part of **Bundle 3 (Application)** — deployed after metric views (C5) and UC Pages (C6).

```yaml
# bundles/bundle3-app/databricks.yml
resources:
  jobs:
    deploy_semantic_layer:
      tasks:
        - task_key: deploy_metric_views
        - task_key: deploy_uc_pages
          depends_on: [deploy_metric_views]
        - task_key: deploy_genie_agents
          depends_on: [deploy_uc_pages]
          notebook_task:
            notebook_path: src/semantic_layer/deploy_genie_agents
            base_parameters:
              locale: ${var.locale}
              catalog: ccf_${var.locale}
```

## Open Questions

| # | Question | Impact | Resolution Path |
|---|---|---|---|
| Q26 | Can the Management API update an existing agent (PUT/PATCH), or must we delete and recreate? | Affects CI/CD workflow | Check API docs for update endpoint; if not available, use delete + create |
| ~~Q27~~ | ~~Single vs. multi-agent~~ | ~~Resolved~~ | **Resolved: single agent.** 3 metric views is 6% of the 50-table limit. Multi-agent adds routing complexity with no accuracy benefit at this scale. Revisit if metric view count exceeds ~15. |
| Q33 | At what metric view count should we split into domain-specific agents? | Future scalability | Benchmark at ~10, ~15, ~20 metric views. Split when Genie accuracy degrades due to context crowding. |

## References

- **Research 06** — Genie + Parameterized MV (canvas notebooks/308703764921982)
- **L200-C5** — Metric Views (canvas notebooks/308703764929801)
- **L200-C6** — UC Pages (canvas notebooks/308703764929921)
- Genie Agent Management API: https://learn.microsoft.com/en-us/azure/databricks/genie-agents/conversation-api/
- Genie Agent best practices: https://learn.microsoft.com/en-us/azure/databricks/genie-agents/best-practices/
- Tune Genie Agent quality: https://learn.microsoft.com/en-us/azure/databricks/genie-agents/tune-quality/
