"""Focused checks for analytical correctness and failure behavior."""
import unittest
import json
import math
import tempfile
from pathlib import Path
import pandas as pd
from streamlit.testing.v1 import AppTest
from src.charts import get_padded_range, daily_chart, ticket_volume_chart
from src.expansion import load_expansion_assumptions, ASSUMPTIONS_PATH
from src.data import load_data, validate_data, DataValidationError, REQUIRED_COLUMNS
from src.metrics import calculate_derived_metrics, calculate_summary_metrics, operational_events

ROOT = Path(__file__).resolve().parents[1]

class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.raw = pd.read_csv(ROOT / 'data' / 'northstar_flagship_30_day_metrics.csv')

    def test_schema_required_columns(self):
        for column in REQUIRED_COLUMNS:
            with self.subTest(column=column), self.assertRaises(DataValidationError):
                validate_data(self.raw.drop(columns=column))

    def test_corrupt_data(self):
        for column, value in [('date', 'bad'), ('total_tokens', 0),
                              ('automation_rate_pct', 0), ('requests', 0),
                              ('p95_latency_ms', -1), ('csat_score', float('inf'))]:
            with self.subTest(column=column):
                corrupt = self.raw.copy()
                corrupt.loc[0, column] = value
                with self.assertRaises(DataValidationError):
                    validate_data(corrupt)
        duplicate = self.raw.copy()
        duplicate.loc[1, 'date'] = duplicate.loc[0, 'date']
        with self.assertRaises(DataValidationError):
            validate_data(duplicate)
        with self.assertRaises(DataValidationError):
            validate_data(self.raw.iloc[1:])

    def test_sort_and_null_notes(self):
        df = validate_data(self.raw.iloc[::-1])
        self.assertTrue(df.date.is_monotonic_increasing)
        self.assertFalse(df.operational_note.isna().any())
        self.assertEqual(len(operational_events(df)), 3)

    def test_independent_totals_and_formulas(self):
        df = calculate_derived_metrics(load_data())
        s = calculate_summary_metrics(df)
        self.assertAlmostEqual(s['spend'], 1213.12, places=2)
        self.assertEqual(s['automated_tickets'], 97488)
        self.assertAlmostEqual(s['spend_per_automated_ticket'], self.raw.spend_usd.sum() / self.raw.automated_tier1_tickets.sum())
        average = sum(self.raw.avg_handle_time_min) / len(self.raw)
        hours = sum(self.raw.automated_tier1_tickets) * (average / .65 - average) / 60
        self.assertAlmostEqual(s['support_hours'], hours)
        self.assertAlmostEqual(s['fte_months'], hours / 160)
        self.assertAlmostEqual(df.tokens_per_request.iloc[0], 26552214 / 18993)
        self.assertAlmostEqual(s['trends']['automation_rate_pct']['change'], 5.4)

    def test_padded_ranges_keep_context_and_bounds(self):
        self.assertEqual(get_padded_range([10, 20]), [9, 21])
        self.assertEqual(get_padded_range([5, 5], min_span=4), [3, 7])
        self.assertEqual(get_padded_range([99.9, 100], min_span=2, bounds=(0, 100)), [98, 100])
        self.assertEqual(get_padded_range([0, .1], min_span=2, bounds=(0, 100)), [0, 2])
        low, high = get_padded_range([0, 100], min_span=200, bounds=(0, 100))
        self.assertEqual([low, high], [0, 100])
        self.assertTrue(all(math.isfinite(v) for v in get_padded_range([0, 0])))
        for values in ([], [float('nan')], [float('inf')]):
            with self.assertRaises(ValueError):
                get_padded_range(values)

    def test_shared_axis_incidents_and_stability_context(self):
        df = calculate_derived_metrics(load_data())
        combined = daily_chart(df, {'tier1_tickets': 'Demand', 'automated_tier1_tickets': 'Automated'}, 'tickets')
        low, high = combined.layout.yaxis.range
        self.assertGreater(low, 0)
        for field in ['tier1_tickets', 'automated_tier1_tickets']:
            self.assertLess(low, df[field].min())
            self.assertGreater(high, df[field].max())
        quality = daily_chart(df, {'grounded_answer_rate_pct': 'Grounding', 'quality_eval_pass_rate_pct': 'Eval'}, '%')
        self.assertGreater(quality.layout.yaxis.range[0], 85)
        self.assertLessEqual(quality.layout.yaxis.range[1], 100)
        stable = daily_chart(df, {'tokens_per_request': 'Tokens/request'}, 'tokens/request')
        low, high = stable.layout.yaxis.range
        self.assertGreaterEqual(high - low, df.tokens_per_request.mean() * .2 - 1e-9)
        self.assertLess((df.tokens_per_request.max() - df.tokens_per_request.min()) / (high - low), .30)
        tail = daily_chart(df, {'p95_latency_ms': 'P95'}, 'ms',
                           events=[('Catalog sync', 'Catalog sync'), ('Traffic burst', 'Promotion traffic burst')])
        self.assertEqual([a.x.day for a in tail.layout.annotations], [9, 21])
        self.assertEqual([a.y for a in tail.layout.annotations], [2168, 1794])
        typical = daily_chart(df, {'p50_latency_ms': 'P50'}, 'ms')
        self.assertEqual(len(typical.layout.annotations), 0)

    def test_ticket_volume_stack_reconciles_to_total(self):
        df = calculate_derived_metrics(load_data())
        fig = ticket_volume_chart(df)
        self.assertEqual(fig.layout.barmode, 'stack')
        self.assertEqual(fig.layout.yaxis.range[0], 0)
        automated, remaining = fig.data
        for index, row in df.iterrows():
            self.assertEqual(automated.y[index], row.automated_tier1_tickets)
            self.assertEqual(automated.y[index] + remaining.y[index], row.tier1_tickets)
            self.assertEqual(automated.text[index], f'{row.automation_rate_pct:.1f}%')
        self.assertEqual(len(automated.x), 31)
        self.assertEqual(len(remaining.x), 31)

    def test_expansion_profiles_follow_the_canonical_document(self):
        label, profiles = load_expansion_assumptions()
        self.assertEqual(set(profiles), {'Northstar Everyday', 'Northstar Active', 'Northstar Gear', 'Northstar Atelier'})
        self.assertEqual(label, 'Synthetic / illustrative brand assumptions defined for the case.')
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'expansion_assumptions.md'
            text = ASSUMPTIONS_PATH.read_text(encoding='utf-8')
            source.write_text(text.replace('Highest in the synthetic portfolio.', 'Revised relative volume for validation.'), encoding='utf-8')
            _, revised = load_expansion_assumptions(source)
            self.assertEqual(revised['Northstar Everyday']['Relative support volume'], 'Revised relative volume for validation.')
            source.write_text(text.replace('| Team maturity | High — illustrative scenario assumption. |', ''), encoding='utf-8')
            with self.assertRaises(ValueError):
                load_expansion_assumptions(source)
        with self.assertRaises(OSError):
            load_expansion_assumptions(Path('nonexistent-assumptions-document.md'))

    def test_app_renders_every_chart(self):
        app = AppTest.from_file(str(ROOT / 'app.py')).run(timeout=30)
        self.assertEqual(len(app.exception), 0, str(app.exception))
        self.assertEqual(len(app.get('plotly_chart')), 15)
        self.assertTrue(any('Daily Automated Tier-1 Tickets' in item.value for item in app.markdown))
        kpis = next(item.value for item in app.markdown if '<div class="kpi-grid">' in item.value)
        self.assertEqual(kpis.count('<div class="kpi-card">'), 6)
        for element in app.get('plotly_chart'):
            spec = json.loads(element.proto.spec)
            if spec['data'][0]['type'] == 'bar':
                self.assertEqual(spec['layout']['barmode'], 'stack')
                self.assertEqual(spec['layout']['yaxis']['range'][0], 0)
            else:
                self.assertGreater(spec['layout']['yaxis']['range'][0], 0)
            self.assertNotEqual(spec['layout']['yaxis'].get('rangemode'), 'tozero')
            for trace in spec['data']:
                self.assertEqual(len(trace['x']), 31)
        self.assertTrue(any('Catalog sync caused' in item.value and 'event-table' in item.value for item in app.markdown))
        self.assertIn('35% reduction', [v.value for v in app.markdown].__str__())
        rendered = '\n'.join(item.value for item in [*app.markdown, *app.caption])
        risk = rendered.index('Rising inference work per ticket')
        self.assertLess(risk, rendered.index('### Peak-load resilience'))
        self.assertLess(rendered.index('### Peak-load resilience'), rendered.index('### Knowledge operations'))
        self.assertIn('1,398 → 1,397', rendered)
        self.assertIn('4.35 → 6.55', rendered)
        self.assertIn('6,075 → 9,148', rendered)
        self.assertIn('Expansion Opportunity & Proposed Next Steps', rendered)
        self.assertIn('Synthetic / illustrative brand assumptions defined for the case.', rendered)
        self.assertIn('docs/expansion_assumptions.md', rendered)
        self.assertIn('Illustrative pilot workload assumptions, not observed Northstar ticket categories', rendered)
        self.assertNotIn('ticket complexity increased', rendered.lower())


if __name__ == '__main__':
    unittest.main()
