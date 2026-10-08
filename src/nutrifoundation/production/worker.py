from __future__ import annotations

import subprocess
from .jobs import JobQueue
from .prefill import PrefillService


def run_one(queue: JobQueue, prefill: PrefillService, command: list[str], *, timeout: int=120) -> dict:
    """One durable task per invocation; bounded worker pools can invoke concurrently.

    No hidden model calls or automatic scientific promotion. Semantic contract
    errors block; transient process timeouts receive bounded retry.
    """
    job = queue.claim(lease_seconds=timeout+30)
    if job is None:
        return {"status":"idle"}
    try:
        if job["payload"].get("kind")!="prefill":
            raise ValueError("Unsupported job type")
        draft = prefill.run_command(job["payload"]["task_id"],command,timeout=timeout)
        result = {"status":"STAGING","draft_id":draft.draft_id}
        queue.complete(job,result)
        return result
    except subprocess.TimeoutExpired:
        queue.fail(job,"worker_timeout",retryable=True)
        return {"status":"retry_or_failed","error":"worker_timeout"}
    except (ValueError,KeyError,subprocess.CalledProcessError,OSError) as error:
        # Do not record subprocess stderr or commands: they may contain credentials.
        queue.fail(job,type(error).__name__,retryable=False)
        return {"status":"blocked","error":type(error).__name__}
