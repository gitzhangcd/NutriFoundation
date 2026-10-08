"""WB-P0.2-C1 demo-only reader/judgment integration; NOT an NDS role/exposure controller.

No qualifying expert, no formal judgment freeze, no Agent candidates or Gold.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from reader_core import Store, make_app as make_reader_app

BASE = Path(__file__).resolve().parent
DEFAULT_ROOT = BASE / 'data'
PROFILE = json.loads((BASE / 'specs/decision_profile.json').read_text(encoding='utf-8'))
FIELD_INFO = {field['key']: field['type'] for group in PROFILE['field_groups'] for field in group['fields']}
REFS = PROFILE['reference_set_categories']
TASKS = {
    'DEMO-R2-PREAI': {'id':'DEMO-R2-PREAI', 'arm':'R2', 'phase':'PRE_AI', 'profile':'NDS_R1_DECISION_CAPTURE', 'label':'5:2 diet 文献证据阅读与合成决策采集', 'synthetic': True},
    'DEMO-R0-NOAI': {'id':'DEMO-R0-NOAI', 'arm':'R0', 'phase':'HUMAN_DE_NOVO', 'profile':'NDS_R1_DECISION_CAPTURE', 'label':'无 Agent 证据判断 · 合成演示', 'synthetic': True},
}


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def empty_decision() -> dict:
    return {
        'decision_focus': None, 'salient_existing_facts': [],
        'decision_changing_missing_information': [], 'currently_acceptable_actions': [],
        'conditional_actions': [], 'not_indicated_prohibited_or_unsafe': [],
        'process_action': [], 'monitoring_needs': [],
        'reference_set': {key: [] for key in REFS},
        'uncertainty_notes': [], 'rationale_notes': [],
        'active_expert_minutes': None, 'clarification_count': 0,
    }


def get_field_value(obj: dict, key: str):
    result = obj
    for part in key.split('.'):
        result = result[part]
    return result


def validate_payload(payload: Any) -> None:
    blank = empty_decision()
    if not isinstance(payload, dict) or set(payload) != set(blank):
        raise ValueError('DECISION_TOP_LEVEL_SCHEMA_MISMATCH')
    if not isinstance(payload.get('reference_set'), dict) or set(payload['reference_set']) != set(REFS):
        raise ValueError('REFERENCE_SET_SCHEMA_MISMATCH')
    for key, typ in FIELD_INFO.items():
        v = get_field_value(payload, key)
        if typ == 'ordered_string_list':
            if not isinstance(v, list) or len(v) > 200 or any(not isinstance(x, str) or len(x)>2000 for x in v):
                raise ValueError('INVALID_FIELD_TYPE:'+key)
        elif typ == 'nullable_string':
            if v is not None and (not isinstance(v,str) or len(v)>10000):
                raise ValueError('INVALID_FIELD_TYPE:'+key)
        elif typ == 'nullable_nonnegative_number':
            if v is not None and (type(v) not in (int,float) or not 0<=v<=1e5):
                raise ValueError('INVALID_FIELD_TYPE:'+key)
        elif typ == 'nonnegative_integer':
            if type(v) is not int or not 0<=v<=1e5:
                raise ValueError('INVALID_FIELD_TYPE:'+key)
        else: raise ValueError('UNSUPPORTED_PROFILE_FIELD:'+key)


class SaveRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    expected_revision: int = Field(ge=0)
    document_id: str
    canonical_revision: str
    source_pdf_sha256: str
    payload: dict[str, Any]
    bindings: dict[str, list[str]]


class DraftDB:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS demo_drafts(
              task_id TEXT PRIMARY KEY, document_id TEXT NOT NULL, canonical_revision TEXT NOT NULL,
              source_pdf_sha256 TEXT NOT NULL, revision INTEGER NOT NULL,
              payload_json TEXT NOT NULL, bindings_json TEXT NOT NULL, updated_at TEXT NOT NULL
            )''')
            db.execute('''CREATE TABLE IF NOT EXISTS demo_events(
              id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL,
              event_type TEXT NOT NULL, revision INTEGER NOT NULL, created_at TEXT NOT NULL
            )''')

    def connect(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.path, timeout=10)
        c.row_factory = sqlite3.Row
        return c

    def load(self, task_id: str, doc: dict | None) -> dict:
        if doc is None: raise HTTPException(409,'SOURCE_NOT_IMPORTED')
        with self.connect() as db:
            row = db.execute('SELECT * FROM demo_drafts WHERE task_id=?', (task_id,)).fetchone()
        if row is None:
            return {'task_id':task_id,'revision':0,'document_id':doc['document_id'],
                    'canonical_revision':doc['revision'],'source_pdf_sha256':doc['source_pdf_sha256'],
                    'payload':empty_decision(),'bindings':{},'updated_at':None,'synthetic':True}
        if (row['document_id'],row['canonical_revision'],row['source_pdf_sha256']) != (
            doc['document_id'],doc['revision'],doc['source_pdf_sha256']):
            raise HTTPException(409,'STALE_DOCUMENT_BINDING')
        return {'task_id':task_id,'revision':row['revision'],'document_id':row['document_id'],
                'canonical_revision':row['canonical_revision'],'source_pdf_sha256':row['source_pdf_sha256'],
                'payload':json.loads(row['payload_json']),'bindings':json.loads(row['bindings_json']),
                'updated_at':row['updated_at'],'synthetic':True}

    def save(self, task_id: str, req: SaveRequest, doc: dict, anchor_store: Store) -> dict:
        if (req.document_id, req.canonical_revision, req.source_pdf_sha256) != (
            doc['document_id'],doc['revision'],doc['source_pdf_sha256']):
            raise HTTPException(409,'STALE_DOCUMENT_BINDING')
        try: validate_payload(req.payload)
        except ValueError as e: raise HTTPException(422,str(e)) from e
        if not isinstance(req.bindings,dict) or set(req.bindings)-set(FIELD_INFO):
            raise HTTPException(422,'UNKNOWN_FIELD_BINDING')
        # Enforce immutable source-bound anchor identity for every bound ID.
        for field, ids in req.bindings.items():
            if not isinstance(ids,list) or len(ids)>50 or len(ids)!=len(set(ids)):
                raise HTTPException(422,'INVALID_ANCHOR_BINDINGS:'+field)
            for anchor_id in ids:
                if not isinstance(anchor_id,str): raise HTTPException(422,'INVALID_ANCHOR_ID')
                try: anchor = anchor_store.get_anchor(anchor_id)
                except ValueError: raise HTTPException(422,'UNKNOWN_ANCHOR_ID') from None
                if (anchor['document_id'] != doc['document_id'] or
                    anchor['canonical_revision'] != doc['revision'] or
                    anchor['source_pdf_sha256'] != doc['source_pdf_sha256'] or
                    anchor['source_markdown_sha256'] != doc['source_markdown_sha256']):
                    raise HTTPException(409,'STALE_ANCHOR_SOURCE')
        with self.connect() as db:
            try:
                db.execute('BEGIN IMMEDIATE')
                row=db.execute('SELECT revision FROM demo_drafts WHERE task_id=?',(task_id,)).fetchone()
                version=row['revision'] if row else 0
                if version!=req.expected_revision:
                    db.rollback()
                    raise HTTPException(409,{'code':'REVISION_CONFLICT','server_revision':version})
                next_version=version+1
                params=(doc['document_id'],doc['revision'],doc['source_pdf_sha256'],next_version,
                        json.dumps(req.payload,ensure_ascii=False,separators=(',',':')),
                        json.dumps(req.bindings,ensure_ascii=False,separators=(',',':')),utc(),task_id)
                if row:
                    db.execute('''UPDATE demo_drafts SET document_id=?, canonical_revision=?,source_pdf_sha256=?,
                      revision=?,payload_json=?,bindings_json=?,updated_at=? WHERE task_id=?''', params)
                else:
                    db.execute('''INSERT INTO demo_drafts
                    (document_id,canonical_revision,source_pdf_sha256,revision,payload_json,bindings_json,updated_at,task_id)
                    VALUES(?,?,?,?,?,?,?,?)''', params)
                db.execute('INSERT INTO demo_events(task_id,event_type,revision,created_at) VALUES(?,?,?,?)',
                           (task_id,'SYNTHETIC_DRAFT_SAVE',next_version,utc()))
                db.commit()
            except Exception:
                db.rollback()
                raise
        return self.load(task_id,doc)


def make_app(root: Path, *, preload_fixture: bool=False) -> FastAPI:
    root=Path(root)
    root.mkdir(parents=True,exist_ok=True)
    anchor_store=Store(root/'sources')
    if preload_fixture and anchor_store.document() is None:
        anchor_store.import_bytes((BASE/'fixtures/5_2_diet.AnnotationSourcePackage.v0.1.zip').read_bytes())
    db=DraftDB(root/'drafts.sqlite')
    app=FastAPI(title='WB-P0.2-C1 Synthetic Reader and Durable Draft Integration')
    reader=make_reader_app(root/'sources')
    app.mount('/reader',reader)

    @app.get('/api/health')
    def health():
        return {'status':'OK','stage':'WB-P0.2-C1','mode':'SYNTHETIC_DEVELOPMENT_ONLY',
                'scientific_capture':'DISABLED','agent_candidates':'NOT_IMPLEMENTED','freeze':'NOT_IMPLEMENTED'}

    @app.get('/api/profile')
    def profile():return PROFILE

    @app.get('/api/tasks')
    def tasks():return {'tasks':list(TASKS.values()),'mode':'SYNTHETIC_DEVELOPMENT_ONLY'}

    def check_task(task_id:str):
        if task_id not in TASKS: raise HTTPException(404,'UNKNOWN_SYNTHETIC_TASK')

    @app.get('/api/tasks/{task_id}/draft')
    def get_draft(task_id:str):
        check_task(task_id)
        return db.load(task_id,anchor_store.document())

    @app.put('/api/tasks/{task_id}/draft')
    def put_draft(task_id:str, req: SaveRequest):
        check_task(task_id)
        doc=anchor_store.document()
        if doc is None:raise HTTPException(409,'SOURCE_NOT_IMPORTED')
        return db.save(task_id,req,doc,anchor_store)

    @app.get('/api/tasks/{task_id}/export')
    def export(task_id:str):
        check_task(task_id)
        x=db.load(task_id,anchor_store.document())
        return {'provenance':'SYNTHETIC_ONLY_NOT_SCIENTIFIC_OUTPUT','schema':'C1_DRAFT_EXPORT/0.1',**x}

    @app.get('/api/tasks/{task_id}/events')
    def events(task_id:str):
        check_task(task_id)
        with db.connect() as c:
            rows=c.execute('SELECT event_type, revision, created_at FROM demo_events WHERE task_id=? ORDER BY id',(task_id,)).fetchall()
        return {'synthetic':True,'events':[dict(r) for r in rows]}

    app.mount('/static',StaticFiles(directory=BASE/'web'),name='c1-static')

    @app.get('/')
    def index():return FileResponse(BASE/'web/index.html')

    return app


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,default=DEFAULT_ROOT)
    p.add_argument('--port',type=int,default=8788)
    p.add_argument('--host',default='127.0.0.1')
    p.add_argument('--demo-source',action='store_true')
    args=p.parse_args()
    import uvicorn
    uvicorn.run(make_app(args.root,preload_fixture=args.demo_source),host=args.host,port=args.port)


if __name__=='__main__':main()