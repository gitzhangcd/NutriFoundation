import json,sqlite3
import pytest
from conftest import h,screen,bind,saved,freeze_req,candidates

def T(env,task='SYN-R2',who='SYN-EXPERT-C'):
 c,k,_=env
 return c.get('/v1/tasks/'+task+'/read-model',headers=h(k,who))

def test_unauthorized_all_surfaces(env):
 c,k,_=env
 for endpoint in ['/v1/tasks','/v1/tasks/SYN-R2/read-model','/v1/tasks/SYN-R2/draft','/v1/tasks/SYN-R2/candidate-set','/v1/tasks/SYN-R2/audit']:
  assert c.get(endpoint).status_code==401
  assert c.get(endpoint,headers={'X-Workbench-Token':'forged'}).status_code==401
 for endpoint in ['/reader/api/document','/reader/api/source','/api/profile','/v1/source/original.pdf']:
  assert c.get(endpoint).status_code==404

def test_r0_no_agent_and_human_packet(env):
 c,k,_=env;bind(env,'SYN-R0','SYN-EXPERT-A')
 x=T(env,'SYN-R0','SYN-EXPERT-A').json()
 assert x['source']['scientific_sources'][0]['source_title']=='SYNTHETIC'
 assert not any('candidate' in key for key in x)
 assert c.get('/v1/tasks/SYN-R0/candidate-set',headers=h(k,'SYN-EXPERT-A')).status_code==403
 assert c.post('/v1/tasks/SYN-R0/candidate-set',headers=h(k,'SYN-PRODUCER-1'),json=candidates()).status_code==403
 saved(env,'SYN-R0','SYN-EXPERT-A')
 assert c.post('/v1/tasks/SYN-R0/freeze',headers=h(k,'SYN-EXPERT-A'),json=freeze_req()).status_code==200
 assert c.get('/v1/tasks/SYN-R0/candidate-set',headers=h(k,'SYN-EXPERT-A')).status_code==403
 assert c.put('/v1/tasks/SYN-R0/draft',headers=h(k,'SYN-EXPERT-A'),json={'expected_revision':1,'payload':{},'packet_digest':'wrong'}).status_code==409

def test_r2_no_agent_preai_and_exposure_before_delivery(env):
 c,k,_=env;bind(env,'SYN-R2','SYN-EXPERT-C')
 pre=T(env).json()
 assert pre['phase']=='PRE_AI' and 'candidate_set' not in pre
 assert c.get('/v1/tasks/SYN-R2/candidate-set',headers=h(k,'SYN-EXPERT-C')).status_code==403
 assert c.post('/v1/tasks/SYN-R2/candidate-set',headers=h(k,'SYN-PRODUCER-1'),json=candidates()).status_code==403
 saved(env,'SYN-R2','SYN-EXPERT-C')
 req=freeze_req();req['exposure_assertions']['agent_output_seen']=True
 assert c.post('/v1/tasks/SYN-R2/freeze',headers=h(k,'SYN-EXPERT-C'),json=req).status_code==422
 req=freeze_req()
 result=c.post('/v1/tasks/SYN-R2/freeze',headers=h(k,'SYN-EXPERT-C'),json=req)
 assert result.status_code==200
 assert result.json()['status']=='FROZEN_SYNTHETIC_ONLY'
 assert result.json()['scientific_capture'] is False
 assert c.post('/v1/tasks/SYN-R2/freeze',headers=h(k,'SYN-EXPERT-C'),json=req).json()==result.json()
 assert c.post('/v1/tasks/SYN-R2/freeze',headers=h(k,'SYN-EXPERT-C'),json={**req,'idempotency_key':'ANOTHER-FREEZE-KEY'}).status_code==409
 assert c.get('/v1/tasks/SYN-R2/candidate-set',headers=h(k,'SYN-EXPERT-C')).status_code==403
 assert c.post('/v1/tasks/SYN-R2/candidate-set',headers=h(k,'SYN-PRODUCER-1'),json=candidates()).status_code==200
 render=T(env).json();assert render['phase']=='POST_AI'
 assert len(render['candidate_set']['items'])==1
 assert render['J_preAI']['read_only'] is True
 assert c.get('/v1/tasks/SYN-R2/candidate-set',headers=h(k,'SYN-EXPERT-C')).status_code==200
 audit=c.get('/v1/tasks/SYN-R2/audit',headers=h(k,'SYN-AUDITOR')).json()['events']
 idx=[e['event'] for e in audit]
 assert idx.index('FREEZE_J_preAI') < idx.index('FREEZE_AGENT_CANDIDATES_SYNTHETIC') < idx.index('CANDIDATE_EXPOSURE')
 assert idx.count('CANDIDATE_EXPOSURE')==1
 assert c.get('/v1/tasks/SYN-R2/audit',headers=h(k,'SYN-EXPERT-C')).status_code==403
 assert c.get('/v1/tasks/SYN-R2/draft',headers=h(k,'SYN-EXPERT-C')).status_code==403

