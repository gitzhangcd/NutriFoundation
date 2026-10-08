"""Build *bounded* source read-model candidates from frozen NDS-R1 documents.

Importing metadata/curated support is not independent full-text verification and
is not authorization to expose any other article/PDF to a human arm.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit
from authority import ScientificAdapter, CASE_REF

AUTHORIZED_SOURCE_KEYS=("source_title","canonical_url","canonical_doi","pmid", "retrieved_on","source_review_date", "locator","bounded_source_support","version_status")
FORBIDDEN_RECURSIVE_KEYS={"removed_system_synthesis","hidden_case_information","scientific_knowledge_binding", "workflow_outcome_scores", "system_view", "agent_expansion_view", "meta_adjudication_view", "evaluator_view", "qualifieddecisionreference", "source_identity_mapping", "source_pdf"}
class PacketError(ValueError):pass

def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')

def digest(value):return hashlib.sha256(canonical(value)).hexdigest()

def ensure_no_forbidden_keys(obj):
    if isinstance(obj,dict):
        for k,v in obj.items():
            if k.casefold() in FORBIDDEN_RECURSIVE_KEYS:raise PacketError('FORBIDDEN_SOURCE_FIELD:'+k)
            ensure_no_forbidden_keys(v)
    elif isinstance(obj,list):
        for v in obj:ensure_no_forbidden_keys(v)

def materialize_baseline(adapter:ScientificAdapter, *, workflow:str)->dict:
    if workflow not in {'R0','R2_PREAI'}:
        raise PacketError('ARM_NOT_AUTHORIZED_FOR_HUMAN_BASELINE')
    source=adapter.source_packet
    if source.get('case_ref')!=CASE_REF or source.get('version')!='v0.2' or source.get('packet_id')!='HBSP-R1P0-001':
        raise PacketError('FROZEN_PACKET_VERSION_OR_CASE_CONFLICT')
    if len(source.get('scientific_sources',[]))!=6:raise PacketError('SOURCE_COUNT_DELTA')
    rows=[]
    for index,record in enumerate(source['scientific_sources'],start=1):
        if not isinstance(record,dict) or not all(k in record for k in AUTHORIZED_SOURCE_KEYS):
            raise PacketError('MISSING_SOURCE_PROVENANCE')
        url=record['canonical_url'];p=urlsplit(url)
        if p.scheme!='https' or not p.netloc or p.username or p.password:
            raise PacketError('NON_HTTPS_SOURCE_IDENTITY')
        if not record['bounded_source_support'] or not all(isinstance(s,str) and len(s.strip())>8 for s in record['bounded_source_support']):
            raise PacketError('INVALID_BOUNDED_SUPPORT')
        # Whitelist, do not copy metadata or hidden labels from a future packet.
        e={k:record[k] for k in AUTHORIZED_SOURCE_KEYS}
        e['source_ref']=f"{source['packet_id']}:S{index:02d}"
        e['representation']='FROZEN_BOUNDED_SOURCE_SUPPORT_NOT_FULLTEXT'
        rows.append(e)
    case=dict(adapter.case_view)
    tasktext=adapter.by('R0_Human_DeNovo_Workpack_v0.2.json')['input_surface']['task_text']
    view={'case_ref':CASE_REF,'task_text':tasktext,'case_visible_observations':case,
        'source_packet_id':source['packet_id'],'source_packet_version':source['version'],
        'authority_blob_sha':'a38d000f9962dac35e00d407f1d984721bc031ef',
        'sources':rows,
        'source_evidence_level':'FROZEN_BOUNDED_EXCERPTS_WITH_LOCATOR_NO_FULLTEXT_SNAPSHOT',
        'fulltext_scientifically_verified':False,
        'not_an_agent_or_gold_projection':True}
    ensure_no_forbidden_keys(view)
    # No arm, expert identity or UI-specific status within this scientific read model.
    view['projection_sha256']=digest(view)
    return view

def view_binding_check(repo_root:Path, *,expected_case_ref:str=CASE_REF):
    """Explicit audit of referenced case view; does not repair an upstream conflict."""
    path=Path(repo_root)/'runs/NDF/D2/Case_0001/Materialized_Projection_Views_v0.2.json'
    data=path.read_bytes()
    sha=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    if sha!='426be595f178408cab11191a3720cf12aea7703b':
        raise PacketError('CASE_PROJECTION_GIT_BLOB_MISMATCH')
    obj=json.loads(data)
    return {'source_path':str(path.relative_to(repo_root)),'source_git_blob_sha':sha,
      'referenced_case_ref':obj['case_ref'],'target_workpack_case_ref':expected_case_ref,
      'same_case_ref':obj['case_ref']==expected_case_ref,
      'decision':'PASS' if obj['case_ref']==expected_case_ref else 'BLOCK_REQUIRES_SCIENTIFIC_OWNER_RECONCILIATION'}

def compare_r0_r2(adapter):
    a=materialize_baseline(adapter,workflow='R0')
    b=materialize_baseline(adapter,workflow='R2_PREAI')
    if canonical(a)!=canonical(b):raise PacketError('R0_R2_BASELINE_INEQUALITY')
    return a
