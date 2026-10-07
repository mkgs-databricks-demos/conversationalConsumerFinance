# L200-C4 v2: FIBO-Aligned Silver Model — Full Phase 1

> **Status:** Draft v2 — Oct 7, 2026**Author:** Matthew Giglia**Parent:** L100 — Conversational Consumer Finance: System Overview**Component:** C4 — FIBO-Aligned Silver Model (Layer 2: Data Platform)**Priority:** P0**Bundle:** Bundle 1 (Infrastructure — all environments)**Supersedes:** L200-C4 v1 (6 tables — retail consumer only)

## Overview

The FIBO-Aligned Silver Model defines the **canonical relational schema** for the full-spectrum banking data generator. This v2 expands from 6 tables to **14 Phase 1 tables** based on the FIBO 2025 Q4 gap analysis, adding a proper party model (person/organization split), addresses, contacts, identifiers, KYC, account identifiers, account statements, and expanded transaction/product columns.

The schema is designed for **all 5 phases** — Phase 1 creates all 14 tables; Phases 2–5 add 18 more (see L200-C17). Tables for future phases are listed here for completeness but are only populated when their phase is activated.

### What Changed from v1

| Change | v1 | v2 | Why |
| --- | --- | --- | --- |
| `silver.customer` | Monolithic party table | Split into `party` (supertype) + `person` + `organization` (subtypes) | FIBO models Party → Person/Organization as a class hierarchy |
| `silver.account_holder` | Simple bridge table | Expanded to `party_relationship` covering all relationship types | FIBO has AccountHolder, BeneficialOwner, AuthorizedSigner, Guarantor |
| Account identifiers | `account_id` only | New `account_identifier` table | FIBO explicitly separates AccountIdentifier (IBAN, sort code, routing) from Account |
| Account statements | Missing | New `account_statement` table | FIBO defines AccountStatement with starting/ending balance and transaction references |
| Addresses | Missing (PII in Lakebase only) | New `party_address` table | FIBO defines PhysicalAddress with hasMailingAddress — needed for the generator even if hashed in analytics |
| Contacts | Missing | New `party_contact` table | FIBO defines ElectronicMailAddress and TelephoneNumber as VirtualAddress |
| Party identifiers | Missing | New `party_identifier` table | FIBO defines Identifier with type (TAX\_ID, BSN, SSN, LEI) |
| KYC | Implicit in account SM | New `party_kyc` table | KYC/AML verification is a first-class event in the party lifecycle |
| Transaction status | Open question Q18 | Added `transaction_status` column | Resolves Q18 — append-only with explicit status per event |
| Product credit columns | Missing | Added `credit_limit`, `min_payment_pct`, `annual_fee`, `grace_period_days` | FIBO `hasCreditLimit` moved to FBC in 2025 — applies to cards and credit lines |
| Balance types | 4 types | 6 types (added PENDING, OVERDRAFT) | More complete FIBO Balance coverage |

## Phase 1 Silver Table Inventory (14 tables)

### Tier 1: Party &amp; Relationship (8 tables)

| Table | FIBO Concept | Grain | SCD2? |
| --- | --- | --- | --- |
| `silver.party` | cmns-pts\:Party | One row per party per version | Yes |
| `silver.person` | cmns-pts\:Person | One row per person (1:1 with party) | No (immutable demographics) |
| `silver.organization` | fibo-be-le-fbo\:FormalOrganization | One row per org (1:1 with party) | No (Phase 3 populates) |
| `silver.party_address` | fibo-fnd-plc-adr\:PhysicalAddress | One row per address per version | Yes |
| `silver.party_contact` | fibo-fnd-plc-vrt\:VirtualAddress | One row per contact method | No (append + soft delete) |
| `silver.party_identifier` | cmns-id\:Identifier | One row per identifier | No (append + expiry) |
| `silver.party_relationship` | fibo-fbc-pas-caa\:AccountHolder | One row per relationship per version | Yes |
| `silver.party_kyc` | Extension (AML/KYC) | One row per KYC event | No (append-only) |

### Tier 2: Accounts &amp; Deposits (6 tables)