def test_r1_agentfirst_no_preai_phase(env):
 c,k,_=env;bind(env,'SYN-R1','SYN-EXPERT-B')
 assert T(env,'SYN-R1','SYN-EXPERT-B').json()['phase']=='WAIT_AGENT_FREEZE'
 assert c.get('/v1/tasks/SYN-R1/draft',headers=h(k,'SYN-EXPERT-B')).status_code==403
 assert c.post('/v1/tasks/SYN-R1/freeze',headers=h(k,'SYN-EXPERT-B'),json=freeze_req()).status_code==403
 assert c.get('/v1/tasks/SYN-R1/candidate-set',headers=h(k,'SYN-EXPERT-B')).status_code==403
 assert c.post('/v1/tasks/SYN-R1/candidate-set',headers=h(k,'SYN-PRODUCER-1'),json=candidates()).status_code==200
 v=T(env,'SYN-R1','SYN-EXPERT-B').json();assert v['phase']=='EXPERT_VERIFY'
 assert v['candidate_set']['items'][0]['source_spans']
 item={'candidate_ref':'SYN-CAND-1','expert_disposition':'UNCERTAIN','rationale':'Synthetic verification'}
 r=c.post('/v1/tasks/SYN-R1/verify',headers=h(k,'SYN-EXPERT-B'),json={'items':[item],'idempotency_key':'SYN-R1-VERIFY-000001'})
 assert r.status_code==200;r2=T(env,'SYN-R1','SYN-EXPERT-B').json()
 assert r2['phase']=='VERIFY_LOCKED' and 'candidate_set' not in r2
 assert c.post('/v1/tasks/SYN-R1/verify',headers=h(k,'SYN-EXPERT-B'),json={'items':[item],'idempotency_key':'NEW-R1-VERIFY-00002'}).status_code==409

def test_r2_reconcile_new_immutable_object(env):
 c,k,_=env;bind(env,'SYN-R2','SYN-EXPERT-C');saved(env,'SYN-R2','SYN-EXPERT-C')
 c.post('/v1/tasks/SYN-R2/freeze',headers=h(k,'SYN-EXPERT-C'),json=freeze_req())
 c.post('/v1/tasks/SYN-R2/candidate-set',headers=h(k,'SYN-PRODUCER-1'),json=candidates())
 origin=T(env).json()['J_preAI']['content_sha']
 item={'candidate_ref':'SYN-CAND-1','expert_disposition':'REJECT','rationale':'No valid evidence',
       'changed_pre_ai_judgment':False,'change_type':None,'source_refs':['SYN-SOURCE-1']}
 profile=env[2].state.adapter.response_schema
 post=json.loads(json.dumps(profile));post['decision_focus']='Synthetic post-AI evaluation'
 r=c.post('/v1/tasks/SYN-R2/reconcile',headers=h(k,'SYN-EXPERT-C'),json={'items':[item],'post_ai_judgment':post,'idempotency_key':'R2-POST-FREEZE-00001'})
 assert r.status_code==200
 assert T(env).json()['phase']=='POST_AI_LOCKED'
 with env[2].state.controller.conn() as db:
  old=db.execute("SELECT content_sha FROM snapshots WHERE task='SYN-R2' AND kind='J_preAI'").fetchone()
  later=db.execute("SELECT content_sha FROM snapshots WHERE task='SYN-R2' AND kind='J_postAI'").fetchone()
 assert old['content_sha']==origin and later['content_sha']!=origin

