"""Daily monitoring charts with data-relative axes and data-backed events."""
import math

import plotly.graph_objects as go

COLORS = ['#087F78', '#426FA4', '#A96717']
TREND_CHART_HEIGHT = 260
FULL_WIDTH_CHART_HEIGHT = 290
# Visual spans, in each metric's native units; these are not performance targets.
MIN_AXIS_SPANS = {
    'automation_rate_pct': 8,
    'avg_handle_time_min': 1.2,
    'csat_score': 6,
    'availability_pct': 0.3,
    'error_rate_pct': 2,
    'p50_latency_ms': 200,
    'p95_latency_ms': 600,
    'grounded_answer_rate_pct': 8,
    'quality_eval_pass_rate_pct': 8,
    'escalation_rate_pct': 6,
    'spend_usd': 25,
    'requests_per_tier1_ticket': 3,
    'tokens_per_tier1_ticket': 4000,
}
TOKENS_PER_REQUEST_MIN_SPAN_RATIO = 0.20


def get_padded_range(series, padding_ratio=0.10, min_span=None, bounds=None):
    """Pad observed extrema; retain context for small changes and respect bounds.

    Expects a flat sequence, including both series for a shared axis. Constant
    data gets a nonzero span. Clamping shifts the window to retain its span when
    possible, while always including the observations.
    """
    values = [float(value) for value in series]
    if not values or not all(math.isfinite(value) for value in values):
        raise ValueError('Axis values must be finite and nonempty.')
    if padding_ratio < 0 or (min_span is not None and min_span <= 0):
        raise ValueError('Axis padding must be nonnegative and minimum span positive.')
    low, high = min(values), max(values)
    center = (low + high) / 2
    span = max((high - low) * (1 + 2 * padding_ratio), min_span or 0)
    if span == 0:
        span = max(abs(center) * 0.10, 1)
    lower, upper = center - span / 2, center + span / 2
    if bounds:
        floor, ceiling = bounds
        if (floor is not None and low < floor) or (ceiling is not None and high > ceiling):
            raise ValueError('Observed data falls outside the logical axis bounds.')
        if floor is not None and lower < floor:
            upper += floor - lower
            lower = floor
        if ceiling is not None and upper > ceiling:
            lower -= upper - ceiling
            upper = ceiling
        if floor is not None:
            lower = max(floor, lower)
        if ceiling is not None:
            upper = min(ceiling, upper)
    return [lower, upper]


def nice_tick_step(span, target_intervals=5):
    """Choose readable 1/2/2.5/5/10 increments without rounding the data."""
    raw = span / target_intervals
    magnitude = 10 ** math.floor(math.log10(raw))
    for multiplier in (1, 2, 2.5, 5, 10):
        if multiplier * magnitude >= raw:
            return multiplier * magnitude