| Table | FIBO Concept | Grain | SCD2? |
| --- | --- | --- | --- |
| `silver.account` | fibo-fbc-pas-caa\:CustomerAccount | One row per account per version | Yes |
| `silver.account_identifier` | fibo-fbc-pas-caa\:AccountIdentifier | One row per identifier | No (reference) |
| `silver.account_balance` | fibo-fbc-pas-caa\:Balance | One row per account per day per type | No (daily snapshot) |
| `silver.account_transaction` | fibo-fbc-pas-caa\:IndividualTransaction | One row per transaction event | No (append-only) |
| `silver.account_statement` | fibo-fbc-pas-caa\:AccountStatement | One row per statement period | No (append-only) |
| `silver.product` | fibo-fbc-pas-fpas\:FinancialProduct | One row per product | No (reference) |

## Table DDL

All Silver tables share these properties:

`CLUSTER BY AUTO`\
`TBLPROPERTIES (`\
`    'delta.enableChangeDataFeed' = 'true',`\
`    'delta.enableRowTracking' = 'true',`\
`    'quality' = 'silver',`\
`    'domain' = 'banking',`\
`    'data_classification' = 'confidential',`\
`    'synthetic' = 'true'`\
`)`

### silver.party

`CREATE TABLE IF NOT EXISTS ${catalog}.silver.party (`\
`    party_id               STRING       NOT NULL  COMMENT 'Unique party identifier',`\
`    party_type             STRING       NOT NULL  COMMENT 'PERSON or ORGANIZATION',`\
`    legal_name             STRING                 COMMENT 'Full legal name',`\
`    party_status           STRING       NOT NULL  COMMENT 'PROSPECT, ACTIVE, SUSPENDED, CLOSED',`\
`    customer_segment       STRING                 COMMENT 'STANDARD, PREMIUM, PRIVATE',`\
`    onboarding_date        DATE                   COMMENT 'Date KYC passed and party became active',`\
`    closure_date           DATE                   COMMENT 'Date party relationship closed',`\
`    source_system          STRING       NOT NULL,`\
`    record_hash            STRING       NOT NULL,`\
`    valid_from             TIMESTAMP    NOT NULL,`\
`    valid_to               TIMESTAMP,`\
`    is_current             BOOLEAN      NOT NULL,`\
`    ingestion_timestamp    TIMESTAMP    NOT NULL,`\
`    CONSTRAINT chk_party_type CHECK (party_type IN ('PERSON', 'ORGANIZATION')),`\
`    CONSTRAINT chk_party_status CHECK (party_status IN ('PROSPECT', 'ACTIVE', 'SUSPENDED', 'CLOSED'))`\
`) USING DELTA;`

### silver.person

`CREATE TABLE IF NOT EXISTS ${catalog}.silver.person (`\
`    party_id               STRING       NOT NULL  COMMENT 'FK to silver.party',`\
`    first_name             STRING                 COMMENT 'Given name',`\
`    last_name              STRING                 COMMENT 'Family name',`\
`    date_of_birth          DATE                   COMMENT 'Date of birth',`\
`    nationality            STRING                 COMMENT 'ISO-3166-1 alpha-2 country code',`\
`    gender                 STRING                 COMMENT 'M, F, X, UNDISCLOSED',`\
`    tax_id_hash            STRING                 COMMENT 'Hashed tax ID (BSN/SSN/NIN) — PII',`\
`    source_system          STRING       NOT NULL,`\
`    ingestion_timestamp    TIMESTAMP    NOT NULL`\
`) USING DELTA;`

**Tags:** `pii:true`

### silver.organization

`CREATE TABLE IF NOT EXISTS ${catalog}.silver.organization (`\
`    party_id               STRING       NOT NULL  COMMENT 'FK to silver.party',`\
`    legal_form             STRING                 COMMENT 'BV, NV, GmbH, Ltd, LLC, Corp',`\
`    registration_number    STRING                 COMMENT 'KVK / Companies House / EIN',`\
`    industry_code          STRING                 COMMENT 'SBI/SIC/NAICS code',`\
`    incorporation_date     DATE                   COMMENT 'Date of incorporation',`\
`    incorporation_country  STRING                 COMMENT 'ISO-3166-1 alpha-2',`\
`    employee_count_range   STRING                 COMMENT '1-10, 11-50, 51-250, 250+',`\
`    annual_revenue_range   STRING                 COMMENT 'Revenue band for segmentation',`\
`    source_system          STRING       NOT NULL,`\
`    ingestion_timestamp    TIMESTAMP    NOT NULL`\
`) USING DELTA;`

