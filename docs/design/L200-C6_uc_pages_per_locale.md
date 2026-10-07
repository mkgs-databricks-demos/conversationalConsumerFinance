# L200-C6: UC Pages per Locale — Detailed Design

> **Status:** Draft v2 — Oct 7, 2026
> **Author:** Matthew Giglia
> **Parent:** L100 — Conversational Consumer Finance: System Overview
> **Component:** C6 — UC Pages per Locale (Layer 3: Semantic Layer)
> **Priority:** P1
> **Bundle:** Bundle 3 (Application — all environments)

## Overview

UC Pages provide **business term definitions** in the locale language that Genie Agents use to understand domain terminology. When a consumer asks "Wat is een incasso?" (What is a direct debit?), the Genie Agent retrieves the Dutch UC Page definition to formulate an accurate, contextual response. Pages are the semantic glue between FIBO ontology concepts and consumer-facing natural language.

This L200 codifies the **60 Phase 1 glossary terms** from **Semantics 02** (canvas notebooks/308703765065096) into a deployable UC Pages strategy with locale-specific authoring, certification workflow, and Genie Agent integration. Semantics 02 supersedes Semantics 01 and covers the expanded party model, account identifiers, account statements, and additional balance/transaction/product terms identified in the FIBO gap analysis.

## Dependencies

| Dependency | Component | What It Provides | Status |
|---|---|---|---|
| **Semantics Doc** | Semantics 02 | 60 Phase 1 glossary terms (108 total across all phases) with definitions, FIBO sources, locale variants | Complete |
| **Locale Config** | C1 | Language code for page authoring (en, en-GB, nl) | Design complete (L200-C1) |
| **Metric Views** | C5 | Pages link to the metric view measures/dimensions they define | Design complete (L200-C5) |

## Design

### Page Inventory (32 terms across 6 subdomains)

| Subdomain | Terms | Priority High | Priority Medium | Priority Low |
|---|---|---|---|---|
| **Parties & Identity** | 12 | 3 | 6 | 3 |
| **Addresses & Contacts** | 4 | 0 | 2 | 2 |
| **Accounts** | 12 | 4 | 5 | 3 |
| **Transactions** | 11 | 4 | 4 | 3 |
| **Balances** | 4 | 1 | 3 | 0 |
| **Payments** | 4 | 4 | 0 | 0 |
| **Products & Services** | 7 | 2 | 3 | 2 |
| **Customer Behavior** | 4 | 1 | 2 | 1 |
| **Security & Compliance** | 4 | 1 | 1 | 2 |
| **Total (Phase 1)** | **60** | **20** | **26** | **14** |

See **Semantics 02** (canvas notebooks/308703765065096) for the full term definitions with FIBO sources and locale variants. Phases 2–5 add 48 more terms (108 total).

### Page Structure (per term)

Each UC Page follows a standard structure, authored in the locale language:

```markdown
# {Term in locale language}

## Definition
{One-paragraph definition in locale language}

## Business Context
{How this term is used in consumer banking; what consumers need to know}

## Data Usage
- **Table:** {silver.table_name.column_name}
- **Metric View Measure/Dimension:** {gold.metric_view.field_name}
- **Values:** {enumerated values if applicable}

## Related Terms
- {Related term 1} (link to its UC Page)
- {Related term 2}

## FIBO Source
- **Concept:** {FIBO class name}
- **Module:** {FIBO module (FBC, FND, LOAN)}
- **IRI:** {FIBO IRI if available}

## Locale Variants
| Locale | Term | Synonyms |
|---|---|---|
| EN | {English term} | {English synonyms} |
| EN-GB | {British term} | {British synonyms} |
| NL | {Dutch term} | {Dutch synonyms} |
```

### Example: Direct Debit / Incasso (NL locale)

```markdown
# Incasso

## Definitie
Een door de crediteur geïnitieerde afschrijving van de betaalrekening van de
debiteur, geautoriseerd door een machtiging. De debiteur geeft vooraf toestemming
aan de crediteur om bedragen af te schrijven.

## Zakelijke Context
Incasso's worden gebruikt voor terugkerende betalingen zoals huur, energie,
verzekeringen en abonnementen. Onder SEPA SDD Core heeft de consument het recht
om een incasso onvoorwaardelijk te storneren binnen 8 weken na afschrijving.
Bij ongeautoriseerde incasso's geldt een termijn van 13 maanden.

## Datagebruik
- **Tabel:** silver.account_transaction.transaction_type = 'DIRECT_DEBIT'
- **Betaalschema:** silver.account_transaction.payment_scheme = 'SDD_CORE'
- **Metric View:** gold.customer_transaction_metrics (direction = 'DEBIT')

## Gerelateerde Termen
- Overschrijving (Credit Transfer)
- Stornering (Reversal)
- Machtiging (Mandate)
- SEPA

## FIBO Bron
- **Concept:** SDD Core
- **Module:** FND/PaymentsAndSchedules
```

