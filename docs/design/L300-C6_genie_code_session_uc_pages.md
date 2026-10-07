# L300-C6: Genie Code Session — UC Pages

> **Status:** Draft v1 — Oct 7, 2026
> **Author:** Matthew Giglia
> **Parent:** L200-C6 v2 — UC Pages per Locale (canvas notebooks/308703764929921)
> **Methodology:** Rapid Ontology Standup — L200-C: Domain, Subdomain & Pages Standup
> **Session Type:** Interactive Genie Code session in DAB repo
> **Estimated Duration:** 2–3 hours (60 Phase 1 pages × ~2 min each + review cycles)

## Session Goal

Create **60 Phase 1 UC Pages** in Unity Catalog — the business term definitions that Genie Agents use to understand consumer banking terminology. Pages are authored in the locale language and organized by subdomain.

### Phase 1 Page Inventory (from Semantics 02)

| Subdomain | Phase 1 Terms | Priority High | Priority Medium |
|---|---|---|---|
| **Account Management** | 12 | 5 (Balance, Payment Account, Savings Account, Account Holder, IBAN) | 7 |
| **Transaction Processing** | 10 | 5 (Credit Transfer, Direct Debit, Monthly Spending, Category, Posting Date) | 5 |
| **Payment Schemes** | 6 | 6 (SCT, SCT Inst, SDD Core, ACH, WIRE, FPS) | 0 |
| **Product Portfolio** | 8 | 3 (Eligibility, Credit Card, Term Deposit) | 5 |
| **Customer Behavior** | 6 | 2 (Spending Trend, Anomaly Detection) | 4 |
| **Security & Compliance** | 6 | 3 (Consumer GUID, Consent, Session Token) | 3 |
| **Party Model** | 4 | 2 (Individual, Organization) | 2 |
| **Identifiers** | 4 | 2 (IBAN, BIC) | 2 |
| **Statements** | 4 | 2 (Account Statement, Statement Period) | 2 |
| **Total** | **60** | **30** | **30** |

**Note:** Semantics 02 has 108 total terms across all phases. Phase 1 covers 60 terms; the remaining 48 are Phase 2–5 terms that will be created in future L300 sessions.

## Input Context

### L200 Design References
- **L200-C6 v2** (canvas notebooks/308703764929921) — UC Pages design with page structure template, certification workflow, and Genie Agent integration
- **Semantics 02** (canvas notebooks/308703765065096) — 108 glossary terms, 12 subdomains, with FIBO source mappings
- **L200-C1** (canvas notebooks/308703764929903) — Locale Config Engine (language codes)

### Page Structure Template (from L200-C6 v2)

Each UC Page follows this structure, authored in the locale language:

```markdown
# {Term in locale language}

## Definition
{One-paragraph definition in locale language}

## Business Context
{How this term is used in consumer banking}

## Data Usage
- **Table:** {silver.table_name.column_name}
- **Metric View Measure/Dimension:** {gold.metric_view.field_name}
- **Values:** {enumerated values if applicable}

## Related Terms
- {Related term 1}
- {Related term 2}

## FIBO Source
- **Concept:** {FIBO class name}
- **Module:** {FIBO module}
```

### Domain and Subdomain Structure

**Domain:** Consumer Banking
**Subdomains (12):**
1. Account Management
2. Transaction Processing
3. Payment Schemes
4. Product Portfolio
5. Customer Behavior
6. Security & Compliance
7. Party Model
8. Identifiers
9. Statements
10. Credit Products
11. Interest & Fees
12. Regulatory Compliance

## Session Script

### Pre-Session Setup (5 min)

```bash
cd /Workspace/Repos/<user>/conversationalConsumerFinance
git checkout -b feature/uc-pages-phase1
```

### Phase 1: Create Domain and Subdomains (10 min)