**Note:** Schema created in Phase 1; populated in Phase 3 when SM-2 (Business Party) is activated.

### silver.party\_address

`CREATE TABLE IF NOT EXISTS ${catalog}.silver.party_address (`\
`    address_id             STRING       NOT NULL  COMMENT 'Unique address record ID',`\
`    party_id               STRING       NOT NULL  COMMENT 'FK to silver.party',`\
`    address_type           STRING       NOT NULL  COMMENT 'MAILING, RESIDENTIAL, LEGAL, STATEMENT',`\
`    address_line_1         STRING                 COMMENT 'Street address',`\
`    address_line_2         STRING                 COMMENT 'Apt/suite/unit',`\
`    city                   STRING                 COMMENT 'City name',`\
`    state_province         STRING                 COMMENT 'State/province/region',`\
`    postal_code            STRING                 COMMENT 'ZIP/postal code',`\
`    country_code           STRING       NOT NULL  COMMENT 'ISO-3166-1 alpha-2',`\
`    is_primary             BOOLEAN      NOT NULL,`\
`    valid_from             TIMESTAMP    NOT NULL,`\
`    valid_to               TIMESTAMP,`\
`    is_current             BOOLEAN      NOT NULL,`\
`    source_system          STRING       NOT NULL,`\
`    ingestion_timestamp    TIMESTAMP    NOT NULL`\
`) USING DELTA;`

**Tags:** `pii:true`

### silver.party\_contact

`CREATE TABLE IF NOT EXISTS ${catalog}.silver.party_contact (`\
`    contact_id             STRING       NOT NULL  COMMENT 'Unique contact record ID',`\
`    party_id               STRING       NOT NULL  COMMENT 'FK to silver.party',`\
`    contact_type           STRING       NOT NULL  COMMENT 'EMAIL, MOBILE, LANDLINE, FAX',`\
`    contact_value          STRING       NOT NULL  COMMENT 'Email address or phone number',`\
`    is_primary             BOOLEAN      NOT NULL,`\
`    is_verified            BOOLEAN      NOT NULL,`\
`    source_system          STRING       NOT NULL,`\
`    ingestion_timestamp    TIMESTAMP    NOT NULL,`\
`    CONSTRAINT chk_contact_type CHECK (contact_type IN ('EMAIL', 'MOBILE', 'LANDLINE', 'FAX'))`\
`) USING DELTA;`

**Tags:** `pii:true`

### silver.party\_identifier

`CREATE TABLE IF NOT EXISTS ${catalog}.silver.party_identifier (`\
`    identifier_id          STRING       NOT NULL  COMMENT 'Unique identifier record ID',`\
`    party_id               STRING       NOT NULL  COMMENT 'FK to silver.party',`\
`    identifier_type        STRING       NOT NULL  COMMENT 'TAX_ID, BSN, SSN, NIN, KVK, LEI, PASSPORT',`\
`    identifier_value_hash  STRING       NOT NULL  COMMENT 'Hashed identifier value — PII',`\
`    issuing_country        STRING                 COMMENT 'ISO-3166-1 alpha-2',`\
`    valid_from             DATE                   COMMENT 'ID validity start',`\
`    valid_to               DATE                   COMMENT 'ID validity end (NULL = no expiry)',`\
`    source_system          STRING       NOT NULL,`\
`    ingestion_timestamp    TIMESTAMP    NOT NULL`\
`) USING DELTA;`

**Tags:** `pii:true`

### silver.party\_relationship

`CREATE TABLE IF NOT EXISTS ${catalog}.silver.party_relationship (`\
`    relationship_id        STRING       NOT NULL  COMMENT 'Unique relationship record ID',`\
`    party_id               STRING       NOT NULL  COMMENT 'FK to silver.party (the holder/signer)',`\
`    related_entity_type    STRING       NOT NULL  COMMENT 'ACCOUNT, PARTY, LOAN, FACILITY',`\
`    related_entity_id      STRING       NOT NULL  COMMENT 'FK to the related entity',`\
`    relationship_type      STRING       NOT NULL  COMMENT 'PRIMARY, JOINT, AUTHORIZED_SIGNER, BENEFICIAL_OWNER, GUARANTOR',`\
`    valid_from             TIMESTAMP    NOT NULL,`\
`    valid_to               TIMESTAMP,`\
`    is_current             BOOLEAN      NOT NULL,`\
`    source_system          STRING       NOT NULL,`\
`    record_hash            STRING       NOT NULL,`\
`    ingestion_timestamp    TIMESTAMP    NOT NULL,`\
`    CONSTRAINT chk_rel_type CHECK (relationship_type IN (`\
`        'PRIMARY', 'JOINT', 'AUTHORIZED_SIGNER', 'BENEFICIAL_OWNER', 'GUARANTOR', 'AUTHORIZED_USER'`\
`    ))`\
`) USING DELTA;`

