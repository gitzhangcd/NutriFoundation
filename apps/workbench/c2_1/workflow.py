"""Transaction-backed synthetic scientific workflow controller.

HARD BOUNDARY: never use as empirical identity provider, do not expose C1 raw
reader endpoints. All 3 arms are server-projected separately; no CSS-only locks.
"""
from __future__ import annotations
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from fastapi import HTTPException
from authority import ScientificAdapter, CASE_REF
from models import canonical_json, validate_decision

ARMS={'SYN-R0':'R0','SYN-R1':'R1','SYN-R2':'R2'}
ASSERT_KEYS={'agent_output_seen','other_expert_output_seen','final_reference_seen','hidden_diet_values_seen','meta_audit_labels_seen'}
DISPOSITIONS={'ACCEPT','REJECT','MODIFY','IRRELEVANT','UNCERTAIN','NEEDS_MORE_EVIDENCE'}

def sha(s:str)->str:return hashlib.sha256(s.encode('utf-8')).hexdigest()
def utc()->str:return datetime.now(timezone.utc).isoformat()
def deny(code:str='FORBIDDEN',status:int=403):raise HTTPException(status,detail={'code':code})

class Controller:
    def __init__(self,path:Path,authority:ScientificAdapter):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        self.a=authority
        with self.conn() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS bindings(task TEXT PRIMARY KEY, case_ref TEXT NOT NULL,
              arm TEXT NOT NULL,actor TEXT NOT NULL,qualification_sha TEXT NOT NULL,
              bound_at TEXT NOT NULL,UNIQUE(case_ref,actor));
            CREATE TABLE IF NOT EXISTS drafts(task TEXT PRIMARY KEY,revision INTEGER NOT NULL,
              payload TEXT NOT NULL, packet_digest TEXT NOT NULL, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS snapshots(task TEXT NOT NULL,kind TEXT NOT NULL,
              actor TEXT NOT NULL,payload TEXT NOT NULL,content_sha TEXT NOT NULL,
              packet_digest TEXT NOT NULL,created_at TEXT NOT NULL,idem TEXT NOT NULL,
              PRIMARY KEY(task,kind),UNIQUE(task,idem));
            CREATE TABLE IF NOT EXISTS candidates(task TEXT PRIMARY KEY,actor TEXT NOT NULL,
              payload TEXT NOT NULL,candidate_sha TEXT NOT NULL, created_at TEXT NOT NULL,idem TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS exposed(task TEXT PRIMARY KEY,actor TEXT NOT NULL,
              candidate_sha TEXT NOT NULL,first_exposed_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT,
              task TEXT NOT NULL,event TEXT NOT NULL,actor TEXT NOT NULL, details TEXT NOT NULL,
              previous_hash TEXT NOT NULL,event_hash TEXT NOT NULL,created_at TEXT NOT NULL);
            CREATE TRIGGER IF NOT EXISTS protect_snapshots_update BEFORE UPDATE ON snapshots BEGIN SELECT RAISE(ABORT,'IMMUTABLE_SNAPSHOTS'); END;
            CREATE TRIGGER IF NOT EXISTS protect_snapshots_delete BEFORE DELETE ON snapshots BEGIN SELECT RAISE(ABORT,'IMMUTABLE_SNAPSHOTS'); END;
            CREATE TRIGGER IF NOT EXISTS protect_candidates_update BEFORE UPDATE ON candidates BEGIN SELECT RAISE(ABORT,'IMMUTABLE_CANDIDATES'); END;
            CREATE TRIGGER IF NOT EXISTS protect_candidates_delete BEFORE DELETE ON candidates BEGIN SELECT RAISE(ABORT,'IMMUTABLE_CANDIDATES'); END;
            CREATE TRIGGER IF NOT EXISTS protect_exposed_update BEFORE UPDATE ON exposed BEGIN SELECT RAISE(ABORT,'IMMUTABLE_EXPOSED'); END;
            CREATE TRIGGER IF NOT EXISTS protect_exposed_delete BEFORE DELETE ON exposed BEGIN SELECT RAISE(ABORT,'IMMUTABLE_EXPOSED'); END;
            CREATE TRIGGER IF NOT EXISTS protect_bindings_update BEFORE UPDATE ON bindings BEGIN SELECT RAISE(ABORT,'IMMUTABLE_BINDINGS'); END;
            CREATE TRIGGER IF NOT EXISTS protect_bindings_delete BEFORE DELETE ON bindings BEGIN SELECT RAISE(ABORT,'IMMUTABLE_BINDINGS'); END;
            CREATE TRIGGER IF NOT EXISTS protect_audit_update BEFORE UPDATE ON audit BEGIN SELECT RAISE(ABORT,'IMMUTABLE_AUDIT'); END;
            CREATE TRIGGER IF NOT EXISTS protect_audit_delete BEFORE DELETE ON audit BEGIN SELECT RAISE(ABORT,'IMMUTABLE_AUDIT'); END;
            ''')
    def conn(self):
        c=sqlite3.connect(self.path,timeout=10)
        c.row_factory=sqlite3.Row;c.execute('PRAGMA busy_timeout=10000')
        return c
    def _log(self,db,task,event,actor,details:dict):
        before=db.execute('SELECT event_hash FROM audit WHERE task=? ORDER BY id DESC LIMIT 1',(task,)).fetchone()
        prev=before['event_hash'] if before else 'GENESIS'
        when=utc();details_string=canonical_json(details)
        digest=sha(canonical_json({'prev':prev,'event':event,'actor':actor,'details':details_string,'when':when,'task':task}))
        db.execute('INSERT INTO audit(task,event,actor,details,previous_hash,event_hash,created_at) VALUES(?,?,?,?,?,?,?)',
                   (task,event,actor,details_string,prev,digest,when))
    def _binding(self,db,task,actor,role='expert'):
        if task not in ARMS:deny('TASK_NOT_FOUND',404)
        row=db.execute('SELECT * FROM bindings WHERE task=?',(task,)).fetchone()
        if not row or row['actor']!=actor or role!='expert':deny('TASK_NOT_FOUND',404)
        return row
    def _snapshot(self,db,task,kind):
        return db.execute('SELECT * FROM snapshots WHERE task=? AND kind=?',(task,kind)).fetchone()
    def _valid_snapshot(self,row):
        if row and sha(row['payload'])!=row['content_sha']:
            deny('IMMUTABLE_SNAPSHOT_INTEGRITY_FAILURE',409)
        return row
    def _candidate(self,db,task):
        row=db.execute('SELECT * FROM candidates WHERE task=?',(task,)).fetchone()
        if row and sha(row['payload'])!=row['candidate_sha']:
            deny('CANDIDATE_INTEGRITY_FAILURE',409)
        return row
    def _phase(self,db,task):
        arm=ARMS[task];cand=self._candidate(db,task)
        if arm=='R0':return 'HUMAN_DE_NOVO_LOCKED' if self._snapshot(db,task,'J_human_de_novo') else 'HUMAN_DE_NOVO'
        if arm=='R1':return 'VERIFY_LOCKED' if self._snapshot(db,task,'R1_verified') else 'EXPERT_VERIFY' if cand else 'WAIT_AGENT_FREEZE'
        pre=self._valid_snapshot(self._snapshot(db,task,'J_preAI'))
        if not pre:return 'PRE_AI'
        if self._snapshot(db,task,'J_postAI'):return 'POST_AI_LOCKED'
        return 'POST_AI' if cand else 'WAIT_AGENT_FREEZE'
    def qualify(self,task,actor,screen:dict)->dict:
        if task not in ARMS:deny('TASK_NOT_FOUND',404)
        if screen['actor_id']!=actor or not actor.startswith('SYN-EXPERT-'):deny('SYNTHETIC_IDENTITY_REQUIRED',422)
        flags=['prior_exposure_to_exact_case','prior_exposure_to_other_arm_output_for_case',
               'prior_access_to_hidden_diet_values','prior_access_to_SRS_claim_labels',
               'prior_access_to_final_reference','prior_access_to_other_expert_judgment']
        if any(screen[k] for k in flags) or screen['declared_conflicts']:
            deny('EXPERT_ELIGIBILITY_SCREEN_FAILED',422)
        with self.conn() as db:
            db.execute('BEGIN IMMEDIATE')
            existing=db.execute('SELECT task FROM bindings WHERE task=? OR (case_ref=? AND actor=?)',(task,CASE_REF,actor)).fetchone()
            if existing:deny('SLOT_ALREADY_BOUND_OR_CROSS_ARM_REUSE',409)
            seal=sha(canonical_json(screen))
            db.execute('INSERT INTO bindings VALUES(?,?,?,?,?,?)',(task,CASE_REF,ARMS[task],actor,seal,utc()))
            self._log(db,task,'QUALIFY_AND_BIND_SYNTHETIC',actor,{'slot':self.a.slots[ARMS[task]],'screen_sha':seal})
        return {'task_id':task,'arm':ARMS[task],'expert_slot':self.a.slots[ARMS[task]],
                'qualified':'SYNTHETIC_ONLY','binding':'BOUND_SYNTHETIC'}
    def task_list(self,actor,role):
        if role!='expert':return {'tasks':[],'mode':'SYNTHETIC_ENGINEERING_ONLY'}
        with self.conn() as db:
            rows=db.execute('SELECT task,arm FROM bindings WHERE actor=?',(actor,)).fetchall()
            return {'tasks':[{'task_id':r['task'],'arm':r['arm'],'phase':self._phase(db,r['task']),
                              'synthetic':True} for r in rows],'mode':'SYNTHETIC_ENGINEERING_ONLY'}
    def read_model(self,task,actor,role):
        # Read surfaces are created in service only. Never expose internal candidate store to R0/R2-preAI.
        with self.conn() as db:
            # First candidate exposure and its audit receipt are one transaction.
            # Reader and judgment panes may request this projection concurrently.
            db.execute('BEGIN IMMEDIATE')
            row=self._binding(db,task,actor,role);arm=row['arm'];phase=self._phase(db,task)
            result={'task_id':task,'case_ref':CASE_REF,'arm':arm,'expert_slot':self.a.slots[arm],
                    'phase':phase,'synthetic':True,'protocol':'NDS-R1 adapter engineering v0.2',
                    'capture_status':'DISABLED_REAL_EXPERTS','allowed_actions':[], 'source':None}
            if arm=='R0':
                result['source']=self.a.human_projection()
                result['allowed_actions']=['draft','freeze'] if phase=='HUMAN_DE_NOVO' else ['view_frozen']
                return result
            if arm=='R1':
                if phase=='WAIT_AGENT_FREEZE':return result
                if phase=='VERIFY_LOCKED':return result
                candidate=self._candidate(db,task)
                if not candidate:deny('MISSING_CANDIDATE_SET',409)
                self._expose(db,task,actor,candidate)
                result['source']={'case_ref':CASE_REF,'case_view':self.a.case_view,
                                 'source_spans_by_candidate':{x['candidate_ref']:x['source_spans'] for x in json.loads(candidate['payload'])}}
                result['candidate_set']={'candidate_set_sha':candidate['candidate_sha'],'items':json.loads(candidate['payload'])}
                result['allowed_actions']=['verify']
                db.commit();return result
            # R2
            pre=self._valid_snapshot(self._snapshot(db,task,'J_preAI'))
            if not pre:
                result['source']=self.a.human_projection();result['allowed_actions']=['draft','freeze']
                return result
            result['J_preAI']={'payload':json.loads(pre['payload']),'content_sha':pre['content_sha'],'read_only':True}
            if phase=='WAIT_AGENT_FREEZE':return result
            if phase=='POST_AI_LOCKED':return result
            candidate=self._candidate(db,task)
            if not candidate:deny('MISSING_CANDIDATE_SET',409)
            self._expose(db,task,actor,candidate)
            result['candidate_set']={'candidate_set_sha':candidate['candidate_sha'],'items':json.loads(candidate['payload'])}
            result['source']={'case_ref':CASE_REF,'source_spans_by_candidate':{x['candidate_ref']:x['source_spans'] for x in json.loads(candidate['payload'])}}
            result['allowed_actions']=['reconcile']
            db.commit();return result
    def _expose(self,db,task,actor,candidate):
        prior=db.execute('SELECT * FROM exposed WHERE task=?',(task,)).fetchone()
        if prior:
            if prior['actor']!=actor or prior['candidate_sha']!=candidate['candidate_sha']:
                deny('EXPOSURE_HISTORY_MISMATCH',409)
            return
        arm=ARMS[task]
        if arm=='R0':deny('AGENT_NEVER_FOR_R0')
        if arm=='R2':
            pre=self._valid_snapshot(self._snapshot(db,task,'J_preAI'))
            if not pre or pre['packet_digest']!=self.a.packet_identity:
                deny('R2_PREAI_FREEZE_REQUIRED')
        db.execute('INSERT INTO exposed VALUES(?,?,?,?)',(task,actor,candidate['candidate_sha'],utc()))
        self._log(db,task,'CANDIDATE_EXPOSURE',actor,{'candidate_sha':candidate['candidate_sha']})
    def draft(self,task,actor,role):
        with self.conn() as db:
            self._binding(db,task,actor,role)
            if self._phase(db,task) not in ('PRE_AI','HUMAN_DE_NOVO'):
                deny('DRAFT_NOT_AVAILABLE')
            row=db.execute('SELECT * FROM drafts WHERE task=?',(task,)).fetchone()
            return {'revision':row['revision'] if row else 0,
                    'payload':json.loads(row['payload']) if row else self.a.response_schema,
                    'packet_digest':self.a.packet_identity,'task_id':task,'synthetic':True}
    def save(self,task,actor,role,expected_revision,payload,packet_digest):
        if packet_digest!=self.a.packet_identity:deny('SOURCE_PACKET_VERSION_MISMATCH',409)
        try:validate_decision(payload,self.a.response_schema)
        except ValueError as e:deny(str(e),422)
        with self.conn() as db:
            db.execute('BEGIN IMMEDIATE');self._binding(db,task,actor,role)
            if self._phase(db,task) not in ('PRE_AI','HUMAN_DE_NOVO'):
                deny('DRAFT_IMMUTABLE_OR_FORBIDDEN')
            prev=db.execute('SELECT revision FROM drafts WHERE task=?',(task,)).fetchone()
            rev=prev['revision'] if prev else 0
            if rev!=expected_revision:deny('REVISION_CONFLICT',409)
            db.execute('INSERT INTO drafts VALUES(?,?,?,?,?) ON CONFLICT(task) DO UPDATE SET revision=excluded.revision,payload=excluded.payload,packet_digest=excluded.packet_digest,updated_at=excluded.updated_at',
                (task,rev+1,canonical_json(payload),packet_digest,utc()))
            self._log(db,task,'SAVE_DRAFT',actor,{'revision':rev+1})
            return {'revision':rev+1,'task_id':task,'synthetic':True}
    def freeze(self,task,actor,role,expected_revision,idem,assertions):
        if set(assertions)!=ASSERT_KEYS or any(type(v) is not bool or v for v in assertions.values()):
            deny('EXPOSURE_ASSERTIONS_MUST_ALL_BE_FALSE',422)
        with self.conn() as db:
            db.execute('BEGIN IMMEDIATE');self._binding(db,task,actor,role)
            arm=ARMS[task];kind={'R0':'J_human_de_novo','R2':'J_preAI'}.get(arm)
            if kind is None:deny('R1_HAS_NO_PREAI_FREEZE')
            old=self._valid_snapshot(self._snapshot(db,task,kind))
            if old:
                if old['idem']==idem and old['actor']==actor:
                    current=db.execute('SELECT revision FROM drafts WHERE task=?',(task,)).fetchone()
                    if not current or current['revision']!=expected_revision:deny('IDEMPOTENCY_PAYLOAD_CONFLICT',409)
                    return self._receipt(old,task,kind)
                deny('ALREADY_FROZEN',409)
            if db.execute('SELECT 1 FROM exposed WHERE task=?',(task,)).fetchone():deny('PREAI_EXPOSURE_VIOLATION',409)
            draft=db.execute('SELECT * FROM drafts WHERE task=?',(task,)).fetchone()
            if not draft or draft['revision']!=expected_revision:deny('DRAFT_REVISION_CONFLICT',409)
            if draft['packet_digest']!=self.a.packet_identity:deny('SOURCE_PACKET_VERSION_MISMATCH',409)
            val=json.loads(draft['payload']);validate_decision(val,self.a.response_schema)
            if not (val['decision_focus'] or val['uncertainty_notes']):deny('EMPTY_JUDGMENT',422)
            # Bind the allowed evidence-anchor association set to the freeze audit
            # before J_preAI/J_human becomes immutable. This association digest is
            # engineering provenance, not scientific judgment content_sha.
            bind_rows=db.execute('SELECT anchor_id,field,document_revision,pdf_sha256 FROM source_bindings WHERE task=? ORDER BY field,anchor_id',(task,)).fetchall()
            evidence_digest=sha(canonical_json([dict(x) for x in bind_rows]))
            self._log(db,task,'FREEZE_SOURCE_BINDING_SET',actor,{'binding_sha256':evidence_digest,'count':len(bind_rows)})
            c=canonical_json(val);digest=sha(c);now=utc()
            db.execute('INSERT INTO snapshots VALUES(?,?,?,?,?,?,?,?)',
                       (task,kind,actor,c,digest,draft['packet_digest'],now,idem))
            self._log(db,task,'FREEZE_'+kind,actor,{'content_sha':digest,'packet_sha':draft['packet_digest'],'revision':expected_revision})
            return {'task_id':task,'kind':kind,'expert_slot':self.a.slots[arm],'submitted_at':now,
                    'content_sha':digest,'exposure_check':'PASS','status':'FROZEN_SYNTHETIC_ONLY',
                    'scientific_capture':False}
    def _receipt(self,row,task,kind):
        return {'task_id':task,'kind':kind,'expert_slot':self.a.slots[ARMS[task]],'submitted_at':row['created_at'],
                'content_sha':row['content_sha'],'exposure_check':'PASS','status':'FROZEN_SYNTHETIC_ONLY',
                'scientific_capture':False}
    def generate(self,task,actor,role,candidates:list[dict],idem):
        if role!='producer' or not actor.startswith('SYN-PRODUCER'):deny('NOT_SYSTEM_PRODUCER')
        if task not in ARMS or ARMS[task]=='R0':deny('AGENT_NEVER_FOR_R0')
        if len({x['candidate_ref'] for x in candidates})!=len(candidates):deny('DUPLICATE_CANDIDATE_REF',422)
        for entry in candidates:
            if not entry['source_spans'] or any(set(ref)!={'source_ref','quote'} or not all(ref.values()) for ref in entry['source_spans']):
                deny('SOURCE_SPAN_REQUIRED',422)
        with self.conn() as db:
            db.execute('BEGIN IMMEDIATE')
            if not db.execute('SELECT 1 FROM bindings WHERE task=?',(task,)).fetchone():deny('EXPERT_QUALIFICATION_BINDING_REQUIRED')
            if ARMS[task]=='R2':
                pre=self._valid_snapshot(self._snapshot(db,task,'J_preAI'))
                if not pre or pre['packet_digest']!=self.a.packet_identity:deny('R2_PREAI_FREEZE_REQUIRED')
            old=self._candidate(db,task)
            if old:
                if old['idem']==idem and old['candidate_sha']==sha(canonical_json(candidates)):
                    return {'candidate_set_sha':old['candidate_sha'],'status':'FROZEN_SYNTHETIC_ONLY'}
                deny('CANDIDATE_SET_IMMUTABLE',409)
            c=canonical_json(candidates);digest=sha(c)
            db.execute('INSERT INTO candidates VALUES(?,?,?,?,?,?)',(task,actor,c,digest,utc(),idem))
            self._log(db,task,'FREEZE_AGENT_CANDIDATES_SYNTHETIC',actor,{'candidate_sha':digest,'count':len(candidates)})
            return {'candidate_set_sha':digest,'status':'FROZEN_SYNTHETIC_ONLY'}
    def candidate_endpoint(self,task,actor,role):
        if task not in ARMS:deny('TASK_NOT_FOUND',404)
        return self.read_model(task,actor,role).get('candidate_set') or deny('TASK_NOT_READY')
    def complete(self,task,actor,role,items,idem,post=None):
        if task not in ARMS or ARMS[task]=='R0':deny('TASK_NOT_FOUND',404)
        kind='R1_verified' if ARMS[task]=='R1' else 'J_postAI'
        with self.conn() as db:
            db.execute('BEGIN IMMEDIATE');self._binding(db,task,actor,role)
            old=self._valid_snapshot(self._snapshot(db,task,kind))
            if old:
                if old['actor']==actor and old['idem']==idem:
                    stored=json.loads(old['payload'])
                    if stored.get('items')!=items or stored.get('post_ai_judgment')!=post:
                        deny('IDEMPOTENCY_PAYLOAD_CONFLICT',409)
                    return self._receipt(old,task,kind)
                deny('ALREADY_FROZEN',409)
            candidate=self._candidate(db,task)
            exposure=db.execute('SELECT * FROM exposed WHERE task=?',(task,)).fetchone()
            if not candidate or not exposure or exposure['actor']!=actor:deny('MUST_EXPOSE_FROZEN_CANDIDATE_FIRST')
            refs={x['candidate_ref'] for x in json.loads(candidate['payload'])}
            if {x['candidate_ref'] for x in items}!=refs or len(items)!=len(refs):deny('INCOMPLETE_OR_DUPLICATE_RECONCILIATION',422)
            if post is not None:
                if ARMS[task]!='R2':deny('R1_POST_AI_NOT_APPLICABLE')
                try:validate_decision(post,self.a.response_schema)
                except ValueError as e:deny(str(e),422)
            elif ARMS[task]=='R2':deny('R2_POST_AI_JUDGMENT_REQUIRED',422)
            pre=self._valid_snapshot(self._snapshot(db,task,'J_preAI')) if ARMS[task]=='R2' else None
            payload={'items':items,'candidate_set_sha':candidate['candidate_sha']}
            if pre:
                payload.update({'pre_ai_content_sha':pre['content_sha'],'post_ai_judgment':post})
            c=canonical_json(payload);digest=sha(c);now=utc()
            db.execute('INSERT INTO snapshots VALUES(?,?,?,?,?,?,?,?)',
                (task,kind,actor,c,digest,self.a.packet_identity,now,idem))
            self._log(db,task,'FREEZE_'+kind,actor,{'content_sha':digest,'candidate_sha':candidate['candidate_sha']})
            return self._receipt(db.execute('SELECT * FROM snapshots WHERE task=? AND kind=?',(task,kind)).fetchone(),task,kind)
    def audit(self,actor,role,task):
        if role!='auditor':deny('AUDITOR_ONLY')
        if task not in ARMS:deny('TASK_NOT_FOUND',404)
        with self.conn() as db:
            rows=db.execute('SELECT event,actor,details,previous_hash,event_hash,created_at FROM audit WHERE task=? ORDER BY id',(task,)).fetchall()
            prev='GENESIS'
            for event in rows:
                if event['previous_hash']!=prev:
                    deny('AUDIT_CHAIN_INTEGRITY_FAILURE',409)
                expected=sha(canonical_json({'prev':prev,'event':event['event'],'actor':event['actor'],
                    'details':event['details'],'when':event['created_at'],'task':task}))
                if expected!=event['event_hash']:deny('AUDIT_CHAIN_INTEGRITY_FAILURE',409)
                prev=event['event_hash']
            return {'task_id':task,'events':[dict(r) for r in rows],'synthetic':True}
