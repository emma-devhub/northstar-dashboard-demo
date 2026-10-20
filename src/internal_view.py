"""Internal-only account planning; no internal inputs flow into customer rendering."""
from html import escape
import pandas as pd
import streamlit as st
from src.customer_view import STYLE, section, chart, trend
from src.charts import ticket_volume_chart
from src.expansion import load_expansion_assumptions
from src.internal_assumptions import load_internal_assumptions
from src.health import calculate_account_health
from src.metrics import operational_events

INTERNAL_STYLE = '''<style>
.qbr-summary {display:grid;grid-template-columns:1fr 1fr 1.4fr;gap:12px;margin:16px 0;}
.qbr-card {border:1px solid #E2E9ED;border-radius:8px;padding:15px 18px;background:white;}
.qbr-label {font-size:.72rem;font-weight:700;color:#486071;letter-spacing:.04rem;text-transform:uppercase;}
.qbr-number {font-size:2.3rem;font-weight:650;letter-spacing:-.06rem;color:#182C3D;line-height:1.3;}
.qbr-status {color:#087F78;font-weight:650;font-size:1.12rem;margin:6px 0;}
.qbr-note {color:#486071;font-size:.8rem;line-height:1.5;}
.qbr-watch {color:#A96717;}
.qbr-bar-row {display:grid;grid-template-columns:2.4fr 2fr 55px 1.1fr;gap:16px;align-items:center;margin:15px 0;font-size:.87rem;}
.qbr-track {height:9px;background:#EDF1F4;border-radius:5px;overflow:hidden;}
.qbr-bar {height:100%;background:#087F78;border-radius:5px;}
.qbr-score {font-size:1.1rem;font-weight:650;color:#182C3D;text-align:right;}
.qbr-evidence {font-size:.72rem;color:#486071;}
.qbr-table-scroll {overflow-x:auto;}
.qbr-table {width:100%;border-collapse:collapse;font-size:.82rem;line-height:1.5;}
.qbr-table th {background:#F5F8FA;color:#486071;text-align:left;font-size:.72rem;}
.qbr-table td,.qbr-table th {padding:11px 12px;border-bottom:1px solid #E2E9ED;vertical-align:top;overflow-wrap:anywhere;}
.qbr-table td:first-child {font-weight:600;color:#182C3D;}
.qbr-callout {background:#FFF6E7;border-left:3px solid #A96717;padding:13px 16px;border-radius:3px;color:#486071;font-size:.88rem;margin:12px 0;}
@media(max-width:700px){.qbr-summary{grid-template-columns:1fr;}.qbr-bar-row{grid-template-columns:1.9fr 1fr 45px;gap:8px;}.qbr-evidence{grid-column:1/-1;}}
</style>'''


def table(rows):
    if not rows:
        return
    keys = list(rows[0])
    head = ''.join(f'<th>{escape(key)}</th>' for key in keys)
    body = ''.join('<tr>' + ''.join(f'<td>{escape(str(row[key]))}</td>' for key in keys) + '</tr>' for row in rows)
    st.markdown(f'<div class="qbr-table-scroll"><table class="qbr-table"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>', unsafe_allow_html=True)


def callout(text):
    st.markdown(f'<div class="qbr-callout">{escape(text)}</div>', unsafe_allow_html=True)