### silver.party\_kyc

`CREATE TABLE IF NOT EXISTS ${catalog}.silver.party_kyc (`\
`    kyc_event_id           STRING       NOT NULL  COMMENT 'Unique KYC event ID',`\
`    party_id               STRING       NOT NULL  COMMENT 'FK to silver.party',`\
`    kyc_status             STRING       NOT NULL  COMMENT 'PENDING, PASSED, FAILED, EXPIRED, ENHANCED',`\
`    verification_date      DATE         NOT NULL  COMMENT 'Date of verification',`\
`    risk_score             STRING                 COMMENT 'LOW, MEDIUM, HIGH',`\
`    pep_flag               BOOLEAN                COMMENT 'Politically Exposed Person flag',`\
`    next_review_date       DATE                   COMMENT 'Next periodic review date',`\
`    source_system          STRING       NOT NULL,`\
`    ingestion_timestamp    TIMESTAMP    NOT NULL`\
`) USING DELTA;`

### silver.account

`CREATE TABLE IF NOT EXISTS ${catalog}.silver.account (`\
`    account_id             STRING       NOT NULL  COMMENT 'Unique account identifier',`\
`    account_type           STRING       NOT NULL  COMMENT 'PAYMENT, SAVINGS, TERM_DEPOSIT, CREDIT_CARD, OPERATING, PAYROLL, ESCROW',`\
`    product_id             STRING       NOT NULL  COMMENT 'FK to silver.product',`\
`    account_status         STRING       NOT NULL  COMMENT 'PENDING, OPEN, DORMANT, BLOCKED, CLOSED',`\
`    currency_code          STRING       NOT NULL  COMMENT 'ISO-4217 currency code',`\
`    opened_date            DATE         NOT NULL  COMMENT 'Date account opened',`\
`    closed_date            DATE                   COMMENT 'Date account closed (NULL = open)',`\
`    source_system          STRING       NOT NULL,`\
`    record_hash            STRING       NOT NULL,`\
`    valid_from             TIMESTAMP    NOT NULL,`\
`    valid_to               TIMESTAMP,`\
`    is_current             BOOLEAN      NOT NULL,`\
`    ingestion_timestamp    TIMESTAMP    NOT NULL,`\
`    CONSTRAINT chk_account_type CHECK (account_type IN (`\
`        'PAYMENT', 'SAVINGS', 'TERM_DEPOSIT', 'CREDIT_CARD',`\
`        'OPERATING', 'PAYROLL', 'ESCROW'`\
`    )),`\
`    CONSTRAINT chk_account_status CHECK (account_status IN ('PENDING', 'OPEN', 'DORMANT', 'BLOCKED', 'CLOSED'))`\
`) USING DELTA;`

### silver.account\_identifier

`CREATE TABLE IF NOT EXISTS ${catalog}.silver.account_identifier (`\
`    account_identifier_id  STRING       NOT NULL  COMMENT 'Unique identifier record ID',`\
`    account_id             STRING       NOT NULL  COMMENT 'FK to silver.account',`\
`    identifier_type        STRING       NOT NULL  COMMENT 'IBAN, BBAN, SORT_CODE_ACCOUNT, ROUTING_ACCOUNT, INTERNAL',`\
`    identifier_value       STRING       NOT NULL  COMMENT 'The actual identifier value',`\
`    is_primary             BOOLEAN      NOT NULL  COMMENT 'Primary identifier flag',`\
`    source_system          STRING       NOT NULL,`\
`    ingestion_timestamp    TIMESTAMP    NOT NULL`\
`) USING DELTA;`

### silver.account\_balance

