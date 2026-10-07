# L300-C7: Genie Code Session — Genie Agent

> **Status:** Draft v1 — Oct 7, 2026
> **Author:** Matthew Giglia
> **Parent:** L200-C7 v2 — Genie Agent per Locale (canvas notebooks/308703764929950)
> **Methodology:** Rapid Ontology Standup — L200-B: Genie Agent Standup
> **Session Type:** Interactive Genie Code session in DAB repo
> **Estimated Duration:** 60–90 minutes per locale (3 locales = ~4 hours total)
> **Prerequisites:** L300-C5 (Metric Views) and L300-C6 (UC Pages) must be complete

## Session Goal

Create **1 Genie Agent per locale** (3 total) — the single governed query engine for the consumer-facing app. Each agent has:

| Component | Count | Details |
|---|---|---|
| **Metric Views** | 3 | customer_transaction_metrics, customer_product_metrics, customer_behavior_metrics |
| **Knowledge Volume** | 1 | Product docs, eligibility rules, FAQ content |
| **Text Instructions** | 8+ | Language, parameter enforcement, MEASURE() syntax, temporal, formatting |
| **Example SQL** | 10+ | Benchmark questions with correct parameterized SQL |
| **Sources** | 4 of 50 | 3 metric views + 1 knowledge volume (6% of limit) |

### Why One Agent, Not Three (from L200-C7 v2)

With only 3 metric views, 12 measures, and 14 fields — 6% of the 50-table limit — a single agent is optimal. No routing needed, cross-domain questions "just work," and follow-up questions maintain conversation state. Multi-agent deferred to Phase 3 when the product catalog exceeds ~15 metric views.

## Input Context

### L200 Design References
- **L200-C7 v2** (canvas notebooks/308703764929950) — Single Genie Agent per locale design with comparison table, configuration template, and deployment strategy
- **L200-C5 v2** (canvas notebooks/308703764929801) — Metric view YAML definitions (the data sources the agent queries)
- **L200-C6 v2** (canvas notebooks/308703764929921) — UC Pages (business term definitions the agent uses via OntoRank)
- **L200-C8** (canvas notebooks/308703764930017) — Agent Orchestration (how the app calls the agent)
- **Research 06** (canvas notebooks/308703764921982) — Genie Agent + Parameterized MV Interaction patterns

### Agent Configuration Template (from L200-C7 v2)

The agent is defined as a YAML template with locale variables, then deployed via the Genie Agent Management API (`POST /api/2.0/genie/spaces`).

### Semantics 02 Terms for Agent Instructions
The agent needs to understand all 60 Phase 1 terms from Semantics 02. The UC Pages (L300-C6) provide the definitions; the agent instructions tell Genie HOW to query the data.

## Session Script

### Pre-Session Setup (5 min)

```bash
cd /Workspace/Repos/<user>/conversationalConsumerFinance
git checkout -b feature/genie-agent-phase1
```

Verify prerequisites:
```sql
-- Verify metric views exist
DESCRIBE ccf_us.gold.customer_transaction_metrics;
DESCRIBE ccf_us.gold.customer_product_metrics;
DESCRIBE ccf_us.gold.customer_behavior_metrics;

-- Verify UC Pages exist
-- (Check via Catalog Explorer or API)
```

### Phase 1: Create the US Locale Agent (30 min)

