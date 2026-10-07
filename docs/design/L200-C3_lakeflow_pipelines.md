# L200-C3: Lakeflow Pipelines (SDP) — Detailed Design

> **Status:** Draft v2 — Oct 7, 2026
> **Author:** Matthew Giglia
> **Parent:** L100 — Conversational Consumer Finance: System Overview
> **Component:** C3 — Lakeflow Pipelines (Layer 2: Data Platform)
> **Priority:** P0
> **Bundle:** Bundle 1 (Infrastructure — all environments)

## Overview

The Lakeflow Pipeline transforms raw events from the state machine simulator (or real customer data in production) through the medallion architecture: Bronze → Silver → Gold. It uses **open-source Spark Declarative Pipelines** (`pyspark.pipelines` module) with streaming semantics, metadata-driven YAML event definitions, and VARIANT-based Bronze tables with automatic shredding.

This pipeline is **the same code** regardless of whether the data source is the synthetic generator (Bundle 2) or real customer data (production via the Genie Code mapping workflow). The Bronze schema is the contract — the pipeline doesn't know or care where the data came from.

### Design Lineage

This design applies the SDP patterns established in:
- **RCM Synthetic Data Generator** — VARIANT Bronze with shredding, metadata-driven YAML, Auto Loader with 7-day cleanup, Delta sink for replay
- **dbxWearables/ZeroBus** — production-grade streaming ingestion with Auto Loader

## Dependencies

| Dependency | Component | What It Provides | Status |
|---|---|---|---|
| **State Machine Simulator** | C2 | NDJSON event files in UC Volume landing zone | Design complete (L200-C2) |
| **FIBO Silver Model** | C4 | Target Silver table schemas | Design complete (Research 02) |
| **Gold Materialized Views** | C14 | Target Gold MV definitions | Design complete (L100 v3) |
| **Locale Config** | C1 | Catalog name (`ccf_${locale}`) | Design complete |

## Design

### Pipeline Module

```python
from pyspark import pipelines as dp
```

All pipeline code uses the open-source `pyspark.pipelines` module — no proprietary APIs. Code is portable to any SDP runtime.

### Bronze Layer: VARIANT with Shredding

Every Bronze table follows the same schema — a thin envelope of typed routing keys plus the full payload as `VARIANT`:

```python
@dp.table(
    name="${catalog}.bronze.account_events",
    comment="Raw account lifecycle events from state machine or customer source"
)
def account_events_bronze():
    return (
        spark.readStream
            .format("cloudFiles")
            .option("cloudFiles.format", "json")
            .option("cloudFiles.inferColumnTypes", "false")
            .option("cloudFiles.cleanSource", "DELETE")
            .option("cloudFiles.cleanSourceRetentionPeriod", "7 days")
            .option("cloudFiles.useManagedFileEvents", "true")
            .load(f"/Volumes/{catalog}/landing/account_events/")
            .select(
                col("event_id").cast("string").alias("_event_id"),
                col("event_type").cast("string").alias("_event_type"),
                col("event_date").cast("date").alias("_simulation_date"),
                col("event_timestamp").cast("timestamp").alias("_event_time"),
                parse_json(to_json(struct("*"))).alias("payload"),
                col("_metadata"),
                struct(
                    col("simulation_run_id").alias("simulation_run_id"),
                    col("locale").alias("locale"),
                    col("seed").cast("int").alias("seed"),
                    lit(True).alias("synthetic"),
                    current_timestamp().alias("ingest_time")
                ).alias("_object_metadata")
            )
    )
```

**Bronze table properties (applied to all Bronze tables):**

```sql
CLUSTER BY AUTO
TBLPROPERTIES (
    'enableVariantShredding' = 'true',
    'delta.enableChangeDataFeed' = 'true'
)
```

**Six Bronze streaming tables (Phase 1):**

