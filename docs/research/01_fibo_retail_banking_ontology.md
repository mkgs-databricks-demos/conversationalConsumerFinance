# FIBO Research: Retail Banking Ontology as Context for UC Semantics

## Purpose

Use FIBO (Financial Industry Business Ontology) — the W3C/EDM Council standard for banking — as **context for Genie Code** to generate metric views, UC Pages, and sample data for an internal POC proving that an ontology isn't needed as a separate layer when UC Semantics can encode the same business meaning directly on the data.

**Author:** Matthew Giglia | **Date:** October 6, 2026
**Project:** NN Bank Conversational Banking

### The Thesis

FIBO defines the *concepts and relationships* for retail banking. OntoBricks materializes those concepts as a knowledge graph. But the same concepts can be expressed as **metric view dimensions, measures, and synonyms** — with FIBO providing the authoritative business definitions that Genie Code uses to generate the YAML. The ontology becomes *input context*, not *runtime infrastructure*.

## FIBO Domain Structure for Retail Banking

FIBO does not have a single "Retail Banking" domain. Retail banking concepts are assembled from several FIBO modules:

| FIBO Domain | Retail Banking Use | Key Concepts |
|---|---|---|
| **FBC** (Financial Business & Commerce) | Accounts, products, services, financial institutions | `CustomerAccount`, `BankAccount`, `DepositAccount`, `FinancialProduct`, `AccountHolder`, `Balance`, `IndividualTransaction` |
| **FND** (Foundations) | Parties, contracts, payments, amounts, dates | `Party`, `Agreement`, `PaymentsAndSchedules`, `CurrencyAmount`, `CashFlows` |
| **LOAN** | Card accounts, consumer credit | `CardAccounts`, `ConsumerLoans`, `LoanProducts` |
| **BE** (Business Entities) | Banks, customers as legal entities | `LegalEntities`, `FunctionalEntities` |

The primary module for this POC is **FBC/ProductsAndServices/ClientsAndAccounts** — it contains `Account`, `Balance`, `IndividualTransaction`, `AccountStatement`, and account-holder relationships.

### FIBO Class Hierarchy for Retail Banking

```
fibo-fbc-pas-caa:Account
├── fibo-fbc-pas-caa:CustomerAccount
│   ├── TransactionDepositAccount (betaalrekening)
│   ├── NonTransactionDepositAccount (spaarrekening)
│   └── LoanAccount
│
fibo-fbc-pas-caa:Balance
├── AvailableBalance
├── LedgerBalance
├── CurrentBalance
│
fibo-fbc-pas-caa:IndividualTransaction
├── DepositTransaction
├── WithdrawalTransaction
├── PaymentTransaction (overschrijving)
├── TransferTransaction
├── PurchaseTransaction
├── FeeTransaction
├── InterestTransaction
│
fibo-fbc-pas-fp:FinancialProduct
├── DepositProduct (CheckingProduct, SavingsProduct, TermDepositProduct)
├── CreditProduct
├── CardProduct
```

## Dutch Banking Terminology → FIBO → UC Semantics Mapping

This is the core mapping that Genie Code will use to generate metric views. Each row maps a Dutch banking term to its FIBO concept and then to the UC Semantics artifact that implements it.

