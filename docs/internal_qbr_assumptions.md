# Internal QBR assumptions

**Canonical label:** “Illustrative internal assumptions for case purposes.”

This is the single source of truth for invented internal relationship, commercial and execution context. None of these statuses are observed customer facts. The app reads the structured scenario below at runtime and fails visibly if it is missing or invalid. The customer renderer never reads this document.

The case provides no stakeholder map, renewal date, contract value, expansion budget, competitor presence, staffing burden, procurement status, margin or executive sponsor strength. No ARR, contract values, margin percentages, headcount, renewal dates or named competitors are invented here. Strong observed flagship outcomes inform the discussion; they do not verify these assumptions.

The five relationship scores, support-burden score and expansion-readiness component ratings below are illustrative analyst judgments on a 0–100 rubric. They are not empirical probabilities or measured KPIs. Each rating includes its scenario rationale. Telemetry-derived scoring rules are separately documented in `dashboard_design.md` and implemented in `src/health.py`. Keep evidence confidence independent of the score.

Brand names, profiles, expansion roles and primary hypotheses remain exclusively in `expansion_assumptions.md`. Pipeline metadata below is an illustrative internal planning overlay, not a committed schedule or a replacement brand profile. All pipeline owners and action owners are proposed functional roles, not assigned named people. Dates start from an illustrative Oct 19, 2026 planning review; the telemetry still ends Aug 31, so current production health after August is unknown. The Nov 2 review approves readiness to launch a pilot; it is not the completion of the EBR’s proposed 4–6-week Everyday phase.

An empty `critical_flags` list means no case-provided critical red flag has been identified. It does not certify that no risk exists. Before a real review, verify severe reliability, major quality/safety, active churn, security/compliance or sponsor-loss issues. Any active critical flag caps the displayed score at 79 (Yellow / WATCH), preserving the uncapped weighted score for audit.

The renewal / competitive watch items are hypotheses to verify, not reports of churn, absent expansion intent or an active competitor. Margin visibility is excluded from the dashboard and score because the case does not support it. The support-burden rating only describes the documented qualitative execution scenario.

## Runtime scenario

Edit the scenario here first, then reconcile downstream planning and re-run tests. Do not add observed metrics or duplicate brand profiles here.

