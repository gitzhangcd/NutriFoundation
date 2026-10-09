"""WB-P0.2-C2.1: synthetic task-scoped reader adapter; never mounts C1 raw routes.

A public real-paper fixture is deliberately distinct from the NDS-R1 authorised
Human Baseline Source Packet. No real clinical/scientific capture is enabled.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path

import fitz
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field

from reader_core import Store, AnchorRequest, LocatorResolveRequest, substring_u16
from pdf_locator import LocatorError, locate_pdf_quote
from workflow import ARMS, deny, sha
from models import canonical_json
from bilingual import projection as bilingual_projection
from translation_contract import validate as validate_translation_pack
from ux_bilingual_demo import projection as synthetic_ux_demo

SOURCE_ID = 'SYN-5-2-PAPER'
GIT_BLOB_SHA = 'fe9d476f52981c7c1d536b8578559b109a5fcbec'
MAX_SEARCH_RESULTS = 16
CJK = re.compile(r'[\u3400-\u9fff\uf900-\ufaff]')
MARKDOWN_MARKUP = re.compile(r'\*\*|__|^#{1,6}\s+', re.M)


def search_text(value: str) -> str:
    """Same visible text as the reader's plainMarkdown(), whitespace collapsed."""
    return ' '.join(MARKDOWN_MARKUP.sub('', value).split()).casefold()


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid')


class BindAnchor(Strict):
    anchor_id: str = Field(min_length=3, max_length=100)
    field: str = Field(min_length=2, max_length=100)
    expected_document_revision: str
    expected_pdf_sha256: str

class BindAnchorItem(BindAnchor):
    item_index: int = Field(ge=0, le=1000)
    item_sha256: str = Field(min_length=64, max_length=64)
    expected_draft_revision: int = Field(ge=1)

