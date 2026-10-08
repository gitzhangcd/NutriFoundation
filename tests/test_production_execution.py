import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from nutrifoundation.cli import app
from nutrifoundation.production.models import digest
from nutrifoundation.production.jobs import JobQueue
from nutrifoundation.production.providers import NCBIRawAdapter
from nutrifoundation.production.prefill import PrefillService
from nutrifoundation.production.worker import run_one
from nutrifoundation.production.workbench import assisted_html
from nutrifoundation.production.review import ReviewService
from test_production_pipeline import pipeline


def test_command_adapter_cache_queue_and_cli_roundtrip(pipeline,tmp_path):
    store,svc,snap,parsed,task,draft=pipeline
    response=tmp_path/'response.json';response.write_text(draft.model_dump_json())
    worker=tmp_path/'worker.py'
    worker.write_text('import sys,json\nfrom pathlib import Path\nr=json.load(sys.stdin)\nassert r["task_sha256"]=='+repr(digest(task))+'\nprint(Path('+repr(str(response))+').read_text())\n')
    q=JobQueue(store);q.enqueue({'kind':'prefill','task_id':task.task_id})
    assert run_one(q,PrefillService(store),[sys.executable,str(worker)])['status']=='STAGING'
    assert q.summary()=={'succeeded':1}
    # Re-executing identical task uses persisted accepted response, not another model call.
    assert PrefillService(store).run_command(task.task_id,['intentionally-missing-command'])==draft
    runner=CliRunner();out=tmp_path/'review.html'
    result=runner.invoke(app,['production','export-review','d1','test-reviewer',str(out),'--db',store.db])
    assert result.exit_code==0,result.output
    assert '证据预填写审查' in out.read_text()
    forbidden=runner.invoke(app,['production','export-review','d1','test-reviewer',str(out),'--mode','source_only','--db',store.db])
    assert forbidden.exit_code!=0
    from zipfile import ZipFile
    blank=tmp_path/'source-only.zip'
    result=runner.invoke(app,['production','export-review','d1','reviewer-a',str(blank),'--mode','source_only','--db',store.db])
    assert result.exit_code==0,result.output
    with ZipFile(blank) as archive:
        manifest=json.loads(archive.read('manifest.json'))
        assert set(archive.namelist())==set(manifest['allowlist'])
        form=json.loads(archive.read('review.json'))
        assert not {'prefill','checks','results','anchors'}&form.keys()
        assert 'review.html' not in archive.namelist()
    stamp=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
    released=runner.invoke(app,['production','release-staging','cli-release','d1','--cutoff',stamp,'--db',store.db])
    assert released.exit_code==0,released.output
    assert json.loads(released.output)['status']=='STAGING_ONLY'


def test_workbench_payload_escaping_and_source_only_guard(pipeline):
    store,svc,snap,parsed,task,draft=pipeline
    PrefillService(store).ingest(draft);reviews=ReviewService(store)
    rt=reviews.create('d1',reviewer_id='</script><img src=x>',mode='assisted')
    html=assisted_html(reviews.export(rt['review_task_id']))
    assert '</script><img src=x>' not in html
    assert '\\u003c/script>' in html
    blank=reviews.create('d1',reviewer_id='r',mode='source_only')
    with pytest.raises(ValueError,match='source-only'):
        assisted_html(reviews.export(blank['review_task_id']))


def test_ncbi_raw_adapter_preserves_bytes_and_sanitizes_secrets(pipeline):
    store,svc,*_=pipeline
    xml=b'<article><front><article-meta><article-id pub-id-type="pmc">PMC123</article-id></article-meta></front></article>'
    class Response:
        status=200;headers={'Content-Type':'application/xml'}
        def read(self,limit):return xml
        def __enter__(self):return self
        def __exit__(self,*args):pass
    adapter=NCBIRawAdapter(svc,JobQueue(store),api_key='synthetic-secret')
    with patch('urllib.request.urlopen',return_value=Response()):
        snapshot=adapter.fetch('PMC123',database='pmc',source_id='pmc123',source_version='v1',license='not_certified')
    assert svc.read(snapshot.snapshot_id)[1]==xml
    with store.transaction() as con:
        events=[row[0] for row in con.execute('SELECT payload FROM d0_event')]
    assert all('synthetic-secret' not in e for e in events)
    with patch('urllib.request.urlopen',side_effect=OSError('secret url')),patch('time.sleep'):
        with pytest.raises(ValueError,match='sanitized'):
            adapter.fetch('PMC123',database='pmc',source_id='pmc123',source_version='v2',license='not_certified')
    with store.transaction() as con:
        assert all('secret url' not in row[0] for row in con.execute('SELECT payload FROM d0_event'))


def test_retry_exhaustion_after_crash_and_transaction_rollback(pipeline):
    store,*_=pipeline;q=JobQueue(store)
    key=q.enqueue({'task':'crash'},max_attempts=1,instant=0)
    assert q.claim(lease_seconds=1,instant=0)
    assert q.claim(instant=2) is None
    assert q.summary()=={'failed':1}
    with pytest.raises(RuntimeError):
        with store.transaction() as con:
            store.put('job_result','rollback',{'n':1},con=con)
            raise RuntimeError('crash before status commit')
    with pytest.raises(ValueError,match='Missing'):
        store.get('job_result','rollback')
