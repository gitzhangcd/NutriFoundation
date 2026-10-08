"""Synthetic mini replica of scientific objects for isolated negative tests.

Deliberately NOT a source of authoritative science; CI also verifies real pinned
GitHub blobs in full repository checkout via test_official_adapter.py.
"""
from __future__ import annotations
import json,sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from authority import PINNED,CASE_REF
from app import make_app
from models import canonical_json

EMPTY={
 'decision_focus':None,'salient_existing_facts':[],'decision_changing_missing_information':[],
 'currently_acceptable_actions':[],'conditional_actions':[],'not_indicated_prohibited_or_unsafe':[],
 'process_action':[],'monitoring_needs':[],
 'reference_set':{x:[] for x in ['preferred','acceptable','conditional','not_currently_indicated','prohibited','unsafe','unresolved']},
 'uncertainty_notes':[],'rationale_notes':[],'active_expert_minutes':None,'clarification_count':0
}
INPUT={'visible_case':{'age_at_screening':43},'human_baseline_source_packet_ref':'runs/NDS/R1/P0.1/Human_Baseline_Source_Packet_v0.2.json'}

def fake_authority():
  def place(suffix,val):
    k=next(x for x in PINNED if x.endswith(suffix));docs[k]=val
  docs={}
  place('Role_Input_Surface_Contract_v0.1.json',{'status':'FROZEN','case_ref':CASE_REF,'arm_surfaces':{'R0':{},'R1':{'expert_initial':['AGENT_CANDIDATE_SET']},'R2':{'expert_post_ai':['FROZEN_J_PREAI']}}})
  place('Exposure_Lock_Registry_v0.1.json',{'status':'FROZEN','case_ref':CASE_REF,'locks':[{'workflow':'R0','state':'PERMANENT_NO_AGENT_EXPOSURE'},{'workflow':'R1','state':'HOLD_UNTIL_REAL_EXPERT_BINDING_AND_AGENT_SET_FREEZE'},{'workflow':'R2','state':'HARD_LOCK_AGENT_UNTIL_J_PREAI_FREEZE'}]})
  place('Judgment_Freeze_Contract_v0.1.json',{'status':'FROZEN','freeze_targets':[{'workflow':'R0','target':'J_human_de_novo','source_workpack':'runs/NDS/R1/P0.1/R0_Human_DeNovo_Workpack_v0.1.json'},{'workflow':'R2','target':'J_preAI','source_workpack':'runs/NDS/R1/P0.1/R2_PreAI_Workpack_v0.1.json'}]})
  place('Expert_Slot_Binding_Registry_v0.1.json',{'case_ref':CASE_REF,'slots':[{'workflow':arm,'expert_slot':slot,'identity_status':'UNBOUND'} for arm,slot in [('R0','EXP-R1P0-A'),('R1','EXP-R1P0-B'),('R2','EXP-R1P0-C')] ]})
  place('Expert_Qualification_Instance_Registry_v0.1.json',{'status':'AWAITING_REAL_EXPERT_INPUT'})
  place('Reconciliation_Exposure_Templates_v0.1.json',{'status':'FROZEN_EMPTY_TEMPLATES'})
  place('Human_Baseline_Source_Packet_v0.2.json',{'case_ref':CASE_REF,'packet_id':'SYN-HBSP-MOCK','scientific_sources':[{'source_title':'SYNTHETIC', 'bounded_source_support':['Only a test fixture']}]})
  place('R0_Human_DeNovo_Workpack_v0.2.json',{'case_ref':CASE_REF,'response':EMPTY,'input_surface':INPUT,'supersedes':'runs/NDS/R1/P0.1/R0_Human_DeNovo_Workpack_v0.1.json'})
  place('R2_PreAI_Workpack_v0.2.json',{'case_ref':CASE_REF,'J_preAI':EMPTY,'input_surface':INPUT,'supersedes':'runs/NDS/R1/P0.1/R2_PreAI_Workpack_v0.1.json'})
  place('R1_AgentFirst_Verification_HoldPack_v0.1.json',{'case_ref':CASE_REF,'status':'HOLD_AGENT_CANDIDATE_SET_NOT_YET_GENERATED'})
  return docs

ACTORS={
  'SYN-ADMIN':'manager',
  'SYN-PRODUCER-1':'producer',
  'SYN-EXPERT-A':'expert',
  'SYN-EXPERT-B':'expert',
  'SYN-EXPERT-C':'expert',
  'SYN-AUDITOR':'auditor',
}

@pytest.fixture
def env(tmp_path):
  app=make_app(tmp_path,test_authority=fake_authority(),actors=ACTORS)
  keys={name:token for token,(name,_) in app.state.tokens.items()}
  c=TestClient(app)
  return c,keys,app

def h(keys,actor):return {'X-Workbench-Token':keys[actor]}

def screen(actor,**kw):
  s=dict(actor_id=actor,professional_role='Clinical nutrition expert TEST ONLY',
  nutrition_or_clinical_nutrition_expertise='Nutrition SCIENTIFIC MOCK',years_relevant_practice_or_research=10,
  relevant_decision_experience='Synthetic decision experience',source_appraisal_experience='Synthetic source appraisal',
  declared_conflicts=[],prior_exposure_to_exact_case=False,
  prior_exposure_to_other_arm_output_for_case=False,prior_access_to_hidden_diet_values=False,
  prior_access_to_SRS_claim_labels=False,prior_access_to_final_reference=False,
  prior_access_to_other_expert_judgment=False)
  s.update(kw);return s

def bind(env,task,actor):
  c,k,_=env;r=c.post('/v1/tasks/'+task+'/qualification',json=screen(actor),headers=h(k,'SYN-ADMIN'))
  assert r.status_code==200,r.text
  return r.json()

def saved(env,task,actor):
  c,k,a=env
  draft=c.get('/v1/tasks/'+task+'/draft',headers=h(k,actor)).json()
  payload=json.loads(json.dumps(draft['payload']))
  payload['decision_focus']='Synthetic judgment only - do not count as empirical'
  r=c.put('/v1/tasks/'+task+'/draft',json={'expected_revision':draft['revision'],'payload':payload,'packet_digest':draft['packet_digest']},headers=h(k,actor))
  assert r.status_code==200,r.text
  return r.json()

def freeze_req():
  return {'expected_revision':1,'idempotency_key':'TEST-IMMUTABLE-KEY-0001',
          'exposure_assertions':{x:False for x in ['agent_output_seen','other_expert_output_seen','final_reference_seen','hidden_diet_values_seen','meta_audit_labels_seen']}}

def candidates():
  return {'idempotency_key':'TEST-AGENT-FREEZE-0001','candidates':[{'candidate_ref':'SYN-CAND-1',
     'text':'Synthetic review candidate only','source_spans':[{'source_ref':'SYN-SOURCE-1','quote':'A test-only evidence span'}]}]}