# L200-C13: Genie Code Data Mapping — Detailed Design

> **Status:** Draft v1 — Oct 6, 2026
> **Author:** Matthew Giglia
> **Parent:** L100 — Conversational Consumer Finance: System Overview
> **Component:** C13 — Genie Code Data Mapping (Cross-cutting)
> **Priority:** P2
> **Bundle:** Bundle 1 (Infrastructure — all environments)

## Overview

The Genie Code Data Mapping workflow is the **production onboarding accelerator** — it maps a customer's real source data model to the canonical FIBO-aligned Silver model using Genie Code as an AI-assisted mapping assistant. This replaces the synthetic data generator (Bundle 2) in production environments, enabling the same metric views, Genie Agents, and consumer app to work with real customer data without rewriting any downstream components.

### The Accelerator Story (from L100)

1. **Day 1:** Deploy Bundle 1 + Bundle 2 → synthetic data flowing, Genie Agent answering. Customer sees the "perfect version."
2. **Week 1–2:** Run Genie Code mapping workflow against real source tables. Genie Code proposes mappings; FDE validates.
3. **Week 3:** Deploy validated mapping spec. Real data flows through the same canonical model.
4. **Week 3+:** Undeploy Bundle 2. Customer has Bundle 1 + Bundle 3 only.

## Dependencies

| Dependency | Component | What It Provides | Status |
|---|---|---|---|
| **FIBO Silver Model** | C4 | Target canonical schema (the mapping target) | Design complete (L200-C4) |
| **Lakeflow Pipelines** | C3 | SDP pipeline that reads the mapping spec at runtime | Design complete (L200-C3) |

## Design

### Mapping Workflow (Lakeflow Job)

```
Lakeflow Job: ccf-${locale}-data-mapping
├── Task 1: Profile Source Tables
│   ├── Read UC metadata for customer's Bronze tables
│   ├── Sample 1000 rows per table
│   ├── Profile columns (types, cardinality, null rates, value distributions)
│   └── Output: source_profile.json
│
├── Task 2: Genie Code Mapping Session
│   ├── Context: FIBO definitions + canonical Silver schema + source profile
│   ├── Prompt: "Map these source columns to the canonical Silver model"
│   ├── Genie Code proposes column-level mappings with transforms
│   └── Output: proposed_mapping.yaml (human-reviewable)
│
├── Task 3: Validate Mapping
│   ├── Execute proposed transforms on sample data
│   ├── Check referential integrity (FK relationships hold)
│   ├── Check type compatibility (source types cast to target types)
│   ├── Check value distributions (mapped values match expected ranges)
│   └── Output: validation_report.json
│
└── Task 4: Generate SDP Config
    ├── Convert validated mapping to SDP YAML event definitions
    ├── Output: src/pipelines/config/customer_*.yaml
    └── These configs replace the generator's event configs in the SDP pipeline
```

### Mapping Specification Format

```yaml
# mappings/nn_bank_core_banking.yaml
source_system: nn_bank_core_banking
locale: nl
version: 1
generated_by: genie_code
validated_by: null  # Set by FDE after review
validated_at: null

tables:
  - source:
      schema: bronze
      table: core_banking_accounts
    target:
      schema: silver
      table: account
    columns:
      - source_column: rekeningnummer
        target_column: account_id
        transform: hash_sha256
        notes: "PII — hash for analytical use"
      - source_column: type_code
        target_column: account_type
        transform: code_map
        code_map:
          B: PAYMENT
          S: SAVINGS
          D: TERM_DEPOSIT
          C: CREDIT_CARD
      - source_column: valuta
        target_column: currency_code
        transform: validate_iso4217
      - source_column: open_datum
        target_column: opened_date
        transform: cast_date
        format: "DD-MM-YYYY"
      - source_column: status
        target_column: account_status
        transform: code_map
        code_map:
          A: OPEN
          B: BLOCKED
          G: CLOSED
          S: DORMANT
    quality_rules:
      - rule: not_null
        columns: [account_id, account_type, currency_code, opened_date]
      - rule: valid_values
        column: account_type
        values: [PAYMENT, SAVINGS, TERM_DEPOSIT, CREDIT_CARD]
```

### SDP Pipeline Integration

The SDP pipeline reads the mapping spec at runtime. When a mapping spec exists, the Silver factory uses it instead of the generator's VARIANT extraction:

```python
# In silver_factory.py
def create_silver_table(config, mapping_spec=None):
    if mapping_spec:
        # Production path: use customer's source columns with transforms
        return create_mapped_silver_table(config, mapping_spec)
    else:
        # Generator path: extract from VARIANT payload
        return create_variant_silver_table(config)
```

## Non-Functional Requirements

| NFR | Target | Rationale |
|---|---|---|
| **Mapping accuracy** | ≥90% of columns correctly mapped by Genie Code | Reduces FDE manual effort |
| **Human review** | Every mapping reviewed by FDE before production use | Safety — AI-proposed, human-validated |
| **Canonical stability** | Mapping changes the source, never the target Silver schema | Downstream metric views and Genie Agents unchanged |

## Testing

| Test | What It Validates |
|---|---|
| **Source profiling** | Profile correctly captures column types, cardinality, null rates |
| **Mapping proposal** | Genie Code proposes reasonable column mappings for known source schemas |
| **Transform execution** | Code maps, date casts, hash transforms produce correct output |
| **Validation** | Referential integrity and type compatibility checks catch errors |
| **SDP integration** | Generated SDP configs produce correct Silver tables from real source data |

## Deployment

Part of **Bundle 1 (Infrastructure)** — the mapping workflow job is available in all environments but only executed when onboarding real customer data.

## Open Questions

| # | Question | Impact | Resolution Path |
|---|---|---|---|
| Q16 | Can Genie Code run as a Lakeflow workflow task? | Affects automation | Research Genie Code workflow task API; fallback: interactive Genie Code session with FDE |
| Q32 | Should the mapping spec be version-controlled in the DAB repo? | Reproducibility | Yes — mapping specs committed to `mappings/` folder in the repo |

## References

- **L100 v3** — Genie Code Data Mapping Workflow section (canvas notebooks/1987168172366090)
- **L200-C4** — FIBO Silver Model (canvas notebooks/308703764885515) — target schema
- **L200-C3** — Lakeflow Pipelines (canvas notebooks/308703764885010) — pipeline integration