def test_identity_cross_arm_and_roles(env):
 c,k,_=env;bind(env,'SYN-R0','SYN-EXPERT-A')
 z=c.post('/v1/tasks/SYN-R2/qualification',headers=h(k,'SYN-ADMIN'),json=screen('SYN-EXPERT-A'))
 assert z.status_code==409
 assert c.get('/v1/tasks/SYN-R0/read-model',headers=h(k,'SYN-EXPERT-C')).status_code==404
 assert c.get('/v1/tasks/SYN-R0/read-model',headers=h(k,'SYN-ADMIN')).status_code==404
 assert c.get('/v1/tasks',headers=h(k,'SYN-EXPERT-C')).json()['tasks']==[]

def test_prior_exposure_and_conflicts_fail_closed(env):
 c,k,_=env
 for mark in ['prior_exposure_to_other_arm_output_for_case','prior_access_to_hidden_diet_values','prior_access_to_SRS_claim_labels','prior_access_to_final_reference','prior_access_to_other_expert_judgment','prior_exposure_to_exact_case']:
  assert c.post('/v1/tasks/SYN-R0/qualification',headers=h(k,'SYN-ADMIN'),json=screen('SYN-EXPERT-A',**{mark:True})).status_code==422
 assert c.post('/v1/tasks/SYN-R0/qualification',headers=h(k,'SYN-ADMIN'),json=screen('SYN-EXPERT-A',declared_conflicts=['conflict'])).status_code==422
 assert c.post('/v1/tasks/SYN-R0/qualification',headers=h(k,'SYN-EXPERT-A'),json=screen('SYN-EXPERT-A')).status_code==403

def test_revision_and_source_digest(env):
 c,k,_=env;bind(env,'SYN-R2','SYN-EXPERT-C')
 p=c.get('/v1/tasks/SYN-R2/draft',headers=h(k,'SYN-EXPERT-C')).json()
 bad=c.put('/v1/tasks/SYN-R2/draft',headers=h(k,'SYN-EXPERT-C'),json={'expected_revision':0,'payload':p['payload'],'packet_digest':'tampered'})
 assert bad.status_code==409
 saved(env,'SYN-R2','SYN-EXPERT-C')
 bad=c.put('/v1/tasks/SYN-R2/draft',headers=h(k,'SYN-EXPERT-C'),json={'expected_revision':0,'payload':p['payload'],'packet_digest':p['packet_digest']})
 assert bad.status_code==409

def test_candidate_store_not_public(env):
 c,k,_=env;bind(env,'SYN-R1','SYN-EXPERT-B')
 assert c.get('/v1/tasks/SYN-R1/candidate-set',headers=h(k,'SYN-EXPERT-B')).status_code==403
 assert c.post('/v1/tasks/SYN-R1/candidate-set',headers=h(k,'SYN-EXPERT-C'),json=candidates()).status_code==403
 bad=candidates();bad['candidates'][0]['source_spans']=[]
 assert c.post('/v1/tasks/SYN-R1/candidate-set',headers=h(k,'SYN-PRODUCER-1'),json=bad).status_code==422
 assert c.post('/v1/tasks/SYN-R1/candidate-set',headers=h(k,'SYN-PRODUCER-1'),json=candidates()).status_code==200
 b=candidates();b['idempotency_key']='different-000000001'
 assert c.post('/v1/tasks/SYN-R1/candidate-set',headers=h(k,'SYN-PRODUCER-1'),json=b).status_code==409

def test_snapshot_tamper_prevents_unlock(env):
 c,k,app=env;bind(env,'SYN-R2','SYN-EXPERT-C');saved(env,'SYN-R2','SYN-EXPERT-C')
 c.post('/v1/tasks/SYN-R2/freeze',headers=h(k,'SYN-EXPERT-C'),json=freeze_req())
 with pytest.raises(sqlite3.IntegrityError,match='IMMUTABLE_SNAPSHOTS'):
  with app.state.controller.conn() as db:
   db.execute("UPDATE snapshots SET payload='{}' WHERE task='SYN-R2' AND kind='J_preAI'")
 assert c.post('/v1/tasks/SYN-R2/candidate-set',headers=h(k,'SYN-PRODUCER-1'),json=candidates()).status_code==200
 assert c.get('/v1/tasks/SYN-R2/read-model',headers=h(k,'SYN-EXPERT-C')).status_code==200

