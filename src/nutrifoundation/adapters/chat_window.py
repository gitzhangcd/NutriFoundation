from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from nutrifoundation.domain.semantic_worker import (
    ResponseEnvelope,
    SemanticSubmissionReceipt,
    TaskBundle,
)


class ChatWindowFileBridge:
    """File-based RPC bridge for a human-visible chat model.

    The bridge never calls a model provider. It exports an immutable TaskBundle
    and later imports a ResponseEnvelope produced in the chat window.
    """

    adapter_type = "chat_window_file_bridge"

    def export_task(
        self,
        task: TaskBundle,
        outbox: str | Path,
    ) -> SemanticSubmissionReceipt:
        outbox = Path(outbox)
        outbox.mkdir(parents=True, exist_ok=True)
        path = outbox / f"{task.task_id}.request.json"
        if path.exists():
            existing = TaskBundle.model_validate_json(path.read_text(encoding="utf-8"))
            if existing.task_sha256 != task.task_sha256:
                raise ValueError(f"Task file already exists with different payload: {path}")
        else:
            path.write_text(task.model_dump_json(indent=2), encoding="utf-8")

        return SemanticSubmissionReceipt(
            task_id=task.task_id,
            task_sha256=task.task_sha256,
            adapter_type=self.adapter_type,
            location=str(path),
            submitted_at=datetime.now(timezone.utc),
        )

    def load_response(self, path: str | Path) -> ResponseEnvelope:
        return ResponseEnvelope.model_validate_json(
            Path(path).read_text(encoding="utf-8")
        )
