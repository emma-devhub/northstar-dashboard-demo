"""Customer-safe rendering. Internal account planning belongs in a separate view."""
from html import escape
import re

import streamlit as st
from src.charts import daily_chart, ticket_volume_chart, TREND_CHART_HEIGHT
from src.expansion import load_expansion_assumptions
from src.metrics import (AHT_REDUCTION_VS_BASELINE, FTE_MONTH_HOURS,
                         PROVIDED_AUTOMATION_PCT, PROVIDED_CSAT_LIFT_POINTS,
                         operational_events)

STYLE = '''<style>
.block-container {max-width: 1440px; padding-top: 4rem; padding-bottom: 2rem;}
h1 {padding-bottom: .25rem !important; font-size: 2rem !important; letter-spacing: -.055rem; font-weight: 650 !important;}
h2 {font-size: 1.32rem !important; letter-spacing: -.02rem; padding-top: .4rem !important;}
h3 {font-size: 1rem !important;}
[data-testid="stVerticalBlockBorderWrapper"] {border-color: #E2E9ED !important; border-radius: 10px !important;}
.eyebrow {color: #087F78; font-size: .73rem; font-weight: 700; letter-spacing: .13rem; margin-bottom: .8rem;}
.kpi-grid {display:grid; grid-template-columns:repeat(6,minmax(0,1fr)); gap:10px;}
.kpi-card {border:1px solid #E2E9ED; border-radius:8px; padding:10px 12px; background:#FFF;}
.kpi-label {font-size:.74rem; line-height:1.2; min-height:1.8rem; font-weight:600; color:#486071;}
.kpi-value {font-size:1.55rem; line-height:1.15; font-weight:650; letter-spacing:-.04rem; margin:3px 0 5px; color:#182C3D; white-space:nowrap;}
.kpi-note {font-size:.70rem; line-height:1.35; color:#486071;}
.kpi-basis {font-size:.64rem; line-height:1.35; color:#486071; margin-top:2px;}
[data-testid="stVerticalBlock"][class*="st-key-trend-"] > [data-testid="stElementContainer"] {flex-shrink:0;}
@media (max-width:1250px) {.kpi-grid {grid-template-columns:repeat(3,minmax(0,1fr));}}
@media (max-width:1100px) {.st-key-adoption-grid [data-testid="stColumn"] {flex:1 1 100% !important; min-width:100% !important;}}
@media (max-width:620px) {.kpi-grid {grid-template-columns:repeat(2,minmax(0,1fr));}}
.event-table {width:100%; table-layout:fixed; border-collapse:collapse; font-size:.85rem;}
.event-table th, .event-table td {text-align:left; padding:14px 12px; border-bottom:1px solid #E2E9ED; vertical-align:top; overflow-wrap:anywhere;}
.event-table th {background:#F5F8FA; color:#486071;}
.event-table th:first-child {width:8%;}
.rule {border-top: 1px solid #E2E9ED; margin-top: .6rem;}
@media (min-width:640px) and (max-width:1100px) {
[data-testid="stHorizontalBlock"] {flex-wrap:wrap;}
[data-testid="stColumn"] {flex:1 1 calc(50% - 1rem) !important; min-width:calc(50% - 1rem) !important;}
}
</style>'''

CAVEATS = [
    '35% AHT improvement and +12 CSAT points are provided deployment-level outcomes relative to an unspecified pre-deployment baseline. The provided 70% automation headline is separate from daily CSV observations.',
    'The CSV captures the first 31 production days. Within-month changes are distinct from the pre/post deployment headline improvements; these trends do not establish causal attribution.',
    'The exact denominator for escalation_rate_pct is not provided. Escalation policy and case mix affect interpretation; lower escalation is not inherently better.',
    'The exact evaluation methodologies and sample sizes for grounded_answer_rate_pct and quality_eval_pass_rate_pct are not provided.',
    'Inference spend excludes implementation costs, Fireworks commercial terms, support labor, and other program costs. No budget or spending target was supplied; budget variance cannot be assessed.',
    'Support-capacity calculations are illustrative. Current AHT uses the unweighted arithmetic mean of the 31 daily AHT values; ticket-level AHT denominators are unspecified.',
    'Rising inference work per ticket cannot be attributed to increased complexity without ticket-level instrumentation. Requests are not equivalent to support tickets.',
    'Availability is displayed daily; no contractual SLA or request-weighted availability calculation is assumed. All data is synthetic.',
]


def section(number, title, takeaway):
    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    st.markdown(f'## {number:02d}  {title}')
    st.caption(takeaway)