| Table | Landing Path | Event Types | Silver Tables Fed |
|---|---|---|---|
| `bronze.account_events` | `/Volumes/{catalog}/landing/account_events/` | Account SM transitions (APPLY, KYC_PASS, ACTIVATE, CLOSE, etc.) | party, person, account, party_relationship, party_kyc |
| `bronze.party_events` | `/Volumes/{catalog}/landing/party_events/` | Party attribute changes (address, contact, identifier updates) | party_address, party_contact, party_identifier |
| `bronze.transaction_events` | `/Volumes/{catalog}/landing/transaction_events/` | Transaction SM transitions (AUTHORIZE, POST, DISPUTE, REVERSE, etc.) | account_transaction |
| `bronze.product_events` | `/Volumes/{catalog}/landing/product_events/` | Product SM transitions (OFFER, APPLY, APPROVE, RENEW, etc.) | product, account_identifier |
| `bronze.balance_snapshots` | `/Volumes/{catalog}/landing/balance_snapshots/` | End-of-day balance calculations | account_balance |
| `bronze.statement_events` | `/Volumes/{catalog}/landing/statement_events/` | Monthly statement generation | account_statement |

### Delta Sink for Replay (Archive)

Parallel to each Bronze table, a Delta sink writes an immutable archive copy that is never cleaned:

```python
dp.create_streaming_table(
    name="${catalog}.archive.account_events_raw",
    comment="Immutable archive of all account events for replay and audit. Never truncated."
)

@dp.append_flow(target="${catalog}.archive.account_events_raw")
def account_events_archive():
    return spark.readStream.table(f"{catalog}.bronze.account_events")
```

**Two paths, one source:**

```
NDJSON files in Volume
    │
    ├──→ Auto Loader → Bronze (VARIANT, shredded, 7-day file cleanup)
    │                    └──→ Silver (flattened, typed, clustered)
    │                           └──→ Gold (Enzyme MVs, parameterized MVs)
    │
    └──→ Delta Sink → Archive (immutable, never deleted, for replay)
```

### Silver Layer: Flatten VARIANT + Full Governance

Silver tables extract typed columns from the Bronze VARIANT payload, apply data quality expectations, and add full comments and tags.

```python
@dp.table(
    name="${catalog}.silver.account_transaction",
    comment="FIBO-aligned transaction records. Source: bronze.transaction_events VARIANT payload."
)
@dp.expect_or_drop("valid_transaction_id", "transaction_id IS NOT NULL")
@dp.expect_or_drop("valid_account_id", "account_id IS NOT NULL")
@dp.expect_or_drop("valid_amount", "amount >= 0")
@dp.expect("valid_direction", "direction IN ('DEBIT', 'CREDIT')")
def account_transaction_silver():
    return (
        spark.readStream.table(f"{catalog}.bronze.transaction_events")
        .filter(col("_event_type").isin(
            "AUTHORIZED", "POSTED", "RECONCILED", "REVERSED", "REFUNDED"
        ))
        .select(
            col("payload:transaction_id").cast("string").alias("transaction_id"),
            col("payload:account_id").cast("string").alias("account_id"),
            col("payload:transaction_date").cast("date").alias("transaction_date"),
            col("payload:posting_date").cast("date").alias("posting_date"),
            col("payload:transaction_type").cast("string").alias("transaction_type"),
            col("payload:direction").cast("string").alias("direction"),
            col("payload:amount").cast("decimal(20,4)").alias("amount"),
            col("payload:currency_code").cast("string").alias("currency_code"),
            col("payload:counterparty_iban").cast("string").alias("counterparty_iban"),
            col("payload:merchant_name").cast("string").alias("merchant_name"),
            col("payload:merchant_category").cast("string").alias("merchant_category"),
            col("payload:remittance_info").cast("string").alias("remittance_info"),
            col("payload:payment_scheme").cast("string").alias("payment_scheme"),
            col("payload:channel_code").cast("string").alias("channel_code"),
            col("_event_id").alias("source_event_id"),
            col("_simulation_date"),
            col("_object_metadata"),
            current_timestamp().alias("ingestion_timestamp")
        )
    )
```

**Silver table properties (applied to all Silver tables):**

```sql
CLUSTER BY AUTO
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.enableRowTracking' = 'true',
    'quality' = 'silver',
    'domain' = 'consumer_banking',
    'data_classification' = 'confidential',
    'synthetic' = 'true'
)
```

**Fourteen Silver tables (Phase 1)** — schemas defined in L200-C4 v2:

**Tier 1: Party & Relationship (8 tables)**

