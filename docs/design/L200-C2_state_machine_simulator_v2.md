# L200-C2 v2: Full-Spectrum State Machine Simulator — Detailed Design

> **Status:** Draft v2 — Oct 7, 2026
> **Author:** Matthew Giglia
> **Parent:** L100 — Conversational Consumer Finance: System Overview
> **Component:** C2 — State Machine Simulator (Layer 1: Data Generation)
> **Priority:** P0
> **Bundle:** Bundle 2 (Data Generator — dev/demo only, optional)
> **Supersedes:** L200-C2 v1 (3 state machines, 12 episodes — retail consumer only)

## Overview

The Full-Spectrum State Machine Simulator generates hyper-realistic synthetic banking data across **all lines of business** — consumer accounts, commercial accounts, lending, mortgages, credit cards, investments, and bank operations. It advances **12 coupled state machines** through **40+ episode types**, driven by a locale configuration, producing daily event streams that feed the Bronze layer.

This is the "if it's worth building for one customer, it's worth building for all" version — a generator that can serve any banking customer worldwide, deployed incrementally across 5 phases.

### Design Lineage

Adapts the hierarchical state machine + event sourcing pattern from:
- **RCM Synthetic Data Generator** — per-claim state machine with episode-driven clinical care sequences
- **Rx Rebate Horizontal** — dual state machine with 5 episode types and YAML-configured scenarios
- **L200-C2 v1** — 3 coupled state machines for retail consumer banking (Phase 1 scope)

## Dependencies

| Dependency | Component | What It Provides | Status |
|---|---|---|---|
| **Locale Config** | C1 | Holiday calendar, merchants, billers, payment schemes, salary dates, name generator, currency | Design complete |
| **Bronze Schema** | C3 | Target table schemas for event output | Design complete |
| **FIBO Research** | Research 01, 02, 07 | FIBO class hierarchy, Silver model, full-spectrum scope | Complete |
| **Semantics** | Semantics 02 | 108 glossary terms across 12 subdomains | Complete |

## State Machine Architecture

### 12 State Machines in 5 Tiers

```
┌─────────────────────────────────────────────────────────────────┐
│  TIER 1: PARTY & RELATIONSHIP (Phase 1)                         │
│  SM-1: Consumer Party Lifecycle                                 │
│  SM-2: Business Party Lifecycle (Phase 3)                       │
│  SM-3: Party Relationship                                       │
├─────────────────────────────────────────────────────────────────┤
│  TIER 2: ACCOUNTS & DEPOSITS (Phase 1)                          │
│  SM-4: Deposit Account Lifecycle                                │
│  SM-5: Transaction Processing                                   │
├─────────────────────────────────────────────────────────────────┤
│  TIER 3: LENDING (Phase 2)                                      │
│  SM-6: Consumer Loan Lifecycle                                  │
│  SM-7: Mortgage Lifecycle                                       │
│  SM-8: Credit Card Lifecycle                                    │
│  SM-9: Commercial Loan Lifecycle (Phase 3)                      │
├─────────────────────────────────────────────────────────────────┤
│  TIER 4: INVESTMENTS & WEALTH (Phase 4)                         │
│  SM-10: Investment Account Lifecycle                            │
│  SM-11: Securities Lifecycle                                    │
├─────────────────────────────────────────────────────────────────┤
│  TIER 5: BANK OPERATIONS (Phase 5)                              │
│  SM-12: General Ledger / Accounting                             │
└─────────────────────────────────────────────────────────────────┘
```

### SM-1: Consumer Party Lifecycle

**FIBO:** `cmns-pts:Party` → `cmns-pts:Person`

