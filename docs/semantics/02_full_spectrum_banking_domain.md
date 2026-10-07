# Semantics 02: Full-Spectrum Banking Domain — UC Pages Candidates

> **Status:** Draft — Oct 7, 2026
> **Author:** Matthew Giglia
> **File:** docs/semantics/02_full_spectrum_banking_domain.md
> **Format:** Structured for Unity Catalog Domains, Subdomains, and Pages
> **Source:** FIBO 2025 Q4 + Research 07 (Full-Spectrum Generator) + Semantics 01 (32 retail terms)
> **Supersedes:** Semantics 01 (which covered retail consumer only — 6 subdomains, 32 terms)

## UC Domain

**Domain:** Banking
**Description:** Business concepts, metrics, and terminology for full-service banking — consumer accounts, commercial accounts, lending, mortgages, credit cards, investments, wealth management, and bank operations. Sourced from FIBO (Financial Industry Business Ontology) 2025 Q4 and adapted for UC Semantics with locale-specific terminology (EN, EN-GB, NL). Covers all 5 tiers of the Conversational Consumer Finance reference architecture.

## UC Subdomains (12)

| # | Subdomain | Description | FIBO Module | Silver Tables | Phase |
|---|---|---|---|---|---|
| 1 | **Parties & Identity** | Customers, businesses, legal entities, identity verification, KYC/AML | FND Parties, BE LegalEntities | party, person, organization, party_identifier, party_kyc | 1 |
| 2 | **Addresses & Contacts** | Physical addresses, email, phone, contact management | FND Places/Addresses, FND Places/VirtualPlaces | party_address, party_contact | 1 |
| 3 | **Accounts** | Bank accounts, account types, lifecycle, identifiers, statements | FBC ClientsAndAccounts | account, account_identifier, account_statement | 1 |
| 4 | **Transactions** | Account postings, payment types, merchant categories, settlement, status | FBC ClientsAndAccounts, FND Accounting | account_transaction | 1 |
| 5 | **Balances** | Account balances, balance types, snapshots | FBC ClientsAndAccounts, FND CashFlows | account_balance | 1 |
| 6 | **Payments** | Credit transfers, direct debits, payment schemes (SEPA/ACH/FPS) | FND PaymentsAndSchedules | account_transaction (payment_scheme) | 1 |
| 7 | **Products & Services** | Banking products, eligibility, rates, fees, product lifecycle | FBC ProductsAndServices | product | 1 |
| 8 | **Consumer Lending** | Personal loans, auto loans, student loans, HELOC, repayment, delinquency | LOAN LoansGeneral, LOAN LoansSpecific | loan, loan_payment, loan_event | 2 |
| 9 | **Mortgage & Real Estate** | Mortgage origination, servicing, property valuation, escrow | LOAN RealEstateLoans | mortgage, mortgage_property | 2 |
| 10 | **Credit Cards** | Card accounts, billing, rewards, disputes, chargebacks | LOAN LoansSpecific/CardAccounts | credit_card, credit_card_statement | 2 |
| 11 | **Investments & Wealth** | Brokerage, securities, holdings, trades, dividends, corporate actions | SEC, DER, IND, MD | investment_account, security, holding, trade, corporate_action, market_data_daily | 4 |
| 12 | **Bank Operations** | General ledger, accounting, regulatory reporting, reference rates | FBC DebtAndEquities, FND Accounting, IND | gl_journal_entry, gl_account, regulatory_report, interest_rate_reference | 5 |

**Cross-cutting subdomains** (from Semantics 01, unchanged):
- **Customer Behavior** — spending patterns, anomalies, trends, segments (behavioral, not FIBO)
- **Security & Compliance** — consumer GUID, session tokens, consent, GDPR (implementation, not FIBO)

## UC Pages — Full Glossary (95 terms)

---

### Subdomain 1: Parties & Identity (12 terms)