| Table | Source Bronze | VARIANT Extraction | SCD2? | Expectations |
|---|---|---|---|---|
| `silver.party` | `bronze.account_events` (APPLY, KYC events) | party_id, party_type, legal_name, status, segment | Yes | valid_party_id NOT NULL |
| `silver.person` | `bronze.account_events` (APPLY events) | party_id, first_name, last_name, date_of_birth, nationality | No | valid_party_id NOT NULL |
| `silver.organization` | `bronze.account_events` (Phase 3) | party_id, legal_form, registration_number | No | Schema only in Phase 1 |
| `silver.party_address` | `bronze.party_events` (ADDRESS_CHANGE) | party_id, address_type, address_lines, city, postal_code, country | Yes | valid_party_id NOT NULL, valid_country |
| `silver.party_contact` | `bronze.party_events` (CONTACT_CHANGE) | party_id, contact_type, contact_value, is_verified | No | valid_contact_type |
| `silver.party_identifier` | `bronze.party_events` (IDENTIFIER_ISSUED) | party_id, identifier_type, identifier_value_hash | No | valid_identifier_type |
| `silver.party_relationship` | `bronze.account_events` (ACTIVATE events) | party_id, related_entity_type, related_entity_id, relationship_type | Yes | valid_relationship_type |
| `silver.party_kyc` | `bronze.account_events` (KYC events) | party_id, kyc_status, verification_date, risk_score | No | valid_kyc_status |

**Tier 2: Accounts & Deposits (6 tables)**

| Table | Source Bronze | VARIANT Extraction | SCD2? | Expectations |
|---|---|---|---|---|
| `silver.account` | `bronze.account_events` (ACTIVATE, CLOSE) | account_id, account_type, product_id, currency, status | Yes | valid_account_id NOT NULL, valid_account_type |
| `silver.account_identifier` | `bronze.product_events` (ACTIVATE) | account_id, identifier_type, identifier_value | No | valid_identifier_type |
| `silver.account_balance` | `bronze.balance_snapshots` | account_id, balance_date, balance_type, amount | No | valid_balance_type, amount >= 0 |
| `silver.account_transaction` | `bronze.transaction_events` | transaction_id, account_id, type, status, direction, amount | No | valid_amount >= 0, valid_direction, valid_status |
| `silver.account_statement` | `bronze.statement_events` | account_id, period_start, period_end, opening/closing balance | No | valid_account_id, period_end >= period_start |
| `silver.product` | `bronze.product_events` (ACTIVATE) | product_id, product_type, currency, rates, credit_limit | No | valid_product_type |

### Gold Layer: Enzyme Materialized Views

Gold materialized views pre-compute joins across Silver tables. Managed by the SDP pipeline with incremental refresh.

```python
@dp.materialized_view(
    name="${catalog}.gold.mv_customer_transactions",
    comment="Pre-computed customer transaction view. Enzyme-optimized. Source for parameterized metric views."
)
def mv_customer_transactions():
    parties = spark.read.table(f"{catalog}.silver.party").filter("is_current = TRUE")
    accounts = spark.read.table(f"{catalog}.silver.account").filter("is_current = TRUE")
    relationships = spark.read.table(f"{catalog}.silver.party_relationship").filter(
        "is_current = TRUE AND related_entity_type = 'ACCOUNT'"
    )
    transactions = spark.read.table(f"{catalog}.silver.account_transaction")
    balances = spark.read.table(f"{catalog}.silver.account_balance")

    return (
        transactions
        .join(accounts, "account_id")
        .join(
            relationships,
            transactions.account_id == relationships.related_entity_id
        )
        .join(parties, relationships.party_id == parties.party_id)
        .join(
            balances,
            (transactions.account_id == balances.account_id) &
            (transactions.transaction_date == balances.balance_date) &
            (balances.balance_type == "AVAILABLE"),
            "left"
        )
        .select(
            parties.party_id.alias("customer_id"),
            parties.customer_segment,
            parties.party_status,
            accounts.account_id,
            accounts.account_type,
            accounts.currency_code,
            transactions.transaction_id,
            transactions.transaction_date,
            transactions.posting_date,
            transactions.transaction_type,
            transactions.transaction_status,
            transactions.direction,
            transactions.amount,
            transactions.currency_code.alias("transaction_currency"),
            transactions.merchant_name,
            transactions.merchant_category,
            transactions.payment_scheme,
            transactions.counterparty_iban,
            transactions.channel_code,
            balances.amount.alias("balance_on_date"),
        )
    )
```

**Gold MV properties:**

```sql
CLUSTER BY AUTO
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.enableRowTracking' = 'true',
    'delta.enableDeletionVectors' = 'true'
)
```