| From | Event | To | Probability | Condition |
|---|---|---|---|---|
| PROSPECT | APPLY | APPLICATION_SUBMITTED | 0.001/day | New customer generation rate |
| APPLICATION_SUBMITTED | KYC_CHECK | KYC_PENDING | 1.0 | Next business day |
| KYC_PENDING | KYC_PASS | APPROVED | 0.92 | 1–3 business days |
| KYC_PENDING | KYC_FAIL | REJECTED | 0.08 | 1–3 business days |
| APPROVED | ACTIVATE | ACTIVE | 1.0 | Same day |
| ACTIVE | SUSPEND | SUSPENDED | 0.0001/day | Compliance event |
| SUSPENDED | REACTIVATE | ACTIVE | 0.7 | 5–30 days |
| SUSPENDED | CLOSE | CLOSED | 0.3 | After 90 days |
| ACTIVE | CLOSE_REQUEST | CLOSED | 0.00005/day | Customer-initiated |
| ACTIVE | LIFE_EVENT | ACTIVE | varies | Address change, name change, segment change |

### SM-2: Business Party Lifecycle (Phase 3)

**FIBO:** `fibo-be-le-fbo:FormalOrganization`

| From | Event | To | Probability | Condition |
|---|---|---|---|---|
| PROSPECT | APPLY | APPLICATION_SUBMITTED | 0.0005/day | New business generation rate |
| APPLICATION_SUBMITTED | UBO_CHECK | UBO_PENDING | 1.0 | Next business day |
| UBO_PENDING | UBO_PASS | KYC_PENDING | 0.85 | 3–10 business days |
| UBO_PENDING | UBO_FAIL | REJECTED | 0.15 | 3–10 business days |
| KYC_PENDING | KYC_PASS | APPROVED | 0.90 | 5–15 business days |
| KYC_PENDING | KYC_FAIL | REJECTED | 0.10 | 5–15 business days |
| APPROVED | ACTIVATE | ACTIVE | 1.0 | Same day |
| ACTIVE | CORPORATE_EVENT | ACTIVE | varies | Merger, acquisition, name change |
| ACTIVE | DISSOLUTION | CLOSED | 0.00002/day | Business closure |

### SM-3: Party Relationship

**FIBO:** `fibo-fbc-pas-caa:AccountHolder`

| From | Event | To | Probability | Condition |
|---|---|---|---|---|
| — | ADD_PRIMARY | PRIMARY | 1.0 | Account opening |
| — | ADD_JOINT | JOINT | 0.15 | Joint account creation |
| — | ADD_AUTHORIZED | AUTHORIZED_SIGNER | 0.05 | Business accounts |
| — | ADD_BENEFICIAL | BENEFICIAL_OWNER | 0.10 | Business accounts (UBO) |
| — | ADD_GUARANTOR | GUARANTOR | 0.08 | Loan applications |
| PRIMARY | REMOVE | REMOVED | 0.001/day | Account closure |
| JOINT | REMOVE | REMOVED | 0.005/day | Relationship change |
| AUTHORIZED_SIGNER | REVOKE | REMOVED | 0.01/day | Authorization revoked |

### SM-4: Deposit Account Lifecycle

**FIBO:** `fibo-fbc-pas-caa:CustomerAccount`

| From | Event | To | Probability | Condition |
|---|---|---|---|---|
| PENDING | ACTIVATE | OPEN | 1.0 | After party approved |
| OPEN | FIRST_TRANSACTION | ACTIVE | 1.0 | First deposit/transaction |
| ACTIVE | NO_ACTIVITY_12MO | DORMANT | — | Deterministic: 365 days no activity |
| DORMANT | TRANSACTION | REACTIVATED | 0.3 | Customer returns |
| REACTIVATED | CONTINUE | ACTIVE | 1.0 | Immediate |
| ACTIVE | COMPLIANCE_BLOCK | BLOCKED | 0.0001/day | Compliance event |
| BLOCKED | RESOLVE | ACTIVE | 0.7 | 5–30 days |
| ACTIVE | CLOSE_REQUEST | CLOSED | 0.00005/day | Customer-initiated |
| DORMANT | AUTO_CLOSE | CLOSED | — | After 24 months dormant |

**Account types generated:** PAYMENT, SAVINGS, TERM_DEPOSIT, OPERATING (Phase 3), PAYROLL (Phase 3), ESCROW (Phase 3)

### SM-5: Transaction Processing

**FIBO:** `fibo-fbc-pas-caa:IndividualTransaction`

