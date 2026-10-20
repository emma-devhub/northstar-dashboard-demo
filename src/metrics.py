"""Shared observed summaries and explicitly illustrative value calculations."""
import pandas as pd

AHT_REDUCTION_VS_BASELINE = 0.35
FTE_MONTH_HOURS = 160
PROVIDED_AUTOMATION_PCT = 70
PROVIDED_CSAT_LIFT_POINTS = 12


def calculate_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result['tokens_per_request'] = result.total_tokens / result.requests
    result['requests_per_tier1_ticket'] = result.requests / result.tier1_tickets
    result['tokens_per_tier1_ticket'] = result.total_tokens / result.tier1_tickets
    return result


def calculate_summary_metrics(df: pd.DataFrame) -> dict:
    trends = {}
    for col in df.select_dtypes(include='number'):
        first, last = float(df[col].iloc[0]), float(df[col].iloc[-1])
        trends[col] = {'first': first, 'last': last, 'change': last - first,
                       'pct_change': (last / first - 1) * 100 if first else None}
    spend = float(df.spend_usd.sum())
    tickets = int(df.automated_tier1_tickets.sum())
    # Arithmetic mean of daily AHT: ticket-level weighting is not specified.
    current_aht = float(df.avg_handle_time_min.mean())
    baseline_aht = current_aht / (1 - AHT_REDUCTION_VS_BASELINE)
    minutes_saved = baseline_aht - current_aht
    hours = tickets * minutes_saved / 60
    return dict(trends=trends, spend=spend, automated_tickets=tickets,
                total_requests=int(df.requests.sum()), total_tokens=int(df.total_tokens.sum()),
                spend_per_automated_ticket=spend / tickets if tickets else None,
                current_avg_aht=current_aht, baseline_aht=baseline_aht,
                minutes_saved=minutes_saved, support_hours=hours,
                fte_months=hours / FTE_MONTH_HOURS)


def operational_events(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for idx, row in df[df.operational_note.ne('')].iterrows():
        previous = df.iloc[idx - 1] if idx else None
        note = row.operational_note
        if 'Catalog sync' in note:
            impact = f'Error {row.error_rate_pct:.2f}%; P95 {row.p95_latency_ms:,.0f} ms; availability {row.availability_pct:.3f}%'
            response = 'Mitigated the same day, per operational note.'
        elif 'Traffic burst' in note:
            impact = f'Error {row.error_rate_pct:.2f}%; P95 {row.p95_latency_ms:,.0f} ms'
            response = 'Autoscaling threshold adjusted, per operational note.'
        elif 'RAG index' in note:
            impact = f'Grounding {row.grounded_answer_rate_pct:.1f}%'
            if previous is not None:
                impact += f' (prior day {previous.grounded_answer_rate_pct:.1f}%)'
            response = 'Return-policy grounding improved, per operational note; causal effect is not isolated.'
        else:
            impact, response = 'See daily telemetry; impact not classified.', 'Review operational note.'
        rows.append({'Date': row.date.strftime('%b %d'), 'Event': note,
                     'Observed impact': impact, 'Response / learning': response})
    return pd.DataFrame(rows)
