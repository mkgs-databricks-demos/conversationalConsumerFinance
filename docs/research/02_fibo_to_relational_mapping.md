# FIBO-to-Relational Mapping for Retail Banking

> **Status:** Draft — Oct 6, 2026
> **Author:** Matthew Giglia
> **File:** docs/research/02_fibo_relational_mapping.md
> **Scope:** How to map FIBO OWL concepts to a normalized relational model in Delta Lake for the Silver layer

## Purpose

FIBO is an OWL ontology — it defines concepts and relationships semantically, not as a physical database schema. This document captures the mapping rules and the concrete Silver table DDL that implements FIBO's retail banking concepts as Delta tables. This is the foundation for L200-C4 (FIBO-Aligned Silver Model) and L200-C14 (Gold Materialized Views).

## Mapping Rules: FIBO → Relational

| FIBO Construct | Relational Representation |
|---|---|
| `owl:Class` | Entity table |
| Subclass | Supertype/subtype tables or a controlled `entity_type` column |
| Datatype property | Typed column |
| Functional property | Column with uniqueness or one-row-per-entity rule |
| Object property, 1-to-1 | Foreign key |
| Object property, 1-to-many | Foreign key on the many-side |
| Object property, many-to-many | Bridge table |
| Qualified relationship | Relationship table with attributes |
| `owl:Restriction` | `NOT NULL`, `CHECK`, uniqueness or data-quality test |
| Individual/reference value | Reference or code table |
| Identifier | Business identifier table or column |
| Annotation property | Metadata/catalog table |
| URI/IRI | `fibo_iri` or `semantic_id` column (optional) |
| Temporal qualification | `valid_from`, `valid_to`, `is_current` |
| Provenance | Source-system and ingestion columns |

### Key Principle

Separate three types of identity:
1. **Business identity** — account number, customer number (source system)
2. **Technical identity** — generated UUID or surrogate key (warehouse)
3. **Semantic identity** — FIBO IRI (optional, for traceability to the ontology)

## Silver Table DDL

All tables use:
- `DECIMAL(20,4)` for monetary amounts — never DOUBLE
- `valid_from` / `valid_to` / `is_current` for SCD2 history
- Delta CDF enabled (`delta.enableChangeDataFeed = true`)
- `source_system` and `record_hash` for provenance

### silver.customer (FIBO: Party / CustomerAccountHolder)

```sql
CREATE TABLE IF NOT EXISTS silver.customer (
    customer_id            STRING NOT NULL,
    party_type             STRING NOT NULL,
    legal_name             STRING,
    first_name             STRING,
    last_name              STRING,
    date_of_birth          DATE,
    country_of_residence   STRING,
    customer_status        STRING NOT NULL,
    customer_segment       STRING,
    onboarding_date        DATE,
    closure_date           DATE,
    source_system          STRING NOT NULL,
    record_hash            STRING NOT NULL,
    valid_from             TIMESTAMP NOT NULL,
    valid_to               TIMESTAMP,
    is_current             BOOLEAN NOT NULL,
    ingestion_timestamp    TIMESTAMP NOT NULL,
    CONSTRAINT chk_party_type CHECK (party_type IN ('PERSON', 'ORGANIZATION')),
    CONSTRAINT chk_customer_status CHECK (customer_status IN ('PROSPECT', 'ACTIVE', 'SUSPENDED', 'CLOSED'))
) USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');
```

### silver.account (FIBO: CustomerAccount / TransactionDepositAccount / DepositAccount)

```sql
CREATE TABLE IF NOT EXISTS silver.account (
    account_id             STRING NOT NULL,
    account_type           STRING NOT NULL,
    product_id             STRING NOT NULL,
    account_status         STRING NOT NULL,
    currency_code          STRING NOT NULL,
    opened_date            DATE NOT NULL,
    closed_date            DATE,
    source_system          STRING NOT NULL,
    record_hash            STRING NOT NULL,
    valid_from             TIMESTAMP NOT NULL,
    valid_to               TIMESTAMP,
    is_current             BOOLEAN NOT NULL,
    ingestion_timestamp    TIMESTAMP NOT NULL,
    CONSTRAINT chk_account_type CHECK (account_type IN ('PAYMENT', 'SAVINGS', 'TERM_DEPOSIT', 'CREDIT_CARD')),
    CONSTRAINT chk_account_status CHECK (account_status IN ('PENDING', 'OPEN', 'DORMANT', 'BLOCKED', 'CLOSED')),
    CONSTRAINT chk_account_dates CHECK (closed_date IS NULL OR closed_date >= opened_date)
) USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');
```

### silver.account_holder (FIBO: AccountHolder / hasPrimaryAccountHolder)

Bridge table — an account may have multiple holders, a customer may have multiple accounts.

```sql
CREATE TABLE IF NOT EXISTS silver.account_holder (
    account_id             STRING NOT NULL,
    customer_id            STRING NOT NULL,
    holder_role            STRING NOT NULL,
    valid_from             TIMESTAMP NOT NULL,
    valid_to               TIMESTAMP,
    is_current             BOOLEAN NOT NULL,
    source_system          STRING NOT NULL,
    record_hash            STRING NOT NULL,
    ingestion_timestamp    TIMESTAMP NOT NULL,
    CONSTRAINT chk_holder_role CHECK (holder_role IN ('PRIMARY', 'JOINT', 'AUTHORIZED_USER'))
) USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');
```

