from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from uuid import uuid4
from .models import RawSnapshot
from .store import ProductionStore


class SnapshotService:
    """Preserve supplied raw bytes before parsing, with one event per acquisition.

    Source adapters acquire authorized content; this service makes no fabricated
    assertion about HTTP responses, scientific verification or publication dates.
    """
    def __init__(self, store: ProductionStore, blob_root: str | Path):
        self.store = store
        self.root = Path(blob_root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def ingest(self, data: bytes, *, source_id: str, source_version: str,
               format: str, content_scope: str, license: str, lane: str = "scientific",
               origin: str, expected_sha256: str | None = None) -> RawSnapshot:
        sha = hashlib.sha256(data).hexdigest()
        if expected_sha256 and sha != expected_sha256:
            raise ValueError("Raw acquisition hash mismatch")
        path = self.root / sha
        if path.exists():
            if hashlib.sha256(path.read_bytes()).hexdigest() != sha:
                raise ValueError("Stored raw blob corrupt")
        else:
            fd, tmp = tempfile.mkstemp(dir=self.root)
            try:
                with os.fdopen(fd, "wb") as out:
                    out.write(data)
                    out.flush()
                    os.fsync(out.fileno())
                os.replace(tmp, path)
            finally:
                if os.path.exists(tmp):
                    os.unlink(tmp)
        from .models import digest
        identity = digest(dict(source_id=source_id, source_version=source_version, sha=sha,
                               format=format, content_scope=content_scope, license=license, lane=lane))
        snapshot = RawSnapshot(snapshot_id="SNAP-"+identity, source_id=source_id,
            source_version=source_version, content_sha256=sha, format=format,
            content_scope=content_scope, license=license, lane=lane,
            byte_count=len(data), blob_path=str(path))
        self.store.put("snapshot", snapshot.snapshot_id, snapshot)
        self.store.event("acquisition", snapshot.snapshot_id, {"event_id":uuid4().hex,
            "origin":origin, "byte_count":len(data), "sha256":sha})
        return snapshot

    def read(self, snapshot_id: str) -> tuple[RawSnapshot, bytes]:
        snapshot = RawSnapshot.model_validate(self.store.get("snapshot", snapshot_id))
        data = Path(snapshot.blob_path).read_bytes()
        if len(data) != snapshot.byte_count or hashlib.sha256(data).hexdigest() != snapshot.content_sha256:
            raise ValueError("Raw snapshot integrity failure")
        return snapshot, data