| From | Event | To | Timing | Notes |
|---|---|---|---|---|
| INITIATED | AUTHORIZE | AUTHORIZED | Instant | Card/PIN |
| INITIATED | DECLINE | DECLINED | Instant | Insufficient funds, fraud block |
| AUTHORIZED | SETTLE | PENDING_SETTLEMENT | 0–1 day | Batch settlement |
| PENDING_SETTLEMENT | POST | POSTED | 1–3 biz days | Locale-dependent (SCT: 1d, ACH: 1–3d) |
| POSTED | RECONCILE | RECONCILED | End of day | Automatic |
| POSTED | CUSTOMER_DISPUTE | DISPUTED | 1–90 days | Customer-initiated |
| DISPUTED | RESOLVE_CUSTOMER | REVERSED | 1–30 days | Favor customer |
| DISPUTED | RESOLVE_MERCHANT | RECONCILED | 1–30 days | Favor merchant |
| POSTED | MERCHANT_REVERSE | REVERSED | 1–5 days | Merchant-initiated |
| REVERSED | REFUND_CREDIT | REFUNDED | 1–5 days | Credit back to account |

### SM-6: Consumer Loan Lifecycle (Phase 2)

**FIBO:** `fibo-loan-spc-cns:ConsumerLoan`

| From | Event | To | Probability | Condition |
|---|---|---|---|---|
| — | APPLY | APPLIED | — | Customer applies |
| APPLIED | APPROVE | APPROVED | 0.75 | 1–5 business days |
| APPLIED | REJECT | REJECTED | 0.25 | 1–5 business days |
| APPROVED | DISBURSE | ACTIVE | 1.0 | 1–3 business days |
| ACTIVE | PAYMENT | ACTIVE | — | Monthly scheduled payment |
| ACTIVE | MISSED_PAYMENT | DELINQUENT | — | Payment not received by due date + 30 days |
| DELINQUENT | CURE | ACTIVE | 0.6 | Payment received |
| DELINQUENT | WORSEN | DEFAULT | 0.1 | 90+ days past due |
| DELINQUENT | RESTRUCTURE | RESTRUCTURED | 0.2 | Loan modification |
| RESTRUCTURED | CONTINUE | ACTIVE | 1.0 | New terms |
| ACTIVE | FORBEARANCE | FORBEARANCE | 0.01 | Hardship request |
| FORBEARANCE | RESUME | ACTIVE | 0.8 | After forbearance period |
| ACTIVE | EARLY_PAYOFF | PAID_OFF | 0.005/month | Customer pays in full |
| ACTIVE | MATURITY | PAID_OFF | — | Deterministic: maturity date |
| DEFAULT | WRITE_OFF | WRITTEN_OFF | 0.5 | After 180 days |
| DEFAULT | RECOVER | ACTIVE | 0.3 | Collections success |

**Loan types:** PERSONAL, AUTO, STUDENT, HELOC

### SM-7: Mortgage Lifecycle (Phase 2)

**FIBO:** `fibo-loan-reln-mtg:LoanSecuredByRealEstate`

| From | Event | To | Probability | Condition |
|---|---|---|---|---|
| — | APPLY | APPLIED | — | Customer applies |
| APPLIED | APPRAISAL | APPRAISED | 1.0 | 5–15 business days |
| APPRAISED | UNDERWRITE | UNDERWRITING | 1.0 | 1–3 business days |
| UNDERWRITING | APPROVE | APPROVED | 0.70 | 10–30 business days |
| UNDERWRITING | REJECT | REJECTED | 0.20 | 10–30 business days |
| UNDERWRITING | CONDITIONAL | CONDITIONALLY_APPROVED | 0.10 | Additional docs needed |
| CONDITIONALLY_APPROVED | SATISFY | APPROVED | 0.85 | 5–15 business days |
| APPROVED | CLOSE | FUNDED | 1.0 | 15–45 days (closing) |
| FUNDED | FIRST_PAYMENT | ACTIVE | 1.0 | First payment date |
| ACTIVE | PAYMENT | ACTIVE | — | Monthly payment |
| ACTIVE | MISSED_PAYMENT | DELINQUENT | — | 30+ days past due |
| DELINQUENT | CURE | ACTIVE | 0.5 | Payment received |
| DELINQUENT | MODIFICATION | MODIFIED | 0.2 | Loan modification |
| DELINQUENT | FORBEARANCE | FORBEARANCE | 0.15 | Hardship |
| DELINQUENT | FORECLOSURE | FORECLOSURE | 0.05 | 120+ days past due |
| ACTIVE | REFINANCE | PAID_OFF | 0.003/month | Refinance to new loan |
| ACTIVE | PAYOFF | PAID_OFF | 0.001/month | Full payoff |
| ACTIVE | RATE_ADJUST | ACTIVE | — | ARM rate adjustment (annual) |

