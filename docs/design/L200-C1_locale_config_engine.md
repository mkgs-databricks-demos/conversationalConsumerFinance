# L200-C1: Locale Config Engine — Detailed Design

> **Status:** Draft v1 — Oct 6, 2026
> **Author:** Matthew Giglia
> **Parent:** L100 — Conversational Consumer Finance: System Overview
> **Component:** C1 — Locale Config Engine (Cross-cutting)
> **Priority:** P1
> **Bundle:** Cross-cutting — consumed by all bundles

## Overview

The Locale Config Engine is the **cross-cutting abstraction** that makes the entire architecture locale-driven. A single YAML file (`locales/{locale}.yaml`) drives all locale-specific behavior across every component: data generation, pipeline configuration, semantic layer, Genie Agent instructions, and app behavior. Deploy as an American Bank (`--var locale=us`), British Bank (`--var locale=gb`), or Dutch Bank (`--var locale=nl`) by changing one variable.

This is not a runtime service — it's a **build-time configuration resolution** pattern. At deployment time, locale variables are substituted into templates to produce locale-specific artifacts (metric view YAML, Genie Agent instructions, episode configs, etc.).

### Design Lineage

- **L100 v3** — Locale Abstraction section (canvas notebooks/1987168172366090)
- **GitHub repo** — Three locale configs already committed: `locales/us.yaml`, `locales/gb.yaml`, `locales/nl.yaml`

## Dependencies

| Dependency | Component | What It Provides | Status |
|---|---|---|---|
| None | — | The Locale Config Engine has no upstream dependencies; it IS the upstream for everything else | — |

## Design

### Locale Config Schema

Each locale YAML file follows a standard schema. The three locale files (US, GB, NL) are already designed and committed to the GitHub repo.

```yaml
# Top-level locale identification
locale: string          # ISO locale code: us, gb, nl
country: string         # Full country name
currency: string        # ISO-4217 currency code: USD, GBP, EUR
language: string        # Language code: en, en-GB, nl

# Account identification format
account_format: string  # routing_account, sort_code_account, or IBAN format
bank_codes: [string]    # Locale-specific bank codes
payment_schemes: [string]  # ACH/WIRE/ZELLE, BACS/CHAPS/FPS, SCT/SCT_INST/SDD_CORE

# Formatting
decimal_separator: string
thousands_separator: string
date_format: string

# Calendar
salary_days: [int]      # Common salary payment days
tax_year_start: string  # MM-DD
holidays: [Holiday]     # Fixed dates, floating dates, Easter-relative
seasonal_spending: [SeasonalPeriod]  # Spending multipliers by period

# Merchants and billers
merchants: {category: [string]}
recurring_billers: {category: [string]}
government_payments: [{name, frequency, typical_amount}]

# Name generation
customer_names:
  source: string        # us_names, gb_names, nl_names

# Semantic layer
genie_agent:
  language_instruction: string
  example_questions_language: string

metric_views:
  synonyms_language: string
  comments_language: string
  currency_format: {code, decimal_places}

uc_pages:
  language: string
```

### Resolution Pattern

Templates use `${locale.*}` variable syntax. At deployment time, a Python resolver reads the locale YAML and substitutes variables:

```python
# src/config/locale_resolver.py
import yaml
from pathlib import Path
from string import Template

def load_locale(locale_code: str) -> dict:
    """Load a locale config from locales/{locale_code}.yaml"""
    config_path = Path(f"locales/{locale_code}.yaml")
    with open(config_path) as f:
        return yaml.safe_load(f)

def resolve_template(template_path: str, locale: dict) -> str:
    """Resolve ${locale.*} variables in a template file"""
    with open(template_path) as f:
        template = f.read()

    # Flatten locale dict for substitution
    flat = flatten_dict(locale, prefix="locale")
    return Template(template).safe_substitute(flat)

def flatten_dict(d: dict, prefix: str = "") -> dict:
    """Flatten nested dict: {a: {b: 1}} → {'a.b': '1'}"""
    items = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, key))
        elif isinstance(v, list):
            items[key] = ", ".join(str(i) for i in v)
        else:
            items[key] = str(v)
    return items
```

### What the Locale Config Drives

| Component | What Changes Per Locale | Template Location |
|---|---|---|
| **State Machine Simulator (C2)** | Salary day, holiday calendar, seasonal multipliers, payment schemes, merchants, billers, government payments, customer names | `src/generator/episodes/*.yaml` |
| **Lakeflow Pipeline (C3)** | Catalog name (`ccf_${locale}`) | `bundles/bundle1-infra/databricks.yml` |
| **Silver Model (C4)** | No change — canonical model is locale-independent | — |
| **Metric Views (C5)** | Synonyms, comments, display_names, currency format | `src/semantic_layer/metric_views/locales/{lang}.yaml` |
| **UC Pages (C6)** | Business term definitions in locale language | `src/semantic_layer/pages/{lang}/` |
| **Genie Agents (C7)** | Language instruction, example questions, example SQL | `src/semantic_layer/genie_agents/{locale}.yaml` |
| **Databricks App (C11)** | Default language, currency formatting, date formatting | App config |
| **Gold MVs (C14)** | No change — Gold MVs are locale-independent (same joins) | — |

### Adding a New Locale

To add a new locale (e.g., German bank):

1. Create `locales/de.yaml` with German-specific config
2. Create `src/semantic_layer/metric_views/locales/de.yaml` with German synonyms
3. Create `src/semantic_layer/pages/de/` with German UC Page definitions
4. Deploy: `databricks bundle deploy --var locale=de`

No code changes required — only configuration files.

## Non-Functional Requirements

| NFR | Target | Rationale |
|---|---|---|
| **Build-time resolution** | All locale variables resolved before deployment | No runtime locale lookups — performance |
| **Additive locales** | Adding a new locale requires only YAML files, no code changes | Extensibility |
| **Validation** | Locale YAML validated against schema before deployment | Catch config errors early |
| **Completeness** | Every template variable must have a value in the locale config | No unresolved `${locale.*}` in deployed artifacts |

## Testing

| Test | What It Validates |
|---|---|
| **Schema validation** | All 3 locale YAMLs conform to the schema |
| **Template resolution** | All `${locale.*}` variables resolve to non-empty values |
| **Completeness check** | No unresolved variables in any deployed artifact |
| **Locale switching** | Deploy with `--var locale=nl`, verify Dutch synonyms in metric views |
| **New locale** | Create a minimal `locales/test.yaml`, deploy, verify all components use test locale values |

## Deployment

The Locale Config Engine is not deployed as a standalone component — it's consumed by all bundles at build time via the `--var locale=` parameter.

```bash
# Deploy Dutch bank
databricks bundle deploy -t dev --var locale=nl

# Deploy American bank
databricks bundle deploy -t dev --var locale=us

# Deploy British bank
databricks bundle deploy -t dev --var locale=gb
```

## Open Questions

| # | Question | Impact | Resolution Path |
|---|---|---|---|
| — | Should locale configs support inheritance (e.g., `gb.yaml` extends `en.yaml`)? | Reduces duplication between US and GB | Defer — 3 locales is manageable without inheritance. Add if we reach 5+ locales. |
| — | Should the resolver validate that all synonym keys in the metric view template exist in the locale synonym file? | Catches missing translations | Yes — add to the deployment validation step |

## References

- **L100 v3** — Locale Abstraction (canvas notebooks/1987168172366090)
- **GitHub repo** — locales/us.yaml, locales/gb.yaml, locales/nl.yaml
- **L200-C5** — Metric Views (canvas notebooks/308703764929801) — primary consumer of locale synonyms