**Genie Code Prompt 1 — Create the UC Domain:**
> "Create a Unity Catalog Domain called 'Consumer Banking' with the description: 'Business concepts, metrics, and terminology for consumer-facing retail banking applications. Covers account management, transactions, payments, products, customer behavior, and security. FIBO-aligned definitions with multi-locale support (EN, EN-GB, NL).'
>
> Then create 12 Subdomains under it:
> 1. Account Management — 'Account types, balances, statuses, and lifecycle management'
> 2. Transaction Processing — 'Transaction types, posting, settlement, and categorization'
> 3. Payment Schemes — 'Payment rails and settlement protocols (SEPA, ACH, FPS)'
> 4. Product Portfolio — 'Banking products, eligibility, and product lifecycle'
> 5. Customer Behavior — 'Spending patterns, trends, and behavioral analytics'
> 6. Security & Compliance — 'Authentication, authorization, consent, and audit'
> 7. Party Model — 'Customer and organization entity types and relationships'
> 8. Identifiers — 'Account and routing identifiers (IBAN, BIC, routing numbers)'
> 9. Statements — 'Account statements, periods, and reporting'
> 10. Credit Products — 'Credit cards, loans, credit limits, and utilization'
> 11. Interest & Fees — 'Interest rates, fee structures, and accrual methods'
> 12. Regulatory Compliance — 'KYC, AML, PSD2, and regulatory reporting'"

### Phase 2: Create High-Priority Pages — Account Management (15 min)

**Genie Code Prompt 2 — Account Management pages (batch):**
> "Create UC Pages for the Account Management subdomain. For each term, I'll give you the definition, business context, data usage, related terms, and FIBO source. Create all pages in English (US locale).
>
> **Page 1: Account Balance**
> - Definition: The amount of money available in a customer's bank account at a specific point in time, calculated as the sum of all posted credits minus all posted debits.
> - Business Context: The most frequently asked question in consumer banking. Consumers check their balance multiple times daily. The 'available balance' excludes pending transactions and holds; the 'ledger balance' includes all posted transactions.
> - Data Usage: Table: `silver.account_balance.balance_amount`; Metric View: `gold.customer_transaction_metrics` → MEASURE(total_balance); Values: numeric, currency-denominated
> - Related Terms: Payment Account, Transaction, Posting Date, Available Balance, Ledger Balance
> - FIBO Source: Concept: MonetaryAmount; Module: FND/Accounting/AccountingEquity
>
> **Page 2: Payment Account**
> - Definition: A bank account held in the name of one or more customers, used for executing payment transactions including deposits, withdrawals, and transfers.
> - Business Context: The primary account type for day-to-day banking. Known as 'checking account' (US), 'current account' (UK), or 'betaalrekening' (NL). Typically linked to a debit card and online banking access.
> - Data Usage: Table: `silver.account.account_type = 'CHECKING'`; Metric View: `gold.customer_product_metrics` → field: product_type; Values: CHECKING, CURRENT_ACCOUNT
> - Related Terms: Savings Account, Account Balance, Account Holder, IBAN
> - FIBO Source: Concept: DepositAccount; Module: FBC/ProductsAndServices/ClientsAndAccounts
>
> **Page 3: Savings Account**
> - Definition: A deposit account that earns interest on the balance held, typically with limited transaction capabilities compared to a payment account.
> - Business Context: Consumers use savings accounts to accumulate funds with interest. May have withdrawal limits or notice periods. Interest rates vary by product tier and balance level.
> - Data Usage: Table: `silver.account.account_type = 'SAVINGS_ACCOUNT'`; Metric View: `gold.customer_product_metrics` → MEASURE(savings_balance); Values: SAVINGS_ACCOUNT
> - Related Terms: Payment Account, Interest Rate, Account Balance, Term Deposit
> - FIBO Source: Concept: SavingsAccount; Module: FBC/ProductsAndServices/ClientsAndAccounts
>
> **Page 4: Account Holder**
> - Definition: An individual or organization that has legal ownership of or authorized access to a bank account, identified by their role (primary holder, joint holder, or authorized user).
> - Business Context: Determines who can view and transact on the account. Joint holders have equal rights; authorized users have delegated access. The party_relationship table tracks the holder-to-account relationship.
> - Data Usage: Table: `silver.party_relationship.relationship_type`; Metric View: `gold.customer_product_metrics` → field: holder_role; Values: PRIMARY, JOINT, AUTHORIZED_USER
> - Related Terms: Individual, Organization, Consumer GUID, Party Relationship
> - FIBO Source: Concept: AccountHolder; Module: FBC/ProductsAndServices/ClientsAndAccounts
>
> **Page 5: IBAN**
> - Definition: International Bank Account Number — a standardized international numbering system for identifying bank accounts across national borders, consisting of a country code, check digits, and a basic bank account number.
> - Business Context: Used in SEPA countries (EU/EEA) for all cross-border and domestic transfers. Format: 2-letter country code + 2 check digits + up to 30 alphanumeric characters. US and UK use domestic routing numbers instead.
> - Data Usage: Table: `silver.account_identifier.identifier_type = 'IBAN'`; Values: alphanumeric, country-specific format
> - Related Terms: BIC, Payment Scheme, Credit Transfer, Account Identifier
> - FIBO Source: Concept: InternationalBankAccountNumber; Module: FBC/ProductsAndServices/ClientsAndAccounts"

