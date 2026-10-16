"""WB-P2 Source Studio: isolated, persistent *synthetic-only* scientific source workflow.

Original EA, TPA, Gold, source text, task grants and NDS are not modified.
Identity/rights/manual QA are separately evidenced. It never qualifies real
source copyright or exposes real expert data. All input is synthetic fixture
text, with size/payload/type limits.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import sqlite3
import threading
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

from fastapi import HTTPException

IDENT=re.compile(r"^P2-SYN-[A-Z0-9-]{3,36}$")
REV=re.compile(r"^[A-Za-z0-9._-]{1,32}$")
PROJECT=re.compile(r"^PRJ-SYN-[A-Z0-9-]{3,40}$")
BATCH=re.compile(r"^BATCH-SYN-[A-Z0-9-]{3,40}$")
TYPES={"RANDOMIZED_TRIAL","OBSERVATIONAL_STUDY","SYSTEMATIC_REVIEW_META",
       "GUIDELINE","CONSENSUS","NARRATIVE_REVIEW","CORRECTION_RETRACTION"}
FORMATS={"MARKDOWN","JATS_XML","HTML","PDF_HANDOFF"}
RIGHTS=("INTERNAL_SOURCE_REVIEW","MACHINE_PROCESSING","RETAIN_ORIGINAL")
CODES={"REGISTERED","RIGHTS_HOLD","RIGHTS_ACCEPTED","CONVERSION_COMPLETE",
       "QA_PENDING","QA_HOLD","QA_ACCEPTED","PACKAGE_FROZEN"}


def encoded(obj): return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
def sha(obj): return hashlib.sha256(obj if isinstance(obj,bytes) else encoded(obj)).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
def error(code,status=409): raise HTTPException(status_code=status,detail={"code":code})

def parsedate(text):
    try:
        d=datetime.fromisoformat(text.replace("Z","+00:00"))
        if d.tzinfo is None:raise ValueError
        return d.astimezone(timezone.utc)
    except (AttributeError,ValueError,TypeError):error("INVALID_OFFSET_DATE",422)

def utflen(text):return len(text.encode("utf-16-le"))//2
def utf16(text,start,end):
    raw=text.encode("utf-16-le")
    if not (type(start)==int and type(end)==int and 0<=start<end<=len(raw)//2):
        error("INVALID_ANCHOR_RANGE",422)
    try:return raw[start*2:end*2].decode("utf-16-le")
    except UnicodeDecodeError:error("INVALID_UTF16_BOUNDARY",422)

class SafeHTML(HTMLParser):
    """Never execute or retain active HTML. Conservative text-only extraction."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.frames=[];self.units=[];self.buf=[];self.skip=0;self.current="PARAGRAPH"
    def handle_starttag(self,tag,attrs):
        tag=tag.lower()
        if tag in ("script","style","iframe","object","svg","form","template"):
            self.skip+=1;return
        if self.skip:return
        if tag in ("h1","h2","h3","h4","h5","h6","p","li","td","th","caption","figcaption","blockquote","section"):
            self.flush()
            self.current=("HEADING" if tag.startswith("h") and len(tag)==2 else
              "TABLE_CELL" if tag in ("td","th") else
              "CAPTION" if tag in ("caption","figcaption") else "PARAGRAPH")
    def handle_endtag(self,tag):
        if tag.lower() in ("script","style","iframe","object","svg","form","template"):
            self.skip=max(0,self.skip-1);return
        if not self.skip and tag.lower() in ("p","li","td","th","caption","figcaption","h1","h2","h3","h4","h5","h6"):
            self.flush()
    def handle_data(self,data):
        if not self.skip:self.buf.append(data)
    def flush(self):
        text=" ".join("".join(self.buf).split())
        if text:self.units.append({"kind":self.current,"text":text})
        self.buf=[];self.current="PARAGRAPH"
    def close(self):
        super().close();self.flush()

