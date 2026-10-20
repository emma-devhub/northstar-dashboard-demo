"""Read internal scenario inputs only when the Internal QBR is selected."""
from datetime import date
import json
from pathlib import Path
import re

INTERNAL_ASSUMPTIONS_PATH = Path(__file__).resolve().parents[1] / 'docs' / 'internal_qbr_assumptions.md'
LABEL = 'Illustrative internal assumptions for case purposes.'


def load_internal_assumptions(path=INTERNAL_ASSUMPTIONS_PATH):
    document = path.read_text(encoding='utf-8')
    match = re.search(r'```json\s*\n(.*?)\n```', document, re.DOTALL)
    if match is None:
        raise ValueError('Internal assumptions need one structured JSON scenario.')
    scenario = json.loads(match.group(1))
    if scenario['label'] != LABEL or LABEL not in document:
        raise ValueError('Internal assumptions need the canonical illustrative label.')
    date.fromisoformat(scenario['review_date'])
    for group in ['relationship', 'expansion_ratings']:
        for item in scenario[group].values():
            score = item['score']
            if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 100:
                raise ValueError('Scenario scores must be numbers from 0 to 100.')
    if not 0 <= scenario['support']['burden_score'] <= 100:
        raise ValueError('Support burden score must be from 0 to 100.')
    for action in scenario['actions']:
        if not all(action.get(key) for key in ('Action', 'Owner', 'Target', 'Status')):
            raise ValueError('Every proposed action needs an owner, target and status.')
        date.fromisoformat(action['Target'])
    if not isinstance(scenario['critical_flags'], list) or not all(
            isinstance(flag, str) and flag.strip() for flag in scenario['critical_flags']):
        raise ValueError('Critical flags must be a list of nonempty issue descriptions.')
    return scenario
