"""Read synthetic brand assumptions from their canonical, reviewable document."""
from pathlib import Path
import re

ASSUMPTIONS_PATH = Path(__file__).resolve().parents[1] / 'docs' / 'expansion_assumptions.md'
PROFILE_FIELDS = (
    'Positioning', 'Relative support volume', 'Catalog complexity', 'Tone',
    'Return / policy complexity', 'Team maturity', 'Expansion role', 'Primary hypothesis',
)


def load_expansion_assumptions(path=ASSUMPTIONS_PATH):
    """Load the canonical label and profile tables; never supply local defaults."""
    document = path.read_text(encoding='utf-8')
    label = re.search(r'\*\*Canonical label for all four brands:\*\* “([^”]+)”', document)
    if label is None:
        raise ValueError('The expansion assumptions document needs its canonical label.')
    profiles = {}
    blocks = re.findall(r'^### (Northstar [^\n]+)\n(.*?)(?=^### |^## |\Z)',
                        document, flags=re.MULTILINE | re.DOTALL)
    for name, block in blocks:
        fields = {}
        for line in block.splitlines():
            cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
            if len(cells) == 2 and cells[0] in PROFILE_FIELDS:
                fields[cells[0]] = cells[1]
        if any(not fields.get(field) for field in PROFILE_FIELDS):
            raise ValueError(f'Incomplete expansion assumption profile: {name}.')
        profiles[name] = fields
    if 'Northstar Everyday' not in profiles:
        raise ValueError('Northstar Everyday is missing from the expansion assumptions.')
    return label.group(1), profiles