**Genie Code Prompt 1 — Create the agent:**
> "Create a Genie Agent called 'American Bank — Consumer Banking Agent' with the following configuration:
>
> **Description:** 'Consumer banking agent for American Bank. Answers questions about accounts, transactions, spending, and products in English. All queries are scoped to the authenticated consumer via the consumer_guid parameter.'
>
> **Data Sources (3 metric views):**
> 1. `ccf_us.gold.customer_transaction_metrics` — 'Parameterized metric view for customer transaction data. MUST be queried as a table-valued function with consumer_guid parameter. Example: SELECT MEASURE(total_balance) FROM ccf_us.gold.customer_transaction_metrics(consumer_guid => \'{consumer_guid}\')'
> 2. `ccf_us.gold.customer_product_metrics` — 'Parameterized metric view for customer product portfolio. MUST be queried as a table-valued function with consumer_guid parameter.'
> 3. `ccf_us.gold.customer_behavior_metrics` — 'Parameterized metric view for customer behavioral analytics. MUST be queried as a table-valued function with consumer_guid parameter.'
>
> **Text Instructions:**
> 1. 'You are a consumer banking assistant for American Bank. Always respond in English.'
> 2. 'CRITICAL: Always query metric views using the consumer_guid parameter as a table-valued function. The consumer_guid is provided in the conversation context. Never omit it. Example: SELECT ... FROM ccf_us.gold.customer_transaction_metrics(consumer_guid => \'{consumer_guid}\') ...'
> 3. 'Use MEASURE() syntax for all metric view measures. Example: SELECT MEASURE(total_balance) FROM ...'
> 4. 'Round all monetary values to 2 decimal places. Use $ prefix for currency.'
> 5. 'When asked about \"last month\", use the previous calendar month. When asked about \"this month\", use the current calendar month to date.'
> 6. 'When asked about spending, default to DEBIT direction unless the consumer specifies income/credits.'
> 7. 'When asked about accounts, include both active and inactive unless the consumer specifies otherwise.'
> 8. 'For transfer-related questions, filter payment_scheme to ACH, WIRE, or ZELLE.'
>
> Create the agent and return the space_id."

**Genie Code Prompt 2 — Add example SQL queries:**
> "Add these example SQL queries to the American Bank agent:
>
> **Example 1: 'What's my balance?'**
> ```sql
> SELECT MEASURE(total_balance) AS balance
> FROM ccf_us.gold.customer_transaction_metrics(consumer_guid => '{consumer_guid}')
> WHERE account_type = 'CHECKING'
> ```
>
> **Example 2: 'How much did I spend this month?'**
> ```sql
> SELECT MEASURE(monthly_spend) AS spending
> FROM ccf_us.gold.customer_transaction_metrics(consumer_guid => '{consumer_guid}')
> WHERE transaction_month = date_trunc('MONTH', current_date())
> ```
>
> **Example 3: 'Show my spending by category'**
> ```sql
> SELECT merchant_category, MEASURE(monthly_spend) AS spend, MEASURE(transaction_count) AS txn_count
> FROM ccf_us.gold.customer_transaction_metrics(consumer_guid => '{consumer_guid}')
> WHERE transaction_month = date_trunc('MONTH', current_date())
> GROUP BY merchant_category
> ORDER BY spend DESC
> ```
>
> **Example 4: 'How many accounts do I have?'**
> ```sql
> SELECT product_type, account_status, MEASURE(total_accounts) AS count
> FROM ccf_us.gold.customer_product_metrics(consumer_guid => '{consumer_guid}')
> GROUP BY product_type, account_status
> ```
>
> **Example 5: 'Show my recent transfers'**
> ```sql
> SELECT transaction_date, MEASURE(total_balance) AS amount, direction
> FROM ccf_us.gold.customer_transaction_metrics(consumer_guid => '{consumer_guid}')
> WHERE payment_scheme IN ('ACH', 'WIRE', 'ZELLE')
> ORDER BY transaction_date DESC
> LIMIT 10
> ```
>
> **Example 6: 'What's my spending trend?'**
> ```sql
> SELECT period, MEASURE(total_amount) AS spend
> FROM ccf_us.gold.customer_behavior_metrics(consumer_guid => '{consumer_guid}')
> WHERE direction = 'DEBIT'
> GROUP BY period
> ORDER BY period DESC
> LIMIT 6
> ```
>
> **Example 7: 'How many unique merchants did I visit this month?'**
> ```sql
> SELECT MEASURE(unique_merchants) AS merchants
> FROM ccf_us.gold.customer_behavior_metrics(consumer_guid => '{consumer_guid}')
> WHERE period = date_trunc('MONTH', current_date())
> AND direction = 'DEBIT'
> ```
>
> **Example 8: 'What's my average transaction amount?'**
> ```sql
> SELECT MEASURE(avg_transaction_value) AS avg_txn
> FROM ccf_us.gold.customer_transaction_metrics(consumer_guid => '{consumer_guid}')
> WHERE transaction_month = date_trunc('MONTH', current_date())
> ```
>
> **Example 9: 'Show my income this month'**
> ```sql
> SELECT MEASURE(total_income) AS income
> FROM ccf_us.gold.customer_transaction_metrics(consumer_guid => '{consumer_guid}')
> WHERE transaction_month = date_trunc('MONTH', current_date())
> ```
>
> **Example 10: 'What products do I have?'**
> ```sql
> SELECT product_type, MEASURE(active_products) AS active
> FROM ccf_us.gold.customer_product_metrics(consumer_guid => '{consumer_guid}')
> WHERE account_status = 'OPEN'
> GROUP BY product_type
> ```"