def structure(fmt,raw,payload=None):
    if fmt=="PDF_HANDOFF":
        if not isinstance(payload,dict) or payload.get("adapter")!="EXTERNAL_MINERU" or not isinstance(payload.get("units"),list):
            error("EXTERNAL_PDF_ADAPTER_REQUIRED",422)
        units=[]
        for unit in payload["units"]:
            if not isinstance(unit,dict) or unit.get("kind") not in ("PARAGRAPH","HEADING","TABLE_CELL","CAPTION","FOOTNOTE"):
                error("INVALID_EXTERNAL_UNIT",422)
            value=unit.get("text")
            if not isinstance(value,str) or not value.strip() or len(value)>10000:
                error("INVALID_EXTERNAL_UNIT",422)
            units.append({"kind":unit["kind"],"text":value.strip(),"page_hint":unit.get("page_hint")})
        parser="EXTERNAL_MINERU_UNVERIFIED"
    elif fmt=="MARKDOWN":
        units=[];paragraph=[]
        def flush():
            if paragraph:
                value=" ".join(paragraph).strip()
                if value:units.append({"kind":"PARAGRAPH","text":value})
                paragraph.clear()
        for line in raw.splitlines():
            v=line.strip()
            if not v:flush();continue
            if v.startswith("#"):flush();units.append({"kind":"HEADING","text":v.lstrip("# ").strip()});continue
            if v.startswith("|"):flush()
            # Keep every cell separate; never join numerical table cells.
            if v.startswith("|"):
                for cell in v.strip("|").split("|"):
                    if cell.strip() and not re.fullmatch(r"[-: ]+",cell):
                        units.append({"kind":"TABLE_CELL","text":cell.strip()})
            elif v.startswith("- ") or v.startswith("* "):flush();units.append({"kind":"PARAGRAPH","text":v[2:].strip()})
            else:paragraph.append(v)
        flush();parser="MARKDOWN_DETERMINISTIC_V0.1"
    elif fmt=="HTML":
        if re.search(r"<!DOCTYPE|<!ENTITY",raw,re.I):error("ACTIVE_MARKUP_REJECTED",422)
        p=SafeHTML()
        try:p.feed(raw);p.close()
        except (ValueError,AssertionError):error("HTML_PARSE_FAILED",422)
        units=p.units;parser="HTML_TEXT_ONLY_V0.1"
    else:
        if re.search(r"<!DOCTYPE|<!ENTITY",raw,re.I):error("XML_DTD_ENTITY_FORBIDDEN",422)
        try:root=ElementTree.fromstring(raw)
        except ElementTree.ParseError:error("XML_PARSE_FAILED",422)
        units=[]
        for node in root.iter():
            tag=node.tag.split("}")[-1].lower() if isinstance(node.tag,str) else ""
            if tag in ("p","title","article-title","td","th","caption","label","fn"):
                value=" ".join("".join(node.itertext()).split())
                if value:units.append({"kind":"HEADING" if tag in ("title","article-title") else
                     "TABLE_CELL" if tag in ("td","th") else
                     "FOOTNOTE" if tag=="fn" else
                     "CAPTION" if tag in ("label","caption") else "PARAGRAPH","text":value})
        parser="JATS_XML_DETERMINISTIC_V0.1"
    if not (1<=len(units)<=1000):error("EMPTY_OR_OVERSIZED_STRUCTURE",422)
    canonical=[]
    for i,u in enumerate(units):
        if len(u["text"])>10000:error("UNIT_TOO_LONG",422)
        canonical.append({"unit_id":"u"+str(i+1).zfill(4),"kind":u["kind"],
          "text":u["text"],"page_hint":u.get("page_hint"),"pdf_locator_status":"PAGE_HINT_ONLY" if u.get("page_hint") else "UNRESOLVED",
          "utf16_length":utflen(u["text"]),"unit_text_sha256":sha(u["text"].encode("utf-8"))})
    return canonical,parser


