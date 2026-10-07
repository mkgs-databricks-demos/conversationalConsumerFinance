# Research 07: Full-Spectrum FIBO Banking Data Generator

> **Status:** Draft — Oct 7, 2026
> **Author:** Matthew Giglia
> **File:** docs/research/07_full_spectrum_fibo_generator.md
> **Scope:** What a complete FIBO-aligned banking data generator would look like — covering all FIBO modules relevant to a full-service bank

## Purpose

The current state machine generator covers **retail consumer banking** — 3 state machines, 12 episode types, 6 Silver tables. This document explores what happens when we expand to cover the **full FIBO ontology** for a universal bank: consumer, commercial, mortgage, securities, treasury, and regulatory. This is the "if it's worth building for one customer, it's worth building for all" version — a generator that could serve any banking customer worldwide, not just retail. :citation[memory.preferences/design-philosophy,Design philosophy]

## FIBO Module Coverage Map

FIBO has **10 financial domains** plus foundations. Here's what each contributes to a banking data generator: :citation[web."https://spec.edmcouncil.org/fibo/ontology/master/latest/tree.html","Ontology file directory ."]

| FIBO Domain | Module | Banking Relevance | Generator Coverage |
|---|---|---|---|
| **FND** | Foundations | Parties, addresses, agreements, dates, currencies, payments | Cross-cutting (all state machines) |
| **FBC** | Financial Business & Commerce | Accounts, balances, transactions, products, institutions, debt, instruments | Core (all banking) |
| **LOAN** | Loans | Consumer loans, mortgages, commercial loans, cards, student loans, green loans | Lending state machines |
| **BE** | Business Entities | Legal entities, corporations, partnerships, trusts, ownership | Commercial banking parties |
| **SEC** | Securities | Debt, equities, funds, ABS/MBS, issuance, identification | Investment/wealth management |
| **DER** | Derivatives | Options, futures, swaps, structured instruments | Treasury/capital markets |
| **IND** | Indicators & Indices | Interest rates, FX, economic indicators, market indices | Reference data feeds |
| **MD** | Market Data | Prices, yields, trading status, analytics | Real-time market feeds |
| **CAE** | Corporate Actions & Events | Dividends, splits, mergers, rights issues | Securities lifecycle |
| **BP** | Business Process | Issuance workflows, process flows | Operational processes |

## Expanded State Machine Architecture

### Current: 3 State Machines (Retail Consumer)

```
Account Lifecycle SM ←→ Transaction Processing SM ←→ Product Relationship SM
```

### Expanded: 12 State Machines (Full-Service Bank)

```
┌─────────────────────────────────────────────────────────────────┐
│  TIER 1: PARTY & RELATIONSHIP (FND + BE)                        │
│                                                                 │
│  SM-1: Consumer Party Lifecycle                                 │
│  SM-2: Business Party Lifecycle                                 │
│  SM-3: Party Relationship (joint, authorized, beneficial owner) │
├─────────────────────────────────────────────────────────────────┤
│  TIER 2: ACCOUNTS & DEPOSITS (FBC)                              │
│                                                                 │
│  SM-4: Deposit Account Lifecycle (checking, savings, CD, money  │
│         market — consumer AND business)                         │
│  SM-5: Transaction Processing (payments, transfers, direct      │
│         debits, card purchases, fees, interest)                 │
├─────────────────────────────────────────────────────────────────┤
│  TIER 3: LENDING (LOAN)                                         │
│                                                                 │
│  SM-6: Consumer Loan Lifecycle (personal, auto, student, HELOC) │
│  SM-7: Mortgage Lifecycle (origination, servicing, payoff)      │
│  SM-8: Credit Card Lifecycle (application, usage, billing,      │
│         payment, rewards, dispute)                              │
│  SM-9: Commercial Loan Lifecycle (term loan, revolver,          │
│         syndicated, trade finance)                              │
├─────────────────────────────────────────────────────────────────┤
│  TIER 4: INVESTMENTS & WEALTH (SEC + DER + IND + MD)            │
│                                                                 │
│  SM-10: Investment Account Lifecycle (brokerage, retirement,    │
│          managed portfolio)                                     │
│  SM-11: Securities Lifecycle (buy, hold, dividend, sell,        │
│          corporate action)                                      │
├─────────────────────────────────────────────────────────────────┤
│  TIER 5: BANK OPERATIONS (FBC + FND)                            │
│                                                                 │
│  SM-12: General Ledger / Accounting (double-entry posting,      │
│          reconciliation, period close)                          │
└─────────────────────────────────────────────────────────────────┘
```