| Dutch Term | English | FIBO Concept | UC Semantics Artifact |
|---|---|---|---|
| **betaalrekening** | payment/current account | `TransactionDepositAccount` | Metric view dimension: `account_type = 'PAYMENT'` + synonym `betaalrekening` |
| **spaarrekening** | savings account | `NonTransactionDepositAccount` | Metric view dimension: `account_type = 'SAVINGS'` + synonym `spaarrekening` |
| **rekeninghouder** | account holder | `CustomerAccountHolder` | Metric view dimension: `customer_id` (filtered by holder role) |
| **saldo** | balance | `Balance` / `hasBalance` | Metric view measure: `total_balance` + synonym `saldo` |
| **overschrijving** | credit transfer | Payment transaction / SCT | Metric view dimension: `transaction_type = 'CREDIT_TRANSFER'` + synonym `overschrijving` |
| **SEPA-overschrijving** | SEPA Credit Transfer | SCT payment scheme | Metric view dimension: `payment_scheme = 'SCT'` |
| **instantoverschrijving** | SEPA Instant Transfer | SCT Inst | Metric view dimension: `payment_scheme = 'SCT_INST'` |
| **incasso** | direct debit | SDD | Metric view dimension: `transaction_type = 'DIRECT_DEBIT'` + synonym `incasso` |
| **IBAN** | International Bank Account Number | `InternationalBankAccountIdentifier` | Table column: `account_identifier` (not a metric view concept) |
| **rekeningafschrift** | account statement | `AccountStatement` | Not a metric — a reporting view |
| **af- en bijschrijving** | debit/credit entry | `debit_credit_indicator` | Metric view dimension: `direction` + synonyms `afschrijving`, `bijschrijving` |
| **boekingsdatum** | posting date | Posting timestamp | Metric view dimension: `posting_date` + synonym `boekingsdatum` |
| **transactiedatum** | transaction date | Transaction date | Metric view dimension: `transaction_date` + synonym `transactiedatum` |
| **mededeling** | remittance information | Remittance text | Table column (not a metric dimension) |
| **tegenrekening** | counterparty account | Counterparty | Metric view dimension: `counterparty_iban` + synonym `tegenrekening` |

## FIBO-Aligned Sample Data Model (Delta Tables)

These are the Silver-layer tables that the metric views will source from. FIBO provides the semantic definitions; Delta provides the physical implementation.

### Core Tables

**`silver_customer`** — Party/customer (FIBO: `Party`, `CustomerAccountHolder`)
- `customer_id`, `party_type`, `legal_name`, `first_name`, `last_name`, `date_of_birth`, `country_of_residence`, `customer_status`, `customer_segment`, `onboarding_date`

**`silver_account`** — Bank account (FIBO: `CustomerAccount`, `TransactionDepositAccount`, `DepositAccount`)
- `account_id`, `account_type` (PAYMENT, SAVINGS, TERM_DEPOSIT, CREDIT_CARD), `product_id`, `currency_code`, `account_status`, `opened_date`, `closed_date`

**`silver_account_holder`** — Customer-account relationship (FIBO: `AccountHolder`, `hasPrimaryAccountHolder`)
- `account_id`, `customer_id`, `holder_role` (PRIMARY, JOINT, AUTHORIZED_USER)

**`silver_account_balance_daily`** — Daily balance snapshot (FIBO: `Balance`, `hasBalance`)
- `account_id`, `balance_date`, `balance_type` (LEDGER, AVAILABLE), `amount` (DECIMAL), `currency_code`

**`silver_account_transaction`** — Account postings (FIBO: `IndividualTransaction`)
- `transaction_id`, `account_id`, `transaction_date`, `posting_date`, `transaction_type` (CREDIT_TRANSFER, DIRECT_DEBIT, CARD_PURCHASE, CASH_WITHDRAWAL, FEE, INTEREST), `direction` (DEBIT, CREDIT), `amount` (DECIMAL), `currency_code`, `counterparty_iban`, `merchant_name`, `merchant_category`, `remittance_info`, `payment_scheme` (SCT, SCT_INST, SDD_CORE)

**`silver_product`** — Banking products (FIBO: `FinancialProduct`)
- `product_id`, `product_code`, `product_name`, `product_type`, `currency_code`, `interest_rate_type`, `overdraft_allowed`

### Key Design Decisions
- Use `DECIMAL(20,4)` for all monetary amounts — never DOUBLE
- Separate `direction` (DEBIT/CREDIT) from non-negative `amount` — explicit accounting sign convention
- `account_type` maps to FIBO class hierarchy (PAYMENT → TransactionDepositAccount, SAVINGS → NonTransactionDepositAccount)
- `payment_scheme` captures SEPA scheme (SCT, SCT_INST, SDD_CORE) — critical for Dutch banking
- Enable Delta CDF on all Silver tables for downstream audit pipelines