| # | Term (EN) | Term (NL) | FIBO Source | Priority | Phase | Data Usage |
|---|---|---|---|---|---|---|
| 1 | Account Balance | Saldo | fibo-fbc-pas-caa:Balance | High | 1 | silver.account_balance.amount |
| 2 | Payment Account | Betaalrekening | TransactionDepositAccount | High | 1 | silver.account.account_type = 'PAYMENT' |
| 3 | Savings Account | Spaarrekening | NonTransactionDepositAccount | High | 1 | silver.account.account_type = 'SAVINGS' |
| 4 | Account Holder | Rekeninghouder | fibo-fbc-pas-caa:CustomerAccountHolder | Medium | 1 | silver.party_relationship.relationship_type |
| 5 | Customer Segment | Klantsegment | Extension | Medium | 1 | silver.party.customer_segment |
| 6 | KYC (Know Your Customer) | KYC | Extension (AML/KYC) | Medium | 1 | silver.party_kyc.kyc_status |
| 7 | Legal Entity | Rechtspersoon | fibo-be-le-fbo:FormalOrganization | Medium | 3 | silver.organization.legal_form |
| 8 | Beneficial Owner | Uiteindelijk Belanghebbende (UBO) | Extension | Medium | 3 | silver.party_relationship.relationship_type = 'BENEFICIAL_OWNER' |
| 9 | Politically Exposed Person (PEP) | Politiek Prominent Persoon (PEP) | Extension | Low | 1 | silver.party_kyc.pep_flag |
| 10 | Tax Identifier | Fiscaal Identificatienummer | fibo-fnd-pty-pty:hasTaxIdentifier | Medium | 1 | silver.party_identifier.identifier_type = 'TAX_ID' |
| 11 | LEI (Legal Entity Identifier) | LEI | cmns-id:Identifier | Low | 3 | silver.party_identifier.identifier_type = 'LEI' |
| 12 | Authorized Signer | Gemachtigde | Extension | Medium | 3 | silver.party_relationship.relationship_type = 'AUTHORIZED_SIGNER' |

### Subdomain 2: Addresses & Contacts (4 terms)

| # | Term (EN) | Term (NL) | FIBO Source | Priority | Phase | Data Usage |
|---|---|---|---|---|---|---|
| 13 | Mailing Address | Postadres | fibo-fnd-pty-pty:hasMailingAddress | Medium | 1 | silver.party_address.address_type = 'MAILING' |
| 14 | Residential Address | Woonadres | fibo-fnd-plc-adr:PhysicalAddress | Medium | 1 | silver.party_address.address_type = 'RESIDENTIAL' |
| 15 | Contact Verification | Contactverificatie | Extension | Low | 1 | silver.party_contact.is_verified |
| 16 | Address Type | Adrestype | Extension | Low | 1 | silver.party_address.address_type |

### Subdomain 3: Accounts (12 terms)

| # | Term (EN) | Term (NL) | FIBO Source | Priority | Phase | Data Usage |
|---|---|---|---|---|---|---|
| 17 | IBAN | IBAN | InternationalBankAccountIdentifier | Medium | 1 | silver.account_identifier.identifier_type = 'IBAN' |
| 18 | Account Status | Rekeningsstatus | fibo-fnd-arr-lif:hasStage | Medium | 1 | silver.account.account_status |
| 19 | Account Identifier | Rekeningidentificatie | fibo-fbc-pas-caa:AccountIdentifier | Medium | 1 | silver.account_identifier |
| 20 | Account Statement | Rekeningafschrift | fibo-fbc-pas-caa:AccountStatement | High | 1 | silver.account_statement |
| 21 | Opening Balance | Beginsaldo | fibo-fbc-pas-caa:hasStartingBalance | Medium | 1 | silver.account_statement.opening_balance |
| 22 | Closing Balance | Eindsaldo | fibo-fbc-pas-caa:hasEndingBalance | Medium | 1 | silver.account_statement.closing_balance |
| 23 | Operating Account | Bedrijfsrekening | Extension (DepositAccount) | Medium | 3 | silver.account.account_type = 'OPERATING' |
| 24 | Payroll Account | Salarisrekening | Extension (DepositAccount) | Low | 3 | silver.account.account_type = 'PAYROLL' |
| 25 | Escrow Account | Derdenrekening | Extension | Low | 3 | silver.account.account_type = 'ESCROW' |
| 26 | Term Deposit | Termijndeposito | CertificateOfDeposit | Medium | 1 | silver.account.account_type = 'TERM_DEPOSIT' |
| 27 | Dormant Account | Slapende Rekening | Extension | Low | 1 | silver.account.account_status = 'DORMANT' |
| 28 | Account Closure | Rekeningopzegging | Extension | Low | 1 | silver.account.account_status = 'CLOSED' |

### Subdomain 4: Transactions (11 terms)

