from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from .models import FrozenModel


class RunManifest(FrozenModel):
    run_id: str
    pipeline_name: str
    pipeline_version: str
    mode: Literal["live", "offline_replay", "test"]
    started_at: datetime
    finished_at: datetime | None = None
    status: Literal["running", "completed", "failed"] = "running"
    inputs: dict[str, Any] = Field(default_factory=dict)
    providers: tuple[str, ...] = ()
    code_version: str | None = None
    outputs: dict[str, Any] = Field(default_factory=dict)
    errors: tuple[str, ...] = ()
