# Consumer Banking UC Semantics Candidates

> **Status:** Draft — Oct 6, 2026
> **Author:** Matthew Giglia
> **File:** docs/semantics/01_consumer_banking_domain.md
> **Format:** Structured for Unity Catalog Domains, Subdomains, and Pages
> **Source:** FIBO ontology + Dutch banking terminology + design discussions

## UC Domain

**Domain:** Consumer Banking
**Description:** Business concepts, metrics, and terminology for consumer-facing retail banking — accounts, transactions, products, and customer financial behavior. Sourced from FIBO (Financial Industry Business Ontology) and adapted for UC Semantics with locale-specific terminology (EN, EN-GB, NL).

## UC Subdomains

| Subdomain | Description | FIBO Module | Tables/Views |
|---|---|---|---|
| **Accounts** | Bank accounts, account types, account lifecycle, account holders | FBC/ClientsAndAccounts | silver.customer, silver.account, silver.account_holder |
| **Transactions** | Account postings, payment types, merchant categories, settlement | FND/Accounting, FBC/ClientsAndAccounts | silver.account_transaction |
| **Balances** | Account balances, balance types, daily snapshots | FND/Accounting/CashFlows | silver.account_balance_daily |
| **Products** | Banking products, eligibility, rates, product lifecycle | FBC/ProductsAndServices | silver.product |
| **Payments** | Credit transfers, direct debits, payment schemes (SEPA/ACH/FPS) | FND/PaymentsAndSchedules | silver.account_transaction (payment_scheme) |
| **Customer Behavior** | Spending patterns, anomalies, trends, segments | Behavioral (not FIBO) | gold.customer_behavior_metrics |

## UC Pages — Glossary Terms (32 terms)

Each term is structured for UC Pages: definition, business context, data usage, related terms, FIBO source, and locale variants.

### Accounts Subdomain (8 terms)

#### 1. Account Balance / Saldo

