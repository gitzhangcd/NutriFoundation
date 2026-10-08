"""Strict engineering envelopes and scientific workpack response validation."""
from __future__ import annotations
import json
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

class Strict(BaseModel):model_config=ConfigDict(extra='forbid')
class Screening(Strict):
    actor_id:str
    professional_role:str=Field(min_length=3,max_length=100)
    nutrition_or_clinical_nutrition_expertise:str=Field(min_length=3,max_length=200)
    years_relevant_practice_or_research:int=Field(ge=0,le=80)
    relevant_decision_experience:str=Field(min_length=3,max_length=500)
    source_appraisal_experience:str=Field(min_length=3,max_length=500)
    declared_conflicts:list[str]
    prior_exposure_to_exact_case:bool
    prior_exposure_to_other_arm_output_for_case:bool
    prior_access_to_hidden_diet_values:bool
    prior_access_to_SRS_claim_labels:bool
    prior_access_to_final_reference:bool
    prior_access_to_other_expert_judgment:bool
    # No field to assert real credentials verified. Synthetic only.

class SaveDraft(Strict):
    expected_revision:int=Field(ge=0)
    payload:dict[str,Any]
    packet_digest:str

class Freeze(Strict):
    expected_revision:int=Field(ge=1)
    idempotency_key:str=Field(min_length=8,max_length=100)
    exposure_assertions:dict[str,bool]

class Candidate(Strict):
    candidate_ref:str=Field(min_length=3,max_length=120)
    text:str=Field(min_length=3,max_length=2000)
    source_spans:list[dict[str,str]]=Field(min_length=1,max_length=20)

class PutCandidates(Strict):
    candidates:list[Candidate]=Field(min_length=1,max_length=50)
    idempotency_key:str=Field(min_length=8,max_length=100)

class VerifyItem(Strict):
    candidate_ref:str
    expert_disposition:Literal['ACCEPT','REJECT','MODIFY','IRRELEVANT','UNCERTAIN','NEEDS_MORE_EVIDENCE']
    rationale:str=Field(max_length=4000)

class SubmitVerification(Strict):
    items:list[VerifyItem]
    idempotency_key:str=Field(min_length=8,max_length=100)

class ReconcileItem(VerifyItem):
    changed_pre_ai_judgment:bool
    change_type:str|None=None
    source_refs:list[str]=Field(default_factory=list)

class SubmitReconciliation(Strict):
    items:list[ReconcileItem]
    post_ai_judgment:dict[str,Any]
    idempotency_key:str=Field(min_length=8,max_length=100)

def canonical_json(value:Any)->str:
    return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False)

def validate_decision(payload:dict[str,Any],schema:dict[str,Any])->None:
    if not isinstance(payload,dict) or set(payload)!=set(schema):raise ValueError('DECISION_SCHEMA_MISMATCH')
    for field,v in schema.items():
        p=payload[field]
        if field=='reference_set':
            if not isinstance(p,dict) or set(p)!=set(v):raise ValueError('REFERENCE_SET_MISMATCH')
            for c,l in p.items():validate_strings(l,field+'.'+c)
        elif field=='decision_focus':
            if p is not None and (not isinstance(p,str) or len(p)>10000):raise ValueError('INVALID_FOCUS')
        elif field=='active_expert_minutes':
            if p is not None and (type(p) not in (int,float) or not 0<=p<=100000):raise ValueError('INVALID_MINUTES')
        elif field=='clarification_count':
            if type(p) is not int or not 0<=p<=100000:raise ValueError('INVALID_CLARIFICATIONS')
        else:validate_strings(p,field)

def validate_strings(p:Any,name:str)->None:
    if not isinstance(p,list) or len(p)>200 or any(not isinstance(x,str) or len(x)>2000 for x in p):
        raise ValueError('INVALID_LIST:'+name)