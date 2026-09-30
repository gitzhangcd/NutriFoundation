from pathlib import Path
import json

import typer

from nutrifoundation.contract import E01_INVARIANTS
from nutrifoundation.connectors.fixture import FixturePubMedConnector
from nutrifoundation.connectors.ncbi import PMCConnector, PubMedConnector
from nutrifoundation.io.loaders import load_structured
from nutrifoundation.persistence.sqlite import SQLiteStore
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


if __name__ == "__main__":
    app()