### Phase 2: Benchmark the US Agent (20 min)

**Genie Code Prompt 3 — Run the 100-question benchmark:**
> "I need to benchmark the American Bank agent. Run these 20 questions through the agent (using a valid consumer_guid from the data) and for each, show me:
> 1. The question asked
> 2. The SQL Genie generated
> 3. Whether the SQL includes the consumer_guid parameter (PASS/FAIL)
> 4. Whether the SQL uses MEASURE() syntax (PASS/FAIL)
> 5. Whether the query returns results (PASS/FAIL)
>
> Questions:
> 1. What's my balance?
> 2. How much did I spend this month?
> 3. Show my spending by category
> 4. How many accounts do I have?
> 5. Show my recent transfers
> 6. What's my spending trend over the last 6 months?
> 7. How many unique merchants did I visit?
> 8. What's my average transaction amount?
> 9. Show my income this month
> 10. What products do I have?
> 11. How much did I spend on groceries?
> 12. What's my savings account balance?
> 13. Show my largest transactions this month
> 14. How does my spending this month compare to last month?
> 15. What payment methods do I use most?
> 16. Am I spending more or less than usual?
> 17. Show my credit card transactions
> 18. What's my total income this year?
> 19. How many transactions did I make today?
> 20. Show my account summary"

**Validation checkpoint:** Review benchmark results:
- [ ] ≥95% of queries include `consumer_guid` parameter
- [ ] ≥90% of queries use `MEASURE()` syntax
- [ ] ≥85% of queries return correct results
- [ ] 0% of queries return cross-consumer data

**Genie Code Prompt 4 — Fix any failures:**
> "For any questions where the agent generated incorrect SQL, add additional example SQL queries or refine the text instructions to address the failure pattern. Then re-run the failed questions."

### Phase 3: Create NL Locale Agent (30 min)