class SourceStudio:
    """Append-only evidence/QA decisions; mutable source status is only a projection."""
    def __init__(self,path:Path,projects=None):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock();self.projects=projects
        with self.connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS p2_sources(
                source_id TEXT,revision_id TEXT,metadata TEXT NOT NULL,raw_sha TEXT NOT NULL,
                raw_format TEXT NOT NULL,status TEXT NOT NULL,created_by TEXT NOT NULL,
                PRIMARY KEY(source_id,revision_id));
            CREATE TABLE IF NOT EXISTS p2_artifacts(
                raw_sha TEXT PRIMARY KEY,raw_content TEXT NOT NULL,raw_format TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS p2_rights(
                source_id TEXT,revision_id TEXT,decision TEXT NOT NULL,actor TEXT NOT NULL,body TEXT NOT NULL,
                PRIMARY KEY(source_id,revision_id));
            CREATE TABLE IF NOT EXISTS p2_documents(
                source_id TEXT,revision_id TEXT,run_id TEXT NOT NULL,doc TEXT NOT NULL,doc_sha TEXT NOT NULL,
                PRIMARY KEY(source_id,revision_id));
            CREATE TABLE IF NOT EXISTS p2_reviews(
                source_id TEXT,revision_id TEXT,unit_id TEXT,actor TEXT NOT NULL,record TEXT NOT NULL,
                PRIMARY KEY(source_id,revision_id,unit_id));
            CREATE TABLE IF NOT EXISTS p2_packages(
                source_id TEXT,revision_id TEXT,package_sha TEXT NOT NULL,record TEXT NOT NULL,
                PRIMARY KEY(source_id,revision_id));
            CREATE TABLE IF NOT EXISTS p2_translations(
                source_id TEXT,revision_id TEXT,unit_id TEXT,record TEXT NOT NULL,
                PRIMARY KEY(source_id,revision_id,unit_id));
            CREATE TABLE IF NOT EXISTS p2_usage(
                source_id TEXT,revision_id TEXT,project_id TEXT,batch_id TEXT,actor TEXT NOT NULL,
                PRIMARY KEY(source_id,revision_id,project_id,batch_id));
            CREATE TABLE IF NOT EXISTS p2_events(
                seq INTEGER PRIMARY KEY AUTOINCREMENT,source_key TEXT NOT NULL,event TEXT NOT NULL,
                actor TEXT NOT NULL,detail TEXT NOT NULL,prev_hash TEXT NOT NULL,entry_hash TEXT NOT NULL,
                at TEXT NOT NULL);
            """)
            for table in ("p2_artifacts","p2_rights","p2_documents","p2_reviews","p2_packages","p2_translations","p2_usage","p2_events"):
                for action in ("UPDATE","DELETE"):
                    db.execute(f"""CREATE TRIGGER IF NOT EXISTS p2_lock_{table}_{action.lower()}
                    BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT,'IMMUTABLE_P2_EVIDENCE'); END""")
        self.path.chmod(0o600)

    def connect(self):
        c=sqlite3.connect(str(self.path),timeout=10)
        c.row_factory=sqlite3.Row;c.execute("PRAGMA foreign_keys=ON");c.execute("PRAGMA busy_timeout=10000")
        return c
    @staticmethod
    def auth(role,allowed):
        if role not in allowed:error("P2_ROLE_FORBIDDEN",403)

    @staticmethod
    def key(sid,rev):return sid+":"+rev
    def row(self,db,sid,rev):
        r=db.execute("SELECT * FROM p2_sources WHERE source_id=? AND revision_id=?",(sid,rev)).fetchone()
        if not r:error("P2_SOURCE_NOT_FOUND",404)
        return r
    def event(self,db,key,actor,event,details):
        last=db.execute("SELECT entry_hash FROM p2_events ORDER BY seq DESC LIMIT 1").fetchone()
        previous=last[0] if last else "GENESIS"
        record={"source_key":key,"event":event,"actor":actor,"detail":details,
                "prev_hash":previous,"at":now()}
        entry=sha(record)
        db.execute("INSERT INTO p2_events(source_key,event,actor,detail,prev_hash,entry_hash,at) VALUES(?,?,?,?,?,?,?)",
                   (key,event,actor,encoded(details).decode(),previous,entry,record["at"]))
        return entry
    def projection(self,db,row):
        meta=json.loads(row["metadata"])
        rec={**meta,"source_id":row["source_id"],"revision_id":row["revision_id"],
             "raw_artifact_sha256":row["raw_sha"],"raw_format":row["raw_format"],
             "status":row["status"],"source_original_text_exposed":False,
             "scientific_capture":False,"gold_qualification":"NOT_ELIGIBLE",
             "expert_exposure_authorized":False}
        rights=db.execute("SELECT decision FROM p2_rights WHERE source_id=? AND revision_id=?",
                          (row["source_id"],row["revision_id"])).fetchone()
        rec["rights_status"]=rights["decision"] if rights else "PENDING_INDEPENDENT_REVIEW"
        q=db.execute("SELECT COUNT(*) FROM p2_reviews WHERE source_id=? AND revision_id=?",
                     (row["source_id"],row["revision_id"])).fetchone()[0]
        d=db.execute("SELECT doc,doc_sha,run_id FROM p2_documents WHERE source_id=? AND revision_id=?",
                     (row["source_id"],row["revision_id"])).fetchone()
        rec.update({"reviewed_units":q,"document_sha256":d["doc_sha"] if d else None,
                    "conversion_run_id":d["run_id"] if d else None,
                    "unit_count":len(json.loads(d["doc"])["units"]) if d else 0})
        p=db.execute("SELECT package_sha FROM p2_packages WHERE source_id=? AND revision_id=?",
                     (row["source_id"],row["revision_id"])).fetchone()
        rec["package_sha256"]=p[0] if p else None
        return rec

    def register(self,role,actor,body):
        self.auth(role,("producer",))
        sid=body.get("source_id");rev=body.get("revision_id")
        if not isinstance(sid,str) or not IDENT.fullmatch(sid) or not isinstance(rev,str) or not REV.fullmatch(rev):
            error("INVALID_P2_SOURCE_VERSION",422)
        title=body.get("title");kind=body.get("source_type");fmt=body.get("raw_format");raw=body.get("raw_content")
        if not isinstance(title,str) or not 5<=len(title.strip())<=240 or kind not in TYPES or fmt not in FORMATS:
            error("INVALID_SOURCE_IDENTITY",422)
        if body.get("rights_assertion")!="SYNTHETIC_FIXTURE":
            error("REAL_SOURCE_INTAKE_DISABLED",403)
        if not isinstance(raw,str) or not raw.strip() or len(raw.encode("utf-8"))>200_000:
            error("INVALID_SOURCE_PAYLOAD",422)
        available=parsedate(body.get("available_at"));fetched=parsedate(body.get("fetched_at"))
        if available>fetched:error("FUTURE_SOURCE_AT_FETCH",422)
        method=body.get("identifier_kind")
        if method not in ("DEMO_DOI","DEMO_PMID","SYNTHETIC_ID"):error("INVALID_SOURCE_IDENTITY",422)
        ref=body.get("identifier")
        if not isinstance(ref,str) or not 3<=len(ref)<=120:error("INVALID_SOURCE_IDENTITY",422)
        family=body.get("source_family_refs",[])
        if not isinstance(family,list) or len(family)>1 or any(not isinstance(x,str) for x in family):
            error("INVALID_SOURCE_FAMILY_REFS",422)
        metadata={"title":title.strip(),"source_type":kind,"identifier_kind":method,
            "identifier":ref,"available_at":available.isoformat(),"fetched_at":fetched.isoformat(),
            "rights_status":"PENDING_INDEPENDENT_REVIEW","artifact_kind":"SYNTHETIC_FIXTURE",
            "source_family_refs":family,
            "correction_status":"UNVERIFIED_DEMO","created_at":now()}
        rawsha=sha(raw.encode("utf-8"))
        with self.lock,self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            old=db.execute("SELECT 1 FROM p2_sources WHERE source_id=? AND revision_id=?",(sid,rev)).fetchone()
            if old:error("SOURCE_VERSION_ALREADY_REGISTERED")
            if family:
                parent_id,parent_rev=(family[0].split(":",1)+[""])[:2]
                if parent_id!=sid or not parent_rev or parent_rev==rev:
                    error("REVISION_LINEAGE_MISMATCH")
                if (re.fullmatch(r"r[0-9]+",rev) and re.fullmatch(r"r[0-9]+",parent_rev) and
                        int(rev[1:])!=int(parent_rev[1:])+1):
                    error("REVISION_NOT_SEQUENTIAL")
                parent=db.execute(
                    "SELECT status,raw_sha FROM p2_sources WHERE source_id=? AND revision_id=?",
                    (parent_id,parent_rev)).fetchone()
                if not parent:error("PARENT_SOURCE_VERSION_NOT_FOUND",404)
                rights=db.execute(
                    "SELECT decision FROM p2_rights WHERE source_id=? AND revision_id=?",
                    (parent_id,parent_rev)).fetchone()
                blocked=parent["status"]=="QA_HOLD" or (
                    parent["status"]=="RIGHTS_HOLD" and rights is not None and rights["decision"]=="HOLD")
                if not blocked:error("PARENT_REWORK_GATE_NOT_SATISFIED")
                if parent["raw_sha"]==rawsha:error("REWORK_REQUIRES_NEW_RAW_ARTIFACT")
            existing_artifact=db.execute("SELECT raw_format FROM p2_artifacts WHERE raw_sha=?",(rawsha,)).fetchone()
            if existing_artifact and existing_artifact["raw_format"]!=fmt:
                error("RAW_ARTIFACT_FORMAT_CONFLICT")
            db.execute("INSERT OR IGNORE INTO p2_artifacts VALUES(?,?,?)",(rawsha,raw,fmt))
            db.execute("INSERT INTO p2_sources VALUES(?,?,?,?,?,?,?)",
                       (sid,rev,encoded(metadata).decode(),rawsha,fmt,"RIGHTS_HOLD",actor))
            ev=self.event(db,self.key(sid,rev),actor,"SOURCE_REGISTERED",{"raw_sha256":rawsha,"synthetic":True})
            return {"source":self.projection(db,self.row(db,sid,rev)),"event_hash":ev}

    def list(self,role,limit=25,offset=0,q="",status="",project_id="",batch_id=""):
        self.auth(role,("producer","manager","curator","auditor"))
        if type(limit)!=int or not 1<=limit<=100 or type(offset)!=int or not 0<=offset<=100000:
            error("INVALID_PAGINATION",422)
        if status and status not in CODES:error("INVALID_STATUS_FILTER",422)
        if len(q)>150:error("INVALID_SEARCH",422)
        with self.connect() as db:
            rows=db.execute("SELECT * FROM p2_sources ORDER BY source_id,revision_id").fetchall()
            visible=[self.projection(db,r) for r in rows]
            if q:
                low=q.lower();visible=[r for r in visible if low in (r["title"]+" "+r["source_id"]+" "+r["identifier"]).lower()]
            if status:visible=[r for r in visible if r["status"]==status]
            if project_id or batch_id:
                related=db.execute("SELECT source_id,revision_id FROM p2_usage WHERE (?='' OR project_id=?) AND (?='' OR batch_id=?)",
                                   (project_id,project_id,batch_id,batch_id)).fetchall()
                allowed={(r["source_id"],r["revision_id"]) for r in related}
                visible=[r for r in visible if (r["source_id"],r["revision_id"]) in allowed]
            return {"sources":visible[offset:offset+limit],"total":len(visible),"limit":limit,"offset":offset,
                    "true_source_qualification":False,"expert_authorization":False}

    def detail(self,role,sid,rev):
        self.auth(role,("manager","producer","curator","auditor"))
        with self.connect() as db:
            row=self.row(db,sid,rev);record=self.projection(db,row)
            rights=db.execute("SELECT decision,body FROM p2_rights WHERE source_id=? AND revision_id=?",(sid,rev)).fetchone()
            record["rights_decision"]=rights["decision"] if rights else "PENDING"
            p=db.execute("SELECT record FROM p2_packages WHERE source_id=? AND revision_id=?",(sid,rev)).fetchone()
            record["package"]=json.loads(p["record"]) if p else None
            record["scope_refs"]=[dict(x) for x in db.execute(
                "SELECT project_id,batch_id FROM p2_usage WHERE source_id=? AND revision_id=?",(sid,rev)).fetchall()]
            return record

    def rights(self,role,actor,sid,rev,body):
        self.auth(role,("auditor",))
        decision=body.get("decision");uses=body.get("uses");evidence=body.get("evidence_ref")
        if decision not in ("APPROVE_SYNTHETIC","HOLD") or not isinstance(uses,list) or not set(uses)==set(RIGHTS):
            error("INVALID_RIGHTS_DECISION",422)
        if not isinstance(evidence,str) or not evidence.startswith("SYN-") or len(evidence)>160:
            error("RIGHTS_EVIDENCE_REQUIRED",422)
        with self.lock,self.connect() as db:
            db.execute("BEGIN IMMEDIATE");row=self.row(db,sid,rev)
            if row["status"]!="RIGHTS_HOLD":error("RIGHTS_REVIEW_STATE_INVALID")
            if row["created_by"]==actor:error("SEPARATION_OF_DUTIES_REQUIRED",403)
            new_state="RIGHTS_ACCEPTED" if decision=="APPROVE_SYNTHETIC" else "RIGHTS_HOLD"
            if db.execute("SELECT 1 FROM p2_rights WHERE source_id=? AND revision_id=?",(sid,rev)).fetchone():
                error("IMMUTABLE_RIGHTS_DECISION_EXISTS")
            evidence_body={"decision":decision,"uses":uses,"evidence_ref":evidence,
                           "synthetic_only":True,"real_rights_qualified":False,"approved_at":now()}
            db.execute("INSERT INTO p2_rights VALUES(?,?,?,?,?)",(sid,rev,decision,actor,encoded(evidence_body).decode()))
            db.execute("UPDATE p2_sources SET status=? WHERE source_id=? AND revision_id=?",(new_state,sid,rev))
            ev=self.event(db,self.key(sid,rev),actor,"RIGHTS_RECORDED",evidence_body)
            return {"status":new_state,"rights":evidence_body,"event_hash":ev}

    def convert(self,role,actor,sid,rev,body):
        self.auth(role,("producer",))
        with self.lock,self.connect() as db:
            db.execute("BEGIN IMMEDIATE");row=self.row(db,sid,rev)
            if row["status"]!="RIGHTS_ACCEPTED":error("SOURCE_NOT_APPROVED_FOR_CONVERSION")
            if db.execute("SELECT 1 FROM p2_documents WHERE source_id=? AND revision_id=?",(sid,rev)).fetchone():
                error("IMMUTABLE_CONVERSION_EXISTS")
            rawrow=db.execute("SELECT raw_content,raw_format FROM p2_artifacts WHERE raw_sha=?",(row["raw_sha"],)).fetchone()
            if rawrow is None or sha(rawrow["raw_content"].encode("utf-8"))!=row["raw_sha"]:
                error("ORIGINAL_ARTIFACT_DRIFT")
            units,parser=structure(row["raw_format"],rawrow["raw_content"],body.get("external_payload"))
            doc={"contract":"P2_STRUCTURED_DOCUMENT_V0.1","source_id":sid,"revision_id":rev,
                 "raw_artifact_sha256":row["raw_sha"],"units":units,"parser":parser,
                 "scientific_capture":False,"original_authority_preserved":True}
            doc_sha=sha(doc);run="P2-RUN-"+doc_sha[:18].upper()
            db.execute("INSERT INTO p2_documents VALUES(?,?,?,?,?)",(sid,rev,run,encoded(doc).decode(),doc_sha))
            db.execute("UPDATE p2_sources SET status='QA_PENDING' WHERE source_id=? AND revision_id=?",(sid,rev))
            ev=self.event(db,self.key(sid,rev),actor,"CONVERSION_FROZEN",{"run_id":run,"doc_sha":doc_sha,"parser":parser,"units":len(units)})
            return {"run_id":run,"document_sha256":doc_sha,"status":"QA_PENDING","unit_count":len(units),
                    "parser":parser,"raw_artifact_sha256":row["raw_sha"],"event_hash":ev}

    def document(self,role,sid,rev):
        self.auth(role,("curator",))
        with self.connect() as db:
            row=self.row(db,sid,rev)
            result=db.execute("SELECT doc,doc_sha,run_id FROM p2_documents WHERE source_id=? AND revision_id=?",(sid,rev)).fetchone()
            if not result:error("DOCUMENT_NOT_CONVERTED",404)
            doc=json.loads(result["doc"]);return {"document":doc,"document_sha256":result["doc_sha"],
                                                      "run_id":result["run_id"],"synthetic_only":True}

    def original(self,role,sid,rev):
        """Read-only original fixture bytes for independent human source QA."""
        self.auth(role,("curator",))
        with self.connect() as db:
            row=self.row(db,sid,rev)
            if row["status"]=="RIGHTS_HOLD":error("SOURCE_RIGHTS_NOT_ACCEPTED")
            original=db.execute("SELECT raw_content,raw_format FROM p2_artifacts WHERE raw_sha=?",
                                (row["raw_sha"],)).fetchone()
            if not original or sha(original["raw_content"].encode("utf-8"))!=row["raw_sha"]:
                error("ORIGINAL_ARTIFACT_DRIFT")
            return {"source_id":sid,"revision_id":rev,"raw_content":original["raw_content"],
                    "raw_format":original["raw_format"],"raw_artifact_sha256":row["raw_sha"],
                    "synthetic_only":True,"original_authority_preserved":True}

    def reviews(self,role,sid,rev):
        self.auth(role,("curator",))
        with self.connect() as db:
            self.row(db,sid,rev)
            rows=db.execute("SELECT unit_id,actor,record FROM p2_reviews WHERE source_id=? AND revision_id=?",
                            (sid,rev)).fetchall()
            # Only independently authenticated Curator receives span metadata.
            # Original text is never echoed by the review-list endpoint;
            # reconstruction/highlighting uses the separate authorized Document IR.
            records=[json.loads(r["record"]) for r in rows]
            return {"source_id":sid,"revision_id":rev,
                    "reviews":[{"unit_id":r["unit_id"],"decision":v["decision"],
                                "reviewer":r["actor"],"start_utf16":v["start_utf16"],
                                "end_utf16":v["end_utf16"],
                                "source_quote_sha256":v["source_quote_sha256"],
                                "pdf_locator_status":v["pdf_locator_status"],
                                "canonical_document_sha256":v["source_ref"]["canonical_document_sha256"]}
                               for r,v in zip(rows,records)],
                    "total":len(rows),"original_text_exposed":False}

    def review(self,role,actor,sid,rev,body):
        self.auth(role,("curator",))
        unitid=body.get("unit_id");decision=body.get("decision")
        if decision not in ("ACCEPT","REJECT") or not isinstance(unitid,str):error("INVALID_QA_DECISION",422)
        with self.lock,self.connect() as db:
            db.execute("BEGIN IMMEDIATE");row=self.row(db,sid,rev)
            if row["status"] not in ("QA_PENDING","QA_HOLD"):error("QA_STATE_INVALID")
            if row["raw_format"]=="PDF_HANDOFF" and decision=="ACCEPT":
                error("PDF_ORIGINAL_VIEWER_REQUIRED")
            if row["created_by"]==actor:error("SEPARATION_OF_DUTIES_REQUIRED",403)
            d=db.execute("SELECT doc,doc_sha FROM p2_documents WHERE source_id=? AND revision_id=?",(sid,rev)).fetchone()
            if not d:error("DOCUMENT_NOT_CONVERTED")
            doc=json.loads(d["doc"]);u=next((x for x in doc["units"] if x["unit_id"]==unitid),None)
            if not u:error("UNIT_NOT_FOUND",404)
            if db.execute("SELECT 1 FROM p2_reviews WHERE source_id=? AND revision_id=? AND unit_id=?",(sid,rev,unitid)).fetchone():
                error("IMMUTABLE_QA_REVIEW_EXISTS")
            start=body.get("start_utf16");end=body.get("end_utf16");quote=body.get("source_quote")
            actual=utf16(u["text"],start,end)
            if not isinstance(quote,str) or actual!=quote or body.get("source_quote_sha256")!=sha(quote.encode("utf-8")):
                error("SOURCE_SPAN_MISMATCH")
            pdf_state=body.get("pdf_locator_status","UNRESOLVED")
            if pdf_state not in ("PAGE_HINT_ONLY","UNRESOLVED"):
                error("PDF_BBOX_NOT_VERIFIED_BY_THIS_RUNTIME")
            findings=body.get("findings",{})
            if not isinstance(findings,dict) or len(encoded(findings))>3000:error("INVALID_QA_FINDINGS",422)
            record={"unit_id":unitid,"decision":decision,"actor":actor,
                "source_ref":{"source_id":sid,"revision_id":rev,"canonical_document_sha256":d["doc_sha"]},
                "start_utf16":start,"end_utf16":end,"source_quote":quote,
                "source_quote_sha256":sha(quote.encode("utf-8")),"pdf_locator_status":pdf_state,
                "findings":findings,"time":now(),"claim_of_real_qualification":False}
            db.execute("INSERT INTO p2_reviews VALUES(?,?,?,?,?)",(sid,rev,unitid,actor,encoded(record).decode()))
            if decision=="REJECT":
                db.execute("UPDATE p2_sources SET status='QA_HOLD' WHERE source_id=? AND revision_id=?",(sid,rev))
            ev=self.event(db,self.key(sid,rev),actor,"UNIT_QA_RECORDED",{"unit_id":unitid,"decision":decision,"quote_sha":record["source_quote_sha256"]})
            return {"review":record,"event_hash":ev}

    def rework_handoff(self,role,sid,rev):
        """Least-privilege immutable QA-rejection handoff.

        Producer may see Unit ID and controlled reason category only, NEVER
        source_quote, raw document or untrusted free-text Curator findings.
        This is a derived view of immutable reviews; no mutable issue table.
        """
        self.auth(role,("producer","curator"))
        categories={"STRUCTURE_GAP","NUMERIC_MISMATCH","ANCHOR_MISMATCH",
                    "OMITTED_CONTENT","TRANSLATION_DISCREPANCY","OTHER"}
        with self.connect() as db:
            row=self.row(db,sid,rev)
            items=db.execute(
                "SELECT unit_id,record FROM p2_reviews WHERE source_id=? AND revision_id=? ORDER BY unit_id",
                (sid,rev)).fetchall()
            issues=[]
            for item in items:
                record=json.loads(item["record"])
                if record["decision"]!="REJECT":continue
                findings=record.get("findings",{})
                code=findings.get("rework_reason_code","OTHER")
                if not isinstance(code,str) or code not in categories:code="OTHER"
                issues.append({"unit_id":item["unit_id"],"reason_code":code,
                    # Deterministic ID derives only from non-sensitive immutable keys,
                    # never a digest of private quote or free-text Curator findings.
                    "issue_ref":sha({"scope":"P2_SYNTHETIC_REJECT_HANDOFF_V1",
                                     "source_id":sid,"revision_id":rev,
                                     "unit_id":item["unit_id"],"decision":"REJECT"}),
                    "resolution":"NEW_REVISION_REQUIRED","immutable":True})
            return {"source_id":sid,"revision_id":rev,"source_status":row["status"],
                "issues":issues,"count":len(issues),"synthetic_only":True,
                "original_text_exposed":False,"findings_text_exposed":False,
                "gold_qualification":"NOT_ELIGIBLE","expert_exposure_authorized":False}

    def translations(self,role,sid,rev):
        """Auxiliary only. No translated quote can replace the original anchor."""
        self.auth(role,("curator",))
        with self.connect() as db:
            self.row(db,sid,rev)
            rows=db.execute("SELECT unit_id,record FROM p2_translations WHERE source_id=? AND revision_id=?",
                            (sid,rev)).fetchall()
            return {"translations":[json.loads(r["record"]) for r in rows],
                    "count":len(rows),"authority":"AUXILIARY_ONLY","scientific_capture":False}

    def save_translation(self,role,actor,sid,rev,body):
        self.auth(role,("curator",))
        unitid=body.get("unit_id");text=body.get("translation_zh")
        ref=body.get("provenance_ref")
        if not isinstance(unitid,str) or not isinstance(text,str) or not (2<=len(text)<=10000):
            error("INVALID_AUXILIARY_TRANSLATION",422)
        if not isinstance(ref,str) or not ref.startswith("SYN-HUMAN-") or len(ref)>150:
            error("TRANSLATION_PROVENANCE_REQUIRED",422)
        with self.lock,self.connect() as db:
            db.execute("BEGIN IMMEDIATE");row=self.row(db,sid,rev)
            if row["status"] not in ("QA_PENDING","QA_HOLD","PACKAGE_FROZEN"):
                error("TRANSLATION_NOT_ALLOWED_BEFORE_CONVERSION")
            doc=db.execute("SELECT doc,doc_sha FROM p2_documents WHERE source_id=? AND revision_id=?",
                           (sid,rev)).fetchone()
            if not doc:error("DOCUMENT_NOT_CONVERTED",404)
            units=json.loads(doc["doc"])["units"]
            unit=next((x for x in units if x["unit_id"]==unitid),None)
            if not unit:error("UNIT_NOT_FOUND",404)
            if body.get("expected_unit_text_sha256")!=unit["unit_text_sha256"]:
                error("TRANSLATION_SOURCE_DRIFT")
            if db.execute("SELECT 1 FROM p2_translations WHERE source_id=? AND revision_id=? AND unit_id=?",
                          (sid,rev,unitid)).fetchone():error("IMMUTABLE_TRANSLATION_EXISTS")
            record={"unit_id":unitid,"translation_zh":text,"language":"zh-CN",
                    "provenance_ref":ref,"translation_sha256":sha(text.encode("utf-8")),
                    "original_unit_sha256":unit["unit_text_sha256"],
                    "canonical_document_sha256":doc["doc_sha"],"actor":actor,
                    "created_at":now(),"authority":"AUXILIARY_ONLY","human_approved_for_expert":False}
            db.execute("INSERT INTO p2_translations VALUES(?,?,?,?)",(sid,rev,unitid,encoded(record).decode()))
            ev=self.event(db,self.key(sid,rev),actor,"AUXILIARY_TRANSLATION_FROZEN",
                         {"unit_id":unitid,"translation_sha256":record["translation_sha256"]})
            return {"translation":record,"event_hash":ev,"source_original_text_changed":False}

    def freeze(self,role,actor,sid,rev,body):
        self.auth(role,("producer",))
        with self.lock,self.connect() as db:
            db.execute("BEGIN IMMEDIATE");row=self.row(db,sid,rev)
            if row["status"] not in ("QA_PENDING","QA_ACCEPTED"):error("QA_INCOMPLETE_OR_REJECTED")
            rights=db.execute("SELECT decision,body FROM p2_rights WHERE source_id=? AND revision_id=?",(sid,rev)).fetchone()
            if rights is None or rights["decision"]!="APPROVE_SYNTHETIC":error("SOURCE_RIGHTS_NOT_ACCEPTED")
            doc=db.execute("SELECT doc,doc_sha FROM p2_documents WHERE source_id=? AND revision_id=?",(sid,rev)).fetchone()
            if not doc or body.get("expected_document_sha256")!=doc["doc_sha"]:error("SOURCE_DOCUMENT_STALE")
            actual=json.loads(doc["doc"])
            reviews=db.execute("SELECT record FROM p2_reviews WHERE source_id=? AND revision_id=?",(sid,rev)).fetchall()
            if len(reviews)!=len(actual["units"]):error("UNIT_QA_COVERAGE_INCOMPLETE")
            if any(json.loads(x["record"])["decision"]!="ACCEPT" for x in reviews):error("QA_REJECTED_UNIT_REQUIRES_NEW_REVISION")
            if db.execute("SELECT 1 FROM p2_packages WHERE source_id=? AND revision_id=?",(sid,rev)).fetchone():
                error("IMMUTABLE_SOURCE_PACKAGE_EXISTS")
            if sha(encoded(actual))!=doc["doc_sha"]:error("DOCUMENT_DIGEST_DRIFT")
            pkg={"contract":"P2_SYNTHETIC_SOURCE_PACKAGE_V0.1","source_id":sid,"revision_id":rev,
                 "source_artifact_sha256":row["raw_sha"],"canonical_document_sha256":doc["doc_sha"],
                 "unit_count":len(actual["units"]),"qa_coverage":"ALL_UNITS",
                 "rights_record_sha256":sha(json.loads(rights["body"])),
                 "review_set_sha256":sha(sorted((json.loads(r["record"]) for r in reviews),key=lambda x:x["unit_id"])),
                 "synthetic_only":True,"real_source_qualified":False,"gold_qualification":"NOT_ELIGIBLE",
                 "expert_exposure_authorized":False,"frozen_at":now(),"frozen_by":actor}
            package_sha=sha(pkg)
            db.execute("INSERT INTO p2_packages VALUES(?,?,?,?)",(sid,rev,package_sha,encoded(pkg).decode()))
            db.execute("UPDATE p2_sources SET status='PACKAGE_FROZEN' WHERE source_id=? AND revision_id=?",(sid,rev))
            ev=self.event(db,self.key(sid,rev),actor,"SOURCE_PACKAGE_FROZEN",{"package_sha":package_sha})
            return {"package":pkg,"package_sha256":package_sha,"event_hash":ev,"scientific_capture":False}

    def bind_scope(self,role,actor,sid,rev,project,batch):
        self.auth(role,("producer",))
        if not PROJECT.fullmatch(project or "") or not BATCH.fullmatch(batch or ""):
            error("INVALID_PROJECT_BATCH",422)
        with self.lock,self.connect() as db:
            db.execute("BEGIN IMMEDIATE");row=self.row(db,sid,rev)
            if row["status"]!="PACKAGE_FROZEN":error("SOURCE_NOT_FROZEN")
            if self.projects is None:error("PROJECT_REGISTRY_NOT_AVAILABLE")
            with self.projects.tpa.connect() as pdb:
                if not pdb.execute("SELECT 1 FROM tpa_project_registry WHERE project_id=?",(project,)).fetchone():
                    error("PROJECT_NOT_FOUND",404)
                if not pdb.execute("SELECT 1 FROM tpa_operational_batches WHERE batch_id=? AND project_id=?",(batch,project)).fetchone():
                    error("PROJECT_BATCH_MISMATCH",409)
            if db.execute("SELECT 1 FROM p2_usage WHERE source_id=? AND revision_id=? AND project_id=? AND batch_id=?",
                          (sid,rev,project,batch)).fetchone():
                return {"source_id":sid,"revision_id":rev,"project_id":project,"batch_id":batch,"replayed":True,
                        "expert_exposure_authorized":False}
            db.execute("INSERT INTO p2_usage VALUES(?,?,?,?,?)",(sid,rev,project,batch,actor))
            ev=self.event(db,self.key(sid,rev),actor,"SOURCE_SCOPE_BOUND",{"project_id":project,"batch_id":batch,"expert_grant":False})
            return {"source_id":sid,"revision_id":rev,"project_id":project,"batch_id":batch,"event_hash":ev,
                    "expert_exposure_authorized":False,"scientific_capture":False}

    def overview(self,role):
        self.auth(role,("producer","manager","curator","auditor"))
        with self.connect() as db:
            statuses=[r["status"] for r in db.execute("SELECT status FROM p2_sources")]
            return {"total":len(statuses),"rights_hold":statuses.count("RIGHTS_HOLD"),
                    "qa_pending":statuses.count("QA_PENDING")+statuses.count("QA_HOLD"),
                    "packages_frozen":statuses.count("PACKAGE_FROZEN"),
                    "synthetic_only":True,"real_source_qualification":False,
                    "real_expert_authorized":False}

    def audit(self,role):
        self.auth(role,("auditor",))
        with self.connect() as db:
            records=db.execute("SELECT * FROM p2_events ORDER BY seq").fetchall()
            prev="GENESIS"
            for r in records:
                raw={"source_key":r["source_key"],"event":r["event"],"actor":r["actor"],
                     "detail":json.loads(r["detail"]),"prev_hash":r["prev_hash"],"at":r["at"]}
                if r["prev_hash"]!=prev or sha(raw)!=r["entry_hash"]:
                    return {"valid":False,"first_invalid_seq":r["seq"],"events_checked":len(records)}
                prev=r["entry_hash"]
            return {"valid":True,"events_checked":len(records),"last_hash":prev,
                    "science_promotion":False}
