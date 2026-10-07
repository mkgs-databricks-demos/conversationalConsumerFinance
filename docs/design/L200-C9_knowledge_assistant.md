# L200-C9: Knowledge Assistant — Detailed Design

> **Status:** Draft v1 — Oct 6, 2026
> **Author:** Matthew Giglia
> **Parent:** L100 — Conversational Consumer Finance: System Overview
> **Component:** C9 — Knowledge Assistant (Layer 4)
> **Priority:** P2
> **Bundle:** Bundle 3 (Application — all environments)

## Overview

The Knowledge Assistant answers consumer questions about **unstructured content** — product documentation, eligibility rules, fee schedules, FAQ pages, and regulatory disclosures. It uses the **Genie Agent volumes feature** (Beta), which allows a Genie Agent to analyze files stored in UC Volumes (PDFs, Word docs, slide decks) alongside structured data in a single conversation. :citation[documentation."https://learn.microsoft.com/en-us/azure/databricks/genie-agents/volumes/",Analyze files in volumes with a Genie Agent]

### Key Finding: Genie Agent Volumes Replaces Custom RAG

The original L100 design assumed a separate Knowledge Assistant component with custom Vector Search and retrieval logic. The Genie Agent volumes feature eliminates this — a single Genie Agent can query both structured metric views AND unstructured documents in UC Volumes. No custom RAG pipeline needed.

**Architecture simplification:**
- ~~Custom Vector Search index~~ → Genie Agent volumes (managed retrieval)
- ~~Custom embedding pipeline~~ → Genie handles file analysis natively
- ~~Separate Knowledge Assistant endpoint~~ → Attach volumes to existing Genie Agents

## Dependencies

| Dependency | Component | What It Provides | Status |
|---|---|---|---|
| **Genie Agents** | C7 | Agents to attach volumes to | Design complete (L200-C7) |
| **UC Volumes** | Bundle 1 | Volume storage for product documentation | Infrastructure |

## Design

### Volume Structure

```
/Volumes/${catalog}/knowledge/
├── product_docs/           # Product brochures, terms & conditions
│   ├── checking_account.pdf
│   ├── savings_account.pdf
│   ├── credit_card_terms.pdf
│   └── personal_loan_guide.pdf
├── faq/                    # Frequently asked questions
│   ├── account_faq.pdf
│   ├── payments_faq.pdf
│   └── security_faq.pdf
├── fee_schedules/          # Fee and rate schedules
│   ├── current_fees.pdf
│   └── interest_rates.pdf
└── regulatory/             # Regulatory disclosures
    ├── privacy_policy.pdf
    └── terms_of_service.pdf
```

### Agent Configuration

Attach the knowledge volume to the Products Agent (or create a dedicated Knowledge Agent):

```python
# Option A: Attach volumes to existing Products Agent
# Via Management API or Genie Agent UI:
# Sources tab → Add → Select volume → Add description

# Volume description (critical for retrieval accuracy):
volume_descriptions = {
    "product_docs": "Product brochures and terms for checking accounts, savings accounts, "
                    "credit cards, and personal loans. Use when consumers ask about product "
                    "features, eligibility, or terms and conditions.",
    "faq": "Frequently asked questions about accounts, payments, and security. "
           "Use when consumers ask 'how do I...' or 'what happens if...' questions.",
    "fee_schedules": "Current fee schedules and interest rates. "
                     "Use when consumers ask about fees, charges, or interest rates.",
    "regulatory": "Privacy policy and terms of service. "
                  "Use when consumers ask about data privacy or legal terms."
}
```

### Locale-Specific Content

Each locale has its own volume with locale-appropriate documents:

| Locale | Volume Path | Content Language | Regulatory Framework |
|---|---|---|---|
| US | `/Volumes/ccf_us/knowledge/` | English | CFPB, Reg E, TILA |
| GB | `/Volumes/ccf_gb/knowledge/` | British English | FCA, PSD2 |
| NL | `/Volumes/ccf_nl/knowledge/` | Dutch | AFM, DNB, PSD2, SEPA |

### How It Works

When a consumer asks a knowledge question (e.g., "What are the fees for my savings account?"):

1. The orchestrator (C8) classifies the intent as KNOWLEDGE
2. Routes to the Genie Agent with volumes attached
3. Genie Agent mode retrieves relevant file content from the volume
4. Genie reasons over the file content + structured data to generate an answer
5. Response includes citations pointing to the specific page of the source file

**No custom code needed** — Genie handles retrieval, reasoning, and citation natively.

## Non-Functional Requirements

| NFR | Target | Rationale |
|---|---|---|
| **Retrieval accuracy** | Relevant document retrieved for ≥85% of knowledge questions | Consumer experience |
| **Citation accuracy** | Citations point to the correct source file and page | Trust and verifiability |
| **Volume limit** | ≤10 volumes per agent | API constraint |
| **File freshness** | Documents updated when product terms change | Accuracy |

## Testing

| Test | What It Validates |
|---|---|
| **Volume attachment** | Volumes successfully attached to Genie Agent |
| **Retrieval accuracy** | "What are the fees?" retrieves fee_schedules, not product_docs |
| **Cross-source query** | "How much did I spend on my credit card, and what's the interest rate?" combines structured data + volume content |
| **Citation verification** | Response cites the correct PDF and page number |
| **Locale content** | NL agent retrieves Dutch documents; US agent retrieves English documents |

## Deployment

Part of **Bundle 3 (Application)**. Volumes are created by Bundle 1; documents are uploaded as part of the deployment process.

## Open Questions

| # | Question | Impact | Resolution Path |
|---|---|---|---|
| Q29 | Should knowledge volumes be attached to each domain agent, or to a single dedicated Knowledge Agent? | Routing simplicity vs. context relevance | POC — start with dedicated Knowledge Agent; merge into domain agents if retrieval is accurate |
| — | Genie Agent volumes is in Beta — is it stable enough for a consumer-facing POC? | Risk | Monitor Beta status; fallback: custom RAG with Vector Search |

## References

- Genie Agent volumes: https://learn.microsoft.com/en-us/azure/databricks/genie-agents/volumes/
- **L200-C7** — Genie Agents (canvas notebooks/308703764929950)
- **L200-C8** — Agent Orchestration (canvas notebooks/308703764930017)