**Validation checkpoint:** Verify all 5 pages created. Check that:
- [ ] Each page is assigned to the Account Management subdomain
- [ ] Definitions are clear and consumer-appropriate
- [ ] Data Usage references match the actual Silver/Gold schema
- [ ] FIBO sources are accurate

### Phase 3: Create High-Priority Pages — Transaction Processing (15 min)

**Genie Code Prompt 3 — Transaction Processing pages (batch):**
> "Create UC Pages for the Transaction Processing subdomain:
>
> **Page 6: Credit Transfer**
> - Definition: A payment initiated by the payer (debtor) to transfer funds from their account to the payee's (creditor's) account. The payer instructs their bank to move the specified amount.
> - Business Context: The most common payment type for bill payments, salary transfers, and person-to-person transfers. Settlement timing depends on the payment scheme: SCT (1 business day), SCT Inst (10 seconds), ACH (1-3 business days), FPS (near-instant).
> - Data Usage: Table: `silver.account_transaction.transaction_type = 'CREDIT_TRANSFER'`; payment_scheme indicates the rail used
> - Related Terms: Direct Debit, Payment Scheme, SCT, ACH, Posting Date
> - FIBO Source: Concept: CreditTransfer; Module: FND/PaymentsAndSchedules
>
> **Page 7: Direct Debit**
> - Definition: A payment initiated by the payee (creditor) to collect funds from the payer's (debtor's) account, authorized by a mandate (standing authorization) given by the payer.
> - Business Context: Used for recurring payments: rent, utilities, insurance, subscriptions. Under SEPA SDD Core, consumers can reverse (storno) a direct debit within 8 weeks unconditionally, or 13 months if unauthorized.
> - Data Usage: Table: `silver.account_transaction.transaction_type = 'DIRECT_DEBIT'`; payment_scheme = 'SDD_CORE'
> - Related Terms: Credit Transfer, Payment Scheme, SDD Core, Mandate
> - FIBO Source: Concept: DirectDebit; Module: FND/PaymentsAndSchedules
>
> **Page 8: Monthly Spending**
> - Definition: The total value of all debit transactions posted to a customer's accounts within a calendar month, excluding internal transfers between the customer's own accounts.
> - Business Context: A key metric for personal financial management. Consumers track monthly spending to budget and identify trends. Broken down by merchant category for spending analysis.
> - Data Usage: Metric View: `gold.customer_transaction_metrics` → MEASURE(monthly_spend); Dimension: transaction_month
> - Related Terms: Merchant Category, Transaction Count, Spending Trend, Direction
> - FIBO Source: Concept: MonetaryAmount (aggregate); Module: FND/Accounting
>
> **Page 9: Merchant Category**
> - Definition: A classification of the merchant or payee in a transaction, used to categorize spending into groups such as groceries, dining, transportation, utilities, and entertainment.
> - Business Context: Enables spending analysis and budgeting. Categories are assigned based on the merchant's MCC (Merchant Category Code) for card transactions, or inferred from payee name for transfers.
> - Data Usage: Table: `silver.account_transaction.merchant_category`; Metric View: `gold.customer_transaction_metrics` → field: merchant_category; `gold.customer_behavior_metrics` → field: merchant_category
> - Related Terms: Monthly Spending, Transaction Count, Spending Trend
> - FIBO Source: Concept: MerchantCategoryCode; Module: FBC/ProductsAndServices
>
> **Page 10: Posting Date**
> - Definition: The date on which a transaction is officially recorded (posted) to the customer's account and affects the account balance. Distinct from the transaction initiation date and the settlement date.
> - Business Context: The posting date determines when a transaction appears in the customer's statement and affects the available balance. For credit transfers, posting may be same-day (instant) or next-business-day depending on the payment scheme.
> - Data Usage: Table: `silver.account_transaction.posting_date`; Metric View: `gold.customer_transaction_metrics` → field: transaction_date
> - Related Terms: Transaction, Account Balance, Settlement, Credit Transfer
> - FIBO Source: Concept: PostingDate; Module: FND/DatesAndTimes"

