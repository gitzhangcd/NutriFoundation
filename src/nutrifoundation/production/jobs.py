from __future__ import annotations

import json
import time
from uuid import uuid4

from .models import digest
from .store import ProductionStore


class JobQueue:
    def __init__(self, store: ProductionStore):
        self.store = store

    def enqueue(self, payload: dict, *, max_attempts: int = 3, instant: float | None = None) -> str:
        if max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        instant = time.time() if instant is None else instant
        key = "JOB-"+digest(payload)
        with self.store.transaction() as con:
            con.execute("INSERT OR IGNORE INTO d0_job(job_key,payload,payload_sha,status,max_attempts,available_at) VALUES(?,?,?,'queued',?,?)",
                (key,json.dumps(payload,ensure_ascii=False),digest(payload),max_attempts,instant))
        return key

    def claim(self, *, lease_seconds: float = 180, instant: float | None = None) -> dict | None:
        if lease_seconds <= 0:
            raise ValueError("Positive lease required")
        instant = time.time() if instant is None else instant
        with self.store.transaction() as con:
            con.execute("UPDATE d0_job SET status='failed',token=NULL,error='attempts_exhausted_after_lease' WHERE status='running' AND lease_until<=? AND attempts>=max_attempts",(instant,))
            row = con.execute("SELECT * FROM d0_job WHERE attempts<max_attempts AND ((status IN ('queued','retry_wait') AND available_at<=?) OR (status='running' AND lease_until<=?)) ORDER BY available_at,job_key LIMIT 1",(instant,instant)).fetchone()
            if not row:
                return None
            token = uuid4().hex
            con.execute("UPDATE d0_job SET status='running',attempts=attempts+1,lease_until=?,token=? WHERE job_key=?",(instant+lease_seconds,token,row["job_key"]))
            return {"job_key":row["job_key"],"token":token,"payload":json.loads(row["payload"]),"attempt":row["attempts"]+1}

    def _owned(self, con, job, instant):
        row = con.execute("SELECT * FROM d0_job WHERE job_key=?",(job["job_key"],)).fetchone()
        if not row or row["status"]!="running" or row["token"]!=job["token"] or row["lease_until"]<=instant:
            raise ValueError("Expired/stale job lease")
        return row

    def complete(self, job: dict, result: dict, *, instant: float | None = None):
        instant = time.time() if instant is None else instant
        with self.store.transaction() as con:
            self._owned(con,job,instant)
            sha = self.store.put("job_result",job["job_key"],result,con=con)
            con.execute("UPDATE d0_job SET status='succeeded',result_sha=?,token=NULL WHERE job_key=?",(sha,job["job_key"]))

    def fail(self, job: dict, error_code: str, *, retryable: bool, instant: float | None = None):
        instant = time.time() if instant is None else instant
        with self.store.transaction() as con:
            row = self._owned(con,job,instant)
            status = "retry_wait" if retryable and row["attempts"]<row["max_attempts"] else "failed" if retryable else "blocked"
            delay = min(60,2**row["attempts"])
            con.execute("UPDATE d0_job SET status=?,available_at=?,token=NULL,error=? WHERE job_key=?",(status,instant+delay,error_code,job["job_key"]))

    def reserve_request(self, provider: str, *, requests_per_second: float, instant: float | None = None) -> float:
        if requests_per_second <= 0:
            raise ValueError("Positive provider rate required")
        instant = time.time() if instant is None else instant
        with self.store.transaction() as con:
            row = con.execute("SELECT next_at FROM d0_rate WHERE provider=?",(provider,)).fetchone()
            slot = max(instant,row[0] if row else instant)
            con.execute("INSERT INTO d0_rate VALUES(?,?) ON CONFLICT(provider) DO UPDATE SET next_at=excluded.next_at",(provider,slot+1/requests_per_second))
        return slot-instant

    def summary(self) -> dict:
        with self.store.transaction() as con:
            rows = con.execute("SELECT status,COUNT(*) FROM d0_job GROUP BY status").fetchall()
        return {row[0]:row[1] for row in rows}
