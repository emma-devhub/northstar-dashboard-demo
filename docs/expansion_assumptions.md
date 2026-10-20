# Expansion Assumptions and Synthetic Brand Profiles

**Canonical label for all four brands:** “Synthetic / illustrative brand assumptions defined for the case.”

This document is the single source of truth for Northstar Everyday, Northstar Active, Northstar Gear and Northstar Atelier. Their profiles are scenario inputs, not observations from the flagship production CSV or facts about a real customer. Public sources were reviewed on October 19, 2026.

## 1. Assumption Methodology

We reviewed public Fireworks customer material and identified a closely analogous enterprise scaling pattern in its [Global QSR Chain customer story](https://fireworks.ai/story-quick-service-restaurant-fast-food). It describes technical benchmarking, a limited-store pilot, staged production expansion, and evaluation of accuracy, latency, throughput, cost and peak-hour behavior. It also describes a unified platform that supports expansion without rebuilding the infrastructure.

The deployment philosophy we take from that example is:

**Benchmark → pilot → validate latency / quality / cost / peak-load behavior → standardize the operating playbook → expand.**

This sequence is our synthesis for the Northstar case, not a quoted Fireworks framework. Standardizing the operating playbook is a recommended implication of platform reuse; the public story does not document a complete playbook. It provides a deployment analogue, not evidence that Northstar is that QSR customer. We do not import its reported performance or rollout milestones into Northstar's forecasts.

The take-home itself points more strongly toward traditional retail: it specifies product catalogs, return policies, brand-specific tone and catalog-based RAG. We therefore use VF Corporation as a structural retail reference. Its [company overview](https://www.vfc.com/our-company) and [brand portfolio](https://www.vfc.com/brands) show an apparel, footwear and equipment portfolio with distinct brand identities. Its official [The North Face profile](https://www.vfc.com/brands/the-north-face) and [Vans profile](https://www.vfc.com/brands/vans) illustrate differences in product technicality and positioning. VF's [FY2026 earnings disclosure](https://www.vfc.com/investors/financial-information/sec-filings/content/0000103379-26-000028/q42026earningsexhibit991.htm) separately reports differing brand revenue scales; revenue is not a support-ticket denominator.

Together these references support a heterogeneous portfolio design, rather than four interchangeable copies of the flagship. We use four synthetic brands to test **scale, brand adaptation, knowledge complexity and experience sensitivity**. Differences in customer expectations are inferred from positioning, not measured customer-research results. No synthetic brand is a one-to-one alias for a VF brand; the value-apparel and premium-service archetypes are case design choices.

**These public examples are structural analogues only. They are not claims about Northstar’s identity.**

## 2. Synthetic Brand Profiles

Every field below belongs to the label **“Synthetic / illustrative brand assumptions defined for the case.”** Relative volume, operational maturity and policy details are scenario assumptions to validate, not measured inputs.

### Northstar Everyday

| Attribute | Case assumption |
| --- | --- |
| Positioning | Mass-market value apparel and everyday essentials. |
| Relative support volume | Highest in the synthetic portfolio. |
| Catalog complexity | Low–Medium. |
| Tone | Friendly, practical, concise. |
| Return / policy complexity | High return frequency is plausible, but rules are mostly standardized; overall policy complexity is Low–Medium. |
| Team maturity | High — illustrative scenario assumption. |
| Expansion role | Scale / repeatability test. |
| Primary hypothesis | Can the flagship deployment pattern be reproduced at high volume with limited customization? |

### Northstar Active

| Attribute | Case assumption |
| --- | --- |
| Positioning | Active / lifestyle apparel. |
| Relative support volume | Medium–High. |
| Catalog complexity | Medium. |
| Tone | Energetic, encouraging, brand-forward. |
| Return / policy complexity | Medium, driven by fit, exchange, seasonal and use-case variation. |
| Team maturity | Medium–High — illustrative scenario assumption. |
| Expansion role | Brand adaptation test. |
| Primary hypothesis | Can the shared architecture handle stronger brand voice and richer product context without requiring a model fork? |

### Northstar Gear

| Attribute | Case assumption |
| --- | --- |
| Positioning | Technical outdoor apparel, footwear and equipment. |
| Relative support volume | Medium–High. |
| Catalog complexity | High. |
| Tone | Precise, expert, confidence-calibrated. |
| Return / policy complexity | High, including warranties, product-use constraints and technical exceptions. |
| Team maturity | High — illustrative scenario assumption. |
| Expansion role | Knowledge-complexity test. |
| Primary hypothesis | Can the RAG and eval stack maintain grounding and precision across more technical product knowledge? |

### Northstar Atelier

| Attribute | Case assumption |
| --- | --- |
| Positioning | Premium lifestyle apparel and accessories. |
| Relative support volume | Lower. |
| Catalog complexity | Medium. |
| Tone | Polished, personalized, high-touch. |
| Return / policy complexity | Medium policy complexity but high service discretion and exception handling. |
| Team maturity | Medium — illustrative scenario assumption. |
| Expansion role | Experience-sensitivity test. |
| Primary hypothesis | Can automation preserve premium CX while using more conservative escalation boundaries? |

## 3. Evidence Basis / Confidence

These categories describe provenance, not a numerical account-health or expansion-confidence score. A plausible inference does not become a Northstar observation.

| Evidence category | What it supports | Boundary |
| --- | --- | --- |
| **PUBLICLY GROUNDED** | Real multi-brand portfolio heterogeneity; differences in commercial scale; product breadth / technicality; brand positioning. | Supported by the official VF references above. The QSR story supports the staged-deployment analogue. Neither source measures Northstar's brands or support operations. |
| **REASONABLE INFERENCE** | Relative catalog complexity; likely policy / service complexity; likely support-contact patterns. | Reasoned from retail archetypes. For example, technical products can require more precise knowledge, and premium service can be more sensitive to escalation choices. These are hypotheses to validate. |
| **ILLUSTRATIVE CASE ASSUMPTION** | Team maturity; exact relative support-volume ordering; exact workload mix; exact policy details. | Assigned for this case. “Highest” and “Medium–High” are relative scenario descriptors, not estimates inferred from VF revenue. Even the brand-specific complexity ratings remain scenario inputs. |

No exact monthly ticket counts, brand-specific spend, automation rates, business outcomes or staffing numbers are invented. No profile asserts observed demand, proven transferability or a guaranteed expansion result. More complex or deeper flagship tickets are possible explanations for rising inference work, not established facts.

## 4. How the Profiles Are Used

The profiles are decision inputs, not standalone deliverables for their own sake. They support:

- **Expansion opportunity:** identify different workload / brand combinations and their potential customer value.
- **Pilot selection:** compare expected transferable volume and value with automation feasibility, cost, quality risk and CX downside. Everyday is the scale / repeatability candidate under these assumptions; validate the assumptions before treating it as the selected deployment.
- **Rollout sequencing:** test repeatable deployment, then brand adaptation, knowledge complexity and experience sensitivity as evidence permits; this is a learning sequence, not a committed schedule.
- **Technical scaling plan:** assess reuse of serving, brand-specific prompts, isolated RAG knowledge, evaluations and monitoring. Active tests whether voice adaptation can avoid a model fork; it does not presume that outcome.
- **Broader-rollout gates:** require demonstrated customer outcomes, stable reliability, acceptable cost per quality-compliant resolution, explainable inference work per ticket, architectural reuse and clear knowledge / escalation ownership. Numeric thresholds require agreement and new telemetry.

### Reference and change rules

- Future customer dashboard, internal QBR and EBR brand references must use these names, attributes and the canonical label above. Link or cite `docs/expansion_assumptions.md`; do not create conflicting local profiles or call an individual brand a temporary example.
- The dashboard design document references this file under **Expansion Assumptions**. The EBR placeholder references it as the input for the future recommendation. The customer dashboard reads the canonical label and Everyday attributes from this file through `src/expansion.py`, and cites this source visibly in Section 09. Its pilot workload suggestions are separately labeled illustrative, not observed ticket categories.
- Update this document first if a profile changes, then reconcile downstream recommendations. Keep observed flagship metrics sourced from `data/northstar_flagship_30_day_metrics.csv` and existing calculations in `src/metrics.py`.
- The existing inference-efficiency evidence remains sufficient: tokens per request are broadly stable, requests and tokens per Tier-1 ticket increase materially, and inference spend rises with usage. Why inference work per ticket is increasing remains unresolved. This document adds no daily spend-per-Tier-1-ticket metric and does not change CSV-derived risk metrics.