def gitblob(raw: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\x00' + raw).hexdigest()


def install_secure_reader(app: FastAPI, controller, root: Path, principal, fixture: Path):
    """Add only authenticated, scope-checked endpoints to C2's existing app."""
    if not fixture.is_file():
        raise RuntimeError('PINNED_SYNTHETIC_SOURCE_MISSING')
    payload = fixture.read_bytes()
    if gitblob(payload) != GIT_BLOB_SHA:
        raise RuntimeError('SYNTHETIC_FIXTURE_BLOB_CHANGED')
    store = Store(Path(root) / 'sources')
    doc = store.import_bytes(payload)
    # Do not register a global source list or grant science source permissions.
    app.state.source_store = store
    app.state.synthetic_source_id = SOURCE_ID
    approved = {x for x in controller.a.response_schema if x != 'reference_set'}
    approved |= {'reference_set.' + k for k in controller.a.response_schema['reference_set']}

    with controller.conn() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS source_bindings (
            task TEXT NOT NULL, anchor_id TEXT NOT NULL, field TEXT NOT NULL,
            actor TEXT NOT NULL, document_revision TEXT NOT NULL,
            pdf_sha256 TEXT NOT NULL, created_at TEXT NOT NULL,
            PRIMARY KEY(task,anchor_id,field)
        )''')
        db.executescript('''
        CREATE TRIGGER IF NOT EXISTS immut_source_bind_update BEFORE UPDATE ON source_bindings BEGIN SELECT RAISE(ABORT,'IMMUTABLE_SOURCE_BINDING'); END;
        CREATE TRIGGER IF NOT EXISTS immut_source_bind_delete BEFORE DELETE ON source_bindings BEGIN SELECT RAISE(ABORT,'IMMUTABLE_SOURCE_BINDING'); END;
        ''')

    with sqlite3.connect(store.db) as db:
        db.executescript('''
        CREATE TRIGGER IF NOT EXISTS immutable_anchor_update BEFORE UPDATE ON anchors BEGIN SELECT RAISE(ABORT,'IMMUTABLE_SOURCE_ANCHOR'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_anchor_delete BEFORE DELETE ON anchors BEGIN SELECT RAISE(ABORT,'IMMUTABLE_SOURCE_ANCHOR'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_locator_update BEFORE UPDATE ON pdf_locators BEGIN SELECT RAISE(ABORT,'IMMUTABLE_PDF_LOCATOR'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_locator_delete BEFORE DELETE ON pdf_locators BEGIN SELECT RAISE(ABORT,'IMMUTABLE_PDF_LOCATOR'); END;
        ''')

    @app.middleware('http')
    async def confidentiality_headers(request, call_next):
        response = await call_next(request)
        for k, v in {
            'Cache-Control': 'private, no-store, max-age=0, must-revalidate',
            'Pragma': 'no-cache', 'Expires': '0',
            'Vary': 'X-Workbench-Token',
            'Referrer-Policy': 'no-referrer',
            'X-Content-Type-Options': 'nosniff',
            'X-Robots-Tag': 'noindex, nofollow',
            'Content-Security-Policy': "default-src 'self'; script-src 'self'; worker-src 'self' blob:; img-src 'self' data:; style-src 'self'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'"
        }.items(): response.headers[k] = v
        return response

    def allowed(task: str, actor: str, role: str, *, full: bool):
        if task not in ARMS: deny('TASK_NOT_FOUND', 404)
        with controller.conn() as db:
            binding = controller._binding(db, task, actor, role)
            phase = controller._phase(db, task)
            # Public real-paper engineering fixture is intentionally available
            # to *synthetic* Human De Novo and Pre/Post AI workflow exercises only.
            if binding['arm'] == 'R1':
                if full: deny('SOURCE_NOT_IN_TASK_PROJECTION', 404)
                if phase != 'EXPERT_VERIFY': deny('SOURCE_NOT_IN_TASK_PROJECTION', 404)
            elif binding['arm'] not in ('R0', 'R2'):
                deny('SOURCE_NOT_IN_TASK_PROJECTION', 404)
        return phase

    def exact_source(source_id: str):
        if source_id != SOURCE_ID: deny('SOURCE_NOT_IN_TASK_PROJECTION', 404)
        if store.document()['revision'] != doc['revision']:
            deny('CANONICAL_SOURCE_REVISION_CHANGED', 409)

    def pdf_integrity():
        try:
            path=store.verified_pdf_path()
            if hashlib.sha256(store.path('document.md').read_bytes()).hexdigest()!=doc['source_markdown_sha256']:
                deny('SOURCE_INTEGRITY_FAILURE',409)
            return path
        except (LocatorError, ValueError, OSError): deny('SOURCE_INTEGRITY_FAILURE', 409)

    def checked_anchor(anchor_id):
        try:
            a=store.get_anchor(anchor_id)
            if (a['document_id']!=doc['document_id'] or
                a['canonical_revision']!=doc['revision'] or
                a['source_pdf_sha256']!=doc['source_pdf_sha256'] or
                a['source_markdown_sha256']!=doc['source_markdown_sha256'] or
                a['quote_sha256']!=hashlib.sha256(a['quote'].encode()).hexdigest()):
                deny('ANCHOR_INTEGRITY_FAILURE',409)
            u=next((u for u in doc['units'] if u['unit_id']==a['unit_id']),None)
            if u is None or a['unit_raw_sha256']!=u['raw_sha256'] or substring_u16(u['raw'],a['start_utf16'],a['end_utf16'])!=a['quote']:
                deny('ANCHOR_INTEGRITY_FAILURE',409)
            return a
        except (KeyError,ValueError,UnicodeError):deny('ANCHOR_INTEGRITY_FAILURE',409)

    def checked_locator(anchor_id):
        try:
            record=store.get_locator(anchor_id)
        except (LocatorError,ValueError):deny('BBOX_NOT_VERIFIABLE',409)
        if record is None:deny('BBOX_NOT_VERIFIABLE',404)
        digest=record.get('locator_sha256')
        rest={k:v for k,v in record.items() if k!='locator_sha256'}
        calc=hashlib.sha256(json.dumps(rest,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
        if digest!=calc or record.get('source_pdf_sha256')!=doc['source_pdf_sha256']:
            deny('BBOX_INTEGRITY_FAILURE',409)
        return record

    def task_anchor(db, task, anchor_id):
        # An anchor may be created before binding. Ownership is task scoped.
        row2 = db.execute('SELECT 1 FROM source_anchor_ownership WHERE task=? AND anchor_id=?',
                          (task,anchor_id)).fetchone()
        if not row2: deny('ANCHOR_NOT_FOUND',404)

    with controller.conn() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS source_anchor_ownership (
            task TEXT NOT NULL, anchor_id TEXT NOT NULL, actor TEXT NOT NULL,
            source_id TEXT NOT NULL, source_sha TEXT NOT NULL, document_revision TEXT NOT NULL,
            PRIMARY KEY(task,anchor_id)
        )''')

    # Append-only audit of source-bound translation bytes DELIVERED, not proof
    # that a human saw or accepted the translation. NEVER stores text in logs.
    with controller.conn() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS translation_projections_served (
          task TEXT NOT NULL, actor TEXT NOT NULL,
          translation_version TEXT NOT NULL, fixture_sha TEXT NOT NULL,
          source_sha TEXT NOT NULL, first_delivered_at TEXT NOT NULL,
          PRIMARY KEY(task,actor,translation_version,fixture_sha,source_sha)
        );
        CREATE TRIGGER IF NOT EXISTS protect_translation_served_update
          BEFORE UPDATE ON translation_projections_served
          BEGIN SELECT RAISE(ABORT,'IMMUTABLE_TRANSLATION_EXPOSURE'); END;
        CREATE TRIGGER IF NOT EXISTS protect_translation_served_delete
          BEFORE DELETE ON translation_projections_served
          BEGIN SELECT RAISE(ABORT,'IMMUTABLE_TRANSLATION_EXPOSURE'); END;
        """)

    # Additive item-level provenance. Original scientific 19-field schema and
    # existing field bindings remain unchanged. Link is immutable and is
    # rejected at read time if the referenced statement has since changed.
    with controller.conn() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS source_item_bindings (
          task TEXT NOT NULL, anchor_id TEXT NOT NULL, field TEXT NOT NULL,
          item_index INTEGER NOT NULL, item_sha256 TEXT NOT NULL,
          draft_revision INTEGER NOT NULL, actor TEXT NOT NULL,
          source_revision TEXT NOT NULL, pdf_sha256 TEXT NOT NULL,
          created_at TEXT NOT NULL,
          PRIMARY KEY(task, anchor_id, field, item_index, item_sha256)
        );
        CREATE TRIGGER IF NOT EXISTS immut_item_bind_update BEFORE UPDATE ON source_item_bindings
          BEGIN SELECT RAISE(ABORT,'IMMUTABLE_ITEM_BINDING'); END;
        CREATE TRIGGER IF NOT EXISTS immut_item_bind_delete BEFORE DELETE ON source_item_bindings
          BEGIN SELECT RAISE(ABORT,'IMMUTABLE_ITEM_BINDING'); END;
        """)

    @app.get('/v1/tasks/{task}/reading-demo')
    def bilingual_reading_demo(task:str,p=Depends(principal)):
        # Independently authored self-contained UX sample; no PDF or anchors,
        # no access for R1, administrators or unbound identities.
        allowed(task,*p,full=True)
        return synthetic_ux_demo()

    @app.get('/v1/tasks/{task}/sources')
    def sources(task: str, p=Depends(principal)):
        phase=allowed(task,*p,full=True)
        pdf_integrity()
        return {'sources':[{'id':SOURCE_ID,'kind':'SYNTHETIC_REAL_PAPER_FIXTURE',
                            'title':doc['title'],'revision':doc['revision'],
                            'pdf_sha256':doc['source_pdf_sha256'],
                            'not_scientific_source_packet':True}],
                'source_scope':'SYNTHETIC_TASK_EXERCISE_ONLY','phase':phase}

    def safe_doc():
        # Return text only, not Markdown/HTML transformed into executable DOM.
        return {'document_id':doc['document_id'], 'revision':doc['revision'],
                'source_pdf_sha256':doc['source_pdf_sha256'],
                'source_markdown_sha256':doc['source_markdown_sha256'],
                'title':doc['title'], 'unit_count':doc['unit_count'],
                'source_pages':doc['source_pages'], 'source_status':doc['source_status'],
                'units':[{k:u[k] for k in ('unit_id','type','heading','raw','pdf_page_hint','raw_sha256')}
                         for u in doc['units']]}

    @app.get('/v1/tasks/{task}/sources/{source_id}/document')
    def document(task: str, source_id: str, p=Depends(principal)):
        allowed(task,*p,full=True);exact_source(source_id);pdf_integrity()
        return safe_doc()

    def source_bound_translation_projection():
        # Operators may provision a *synthetic*, unverified full-unit pack in a
        # private runtime folder, not an API upload or publicly served asset.
        p = Path(root) / 'translation_sidecars' / (doc['document_id'] + '.json')
        if not p.exists():
            return bilingual_projection(doc)
        if not p.is_file() or p.is_symlink() or p.stat().st_size > 8_000_000:
            deny('TRANSLATION_SIDECAR_INVALID',409)
        try:
            pack = json.loads(p.read_text(encoding='utf-8'))
            return validate_translation_pack(doc, pack)
        except (ValueError, TypeError, KeyError, UnicodeError, OSError):
            deny('TRANSLATION_SIDECAR_INVALID',409)

    @app.get('/v1/tasks/{task}/sources/{source_id}/translations')
    def translations(task: str, source_id: str, p=Depends(principal)):
        # Delivery of translation can affect independent expert understanding:
        # serve only after exact task authorization AND record delivery atomically.
        # R1 is never allowed full-source translation.
        allowed(task, *p, full=True)
        exact_source(source_id)
        pdf_integrity()
        result = source_bound_translation_projection()
        from datetime import datetime, timezone
        with controller.conn() as db:
            db.execute('BEGIN IMMEDIATE')
            controller._binding(db, task, p[0], p[1])
            identity = (task, p[0], result['translation_version'],
                        result['translation_fixture_sha256'], doc['source_markdown_sha256'])
            previous = db.execute(
                'SELECT translation_version,fixture_sha,source_sha FROM '
                'translation_projections_served WHERE task=? AND actor=? LIMIT 1',
                (task,p[0])).fetchone()
            if previous and (previous['translation_version'] != result['translation_version'] or
                             previous['fixture_sha'] != result['translation_fixture_sha256'] or
                             previous['source_sha'] != doc['source_markdown_sha256']):
                deny('TRANSLATION_VERSION_CHANGED_AFTER_EXPOSURE',409)
            row = db.execute(
                'SELECT 1 FROM translation_projections_served WHERE '
                'task=? AND actor=? AND translation_version=? AND fixture_sha=? AND source_sha=?',
                identity).fetchone()
            if row is None:
                db.execute('INSERT INTO translation_projections_served VALUES (?,?,?,?,?,?)',
                           (*identity, datetime.now(timezone.utc).isoformat()))
                controller._log(db, task, 'TRANSLATION_PROJECTION_DELIVERED', p[0], {
                    'translation_version': result['translation_version'],
                    'fixture_sha': result['translation_fixture_sha256'],
                    'source_sha': doc['source_markdown_sha256'],
                    'qualified_translation': False})
        result['delivery_audit'] = 'RECORDED_NOT_PROOF_OF_HUMAN_VIEWING'
        return result

    searchable={u['unit_id']:search_text(u['raw']) for u in doc['units']}

    @app.get('/v1/tasks/{task}/sources/{source_id}/search')
    def search(task: str, source_id: str, q: str=Query(min_length=2,max_length=100),
               offset: int=Query(0,ge=0,le=10_000), p=Depends(principal)):
        allowed(task,*p,full=True);exact_source(source_id);pdf_integrity()
        needle=search_text(q)
        if len(needle)<(2 if CJK.search(needle) else 3):deny('SEARCH_QUERY_TOO_SHORT',422)
        # No source search across other tasks; only this fixed allowlisted document.
        results=[{'unit_id':u['unit_id'],'snippet':u['raw'][:450],
                  'pdf_page_hint':u['pdf_page_hint']} for u in doc['units'] if needle in searchable[u['unit_id']]]
        page=results[offset:offset+MAX_SEARCH_RESULTS]
        return {'results':page,'total':len(results),'offset':offset,
                'truncated':offset+len(page)<len(results)}

    @app.get('/v1/tasks/{task}/sources/{source_id}/original.pdf')
    def original(task:str,source_id:str,p=Depends(principal)):
        allowed(task,*p,full=True);exact_source(source_id)
        return Response(pdf_integrity().read_bytes(),media_type='application/pdf',
                        headers={'Content-Disposition':'inline; filename="task-scoped-source.pdf"'})

    @app.get('/v1/tasks/{task}/sources/{source_id}/pages/{page}/png')
    def page_image(task:str,source_id:str,page:int,scale:float=Query(1.3,ge=.6,le=2),p=Depends(principal)):
        allowed(task,*p,full=True);exact_source(source_id)
        with fitz.open(pdf_integrity()) as pdf:
            if not 1 <= page <= len(pdf):deny('PAGE_NOT_FOUND',404)
            content=pdf[page-1].get_pixmap(matrix=fitz.Matrix(scale,scale),alpha=False).tobytes('png')
        return Response(content,media_type='image/png')

    @app.get('/v1/tasks/{task}/sources/{source_id}/assets/{asset_id}')
    def asset(task:str,source_id:str,asset_id:str,p=Depends(principal)):
        allowed(task,*p,full=True);exact_source(source_id);pdf_integrity()
        manifest=json.loads(store.path('conversion_manifest.json').read_text())
        matched=[a for a in manifest.get('assets',[]) if hashlib.sha256(a['path'].encode()).hexdigest()[:20]==asset_id]
        if len(matched)!=1:deny('ASSET_NOT_FOUND',404)
        entry=matched[0]
        if not entry['path'].startswith('assets/') or '/' in entry['path'][7:]:deny('ASSET_NOT_FOUND',404)
        path=store.path(entry['path'])
        if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']:deny('SOURCE_INTEGRITY_FAILURE',409)
        return Response(path.read_bytes(),media_type='image/png' if path.suffix.lower()=='.png' else 'image/jpeg')

    @app.post('/v1/tasks/{task}/sources/{source_id}/anchors',status_code=201)
    def create_anchor(task:str,source_id:str,req:AnchorRequest,p=Depends(principal)):
        phase=allowed(task,*p,full=True);exact_source(source_id);pdf_integrity()
        if phase not in ('PRE_AI','HUMAN_DE_NOVO'):deny('SOURCE_BINDINGS_FROZEN')
        try:anchor=store.create_anchor(req)
        except ValueError:deny('STALE_OR_INVALID_QUOTE_RANGE',409)
        with controller.conn() as db:
            db.execute('BEGIN IMMEDIATE');controller._binding(db,task,p[0],p[1])
            if controller._phase(db,task) not in ('PRE_AI','HUMAN_DE_NOVO'):deny('SOURCE_BINDINGS_FROZEN')
            db.execute('INSERT OR IGNORE INTO source_anchor_ownership VALUES(?,?,?,?,?,?)',
                       (task,anchor['anchor_id'],p[0],SOURCE_ID,doc['source_pdf_sha256'],doc['revision']))
            controller._log(db,task,'SOURCE_ANCHOR_CREATED',p[0],{'anchor_id':anchor['anchor_id'],'source_sha':doc['source_pdf_sha256']})
        return anchor

    @app.get('/v1/tasks/{task}/sources/{source_id}/anchors')
    def anchors(task:str,source_id:str,p=Depends(principal)):
        allowed(task,*p,full=True);exact_source(source_id);pdf_integrity()
        with controller.conn() as db:
            ids=[r['anchor_id'] for r in db.execute('SELECT anchor_id FROM source_anchor_ownership WHERE task=? ORDER BY anchor_id',(task,))]
        return {'items':[checked_anchor(i) for i in ids]}

    @app.get('/v1/tasks/{task}/sources/{source_id}/anchors/{anchor_id}')
    def anchor(task:str,source_id:str,anchor_id:str,p=Depends(principal)):
        allowed(task,*p,full=True);exact_source(source_id);pdf_integrity()
        with controller.conn() as db:task_anchor(db,task,anchor_id)
        return checked_anchor(anchor_id)

    @app.post('/v1/tasks/{task}/sources/{source_id}/anchors/{anchor_id}/resolve')
    def resolve(task:str,source_id:str,anchor_id:str,req:LocatorResolveRequest,p=Depends(principal)):
        allowed(task,*p,full=True);exact_source(source_id);pdf_integrity()
        with controller.conn() as db:task_anchor(db,task,anchor_id)
        checked_anchor(anchor_id)
        try:return store.resolve_pdf_locator(anchor_id,req)
        except (LocatorError,ValueError):deny('BBOX_NOT_VERIFIABLE',409)

    @app.get('/v1/tasks/{task}/sources/{source_id}/anchors/{anchor_id}/locator')
    def locator(task:str,source_id:str,anchor_id:str,p=Depends(principal)):
        allowed(task,*p,full=True);exact_source(source_id);pdf_integrity()
        with controller.conn() as db:task_anchor(db,task,anchor_id)
        checked_anchor(anchor_id)
        return checked_locator(anchor_id)

    @app.post('/v1/tasks/{task}/sources/{source_id}/bind-anchor')
    def bind_anchor(task:str,source_id:str,req:BindAnchor,p=Depends(principal)):
        phase=allowed(task,*p,full=True);exact_source(source_id);pdf_integrity()
        if phase not in ('PRE_AI','HUMAN_DE_NOVO'):deny('SOURCE_BINDINGS_FROZEN')
        if req.field not in approved:deny('INVALID_PROFILE_FIELD',422)
        if req.expected_document_revision!=doc['revision'] or req.expected_pdf_sha256!=doc['source_pdf_sha256']:
            deny('STALE_SOURCE_BINDING',409)
        with controller.conn() as db:
            db.execute('BEGIN IMMEDIATE')
            controller._binding(db,task,p[0],p[1]);task_anchor(db,task,req.anchor_id)
            checked_anchor(req.anchor_id)
            if controller._phase(db,task) not in ('PRE_AI','HUMAN_DE_NOVO'):deny('SOURCE_BINDINGS_FROZEN')
            db.execute('INSERT OR IGNORE INTO source_bindings VALUES(?,?,?,?,?,?,?)',
                       (task,req.anchor_id,req.field,p[0],doc['revision'],doc['source_pdf_sha256'],__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()))
            controller._log(db,task,'SOURCE_ANCHOR_FIELD_BOUND',p[0],{'field':req.field,'anchor_id':req.anchor_id})
        return {'field':req.field,'anchor_id':req.anchor_id,'synthetic':True}

    def item_text(payload, field, index):
        value=payload
        for part in field.split('.'):
            if not isinstance(value,dict) or part not in value:
                deny('ITEM_FIELD_NOT_IN_DRAFT',422)
            value=value[part]
        if isinstance(value,str):
            if index!=0 or not value.strip():deny('ITEM_INDEX_NOT_FOUND',422)
            return value
        if isinstance(value,list) and 0<=index<len(value) and isinstance(value[index],str) and value[index].strip():
            return value[index]
        deny('ITEM_INDEX_NOT_FOUND',422)

    @app.post('/v1/tasks/{task}/sources/{source_id}/bind-anchor-item')
    def bind_anchor_item(task:str,source_id:str,req:BindAnchorItem,p=Depends(principal)):
        phase=allowed(task,*p,full=True);exact_source(source_id);pdf_integrity()
        if phase not in ('PRE_AI','HUMAN_DE_NOVO'):deny('SOURCE_BINDINGS_FROZEN',409)
        if req.field not in approved:deny('INVALID_PROFILE_FIELD',422)
        if req.expected_document_revision!=doc['revision'] or req.expected_pdf_sha256!=doc['source_pdf_sha256']:
            deny('STALE_SOURCE_BINDING',409)
        with controller.conn() as db:
            db.execute('BEGIN IMMEDIATE')
            controller._binding(db,task,p[0],p[1]);task_anchor(db,task,req.anchor_id)
            checked_anchor(req.anchor_id)
            if controller._phase(db,task) not in ('PRE_AI','HUMAN_DE_NOVO'):deny('SOURCE_BINDINGS_FROZEN',409)
            draft=db.execute('SELECT revision,payload FROM drafts WHERE task=?',(task,)).fetchone()
            if not draft or draft['revision']!=req.expected_draft_revision:
                deny('STALE_DRAFT_REVISION',409)
            statement=item_text(json.loads(draft['payload']),req.field,req.item_index)
            if hashlib.sha256(statement.encode('utf-8')).hexdigest()!=req.item_sha256:
                deny('JUDGMENT_ITEM_CHANGED',409)
            import datetime
            db.execute('INSERT OR IGNORE INTO source_bindings VALUES(?,?,?,?,?,?,?)',
                       (task,req.anchor_id,req.field,p[0],doc['revision'],doc['source_pdf_sha256'],
                        datetime.datetime.now(datetime.timezone.utc).isoformat()))
            db.execute('INSERT OR IGNORE INTO source_item_bindings VALUES(?,?,?,?,?,?,?,?,?,?)',
                       (task,req.anchor_id,req.field,req.item_index,req.item_sha256,draft['revision'],
                        p[0],doc['revision'],doc['source_pdf_sha256'],datetime.datetime.now(datetime.timezone.utc).isoformat()))
            controller._log(db,task,'SOURCE_ANCHOR_ITEM_BOUND',p[0],
                            {'field':req.field,'item_index':req.item_index,
                             'item_sha256':req.item_sha256,'anchor_id':req.anchor_id,
                             'draft_revision':req.expected_draft_revision})
        return {'anchor_id':req.anchor_id,'field':req.field,'item_index':req.item_index,
                'item_sha256':req.item_sha256,'draft_revision':req.expected_draft_revision,'synthetic':True}

    @app.get('/v1/tasks/{task}/sources/{source_id}/item-bindings')
    def item_bindings(task:str,source_id:str,p=Depends(principal)):
        allowed(task,*p,full=True);exact_source(source_id);pdf_integrity()
        with controller.conn() as db:
            controller._binding(db,task,p[0],p[1])
            draft=db.execute('SELECT payload FROM drafts WHERE task=?',(task,)).fetchone()
            stored=json.loads(draft['payload']) if draft else None
            rows=db.execute('SELECT anchor_id,field,item_index,item_sha256,draft_revision,source_revision,pdf_sha256 '
                            'FROM source_item_bindings WHERE task=? ORDER BY field,item_index,anchor_id',(task,)).fetchall()
            result=[]
            for row in rows:
                entry=dict(row); task_anchor(db,task,entry['anchor_id'])
                checked_anchor(entry['anchor_id'])
                valid=False
                if stored is not None:
                    try:
                        st=item_text(stored,entry['field'],entry['item_index'])
                        valid=hashlib.sha256(st.encode('utf-8')).hexdigest()==entry['item_sha256']
                    except HTTPException:pass
                entry['current_statement_matches']=valid
                result.append(entry)
        return {'items':result,'synthetic':True}

    @app.get('/v1/tasks/{task}/sources/{source_id}/bindings')
    def bindings(task:str,source_id:str,p=Depends(principal)):
        allowed(task,*p,full=True);exact_source(source_id);pdf_integrity()
        with controller.conn() as db:
            rows=db.execute('SELECT anchor_id,field,document_revision,pdf_sha256 FROM source_bindings WHERE task=? ORDER BY field,anchor_id',(task,)).fetchall()
        return {'items':[dict(row) for row in rows],'synthetic':True}

    @app.get('/v1/tasks/{task}/sources/{source_id}/export')
    def export(task:str,source_id:str,p=Depends(principal)):
        allowed(task,*p,full=True);exact_source(source_id);pdf_integrity()
        with controller.conn() as db:
            own=db.execute('SELECT anchor_id,field,document_revision,pdf_sha256 FROM source_bindings WHERE task=?',(task,)).fetchall()
        return {'provenance':'SYNTHETIC_ONLY_NOT_SCIENTIFIC_OUTPUT',
                'task_id':task,'source_revision':doc['revision'], 'source_pdf_sha256':doc['source_pdf_sha256'],
                'source':safe_doc(), 'source_bindings':[dict(row) for row in own]}

    @app.get('/v1/tasks/{task}/sources/{source_id}/candidate-spans')
    def candidate_spans(task:str,source_id:str,p=Depends(principal)):
        # R1 never receives full source or raw PDF: only explicitly attached verified spans.
        allowed(task,*p,full=False);exact_source(source_id)
        pdf=pdf_integrity()
        with controller.conn() as db:
            db.execute('BEGIN IMMEDIATE');controller._binding(db,task,p[0],p[1])
            if controller._phase(db,task)!='EXPERT_VERIFY':deny('SOURCE_NOT_IN_TASK_PROJECTION',404)
            c=controller._candidate(db,task)
            if not c:deny('SOURCE_NOT_IN_TASK_PROJECTION',404)
            selected=[]
            for candidate in json.loads(c['payload']):
                for item in candidate['source_spans']:
                    if item['source_ref'] != SOURCE_ID: continue
                    try: match=locate_pdf_quote(pdf,item['quote'],doc['source_pdf_sha256'])
                    except LocatorError:deny('CANDIDATE_SPAN_NOT_VERIFIABLE',409)
                    selected.append({'candidate_ref':candidate['candidate_ref'],
                                     'quote':item['quote'],'page':match['page'],
                                     'bbox':match['rects'],'source_id':SOURCE_ID})
            if not selected:deny('SOURCE_NOT_IN_TASK_PROJECTION',404)
            controller._expose(db,task,p[0],c) # durable exposure log precedes bytes
        return {'candidate_spans':selected,'synthetic':True,'no_full_pdf':True}