### Phase 4: Continue with Remaining Subdomains (60 min)

Continue the same pattern for the remaining 8 subdomains. For each batch:

**Genie Code Prompt pattern:**
> "Create UC Pages for the {Subdomain} subdomain: [list of terms with definition, business context, data usage, related terms, FIBO source]"

**Subdomain batches:**
- Payment Schemes (6 pages): SCT, SCT Inst, SDD Core, ACH, WIRE, FPS
- Product Portfolio (8 pages): Eligibility, Credit Card, Term Deposit, Debit Card, Product Type, Product Status, Credit Limit, Credit Utilization
- Customer Behavior (6 pages): Spending Trend, Anomaly Detection, Behavioral State, Proactive Insight, Unique Merchants, Average Transaction
- Security & Compliance (6 pages): Consumer GUID, Consent State, Session Token, JWT, Rate Limiting, PII Masking
- Party Model (4 pages): Individual, Organization, Party Relationship, Party Role
- Identifiers (4 pages): IBAN, BIC, Routing Number, Account Number
- Statements (4 pages): Account Statement, Statement Period, Opening Balance, Closing Balance

### Phase 5: Locale Variants (30 min per locale)

**Genie Code Prompt — Generate NL locale pages:**
> "For each of the 60 UC Pages we just created, generate a Dutch (NL) locale variant. The Dutch page should:
> 1. Use the Dutch term as the page title (e.g., 'Saldo' instead of 'Account Balance')
> 2. Have the definition translated to Dutch
> 3. Keep the Data Usage section in English (technical references)
> 4. Translate the Business Context to Dutch
> 5. Use Dutch related term names
>
> Start with the Account Management subdomain. Here are the Dutch terms:
> - Account Balance → Saldo
> - Payment Account → Betaalrekening
> - Savings Account → Spaarrekening
> - Account Holder → Rekeninghouder
> - IBAN → IBAN (same in Dutch)
>
> Generate the Dutch pages."

**Repeat for GB locale** with British English terminology (current account, sort code, standing order, etc.).

### Phase 6: Certification (10 min)

**Genie Code Prompt — Certify high-priority pages:**
> "Mark all 30 High-priority UC Pages as 'Certified' in Unity Catalog. These are the terms that directly map to metric view measures and fields — they need to be certified for Genie OntoRank scoring to prioritize them."

## Validation

### Verification Queries