### Metadata-Driven Pipeline: YAML Event Definitions

The pipeline is **entirely metadata-driven**. Each event type is defined in YAML; the pipeline code reads these definitions and dynamically generates Bronze, Silver, and Archive tables.

```yaml
# src/pipelines/config/transaction_events.yaml
event_name: transaction_events
description: "Account transaction lifecycle events"
landing_path: "/Volumes/${catalog}/landing/transaction_events/"
bronze_table: "${catalog}.bronze.transaction_events"
silver_table: "${catalog}.silver.account_transaction"
archive_table: "${catalog}.archive.transaction_events_raw"

auto_loader:
  format: json
  clean_source: DELETE
  clean_source_retention: "7 days"
  use_managed_file_events: true
  infer_column_types: false

bronze_keys:
  - { name: "_event_id", type: "STRING", comment: "Deterministic event identifier" }
  - { name: "_event_type", type: "STRING", comment: "Event classification" }
  - { name: "_simulation_date", type: "DATE", comment: "Simulation date" }
  - { name: "_event_time", type: "TIMESTAMP", comment: "Simulated event time" }

silver_columns:
  - { name: "transaction_id", variant_path: "payload:transaction_id", type: "STRING", nullable: false, comment: "Unique transaction identifier" }
  - { name: "account_id", variant_path: "payload:account_id", type: "STRING", nullable: false, comment: "Account this transaction belongs to" }
  - { name: "transaction_date", variant_path: "payload:transaction_date", type: "DATE", nullable: false, comment: "Date the transaction occurred" }
  - { name: "posting_date", variant_path: "payload:posting_date", type: "DATE", comment: "Date posted to ledger" }
  - { name: "transaction_type", variant_path: "payload:transaction_type", type: "STRING", nullable: false, comment: "CREDIT_TRANSFER, DIRECT_DEBIT, CARD_PURCHASE, etc." }
  - { name: "direction", variant_path: "payload:direction", type: "STRING", nullable: false, comment: "DEBIT or CREDIT" }
  - { name: "amount", variant_path: "payload:amount", type: "DECIMAL(20,4)", nullable: false, comment: "Transaction amount (always non-negative)" }
  - { name: "currency_code", variant_path: "payload:currency_code", type: "STRING", nullable: false, comment: "ISO-4217 currency code" }
  - { name: "merchant_name", variant_path: "payload:merchant_name", type: "STRING", comment: "Merchant or counterparty name" }
  - { name: "merchant_category", variant_path: "payload:merchant_category", type: "STRING", comment: "Merchant category (groceries, dining, etc.)" }
  - { name: "payment_scheme", variant_path: "payload:payment_scheme", type: "STRING", comment: "SCT, SCT_INST, SDD_CORE, ACH, FPS, etc." }

silver_filter: "_event_type IN ('AUTHORIZED', 'POSTED', 'RECONCILED', 'REVERSED', 'REFUNDED')"

expectations:
  - { name: "valid_transaction_id", expr: "transaction_id IS NOT NULL", action: "drop" }
  - { name: "valid_account_id", expr: "account_id IS NOT NULL", action: "drop" }
  - { name: "valid_amount", expr: "amount >= 0", action: "drop" }
  - { name: "valid_direction", expr: "direction IN ('DEBIT', 'CREDIT')", action: "warn" }

table_properties:
  quality: silver
  domain: consumer_banking
  subdomain: transactions
  data_classification: confidential
  synthetic: "true"

clustering: auto
```

**Dynamic table generation from YAML:**

```python
import yaml
from pathlib import Path
from pyspark import pipelines as dp

def load_event_configs(config_dir: str) -> list[dict]:
    configs = []
    for yaml_file in sorted(Path(config_dir).glob("*.yaml")):
        with open(yaml_file) as f:
            configs.append(yaml.safe_load(f))
    return configs

def create_pipeline_tables(config_dir: str, catalog: str):
    for config in load_event_configs(config_dir):
        # Resolve catalog variable
        config = resolve_variables(config, {"catalog": catalog})

        # Create Bronze streaming table
        create_bronze_table(config)

        # Create Archive append flow
        create_archive_flow(config)

        # Create Silver streaming table
        create_silver_table(config)
```

### File Structure

