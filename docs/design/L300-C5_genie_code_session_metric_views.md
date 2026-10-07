# L300-C5: Genie Code Session — Metric Views

> **Status:** Draft v1 — Oct 7, 2026
> **Author:** Matthew Giglia
> **Parent:** L200-C5 v2 — Metric Views per Locale (canvas notebooks/308703764929801)
> **Methodology:** Rapid Ontology Standup — L200-A: Metric View Standup
> **Session Type:** Interactive Genie Code session in DAB repo
> **Estimated Duration:** 45–60 minutes per locale (3 locales = ~3 hours total)

## Session Goal

Create the **3 Phase 1 parameterized metric views** in Unity Catalog using interactive Genie Code sessions:

| Metric View | Source (Layer 1 Gold MV) | Measures | Fields | Parameter |
|---|---|---|---|---|
| `gold.customer_transaction_metrics` | `gold.mv_customer_transactions` | 5 (total_balance, monthly_spend, total_income, transaction_count, avg_transaction_value) | 8 (account_type, transaction_month, transaction_week, transaction_date, merchant_category, payment_scheme, direction, channel) | `consumer_guid` (STRING, no default) |
| `gold.customer_product_metrics` | `gold.mv_customer_products` | 3 (active_products, total_accounts, savings_balance) | 3 (product_type, account_status, holder_role) | `consumer_guid` (STRING, no default) |
| `gold.customer_behavior_metrics` | `gold.mv_customer_behavior` | 4 (total_amount, transaction_count, avg_amount, unique_merchants) | 3 (period, merchant_category, direction) | `consumer_guid` (STRING, no default) |

**Total:** 3 metric views, 12 measures, 14 fields, 1 required parameter each.

## Input Context

### L200 Design References
- **L200-C5 v2** (canvas notebooks/308703764929801) — Full YAML definitions for all 3 metric views with locale template variables
- **L200-C14** (canvas notebooks/308703764885757) — Gold Materialized Views (Layer 1 source tables)
- **L200-C1** (canvas notebooks/308703764929903) — Locale Config Engine (synonym/comment YAML files)
- **Research 05** (canvas notebooks/308703764881180) — Two-Layer Metric View Pattern rationale
- **Research 06** (canvas notebooks/308703764921982) — Genie Agent + Parameterized MV Interaction

### Semantics 02 Terms to Feed Genie Code
From the 108-term glossary (canvas notebooks/308703765065096), the following terms map directly to metric view measures and fields:

**Measures (12 terms):**
- Account Balance, Monthly Spending, Total Income, Transaction Count, Average Transaction Value
- Active Products, Total Accounts, Savings Balance
- Total Amount, Average Amount, Unique Merchants, Spending Trend (MoM)

**Fields / Dimensions (14 terms):**
- Account Type, Transaction Month, Transaction Date, Merchant Category, Payment Scheme, Direction, Channel
- Product Type, Account Status, Holder Role
- Period, Merchant Category (behavior), Direction (behavior)

**Cross-cutting terms:**
- Consumer GUID, Parameterized Metric View, Two-Layer Pattern, Enzyme Materialized View

### Prerequisite Artifacts
Before this session, the following must exist:
1. ✅ Silver tables populated (L200-C4 — 14 Phase 1 tables)
2. ✅ Gold Materialized Views created (L200-C14 — 3 Enzyme MVs)
3. ✅ Locale YAML files committed to repo (L200-C1 — `en.yaml`, `en-GB.yaml`, `nl.yaml`)

## Session Script

### Pre-Session Setup (5 min)

```
# Terminal commands — not Genie Code prompts
cd /Workspace/Repos/<user>/conversationalConsumerFinance
git checkout -b feature/metric-views-phase1
```

Verify Gold MVs exist and have data:
```sql
-- Verify Layer 1 sources
SELECT COUNT(*) FROM ccf_us.gold.mv_customer_transactions;
SELECT COUNT(*) FROM ccf_us.gold.mv_customer_products;
SELECT COUNT(*) FROM ccf_us.gold.mv_customer_behavior;
```

