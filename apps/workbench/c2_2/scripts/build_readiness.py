"""Emit nonsensitive, machine-readable gate decision. Never change scientific files."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gates import assess
p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args();j=assess(a.repo_root)
if j['real_person_ux_pilot'].startswith('NO_GO') and j['formal_NDS_R1_experiment'].startswith('NO_GO'):
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(j,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print('C22_OFFICIAL_SOURCE_PROJECTION='+j['bounded_projection_contract'])
    print('C22_REAL_HUMAN_PILOT='+j['real_person_ux_pilot'])
    print('C22_SCIENTIFIC_CASE_VIEW='+j['case_projection_binding']['decision'])
else:
    raise SystemExit('UNEXPECTED_UNQUALIFIED_REAL_HUMAN_GO')
