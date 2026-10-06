from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class ValidationCheck:
    validator_id: str
    rule_id: str
    status: str
    error_code: str | None = None
    severity: str = "ERROR"
    object_ref: str | None = None
    path: str | None = None
    expected: Any = None
    observed: Any = None
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class ValidationContext:
    contract_version: str = "NDF-D0-v0.1"
    projection_policy_version: str = "NDF-D0-Projection-v0.1"
    cutoff_time: str | None = None
    authorized_view: str = "SYSTEM_VIEW"
    frozen_revisions: dict[str, str] = field(default_factory=dict)


@dataclass
class ValidationReport:
    run_id: str
    contract_version: str
    projection_policy_version: str
    target_refs: list[str]
    checks: list[ValidationCheck]
    generated_time: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def failed_checks(self) -> int:
        return sum(1 for c in self.checks if c.status == "FAIL")

    @property
    def warning_checks(self) -> int:
        return sum(1 for c in self.checks if c.status == "WARN")

    @property
    def qualification(self) -> str:
        return "FAIL" if self.failed_checks else "PASS"

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "contract_version": self.contract_version,
            "projection_policy_version": self.projection_policy_version,
            "target_refs": self.target_refs,
            "checks": [asdict(c) for c in self.checks],
            "summary": {
                "total_checks": len(self.checks),
                "failed_checks": self.failed_checks,
                "warning_checks": self.warning_checks,
            },
            "qualification": self.qualification,
            "generated_time": self.generated_time,
        }