```sql
-- Count pages by subdomain
SELECT subdomain, COUNT(*) as page_count
FROM system.information_schema.catalog_tags
WHERE tag_name = 'uc_page_subdomain'
GROUP BY subdomain;

-- Verify certification status
SELECT page_name, certification_status
FROM system.information_schema.catalog_tags
WHERE tag_name = 'uc_page' AND certification_status = 'CERTIFIED';
```

### Genie Agent Integration Test

After pages are created, test that the Genie Agent can retrieve definitions:

| Question | Expected Behavior |
|---|---|
| "What is a direct debit?" | Agent retrieves the Direct Debit UC Page definition |
| "Wat is een incasso?" (NL) | NL Agent retrieves the Dutch Direct Debit page |
| "What's the difference between a credit transfer and a direct debit?" | Agent retrieves both pages and compares |
| "What payment schemes are available?" | Agent retrieves Payment Scheme pages |

### Validation Criteria

| Check | Pass Criteria |
|---|---|
| **Page count** | 60 pages created (30 High + 30 Medium priority) |
| **Subdomain assignment** | All pages assigned to correct subdomain |
| **FIBO linkage** | Every page has a FIBO Source section |
| **Data Usage accuracy** | Table/column references match actual Silver/Gold schema |
| **Locale coverage** | All 30 High-priority pages have NL and GB variants |
| **Certification** | All 30 High-priority pages marked Certified |
| **Genie discovery** | Agent can retrieve page definitions for definitional questions |

## DAB Integration

### File Outputs

```
src/semantic_layer/
├── pages/
│   ├── en/
│   │   ├── account_management/
│   │   │   ├── account_balance.md
│   │   │   ├── payment_account.md
│   │   │   ├── savings_account.md
│   │   │   ├── account_holder.md
│   │   │   └── iban.md
│   │   ├── transaction_processing/
│   │   ├── payment_schemes/
│   │   ├── product_portfolio/
│   │   ├── customer_behavior/
│   │   ├── security_compliance/
│   │   ├── party_model/
│   │   ├── identifiers/
│   │   └── statements/
│   ├── nl/
│   │   └── (same structure, Dutch content)
│   ├── en-GB/
│   │   └── (same structure, British English content)
│   └── deploy_pages.py
└── ...
```

### Commit Sequence

```bash
git add src/semantic_layer/pages/
git commit -m "feat(semantic-layer): add 60 Phase 1 UC Pages across 9 subdomains

- 30 High-priority pages (certified)
- 30 Medium-priority pages
- 3 locale variants: EN (US), EN-GB, NL
- FIBO-aligned definitions with source traceability
- Organized by subdomain under Consumer Banking domain
- 12 subdomains created

Implements L200-C6 v2 design.
Sources from Semantics 02 (108-term glossary).
Follows Rapid Ontology Standup L200-C methodology."

git push origin feature/uc-pages-phase1
```

## Open Questions

| # | Question | Impact | Resolution Path |
|---|---|---|---|
| Q-L300-4 | Can Genie Code create UC Pages via API, or only through Catalog Explorer UI? | Affects automation | Test in session; fallback: batch script using REST API |
| Q-L300-5 | Does Genie Code support batch page creation (multiple pages in one prompt)? | Affects session duration | Test with 5-page batch; if not, create individually |
| Q-L300-6 | How does UC handle locale variants of the same term — separate pages or page attributes? | Affects page structure | Research UC Pages locale support; may need separate pages per locale |
| Q-L300-7 | Can we programmatically set certification status via API? | Affects certification workflow | Check UC REST API for certification endpoints |

## References

- **L200-C6 v2** — UC Pages per Locale (canvas notebooks/308703764929921)
- **Semantics 02** — Full-Spectrum Banking Domain, 108 terms (canvas notebooks/308703765065096)
- **L200-C1** — Locale Config Engine (canvas notebooks/308703764929903)
- **Rapid Ontology Standup** — L200-C: Domain, Subdomain & Pages Standup methodology