**Mortgage types:** FIXED_30, FIXED_15, ARM_5_1, ARM_7_1, INTEREST_ONLY

### SM-8: Credit Card Lifecycle (Phase 2)

**FIBO:** `fibo-loan-spc-crd:CreditCardAccount`

| From | Event | To | Probability | Condition |
|---|---|---|---|---|
| — | APPLY | APPLIED | — | Customer applies |
| APPLIED | APPROVE | APPROVED | 0.65 | 1–3 business days |
| APPLIED | REJECT | REJECTED | 0.35 | 1–3 business days |
| APPROVED | ACTIVATE | ACTIVE | 0.90 | Card received + activated |
| ACTIVE | PURCHASE | ACTIVE | — | Card purchase (via SM-5) |
| ACTIVE | CASH_ADVANCE | ACTIVE | 0.01/month | Cash advance |
| ACTIVE | STATEMENT | STATEMENT_GENERATED | — | Monthly billing cycle |
| STATEMENT_GENERATED | FULL_PAYMENT | ACTIVE | 0.45 | By due date |
| STATEMENT_GENERATED | MIN_PAYMENT | ACTIVE | 0.35 | By due date |
| STATEMENT_GENERATED | PARTIAL_PAYMENT | ACTIVE | 0.10 | By due date |
| STATEMENT_GENERATED | NO_PAYMENT | DELINQUENT | 0.05 | Past due date + 30 days |
| STATEMENT_GENERATED | INTEREST_CHARGE | ACTIVE | — | If balance carried |
| ACTIVE | LIMIT_INCREASE | ACTIVE | 0.02/year | Automatic or requested |
| ACTIVE | LIMIT_DECREASE | ACTIVE | 0.005/year | Risk-based |
| ACTIVE | BLOCK | BLOCKED | 0.001/month | Fraud or compliance |
| BLOCKED | UNBLOCK | ACTIVE | 0.8 | After investigation |
| ACTIVE | EXPIRE | EXPIRED | — | Deterministic: expiry date |
| EXPIRED | RENEW | ACTIVE | 0.9 | New card issued |
| ACTIVE | CANCEL | CANCELLED | 0.005/month | Customer-initiated |

**Card types:** VISA, MASTERCARD, AMEX
**Rewards:** CASHBACK, POINTS, MILES, NONE

### SM-9: Commercial Loan Lifecycle (Phase 3)

**FIBO:** `fibo-loan-ln-ln:Loan` (commercial)

| From | Event | To | Probability | Condition |
|---|---|---|---|---|
| — | APPLY | APPLIED | — | Business applies |
| APPLIED | APPROVE | APPROVED | 0.60 | 15–45 business days |
| APPLIED | REJECT | REJECTED | 0.40 | 15–45 business days |
| APPROVED | DISBURSE | ACTIVE | 1.0 | 5–15 business days |
| ACTIVE | DRAW | ACTIVE | — | Revolver: draw on facility |
| ACTIVE | REPAY | ACTIVE | — | Revolver: repay drawn amount |
| ACTIVE | PAYMENT | ACTIVE | — | Term loan: scheduled payment |
| ACTIVE | COVENANT_TEST | ACTIVE | — | Quarterly covenant testing |
| ACTIVE | COVENANT_BREACH | BREACH | 0.05/quarter | Financial covenant violated |
| BREACH | WAIVER | ACTIVE | 0.6 | Lender grants waiver |
| BREACH | RESTRUCTURE | RESTRUCTURED | 0.3 | Loan restructured |
| BREACH | ACCELERATE | DEFAULT | 0.1 | Lender accelerates |
| ACTIVE | MATURITY | PAID_OFF | — | Deterministic: maturity date |
| ACTIVE | REFINANCE | PAID_OFF | 0.01/month | Refinance |

