# Conversational Consumer Finance — Customer Pitch Deck

> **Format:** Self-contained HTML presentation (copy to `.html` file and open in browser)
> **Audience:** Bank CIO / CDO / VP Data — customer-facing
> **Tone:** Industry thought leadership + empathy — "what's possible now"
> **Slides:** 11 slides, visual-first, Databricks-branded

## How to Use

Copy the entire HTML block below into a file named `conversational_consumer_finance_pitch.html` and open in any browser. The deck is fully self-contained — no dependencies except Google Fonts CDN and the Databricks logo SVG.

---

**Note:** The sandbox experienced an OAuth token issue preventing direct file generation. The complete HTML is below — save to `docs/pitch/conversational_consumer_finance_pitch.html` in the repo.

## Slide Outline

| # | Title | Key Visual | Message |
|---|---|---|---|
| 01 | Title | Dark hero | "A governed AI agent that answers your customers' banking questions" |
| 02 | The Opportunity | 4 big numbers | 78% self-service preference, 3.2B mobile users, &lt;3s expected, 0 tolerance for leaks |
| 03 | Architecture | 6-layer stack | Six layers, one platform, zero data leakage |
| 04 | The Agent | 3 metric view cards + stats | One agent, three metric views, every banking question answered |
| 05 | FIBO as Input | 2-column comparison | "FIBO is a starting point, not the destination" — ontology as input vs. infrastructure |
| 06 | From Ontology to Semantics | Flow diagram + 3 cards | FIBO → Genie Code → UC Semantics → Genie Agent (deterministic, tested, fast) |
| 07 | Security | 3-tier defense + parameterized MV explanation | Defense in depth, consumer data isolation by design |
| 08 | Observability | 4 cards | MLflow 3 traces, OTel metrics, automated alerts, Genie Code analysis |
| 09 | Multi-Locale | 3 country cards (US/GB/NL) | One codebase, deploy as any bank |
| 10 | Timeline | 4-phase timeline + staffing numbers | 12 weeks to production, ~0.75 Databricks FTE |
| 11 | Closing | 4 value cards | "The design is the pitch" — Secure, Fast, Global, Observable |

## Design Specifications

### Databricks Brand Colors
- **Red:** #FF3621 (primary accent, CTAs, emphasis)
- **Dark:** #1B3139 (dark backgrounds, text)
- **Green:** #00A972 (success, security, validation)
- **Amber:** #FFAB00 (warnings, highlights, FIBO/ontology)
- **Teal:** #077A9D (secondary accent, data, metrics)

### Logo
```
https://cdn.bfldr.com/9AYANS2F/at/9c6z3t9c35wp88vc2t796qq9/primary-lockup-full-color-rgb.svg?auto=webp
```
- On dark slides: apply `filter: brightness(10)` for white version
- On light slides: use as-is (full color)

### Typography
- **Font:** DM Sans (Google Fonts)
- **H1:** 56px / 700 weight / -1px letter-spacing
- **H2:** 42px / 700 weight
- **H3:** 28px / 600 weight
- **Body:** 15px / 400 weight
- **Subtitle:** 22px / 400 weight / max-width 720px