def test_audit_hash_chain(env):
 c,k,_=env;bind(env,'SYN-R0','SYN-EXPERT-A');saved(env,'SYN-R0','SYN-EXPERT-A')
 rows=c.get('/v1/tasks/SYN-R0/audit',headers=h(k,'SYN-AUDITOR')).json()['events']
 assert rows[0]['previous_hash']=='GENESIS'
 assert rows[1]['previous_hash']==rows[0]['event_hash']
 assert 'Synthetic judgment' not in json.dumps(rows)

def test_api_is_not_production(env):
 c,k,_=env
 assert c.get('/health').json()['scientific_capture']=='DISABLED'
 assert c.get('/v1/tasks',headers=h(k,'SYN-ADMIN')).json()['tasks']==[]
 assert c.get('/openapi.json').status_code==404
 assert c.get('/docs').status_code==404

def test_freeze_after_restart_persistent(env):
 from app import make_app
 from conftest import fake_authority,ACTORS
 from pathlib import Path
 c,k,a=env;bind(env,'SYN-R2','SYN-EXPERT-C');saved(env,'SYN-R2','SYN-EXPERT-C')
 receipt=c.post('/v1/tasks/SYN-R2/freeze',headers=h(k,'SYN-EXPERT-C'),json=freeze_req()).json()
 nxt=make_app(a.state.controller.path.parent,test_authority=fake_authority(),actors=ACTORS)
 # Auth tokens are intentionally rotated; no saved sessions.
 fresh={name:token for token,(name,_) in nxt.state.tokens.items()}
 r=TestClient(nxt).get('/v1/tasks/SYN-R2/read-model',headers=h(fresh,'SYN-EXPERT-C'))
 assert r.status_code==200 and r.json()['phase']=='WAIT_AGENT_FREEZE'
 assert r.json()['J_preAI']['content_sha']==receipt['content_sha']

from fastapi.testclient import TestClient

def test_candidate_idempotency_cannot_replace_payload(env):
 c,k,_=env;bind(env,'SYN-R1','SYN-EXPERT-B')
 req=candidates();ok=c.post('/v1/tasks/SYN-R1/candidate-set',headers=h(k,'SYN-PRODUCER-1'),json=req)
 assert ok.status_code==200
 changed=candidates();changed['candidates'][0]['text']='A different candidate, same idempotency key'
 assert c.post('/v1/tasks/SYN-R1/candidate-set',headers=h(k,'SYN-PRODUCER-1'),json=changed).status_code==409
 assert c.post('/v1/tasks/SYN-R1/candidate-set',headers=h(k,'SYN-PRODUCER-1'),json=req).json()==ok.json()

def test_completed_idempotency_is_payload_bound(env):
 c,k,_=env;bind(env,'SYN-R1','SYN-EXPERT-B')
 c.post('/v1/tasks/SYN-R1/candidate-set',headers=h(k,'SYN-PRODUCER-1'),json=candidates())
 T(env,'SYN-R1','SYN-EXPERT-B')
 data={'items':[{'candidate_ref':'SYN-CAND-1','expert_disposition':'ACCEPT','rationale':'Synthetic'}],
      'idempotency_key':'VERIFY-TEST-UNIQUE-KEY'}
 r=c.post('/v1/tasks/SYN-R1/verify',headers=h(k,'SYN-EXPERT-B'),json=data)
 assert r.status_code==200
 assert c.post('/v1/tasks/SYN-R1/verify',headers=h(k,'SYN-EXPERT-B'),json=data).status_code==200
 data['items'][0]['expert_disposition']='REJECT'
 assert c.post('/v1/tasks/SYN-R1/verify',headers=h(k,'SYN-EXPERT-B'),json=data).status_code==409

def test_audit_tamper_rejected(env):
 c,k,app=env;bind(env,'SYN-R0','SYN-EXPERT-A')
 with pytest.raises(sqlite3.IntegrityError,match='IMMUTABLE_AUDIT'):
  with app.state.controller.conn() as db:db.execute("UPDATE audit SET details='{}' WHERE task='SYN-R0'")
 assert c.get('/v1/tasks/SYN-R0/audit',headers=h(k,'SYN-AUDITOR')).status_code==200