### Phase 1: Research the Source Data (10 min)

**Genie Code Prompt 1 — Profile the Gold MVs:**
> "Profile the three Gold materialized views in `ccf_us.gold`: `mv_customer_transactions`, `mv_customer_products`, and `mv_customer_behavior`. For each, show me the column names, data types, row counts, and a sample of 5 rows. I need to understand the grain and cardinality before building metric views on top of them."

**Expected output:** Column listings, sample data, row counts. Verify the columns match L200-C14's design.

**Genie Code Prompt 2 — Validate join keys:**
> "For each of the three Gold MVs, show me the distinct values of `customer_id` and confirm it's the consumer isolation key. Also show the distinct values of any categorical columns (account_type, product_type, direction, payment_scheme, merchant_category, channel_code, account_status, holder_role) so I can validate the domain values match our FIBO-aligned Silver model."

**Expected output:** Distinct value lists. Cross-reference against L200-C4 v2 Silver model enums.

### Phase 2: Build the YAML Definitions (20 min)

**Genie Code Prompt 3 — Create customer_transaction_metrics:**
> "Create a parameterized metric view `ccf_us.gold.customer_transaction_metrics` using YAML syntax. Here are the requirements:
>
> **Source:** `ccf_us.gold.mv_customer_transactions`
>
> **Required parameter:** `consumer_guid` (STRING, no default value). The filter is `customer_id = :consumer_guid`. This parameter has NO default — queries without it must fail.
>
> **Fields (dimensions):**
> - `account_type` — Type of bank account (checking, savings, credit card, term deposit)
> - `transaction_month` — Expression: `date_trunc('MONTH', transaction_date)`
> - `transaction_week` — Expression: `date_trunc('WEEK', transaction_date)`
> - `transaction_date` — The posting date of the transaction
> - `merchant_category` — Category of the merchant or payee
> - `payment_scheme` — Payment rail used (ACH, WIRE, ZELLE for US)
> - `direction` — CREDIT or DEBIT
> - `channel` — Expression uses column `channel_code`
>
> **Measures:**
> - `total_balance` — `SUM(balance_on_date)` — format: number, prefix '$', 2 decimal places
> - `monthly_spend` — `SUM(CASE WHEN direction = 'DEBIT' THEN amount END)` — format: number, prefix '$', 2 decimal places
> - `total_income` — `SUM(CASE WHEN direction = 'CREDIT' THEN amount END)` — format: number, prefix '$', 2 decimal places
> - `transaction_count` — `COUNT(DISTINCT transaction_id)`
> - `avg_transaction_value` — `AVG(amount)` — format: number, prefix '$', 2 decimal places
>
> **Comment:** 'Consumer transaction metrics. Layer 2 of the two-layer metric view pattern. Source: pre-computed Enzyme MV. Consumer isolation via required consumer_guid parameter.'
>
> Generate the full `CREATE OR REPLACE VIEW ... WITH METRICS LANGUAGE YAML` DDL statement."

**Validation checkpoint:** Review the generated DDL. Verify:
- [ ] Parameter has no default value
- [ ] Filter uses `:consumer_guid` bind syntax
- [ ] All 5 measures use correct aggregation expressions
- [ ] All 8 fields are present with correct expressions
- [ ] Format blocks specify currency prefix and decimal places