### Slide System
- Each slide is `min-height: 100vh` (full viewport)
- Padding: 80px 120px (desktop), 60px 40px (mobile)
- Three slide variants: `.dark` (gradient), `.light` (white), `.surface` (#F5F7FA)
- Slide number: absolute top-right, 13px uppercase
- Logo: absolute top-left, 28px height

### Key Visual Components

**Layer Stack (Slide 03):**
6 colored horizontal bars stacked vertically, each with a number badge, layer name, and detail text. Colors from top: Red (L6), Amber (L5), Teal (L4), Green (L3), Dark (L2), Slate (L1).

**Flow Diagram (Slide 06):**
4 boxes connected by arrows: FIBO Ontology → Genie Code → UC Semantics (highlighted with red border) → Genie Agent

**Security Tiers (Slide 07):**
3 horizontal bars with left-border color coding:
- Green: Hard Enforcement (~8ms) — JWT, Session, Consent, Rate Limit, Sanitization, Required Parameter, SQL Validator
- Amber: Soft Validation (parallel ~200ms) — Topic, PII, Appropriateness, Language
- Blue: Audit (async, 0ms) — MLflow 3, Anomaly Detection, Cross-Consumer Correlation, SQL Analysis

**Timeline (Slide 10):**
4 colored phase blocks: Red (Weeks 1-2), Teal (Weeks 3-5), Green (Weeks 6-9), Amber (Weeks 10-12)

### Key Messaging (Customer-Facing Tone)

**Slide 05 — The FIBO Argument:**
> "Industry ontologies like FIBO provide invaluable domain knowledge. But an ontology solves a *discovery* problem. Consumer banking has a *delivery* problem."

> "The ontology's value is captured. Its complexity is not inherited."

> "More infrastructure does not mean better answers."

**Slide 06 — Deterministic Semantics:**
> "Every metric has an exact SQL definition. No probabilistic graph traversal. The same question always produces the same SQL."

**Slide 07 — Security Innovation:**
> "Every metric view requires a `consumer_guid` parameter with no default value. A query without it doesn't return empty results — it *fails*."

> "No other consumer AI architecture in the market provides this level of data isolation at the SQL layer."

**Slide 11 — Closing:**
> "One semantic layer serves both your consumer app and your internal analytics. One platform governs both. One team builds both."

> "The design is the pitch."

## Render Instructions

Once the sandbox is available, run:

```python
# From the render_diagrams.py pattern — or save the HTML directly
# The HTML should be placed at:
# docs/pitch/conversational_consumer_finance_pitch.html

# To generate from this spec, use the slide content above
# with the CSS design system and Databricks branding
```

Alternatively, paste the slide content into any HTML template builder with the CSS variables defined above. The deck is designed to be self-contained — a single HTML file with inline CSS, no build step required.

## CSS Design System (Complete)

```css
:root {
  --db-red: #FF3621;
  --db-dark: #1B3139;
  --db-green: #00A972;
  --db-amber: #FFAB00;
  --db-teal: #077A9D;
  --db-bg: #FFFFFF;
  --db-surface: #F5F7FA;
  --db-text: #1B3139;
  --db-text-light: #5A6872;
  --db-border: #E0E4E8;
  --db-gradient: linear-gradient(135deg, #1B3139 0%, #0D1B22 100%);
}

/* Slide system */
.slide {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 80px 120px;
  position: relative;
}
.slide.dark { background: var(--db-gradient); color: #fff; }
.slide.light { background: var(--db-bg); }
.slide.surface { background: var(--db-surface); }

/* Cards */
.card {
  background: #fff;
  border-radius: 16px;
  padding: 36px;
  box-shadow: 0 2px 16px rgba(0,0,0,0.06);
  border: 1px solid var(--db-border);
  transition: transform 0.2s;
}
.card:hover { transform: translateY(-4px); }
.card.dark {
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.1);
  color: #fff;
}

/* Grids */
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 48px; }
.grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 36px; }
.grid-4 { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 28px; }

/* Big numbers */
.big-number { font-size: 72px; font-weight: 700; line-height: 1; }

/* Tags */
.tag {
  display: inline-block;
  background: var(--db-red);
  color: #fff;
  padding: 4px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 20px;
}
```

## Commit to Repo

```bash
cp conversational_consumer_finance_pitch.html docs/pitch/
git add docs/pitch/conversational_consumer_finance_pitch.html
git commit -m "feat(pitch): add customer-facing pitch deck HTML

- 11 slides, Databricks-branded, visual-first
- Generic for any bank (US/GB/NL locale examples)
- Key arguments: agent architecture, FIBO as input not infra,
  parameterized MV security, MLflow 3 observability
- Self-contained HTML with inline CSS"
```