def render_internal_dashboard(df, summary):
    scenario = load_internal_assumptions()
    brand_label, profiles = load_expansion_assumptions()
    if {item['brand'] for item in scenario['pipeline']} != set(profiles):
        raise ValueError('Internal pipeline must cover exactly the canonical expansion brands.')
    health = calculate_account_health(df, summary, scenario)
    t = summary['trends']
    st.markdown(STYLE + INTERNAL_STYLE, unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">NORTHSTAR / FIREWORKS INTERNAL ACCOUNT PLANNING</div>', unsafe_allow_html=True)
    st.title('Northstar — Internal QBR')
    st.write('Account condition, expansion gates and resource decisions')
    st.caption(f"Fireworks account, engineering / deployment and leadership teams · Telemetry: {df.date.min():%b %d}–{df.date.max():%b %d, %Y} · Planning review: {scenario['review_date']}")
    st.caption('Internal-only scenario planning. August telemetry does not establish current production health in October. No customer-safe export is implied by this view.')
    status_color = '#087F78' if health['status'] == 'HEALTHY' else '#A96717' if health['status'] == 'WATCH' else '#B42318'
    st.markdown(f'''<div class="qbr-summary">
<div class="qbr-card"><div class="qbr-label">Account health · provisional</div><div class="qbr-number">{health['score']:.1f} <span style="font-size:1rem">/ 100</span></div><div class="qbr-status" style="color:{status_color}">{health['status']}</div><div class="qbr-note">Weighted analyst rubric, not a predictive model</div></div>
<div class="qbr-card"><div class="qbr-label">Evidence confidence</div><div class="qbr-number" style="font-size:1.65rem">Medium–High</div><div class="qbr-note">Production evidence is strong within a limited window. Commercial context is assumed.</div></div>
<div class="qbr-card"><div class="qbr-label">Expansion status</div><div class="qbr-status">Pilot-ready / portfolio rollout gated</div><div class="qbr-note">Recommend controlled Everyday validation. Broader spend, staffing and launch commitments remain gated.</div></div></div>''', unsafe_allow_html=True)
    st.caption('Health measures current account condition; confidence measures how much direct evidence supports that assessment. Confidence is a qualitative overlay, not an input to the score.')

    section(1, 'Account Health', 'Strong flagship outcomes support a pilot; economics, commercial evidence and portability constrain portfolio commitment.')
    bars = []
    for p in health['pillars']:
        color = '#A96717' if p['score'] < 80 else '#087F78'
        basis = ' · Primarily assumption-driven' if p['key'] == 'relationship' else ''
        bars.append(f'<div class="qbr-bar-row"><div>{escape(p["name"])} <span class="qbr-note">{p["weight"]:.0%}</span></div><div class="qbr-track"><div class="qbr-bar" style="width:{p["score"]:.2f}%;background:{color}"></div></div><div class="qbr-score">{p["score"]:.1f}</div><div class="qbr-evidence">{p["confidence"]} confidence{basis}</div></div>')
    st.markdown(''.join(bars), unsafe_allow_html=True)
    left, right = st.columns(2)
    with left, st.container(border=True):
        st.markdown('### Top health drivers')
        st.markdown('- Strong provided business outcomes: 70% automation, 35% AHT reduction, +12 CSAT points\n- Increasing observed automation and automated-ticket volume\n- Improving grounding / evaluation quality\n- Improving P50 / P95 latency and error performance')
    with right, st.container(border=True):
        st.markdown('### Top watch items')
        st.markdown('- Rising inference work per Tier-1 ticket\n- Second-brand portability remains unproven\n- Expansion budget not established (scenario)\n- Relationship / commercial evidence is primarily assumed')
    if health['cap_applied']:
        st.warning(f"Critical-risk cap active: {', '.join(health['critical_flags'])}. Raw weighted score {health['raw_score']:.2f}; displayed score capped at 79 (WATCH) or lower.")
    else:
        st.caption('Critical-risk override: no case-provided critical red flag, so no cap is applied. Any active critical issue caps overall health at 79 (Yellow / WATCH), regardless of a higher weighted average.')
    with st.expander('Score methodology, component rules and evidence'):
        st.write('All component ratings and thresholds are illustrative internal policy choices. They are not contractual targets, probabilities or a calibrated health model. Healthy ≥80; Watch 60–<80; At risk <60. Critical-risk cap: 79.')
        st.code('Health = 0.25 × Value + 0.25 × Technical + 0.15 × Economics\n       + 0.15 × Relationship + 0.20 × Expansion', language=None)
        table([{'Pillar':p['name'], 'Score':f"{p['score']:.2f}", 'Weight':f"{p['weight']:.0%}", 'Contribution':f"{p['contribution']:.4f}", 'Confidence':p['confidence']} for p in health['pillars']])
        st.caption(f"Unrounded weighted sum: {health['raw_score']:.4f}; display: {health['score']:.1f}. Calculate with full precision before rounding.")
        for p in health['pillars']:
            st.markdown('#### ' + p['name'])
            table([{'Component':c['component'], 'Weight':f"{c['weight']:.0%}", 'Score':str(c['score']), 'Basis / rule':c['basis'] + '. ' + c['rule'], 'Evidence / limitation':c['evidence']} for c in health['components'] if c['pillar']==p['key']])
        st.caption('Why not 100: 31 days, unspecified baseline/eval methodologies, no causal attribution, recovered incidents, unknown intent economics and unverified internal assumptions. Critical examples: severe reliability breach, major quality/safety failure, active churn/renewal threat, unresolved security/compliance blocker, executive sponsor loss.')

    section(2, 'Customer Value & Production Health', 'Compact daily evidence, not a second copy of every customer chart. Endpoint improvements do not erase temporary incidents.')
    st.caption('Observed synthetic CSV: 31 daily points per series. Provided baseline outcomes are separate from within-month changes. Data-relative line axes preserve trend visibility; stacked ticket bars start at zero.')
    incidents = [('Catalog sync', 'Catalog sync'), ('Traffic burst', 'Promotion traffic burst')]
    volume_figure = ticket_volume_chart(df)
    # Compact internal panel: daily percentages remain in hover and the adjacent trend.
    volume_figure.update_traces(text=None, textposition='none')
    volume_figure.update_layout(height=225)
    configs = [
        ('Automation', {'automation_rate_pct':'Automated share'}, '%', 1, 'pp', (), None),
        ('Automated & Total Tier-1 Tickets', {'tier1_tickets':'Total demand','automated_tier1_tickets':'AI automated'}, 'tickets', 0, 'pct', (), volume_figure),
        ('Inference Spend', {'spend_usd':'Daily inference spend'}, 'USD', 2, 'pct', (), None),
        ('Error Rate', {'error_rate_pct':'Daily error rate'}, '%', 2, 'pp', incidents, None),
        ('Availability', {'availability_pct':'Daily availability'}, '%', 3, 'pp', incidents[:1], None),
        ('P95 Latency', {'p95_latency_ms':'P95'}, 'ms', 0, 'pct', incidents, None),
    ]
    for i in range(0,len(configs),2):
        for col, config in zip(st.columns(2), configs[i:i+2]):
            title, series, unit, dec, change, events, figure = config
            with col:
                chart(df, summary, title, series, unit, dec, change, events=events, height=225, figure=figure)
    left, right = st.columns(2)
    with left:
        chart(df, summary, 'Grounding & Evaluation', {'grounded_answer_rate_pct':'Grounding','quality_eval_pass_rate_pct':'Eval pass'}, '%', events=[('RAG index','RAG refresh')], height=225)
    with right, st.container(border=True):
        st.markdown('### Outcomes & recovery context')
        st.write(f"Provided: 70% automation, 35% AHT reduction and +12 CSAT points vs pre-deployment. Observed AHT {t['avg_handle_time_min']['first']:.2f} → {t['avg_handle_time_min']['last']:.2f} min; CSAT {t['csat_score']['first']:.1f} → {t['csat_score']['last']:.1f}.")
        st.caption('P50: ' + trend(summary,'p50_latency_ms',' ms',0,'pct') + ' · Escalation: ' + trend(summary,'escalation_rate_pct','%',1))
        st.write('Aug 9 catalog sync was mitigated the same day. Aug 21 promotion burst prompted an autoscaling-threshold adjustment. Recovery is visible; multi-brand operating readiness is still unproven.')
        st.caption('Escalation denominator and eval methodology / sample sizes are unspecified. Lower escalation alone does not establish better quality. No persistent regression is visible in this one-month window.')
    with st.expander('Observed operational events'):
        table(operational_events(df).to_dict('records'))

    section(3, 'Economics & Support Burden', 'Good customer outcomes, but unit economics and marginal support burden are not yet fully explained.')
    for col, field, label, dec in zip(st.columns(3),
            ['tokens_per_request','requests_per_tier1_ticket','tokens_per_tier1_ticket'],
            ['Tokens / request','Requests / Tier-1 ticket','Tokens / Tier-1 ticket'],[0,2,0]):
        with col:
            st.metric(label, f"{t[field]['last']:,.{dec}f}", f"{t[field]['pct_change']:+.1f}% vs first day", delta_color='off')
            st.caption(f"{t[field]['first']:,.{dec}f} → {t[field]['last']:,.{dec}f} · calculated from CSV")
    callout('Tokens/request are broadly stable. More requests and tokens per Tier-1 ticket could reflect harder tickets, deeper automation, broader coverage or avoidable orchestration. Current telemetry cannot distinguish these causes. Expansion could worsen gross economics and engineering burden if additional compute only preserves existing outcomes.')
    left, right = st.columns(2)
    with left:
        chart(df, summary, 'Requests per Tier-1 Ticket', {'requests_per_tier1_ticket':'Inference work'}, 'requests/ticket',2,'pct',height=225)
    with right:
        chart(df, summary, 'Tokens per Tier-1 Ticket', {'tokens_per_tier1_ticket':'Inference work'}, 'tokens/ticket',0,'pct',height=225)
    st.caption(rf"31-day inference spend \${summary['spend']:,.2f} / {summary['automated_tickets']:,} automated tickets = \${summary['spend_per_automated_ticket']:.4f} per automated-ticket allocation. Deployment spend cannot be matched to quality-compliant resolutions. It excludes implementation and labor; this is not gross margin or total support cost.")
    left, right = st.columns(2)
    with left, st.container(border=True):
        st.markdown('### Current support burden: ' + scenario['support']['current'])
        st.caption(scenario['label'])
        st.write(scenario['support']['assumption'])
        st.write('Scaling watch: bespoke model work, manual knowledge operations, fragmented evaluation / monitoring and rising inference work per ticket.')
    with right, st.container(border=True):
        watch = scenario['renewal_competitive_watch']
        st.markdown('### Renewal & Competitive Risk')
        st.caption('Potential risks to validate · ' + scenario['label'])
        st.write('**Expansion appetite:** ' + watch['expansion'])
        st.write('**Competitive exposure:** ' + watch['competition'])
        st.write('**Monitor:** ' + watch['monitor'])
        st.write('**Decision needed:** ' + watch['decision'])

    section(4, 'Top Three Internal Risks', 'Prioritize instrumentation and reusable operations before promising portfolio scale.')
    table([
        {'Risk':'1 · Inference economics / orchestration efficiency','Evidence / unknown':f"Requests/ticket {t['requests_per_tier1_ticket']['pct_change']:+.1f}%; tokens/ticket {t['tokens_per_tier1_ticket']['pct_change']:+.1f}%. Legitimate deeper automation vs avoidable overhead unknown.",'Internal consequence':'Additional compute and bespoke optimization may erode gross economics; magnitude unknown.','Action / owner':'Account Manager + Deployment Engineer / Data Science: check customer impact and investigate intent-level economics before diagnosing a cost problem. Oct 23 proposal.'},
        {'Risk':'2 · Cross-brand repeatability','Evidence / unknown':'Only one brand observed. Architecture portability, repeatable implementation, brand quality and operating model unproven.','Internal consequence':'Four bespoke deployments could consume resources without a reusable platform.','Action / owner':'Run controlled Everyday validation before portfolio commitment. Account Team + Northstar CX · Oct 26 scope proposal.'},
        {'Risk':'3 · Operational scale / knowledge management','Evidence / unknown':'Catalog-sync and promotion-traffic incidents recovered. Five brands multiply refreshes, policies and peak-load failure modes.','Internal consequence':'Manual knowledge / incident work could increase marginal support effort.','Action / owner':'Standardize ingestion, rollback, autoscaling and runbooks. Engineering + Knowledge Owner · Oct 28–30 proposals.'}])
    st.caption('Consequences are risk hypotheses, not measured losses. Target dates reference the illustrative execution plan below; relationship / commercial uncertainty is tracked separately.')

    section(5, 'Relationship & Commercial', 'Assumed executive support is encouraging; operating coverage, procurement and funding need verification.')
    st.caption(scenario['label'] + ' Source: docs/internal_qbr_assumptions.md. Primarily assumption-driven; LOW evidence confidence.')
    table(scenario['stakeholders'])
    left, right = st.columns(2)
    with left, st.container(border=True):
        st.markdown('### Renewal risk: ' + scenario['relationship']['renewal']['status'])
        st.write(scenario['relationship']['renewal']['assumption'])
        st.caption('Retention and expansion are separate questions. No renewal date or confirmed lack of expansion intent is supplied.')
    with right, st.container(border=True):
        st.markdown('### Competitive risk: ' + scenario['relationship']['competition']['status'])
        st.write(scenario['relationship']['competition']['assumption'])
        st.caption('Monitor brand / function pilots and vendor-selection plans with the Account Manager. No named competitor or active competitive process is assumed.')
    callout(scenario['relationship']['budget']['assumption'])

    section(6, 'Expansion Pipeline', 'Internal expansion pipeline — illustrative sequencing based on synthetic profiles. No revenue estimate or committed launch schedule.')
    st.caption(brand_label + ' Source: docs/expansion_assumptions.md. Internal planning overlay: docs/internal_qbr_assumptions.md.')
    for i in range(0,len(scenario['pipeline']),2):
        for col, item in zip(st.columns(2), scenario['pipeline'][i:i+2]):
            profile = profiles[item['brand']]
            with col, st.container(border=True):
                st.markdown('### ' + item['brand'])
                st.caption(item['stage'] + ' · Priority ' + item['priority'])
                st.write('**Role:** ' + profile['Expansion role'])
                st.write('**Hypothesis:** ' + profile['Primary hypothesis'])
                st.write('**Blocker:** ' + item['blocker'])
                st.write('**Next gate:** ' + item['gate'])
                st.caption('Internal confidence: ' + item['confidence'] + '\n\nProposed owner: ' + item['owner'])

    section(7, 'Internal Dependencies', 'These are open readiness requirements, not evidence that the work has already been completed.')
    groups = [
        ('Data / telemetry','Intent-level volume, human AHT, automation, grounding / eval, escalation and inference cost. Add turns, requests, retries and retrieval calls.','Fireworks Data Science / Deployment + Northstar CX'),
        ('Platform / engineering','Reusable brand configuration, brand-isolated RAG, catalog ingestion / rollback, peak-load validation and common eval harness.','Fireworks Engineering / Deployment'),
        ('Customer / operating model','Knowledge owner per brand, escalation-policy owner, support-team readiness and agreed eligible pilot workloads.','Northstar CX + brand operations; Fireworks Account Lead'),
        ('Commercial','Pilot budget approval, broader-rollout investment framework and confirmed procurement / contracting path.','Fireworks Account Lead + Northstar VP CX / Finance')]
    for i in range(0,4,2):
        for col, (name,body,owner) in zip(st.columns(2),groups[i:i+2]):
            with col, st.container(border=True):
                st.markdown('### ' + name)
                st.write(body)
                st.caption('OPEN · Proposed accountable roles: ' + owner)

    section(8, 'Decisions Needed', 'Recommendations for the next internal / joint review. None is recorded as approved.')
    table([
        {'Decision':'1 · Approve Everyday as validation target?','Recommendation':'YES, subject to intent-level workload validation.','Decision owner (proposed)':'Fireworks Account Lead + Northstar VP CX'},
        {'Decision':'2 · What explains rising inference work / ticket?','Recommendation':scenario['renewal_competitive_watch']['decision'],'Decision owner (proposed)':'Fireworks Account Manager + Deployment Engineer / Data Science'},
        {'Decision':'3 · Commit to all four brands now?','Recommendation':'NO. Use stage-gated expansion; broad funding is not committed.','Decision owner (proposed)':'Fireworks leadership + Northstar executives'},
        {'Decision':'4 · Default technical architecture?','Recommendation':'Shared platform + brand prompt / isolated RAG / brand eval. Fine-tune only for persistent eval-proven gaps.','Decision owner (proposed)':'Fireworks Engineering + Northstar VP Engineering'},
        {'Decision':'5 · What gates portfolio rollout?','Recommendation':'Repeatable quality, stable acceptable unit economics, architecture reuse, operating ownership and peak-load readiness.','Decision owner (proposed)':'Joint executive go / no-go review'}])
    st.caption('Optimize compute per quality-compliant resolved ticket, subject to automation, quality and CSAT holding / improving and latency / reliability meeting agreed targets. EBR pilot thresholds remain illustrative and require joint agreement.')

    section(9, 'Next Actions', 'Role-based proposed owners and target dates make the plan actionable without inventing named people or completed work.')
    st.caption(scenario['action_label'] + ' All statuses are proposed; dates are not commitments. The go / no-go review is pilot-launch readiness, not pilot completion.')
    table([{**action,'Target':pd.Timestamp(action['Target']).strftime('%b %d, %Y')} for action in scenario['actions']])
    with st.expander('Provenance and review boundaries'):
        st.write('Provided: case headline outcomes. Observed: August synthetic CSV and operational notes. Calculated: shared metric functions. Illustrative: health rubric, internal scenario ratings, brand profiles, pipeline priorities, owners, dates and recommendations.')
        st.write('This local case app separates rendered views, not authenticated roles. Navigation is not access control. Do not use it to publish real confidential internal content to customer audiences without an authorization boundary.')
        st.caption('No ARR, contract value, margin %, staffing count, named competitor or renewal date is invented. Internal assumptions are never loaded by the customer rendering branch. Portfolio averages judge flagship health; intent-level economics are needed to optimize expansion.')