**Genie Code Prompt 5 — Create the Dutch agent:**
> "Create a Genie Agent called 'NN Bank — Consument Bankieren Agent' with the following configuration:
>
> **Description:** 'Consument bankieren agent voor NN Bank. Beantwoordt vragen over rekeningen, transacties, uitgaven en producten in het Nederlands. Alle queries zijn beperkt tot de geauthenticeerde consument via de consumer_guid parameter.'
>
> **Data Sources:** Same 3 metric views but in `ccf_nl` catalog:
> 1. `ccf_nl.gold.customer_transaction_metrics`
> 2. `ccf_nl.gold.customer_product_metrics`
> 3. `ccf_nl.gold.customer_behavior_metrics`
>
> **Text Instructions (in Dutch):**
> 1. 'Je bent een bankassistent voor NN Bank. Antwoord altijd in het Nederlands.'
> 2. 'KRITIEK: Gebruik altijd de consumer_guid parameter bij het bevragen van metric views als table-valued function.'
> 3. 'Gebruik MEASURE() syntax voor alle metric view measures.'
> 4. 'Rond alle geldbedragen af op 2 decimalen. Gebruik € als valutasymbool.'
> 5. 'Bij \"vorige maand\" gebruik de vorige kalendermaand. Bij \"deze maand\" gebruik de huidige kalendermaand tot heden.'
> 6. 'Bij vragen over uitgaven, gebruik standaard DEBIT richting tenzij de consument inkomsten/bijschrijvingen specificeert.'
> 7. 'Bij overschrijvingen, filter payment_scheme op SCT, SCT_INST.'
> 8. 'Bij incasso\'s, filter payment_scheme op SDD_CORE.'
>
> **Example SQL (Dutch questions):**
> 1. 'Wat is mijn saldo?' → SELECT MEASURE(total_balance) FROM ccf_nl.gold.customer_transaction_metrics(consumer_guid => '{consumer_guid}')
> 2. 'Hoeveel heb ik deze maand uitgegeven?' → SELECT MEASURE(monthly_spend) FROM ... WHERE transaction_month = date_trunc('MONTH', current_date())
> 3. 'Laat mijn uitgaven per categorie zien' → SELECT merchant_category, MEASURE(monthly_spend) FROM ... GROUP BY merchant_category ORDER BY spend DESC
> 4. 'Laat mijn rekeningen zien' → SELECT product_type, account_status, MEASURE(total_accounts) FROM ccf_nl.gold.customer_product_metrics(consumer_guid => '{consumer_guid}') GROUP BY product_type, account_status
> 5. 'Laat mijn laatste overschrijvingen zien' → SELECT ... WHERE payment_scheme IN ('SCT', 'SCT_INST') ORDER BY transaction_date DESC LIMIT 10
> 6. 'Wat is mijn uitgaventrend?' → SELECT period, MEASURE(total_amount) FROM ccf_nl.gold.customer_behavior_metrics(consumer_guid => '{consumer_guid}') WHERE direction = 'DEBIT' GROUP BY period ORDER BY period DESC LIMIT 6
> 7. 'Hoeveel unieke winkels heb ik bezocht?' → SELECT MEASURE(unique_merchants) FROM ...
> 8. 'Wat is mijn gemiddelde transactiebedrag?' → SELECT MEASURE(avg_transaction_value) FROM ...
> 9. 'Laat mijn inkomen deze maand zien' → SELECT MEASURE(total_income) FROM ...
> 10. 'Welke producten heb ik?' → SELECT product_type, MEASURE(active_products) FROM ... WHERE account_status = 'OPEN' GROUP BY product_type"

### Phase 4: Create GB Locale Agent (30 min)

**Genie Code Prompt 6 — Create the British agent:**
> "Create a Genie Agent called 'British Bank — Consumer Banking Agent' with British English instructions:
>
> Key differences from US:
> - Currency: £ instead of $
> - Terminology: 'current account' not 'checking account', 'sort code' not 'routing number', 'standing order' not 'recurring transfer'
> - Payment schemes: BACS, CHAPS, FPS instead of ACH, WIRE, ZELLE
> - Catalog: `ccf_gb` instead of `ccf_us`
>
> [Same structure as US agent with British English adaptations]"

### Phase 5: Export Agent Configurations (10 min)

**Genie Code Prompt 7 — Export agent configs:**
> "Export the configuration for all 3 agents as YAML template files:
> 1. `src/semantic_layer/genie_agents/consumer_agent.yaml.tmpl` — the locale-parameterized template
> 2. `src/semantic_layer/genie_agents/deploy_genie_agents.py` — deployment script using Management API
>
> The template should use `${locale.*}` variables for all locale-specific content (language instructions, example questions, currency symbol, payment schemes, catalog name)."

## Validation

### 100-Question Benchmark (per locale)

Run the full benchmark after agent creation. Minimum thresholds:

| Metric | Target | Measurement |
|---|---|---|
| **Parameter inclusion rate** | ≥95% | % of generated SQL with `consumer_guid` parameter |
| **MEASURE() usage** | ≥90% | % of generated SQL using `MEASURE()` for measures |
| **Query success rate** | ≥85% | % of queries returning correct, non-empty results |
| **Cross-consumer isolation** | 100% | 0 queries returning data for wrong consumer |
| **Language accuracy** | ≥95% | % of responses in correct locale language |
| **Synonym recognition** | ≥80% | % of locale-specific terms correctly understood |

### Cross-Locale Consistency Test