### Coupling Points Between All 12 State Machines

```
SM-1 (Consumer Party) ──────────┐
SM-2 (Business Party) ──────────┤
SM-3 (Party Relationship) ──────┤
                                ▼
                    SM-4 (Deposit Accounts) ◄──── SM-12 (GL Posting)
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
         SM-5 (Txns)  SM-6 (Loans) SM-10 (Investments)
              │          │          │
              │     ┌────┼────┐     │
              │     ▼    ▼    ▼     ▼
              │  SM-7  SM-8  SM-9  SM-11 (Securities)
              │  (Mtg) (Card)(Comm)  │
              │          │          │
              └──────────┼──────────┘
                         ▼
                    SM-12 (GL Posting)
                    Every financial event → double-entry journal
```

## Expanded Silver Table Inventory

### Tier 1: Party & Relationship (8 tables)

| Table | FIBO Concept | New? |
|---|---|---|
| `silver.party` | Party (supertype for person + organization) | **Renamed** from `silver.customer` — now covers both consumers and businesses |
| `silver.person` | IndividualPerson (consumer-specific attributes) | **New** — date_of_birth, nationality, tax_id_hash |
| `silver.organization` | FormalOrganization / LegalEntity | **New** — legal_form, registration_number, industry_code, incorporation_date |
| `silver.party_address` | PhysicalAddress / hasMailingAddress | **New** — address_type, address_lines, city, postal_code, country |
| `silver.party_contact` | ElectronicMailAddress / TelephoneNumber | **New** — contact_type (EMAIL, MOBILE, LANDLINE), contact_value |
| `silver.party_identifier` | PartyIdentifier | **New** — identifier_type (TAX_ID, BSN, SSN, KVK), identifier_value_hash |
| `silver.party_relationship` | AccountHolder + beneficial owner + authorized signer | **Expanded** from `silver.account_holder` — now covers all party-to-party and party-to-account relationships |
| `silver.party_kyc` | KYC/AML verification events | **New** — kyc_status, verification_date, risk_score, pep_flag |

### Tier 2: Accounts & Deposits (6 tables)

| Table | FIBO Concept | New? |
|---|---|---|
| `silver.account` | CustomerAccount / DepositAccount | **Expanded** — now includes business accounts (OPERATING, PAYROLL, ESCROW) |
| `silver.account_identifier` | AccountIdentifier / BankAccountIdentifier | **New** — IBAN, BBAN, sort_code, routing_number per locale |
| `silver.account_balance` | Balance / hasBalance | **Renamed** from `silver.account_balance_daily` — now includes intraday balances |
| `silver.account_transaction` | IndividualTransaction | **Expanded** — adds transaction_status, authorization_code, settlement_date |
| `silver.account_statement` | AccountStatement | **New** — period, opening/closing balance, transaction count |
| `silver.product` | FinancialProduct / BankingProduct | **Expanded** — adds credit_limit, min_payment, annual_fee, interest_rate |

### Tier 3: Lending (8 tables)

| Table | FIBO Concept | New? |
|---|---|---|
| `silver.loan` | Loan / ConsumerLoan / CommercialLoan | **New** — loan_type, principal, interest_rate, term_months, maturity_date, collateral_type |
| `silver.loan_payment` | PaymentSchedule / hasPaymentHistory | **New** — payment_date, principal_amount, interest_amount, penalty, remaining_balance |
| `silver.loan_event` | LoanEvent | **New** — event_type (DISBURSEMENT, PAYMENT, DELINQUENCY, DEFAULT, RESTRUCTURE, PAYOFF) |
| `silver.mortgage` | LoanSecuredByRealEstate / ClosedEndMortgageLoan | **New** — property_type, ltv_ratio, appraisal_value, escrow_amount |
| `silver.mortgage_property` | RealProperty | **New** — property_address, property_type, valuation_date, valuation_amount |
| `silver.credit_card` | CreditCardAccount / ConsumerCreditCardAgreement | **New** — card_number_hash, card_type, credit_limit, billing_cycle_day, rewards_program |
| `silver.credit_card_statement` | Statement for credit card billing | **New** — statement_date, balance, min_payment, due_date, interest_charged |
| `silver.commercial_facility` | CreditFacility / RevolvingCreditFacility | **New** — facility_type (REVOLVER, TERM, SYNDICATED), committed_amount, drawn_amount, undrawn_amount |