```
src/pipelines/
├── pipeline.py                  # Main pipeline entry point
├── bronze/
│   └── bronze_factory.py        # Dynamic Bronze table creation from YAML
├── silver/
│   ├── silver_factory.py        # Dynamic Silver table creation from YAML
│   └── scd2_factory.py          # SCD2 merge logic for dimension tables
├── gold/
│   ├── mv_customer_transactions.py
│   ├── mv_customer_products.py
│   └── mv_customer_behavior.py
├── config/
│   ├── tier1_party/
│   │   ├── account_events.yaml      # → party, person, account, party_relationship, party_kyc
│   │   └── party_events.yaml        # → party_address, party_contact, party_identifier
│   ├── tier2_accounts/
│   │   ├── transaction_events.yaml  # → account_transaction
│   │   ├── product_events.yaml      # → product, account_identifier
│   │   ├── balance_snapshots.yaml   # → account_balance
│   │   └── statement_events.yaml    # → account_statement
│   ├── tier3_lending/               # Phase 2+ configs (empty in Phase 1)
│   ├── tier4_investments/           # Phase 4+ configs (empty in Phase 1)
│   └── tier5_operations/            # Phase 5+ configs (empty in Phase 1)
└── utils/
    ├── yaml_loader.py           # YAML config reader with variable resolution
    └── expectations.py          # Data quality expectation helpers
```

## Non-Functional Requirements

| NFR | Target | Rationale |
|---|---|---|
| **Streaming latency** | Events available in Silver within 5 minutes of landing in Bronze | Consumer app data freshness |
| **Incremental refresh** | Gold MVs refresh incrementally, not full recompute | Cost and latency |
| **Schema stability** | Bronze VARIANT absorbs schema changes; Silver schema is the contract | Downstream compatibility |
| **Data quality** | All Silver tables have expectations; dropped rows logged | Data integrity |
| **Portability** | All code uses `pyspark.pipelines` (open-source SDP) | No vendor lock-in |

## Testing

| Test | What It Validates |
|---|---|
| YAML config loading | All 6 Phase 1 event configs parse correctly; variable resolution works |
| Bronze VARIANT ingestion | NDJSON → VARIANT with shredding; `_metadata` and `_object_metadata` populated |
| Silver extraction | VARIANT payload fields extracted to correct types; expectations enforced |
| Gold MV joins | Pre-computed joins produce correct results; incremental refresh works |
| Archive completeness | Archive table contains all events (no cleanup) |
| End-to-end | Simulator → NDJSON → Bronze → Silver → Gold → Metric View query returns correct data |

## Deployment

Part of **Bundle 1 (Infrastructure)** — deployed to all environments.

```yaml
# bundles/bundle1-infra/databricks.yml (pipeline section)
resources:
  pipelines:
    ccf_pipeline:
      name: ccf-${var.locale}-pipeline
      catalog: ccf_${var.locale}
      target: ccf_${var.locale}
      libraries:
        - notebook:
            path: src/pipelines/pipeline.py
      configuration:
        catalog: ccf_${var.locale}
        locale: ${var.locale}
      continuous: false  # Triggered by daily simulation job
```

## Open Questions

| # | Question | Impact | Resolution Path |
|---|---|---|---|
| Q11 | Incremental refresh latency for Gold MVs | Data freshness | POC benchmark |
| Q17 | Can SDP read external YAML config files at pipeline execution time? | Metadata-driven pattern | Validate in POC; fallback: compile configs into pipeline code |
| — | Should Bronze tables be partitioned by `_simulation_date`? | Query performance for backfill scenarios | Benchmark; CLUSTER BY AUTO may handle this |
| — | Auto Loader `cleanSource = DELETE` behavior with backfill | Backfill writes many files at once; cleanup timing | Validate that 7-day retention handles backfill correctly |

## References

- L100 — Conversational Consumer Finance (parent)
- L200-C2 — State Machine Simulator (upstream data source)
- Research 02 — FIBO-to-Relational Mapping (Silver table schemas)
- Research 05 — Two-Layer Metric View Pattern (Gold layer design)
- PySpark Pipelines API: https://spark.apache.org/docs/latest/api/python/reference/pyspark.pipelines.html
- Lakeflow Python dev guide: https://learn.microsoft.com/en-us/azure/databricks/ldp/developer/python-dev/
- Lakeflow best practices: https://learn.microsoft.com/en-us/azure/databricks/ldp/best-practices/index/