**Genie Code Prompt 4 — Create customer_product_metrics:**
> "Create a parameterized metric view `ccf_us.gold.customer_product_metrics` using YAML syntax.
>
> **Source:** `ccf_us.gold.mv_customer_products`
>
> **Required parameter:** `consumer_guid` (STRING, no default). Filter: `customer_id = :consumer_guid`.
>
> **Fields:**
> - `product_type` — Type of banking product (CHECKING, SAVINGS, CREDIT_CARD, TERM_DEPOSIT)
> - `account_status` — Current status (OPEN, CLOSED, BLOCKED, DORMANT)
> - `holder_role` — Role of the customer on the account (PRIMARY, JOINT, AUTHORIZED_USER)
>
> **Measures:**
> - `active_products` — `COUNT(DISTINCT CASE WHEN account_status = 'OPEN' THEN product_id END)`
> - `total_accounts` — `COUNT(DISTINCT account_id)`
> - `savings_balance` — `COUNT(DISTINCT CASE WHEN product_type = 'SAVINGS_ACCOUNT' AND account_status = 'OPEN' THEN account_id END)`
>
> **Comment:** 'Consumer product portfolio metrics. Layer 2 of the two-layer metric view pattern.'
>
> Generate the full DDL."

**Genie Code Prompt 5 — Create customer_behavior_metrics:**
> "Create a parameterized metric view `ccf_us.gold.customer_behavior_metrics` using YAML syntax.
>
> **Source:** `ccf_us.gold.mv_customer_behavior`
>
> **Required parameter:** `consumer_guid` (STRING, no default). Filter: `customer_id = :consumer_guid`.
>
> **Fields:**
> - `period` — The time period (month granularity)
> - `merchant_category` — Spending category
> - `direction` — CREDIT or DEBIT
>
> **Measures:**
> - `total_amount` — `SUM(total_amount)` — format: number, prefix '$', 2 decimal places
> - `transaction_count` — `SUM(transaction_count)`
> - `avg_amount` — `AVG(avg_amount)` — format: number, prefix '$', 2 decimal places
> - `unique_merchants` — `SUM(unique_merchants)`
>
> **Comment:** 'Consumer behavioral metrics. Layer 2 of the two-layer metric view pattern. Pre-aggregated at customer × month × category × direction grain.'
>
> Generate the full DDL."

### Phase 3: Execute and Validate (15 min)

**Genie Code Prompt 6 — Execute all three DDL statements:**
> "Execute the three CREATE OR REPLACE VIEW statements we just built. After each one succeeds, run a DESCRIBE on the view to confirm the schema matches our design."

**Genie Code Prompt 7 — Test parameter enforcement:**
> "Test the parameter enforcement on `ccf_us.gold.customer_transaction_metrics`:
> 1. First, try querying WITHOUT the consumer_guid parameter — this should fail
> 2. Then query WITH a valid consumer_guid using table-valued function syntax:
>    `SELECT MEASURE(total_balance), MEASURE(monthly_spend) FROM ccf_us.gold.customer_transaction_metrics(consumer_guid => '<pick_a_valid_guid>')`
> 3. Show me the results to confirm the measures compute correctly"

**Genie Code Prompt 8 — Cross-consumer isolation test:**
> "Pick two different consumer_guid values from the Gold MV. Run the same query against `customer_transaction_metrics` for each. Confirm the results are different — this validates consumer data isolation."

**Genie Code Prompt 9 — Full measure validation:**
> "For a single consumer_guid, run these validation queries:
> 1. `SELECT MEASURE(total_balance), MEASURE(monthly_spend), MEASURE(total_income), MEASURE(transaction_count), MEASURE(avg_transaction_value) FROM ccf_us.gold.customer_transaction_metrics(consumer_guid => '<guid>')`
> 2. `SELECT MEASURE(active_products), MEASURE(total_accounts), MEASURE(savings_balance) FROM ccf_us.gold.customer_product_metrics(consumer_guid => '<guid>')`
> 3. `SELECT MEASURE(total_amount), MEASURE(transaction_count), MEASURE(avg_amount), MEASURE(unique_merchants) FROM ccf_us.gold.customer_behavior_metrics(consumer_guid => '<guid>')`
>
> All 12 measures should return non-null values."

### Phase 4: Locale Deployment (15 min per additional locale)