## How to Use FIBO as Context for Genie Code

The strategy: feed FIBO's business definitions into Genie Code as context, then use Genie Code to generate metric view YAML, sample data, and UC Pages.

### Step 1: Create a FIBO Context Document

Create a markdown document containing:
- The Dutch-to-FIBO-to-UC mapping table (above)
- The FIBO class hierarchy for retail banking
- The Silver table schemas
- Business rules (e.g., "a betaalrekening is a TransactionDepositAccount — it can send and receive payments; a spaarrekening is a NonTransactionDepositAccount — it cannot directly send payments to third parties")

Upload this as a UC Volume document attached to the Genie Agent.

### Step 2: Use Genie Code to Generate Metric Views

Prompt Genie Code with the FIBO context and ask it to generate metric view YAML:

*"Using the FIBO retail banking definitions in the attached context document, generate a metric view YAML for customer-level transaction metrics. Source table is `nn_bank_poc.silver.account_transaction` joined to `nn_bank_poc.silver.account` and `nn_bank_poc.silver.customer`. Include Dutch synonyms for all fields and measures based on the Dutch-to-FIBO mapping."*

### Step 3: Generate Sample Data

Use Genie Code or a notebook to generate realistic sample data:
- 100 customers with Dutch names
- 200 accounts (mix of betaalrekening and spaarrekening)
- 10,000 transactions across 6 months
- Daily balance snapshots
- 5 banking products

The sample data should use EUR, Dutch IBANs (NL format), SEPA payment schemes, and realistic merchant categories.

### Step 4: Create UC Pages from FIBO Definitions

For each key business term, create a UC Page using the FIBO definition as the authoritative source, translated to Dutch:

- **Saldo (Balance):** "Het nettobedrag dat beschikbaar is op een bankrekening op een bepaald moment. FIBO: fibo-fbc-pas-caa:Balance — het monetaire bedrag dat de nettopositie van een rekening vertegenwoordigt."
- **Betaalrekening (Payment Account):** "Een bankrekening waarmee de rekeninghouder betalingen kan doen en ontvangen. FIBO: TransactionDepositAccount."
- **Overschrijving (Credit Transfer):** "Een betaaltransactie waarbij geld wordt overgemaakt van de rekening van de opdrachtgever naar de rekening van de begunstigde. SEPA: SCT (SEPA Credit Transfer)."

### Step 5: Curate Genie Agent with FIBO-Informed Instructions

The Genie Agent instructions reference the FIBO definitions without requiring a graph:

*"Dit is een Genie Agent voor NN Bank klantgegevens. Gebruik de volgende definities: een betaalrekening (account_type = 'PAYMENT') is een rekening waarmee betalingen gedaan en ontvangen kunnen worden. Een spaarrekening (account_type = 'SAVINGS') is een depositorekening die niet bedoeld is voor dagelijkse betalingen. Saldo verwijst naar het beschikbare bedrag op de rekening. Antwoord altijd in het Nederlands."*

## What This Proves

When the POC is complete, we can demonstrate:

1. **FIBO's business definitions are fully expressible as UC Semantics** — metric view dimensions, measures, synonyms, and UC Pages encode the same meaning that FIBO's OWL classes and properties define
2. **Genie Code can use FIBO as context** to generate metric views — the ontology is input, not infrastructure
3. **A Genie Agent answers Dutch consumer banking questions** using FIBO-aligned metric views — no graph traversal needed
4. **The same metric views serve both the consumer app and internal analytics** — one semantic layer, two audiences
5. **An ontology is not needed as a runtime layer** when the business meaning is encoded directly on the data through UC Semantics

The ontology's value is in its *definitions*, not its *materialization*. FIBO tells you what "balance" means, what "payment account" means, how accounts relate to customers. UC Semantics encodes those definitions as metadata on the data itself. The graph is unnecessary middleware.
