from __future__ import annotations

import json
import shlex
from pathlib import Path
from datetime import datetime

import typer

from .models import IndependentReadout, ParsedDocument, PrefillDraft, RawSnapshot, ReviewDecision
from .acquisition import SnapshotService
from .parsing import parse_document
from .prefill import PrefillService
from .review import ReviewService
from .store import ProductionStore
from .verification import verify_draft
from .jobs import JobQueue
from .worker import run_one
from .release import ReleaseService

app = typer.Typer(help="D0 staging production: version-bound drafts, review and durable jobs; no canonical/Gold promotion.")


def emit(value):
    if hasattr(value,"model_dump"):
        value = value.model_dump(mode="json")
    typer.echo(json.dumps(value,ensure_ascii=False,indent=2))


@app.command("snapshot")
def snapshot_cmd(path: Path, source_id: str, source_version: str, format: str,
                 scope: str, license: str, lane: str="scientific",
                 expected_sha256: str | None=None, db: Path=Path("nutrifoundation.db"),
                 blobs: Path=Path("d0_blobs")):
    """Preserve acquired file bytes; supplied origin is local import, not HTTP proof."""
    store = ProductionStore(db)
    snapshot = SnapshotService(store,blobs).ingest(path.read_bytes(),source_id=source_id,
        source_version=source_version,format=format,content_scope=scope,license=license,lane=lane,
        origin="local_import:"+path.name,expected_sha256=expected_sha256)
    emit(snapshot)


@app.command("fetch-ncbi")
def fetch_ncbi_cmd(identifier: str,database: str,source_id: str,source_version: str,license: str,
                   db: Path=Path("nutrifoundation.db"),blobs: Path=Path("d0_blobs")):
    """Acquire official raw XML; rights and scientific qualification remain separate."""
    from .providers import NCBIRawAdapter
    store=ProductionStore(db)
    emit(NCBIRawAdapter(SnapshotService(store,blobs),JobQueue(store)).fetch(identifier,
        database=database,source_id=source_id,source_version=source_version,license=license))


@app.command("parse")
def parse_cmd(snapshot_id: str, db: Path=Path("nutrifoundation.db")):
    store = ProductionStore(db)
    snapshot = RawSnapshot.model_validate(store.get("snapshot",snapshot_id))
    parsed = parse_document(snapshot,Path(snapshot.blob_path).read_bytes())
    store.put("parsed",parsed.parsed_id,parsed)
    store.depend(parsed.parsed_id,(snapshot_id,))
    emit({"parsed_id":parsed.parsed_id,"anchor_count":len(parsed.anchors)})


@app.command("prepare")
def prepare_cmd(snapshot_id: str, parsed_id: str, authority_sha256: str, extractor_id: str,
                model_version: str, prompt_version: str, coverage: str,
                db: Path=Path("nutrifoundation.db"),budget_tokens: int=16000):
    store = ProductionStore(db)
    task = PrefillService(store).prepare(RawSnapshot.model_validate(store.get("snapshot",snapshot_id)),
        ParsedDocument.model_validate(store.get("parsed",parsed_id)),authority_sha256=authority_sha256,
        extractor_id=extractor_id,model_version=model_version,prompt_version=prompt_version,
        coverage_request=coverage,budget_tokens=budget_tokens)
    emit(task)


@app.command("ingest-draft")
def ingest_cmd(path: Path,db: Path=Path("nutrifoundation.db")):
    emit(PrefillService(ProductionStore(db)).ingest(PrefillDraft.model_validate_json(path.read_text())))


@app.command("verify")
def verify_cmd(draft_id: str, readout: Path | None=None,db: Path=Path("nutrifoundation.db")):
    store = ProductionStore(db)
    draft = PrefillDraft.model_validate(store.get("draft",draft_id))
    independent = IndependentReadout.model_validate_json(readout.read_text()) if readout else None
    if independent:
        store.put("independent_readout",independent.readout_id,independent)
    report = verify_draft(draft,ParsedDocument.model_validate(store.get("parsed",draft.task.parsed_id)),independent)
    store.put("verification",report.report_id,report)
    store.depend(report.report_id,(draft_id,)+((independent.readout_id,) if independent else ()))
    emit(report)