### Tier 4: Investments & Wealth (6 tables)

| Table | FIBO Concept | New? |
|---|---|---|
| `silver.investment_account` | InvestmentAccount / BrokerageAccount | **New** — account_type (BROKERAGE, RETIREMENT, MANAGED), investment_objective |
| `silver.security` | SecurityAsset / EquityInstrument / DebtInstrument | **New** — security_type (EQUITY, BOND, FUND, ETF), isin, ticker, currency |
| `silver.holding` | SecurityHolding | **New** — account_id, security_id, quantity, cost_basis, market_value |
| `silver.trade` | SecurityTransaction | **New** — trade_type (BUY, SELL), quantity, price, settlement_date, commission |
| `silver.corporate_action` | CorporateAction | **New** — action_type (DIVIDEND, SPLIT, MERGER, RIGHTS_ISSUE), ex_date, record_date, pay_date |
| `silver.market_data_daily` | MarketData / SecurityPrice | **New** — security_id, price_date, open, high, low, close, volume |

### Tier 5: Bank Operations (4 tables)

| Table | FIBO Concept | New? |
|---|---|---|
| `silver.gl_journal_entry` | AccountingTransaction / GeneralLedger | **New** — entry_id, posting_date, debit_account, credit_account, amount, description |
| `silver.gl_account` | LedgerAccount | **New** — gl_account_id, account_name, account_type (ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE) |
| `silver.regulatory_report` | Regulatory reporting | **New** — report_type (HMDA, CRA, BSA/AML, FATCA), reporting_period, status |
| `silver.interest_rate_reference` | InterestRate / ReferenceRate | **New** — rate_type (EURIBOR, SOFR, SONIA, ECB_REFI), rate_date, rate_value |

### Total Silver Table Count

| Tier | Tables | Current | New |
|---|---|---|---|
| Tier 1: Party & Relationship | 8 | 2 (customer, account_holder) | 6 new |
| Tier 2: Accounts & Deposits | 6 | 4 (account, balance, transaction, product) | 2 new |
| Tier 3: Lending | 8 | 0 | 8 new |
| Tier 4: Investments & Wealth | 6 | 0 | 6 new |
| Tier 5: Bank Operations | 4 | 0 | 4 new |
| **Total** | **32** | **6** | **26 new** |

## Expanded Episode Types

### Current: 12 Episodes (Retail Consumer)

### Expanded: 40+ Episodes (Full-Service Bank)

#### Tier 1: Party Episodes (6)

| # | Episode | State Machine | Events Generated |
|---|---|---|---|
| 1 | Consumer Onboarding | SM-1 | Application, KYC check, identity verification, account opening |
| 2 | Business Onboarding | SM-2 | Company registration, UBO verification, KYC/AML, account opening |
| 3 | Life Event (Consumer) | SM-1 | Address change, name change, marriage, divorce, death |
| 4 | Corporate Event (Business) | SM-2 | Merger, acquisition, name change, ownership change, dissolution |
| 5 | Relationship Change | SM-3 | Add joint holder, remove authorized signer, change beneficial owner |
| 6 | KYC Refresh | SM-1/SM-2 | Periodic re-verification, enhanced due diligence, PEP screening |

#### Tier 2: Account & Transaction Episodes (8)

| # | Episode | State Machine | Events Generated |
|---|---|---|---|
| 7 | Salary & Income | SM-5 | Salary credit, freelance income, government benefits |
| 8 | Recurring Bills | SM-5 | Rent, utilities, insurance, subscriptions |
| 9 | Consumer Spending | SM-5 | Card purchases, ATM withdrawals, online payments |
| 10 | Transfers | SM-5 | SEPA/ACH/FPS credit transfers, instant transfers |
| 11 | Direct Debits | SM-5 | Incasso, reversals (storno), mandate management |
| 12 | Savings Goal | SM-4 | Automatic transfers, interest accrual, goal tracking |
| 13 | Business Payments | SM-5 | Payroll batch, supplier payments, tax payments, VAT |
| 14 | Cash Management | SM-5 | Sweep accounts, zero-balance accounts, pooling |

