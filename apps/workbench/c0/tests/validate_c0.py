import json
from pathlib import Path
r=Path(__file__).resolve().parents[1]
p=json.loads((r/'fixtures/synthetic_tasks.json').read_text())
assert p['experts_are_real'] is False
assert len(p['tasks'])==5
ids={x['id'] for x in p['tasks']}
assert len(ids)==5
for x in p['tasks']:
    if x['arm']=='R0' or (x['arm']=='R2' and x['phase']=='pre_ai_draft'):
        assert x['agent_candidate'] is None
        assert not any('CANDIDATE' in z for z in x['allowed_sources'])
    if x['arm']=='R1' and x['phase']=='agent_set_pending':
        assert x['questions']==[] and x['agent_candidate'] is None
    if x['arm']=='R1' and x['phase']=='agent_set_frozen':
        assert x['agent_candidate'] and 'SYNTH-REFERENCED-SPANS' in x['allowed_sources']
html=(r/'prototype/index.html').read_text()
for s in ['DEMO-R0-001','DEMO-R1-HOLD','DEMO-R1-VERIFY','DEMO-R2-PRE','DEMO-R2-POST','SYNTHETIC','requestForbidden','revealCandidate']:
    assert s in html, s
spec=(r/'docs/WB-P0.2-C0_Page_Contract_v0.1.md').read_text()
assert all(f'P{i:02d}' in spec for i in range(1,12))
print('C0 STATIC PROTOTYPE GATE PASS: 5 synthetic arm/phase tasks, 11 page mappings, no candidate leakage in fixture preAI profiles')