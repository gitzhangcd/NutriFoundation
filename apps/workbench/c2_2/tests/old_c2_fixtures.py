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

EMPTY={
 'decision_focus':None,'salient_existing_facts':[],'decision_changing_missing_information':[],
 'currently_acceptable_actions':[],'conditional_actions':[],'not_indicated_prohibited_or_unsafe':[],
 'process_action':[],'monitoring_needs':[],
 'reference_set':{x:[] for x in ['preferred','acceptable','conditional','not_currently_indicated','prohibited','unsafe','unresolved']},
 'uncertainty_notes':[],'rationale_notes':[],'active_expert_minutes':None,'clarification_count':0
}
INPUT={'visible_case':{'age_at_screening':43},'task_text':'Synthetic case task','human_baseline_source_packet_ref':'runs/NDS/R1/P0.1/Human_Baseline_Source_Packet_v0.2.json'}

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
  place('Human_Baseline_Source_Packet_v0.2.json',{'case_ref':CASE_REF,'version':'v0.2','packet_id':'HBSP-R1P0-001','scientific_sources':[{**{key:None for key in ['canonical_doi','pmid','source_review_date']},'source_title':f'SYN SOURCE {i}','canonical_url':f'https://example.org/source{i}','retrieved_on':'2026-10-07','locator':'section','bounded_source_support':['Only a synthetic engineering excerpt not a real statement.'],'version_status':'SYNTHETIC'} for i in range(6)]})
  place('R0_Human_DeNovo_Workpack_v0.2.json',{'case_ref':CASE_REF,'response':EMPTY,'input_surface':INPUT,'supersedes':'runs/NDS/R1/P0.1/R0_Human_DeNovo_Workpack_v0.1.json'})
  place('R2_PreAI_Workpack_v0.2.json',{'case_ref':CASE_REF,'J_preAI':EMPTY,'input_surface':INPUT,'supersedes':'runs/NDS/R1/P0.1/R2_PreAI_Workpack_v0.1.json'})
  place('R1_AgentFirst_Verification_HoldPack_v0.1.json',{'case_ref':CASE_REF,'status':'HOLD_AGENT_CANDIDATE_SET_NOT_YET_GENERATED'})
  return docs