#### Tier 3: Lending Episodes (10)

| # | Episode | State Machine | Events Generated |
|---|---|---|---|
| 15 | Personal Loan Lifecycle | SM-6 | Application, approval, disbursement, repayment, early payoff |
| 16 | Auto Loan Lifecycle | SM-6 | Application, vehicle valuation, approval, disbursement, repayment |
| 17 | Student Loan Lifecycle | SM-6 | Application, enrollment verification, disbursement, grace period, repayment |
| 18 | Mortgage Origination | SM-7 | Application, appraisal, underwriting, approval, closing, funding |
| 19 | Mortgage Servicing | SM-7 | Monthly payment, escrow, insurance, tax, rate adjustment (ARM) |
| 20 | Mortgage Life Events | SM-7 | Refinance, modification, forbearance, short sale, foreclosure |
| 21 | Credit Card Usage | SM-8 | Purchases, cash advances, balance transfers, rewards accrual |
| 22 | Credit Card Billing | SM-8 | Statement generation, minimum payment, full payment, interest charge |
| 23 | Commercial Term Loan | SM-9 | Drawdown, repayment, covenant testing, restructuring |
| 24 | Revolving Credit Facility | SM-9 | Draw, repay, redraw, commitment fee, utilization reporting |

#### Tier 4: Investment Episodes (8)

| # | Episode | State Machine | Events Generated |
|---|---|---|---|
| 25 | Account Opening (Investment) | SM-10 | Application, suitability assessment, account activation |
| 26 | Equity Trading | SM-11 | Buy order, execution, settlement, holding update |
| 27 | Bond Trading | SM-11 | Buy, coupon payment, maturity, sell |
| 28 | Fund Investment | SM-11 | Subscription, NAV calculation, redemption, distribution |
| 29 | Dividend Processing | SM-11 | Declaration, ex-date, record date, payment, reinvestment |
| 30 | Corporate Action | SM-11 | Stock split, merger, rights issue, tender offer |
| 31 | Portfolio Rebalancing | SM-10 | Target allocation drift, rebalance trades, confirmation |
| 32 | Market Data Feed | Reference | Daily prices, rates, indices, FX rates |

#### Tier 5: Operations Episodes (8)

| # | Episode | State Machine | Events Generated |
|---|---|---|---|
| 33 | GL Posting | SM-12 | Double-entry journal for every financial event |
| 34 | End-of-Day Processing | SM-12 | Balance calculation, interest accrual, fee assessment |
| 35 | Month-End Close | SM-12 | Period close, accruals, provisions, reporting |
| 36 | Regulatory Reporting | SM-12 | HMDA, CRA, BSA/AML, FATCA, SEPA reporting |
| 37 | Fraud Detection | SM-5 | Suspicious transaction, alert, investigation, SAR filing |
| 38 | Dispute Resolution | SM-5 | Customer dispute, chargeback, provisional credit, resolution |
| 39 | Interest Rate Change | Reference | Central bank rate change → ARM adjustment, savings rate change |
| 40 | FX Rate Update | Reference | Daily FX rates for multi-currency accounts |

## Expanded Gold Materialized Views

| Gold MV | Source Silver Tables | Consumer Questions It Enables |
|---|---|---|
| `gold.mv_customer_transactions` | party + account + transaction + balance | "What's my balance?", "Show my spending" |
| `gold.mv_customer_products` | party + account + product | "What products do I have?" |
| `gold.mv_customer_behavior` | party + transaction (aggregated) | "Why is my spending higher?" |
| `gold.mv_customer_loans` | party + loan + loan_payment | "How much do I owe?", "When is my next payment?" |
| `gold.mv_customer_mortgage` | party + mortgage + mortgage_property + loan_payment | "What's my mortgage balance?", "Show my amortization" |
| `gold.mv_customer_cards` | party + credit_card + credit_card_statement + transaction | "What's my credit card balance?", "Show my rewards" |
| `gold.mv_customer_investments` | party + investment_account + holding + security + market_data | "What's my portfolio worth?", "Show my dividends" |
| `gold.mv_business_accounts` | party (org) + account + transaction + balance | "Show our operating account balance" |
| `gold.mv_business_loans` | party (org) + commercial_facility + loan_payment | "What's our credit facility utilization?" |
| `gold.mv_bank_gl` | gl_journal_entry + gl_account | "Show today's GL postings" (internal) |

