"""Strict validation before any customer-facing calculation or rendering."""
from pathlib import Path
import numpy as np
import pandas as pd

DATA_PATH = Path(__file__).resolve().parents[1] / 'data' / 'northstar_flagship_30_day_metrics.csv'
NUMERIC_COLUMNS = (
    'requests input_tokens output_tokens total_tokens spend_usd p50_latency_ms '
    'p95_latency_ms error_rate_pct availability_pct tier1_tickets '
    'automated_tier1_tickets automation_rate_pct avg_handle_time_min csat_score '
    'grounded_answer_rate_pct quality_eval_pass_rate_pct escalation_rate_pct'
).split()
REQUIRED_COLUMNS = ['date', 'deployment', *NUMERIC_COLUMNS, 'operational_note']
AUTOMATION_ROUNDING_TOLERANCE_PP = 0.06

class DataValidationError(ValueError):
    """An actionable dataset issue suitable for display to a reviewer."""


def validate_data(raw: pd.DataFrame) -> pd.DataFrame:
    missing = sorted(set(REQUIRED_COLUMNS) - set(raw.columns))
    if missing:
        raise DataValidationError('Missing required columns: ' + ', '.join(missing))
    df = raw.copy()
    if df.empty:
        raise DataValidationError('The dataset has no daily records.')
    df['date'] = pd.to_datetime(df['date'], errors='coerce', format='%Y-%m-%d')
    if df['date'].isna().any():
        raise DataValidationError('Every date must be valid and formatted YYYY-MM-DD.')
    if df['date'].duplicated().any():
        raise DataValidationError('Duplicate dates found; expected one record per day.')
    if df['deployment'].isna().any() or df['deployment'].nunique() != 1:
        raise DataValidationError('Expected exactly one non-null flagship deployment.')
    for field in NUMERIC_COLUMNS:
        df[field] = pd.to_numeric(df[field], errors='coerce')
        if not np.isfinite(df[field]).all() or (df[field] < 0).any():
            raise DataValidationError(f'{field} must contain finite, non-negative numbers.')
    for field in ['requests', 'tier1_tickets', 'avg_handle_time_min']:
        if (df[field] <= 0).any():
            raise DataValidationError(f'{field} must be positive to calculate valid ratios.')
    counts = ['requests', 'input_tokens', 'output_tokens', 'total_tokens',
              'tier1_tickets', 'automated_tier1_tickets']
    if any((df[c] % 1 != 0).any() for c in counts):
        raise DataValidationError('Request, token, and ticket counts must be whole numbers.')
    rates = [c for c in NUMERIC_COLUMNS if c.endswith('_pct')] + ['csat_score']
    if any((df[c] > 100).any() for c in rates):
        raise DataValidationError('Percentage metrics and CSAT must be between 0 and 100.')
    if (df['automated_tier1_tickets'] > df['tier1_tickets']).any():
        raise DataValidationError('Automated tickets cannot exceed total Tier-1 tickets.')
    if (df['p50_latency_ms'] > df['p95_latency_ms']).any():
        raise DataValidationError('P50 latency cannot exceed P95 latency.')
    if not (df['total_tokens'] == df['input_tokens'] + df['output_tokens']).all():
        raise DataValidationError('Token reconciliation failed: total_tokens must equal input_tokens + output_tokens.')
    expected = df['automated_tier1_tickets'] / df['tier1_tickets'] * 100
    if ((expected - df['automation_rate_pct']).abs() > AUTOMATION_ROUNDING_TOLERANCE_PP).any():
        raise DataValidationError('Automation rates do not reconcile with ticket counts (0.06 pp rounding tolerance).')
    df['operational_note'] = df['operational_note'].fillna('').astype(str).str.strip()
    df = df.sort_values('date').reset_index(drop=True)
    if len(df) != 31 or not df['date'].diff().dropna().dt.total_seconds().eq(86400).all():
        raise DataValidationError('This first-31-days view requires 31 consecutive daily observations.')
    return df


def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    try:
        return validate_data(pd.read_csv(path))
    except (OSError, pd.errors.ParserError, UnicodeError) as exc:
        raise DataValidationError(f'Unable to read the metrics CSV at data/{path.name}: {exc}') from exc