**Facility types:** TERM_LOAN, REVOLVER, SYNDICATED, TRADE_FINANCE

### SM-10: Investment Account Lifecycle (Phase 4)

**FIBO:** `fibo-sec-sec-ast:InvestmentAccount`

| From | Event | To | Probability | Condition |
|---|---|---|---|---|
| — | APPLY | APPLIED | — | Customer applies |
| APPLIED | SUITABILITY | SUITABILITY_ASSESSED | 1.0 | 1–3 business days |
| SUITABILITY_ASSESSED | APPROVE | ACTIVE | 0.95 | Same day |
| SUITABILITY_ASSESSED | REJECT | REJECTED | 0.05 | Suitability fail |
| ACTIVE | FUND | ACTIVE | — | Initial deposit |
| ACTIVE | TRADE | ACTIVE | — | Buy/sell securities (via SM-11) |
| ACTIVE | REBALANCE | ACTIVE | 0.08/month | Portfolio rebalance |
| ACTIVE | WITHDRAW | ACTIVE | 0.02/month | Partial withdrawal |
| ACTIVE | FREEZE | FROZEN | 0.0005/month | Regulatory or compliance |
| FROZEN | UNFREEZE | ACTIVE | 0.7 | After investigation |
| ACTIVE | CLOSE | CLOSED | 0.003/month | Customer-initiated |

**Account types:** BROKERAGE, RETIREMENT, MANAGED, CUSTODY

### SM-11: Securities Lifecycle (Phase 4)

**FIBO:** `fibo-sec-sec-ast:Security`, `fibo-cae-ce-act:CorporateAction`

| From | Event | To | Timing | Notes |
|---|---|---|---|---|
| — | BUY_ORDER | PENDING | Instant | Order placed |
| PENDING | EXECUTE | EXECUTED | 0–1 day | Market hours |
| EXECUTED | SETTLE | SETTLED | T+1 or T+2 | Settlement cycle |
| SETTLED | HOLD | HOLDING | — | Position in portfolio |
| HOLDING | DIVIDEND | HOLDING | — | Dividend payment (ex-date) |
| HOLDING | COUPON | HOLDING | — | Bond coupon payment |
| HOLDING | SPLIT | HOLDING | — | Stock split (adjust quantity) |
| HOLDING | MERGER | HOLDING | — | Merger (convert shares) |
| HOLDING | SELL_ORDER | SELL_PENDING | — | Sell order placed |
| SELL_PENDING | EXECUTE | SOLD | 0–1 day | Market hours |
| SOLD | SETTLE | CLOSED | T+1 or T+2 | Settlement cycle |
| HOLDING | MATURITY | CLOSED | — | Bond maturity (return principal) |

### SM-12: General Ledger / Accounting (Phase 5)

**FIBO:** `fibo-fbc-pas-caa:AccountingTransaction`

SM-12 is a **reactive state machine** — it doesn't generate events independently. Every financial event from SM-1 through SM-11 triggers a double-entry journal posting in SM-12.

| Source Event | Debit Account | Credit Account |
|---|---|---|
| Customer deposit | Cash/Bank | Customer Deposit Liability |
| Customer withdrawal | Customer Deposit Liability | Cash/Bank |
| Loan disbursement | Loan Receivable | Cash/Bank |
| Loan payment (principal) | Cash/Bank | Loan Receivable |
| Loan payment (interest) | Cash/Bank | Interest Income |
| Fee charged | Customer Deposit Liability | Fee Income |
| Interest accrued (savings) | Interest Expense | Accrued Interest Payable |
| Interest paid (savings) | Accrued Interest Payable | Customer Deposit Liability |
| Card purchase | Merchant Payable | Card Receivable |
| Card payment | Cash/Bank | Card Receivable |
| Dividend received | Cash/Bank | Investment Income |
| Trade settlement (buy) | Investment Securities | Cash/Bank |
| Trade settlement (sell) | Cash/Bank | Investment Securities |
| Provision for loan loss | Provision Expense | Loan Loss Reserve |