| Question (EN) | Question (NL) | Question (GB) | Expected: Same Data? |
|---|---|---|---|
| "What's my balance?" | "Wat is mijn saldo?" | "What's my current account balance?" | Yes (same consumer, same metric) |
| "Show spending by category" | "Laat uitgaven per categorie zien" | "Show spending by category" | Yes |
| "Recent transfers" | "Laatste overschrijvingen" | "Recent bank transfers" | Yes (different payment schemes) |

### Agent Quality Tuning Checklist

Per Databricks best practices:
- [ ] ≤5 tables (we have 3 metric views + 1 knowledge volume = 4 ✅)
- [ ] Well-annotated data (locale-specific comments and synonyms ✅)
- [ ] ≥5 example SQL queries (we have 10+ per locale ✅)
- [ ] Use metric views (all agents query parameterized MVs ✅)
- [ ] Start small, iterate (deploy with 10 examples; add more based on benchmark ✅)

## DAB Integration

### File Outputs

```
src/semantic_layer/
├── genie_agents/
│   ├── consumer_agent.yaml.tmpl      # Locale-parameterized template
│   ├── deploy_genie_agents.py        # Management API deployment script
│   └── benchmark/
│       ├── benchmark_questions_en.yaml
│       ├── benchmark_questions_nl.yaml
│       ├── benchmark_questions_gb.yaml
│       └── run_benchmark.py
└── ...
```

### Commit Sequence

```bash
git add src/semantic_layer/genie_agents/
git commit -m "feat(semantic-layer): add single Genie Agent per locale

- 1 agent per locale (US, NL, GB) — 3 total
- Each agent: 3 metric views + 1 knowledge volume (4 of 50 sources)
- 10+ example SQL per locale with parameterized MV syntax
- 8 text instructions per locale (language, parameter, formatting)
- 100-question benchmark suite per locale
- Deployment via Genie Agent Management API

Implements L200-C7 v2 single-agent design.
Follows Rapid Ontology Standup L200-B methodology."

git push origin feature/genie-agent-phase1
```

### Deployment Order (Bundle 3)

```yaml
# bundles/bundle3-app/databricks.yml
resources:
  jobs:
    deploy_semantic_layer:
      tasks:
        - task_key: deploy_metric_views    # L300-C5
        - task_key: deploy_uc_pages        # L300-C6
          depends_on: [deploy_metric_views]
        - task_key: deploy_genie_agents    # L300-C7 (this doc)
          depends_on: [deploy_uc_pages]
        - task_key: run_benchmark          # Validation
          depends_on: [deploy_genie_agents]
```

## Open Questions

| # | Question | Impact | Resolution Path |
|---|---|---|---|
| Q-L300-8 | Can the Management API update an existing agent (PUT/PATCH), or must we delete and recreate? | Affects CI/CD idempotency | Test API; if no update, use delete + create pattern |
| Q-L300-9 | How do we inject `consumer_guid` into the conversation context before the first question? | Affects app integration (L200-C8/C11) | Options: system message injection, conversation metadata, or app-layer parameter injection |
| Q-L300-10 | What's the optimal number of example SQL queries? Diminishing returns after N? | Affects curation effort | Start with 10, benchmark, add more if accuracy < 90% |
| Q-L300-11 | Can we attach the knowledge volume programmatically via the Management API? | Affects deployment automation | Check API docs for volume attachment |

## References

- **L200-C7 v2** — Genie Agent per Locale (canvas notebooks/308703764929950)
- **L200-C5 v2** — Metric Views per Locale (canvas notebooks/308703764929801)
- **L200-C6 v2** — UC Pages per Locale (canvas notebooks/308703764929921)
- **L200-C8** — Agent Orchestration (canvas notebooks/308703764930017)
- **Research 06** — Genie Agent + Parameterized MV Interaction (canvas notebooks/308703764921982)
- **Rapid Ontology Standup** — L200-B: Genie Agent Standup methodology
- Genie Agent Management API: https://learn.microsoft.com/en-us/azure/databricks/genie-agents/conversation-api/
- Genie Agent best practices: https://learn.microsoft.com/en-us/azure/databricks/genie-agents/best-practices/
- Tune Genie Agent quality: https://learn.microsoft.com/en-us/azure/databricks/genie-agents/tune-quality/