```json
{
  "label": "Illustrative internal assumptions for case purposes.",
  "review_date": "2026-10-19",
  "relationship": {
    "sponsor": {
      "status": "Strong",
      "assumption": "VP Customer Experience is a strong business sponsor / assumed champion; VP Engineering is supportive but requires scalability and repeatable economics evidence.",
      "score": 90
    },
    "coverage": {
      "status": "Incomplete",
      "assumption": "Coverage beyond the two executives is incomplete / not provided. Brand operating owners and procurement / finance contacts are not confirmed.",
      "score": 65
    },
    "budget": {
      "status": "Not committed",
      "assumption": "Broad four-brand expansion budget is not yet committed; procurement / commercial approval for broad rollout is not yet secured.",
      "score": 60
    },
    "renewal": {
      "status": "Low / unknown near term",
      "assumption": "No active renewal threat is provided, and renewal timing is unknown. A satisfied flagship customer may still choose to stay at the current scope; validate renewal intent and expansion appetite separately with the Account Manager.",
      "score": 85
    },
    "competition": {
      "status": "Moderate / unknown",
      "assumption": "Other brands or functions may evaluate third-party alternatives, including Fireworks competitors. Monitor evaluations and vendor-selection plans; no competitor presence is confirmed.",
      "score": 65
    }
  },
  "support": {
    "current": "Manageable",
    "assumption": "Current flagship support burden is assumed manageable. Multi-brand rollout would increase burden unless knowledge ingestion, evals, monitoring and deployment operations are standardized.",
    "boundary": "Engineering and support hours per brand are not measured; manageable flagship burden does not establish low incremental rollout effort.",
    "burden_score": 75
  },
  "expansion_ratings": {
    "fit": {
      "score": 85,
      "rationale": "Everyday is a credible scale / repeatability pilot under canonical synthetic profiles; cross-brand portability is unproven."
    },
    "reuse": {
      "score": 85,
      "rationale": "Shared serving, isolated brand context, RAG, eval and monitoring reuse is plausible; not yet validated on a second brand."
    },
    "economics": {
      "score": 60,
      "rationale": "Intent-level cost per quality-compliant resolution is unavailable."
    },
    "peak": {
      "score": 80,
      "rationale": "Promotion incident recovered after autoscaling adjustment; multi-brand peak-load validation remains open."
    },
    "knowledge": {
      "score": 75,
      "rationale": "Catalog-sync incident exposes the need for standardized ingestion, validation and rollback."
    },
    "team": {
      "score": 80,
      "rationale": "Everyday team maturity is high only under the synthetic scenario; named operating ownership is unconfirmed."
    }
  },
  "stakeholders": [
    {
      "Stakeholder": "VP Customer Experience",
      "Role": "Business sponsor / assumed champion",
      "Health / coverage": "Strong (assumed)",
      "Gap / next evidence": "Confirm cross-brand priorities and pilot budget"
    },
    {
      "Stakeholder": "VP Engineering",
      "Role": "Technical decision-maker",
      "Health / coverage": "Supportive (assumed)",
      "Gap / next evidence": "Demonstrate scalability and repeatable economics"
    },
    {
      "Stakeholder": "Brand / operations owners",
      "Role": "Knowledge, escalation and rollout owners",
      "Health / coverage": "Incomplete / not provided",
      "Gap / next evidence": "Map accountable owners and team readiness"
    },
    {
      "Stakeholder": "Procurement / finance",
      "Role": "Commercial approval",
      "Health / coverage": "Not confirmed",
      "Gap / next evidence": "Confirm approval path and broad-rollout funding"
    }
  ],
  "pipeline": [
    {
      "brand": "Northstar Everyday",
      "stage": "Proposed pilot",
      "priority": "1 · Highest",
      "confidence": "Medium–High, assumption-driven",
      "blocker": "Intent mix, baseline, scope, budget and operating owner unvalidated",
      "gate": "Validate intent mix + approve pilot scope",
      "owner": "Fireworks Account Lead + Deployment"
    },
    {
      "brand": "Northstar Active",
      "stage": "Discovery / next-wave candidate",
      "priority": "2 · Second",
      "confidence": "Medium, assumption-driven",
      "blocker": "No second-brand reuse or unit-economic evidence",
      "gate": "Everyday demonstrates architecture reuse + acceptable unit economics",
      "owner": "Fireworks Account Team + Solutions Engineering"
    },
    {
      "brand": "Northstar Gear",
      "stage": "Future validation",
      "priority": "3 · Third",
      "confidence": "Medium–Low, assumption-driven",
      "blocker": "Technical knowledge / warranty evaluation and retrieval readiness unproven",
      "gate": "RAG / eval stack proven on second brand",
      "owner": "Fireworks Deployment + RAG / Evaluation Engineering"
    },
    {
      "brand": "Northstar Atelier",
      "stage": "Future validation",
      "priority": "4 · Conditional",
      "confidence": "Medium–Low, assumption-driven",
      "blocker": "Premium-CX automation boundaries and escalation ownership unvalidated",
      "gate": "Validate automation boundaries and premium-CX strategy",
      "owner": "Fireworks Account Team + Deployment"
    }
  ],
  "action_label": "Illustrative execution plan for case purposes.",
  "actions": [
    {
      "Action": "Check with Account Manager + engineer on rising inference work / ticket and customer impact; agree intent-level analysis",
      "Owner": "Fireworks Account Manager + Deployment Engineer / Data Science",
      "Target": "2026-10-23",
      "Status": "Proposed · not started"
    },
    {
      "Action": "Define Everyday eligible intents + baseline volume / AHT",
      "Owner": "Northstar CX + Fireworks Account Team",
      "Target": "2026-10-26",
      "Status": "Proposed · not started"
    },
    {
      "Action": "Validate autoscaling / peak-load thresholds",
      "Owner": "Fireworks Engineering",
      "Target": "2026-10-28",
      "Status": "Proposed · not started"
    },
    {
      "Action": "Define reusable brand RAG ingestion / rollback runbook",
      "Owner": "Fireworks Engineering + Northstar Knowledge Owner",
      "Target": "2026-10-30",
      "Status": "Proposed · not started"
    },
    {
      "Action": "Confirm sponsor, renewal / expansion intent, alternative-provider evaluations, brand owner and pilot budget",
      "Owner": "Fireworks Account Manager + Northstar VP CX",
      "Target": "2026-10-30",
      "Status": "Proposed · not started"
    },
    {
      "Action": "Pilot go / no-go review",
      "Owner": "Fireworks + Northstar executive team",
      "Target": "2026-11-02",
      "Status": "Proposed · not started"
    }
  ],
  "critical_flags": [],
  "renewal_competitive_watch": {
    "expansion": "The customer may be happy with the current flagship deployment and have no immediate appetite to expand. Satisfaction does not establish expansion intent or a funded next step.",
    "competition": "Other brands or functions may evaluate third-party alternatives, including Fireworks competitors. Monitor evaluations and vendor-selection plans; no competitor presence is confirmed.",
    "monitor": "Check with the Account Manager on renewal intent, appetite to expand, brand / function plans and any alternative-provider evaluations.",
    "decision": "Check in with the Account Manager and deployment engineer on rising inference work / ticket. Determine whether extra compute creates value or reflects avoidable orchestration before treating it as a confirmed cost problem or making expansion commitments."
  }
}
```