**Genie Code Prompt 10 — Generate NL locale variant:**
> "Now create the Dutch (NL) locale variant of `customer_transaction_metrics` in catalog `ccf_nl`. Use the same structure but replace:
> - Currency prefix: '€' instead of '$'
> - Comment: Dutch language version
> - Add synonyms for Dutch terms:
>   - account_type synonyms: ['rekeningtype', 'soort rekening']
>   - total_balance synonyms: ['saldo', 'rekeningsaldo', 'totaal saldo']
>   - monthly_spend synonyms: ['maandelijkse uitgaven', 'uitgaven deze maand']
>   - total_income synonyms: ['maandelijks inkomen', 'bijschrijvingen', 'inkomsten']
>   - transaction_count synonyms: ['aantal transacties']
>   - merchant_category synonyms: ['categorie', 'bestedingscategorie']
>   - direction synonyms: ['afschrijving', 'bijschrijving', 'richting']
>   - payment_scheme synonyms: ['betaalschema', 'betaalmethode']
>
> Generate the full DDL for the NL locale."

**Repeat for GB locale** with £ prefix and British English synonyms (current account vs. checking account, etc.).

### Phase 5: Export and Commit (5 min)

**Genie Code Prompt 11 — Export YAML templates:**
> "Export the resolved YAML for each metric view as a standalone file. I need:
> 1. `src/semantic_layer/metric_views/customer_transaction_metrics.yaml.tmpl` — with `${locale.*}` template variables
> 2. `src/semantic_layer/metric_views/customer_product_metrics.yaml.tmpl`
> 3. `src/semantic_layer/metric_views/customer_behavior_metrics.yaml.tmpl`
> 4. `src/semantic_layer/metric_views/locales/en.yaml` — US English synonyms
> 5. `src/semantic_layer/metric_views/locales/nl.yaml` — Dutch synonyms
> 6. `src/semantic_layer/metric_views/locales/en-GB.yaml` — British English synonyms"

## Validation

### Benchmark Questions (per locale)

These questions should be answerable by a Genie Agent querying the metric views. Run them after the Genie Agent is created (L300-C7):

| # | Question (EN) | Expected SQL Pattern | Expected Metric View |
|---|---|---|---|
| 1 | "What's my balance?" | `SELECT MEASURE(total_balance) FROM customer_transaction_metrics(consumer_guid => ...)` | transaction |
| 2 | "How much did I spend this month?" | `SELECT MEASURE(monthly_spend) FROM ... WHERE transaction_month = date_trunc('MONTH', current_date())` | transaction |
| 3 | "Show my spending by category" | `SELECT merchant_category, MEASURE(monthly_spend) FROM ... GROUP BY merchant_category` | transaction |
| 4 | "How many accounts do I have?" | `SELECT MEASURE(total_accounts) FROM customer_product_metrics(consumer_guid => ...)` | product |
| 5 | "What products am I eligible for?" | `SELECT product_type, MEASURE(active_products) FROM ... GROUP BY product_type` | product |
| 6 | "Show my spending trend" | `SELECT period, MEASURE(total_amount) FROM customer_behavior_metrics(consumer_guid => ...) GROUP BY period ORDER BY period` | behavior |
| 7 | "How many unique merchants did I visit?" | `SELECT MEASURE(unique_merchants) FROM customer_behavior_metrics(consumer_guid => ...)` | behavior |
| 8 | "What's my average transaction?" | `SELECT MEASURE(avg_transaction_value) FROM customer_transaction_metrics(consumer_guid => ...)` | transaction |

### Validation Criteria

| Check | Pass Criteria |
|---|---|
| **Parameter enforcement** | Query without `consumer_guid` returns error, not empty results |
| **Consumer isolation** | Two different GUIDs return different data |
| **All 12 measures** | Non-null values for a populated consumer |
| **MEASURE() syntax** | All measures queryable via `MEASURE(name)` |
| **Table-valued function** | `FROM mv_name(consumer_guid => 'x')` syntax works |
| **Locale synonyms** | NL: "Wat is mijn saldo?" resolves to `total_balance`; GB: "current account" resolves to `account_type` |
| **Format** | Currency values display with correct locale prefix ($, €, £) |