**Period events:**
- **End of day:** Balance calculation, interest accrual
- **End of month:** Period close, accruals, provisions
- **End of quarter:** Regulatory reporting, covenant testing

## Coupling Points (All 12 State Machines)

```
SM-1 (Consumer) ──────────┐
SM-2 (Business) ──────────┤
SM-3 (Relationships) ─────┤
                           ▼
              SM-4 (Deposit Accounts) ◄──── SM-12 (GL)
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
              SM-12 (GL) ← Every financial event
```

**Key coupling rules:**

| Trigger | Source | Target | Effect |
|---|---|---|---|
| Party ACTIVE | SM-1/SM-2 | SM-4 | Account creation enabled |
| Party CLOSED | SM-1/SM-2 | SM-4, SM-6–9 | All accounts closed, all loans settled |
| Account BLOCKED | SM-4 | SM-5 | All transactions DECLINED |
| Account DORMANT | SM-5 → SM-4 | SM-4 | No transactions for 12 months |
| Balance > threshold | SM-5 | SM-6, SM-8 | Product eligibility triggered |
| Income > threshold | SM-5 | SM-6, SM-8 | Credit eligibility triggered |
| Loan DELINQUENT | SM-6/SM-7 | SM-4 | Account BLOCKED risk |
| Loan DEFAULT | SM-6/SM-7 | SM-12 | Provision for loan loss |
| Card BLOCKED | SM-8 | SM-5 | Card transactions DECLINED |
| Investment TRADE | SM-11 | SM-12 | GL journal entry |
| Any financial event | SM-5–11 | SM-12 | Double-entry journal posting |

## 40+ Episode Types

### Tier 1: Party Episodes (6)

| # | Episode | SM | Events/Day/100 Parties | Phase |
|---|---|---|---|---|
| 1 | Consumer Onboarding | SM-1 | 0.1 | 1 |
| 2 | Business Onboarding | SM-2 | 0.05 | 3 |
| 3 | Consumer Life Event | SM-1 | 0.01–0.05 | 1 |
| 4 | Corporate Event | SM-2 | 0.005–0.02 | 3 |
| 5 | Relationship Change | SM-3 | 0.01–0.05 | 1 |
| 6 | KYC Refresh | SM-1/SM-2 | 0.005 | 1 |

### Tier 2: Account & Transaction Episodes (8)

| # | Episode | SM | Events/Day/100 Parties | Phase |
|---|---|---|---|---|
| 7 | Salary & Income | SM-5 | 3–5 (pay date) | 1 |
| 8 | Recurring Bills | SM-5 | 8–15 (bill dates) | 1 |
| 9 | Consumer Spending | SM-5 | 40–80 | 1 |
| 10 | Transfers | SM-5 | 5–10 | 1 |
| 11 | Direct Debits | SM-5 | 3–8 | 1 |
| 12 | Savings Goal | SM-4 | 2–4 (monthly) | 1 |
| 13 | Business Payments | SM-5 | 10–30 | 3 |
| 14 | Cash Management | SM-5 | 2–5 | 3 |

### Tier 3: Lending Episodes (10)

| # | Episode | SM | Events/Day/100 Parties | Phase |
|---|---|---|---|---|
| 15 | Personal Loan Lifecycle | SM-6 | 0.5–2 | 2 |
| 16 | Auto Loan Lifecycle | SM-6 | 0.2–1 | 2 |
| 17 | Student Loan Lifecycle | SM-6 | 0.1–0.5 | 2 |
| 18 | Mortgage Origination | SM-7 | 0.05–0.2 | 2 |
| 19 | Mortgage Servicing | SM-7 | 1–3 (monthly) | 2 |
| 20 | Mortgage Life Events | SM-7 | 0.01–0.05 | 2 |
| 21 | Credit Card Usage | SM-8 | 5–15 | 2 |
| 22 | Credit Card Billing | SM-8 | 1–3 (monthly) | 2 |
| 23 | Commercial Term Loan | SM-9 | 0.5–2 | 3 |
| 24 | Revolving Credit Facility | SM-9 | 1–5 | 3 |