def daily_chart(df, series, unit, events=(), height=TREND_CHART_HEIGHT):
    fields = list(series)
    values = df[fields].to_numpy().ravel()
    min_span = max((MIN_AXIS_SPANS.get(field, 0) for field in fields), default=0)
    if 'tokens_per_request' in fields:
        # A minimum 20%-of-mean window keeps modest token noise in context.
        min_span = max(min_span, float(df.tokens_per_request.mean()) * TOKENS_PER_REQUEST_MIN_SPAN_RATIO)
    bounds = (0, 100) if unit in ('%', 'points') else (0, None)
    axis_range = get_padded_range(values, min_span=min_span or None, bounds=bounds)
    step = nice_tick_step(axis_range[1] - axis_range[0])
    decimals = max(0, -math.floor(math.log10(step)))
    if step / (10 ** math.floor(math.log10(step))) == 2.5:
        decimals += 1

    fig = go.Figure()
    for idx, (field, label) in enumerate(series.items()):
        fig.add_trace(go.Scatter(
            x=df.date, y=df[field], name=label, mode='lines+markers',
            line=dict(color=COLORS[idx % len(COLORS)], width=2.5,
                      dash='solid' if idx == 0 else 'dash'),
            marker=dict(size=4),
            hovertemplate='%{x|%b %d}<br>' + label + ': %{y:,.2f} ' + unit + '<extra></extra>'))
    for token, label in events:
        rows = df[df.operational_note.str.contains(token, regex=False)]
        for _, row in rows.iterrows():
            field = fields[-1]
            fig.add_annotation(x=row.date, y=row[field], text=row.date.strftime('%b') + f' {row.date.day} · ' + label,
                               showarrow=True, arrowhead=0, ax=0, ay=-27,
                               font=dict(size=10, color='#8A5316'),
                               bgcolor='#FFF6E7', borderpad=3, arrowcolor='#A96717')
    fig.update_layout(
        height=height, margin=dict(l=12, r=15, t=35 if events else 12, b=12),
        paper_bgcolor='white', plot_bgcolor='white',
        font=dict(family='Helvetica Neue, sans-serif', color='#486071', size=12),
        hovermode='x unified', showlegend=len(series) > 1,
        legend=dict(orientation='h', y=-0.24, x=0, font=dict(size=11)),
        xaxis=dict(tickformat='%b %d', dtick=7 * 86400000,
                   tick0=df.date.min(), showgrid=False,
                   range=[df.date.min(), df.date.max()], automargin=True),
        yaxis=dict(title=unit, range=axis_range, tick0=0, dtick=step,
                   tickformat=f',.{decimals}f', gridcolor='#EDF1F4',
                   zeroline=False, automargin=True),
    )
    return fig


def ticket_volume_chart(df):
    """One daily total, split into automated and remaining Tier-1 tickets."""
    from datetime import timedelta

    automated = df.automated_tier1_tickets
    remaining = df.tier1_tickets - automated
    context = list(zip(df.tier1_tickets, df.automation_rate_pct))
    fig = go.Figure([
        go.Bar(
            x=df.date, y=automated, name='AI automated',
            marker_color=COLORS[0],
            text=[f'{rate:.1f}%' for rate in df.automation_rate_pct],
            textposition='inside', textangle=-90, insidetextanchor='middle', constraintext='none',
            textfont=dict(color='white', size=10), customdata=context,
            hovertemplate='%{x|%b %d}<br>AI automated: %{y:,.0f} tickets'
                          '<br>Automation: %{customdata[1]:.1f}%'
                          '<br>Total Tier-1: %{customdata[0]:,.0f} tickets<extra></extra>',
        ),
        go.Bar(
            x=df.date, y=remaining, name='Other Tier-1 tickets',
            marker_color='#C7D9E8', customdata=context,
            hovertemplate='%{x|%b %d}<br>Other Tier-1: %{y:,.0f} tickets'
                          '<br>Total Tier-1: %{customdata[0]:,.0f} tickets<extra></extra>',
        ),
    ])
    maximum = float(df.tier1_tickets.max()) * 1.08
    fig.update_layout(
        height=TREND_CHART_HEIGHT, barmode='stack', bargap=.18,
        margin=dict(l=12, r=15, t=12, b=12),
        paper_bgcolor='white', plot_bgcolor='white',
        font=dict(family='Helvetica Neue, sans-serif', color='#486071', size=12),
        hovermode='x unified',
        legend=dict(orientation='h', y=-.24, x=0, font=dict(size=11), traceorder='normal'),
        xaxis=dict(tickformat='%b %d', dtick=7 * 86400000, tick0=df.date.min(),
                   range=[df.date.min() - timedelta(hours=12), df.date.max() + timedelta(hours=12)],
                   showgrid=False, automargin=True),
        yaxis=dict(title='tickets', range=[0, maximum], tick0=0,
                   dtick=nice_tick_step(maximum), tickformat=',.0f',
                   gridcolor='#EDF1F4', zeroline=False, automargin=True),
    )
    return fig