| # | Term (EN) | Term (NL) | FIBO Source | Priority | Phase | Data Usage |
|---|---|---|---|---|---|---|
| 29 | Credit Transfer | Overschrijving | Payment transaction / SCT | High | 1 | silver.account_transaction.transaction_type = 'CREDIT_TRANSFER' |
| 30 | Direct Debit | Incasso | SDD Core | High | 1 | silver.account_transaction.transaction_type = 'DIRECT_DEBIT' |
| 31 | Monthly Spending | Maandelijkse Uitgaven | Extension | High | 1 | Metric view measure: monthly_spend |
| 32 | Transaction Category | Transactiecategorie | Extension | High | 1 | silver.account_transaction.merchant_category |
| 33 | Posting Date | Boekingsdatum | fibo-fbc-pas-caa:hasPostingDate | Medium | 1 | silver.account_transaction.posting_date |
| 34 | Transaction Direction | Af-/Bijschrijving | Extension | Medium | 1 | silver.account_transaction.direction |
| 35 | Counterparty | Tegenrekening | Extension | Medium | 1 | silver.account_transaction.counterparty_iban |
| 36 | Remittance Information | Mededeling | Extension | Low | 1 | silver.account_transaction.remittance_info |
| 37 | Transaction Status | Transactiestatus | fibo-fnd-arr-lif:hasStage | Medium | 1 | silver.account_transaction.transaction_status |
| 38 | Settlement Date | Verrekeningsdatum | Extension | Low | 1 | silver.account_transaction.settlement_date |
| 39 | Authorization Code | Autorisatiecode | Extension | Low | 1 | silver.account_transaction.authorization_code |

### Subdomain 5: Balances (4 terms)