### Tier 4: Investment Episodes (8)

| # | Episode | SM | Events/Day/100 Parties | Phase |
|---|---|---|---|---|
| 25 | Investment Account Opening | SM-10 | 0.05 | 4 |
| 26 | Equity Trading | SM-11 | 2–10 | 4 |
| 27 | Bond Trading | SM-11 | 0.5–2 | 4 |
| 28 | Fund Investment | SM-11 | 0.5–3 | 4 |
| 29 | Dividend Processing | SM-11 | 0.1–0.5 (quarterly) | 4 |
| 30 | Corporate Action | SM-11 | 0.01–0.05 | 4 |
| 31 | Portfolio Rebalancing | SM-10 | 0.05–0.2 (monthly) | 4 |
| 32 | Market Data Feed | Reference | N/A (daily prices) | 4 |

### Tier 5: Operations Episodes (8)

| # | Episode | SM | Events/Day/100 Parties | Phase |
|---|---|---|---|---|
| 33 | GL Posting | SM-12 | 1:1 with financial events | 5 |
| 34 | End-of-Day Processing | SM-12 | 1 (daily) | 5 |
| 35 | Month-End Close | SM-12 | 1 (monthly) | 5 |
| 36 | Regulatory Reporting | SM-12 | 0.01 (quarterly) | 5 |
| 37 | Fraud Detection | SM-5 | 0.01–0.05 | 1 |
| 38 | Dispute Resolution | SM-5 | 0.01–0.05 | 1 |
| 39 | Interest Rate Change | Reference | 0.01 (monthly) | 5 |
| 40 | FX Rate Update | Reference | 1 (daily) | 5 |

### Cross-Cutting Episodes

| # | Episode | SM | Phase |
|---|---|---|---|
| 41 | Spending Anomaly | SM-5 | 1 |
| 42 | Life Event (Consumer) | SM-1 | 1 |
| 43 | Fraud & Security | SM-5 | 1 |

## Execution Model

Same as v1 — daily Lakeflow Job with deterministic replay, backfill, and gap detection. The key change is the **phase-gated episode loader**:

```python
def load_episodes(locale: str, phase: int) -> list[Episode]:
    """Load only the episodes for the active phase and below."""
    all_episodes = load_all_episode_configs(locale)
    return [ep for ep in all_episodes if ep.phase <= phase]
```

**Phase configuration in Bundle 2:**

```yaml
# bundles/bundle2-generator/databricks.yml
variables:
  phase:
    default: 1  # Start with retail consumer only
    # Set to 2 for lending, 3 for commercial, 4 for investments, 5 for operations
```

## Population Design

| Phase | Parties | Accounts/Party | Products | Daily Events/100 | Backfill |
|---|---|---|---|---|---|
| 1 (Retail) | 500 consumers | 1.5 | 8–12 | 70–140 | 6 months |
| 2 (+Lending) | 500 consumers | 2.0 | 15–20 | 120–220 | 6 months |
| 3 (+Commercial) | 500 consumers + 50 businesses | 2.5 | 20–25 | 180–350 | 6 months |
| 4 (+Investments) | 500 + 50 + 100 investors | 3.0 | 25–30 | 250–500 | 12 months |
| 5 (+Operations) | Same | Same | Same | +GL entries | 12 months |

## File Structure (expanded)