@app.command("export-review")
def export_review_cmd(draft_id: str,reviewer_id: str,out: Path,mode: str="assisted",db: Path=Path("nutrifoundation.db")):
    svc = ReviewService(ProductionStore(db))
    task = svc.create(draft_id,reviewer_id=reviewer_id,mode=mode)
    projection = svc.export(task["review_task_id"])
    out.parent.mkdir(parents=True,exist_ok=True)
    # Package the same raw bytes next to either review view. No answer-bearing
    # machine artifact is copied into a source-only handoff.
    raw = ProductionStore(db).get("snapshot",task["snapshot_id"])
    import hashlib
    content=Path(raw["blob_path"]).read_bytes()
    if hashlib.sha256(content).hexdigest()!=raw["content_sha256"]:
        raise ValueError("Review source integrity failure")
    ext={"JATS_XML":"xml","TEXT":"txt","PDF":"pdf","HTML":"html"}.get(raw["format"],"bin")
    source_path=out.with_suffix('.source.'+ext)
    projection['source_file']=source_path.name
    if out.suffix.lower()=='.zip':
        from zipfile import ZipFile,ZIP_DEFLATED
        from .models import digest
        with ZipFile(out,'w',compression=ZIP_DEFLATED) as archive:
            archive.writestr(source_path.name,content)
            archive.writestr('review.json',json.dumps(projection,ensure_ascii=False,indent=2)+'\n')
            archive.writestr('manifest.json',json.dumps({'mode':mode,'review_task_id':task['review_task_id'],
                'source_sha256':raw['content_sha256'],'review_sha256':digest(projection),
                'allowlist':[source_path.name,'review.json','manifest.json']},indent=2)+'\n')
    elif out.suffix.lower()==".html":
        from .workbench import assisted_html
        out.write_text(assisted_html(projection),encoding="utf-8")
        source_path.write_bytes(content)
    else:
        out.write_text(json.dumps(projection,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        source_path.write_bytes(content)
    emit({"review_task_id":task["review_task_id"],"mode":mode,"output":str(out)})


@app.command("submit-review")
def submit_review_cmd(path: Path,db: Path=Path("nutrifoundation.db")):
    decision = ReviewDecision.model_validate_json(path.read_text())
    emit({"decision_sha256":ReviewService(ProductionStore(db)).submit(decision),"promotion":False})


@app.command("apply-review")
def apply_review_cmd(decision_id: str,new_draft_id: str,db: Path=Path("nutrifoundation.db")):
    emit(ReviewService(ProductionStore(db)).revised_draft(decision_id,new_draft_id))


@app.command("enqueue")
def enqueue_cmd(task_id: str,db: Path=Path("nutrifoundation.db")):
    store = ProductionStore(db)
    store.get("task",task_id)
    emit({"job_key":JobQueue(store).enqueue({"kind":"prefill","task_id":task_id})})


@app.command("work-one")
def work_cmd(command: str,db: Path=Path("nutrifoundation.db"),timeout: int=120):
    store = ProductionStore(db)
    emit(run_one(JobQueue(store),PrefillService(store),shlex.split(command),timeout=timeout))


@app.command("jobs")
def jobs_cmd(db: Path=Path("nutrifoundation.db")):
    emit(JobQueue(ProductionStore(db)).summary())


@app.command("promotion-gates")
def gates_cmd(draft_id: str,report_id: str,use: str="canonical",db: Path=Path("nutrifoundation.db")):
    emit(ReleaseService(ProductionStore(db)).promotion_gates(draft_id,report_id,use=use))


@app.command("invalidate")
def invalidate_cmd(dependency_id: str,reason: str,db: Path=Path("nutrifoundation.db")):
    emit({"affected":ProductionStore(db).invalidate(dependency_id,reason)})


@app.command("release-staging")
def release_cmd(release_id: str,draft_ids: list[str],cutoff: str=typer.Option(...,help="Timezone-aware ISO 8601 cutoff."),mode: str="SYSTEM_FAITHFUL",db: Path=Path("nutrifoundation.db")):
    try:
        stamp=datetime.fromisoformat(cutoff.replace('Z','+00:00'))
    except ValueError:
        raise typer.BadParameter('cutoff requires ISO 8601 with timezone') from None
    emit(ReleaseService(ProductionStore(db)).staging_release(tuple(draft_ids),release_id=release_id,cutoff_mode=mode,cutoff=stamp))


@app.command("export-schemas")
def schemas_cmd(out: Path):
    """Generate execution schemas from the runtime models, not frozen ontology."""
    out.mkdir(parents=True,exist_ok=True)
    from .models import ExtractionTask,FieldAssertion,ResultDraft,VerificationReport
    for model in (RawSnapshot,ParsedDocument,ExtractionTask,FieldAssertion,ResultDraft,PrefillDraft,
                  IndependentReadout,ReviewDecision,VerificationReport):
        (out/(model.__name__+'.schema.json')).write_text(json.dumps(model.model_json_schema(),ensure_ascii=False,indent=2)+'\n')
    emit({"schemas":9,"contract_version":"D0-production-v0.1","output":str(out)})


@app.command("curation-plan")
def curation_cmd(input_path: Path,count: int,exploration_count: int=1,seed: int=0):
    """Select priority/exploration sources from explicit question-gap proposals."""
    from .curation import priority_plan
    payload=json.loads(input_path.read_text())
    emit(priority_plan(payload['sources'],payload['question_gaps'],count=count,exploration_count=exploration_count,seed=seed))


@app.command("audit-plan")
def audit_cmd(input_path: Path,per_stratum: int=2,seed: int=0):
    """Random stratified audit manifest; does not fabricate reference labels."""
    from .curation import stratified_audit_plan
    emit(stratified_audit_plan(json.loads(input_path.read_text()),per_stratum=per_stratum,seed=seed))
