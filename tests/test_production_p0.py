from datetime import date
from dataclasses import replace

import pytest

from nutrifoundation.connectors.ncbi import parse_pubmed_xml
from nutrifoundation.services.ingestion import classify_source_type
from nutrifoundation.persistence.sqlite import SQLiteStore
from nutrifoundation.services.semantic_bridge import SemanticTaskOrchestrator, SemanticResponseIngestionService
from test_semantic_worker_bridge import make_store, make_response
from nutrifoundation.production.release import cutoff_eligibility


def test_source_selection_binds_version_and_keeps_latest(tmp_path):
    store = SQLiteStore(tmp_path/'old.db'); store.initialize()
    old = store.save_source_text('s','pmc_fulltext','OLD','test')
    new = store.save_source_text('s','pmc_fulltext','NEW','test')
    with store.connect() as con:
        con.execute('UPDATE source_text_snapshot SET retrieved_at=? WHERE text_id=?',('2026-01-01',old))
        con.execute('UPDATE source_text_snapshot SET retrieved_at=? WHERE text_id=?',('2026-02-01',new))
    assert store.get_source_text('s')[0]=='NEW'
    assert store.get_source_text('s',snapshot_id=old)[0]=='OLD'
    with pytest.raises(ValueError,match='hash mismatch'):
        store.get_source_text('s',snapshot_id=new,expected_sha256='0'*64)
    with pytest.raises(ValueError,match='not found'):
        store.get_source_text('s',snapshot_id='missing')


def test_chat_default_is_draft_only(tmp_path):
    store=make_store(tmp_path)
    task=SemanticTaskOrchestrator(store).prepare_evidence_task('SA-TEST-001','EU-TEST-001')
    result=SemanticResponseIngestionService(store).ingest(make_response(task))
    assert result.task_state=='ingested'
    assert not result.f0_frozen
    assert store.list_f0_evidence()==[]
    assert result.verification_scope=='legacy_mechanical_checks_only'


@pytest.mark.parametrize('pubdate,precision,start,end',[
    ('<Year>2023</Year>','year',date(2023,1,1),date(2023,12,31)),
    ('<Year>2024</Year><Month>Feb</Month>','month',date(2024,2,1),date(2024,2,29)),
    ('<Year>2024</Year><Month>13</Month>','unresolved',None,None),
    ('<MedlineDate>2023 Winter-2024 Spring</MedlineDate>','unresolved',None,None),
])
def test_partial_date_is_not_fabricated(pubdate,precision,start,end):
    xml=f'<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>1</PMID><Article><ArticleTitle>Nonrandom intervention study</ArticleTitle><Journal><JournalIssue><PubDate>{pubdate}</PubDate></JournalIssue></Journal><PublicationTypeList><PublicationType>Clinical Trial</PublicationType></PublicationTypeList></Article></MedlineCitation></PubmedArticle></PubmedArticleSet>'
    article=parse_pubmed_xml(xml)[0]
    assert article.publication_date is None
    assert article.publication_date_precision==precision
    assert (article.publication_date_start,article.publication_date_end)==(start,end)
    assert classify_source_type(article) is None
    assert classify_source_type(replace(article,publication_types=('Unclassified',))) is None
    assert cutoff_eligibility(start,end,date(2023,6,1)) in {'UNRESOLVED','INELIGIBLE'}