```
src/generator/
├── simulate_day.py
├── backfill.py
├── engine/
│   ├── simulator.py
│   ├── state_store.py
│   ├── rng.py
│   └── phase_loader.py          # Phase-gated episode loading
├── state_machines/
│   ├── tier1_party/
│   │   ├── consumer_party.py     # SM-1
│   │   ├── business_party.py     # SM-2
│   │   └── party_relationship.py # SM-3
│   ├── tier2_accounts/
│   │   ├── deposit_account.py    # SM-4
│   │   └── transaction.py        # SM-5
│   ├── tier3_lending/
│   │   ├── consumer_loan.py      # SM-6
│   │   ├── mortgage.py           # SM-7
│   │   ├── credit_card.py        # SM-8
│   │   └── commercial_loan.py    # SM-9
│   ├── tier4_investments/
│   │   ├── investment_account.py  # SM-10
│   │   └── securities.py         # SM-11
│   ├── tier5_operations/
│   │   └── general_ledger.py     # SM-12
│   └── behavioral.py             # Behavioral state overlay
├── episodes/
│   ├── tier1/                    # 6 episode configs
│   ├── tier2/                    # 8 episode configs
│   ├── tier3/                    # 10 episode configs
│   ├── tier4/                    # 8 episode configs
│   └── tier5/                    # 8 episode configs
├── merchants/
├── names/
└── reference_data/
    ├── securities_universe.yaml  # Phase 4: stock/bond/fund catalog
    ├── interest_rates.yaml       # Phase 5: reference rate history
    └── gl_chart_of_accounts.yaml # Phase 5: GL account structure
```

## Non-Functional Requirements

| NFR | Target | Rationale |
|---|---|---|
| **Determinism** | `simulate(date, seed, locale, phase)` produces identical output | Reproducibility |
| **Phase 1 throughput** | 500 customers × ~1.2 events/customer = ~600 events in < 5 min | Demo SLA |
| **Phase 5 throughput** | 650 parties × ~5 events/party = ~3,250 events in < 15 min | Full-spectrum demo |
| **Backfill (Phase 1)** | 6 months × 500 customers = ~108K events in < 30 min | POC setup |
| **Backfill (Phase 5)** | 12 months × 650 parties = ~1.2M events in < 2 hours | Full-spectrum setup |
| **Phase independence** | Each phase adds SMs and episodes without changing existing ones | Incremental deployment |

## Testing

| Test | What It Validates |
|---|---|
| **Phase gating** | Phase 1 generates only Tier 1+2 events; Phase 2 adds Tier 3; etc. |
| **SM coupling** | Account BLOCKED → transactions DECLINED; loan DEFAULT → GL provision |
| **GL double-entry** | Every financial event produces a balanced journal entry (debits = credits) |
| **Mortgage amortization** | Monthly payments correctly split between principal and interest |
| **Credit card billing** | Statement balance, minimum payment, interest charge calculated correctly |
| **Investment settlement** | T+1/T+2 settlement timing correct; holdings updated after settlement |
| **Deterministic replay** | Same (date, seed, locale, phase) → identical output |
| **Locale correctness** | NL: EUR/IBAN/SEPA; US: USD/routing/ACH; GB: GBP/sort code/FPS |

## Deployment

Same as v1 — Bundle 2 (Data Generator), dev/demo only. The `phase` variable controls which tiers are active.

## Open Questions

| # | Question | Impact | Resolution Path |
|---|---|---|---|
| Q14 | Backfill performance at Phase 5 scale (1.2M events) | Setup time | Benchmark; optimize with repartitioning |
| Q15 | Determinism across Spark workers | Core principle | Validate with identical runs on different cluster sizes |
| Q34 | Should the securities universe (Phase 4) use real tickers or synthetic? | Realism vs. licensing | Synthetic tickers with realistic price patterns; option to load real market data |
| Q35 | Should GL posting (Phase 5) be synchronous (same event) or asynchronous (separate job)? | Latency vs. consistency | Synchronous for correctness; GL entries generated in the same simulation step |

## References

- **L200-C2 v1** — Retail consumer scope (notebooks/308703764868243)
- **Research 07** — Full-Spectrum FIBO Generator (notebooks/308703765046744)
- **Semantics 02** — 108 glossary terms (notebooks/308703765065096)
- **L100 v4** — System Overview (notebooks/1987168172366090)