def trend(summary, field, unit='', decimals=1, change='pp'):
    t = summary['trends'][field]
    ending = f"{t['pct_change']:+.1f}%" if change == 'pct' else f"{t['change']:+.{decimals}f} {change}"
    return f"{t['first']:,.{decimals}f}{unit} → {t['last']:,.{decimals}f}{unit} · {ending}"


def chart(df, summary, title, series, unit, decimals=1, change='pp', events=(), note=None,
          height=TREND_CHART_HEIGHT, figure=None):
    key = 'trend-' + re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    with st.container(border=True, key=key, gap=None, height="stretch"):
        st.markdown(f'### {title}')
        details = [f"{label}: {trend(summary, field, '%' if unit == '%' else ' ' + unit, decimals, change)}"
                   for field, label in series.items()]
        st.caption('  \n'.join(details))
        st.plotly_chart(figure if figure is not None else daily_chart(df, series, unit, events, height), use_container_width=True,
                        config={'displayModeBar': False}, key=title)
        if note:
            st.caption(note)


def render_customer_dashboard(df, s):
    st.markdown(STYLE, unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">NORTHSTAR / FLAGSHIP OPERATIONS</div>', unsafe_allow_html=True)
    st.title('Northstar Flagship — Account Health')
    st.write('Production performance, customer outcomes, AI quality, and spend | First 31 days')
    st.caption(f"{df.date.min():%b %d} – {df.date.max():%b %d, %Y} · {len(df)} daily observations · Synthetic production data")
    st.caption('Customer Account Health · Fine-tuned support model + brand system prompt + catalog RAG')
    t = s['trends']
    kpis = [
        ('Tier-1 Automation', f'{PROVIDED_AUTOMATION_PCT}%',
         f"{t['automation_rate_pct']['first']:.1f}% → {t['automation_rate_pct']['last']:.1f}% observed", 'Provided deployment headline'),
        ('Average Handle Time', f'{AHT_REDUCTION_VS_BASELINE:.0%} reduction',
         f"{t['avg_handle_time_min']['first']:.2f} → {t['avg_handle_time_min']['last']:.2f} min observed", 'Provided · vs. pre-deployment baseline'),
        ('Customer Satisfaction', f'+{PROVIDED_CSAT_LIFT_POINTS} points',
         f"{t['csat_score']['first']:.1f} → {t['csat_score']['last']:.1f} observed", 'Provided · vs. pre-deployment baseline'),
        ('Automated Tier-1 Tickets', f"{s['automated_tickets']:,}", '31-day total', 'Observed · CSV ticket counts'),
        ('Estimated Support Capacity Released', f"{s['support_hours']:,.0f} h", 'Illustrative capacity equivalent', 'Calculated · assumptions below'),
        ('31-Day AI Inference Spend', f"${s['spend']:,.2f}", 'Inference only · 31-day total', 'Observed · CSV inference spend'),
    ]
    cards = [f'<div class="kpi-card"><div class="kpi-label">{escape(label)}</div>'
             f'<div class="kpi-value">{escape(value)}</div><div class="kpi-note">{escape(detail)}</div>'
             f'<div class="kpi-basis">{escape(basis)}</div></div>' for label, value, detail, basis in kpis]
    st.markdown('<div class="kpi-grid">' + ''.join(cards) + '</div>', unsafe_allow_html=True)
    st.caption('Metric provenance: Provided = case-prompt outcomes · Observed = daily CSV telemetry · Calculated / illustrative = formulas and assumptions below.')
    st.caption('Line charts use data-relative Y-axis ranges for trend visibility; stacked bars start at zero. Compare labeled values and units across panels.')

    section(1, 'Usage & Adoption', 'AI automation is increasing while handling a growing share of Tier-1 support demand.')
    with st.container(key='adoption-grid'):
        left, right = st.columns(2)
        with left:
            chart(df, s, 'Tier-1 Automation Rate', {'automation_rate_pct': 'Automated share'}, '%')
        with right:
            chart(df, s, 'Tier-1 Ticket Volume', {'tier1_tickets': 'Total Tier-1 demand', 'automated_tier1_tickets': 'AI automated'}, 'tickets', 0, 'pct', figure=ticket_volume_chart(df))
    st.caption(f"Model inference requests: {s['total_requests']:,} · Total tokens: {s['total_tokens']:,}. Requests are not customer tickets.")

    section(2, 'Customer Outcomes', 'Automation increased while handling time declined and customer satisfaction improved. These concurrent trends do not establish causality.')
    left, right = st.columns(2)
    with left:
        chart(df, s, 'Average Handle Time', {'avg_handle_time_min': 'Daily AHT'}, 'min', 2, 'pct', note='Provided deployment outcome: 35% below pre-deployment baseline. The within-month change is shown above.')
    with right:
        chart(df, s, 'Customer Satisfaction', {'csat_score': 'CSAT'}, 'points', 1, 'points', note='Provided deployment outcome: +12 points vs. pre-deployment baseline. The within-month change is shown above.')

    section(3, 'Reliability & Performance', 'Usage increased materially while long-run latency and reliability improved, with two temporary operational incidents.')
    incidents = [('Catalog sync', 'Catalog sync'), ('Traffic burst', 'Promotion traffic burst')]
    left, right = st.columns(2)
    with left:
        chart(df, s, 'Availability', {'availability_pct': 'Daily availability'}, '%', 3,
              events=incidents[:1])
    with right:
        chart(df, s, 'Error Rate', {'error_rate_pct': 'Daily error rate'}, '%', 2, events=incidents)
    left, right = st.columns(2)
    with left:
        chart(df, s, 'P50 Latency', {'p50_latency_ms': 'P50'}, 'ms', 0, 'pct',
              note='Typical serving experience. Negative change indicates lower latency.')
    with right:
        chart(df, s, 'P95 Latency', {'p95_latency_ms': 'P95'}, 'ms', 0, 'pct', events=incidents,
              note='Tail-performance / degradation risk. Incident values are also listed in Operational Events.')

    section(4, 'AI Quality', 'Grounding and evaluation pass rates improved while escalation declined over the month.')
    left, right = st.columns(2)
    with left:
        chart(df, s, 'Grounding & Evaluation Quality', {'grounded_answer_rate_pct': 'Grounded answers', 'quality_eval_pass_rate_pct': 'Evaluation pass rate'}, '%', events=[('RAG index', 'RAG index refresh')],
              note='The operational note reports improved return-policy grounding following the index refresh. The CSV does not isolate a causal effect.')
    with right:
        chart(df, s, 'Escalation Rate', {'escalation_rate_pct': 'Escalation rate'}, '%',
              note='Escalations declined as grounding and evaluation pass rates improved. Interpretation depends on escalation policy and case mix; denominator not supplied.')

    section(5, 'Spend & Value', 'Inference spend increased with usage while business and quality outcomes continued to improve.')
    left, right = st.columns(2)
    with left:
        chart(df, s, 'Daily Automated Tier-1 Tickets', {'automated_tier1_tickets': 'AI automated'}, 'tickets', 0, 'pct',
              note=f"31-day total: {s['automated_tickets']:,} automated Tier-1 tickets. Ticket counts are separate from model inference requests.")
    with right:
        chart(df, s, 'Daily Inference Spend', {'spend_usd': 'Inference spend'}, 'USD', 2, 'pct',
              note=f"31-day total: ${s['spend']:,.2f}. Inference spend only; excludes implementation, staffing, and other program costs. Budget and target not provided.")
    st.caption(f"First → last day: inference spend {s['trends']['spend_usd']['pct_change']:+.1f}% · automated Tier-1 tickets {s['trends']['automated_tier1_tickets']['pct_change']:+.1f}% · model inference requests {s['trends']['requests']['pct_change']:+.1f}%. Spend grew alongside support volume and model activity; requests are not support tickets.")
    for col, label, value in zip(st.columns(3),
                                ['Automated Tier-1 tickets', 'Total inference spend', 'Inference Spend per Automated Tier-1 Ticket'],
                                [f"{s['automated_tickets']:,}", f"${s['spend']:,.2f}", f"${s['spend_per_automated_ticket']:.4f}"]):
        with col:
            st.metric(label, value)
    st.caption('Calculated unit economics = period inference spend ÷ period automated Tier-1 tickets. This allocates deployment inference spend across automated tickets; it is not total support cost per ticket.')

    st.markdown('### Efficiency Watch')
    fields = [('tokens_per_request', 'Tokens per request', 'tokens/request'),
              ('requests_per_tier1_ticket', 'Requests per Tier-1 ticket', 'requests/ticket'),
              ('tokens_per_tier1_ticket', 'Tokens per Tier-1 ticket', 'tokens/ticket')]
    left, right = st.columns(2)
    for col, (field, label, unit) in zip([left, right], fields[:2]):
        with col:
            chart(df, s, label, {field: 'Calculated daily ratio'}, unit, 2, 'pct')
    left, right = st.columns(2)
    with left:
        field, label, unit = fields[2]
        chart(df, s, label, {field: 'Calculated daily ratio'}, unit, 2, 'pct')
    with right, st.container(border=True, height='stretch'):
        st.markdown('### What to monitor next')
        st.write('Inference work per support ticket increased over the month, while token usage per request remained broadly stable. Current telemetry cannot distinguish whether this reflects more complex cases, deeper conversations, or avoidable orchestration overhead.')
        st.caption('Next instrumentation: ticket intent, ticket complexity, turns per ticket, requests per ticket, retries, retrieval calls, and cost per quality-compliant resolution.')
        st.caption('Tokens/request uses a minimum vertical span of 20% of its daily mean to keep routine variation in context. All three ratios are calculated from daily CSV totals.')

    section(6, 'Estimated Support Capacity Released', 'Illustrative estimate · a translation of the provided AHT outcome, not measured labor savings.')
    with st.container(border=True):
        for col, label, value in zip(st.columns(4),
            ['Implied baseline AHT', 'Minutes saved / automated ticket', 'Estimated support hours released', 'Illustrative FTE-month equivalent'],
            [f"{s['baseline_aht']:.2f} min", f"{s['minutes_saved']:.2f} min", f"{s['support_hours']:,.0f} h", f"{s['fte_months']:.1f}"]):
            with col:
                st.metric(label, value)
        st.caption(f"Calculated: mean daily current AHT {s['current_avg_aht']:.2f} min ÷ (1 − {AHT_REDUCTION_VS_BASELINE:.0%}); saved minutes × {s['automated_tickets']:,} automated tickets ÷ 60; hours ÷ {FTE_MONTH_HOURS} per FTE-month.")
        st.write('Capacity equivalent only; not a staffing reduction estimate. Assumes the stated 35% AHT reduction applies to automated Tier-1 tickets. Does not include implementation, support, labor, or other program costs.')

    section(7, 'Operational Events', 'Events come from operational notes; observed impacts come from daily telemetry.')
    st.markdown(operational_events(df).to_html(index=False, classes='event-table', border=0, escape=True), unsafe_allow_html=True)

    render_scaling_risks(s)
    render_expansion_opportunity()
    with st.expander('Assumptions & Caveats'):
        for item in CAVEATS:
            st.markdown('- ' + item)
    st.caption('Northstar Account Intelligence · Customer Account Health · First 31 production days')


def render_scaling_risks(summary):
    section(8, 'Key Risks & Recommended Actions',
            'The largest unresolved scaling question is why inference work per ticket is rising.')
    trends = summary['trends']
    with st.container(border=True):
        st.markdown('### Rising inference work per ticket')
        left, right = st.columns(2)
        with left:
            st.markdown('**Evidence · calculated daily ratios**')
            rows = []
            for field, label, decimals in [
                ('tokens_per_request', 'Tokens / request', 0),
                ('requests_per_tier1_ticket', 'Requests / Tier-1 ticket', 2),
                ('tokens_per_tier1_ticket', 'Tokens / Tier-1 ticket', 0),
            ]:
                metric = trends[field]
                rows.append(f"| {label} | {metric['first']:,.{decimals}f} → {metric['last']:,.{decimals}f} | {metric['pct_change']:+.1f}% |")
            st.markdown('| Daily ratio | First → last | Change |\n| --- | --- | --- |\n' + '\n'.join(rows))
            st.caption('Tokens per request stayed broadly stable; average requests and total tokens per Tier-1 ticket increased. These are aggregate ratios, not ticket-level traces.')
            st.markdown('**Why it matters**')
            st.write('If extra inference is needed simply to maintain automation, quality and CX outcomes, multi-brand spend could scale faster than customer value.')
            st.markdown('**What we do not yet know**')
            st.write('The increase could reflect more complex tickets, longer conversations, broader automation coverage, or avoidable retries, retrieval calls, loops and workflow overhead. Current telemetry cannot distinguish these explanations.')
        with right:
            st.markdown('**Recommended action**')
            st.write('Instrument and analyze ticket-level unit economics.')
            st.markdown("""Track:
- **Case context:** ticket intent, ticket complexity, turns per ticket.
- **Inference work:** requests per ticket, retrieval calls, retries, tokens per ticket.
- **Outcomes:** automation outcome, grounding / eval pass, AHT saved.
- **Unit economics:** inference cost per quality-compliant resolution.""")
            st.markdown('**Optimization objective**')
            st.write('Reduce compute per quality-compliant resolved ticket while holding automation, quality, CSAT, latency, and reliability constant or improving.')
    left, right = st.columns(2)
    with left, st.container(border=True, height='stretch'):
        st.markdown('### Peak-load resilience')
        st.markdown("""**Evidence:** The Aug 21 promotion traffic burst temporarily increased P95 latency and error rate.

**Why it matters:** Additional brands can introduce overlapping peak events and seasonal traffic spikes.

**Recommended action:** Validate autoscaling thresholds and peak-load behavior before broader rollout.""")
    with right, st.container(border=True, height='stretch'):
        st.markdown('### Knowledge operations')
        st.markdown("""**Evidence:** The Aug 9 catalog sync affected latency and error rate; the Aug 24 RAG refresh was associated with improved grounding.

**Why it matters:** Each brand adds its own catalog, return policies and knowledge-update lifecycle.

**Recommended action:** Standardize brand-level knowledge ingestion, validation, monitoring, refresh and rollback processes.""")


def render_expansion_opportunity():
    section(9, 'Expansion Opportunity & Proposed Next Steps',
            'Use the second-brand pilot to prove customer value and repeatable unit economics, with ticket-level instrumentation from day one.')
    try:
        assumption_label, profiles = load_expansion_assumptions()
    except (OSError, ValueError):
        st.error('Expansion assumptions could not be loaded. Check docs/expansion_assumptions.md before reviewing the pilot recommendation.')
        return
    candidate = 'Northstar Everyday'
    profile = profiles[candidate]
    st.markdown('**How to select the next workload / brand**')
    st.markdown('**Expansion priority ∝ Ticket Volume × Value per Ticket × Automation Confidence × Transferability from Flagship**')
    st.caption('Adjust for inference / implementation cost, quality risk, CX downside and operational complexity. This is a conceptual framework, not a measured formula: the current data lacks intent-level economics.')
    st.write('Portfolio averages are sufficient to judge flagship health; intent-level economics are needed to optimize expansion.')
    left, right = st.columns(2)
    with left, st.container(border=True, height='stretch'):
        st.markdown(f'### Why {candidate}')
        st.caption(assumption_label)
        st.markdown(f"""- **Relative support volume:** {profile['Relative support volume']}
- **Catalog complexity:** {profile['Catalog complexity']}
- **Return / policy structure:** {profile['Return / policy complexity']}
- **Team maturity:** {profile['Team maturity']}""")
        st.write('Everyday likely maximizes high-confidence transferable workload volume.')
        st.caption('Under these assumptions, it likely offers the greatest overlap with flagship-like, high-volume Tier-1 workflows and strong potential for measurable aggregate agent-time savings. Validate both with intent-level data.')
    with right, st.container(border=True, height='stretch'):
        st.markdown('### Controlled second-brand pilot')
        st.write(f'Begin with {candidate}, focused on high-confidence Tier-1 workflows.')
        st.caption('Illustrative pilot workload assumptions, not observed Northstar ticket categories:')
        st.markdown("""- Order status / shipping
- Standard return eligibility
- Straightforward product lookup / availability
- Basic sizing / policy questions""")
        st.markdown('**Connect the pilot to the scaling risk**')
        st.write('Instrument ticket-level unit economics from day one. Determine whether rising inference work per ticket reflects legitimate value creation or avoidable efficiency loss.')
    left, right = st.columns(2)
    with left, st.container(border=True, height='stretch'):
        st.markdown('### 1. Value replication')
        st.markdown("""Can Everyday reproduce:
- Strong automation and AHT improvement
- No material CSAT regression
- Strong grounding / quality
- Stable reliability""")
    with right, st.container(border=True, height='stretch'):
        st.markdown('### 2. Deployment repeatability')
        st.write('Reuse the serving layer, RAG pattern, evaluation framework, monitoring and operating playbook.')
        st.caption('Prove this without significant bespoke engineering, unnecessary model / code forks or unexplained unit-economic deterioration.')
    with st.container(border=True):
        st.markdown('### Broader rollout gate')
        left, right = st.columns(2)
        with left:
            st.markdown("""- Comparable or improving quality
- Stable reliability
- Acceptable cost per quality-compliant automated resolution
- Explainable inference work per ticket""")
        with right:
            st.markdown("""- High reuse of serving / RAG / eval / monitoring architecture
- Clear brand-level knowledge ownership
- Appropriate escalation policy ownership""")
        st.caption('Agree success thresholds with Northstar before launch; the flagship aggregates do not establish intent-level cost targets.')
    st.info('Recommended next step: Proceed with Northstar Everyday as a controlled second-brand pilot, prioritizing high-volume, high-confidence workloads and instrumenting ticket-level unit economics from day one.')
    st.caption('Expansion brand profiles are synthetic / illustrative assumptions defined for the case. See docs/expansion_assumptions.md.')