## DAB Integration

### File Outputs

```
src/semantic_layer/
├── metric_views/
│   ├── customer_transaction_metrics.yaml.tmpl
│   ├── customer_product_metrics.yaml.tmpl
│   ├── customer_behavior_metrics.yaml.tmpl
│   ├── locales/
│   │   ├── en.yaml
│   │   ├── en-GB.yaml
│   │   └── nl.yaml
│   └── deploy_metric_views.py
└── ...
```

### Commit Sequence

```bash
git add src/semantic_layer/metric_views/
git commit -m "feat(semantic-layer): add 3 Phase 1 parameterized metric views

- customer_transaction_metrics: 5 measures, 8 fields
- customer_product_metrics: 3 measures, 3 fields
- customer_behavior_metrics: 4 measures, 3 fields
- All use required consumer_guid parameter (no default)
- Locale templates for US, GB, NL with FIBO-aligned synonyms
- Two-layer pattern: sources from Enzyme Gold MVs (Layer 1)

Implements L200-C5 v2 design.
Follows Rapid Ontology Standup L200-A methodology."

git push origin feature/metric-views-phase1
```

### Bundle 3 Integration

The `deploy_metric_views.py` notebook resolves locale templates and executes DDL:

```python
# src/semantic_layer/deploy_metric_views.py
import yaml
from string import Template

def deploy_metric_views(locale: str, catalog: str):
    """Deploy all 3 metric views for a given locale."""
    
    # Load locale config
    locale_config = yaml.safe_load(
        open(f"locales/{locale}.yaml")
    )
    
    templates = [
        "customer_transaction_metrics.yaml.tmpl",
        "customer_product_metrics.yaml.tmpl",
        "customer_behavior_metrics.yaml.tmpl",
    ]
    
    for tmpl_file in templates:
        view_name = tmpl_file.replace(".yaml.tmpl", "")
        
        # Resolve template variables
        tmpl = Template(open(tmpl_file).read())
        resolved_yaml = tmpl.safe_substitute(
            catalog=catalog,
            **flatten_dict(locale_config)
        )
        
        # Execute DDL
        spark.sql(f"""
            CREATE OR REPLACE VIEW {catalog}.gold.{view_name}
            WITH METRICS LANGUAGE YAML AS
            $${resolved_yaml}$$
        """)
        
        print(f"✅ Created {catalog}.gold.{view_name}")
```

## Open Questions

| # | Question | Impact | Resolution Path |
|---|---|---|---|
| Q-L300-1 | Does Genie Code support `CREATE VIEW ... WITH METRICS LANGUAGE YAML` directly, or must we use a notebook cell? | Affects session flow | Test in Genie Code; fallback to notebook execution |
| Q-L300-2 | Can Genie Code generate the locale synonym YAML from Semantics 02 terms automatically? | Could accelerate locale deployment | Test with prompt: "Generate Dutch synonyms for these banking terms" |
| Q-L300-3 | How does Genie Code handle the `${locale.*}` template syntax — will it try to resolve the variables? | Affects template generation | Use raw string blocks or escape syntax |

## References

- **L200-C5 v2** — Metric Views per Locale (canvas notebooks/308703764929801)
- **L200-C14** — Gold Materialized Views (canvas notebooks/308703764885757)
- **L200-C1** — Locale Config Engine (canvas notebooks/308703764929903)
- **Semantics 02** — Full-Spectrum Banking Domain (canvas notebooks/308703765065096)
- **Rapid Ontology Standup** — L200-A: Metric View Standup methodology
- Metric view YAML reference: https://learn.microsoft.com/en-us/azure/databricks/uc-semantics/metric-views/yaml-reference/
- Parameters: https://learn.microsoft.com/en-us/azure/databricks/uc-semantics/metric-views/use-parameters/