### silver.account_balance_daily (FIBO: Balance / hasBalance)

```sql
CREATE TABLE IF NOT EXISTS silver.account_balance_daily (
    account_id             STRING NOT NULL,
    balance_date           DATE NOT NULL,
    balance_type           STRING NOT NULL,
    amount                 DECIMAL(20,4) NOT NULL,
    currency_code          STRING NOT NULL,
    source_system          STRING NOT NULL,
    record_hash            STRING NOT NULL,
    ingestion_timestamp    TIMESTAMP NOT NULL,
    CONSTRAINT chk_balance_type CHECK (balance_type IN ('LEDGER', 'AVAILABLE', 'COLLECTED', 'CURRENT'))
) USING DELTA
PARTITIONED BY (balance_date)
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');
```

### silver.account_transaction (FIBO: IndividualTransaction)

```sql
CREATE TABLE IF NOT EXISTS silver.account_transaction (
    transaction_id         STRING NOT NULL,
    account_id             STRING NOT NULL,
    transaction_date       DATE NOT NULL,
    posting_date           DATE,
    value_date             DATE,
    transaction_type       STRING NOT NULL,
    direction              STRING NOT NULL,
    amount                 DECIMAL(20,4) NOT NULL,
    currency_code          STRING NOT NULL,
    counterparty_iban      STRING,
    merchant_name          STRING,
    merchant_category      STRING,
    remittance_info        STRING,
    payment_scheme         STRING,
    channel_code           STRING,
    source_system          STRING NOT NULL,
    record_hash            STRING NOT NULL,
    ingestion_timestamp    TIMESTAMP NOT NULL,
    CONSTRAINT chk_direction CHECK (direction IN ('DEBIT', 'CREDIT')),
    CONSTRAINT chk_amount CHECK (amount >= 0),
    CONSTRAINT chk_transaction_type CHECK (transaction_type IN (
        'CREDIT_TRANSFER', 'DIRECT_DEBIT', 'CARD_PURCHASE', 'CASH_WITHDRAWAL',
        'FEE', 'INTEREST', 'SALARY', 'GOVERNMENT_BENEFIT', 'REFUND', 'REVERSAL'
    ))
) USING DELTA
PARTITIONED BY (transaction_date)
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');
```

### silver.product (FIBO: FinancialProduct)

```sql
CREATE TABLE IF NOT EXISTS silver.product (
    product_id             STRING NOT NULL,
    product_code           STRING NOT NULL,
    product_name           STRING NOT NULL,
    product_type           STRING NOT NULL,
    currency_code          STRING,
    interest_rate_type     STRING,
    overdraft_allowed      BOOLEAN,
    active_from            DATE,
    active_to              DATE,
    source_system          STRING NOT NULL,
    record_hash            STRING NOT NULL,
    ingestion_timestamp    TIMESTAMP NOT NULL,
    CONSTRAINT chk_product_type CHECK (product_type IN (
        'CHECKING_ACCOUNT', 'SAVINGS_ACCOUNT', 'TERM_DEPOSIT', 'CREDIT_CARD', 'PERSONAL_LOAN', 'MORTGAGE'
    ))
) USING DELTA;
```

## Design Decisions

1. **Separate `direction` from non-negative `amount`** — explicit accounting sign convention. A debit of €42.18 is stored as `direction = 'DEBIT', amount = 42.18`, not `amount = -42.18`.
2. **Account type maps to FIBO class hierarchy** — PAYMENT → TransactionDepositAccount, SAVINGS → NonTransactionDepositAccount. The type is a dimension value, not a separate table.
3. **Bridge table for account-holder relationship** — preserves joint ownership and multiple roles. Don't put `customer_id` directly on `silver.account`.
4. **`payment_scheme` on transactions** — captures SEPA scheme (SCT, SCT_INST, SDD_CORE) for Dutch banking, ACH/WIRE for US, BACS/CHAPS/FPS for UK.
5. **No clear-text account numbers in analytical tables** — use hashed identifiers. Clear text only in Lakebase (Postgres) for the app layer.

## What NOT to Do

1. **Don't create one table per OWL class** — produces a fragmented schema with poor analytics performance
2. **Don't use a universal entity table** (`entity_id, entity_type, attribute_name, attribute_value`) — loses typing, constraints, and financial precision
3. **Don't use DOUBLE for money** — use `DECIMAL(20,4)`
4. **Don't put all relationships into JSON** — use bridge tables for important relationships
5. **Don't rename columns every time the ontology terminology changes** — maintain a semantic mapping layer and aliases

## Sources

- FIBO Ontology: https://spec.edmcouncil.org/fibo/
- FIBO GitHub: https://github.com/edmcouncil/fibo
- FIB-DM Entity List: https://fib-dm.com/
- Delta Lake Constraints: https://docs.delta.io/2.4.0/delta-constraints.html
- Delta Lake CDF: https://docs.delta.io/delta-change-data-feed/
