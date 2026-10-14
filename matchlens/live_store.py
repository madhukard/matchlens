"""Private Azure Blob publication; serving identity has read access only."""

import json
import os
from functools import lru_cache
from pathlib import Path
from threading import Lock
from time import monotonic

from azure.core.exceptions import ResourceExistsError
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.storage.blob import BlobServiceClient, ContentSettings

FALLBACK = Path(__file__).parent / "data" / "live.json"
_cache = None
_cache_time = 0.0
_lock = Lock()


@lru_cache(maxsize=1)
def container():
    credential = (
        ManagedIdentityCredential(client_id=os.environ["AZURE_CLIENT_ID"])
        if os.getenv("AZURE_CLIENT_ID")
        else DefaultAzureCredential()
    )
    client = BlobServiceClient(
        os.environ["MATCHLENS_STORAGE_URL"],
        credential=credential,
        retry_total=1,
        connection_timeout=4,
        read_timeout=6,
    )
    return client.get_container_client("runs")


def publish(run: dict, archive: bool = False):
    payload = json.dumps(run, ensure_ascii=False)
    if os.getenv("MATCHLENS_STORAGE_URL"):
        name = f"archive/{run['run_id']}.json" if archive else "latest.json"
        container().upload_blob(
            name,
            payload,
            overwrite=not archive,
            content_settings=ContentSettings(content_type="application/json"),
        )
    else:
        target = Path(os.getenv("MATCHLENS_LIVE_FILE", str(FALLBACK)))
        target.parent.mkdir(parents=True, exist_ok=True)
        temp = target.with_suffix(".tmp")
        temp.write_text(payload)
        temp.replace(target)


def acquire_worker_lease():
    """Only one manual job can publish a stream; crashes release the lease after 60s."""
    blob = container().get_blob_client("operator.lock")
    try:
        blob.upload_blob(b"MatchLens operator lock", overwrite=False)
    except ResourceExistsError:
        pass
    return blob.acquire_lease(lease_duration=60)


def read_run() -> dict:
    global _cache, _cache_time
    with _lock:
        if _cache is not None and monotonic() - _cache_time < 2:
            return _cache
        try:
            if os.getenv("MATCHLENS_STORAGE_URL"):
                payload = container().download_blob("latest.json").readall()
            else:
                payload = Path(os.getenv("MATCHLENS_LIVE_FILE", str(FALLBACK))).read_bytes()
            result = json.loads(payload)
            if not isinstance(result.get("frames"), list):
                raise ValueError("Invalid run")
            _cache, _cache_time = result, monotonic()
            return result
        except Exception:
            # Availability must not turn into silently presenting old data as live.
            if FALLBACK.exists():
                result = json.loads(FALLBACK.read_text())
                result["delivery"] = "bundled_recording"
                result["status"] = "recorded"
                return result
            return {
                "run_id": "not-started",
                "status": "not_started",
                "frames": [],
                "delivery": "unavailable",
            }
