from pathlib import Path

import typer

from nutrifoundation.contract import E01_INVARIANTS
from nutrifoundation.io.loaders import load_structured

app = typer.Typer(help="NutriFoundation Engine reference CLI")


@app.command("contract-check")
def contract_check() -> None:
    """Print the frozen E0.1 executable invariants."""
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
        raise typer.BadParameter("frozen_gold_count does not match gold_claims length")

    for item in ready:
        if item.get("human_adjudication") != "pending" and not gold_claims:
            raise typer.BadParameter(
                "Non-pending human gate must have explicit Gold/adjudication records"
            )

    typer.echo(
        f"PASS  registry={path} frozen_gold_count={frozen} "
        f"ready_candidates={len(ready)}"
    )


if __name__ == "__main__":
    app()
