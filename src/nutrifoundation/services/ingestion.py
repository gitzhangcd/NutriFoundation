from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from nutrifoundation.connectors.ncbi import PubMedArticle, PubMedProvider
from nutrifoundation.domain.enums import SourceType
from nutrifoundation.domain.models import Provenance, SourceArtifact, SourceIdentifiers
from nutrifoundation.domain.run_manifest import RunManifest
from nutrifoundation.persistence.sqlite import SQLiteStore


def classify_source_type(article: PubMedArticle, *, legacy: bool = False) -> SourceType | None:
    publication_types = set(article.publication_types)
    title = article.title.lower()

    if "Practice Guideline" in publication_types:
        return SourceType.GUIDELINE
    if "Meta-Analysis" in publication_types or "Network Meta-Analysis" in publication_types:
        return SourceType.META_ANALYSIS
    if "Systematic Review" in publication_types:
        return SourceType.SYSTEMATIC_REVIEW
    if "Randomized Controlled Trial" in publication_types or (legacy and "Clinical Trial" in publication_types):
        return SourceType.RCT
    if "Observational Study" in publication_types or "cohort" in title:
        return SourceType.COHORT
    if "consensus report" in title:
        return SourceType.CONSENSUS

    # PubMed may describe the corrected canonical article by publication-history
    # type rather than repeating the original trial design.
    if "Corrected and Republished Article" in publication_types:
        abstract = (article.abstract or "").lower()
        if any(
            token in abstract
            for token in ("randomized", "randomised", "randomly assigned", "randomly allocated")
        ):
            return SourceType.RCT

    if "Position Statement" in publication_types or "position statement" in title:
        return SourceType.POSITION_STATEMENT
    return SourceType.POSITION_STATEMENT if legacy else None


def article_to_source(
    article: PubMedArticle,
    source_id: str,
    *,
    provider: str = "PubMed",
    run_id: str | None = None,
    legacy_source_types: bool = False,
) -> SourceArtifact:
    source_type = classify_source_type(article, legacy=legacy_source_types)
    if source_type is None:
        raise ValueError("Unresolved source type; retain acquisition and request classification")
    return SourceArtifact(
        source_id=source_id,
        source_type=source_type,
        title=article.title,
        authors=article.authors,
        publication_date=article.publication_date,
        identifiers=SourceIdentifiers(
            doi=article.doi,
            pmid=article.pmid,
            pmcid=article.pmcid,
        ),
        provenance=Provenance(
            source=f"https://pubmed.ncbi.nlm.nih.gov/{article.pmid}/",
            provider=provider,
            retrieved_at=datetime.now(timezone.utc),
            metadata={
                "publication_types": list(article.publication_types),
                "journal": article.journal,
                "run_id": run_id,
                **({
                    "publication_date_raw": article.publication_date_raw,
                    "publication_date_precision": article.publication_date_precision,
                    "publication_date_start": article.publication_date_start.isoformat() if article.publication_date_start else None,
                    "publication_date_end": article.publication_date_end.isoformat() if article.publication_date_end else None,
                    "source_type_status": "metadata_candidate_not_design_verified",
                } if article.publication_date_raw else {}),
            },
        ),
    )


class SourceArtifactIngestionService:
    def __init__(
        self,
        connector: PubMedProvider,
        store: SQLiteStore,
        *,
        mode: str = "live",
        code_version: str = "0.2.0",
        legacy_source_types: bool = False,
    ):
        self.connector = connector
        self.store = store
        self.mode = mode
        self.code_version = code_version
        self.legacy_source_types = legacy_source_types

    def ingest(self, mapping: list[tuple[str, str]]) -> RunManifest:
        run_id = (
            f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-"
            f"{uuid4().hex[:8]}"
        )

        manifest = RunManifest(
            run_id=run_id,
            pipeline_name="source_artifact_ingestion",
            pipeline_version="E0.2",
            mode=self.mode,
            started_at=datetime.now(timezone.utc),
            inputs={
                "mapping": [
                    {"source_id": source_id, "pmid": pmid}
                    for source_id, pmid in mapping
                ]
            },
            providers=(self.connector.__class__.__name__,),
            code_version=self.code_version,
        )

        self.store.initialize()
        self.store.save_run_manifest(manifest)

        errors: list[str] = []
        saved: list[str] = []

        try:
            articles = self.connector.fetch_articles([pmid for _, pmid in mapping])
            by_pmid = {article.pmid: article for article in articles}

            for source_id, pmid in mapping:
                if pmid not in by_pmid:
                    errors.append(f"missing PMID {pmid}")
                    self.store.log_ingestion_event(
                        run_id,
                        source_id,
                        "fetch",
                        "failed",
                        f"PMID {pmid} missing",
                    )
                    continue

                try:
                    source = article_to_source(
                        by_pmid[pmid], source_id,
                        provider=self.connector.__class__.__name__, run_id=run_id,
                        legacy_source_types=self.legacy_source_types,
                    )
                except ValueError as error:
                    errors.append(f"{source_id}: {error}")
                    self.store.log_ingestion_event(run_id, source_id, "classify", "deferred", str(error))
                    continue
                self.store.upsert_source(source)
                if by_pmid[pmid].abstract:
                    self.store.save_source_text(
                        source_id,
                        "pubmed_abstract",
                        by_pmid[pmid].abstract,
                        self.connector.__class__.__name__,
                    )
                saved.append(source_id)
                self.store.log_ingestion_event(
                    run_id,
                    source_id,
                    "upsert_source",
                    "completed",
                    pmid,
                )

            status = "completed" if not errors else "failed"

        except Exception as error:
            errors.append(str(error))
            status = "failed"

        final = manifest.model_copy(
            update={
                "finished_at": datetime.now(timezone.utc),
                "status": status,
                "outputs": {
                    "saved_source_ids": saved,
                    "saved_count": len(saved),
                },
                "errors": tuple(errors),
            }
        )
        self.store.save_run_manifest(final)
        return final
