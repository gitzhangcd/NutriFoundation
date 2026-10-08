"""Replay an existing D0.2.1 pack through new production services.

This imports prior NONBLIND staging, not new independent extraction or Gold.
Usage: python scripts/run_d0_b002_pilot.py --source-pack PATH --authority FILE --out DIR
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

from nutrifoundation.production.acquisition import SnapshotService
from nutrifoundation.production.models import FieldAssertion,PrefillDraft,ResultDraft,digest,now
from nutrifoundation.production.parsing import parse_document,replay_anchor
from nutrifoundation.production.prefill import PrefillService
from nutrifoundation.production.review import ReviewService
from nutrifoundation.production.release import ReleaseService
from nutrifoundation.production.store import ProductionStore


def run(source_pack: Path, authority: Path, out: Path) -> dict:
    out.mkdir(parents=True,exist_ok=True)
    store=ProductionStore(out/'pilot.db')
    xml=(source_pack/'raw/PMC9854100.1.xml').read_bytes()
    sha=hashlib.sha256(xml).hexdigest()
    prior=json.loads((source_pack/'Evidence_Anchors_v1.0.json').read_text())['anchors']
    root=ET.fromstring(xml)
    node_paths={}
    def index_paths(node,path):
        node_paths[id(node)]=path
        for i,child in enumerate(node):
            index_paths(child,path+f'/{i}')
    index_paths(root,'root')
    old={a['anchor_id']:a for a in prior}
    for a in prior:
        if a['source_path'].endswith('.xml'):
            original_data=(source_pack/a['source_path']).read_bytes()
            assert a['source_sha256']==hashlib.sha256(original_data).hexdigest()
            anchor_root=ET.fromstring(original_data)
            xpath=a['xpath']
            prefix='/'+anchor_root.tag+'/'
            if xpath.startswith(prefix):
                xpath='./'+xpath[len(prefix):]
            else:
                xpath='.'+xpath
            found=anchor_root.findall(xpath)
            assert len(found)==1,(a['anchor_id'],'XPath not unique')
            assert ''.join(found[0].itertext())==a['exact_text'],a['anchor_id']
    snap=SnapshotService(store,out/'blobs').ingest(xml,source_id='PMID36670395',source_version='PMC9854100.1',
        format='JATS_XML',content_scope='fulltext',license='CC-BY-4.0 as bound in D0.2.1',origin='D0.2.1 offline raw import',expected_sha256=sha)
    parsed=parse_document(snap,xml)
    store.put('parsed',parsed.parsed_id,parsed);store.depend(parsed.parsed_id,(snap.snapshot_id,))
    for a in parsed.anchors:
        replay_anchor(snap,xml,a)
    task=PrefillService(store).prepare(snap,parsed,authority_sha256=hashlib.sha256(authority.read_bytes()).hexdigest(),
        extractor_id='prior-nonblind-staging-import',model_version='NOT_RUN',prompt_version='NOT_APPLICABLE',
        coverage_request='Table3 30 result cells; preserve prior conflicts and missing scope')
    def assertion(old_id,value=None):
        text=old[old_id]['exact_text']
        xpath=old[old_id]['xpath']
        xpath='./'+xpath[len('/article/'):] if xpath.startswith('/article/') else '.'+xpath
        source_node=root.find(xpath)
        assert source_node is not None,old_id
        # Bind node identity/position, not just text: identical numbers and
        # outcome labels legitimately occur in different rows and tables.
        matches=[a for a in parsed.anchors if a.locator==node_paths[id(source_node)]]
        if not matches and source_node.tag in {'td','th'}:
            for table in root.findall('.//table-wrap'):
                for ri,row in enumerate(table.findall('.//tr')):
                    cells=[c for c in row if c.tag in {'td','th'}]
                    for ci,cell in enumerate(cells):
                        if cell is source_node:
                            matches=[a for a in parsed.anchors if a.context.get('table_id')==table.get('id')
                                and a.context.get('row')==ri and a.context.get('cell')==ci]
        assert len(matches)==1,old_id
        assert matches[0].exact_text==text,old_id
        val=text if value is None else value
        assert val in text
        return FieldAssertion(state='PRESENT',source_value=val,anchor_refs=(matches[0].anchor_id,))
    def unknown(reason):
        return FieldAssertion(state='UNRESOLVED',reason=reason)
    effects=json.loads((source_pack/'Table3_Source_Extraction_v1.0.json').read_text())['effects']
    results=[]
    for effect in effects:
        refs=effect['anchor_refs']
        fields={'study_id':unknown('TLGS report dependency identity not independently adjudicated'),
            'population':assertion('JATS-Par36'),'analysis_population':assertion('JATS-Par36'),
            'exposure':assertion(refs['group_anchor']),'comparator':unknown('Score contrast/reference not explicitly bound'),
            'outcome':assertion(refs['column_anchor']),'time':assertion('JATS-Par50'),
            'estimand':assertion('JATS-Par49'),'model':assertion(refs['row_anchor']),
            'effect_measure':assertion('JATS-Par49','odds ratios'),
            'effect_value':assertion(refs['cell_anchor']),
            'effect_unit':unknown('Score increment not explicitly bound'),
            'exposure_increment':unknown('Do not infer 1 SD or quintile contrast'),
            'reference_category':unknown('Do not infer remaining Pre-DM'),
            'adjustment':assertion(refs['adjustment_anchor'])}
        if 'base_adjustment_anchor' in refs:
            fields['base_adjustment']=assertion(refs['base_adjustment_anchor'])
        issues=tuple(effect.get('conflict_refs',[]))
        results.append(ResultDraft(result_id=effect['candidate_effect_id'],object_type='EvidenceUnit',fields=fields,issues=issues))
        selected=next(a for a in parsed.anchors if a.anchor_id==fields['effect_value'].anchor_refs[0])
        assert selected.context['table_id']=='Tab3'
        assert selected.context['row']==effect['table_body_row_index']
        assert selected.context['cell']==effect['table_column_index']-1
    # Source discrepancies remain separate source-stated readings, not selected truth.
    conflicts=json.loads((source_pack/'Source_Conflict_Register_v1.0.json').read_text())
    store.put('source_conflicts','B002-S1-001-prior-conflicts',conflicts)
    draft=PrefillDraft(draft_id='B002-S1-001-D0-STAGING-v1',task=task,task_sha256=digest(task),
        results=tuple(results),coverage_completed='30 Table3 source-stated result cells imported and re-anchored',
        coverage_omissions=('No new model extraction or independent readout','Source OR/P discrepancies OPEN; no expert adjudication'))
    report=PrefillService(store).ingest(draft)
    reviews=ReviewService(store)
    for mode,label in [('assisted','UNASSIGNED-assisted'),('source_only','UNASSIGNED-A'),('source_only','UNASSIGNED-B')]:
        rt=reviews.create(draft.draft_id,reviewer_id=label,mode=mode)
        projection=reviews.export(rt['review_task_id'])
        (out/(label+'.json')).write_text(json.dumps(projection,ensure_ascii=False,indent=2)+'\n')
        if mode=='source_only':
            assert not {'prefill','results','checks','anchors','issues'}&projection.keys()
        else:
            from nutrifoundation.production.workbench import assisted_html
            (out/'Assisted_Review.html').write_text(assisted_html(projection),encoding='utf-8')
    gates=ReleaseService(store).promotion_gates(draft.draft_id,report.report_id,use='canonical')
    failures=[c for c in report.checks if c.status=='FAIL']
    assert not failures,[(c.field,c.rule,c.reason) for c in failures]
    assert not gates['allowed']
    report_data={'candidate_id':'B002-S1-001','execution_mode':'IMPORT_PRIOR_NONBLIND_STAGING_WITH_RAW_AND_ANCHOR_REPLAY',
        'raw_sha256':sha,'authority_sha256':task.authority_sha256,
        'prior_anchor_count':len(prior),'prior_xml_anchors_replayed':sum(a['source_path'].endswith('.xml') for a in prior),
        'new_parser_anchor_count':len(parsed.anchors),'table_result_count':len(results),
        'mechanical_fail_count':len(failures),'unresolved_check_count':sum(c.status=='UNRESOLVED' for c in report.checks),
        'open_source_conflicts':conflicts['conflicts'],'independent_readouts':0,'expert_decisions':0,
        'model_calls':0,'canonical_promotions':0,'gold_created':0,
        'draft_sha256':digest(draft),'verification_sha256':digest(report),'promotion_gates':gates}
    (out/'Pilot_Report.json').write_text(json.dumps(report_data,ensure_ascii=False,indent=2)+'\n')
    return report_data


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source-pack',type=Path,required=True)
    p.add_argument('--authority',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    report=run(args.source_pack,args.authority,args.out)
    print(json.dumps({k:v for k,v in report.items() if k!='open_source_conflicts'},ensure_ascii=False,indent=2))
