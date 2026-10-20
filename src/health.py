"""Provisional internal analyst rubric, distinct from observed production metrics.

Weights and qualification rules are policy choices, not fitted or calibrated
customer-health predictions. Assumption-driven ratings live in the canonical
internal assumptions document. See docs/dashboard_design.md for governance.
"""
from src.metrics import (AHT_REDUCTION_VS_BASELINE, PROVIDED_AUTOMATION_PCT,
                         PROVIDED_CSAT_LIFT_POINTS)

PILLAR_POLICY = (
    ('value', 'Customer Value & Adoption', .25, 'HIGH'),
    ('technical', 'Technical & AI Health', .25, 'HIGH'),
    ('economics', 'Economic Efficiency & Support Burden', .15, 'MEDIUM'),
    ('relationship', 'Relationship & Commercial Health', .15, 'LOW'),
    ('expansion', 'Expansion Readiness', .20, 'MEDIUM'),
)
HEALTHY_MIN = 80
WATCH_MIN = 60
CRITICAL_CAP = 79


def calculate_account_health(df, summary, scenario):
    """Return full component audit, weighted score, confidence and critical cap."""
    t = summary['trends']
    components = []

    def add(pillar, name, weight, score, basis, rule, evidence):
        if not 0 <= score <= 100:
            raise ValueError('Health component outside 0–100.')
        components.append(dict(pillar=pillar, component=name, weight=weight,
                               score=score, basis=basis, rule=rule, evidence=evidence))

    def rubric(pillar, name, weight, condition, good, fallback, rule, evidence):
        add(pillar, name, weight, good if condition else fallback,
            'Illustrative rubric applied to provided / observed evidence',
            f'{rule}: {good} if met; otherwise {fallback}.', evidence)

    rubric('value', 'Automation / adoption', .30,
           PROVIDED_AUTOMATION_PCT >= 70 and t['automation_rate_pct']['change'] > 0,
           95, 65, 'Provided automation ≥70% and observed automation rises',
           f"Provided {PROVIDED_AUTOMATION_PCT}%; observed +{t['automation_rate_pct']['change']:.1f} pp")
    rubric('value', 'AHT improvement', .25, AHT_REDUCTION_VS_BASELINE >= .35,
           95, 65, 'Provided baseline AHT reduction ≥35%', '35% provided vs unspecified pre-deployment baseline')
    rubric('value', 'CSAT improvement', .25, PROVIDED_CSAT_LIFT_POINTS >= 12,
           95, 65, 'Provided baseline CSAT lift ≥12 points', '+12 points provided vs unspecified baseline')
    rubric('value', 'Sustained usage / volume', .20,
           t['requests']['change'] > 0 and t['automated_tier1_tickets']['change'] > 0,
           90, 60, 'Both requests and automated tickets rise first → last day',
           f"Requests {t['requests']['pct_change']:+.1f}%; automated tickets {t['automated_tier1_tickets']['pct_change']:+.1f}%")

    rubric('technical', 'Reliability', .30,
           t['availability_pct']['last'] >= 99.9 and t['error_rate_pct']['last'] < 1
           and t['error_rate_pct']['change'] < 0,
           90, 55, 'Final availability ≥99.9%, final error <1%, error improves',
           f"Final availability {t['availability_pct']['last']:.3f}%; error {t['error_rate_pct']['last']:.2f}%")
    rubric('technical', 'Latency', .20,
           t['p50_latency_ms']['change'] < 0 and t['p95_latency_ms']['change'] < 0,
           90, 60, 'Both P50 and P95 improve first → last day',
           f"P50 {t['p50_latency_ms']['pct_change']:+.1f}%; P95 {t['p95_latency_ms']['pct_change']:+.1f}%")
    rubric('technical', 'Grounding / eval quality', .30,
           t['grounded_answer_rate_pct']['change'] > 0 and t['quality_eval_pass_rate_pct']['change'] > 0,
           90, 55, 'Both grounding and evaluation pass improve',
           f"Grounding +{t['grounded_answer_rate_pct']['change']:.1f} pp; eval +{t['quality_eval_pass_rate_pct']['change']:.1f} pp")
    catalog = df.operational_note.str.contains('Catalog sync', regex=False)
    traffic = df.operational_note.str.contains('Traffic burst', regex=False)
    incidents = int((catalog | traffic).sum())
    recovered = (df.loc[catalog, 'operational_note'].str.contains('mitigat', case=False).all()
                 and df.loc[traffic, 'operational_note'].str.contains('adjust', case=False).all())
    recovery_score = max(50, 90 - 3 * incidents) if recovered and t['escalation_rate_pct']['change'] < 0 else 55
    add('technical', 'Escalation / operational recovery', .20, recovery_score,
        'Illustrative rubric applied to observed notes',
        '90 − 3 per catalog/traffic incident (floor 50) if notes report mitigation/adjustment and escalation declines; otherwise 55.',
        f"{incidents} catalog / traffic incidents; escalation {t['escalation_rate_pct']['change']:+.1f} pp. Denominator unspecified.")

    spend_ratio = t['spend_usd']['last'] / t['automated_tier1_tickets']['last']
    start_ratio = t['spend_usd']['first'] / t['automated_tier1_tickets']['first']
    rubric('economics', 'Spend / output efficiency', .35, spend_ratio <= start_ratio,
           90, 75, 'Daily inference spend / automated-ticket allocation does not increase',
           f"Allocation {start_ratio:.4f} → {spend_ratio:.4f} USD; not total support cost or quality-compliant resolution cost")
    work_increasing = (t['requests_per_tier1_ticket']['change'] > 0 or t['tokens_per_tier1_ticket']['change'] > 0)
    rubric('economics', 'Inference efficiency / ticket', .35, not work_increasing,
           85, 60, 'Neither requests/Tier-1 ticket nor tokens/Tier-1 ticket rises',
           f"Requests/ticket {t['requests_per_tier1_ticket']['pct_change']:+.1f}%; tokens/ticket {t['tokens_per_tier1_ticket']['pct_change']:+.1f}%; cause unknown")
    add('economics', 'Support burden / operating effort', .30, scenario['support']['burden_score'],
        'Internal scenario judgment', 'Rating from docs/internal_qbr_assumptions.md',
        scenario['support']['assumption'] + ' ' + scenario['support']['boundary'])

    for key, name, weight in [('sponsor', 'Executive sponsor strength', .30),
                              ('coverage', 'Stakeholder coverage', .20),
                              ('budget', 'Budget alignment', .20),
                              ('renewal', 'Renewal risk', .15),
                              ('competition', 'Competitive risk', .15)]:
        item = scenario['relationship'][key]
        add('relationship', name, weight, item['score'], 'Internal scenario judgment',
            'Rating from docs/internal_qbr_assumptions.md', item['assumption'])
    for key, name, weight in [('fit', 'Second-brand fit / portability', .25),
                              ('reuse', 'Architecture reuse potential', .20),
                              ('economics', 'Unit-economics visibility', .20),
                              ('peak', 'Peak-load readiness', .15),
                              ('knowledge', 'Knowledge operations', .10),
                              ('team', 'Operating-team readiness', .10)]:
        item = scenario['expansion_ratings'][key]
        add('expansion', name, weight, item['score'], 'Illustrative readiness judgment',
            'Rating from docs/internal_qbr_assumptions.md, informed by canonical brand profiles / telemetry', item['rationale'])

    pillars = []
    for key, name, weight, confidence in PILLAR_POLICY:
        rows = [row for row in components if row['pillar'] == key]
        if abs(sum(row['weight'] for row in rows) - 1) > 1e-9:
            raise ValueError('Component weights must sum to one within each pillar.')
        value = sum(row['weight'] * row['score'] for row in rows)
        pillars.append(dict(key=key, name=name, weight=weight, score=value,
                            contribution=value * weight, confidence=confidence))
    raw = sum(pillar['contribution'] for pillar in pillars)
    flags = scenario['critical_flags']
    score = min(raw, CRITICAL_CAP) if flags else raw
    return dict(pillars=pillars, components=components, raw_score=raw, score=score,
                status='HEALTHY' if score >= HEALTHY_MIN else 'WATCH' if score >= WATCH_MIN else 'AT RISK',
                confidence='MEDIUM–HIGH', critical_flags=flags, cap_applied=bool(flags))
