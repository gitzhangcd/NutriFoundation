from pathlib import Path
import json
import shlex

import typer

from nutrifoundation.agents.evidence_extraction import (
    EvidenceExtractionAgent,
    SubprocessEvidenceExtractionProvider,
)
from nutrifoundation.agents.evidence_verification import IndependentEvidenceVerifier
from nutrifoundation.contract import E01_INVARIANTS
from nutrifoundation.connectors.fixture import FixturePubMedConnector
from nutrifoundation.connectors.ncbi import PMCConnector, PubMedConnector
from nutrifoundation.io.loaders import load_structured
from nutrifoundation.persistence.sqlite import SQLiteStore
from nutrifoundation.services.evidence_pipeline import EvidenceProductionService
from nutrifoundation.services.evidence_replay import replay_batch001_evidence
from nutrifoundation.services.ingestion import SourceArtifactIngestionService
from nutrifoundation.services.replay import replay_batch001

app = typer.Typer(help="NutriFoundation Engine reference CLI")


@app.command("contract-check")
def contract_check() -> None:
    """Print the frozen executable invariants."""
    for invariant in E01_INVARIANTS:
        typer.echo(f"PASS  {invariant.key}: {invariant.statement}")


@app.command("validate-gold-gate")
def validate_gold_gate(path: Path) -> None:
    """Validate that a Gold registry respects the mandatory human gate."""
    data = load_structured(path)
    frozen = int(data.get("frozen_gold_count", 0))
    gold_claims = data.get("gold_claims", []) or []
    ready = data.get("ready_candidates", []) or []

    if frozen != len(gold_claims):
        raise typer.BadParameter(
            "frozen_gold_count does not match gold_claims length"
        )

    for item in ready:
        if item.get("human_adjudication") != "pending" and not gold_claims:
            raise typer.BadParameter(
                "Non-pending human gate must have explicit Gold/adjudication records"
            )

    typer.echo(
        f"PASS  registry={path} frozen_gold_count={frozen} "
        f"ready_candidates={len(ready)}"
    )


@app.command("init-db")
def init_db(db: Path = Path("nutrifoundation.db")) -> None:
    """Initialize the SQLite persistence layer."""
    SQLiteStore(db).initialize()
    typer.echo(f"PASS  initialized={db}")


@app.command("ingest-pmid")
def ingest_pmid(
    pmid: str,
    source_id: str,
    db: Path = Path("nutrifoundation.db"),
) -> None:
    """Retrieve one PMID from live PubMed and persist a SourceArtifact."""
    service = SourceArtifactIngestionService(
        PubMedConnector(),
        SQLiteStore(db),
        mode="live",
    )
    manifest = service.ingest([(source_id, pmid)])
    typer.echo(manifest.model_dump_json(indent=2))
    if manifest.status != "completed":
        raise typer.Exit(1)


@app.command("fetch-pmc")
def fetch_pmc(
    pmcid: str,
    source_id: str | None = None,
    db: Path = Path("nutrifoundation.db"),
) -> None:
    """Retrieve rights-available PMC XML and persist its exact bytes."""
    store = SQLiteStore(db)
    store.initialize()
    xml = PMCConnector().fetch_full_text_xml(pmcid)
    store.save_full_text(pmcid, xml, source_id=source_id)
    typer.echo(f"PASS  pmcid={pmcid} chars={len(xml)} db={db}")


@app.command("replay-batch001")
def replay_batch001_cmd(
    registry: Path,
    db: Path = Path("batch001_replay.db"),
    fixture: Path | None = None,
    live: bool = False,
) -> None:
    """Replay the 20-source Batch001 registry into a fresh persistence DB."""
    if fixture and live:
        raise typer.BadParameter("Choose either --fixture or --live")

    connector = (
        PubMedConnector()
        if live
        else FixturePubMedConnector(
            fixture or Path("fixtures/pubmed_batch001_articles.json")
        )
    )

    report = replay_batch001(
        registry,
        connector,
        SQLiteStore(db),
        mode="live" if live else "offline_replay",
    )

    typer.echo(
        json.dumps(
            report.as_dict(),
            indent=2,
            ensure_ascii=False,
        )
    )

    if report.status != "PASS":
        raise typer.Exit(1)


@app.command("produce-evidence")
def produce_evidence(
    source_id: str,
    evidence_id: str,
    extractor_command: str = typer.Option(
        ...,
        help="External JSON extraction command, e.g. 'python my_extractor.py'",
    ),
    db: Path = Path("nutrifoundation.db"),
) -> None:
    """Run extraction -> independent verification -> F0 freeze for one source."""
    provider = SubprocessEvidenceExtractionProvider(
        shlex.split(extractor_command)
    )
    service = EvidenceProductionService(
        EvidenceExtractionAgent(provider),
        IndependentEvidenceVerifier(),
        SQLiteStore(db),
        mode="live",
    )
    manifest = service.produce([(source_id, evidence_id)])
    typer.echo(manifest.model_dump_json(indent=2))
    if manifest.status != "completed":
        raise typer.Exit(1)


@app.command("replay-evidence-batch001")
def replay_evidence_batch001_cmd(
    source_registry: Path = Path(
        "fixtures/Batch001_Verified_SourceArtifact_Registry_v0.1.yaml"
    ),
    evidence_registry: Path = Path(
        "fixtures/Batch001_EvidenceUnit_Frozen_v0.1.yaml"
    ),
    pubmed_fixture: Path = Path(
        "fixtures/pubmed_batch001_articles.json"
    ),
    db: Path = Path("batch001_evidence_replay.db"),
) -> None:
    """Replay SourceArtifact -> EvidenceUnit candidate -> verification -> F0 for Batch001."""
    report = replay_batch001_evidence(
        source_registry,
        pubmed_fixture,
        evidence_registry,
        SQLiteStore(db),
    )
    typer.echo(
        json.dumps(
            report.as_dict(),
            indent=2,
            ensure_ascii=False,
        )
    )
    if report.status != "PASS":
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