`CREATE TABLE IF NOT EXISTS ${catalog}.silver.account_balance (`\
`    account_id             STRING       NOT NULL  COMMENT 'FK to silver.account',`\
`    balance_date           DATE         NOT NULL  COMMENT 'Date of balance snapshot',`\
`    balance_type           STRING       NOT NULL  COMMENT 'LEDGER, AVAILABLE, COLLECTED, CURRENT, PENDING, OVERDRAFT',`\
`    amount                 DECIMAL(20,4) NOT NULL COMMENT 'Balance amount in account currency',`\
`    currency_code          STRING       NOT NULL  COMMENT 'ISO-4217',`\
`    source_system          STRING       NOT NULL,`\
`    record_hash            STRING       NOT NULL,`\
`    ingestion_timestamp    TIMESTAMP    NOT NULL,`\
`    CONSTRAINT chk_balance_type CHECK (balance_type IN (`\
`        'LEDGER', 'AVAILABLE', 'COLLECTED', 'CURRENT', 'PENDING', 'OVERDRAFT'`\
`    ))`\
`) USING DELTA`\
`PARTITIONED BY (balance_date);`

### silver.account\_transaction

`CREATE TABLE IF NOT EXISTS ${catalog}.silver.account_transaction (`\
`    transaction_id         STRING       NOT NULL  COMMENT 'Unique transaction identifier',`\
`    account_id             STRING       NOT NULL  COMMENT 'FK to silver.account',`\
`    transaction_date       DATE         NOT NULL  COMMENT 'Date transaction occurred',`\
`    posting_date           DATE                   COMMENT 'Date posted to ledger',`\
`    value_date             DATE                   COMMENT 'Interest calculation date',`\
`    settlement_date        DATE                   COMMENT 'Settlement/clearing date',`\
`    transaction_type       STRING       NOT NULL  COMMENT 'CREDIT_TRANSFER, DIRECT_DEBIT, CARD_PURCHASE, etc.',`\
`    transaction_status     STRING       NOT NULL  COMMENT 'AUTHORIZED, POSTED, RECONCILED, REVERSED, DISPUTED',`\
`    direction              STRING       NOT NULL  COMMENT 'DEBIT or CREDIT',`\
`    amount                 DECIMAL(20,4) NOT NULL COMMENT 'Transaction amount (always non-negative)',`\
`    currency_code          STRING       NOT NULL  COMMENT 'ISO-4217',`\
`    counterparty_iban      STRING                 COMMENT 'Counterparty IBAN',`\
`    merchant_name          STRING                 COMMENT 'Merchant or counterparty name',`\
`    merchant_category      STRING                 COMMENT 'Merchant category',`\
`    remittance_info        STRING                 COMMENT 'Payment reference',`\
`    payment_scheme         STRING                 COMMENT 'SCT, SDD_CORE, ACH, FPS, etc.',`\
`    channel_code           STRING                 COMMENT 'MOBILE, ONLINE, ATM, POS, BRANCH',`\
`    authorization_code     STRING                 COMMENT 'Card authorization code',`\
`    source_system          STRING       NOT NULL,`\
`    record_hash            STRING       NOT NULL,`\
`    ingestion_timestamp    TIMESTAMP    NOT NULL,`\
`    CONSTRAINT chk_direction CHECK (direction IN ('DEBIT', 'CREDIT')),`\
`    CONSTRAINT chk_amount CHECK (amount >= 0),`\
`    CONSTRAINT chk_txn_status CHECK (transaction_status IN (`\
`        'AUTHORIZED', 'PENDING_SETTLEMENT', 'POSTED', 'RECONCILED',`\
`        'REVERSED', 'DISPUTED', 'REFUNDED', 'DECLINED'`\
`    ))`\
`) USING DELTA`\
`PARTITIONED BY (transaction_date);`

### silver.account\_statement

`CREATE TABLE IF NOT EXISTS ${catalog}.silver.account_statement (`\
`    statement_id           STRING       NOT NULL  COMMENT 'Unique statement ID',`\
`    account_id             STRING       NOT NULL  COMMENT 'FK to silver.account',`\
`    period_start           DATE         NOT NULL  COMMENT 'Statement period start',`\
`    period_end             DATE         NOT NULL  COMMENT 'Statement period end',`\
`    statement_date         DATE         NOT NULL  COMMENT 'Date statement generated',`\
`    opening_balance        DECIMAL(20,4) NOT NULL COMMENT 'Opening balance for period',`\
`    closing_balance        DECIMAL(20,4) NOT NULL COMMENT 'Closing balance for period',`\
`    total_debits           DECIMAL(20,4)          COMMENT 'Sum of debits in period',`\
`    total_credits          DECIMAL(20,4)          COMMENT 'Sum of credits in period',`\
`    transaction_count      INT                    COMMENT 'Number of transactions in period',`\
`    currency_code          STRING       NOT NULL  COMMENT 'ISO-4217',`\
`    source_system          STRING       NOT NULL,`\
`    ingestion_timestamp    TIMESTAMP    NOT NULL`\
`) USING DELTA;`