| # | Term (EN) | Term (NL) | FIBO Source | Priority | Phase | Data Usage |
|---|---|---|---|---|---|---|
| 1 | (Account Balance — see #1 above) | | | | | |
| 40 | Available Balance | Beschikbaar Saldo | Extension (Balance subtype) | High | 1 | silver.account_balance.balance_type = 'AVAILABLE' |
| 41 | Ledger Balance | Boeksaldo | Extension (Balance subtype) | Medium | 1 | silver.account_balance.balance_type = 'LEDGER' |
| 42 | Pending Balance | Saldo in Behandeling | Extension | Medium | 1 | silver.account_balance.balance_type = 'PENDING' |
| 43 | Overdraft | Roodstand | Extension | Medium | 1 | silver.account_balance.balance_type = 'OVERDRAFT' |

### Subdomain 6: Payments (4 terms — unchanged from Semantics 01)

| # | Term (EN) | Term (NL) | FIBO Source | Priority | Phase | Data Usage |
|---|---|---|---|---|---|---|
| 44 | SEPA Credit Transfer (SCT) | SEPA Overschrijving | SCT | High | 1 | payment_scheme = 'SCT' |
| 45 | SEPA Instant (SCT Inst) | Instantoverschrijving | SCT Inst | High | 1 | payment_scheme = 'SCT_INST' |
| 46 | SEPA Direct Debit (SDD Core) | SEPA Incasso | SDD Core | High | 1 | payment_scheme = 'SDD_CORE' |
| 47 | Payment Scheme | Betaalschema | FND PaymentsAndSchedules | High | 1 | silver.account_transaction.payment_scheme |

### Subdomain 7: Products & Services (7 terms)

| # | Term (EN) | Term (NL) | FIBO Source | Priority | Phase | Data Usage |
|---|---|---|---|---|---|---|
| 48 | Product Type | Producttype | fibo-fbc-pas-fpas:FinancialProduct | Medium | 1 | silver.product.product_type |
| 49 | Product Eligibility | Productgeschiktheid | Extension | High | 1 | Product SM: ELIGIBLE state |
| 50 | Credit Utilization | Kredietbenutting | Extension | Medium | 2 | Metric view measure |
| 51 | Interest Accrual | Renteopbouw | Extension | Medium | 1 | Episode 6: quarterly interest |
| 52 | Credit Limit | Kredietlimiet | fibo-fbc-dae-dbt:hasCreditLimit | High | 2 | silver.product.credit_limit |
| 53 | Annual Fee | Jaarlijkse Kosten | Extension | Medium | 2 | silver.product.annual_fee |
| 54 | Grace Period | Rentevrije Periode | Extension | Low | 2 | silver.product.grace_period_days |

### Subdomain 8: Consumer Lending (12 terms)

| # | Term (EN) | Term (NL) | FIBO Source | Priority | Phase | Data Usage |
|---|---|---|---|---|---|---|
| 55 | Loan | Lening | fibo-loan-ln-ln:Loan | High | 2 | silver.loan |
| 56 | Principal | Hoofdsom | fibo-fbc-dae-dbt:hasPrincipal | High | 2 | silver.loan.principal_amount |
| 57 | Interest Rate | Rentepercentage | fibo-fbc-dae-dbt:hasInterestRate | High | 2 | silver.loan.interest_rate |
| 58 | Maturity Date | Einddatum | fibo-fbc-dae-dbt:hasMaturityDate | Medium | 2 | silver.loan.maturity_date |
| 59 | Amortization | Aflossing | Extension | Medium | 2 | silver.loan_payment (principal portion) |
| 60 | Loan Balance | Uitstaand Saldo | fibo-loan-ln-ln:hasLoanBalance | High | 2 | silver.loan.current_balance |
| 61 | Delinquency | Betalingsachterstand | Extension | Medium | 2 | silver.loan.loan_status = 'DELINQUENT' |
| 62 | Default | Wanbetaling | Extension | Medium | 2 | silver.loan.loan_status = 'DEFAULT' |
| 63 | Forbearance | Betalingsuitstel | Extension | Low | 2 | silver.loan_event.event_type = 'FORBEARANCE' |
| 64 | Collateral | Onderpand | fibo-fbc-dae-dbt:isCollateralizedBy | Medium | 2 | silver.loan.collateral_type |
| 65 | Loan-to-Value (LTV) | Loan-to-Value | Extension | Medium | 2 | silver.mortgage.ltv_ratio |
| 66 | Consumer Loan | Consumptief Krediet | fibo-loan-spc-cns:ConsumerLoan | High | 2 | silver.loan.loan_type IN ('PERSONAL','AUTO','STUDENT') |

### Subdomain 9: Mortgage & Real Estate (8 terms)

| # | Term (EN) | Term (NL) | FIBO Source | Priority | Phase | Data Usage |
|---|---|---|---|---|---|---|
| 67 | Mortgage | Hypotheek | fibo-loan-reln-mtg:Mortgage | High | 2 | silver.mortgage |
| 68 | Mortgage Type | Hypotheektype | owl:subClassOf | Medium | 2 | silver.mortgage.mortgage_type |
| 69 | Escrow | Escrow / Derdenrekening | Extension | Medium | 2 | silver.mortgage.escrow_amount |
| 70 | Appraisal | Taxatie | Extension | Medium | 2 | silver.mortgage.appraisal_value |
| 71 | Property Valuation | Woningwaarde | Extension | Medium | 2 | silver.mortgage_property.valuation_amount |
| 72 | Refinance | Oversluiten | Extension | Low | 2 | Mortgage SM: REFINANCE event |
| 73 | Foreclosure | Executieverkoop | Extension | Low | 2 | Mortgage SM: FORECLOSURE event |
| 74 | ARM (Adjustable Rate) | Variabele Rente Hypotheek | Extension | Medium | 2 | silver.mortgage.mortgage_type = 'ARM' |

### Subdomain 10: Credit Cards (8 terms)

| # | Term (EN) | Term (NL) | FIBO Source | Priority | Phase | Data Usage |
|---|---|---|---|---|---|---|
| 75 | Credit Card | Creditcard | fibo-loan-spc-crd:CreditCard | High | 2 | silver.credit_card |
| 76 | Billing Cycle | Factureringsperiode | Extension | Medium | 2 | silver.credit_card.billing_cycle_day |
| 77 | Minimum Payment | Minimale Betaling | Extension | High | 2 | silver.credit_card_statement.minimum_payment |
| 78 | Statement Balance | Afschriftsaldo | fibo-fbc-pas-caa:hasEndingBalance | High | 2 | silver.credit_card_statement.statement_balance |
| 79 | Cash Advance | Geldopname | Extension | Low | 2 | transaction_type = 'CASH_ADVANCE' |
| 80 | Rewards | Beloningen / Punten | Extension | Medium | 2 | silver.credit_card.rewards_program |
| 81 | Chargeback | Terugboeking | Extension | Medium | 2 | Dispute SM event |
| 82 | Card Status | Kaartstatus | fibo-fnd-arr-lif:hasStage | Medium | 2 | silver.credit_card.card_status |

### Subdomain 11: Investments & Wealth (12 terms)

| # | Term (EN) | Term (NL) | FIBO Source | Priority | Phase | Data Usage |
|---|---|---|---|---|---|---|
| 83 | Security | Effect | fibo-sec-sec-ast:Security | High | 4 | silver.security |
| 84 | ISIN | ISIN | fibo-sec-sec-id:hasISIN | Medium | 4 | silver.security.isin |
| 85 | Portfolio | Portefeuille | Extension | High | 4 | silver.investment_account + silver.holding |
| 86 | Holding | Positie | Extension | High | 4 | silver.holding |
| 87 | Trade | Transactie (Beurs) | fibo-fnd-txn-sec:SecuritiesTransaction | High | 4 | silver.trade |
| 88 | Dividend | Dividend | fibo-cae-ce-act:CorporateAction | High | 4 | silver.corporate_action.action_type = 'DIVIDEND' |
| 89 | Stock Split | Aandelensplitsing | fibo-cae-ce-act:CorporateAction | Medium | 4 | silver.corporate_action.action_type = 'SPLIT' |
| 90 | NAV (Net Asset Value) | Intrinsieke Waarde | Extension | Medium | 4 | Calculated from holdings |
| 91 | Cost Basis | Kostprijs | Extension | Medium | 4 | silver.holding.cost_basis |
| 92 | Unrealized Gain/Loss | Ongerealiseerde Winst/Verlies | Extension | Medium | 4 | silver.holding.unrealized_gain_loss |
| 93 | Settlement (T+1/T+2) | Afwikkeling | Extension | Low | 4 | silver.trade.settlement_date |
| 94 | Corporate Action | Kapitaalactie | fibo-cae-ce-act:CorporateAction | Medium | 4 | silver.corporate_action |

### Subdomain 12: Bank Operations (6 terms)

| # | Term (EN) | Term (NL) | FIBO Source | Priority | Phase | Data Usage |
|---|---|---|---|---|---|---|
| 95 | General Ledger | Grootboek | fibo-fbc-pas-caa:GeneralLedger | Medium | 5 | silver.gl_journal_entry |
| 96 | Journal Entry | Journaalpost | fibo-fbc-pas-caa:AccountingTransaction | Medium | 5 | silver.gl_journal_entry |
| 97 | Chart of Accounts | Rekeningschema | Extension | Low | 5 | silver.gl_account |
| 98 | Reference Rate | Referentierente | fibo-ind-ir-ir:ReferenceInterestRate | High | 5 | silver.interest_rate_reference |
| 99 | Regulatory Report | Toezichtrapportage | Extension | Low | 5 | silver.regulatory_report |
| 100 | Accounting Period | Boekperiode | Extension | Low | 5 | silver.gl_journal_entry.period |

### Cross-Cutting: Customer Behavior (4 terms — unchanged from Semantics 01)

| # | Term (EN) | Term (NL) | Priority | Phase |
|---|---|---|---|---|
| 101 | Spending Trend (MoM) | Bestedingstrend | High | 1 |
| 102 | Spending Anomaly | Bestedingsanomalie | Medium | 1 |
| 103 | Customer Behavior State | Gedragsstatus | Low | 1 |
| 104 | Proactive Insight | Proactief Inzicht | Medium | 1 |

### Cross-Cutting: Security & Compliance (4 terms — unchanged from Semantics 01)

| # | Term (EN) | Term (NL) | Priority | Phase |
|---|---|---|---|---|
| 105 | Consumer GUID | Consumer GUID | High | 1 |
| 106 | Session Token | Sessietoken | Low | 1 |
| 107 | Consent State | Toestemmingsstatus | Medium | 1 |
| 108 | GDPR Right to Erasure | Recht op Vergetelheid | Medium | 1 |

## Summary

| Metric | Semantics 01 | Semantics 02 | Delta |
|---|---|---|---|
| **Domain** | Consumer Banking | **Banking** | Renamed |
| **Subdomains** | 6 | **12** (+2 cross-cutting) | +6 new |
| **UC Page candidates** | 32 | **108** | +76 new |
| **High priority** | 14 | **35** | +21 |
| **Medium priority** | 13 | **48** | +35 |
| **Low priority** | 5 | **25** | +20 |
| **Phase 1 terms** | 32 | **60** | +28 |
| **Phase 2 terms** | 0 | **32** | +32 |
| **Phase 3 terms** | 0 | **6** | +6 |
| **Phase 4 terms** | 0 | **12** | +12 |
| **Phase 5 terms** | 0 | **6** | +6 |

## Tagging Strategy

| Priority | Count | Action |
|---|---|---|
| **High** | 35 | Create UC Pages immediately for the active phase; include in Genie Agent instructions |
| **Medium** | 48 | Create UC Pages when the phase is greenlit; include in Genie Agent knowledge store |
| **Low** | 25 | Document as internal/technical terms; create UC Pages if time permits |

## Implementation Notes

- UC Pages should be authored in the locale language (EN, EN-GB, or NL) based on the deployment locale
- Each Page should link to the metric view measure or dimension it defines
- Pages marked "Certified" become the authoritative source for Genie Ontology's OntoRank
- The FIBO source provides the semantic lineage — "this definition is grounded in the W3C financial ontology"
- **Phase gating:** Only create Pages for terms in the active phase. Phase 2+ terms are documented here but not deployed until their phase is greenlit.
- **Genie Code input:** This glossary is the primary input for Genie Code when generating metric views — having all 108 terms defined accelerates every future phase.