## Expanded Metric Views

| Metric View | Source Gold MV | Audience | Measures |
|---|---|---|---|
| `gold.consumer_transaction_metrics` | mv_customer_transactions | Consumer | balance, spend, income, txn_count |
| `gold.consumer_loan_metrics` | mv_customer_loans | Consumer | outstanding, next_payment, remaining_term |
| `gold.consumer_mortgage_metrics` | mv_customer_mortgage | Consumer | balance, equity, ltv, escrow |
| `gold.consumer_card_metrics` | mv_customer_cards | Consumer | balance, available_credit, utilization, rewards |
| `gold.consumer_investment_metrics` | mv_customer_investments | Consumer | portfolio_value, gain_loss, dividend_income |
| `gold.business_account_metrics` | mv_business_accounts | Business | balance, cash_position, payables, receivables |
| `gold.business_loan_metrics` | mv_business_loans | Business | drawn, undrawn, utilization, covenant_status |
| `gold.bank_operations_metrics` | mv_bank_gl | Internal | daily_postings, period_close_status, exceptions |

## Scale Comparison

| Dimension | Current (Retail) | Full-Spectrum |
|---|---|---|
| **State machines** | 3 | 12 |
| **Episode types** | 12 | 40+ |
| **Silver tables** | 6 | 32 |
| **Gold MVs** | 3 | 10 |
| **Metric views** | 3 | 8 |
| **UC Pages** | 32 | ~120 |
| **Genie Agents** | 1 per locale | 3 per locale (consumer, business, internal) |
| **Daily events per 100 parties** | ~70–140 | ~300–600 |
| **FIBO modules covered** | FBC (partial), FND (partial) | FBC, FND, LOAN, BE, SEC, DER, IND, MD, CAE |
| **Locale configs** | 3 (US, GB, NL) | 3+ (extensible) |
| **Audience** | Consumer only | Consumer + Business + Internal |

## Implementation Strategy

### Phase 1: Retail Consumer (current — NN Bank POC)
- 3 SMs, 12 episodes, 6 Silver tables, 3 Gold MVs, 3 metric views
- **Timeline:** 12 weeks

### Phase 2: Retail Lending + Cards
- Add SM-6 (Consumer Loans), SM-7 (Mortgage), SM-8 (Credit Cards)
- Add 8 Silver tables, 3 Gold MVs, 3 metric views
- **Timeline:** 6 weeks incremental

### Phase 3: Commercial Banking
- Add SM-2 (Business Party), SM-9 (Commercial Loans)
- Add 4 Silver tables, 2 Gold MVs, 2 metric views
- Split Genie Agent: consumer + business
- **Timeline:** 4 weeks incremental

### Phase 4: Investments & Wealth
- Add SM-10 (Investment Account), SM-11 (Securities)
- Add 6 Silver tables, 1 Gold MV, 1 metric view
- **Timeline:** 6 weeks incremental

### Phase 5: Bank Operations
- Add SM-12 (GL), regulatory reporting, interest rate feeds
- Add 4 Silver tables, 1 Gold MV, 1 metric view
- Internal-facing Genie Agent
- **Timeline:** 4 weeks incremental

### Total: ~32 weeks for full-spectrum (vs. 12 weeks for retail-only)

## The Pitch

*"This is a complete FIBO-aligned banking data generator that produces realistic, longitudinally coherent data for every line of business a bank operates — consumer, commercial, mortgage, cards, investments, and treasury. Deploy it with one locale config and you have a working bank with metric views, Genie Agents, and a consumer app. The same canonical Silver model serves all audiences. The same Genie Code mapping workflow onboards real customer data. The ontology is the input — not the infrastructure."*

## Sources

- FIBO module tree: https://spec.edmcouncil.org/fibo/ontology/master/latest/tree.html
- FIBO GitHub: https://github.com/edmcouncil/fibo
- FIB-DM entity list: https://fib-dm.com/
- FIBO releases: https://github.com/edmcouncil/fibo/releases
- Bank Ontology definitions: https://bankontology.com/entity-definitions-list-report/