### Deployment Strategy

Pages are authored as markdown files per locale and deployed via the UC Pages API or Catalog Explorer:

```
src/semantic_layer/pages/
├── en/                          # US English pages
│   ├── accounts/
│   │   ├── account_balance.md
│   │   ├── checking_account.md
│   │   ├── savings_account.md
│   │   └── ...
│   ├── transactions/
│   ├── payments/
│   ├── products/
│   ├── behavior/
│   └── security/
├── en-GB/                       # British English pages
│   ├── accounts/
│   │   ├── account_balance.md
│   │   ├── current_account.md   # "current account" not "checking account"
│   │   └── ...
│   └── ...
└── nl/                          # Dutch pages
    ├── accounts/
    │   ├── saldo.md
    │   ├── betaalrekening.md
    │   ├── spaarrekening.md
    │   └── ...
    └── ...
```

### Certification Workflow

| Phase | Action | Who |
|---|---|---|
| **Draft** | Pages authored from FIBO definitions + Semantics 01 | Genie Code (assisted) or FDE |
| **Review** | Domain expert validates definitions against banking regulations | Customer SME or FDE |
| **Certified** | Page marked as Certified in UC | Domain owner |
| **Active** | Genie Agent uses Certified pages for OntoRank scoring | Automatic |

Pages marked **Certified** become the authoritative source for Genie Ontology's OntoRank — they influence how Genie prioritizes and interprets terms.

### Genie Agent Integration

UC Pages are automatically available to Genie Agents that have access to the same catalog. No manual configuration needed — Genie discovers Pages via UC metadata.

When a consumer asks a definitional question ("What is a direct debit?"), Genie can:
1. Retrieve the UC Page definition
2. Formulate a response in the locale language
3. Cite the Page as the source

## Non-Functional Requirements

| NFR | Target | Rationale |
|---|---|---|
| **Locale completeness** | All 20 High-priority Phase 1 terms have Pages in all 3 locales | Consumer experience |
| **FIBO traceability** | Every Page links to its FIBO source concept | Semantic lineage |
| **Certification** | All High-priority Pages certified before POC demo | Genie OntoRank accuracy |
| **Consistency** | Same term has consistent definitions across locales (translated, not rewritten) | Cross-locale coherence |

## Testing

| Test | What It Validates |
|---|---|
| **Page creation** | All 32 Pages create successfully in UC |
| **Locale coverage** | Each locale has Pages for all 14 High-priority terms |
| **Genie discovery** | Genie Agent can retrieve Page definitions when asked definitional questions |
| **Language accuracy** | Dutch Pages use correct banking terminology (validated by native speaker or Genie Code) |
| **FIBO linkage** | Each Page's FIBO source is accurate (spot-check against FIBO spec) |
| **Certification** | Certified Pages influence Genie OntoRank scoring |

## Deployment

Part of **Bundle 3 (Application)** — deployed after metric views (C5) so Pages can reference metric view measures.

```yaml
# bundles/bundle3-app/databricks.yml
resources:
  jobs:
    deploy_semantic_layer:
      tasks:
        - task_key: deploy_metric_views
          # ... (from L200-C5)
        - task_key: deploy_uc_pages
          depends_on:
            - task_key: deploy_metric_views
          notebook_task:
            notebook_path: src/semantic_layer/deploy_pages
            base_parameters:
              locale: ${var.locale}
              catalog: ccf_${var.locale}
```

## Open Questions

| # | Question | Impact | Resolution Path |
|---|---|---|---|
| — | Can UC Pages be created programmatically via API, or only through Catalog Explorer? | Affects deployment automation | Research UC Pages API; fallback: Genie Code session to create Pages interactively |
| — | Do Certified Pages need to be re-certified when the definition is updated? | Affects maintenance workflow | Check UC certification lifecycle docs |

## References

- **Semantics 01** — Consumer Banking Domain (canvas notebooks/308703764881431) — 32 glossary terms
- **L200-C5** — Metric Views (canvas notebooks/308703764929801) — Pages link to metric view fields
- **L200-C1** — Locale Config (canvas notebooks/308703764929903) — language code for page authoring
- **L100 v3** — UC Pages section (canvas notebooks/1987168172366090)