### silver.product

`CREATE TABLE IF NOT EXISTS ${catalog}.silver.product (`\
`    product_id             STRING       NOT NULL  COMMENT 'Unique product identifier',`\
`    product_code           STRING       NOT NULL  COMMENT 'Short product code',`\
`    product_name           STRING       NOT NULL  COMMENT 'Display name (locale-specific)',`\
`    product_type           STRING       NOT NULL  COMMENT 'CHECKING_ACCOUNT, SAVINGS_ACCOUNT, TERM_DEPOSIT, CREDIT_CARD, PERSONAL_LOAN, MORTGAGE',`\
`    currency_code          STRING                 COMMENT 'Default currency',`\
`    interest_rate_type     STRING                 COMMENT 'FIXED, VARIABLE, TIERED',`\
`    overdraft_allowed      BOOLEAN                COMMENT 'Whether overdraft is permitted',`\
`    credit_limit           DECIMAL(20,4)          COMMENT 'Credit limit (cards/credit lines)',`\
`    min_payment_pct        DECIMAL(5,2)           COMMENT 'Minimum payment percentage',`\
`    annual_fee             DECIMAL(20,4)          COMMENT 'Annual card/account fee',`\
`    grace_period_days      INT                    COMMENT 'Interest-free grace period in days',`\
`    active_from            DATE                   COMMENT 'Product availability start',`\
`    active_to              DATE                   COMMENT 'Product availability end (NULL = active)',`\
`    source_system          STRING       NOT NULL,`\
`    record_hash            STRING       NOT NULL,`\
`    ingestion_timestamp    TIMESTAMP    NOT NULL,`\
`    CONSTRAINT chk_product_type CHECK (product_type IN (`\
`        'CHECKING_ACCOUNT', 'SAVINGS_ACCOUNT', 'TERM_DEPOSIT',`\
`        'CREDIT_CARD', 'PERSONAL_LOAN', 'MORTGAGE'`\
`    ))`\
`) USING DELTA;`

## Future Phase Tables (schema created in Phase 1, populated later)

These tables are created empty in Phase 1 so the SDP pipeline schema is complete. They are populated when their phase is activated via the `phase` variable in Bundle 2.

| Table | Phase | Populated By |
| --- | --- | --- |
| `silver.organization` | Phase 3 | SM-2 (Business Party) |
| `silver.loan` | Phase 2 | SM-6 (Consumer Loan) |
| `silver.loan_payment` | Phase 2 | SM-6 |
| `silver.loan_event` | Phase 2 | SM-6 |
| `silver.mortgage` | Phase 2 | SM-7 (Mortgage) |
| `silver.mortgage_property` | Phase 2 | SM-7 |
| `silver.credit_card` | Phase 2 | SM-8 (Credit Card) |
| `silver.credit_card_statement` | Phase 2 | SM-8 |
| `silver.commercial_facility` | Phase 3 | SM-9 (Commercial Loan) |
| `silver.investment_account` | Phase 4 | SM-10 (Investment Account) |
| `silver.security` | Phase 4 | SM-11 (Securities) |
| `silver.holding` | Phase 4 | SM-11 |
| `silver.trade` | Phase 4 | SM-11 |
| `silver.corporate_action` | Phase 4 | SM-11 |
| `silver.market_data_daily` | Phase 4 | Reference data feed |
| `silver.gl_journal_entry` | Phase 5 | SM-12 (GL) |
| `silver.gl_account` | Phase 5 | Reference data |
| `silver.regulatory_report` | Phase 5 | SM-12 |
| `silver.interest_rate_reference` | Phase 5 | Reference data feed |

**Total: 14 Phase 1 tables + 18 future phase tables = 32 Silver tables created in Phase 1 (18 empty).**

## SCD2 Implementation

Same pattern as v1 — record hash comparison for dimension tables:

