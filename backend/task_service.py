import uuid
import time
from typing import Dict, Any, Optional

JOBS_REGISTRY: Dict[str, Dict[str, Any]] = {}


def create_job(job_type: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    job_id = str(uuid.uuid4())
    job_info = {
        "job_id": job_id,
        "job_type": job_type,
        "status": "queued",
        "progress": 0,
        "message": "Job queued for processing...",
        "result": None,
        "error": None,
        "created_at": time.time(),
        "metadata": metadata or {}
    }
    JOBS_REGISTRY[job_id] = job_info
    return job_info


def update_job(job_id: str, status: Optional[str] = None, progress: Optional[int] = None, message: Optional[str] = None, result: Any = None, error: Any = None):
    if job_id in JOBS_REGISTRY:
        if status:
            JOBS_REGISTRY[job_id]["status"] = status
        if progress is not None:
            JOBS_REGISTRY[job_id]["progress"] = min(100, max(0, progress))
        if message:
            JOBS_REGISTRY[job_id]["message"] = message
        if result is not None:
            JOBS_REGISTRY[job_id]["result"] = result
        if error is not None:
            JOBS_REGISTRY[job_id]["error"] = error


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    return JOBS_REGISTRY.get(job_id)
