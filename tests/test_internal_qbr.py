"""Validate the score contract, canonical assumptions and audience separation."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from src.data import load_data
from src.metrics import calculate_derived_metrics, calculate_summary_metrics
from src.expansion import load_expansion_assumptions
from src.internal_assumptions import load_internal_assumptions, INTERNAL_ASSUMPTIONS_PATH
from src.health import calculate_account_health

ROOT = Path(__file__).resolve().parents[1]


def rendered(app):
    return '\n'.join(str(item.value) for item in [*app.markdown,*app.caption,*app.metric,*app.warning,*app.error])


class InternalQBRTests(unittest.TestCase):
    def setUp(self):
        self.df = calculate_derived_metrics(load_data())
        self.summary = calculate_summary_metrics(self.df)
        self.scenario = load_internal_assumptions()

    def test_independent_weighted_arithmetic(self):
        h = calculate_account_health(self.df,self.summary,self.scenario)
        expected = [95*.30+95*.25+95*.25+90*.20,
                    90*.30+90*.20+90*.30+84*.20,
                    75*.35+60*.35+75*.30,
                    90*.30+65*.20+60*.20+85*.15+65*.15,
                    85*.25+85*.20+60*.20+80*.15+75*.10+80*.10]
        self.assertEqual(len(h['pillars']),5)
        for p,score in zip(h['pillars'],expected):
            self.assertAlmostEqual(p['score'],score)
        total = sum(v*w for v,w in zip(expected,[.25,.25,.15,.15,.20]))
        self.assertAlmostEqual(h['raw_score'],total)
        self.assertAlmostEqual(total,82.8875)
        self.assertEqual(h['status'],'HEALTHY')
        self.assertEqual([p['confidence'] for p in h['pillars']],['HIGH','HIGH','MEDIUM','LOW','MEDIUM'])
        self.assertFalse(h['cap_applied'])

    def test_score_reacts_to_evidence_and_scenario(self):
        base = calculate_account_health(self.df,self.summary,self.scenario)
        altered = deepcopy(self.summary)
        altered['trends']['p95_latency_ms']['change'] = 10
        degraded = calculate_account_health(self.df,altered,self.scenario)
        self.assertAlmostEqual(base['score']-degraded['score'],30*.20*.25)
        other = deepcopy(self.scenario)
        other['relationship']['budget']['score'] = 0
        changed = calculate_account_health(self.df,self.summary,other)
        self.assertAlmostEqual(base['score']-changed['score'],60*.20*.15)
        self.assertEqual(base['confidence'],changed['confidence'])

    def test_critical_override_preserves_raw_and_never_improves_low_score(self):
        scenario = deepcopy(self.scenario)
        scenario['critical_flags'] = ['Illustrative active sponsor-loss test']
        h = calculate_account_health(self.df,self.summary,scenario)
        self.assertEqual(h['score'],79)
        self.assertGreater(h['raw_score'],79)
        self.assertEqual(h['status'],'WATCH')
        self.assertTrue(h['cap_applied'])
        for row in scenario['relationship'].values():
            row['score']=0
        for row in scenario['expansion_ratings'].values():
            row['score']=0
        low = calculate_account_health(self.df,self.summary,scenario)
        self.assertEqual(low['score'],low['raw_score'])
        self.assertLess(low['score'],79)

    def test_assumption_source_dates_and_pipeline(self):
        _,profiles=load_expansion_assumptions()
        self.assertEqual({row['brand'] for row in self.scenario['pipeline']},set(profiles))
        self.assertEqual(len(self.scenario['actions']),6)
        self.assertTrue(all(row['Owner'] and row['Target'] and row['Status'] for row in self.scenario['actions']))
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'assumptions.md'
            original=INTERNAL_ASSUMPTIONS_PATH.read_text()
            p.write_text(original.replace('"status": "Strong"','"status": "Needs confirmation"'))
            self.assertEqual(load_internal_assumptions(p)['relationship']['sponsor']['status'],'Needs confirmation')
            p.write_text(original.replace('"score": 90','"score": 150',1))
            with self.assertRaises(ValueError):
                load_internal_assumptions(p)
        with self.assertRaises(OSError):
            load_internal_assumptions(Path('/nonexistent/internal.md'))

    def test_views_render_and_do_not_retain_internal_content(self):
        app=AppTest.from_file(str(ROOT/'app.py')).run(timeout=30)
        self.assertFalse(app.exception)
        self.assertEqual(app.radio[0].value,'Customer Account Health')
        original_customer=rendered(app)
        self.assertNotIn('qbr-summary',original_customer)
        app.radio[0].set_value('Internal QBR').run(timeout=30)
        self.assertFalse(app.exception,str(app.exception))
        self.assertFalse(app.error,str(app.error))
        text=rendered(app)
        for token in ['82.9','Illustrative internal assumptions for case purposes.',
                      'Primarily assumption-driven','Medium–High','Critical-risk override',
                      'Renewal & Competitive Risk','Moderate / unknown',
                      'Decisions Needed','Nov 02, 2026','Pilot go / no-go review']:
            self.assertIn(token,text)
        self.assertNotIn('Margin visibility',text)
        self.assertNotIn('margin visibility',text)
        self.assertIn('Satisfaction does not establish expansion intent',text)
        self.assertIn('Other brands or functions may evaluate third-party alternatives',text)
        self.assertIn('Check in with the Account Manager and deployment engineer',text)
        for name,profile in load_expansion_assumptions()[1].items():
            self.assertIn(name,text)
            self.assertIn(profile['Primary hypothesis'],text)
        self.assertEqual(len(app.get('plotly_chart')),9)
        for chart in app.get('plotly_chart'):
            spec=json.loads(chart.proto.spec)
            self.assertTrue(all(len(trace['x'])==31 for trace in spec['data']))
        app.radio[0].set_value('Customer Account Health').run(timeout=30)
        self.assertFalse(app.exception)
        self.assertEqual(len(app.get('plotly_chart')),15)
        self.assertEqual(original_customer,rendered(app))
        for forbidden in ['qbr-summary','Manageable','Primarily assumption-driven','Renewal risk:',
                          'Competitive risk:','Fireworks Account Lead','Oct 23','82.9']:
            self.assertNotIn(forbidden,rendered(app))

    def test_customer_does_not_load_internal_scenario(self):
        with patch('src.internal_assumptions.load_internal_assumptions',side_effect=AssertionError('internal read')) as loader:
            app=AppTest.from_file(str(ROOT/'app.py')).run(timeout=30)
            self.assertFalse(app.exception)
            loader.assert_not_called()


if __name__=='__main__':
    unittest.main()