- **Definition (EN):** The net monetary amount available in a bank account at a specific point in time.
- **Definition (NL):** Het nettobedrag dat beschikbaar is op een bankrekening op een bepaald moment.
- **Business Context:** The most frequently asked consumer question. Includes available balance (what you can spend) and ledger balance (what's been posted). Pending transactions may cause these to differ.
- **Data Usage:** `silver.account_balance_daily.amount` where `balance_type = 'AVAILABLE'`. Metric view measure: `total_balance = SUM(balance)`.
- **FIBO Source:** `fibo-fbc-pas-caa:Balance` — the monetary amount representing the net position of an account.
- **Related Terms:** Available Balance, Ledger Balance, Pending Transaction
- **Locale Variants:** EN: "balance, account balance" / NL: "saldo, rekeningsaldo" / EN-GB: "balance, account balance"
- **Priority:** High — UC Page candidate

#### 2. Payment Account / Betaalrekening

- **Definition (EN):** A bank account from which the holder can make and receive payments, including transfers, card purchases, and direct debits.
- **Definition (NL):** Een bankrekening waarmee de rekeninghouder betalingen kan doen en ontvangen, inclusief overschrijvingen, pinbetalingen en incasso's.
- **Business Context:** The primary account type for daily banking. In FIBO terms, this is a TransactionDepositAccount — an account usable for third-party payment transactions. Distinguished from a savings account (spaarrekening) which cannot directly send payments.
- **Data Usage:** `silver.account.account_type = 'PAYMENT'`. Metric view dimension with synonym `betaalrekening`.
- **FIBO Source:** `TransactionDepositAccount` — an account from which the holder may make transfers or withdrawals.
- **Related Terms:** Savings Account, Current Account, IBAN
- **Locale Variants:** EN: "checking account, payment account" / NL: "betaalrekening" / EN-GB: "current account"
- **Priority:** High — UC Page candidate

#### 3. Savings Account / Spaarrekening

- **Definition (EN):** A deposit account intended for saving money, typically earning interest, and not intended for day-to-day payment transactions.
- **Definition (NL):** Een depositorekening bedoeld om geld te sparen, doorgaans met rente, en niet bedoeld voor dagelijkse betalingen.
- **Business Context:** In FIBO terms, a NonTransactionDepositAccount. EU case law uses the ability to make or receive third-party payment transactions as the decisive criterion for distinguishing payment accounts from savings accounts.
- **Data Usage:** `silver.account.account_type = 'SAVINGS'`. Metric view dimension with synonym `spaarrekening`.
- **FIBO Source:** `NonTransactionDepositAccount`
- **Related Terms:** Payment Account, Interest, Term Deposit
- **Locale Variants:** EN: "savings account" / NL: "spaarrekening" / EN-GB: "savings account"
- **Priority:** High — UC Page candidate

#### 4. Account Holder / Rekeninghouder

- **Definition (EN):** A person or organization legally associated with a bank account, with rights to transact on that account.
- **Definition (NL):** Een persoon of organisatie die juridisch verbonden is aan een bankrekening, met het recht om transacties uit te voeren.
- **Data Usage:** `silver.account_holder.holder_role` (PRIMARY, JOINT, AUTHORIZED_USER).
- **FIBO Source:** `fibo-fbc-pas-caa:CustomerAccountHolder`
- **Related Terms:** Joint Account, Authorized User, KYC
- **Priority:** Medium — UC Page candidate

#### 5. IBAN (International Bank Account Number)

- **Definition:** A standardized international identifier for bank accounts, used for cross-border and domestic payments in SEPA countries.
- **Business Context:** Format varies by country. NL: NL + 2 check digits + 4 bank code + 10 account number (e.g., NL91ABNA0417164300). The IBAN identifies the account, not the account holder.
- **Data Usage:** `silver.account_transaction.counterparty_iban`. Not stored in clear text in analytical tables — hashed for joins.
- **FIBO Source:** `InternationalBankAccountIdentifier`
- **Priority:** Medium — UC Page candidate

#### 6. Account Status

- **Definition:** The current lifecycle state of a bank account: PENDING, OPEN, ACTIVE, DORMANT, BLOCKED, or CLOSED.
- **Data Usage:** `silver.account.account_status`. Drives the Account Lifecycle state machine.
- **Related Terms:** KYC, Dormant Account, Account Closure
- **Priority:** Medium — UC Page candidate

#### 7. Customer Segment

- **Definition:** A classification of customers based on financial profile: Premium (high AUM/income), Standard, or Basic.
- **Data Usage:** `silver.customer.customer_segment`. Metric view dimension. Drives product eligibility.
- **Priority:** Medium — UC Page candidate

#### 8. KYC (Know Your Customer)

- **Definition:** The regulatory process of verifying a customer's identity before opening an account. Required by anti-money laundering (AML) regulations.
- **Data Usage:** Account Lifecycle SM: APPLICATION_SUBMITTED → KYC_PENDING → APPROVED/REJECTED.
- **Priority:** Low — UC Page candidate

### Transactions Subdomain (8 terms)

#### 9. Credit Transfer / Overschrijving

- **Definition (EN):** A payment transaction where money is transferred from the originator's account to the beneficiary's account.
- **Definition (NL):** Een betaaltransactie waarbij geld wordt overgemaakt van de rekening van de opdrachtgever naar de rekening van de begunstigde.
- **Data Usage:** `silver.account_transaction.transaction_type = 'CREDIT_TRANSFER'`. Payment scheme: SCT (SEPA), ACH (US), BACS (UK).
- **FIBO Source:** Payment transaction / SCT
- **Locale Variants:** EN: "transfer, bank transfer" / NL: "overschrijving" / EN-GB: "bank transfer"
- **Priority:** High — UC Page candidate

#### 10. Direct Debit / Incasso

- **Definition (EN):** A creditor-initiated debit from a debtor's payment account, authorized by a mandate.
- **Definition (NL):** Een door de crediteur geïnitieerde afschrijving van de betaalrekening van de debiteur, geautoriseerd door een machtiging.
- **Business Context:** SEPA SDD Core allows unconditional reversal (storno) within 8 weeks. Unauthorized direct debits can be reversed within 13 months.
- **Data Usage:** `silver.account_transaction.transaction_type = 'DIRECT_DEBIT'`. Payment scheme: SDD_CORE (SEPA), ACH (US), BACS (UK).
- **Locale Variants:** EN: "direct debit" / NL: "incasso" / EN-GB: "direct debit"
- **Priority:** High — UC Page candidate

#### 11. Monthly Spending / Maandelijkse Uitgaven

- **Definition:** The total amount debited from a customer's accounts in a calendar month, excluding transfers between own accounts.
- **Data Usage:** Metric view measure: `monthly_spend = SUM(CASE WHEN direction = 'DEBIT' THEN amount END)`.
- **Locale Variants:** EN: "monthly spending, monthly expenses" / NL: "maandelijkse uitgaven, uitgaven deze maand"
- **Priority:** High — UC Page candidate

#### 12. Transaction Category / Transactiecategorie

- **Definition:** A classification of transactions by merchant type: groceries, dining, transport, retail, entertainment, healthcare, utilities, subscriptions.
- **Data Usage:** `silver.account_transaction.merchant_category`. Metric view dimension.
- **Locale Variants:** EN: "category, spending category" / NL: "categorie, bestedingscategorie"
- **Priority:** High — UC Page candidate

#### 13. Posting Date / Boekingsdatum

- **Definition:** The date a transaction is recorded (posted) to the account ledger. May differ from the transaction date (when the purchase was made).
- **Data Usage:** `silver.account_transaction.posting_date`.
- **Locale Variants:** EN: "posting date" / NL: "boekingsdatum" / EN-GB: "posting date"
- **Priority:** Medium — UC Page candidate

#### 14. Transaction Direction / Af- en Bijschrijving

- **Definition:** Whether a transaction is a debit (money leaving the account) or credit (money entering the account).
- **Data Usage:** `silver.account_transaction.direction` (DEBIT, CREDIT). Amount is always non-negative; direction determines the sign.
- **Locale Variants:** EN: "debit, credit" / NL: "afschrijving, bijschrijving"
- **Priority:** Medium — UC Page candidate

#### 15. Counterparty / Tegenrekening

- **Definition:** The other party in a transaction — the account that sent or received the payment.
- **Data Usage:** `silver.account_transaction.counterparty_iban`.
- **Locale Variants:** EN: "counterparty" / NL: "tegenrekening, tegenpartij"
- **Priority:** Medium — UC Page candidate

#### 16. Remittance Information / Mededeling

- **Definition:** Free-text description attached to a payment, describing the purpose of the transaction.
- **Data Usage:** `silver.account_transaction.remittance_info`.
- **Locale Variants:** EN: "description, reference" / NL: "mededeling, omschrijving"
- **Priority:** Low — UC Page candidate

### Payments Subdomain (4 terms)

#### 17. SEPA Credit Transfer (SCT)

- **Definition:** A euro credit transfer using SEPA rules, identified by IBAN. Standard execution: 1 business day.
- **Data Usage:** `silver.account_transaction.payment_scheme = 'SCT'`.
- **Priority:** High (NL/EU) — UC Page candidate

#### 18. SEPA Instant Credit Transfer (SCT Inst)

- **Definition:** An instant variant of SCT — funds available to the beneficiary within seconds, 24/7/365.
- **Data Usage:** `silver.account_transaction.payment_scheme = 'SCT_INST'`.
- **Locale Variants:** NL: "instantoverschrijving"
- **Priority:** High (NL/EU) — UC Page candidate

#### 19. SEPA Direct Debit (SDD Core)

- **Definition:** A SEPA direct debit scheme for consumer accounts. 8-week unconditional reversal right; 13-month for unauthorized debits.
- **Data Usage:** `silver.account_transaction.payment_scheme = 'SDD_CORE'`.
- **Priority:** High (NL/EU) — UC Page candidate

#### 20. Payment Scheme

- **Definition:** The payment network or protocol used to execute a transaction. Varies by locale: SEPA (SCT, SCT_INST, SDD_CORE) for EU; ACH, WIRE, ZELLE for US; BACS, CHAPS, FPS for UK.
- **Data Usage:** `silver.account_transaction.payment_scheme`. Metric view dimension.
- **Priority:** High — UC Page candidate

### Products Subdomain (4 terms)

#### 21. Product Eligibility

- **Definition:** Whether a customer qualifies for a specific banking product based on financial criteria (balance, income, tenure, credit score).
- **Data Usage:** Product Relationship SM: balance/income threshold → ELIGIBLE state. Metric view dimension.
- **Priority:** High — UC Page candidate

#### 22. Credit Utilization

- **Definition:** The ratio of outstanding credit balance to the credit limit, expressed as a percentage.
- **Data Usage:** Metric view measure: `credit_utilization = SUM(outstanding) / SUM(credit_limit)`.
- **Priority:** Medium — UC Page candidate

#### 23. Interest Accrual

- **Definition:** The process of calculating and crediting interest earned on a savings or deposit account, typically quarterly in the Netherlands.
- **Data Usage:** Episode 6 (Savings Goal): quarterly interest credit event.
- **Priority:** Medium — UC Page candidate

#### 24. Product Type

- **Definition:** The classification of a banking product: CHECKING_ACCOUNT, SAVINGS_ACCOUNT, TERM_DEPOSIT, CREDIT_CARD, PERSONAL_LOAN, MORTGAGE.
- **Data Usage:** `silver.product.product_type`. Metric view dimension.
- **Priority:** Medium — UC Page candidate

### Customer Behavior Subdomain (4 terms)

#### 25. Spending Trend (Month-over-Month)

- **Definition:** The percentage change in total spending from one month to the next.
- **Data Usage:** Metric view measure: `spending_trend_mom`. Gold layer aggregation.
- **Priority:** High — UC Page candidate

#### 26. Spending Anomaly

- **Definition:** A statistically unusual spending pattern — significantly higher or lower than the customer's baseline, or in an unusual category or geography.
- **Data Usage:** Episode 10 (Spending Anomaly). Metric view measure: `anomaly_score`.
- **Priority:** Medium — UC Page candidate

#### 27. Customer Behavior State

- **Definition:** The current behavioral classification of a customer: NORMAL, PAYDAY, BILL_WINDOW, WEEKEND_SPEND, or LOW_BALANCE. Determines spending probability and category distribution.
- **Data Usage:** State machine overlay. Not directly in metric views but drives the simulation.
- **Priority:** Low — UC Page candidate (internal/technical)

#### 28. Proactive Insight

- **Definition:** A system-generated notification about a customer's financial situation, surfaced before the customer asks. Examples: "Your spending on dining is up 30% this month" or "You may qualify for a Premium Saver account."
- **Data Usage:** `app.insights` table in Lakebase. Generated by nightly Lakeflow Jobs.
- **Priority:** Medium — UC Page candidate

### Security & Compliance Subdomain (4 terms)

#### 29. Consumer GUID

- **Definition:** A globally unique identifier assigned to each consumer by the Lakebase session management layer. Used as the required parameter for parameterized metric views to enforce consumer data isolation.
- **Data Usage:** Parameterized metric view filter: `customer_id = :consumer_guid`. Lakebase session table.
- **Priority:** High — UC Page candidate (internal/technical)

#### 30. Session Token

- **Definition:** A short-lived token issued by the Databricks App after JWT validation, used for subsequent requests in the same session without re-validating the JWT.
- **Data Usage:** Lakebase session management. Not in metric views.
- **Priority:** Low — UC Page candidate (internal/technical)

#### 31. Consent State

- **Definition:** Whether a consumer has granted or revoked consent for specific types of data queries (e.g., transaction history, product recommendations, spending analysis).
- **Data Usage:** `app.consent` table in Lakebase. Checked before every Genie Agent API call.
- **Priority:** Medium — UC Page candidate

#### 32. GDPR Right to Erasure

- **Definition:** A consumer's right under GDPR to request deletion of all their personal data. Implemented as DELETE from Lakebase (Postgres) + Delta DML + VACUUM.
- **Data Usage:** Deletion keyed by `customer_id` across all tables.
- **Priority:** Medium — UC Page candidate

## Tagging Strategy

| Priority | Count | Action |
|---|---|---|
| **High** | 14 | Create UC Pages immediately; include in Genie Agent instructions |
| **Medium** | 13 | Create UC Pages during L200-C6; include in Genie Agent knowledge store |
| **Low** | 5 | Document as internal/technical terms; create UC Pages if time permits |

## Implementation Notes

- UC Pages should be authored in the locale language (EN, EN-GB, or NL) based on the deployment locale
- Each Page should link to the metric view measure or dimension it defines
- Pages marked "Certified" become the authoritative source for Genie Ontology's OntoRank
- The FIBO source provides the semantic lineage — "this definition is grounded in the W3C financial ontology"