| Table | SCD2? | Hash Input Columns |
| --- | --- | --- |
| `party` | Yes | party\_id, party\_type, legal\_name, party\_status, customer\_segment, onboarding\_date, closure\_date |
| `party_address` | Yes | party\_id, address\_type, address\_line\_1, address\_line\_2, city, state\_province, postal\_code, country\_code, is\_primary |
| `party_relationship` | Yes | party\_id, related\_entity\_type, related\_entity\_id, relationship\_type |
| `account` | Yes | account\_id, account\_type, product\_id, account\_status, currency\_code, opened\_date, closed\_date |

All other tables are append-only, daily snapshot, or reference data — no SCD2 needed.

## Governance Metadata

| Tag | Values | Purpose |
| --- | --- | --- |
| `domain` | `banking` (renamed from `consumer_banking`) | UC Domain |
| `subdomain` | `parties`, `addresses`, `contacts`, `identifiers`, `kyc`, `accounts`, `balances`, `transactions`, `statements`, `products` | UC Subdomain |
| `fibo_concept` | FIBO class name | Traceability to ontology |
| `quality` | `silver` | Medallion layer |
| `data_classification` | `confidential` | Data sensitivity |
| `pii` | `true` / `false` | PII flag (true for person, party\_address, party\_contact, party\_identifier) |
| `synthetic` | `true` / `false` | Generator vs. real data |
| `phase` | `1` through `5` | Which phase populates this table |

## Non-Functional Requirements

Same as v1 plus:

| NFR | Target | Rationale |
| --- | --- | --- |
| **Phase 1 completeness** | All 14 Phase 1 tables populated by the generator | Consumer-facing queries work end-to-end |
| **Future phase readiness** | All 32 table schemas created (18 empty) | No DDL changes needed when a phase is activated |
| **Party model integrity** | Every party has exactly one person OR organization subtype record | Supertype/subtype invariant |
| **Relationship integrity** | Every account has at least one PRIMARY relationship | Account-holder invariant |

## Testing

All v1 tests plus:

| Test | What It Validates |
| --- | --- |
| **Party supertype/subtype** | Every party\_id in silver.person exists in silver.party with party\_type = 'PERSON' |
| **Address completeness** | Every active party has at least one address with is\_primary = TRUE |
| **Identifier completeness** | Every active party has at least one identifier |
| **KYC lifecycle** | Every ACTIVE party has a PASSED KYC event |
| **Account identifier** | Every account has at least one identifier with is\_primary = TRUE |
| **Statement generation** | Monthly statements generated for all active accounts |
| **Transaction status** | Every transaction has a valid status from the SM-5 lifecycle |
| **Future phase tables empty** | Phase 2–5 tables exist but have 0 rows in Phase 1 |

## Deployment

Same as v1 — Bundle 1 (Infrastructure). All 32 table schemas created by the SDP pipeline. Phase 1 populates 14; Phases 2–5 populate the remaining 18.

## Open Questions

| # | Question | Impact | Resolution Path |
| --- | --- | --- | --- |
| ~~Q18~~ | ~~Transaction status column~~ | **Resolved** | Added `transaction_status` column. Append-only with explicit status per event. |
| ~~Q19~~ | ~~Partitioning vs. clustering~~ | **Resolved** | `account_balance` and `account_transaction` partitioned by date; all others CLUSTER BY AUTO. |
| Q39 | Should PII tables (person, party\_address, party\_contact, party\_identifier) be in a separate schema (`silver_pii`) with tighter access controls? | Security | Defer to POC — single `silver` schema for simplicity; split if access control requirements demand it. |
| Q40 | Should `silver.organization` be created empty in Phase 1, or deferred entirely to Phase 3? | Schema management | Current design: create empty. This avoids DDL changes when Phase 3 activates. |

## References

- **L200-C4 v1** — Original 6-table design (notebooks/308703764885515)
- **Research 02** — FIBO-to-Relational Mapping (notebooks/308703764881119)
- **Research 07** — Full-Spectrum FIBO Generator (notebooks/308703765046744)
- **Semantics 02** — 108 glossary terms (notebooks/308703765065096)
- **FIBO-to-Silver HTML Mapping** — Interactive visualization (fibo\_silver\_model\_mapping.html)
- FIBO 2025 Q4: spec.edmcouncil.org/fibo
