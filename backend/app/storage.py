import json
import sqlite3
from pathlib import Path
from uuid import uuid4

from app.config import get_settings
from app.keyword_expansion import expand_keywords
from app.models import SearchJob, SearchJobCreate, SearchJobStatus, SearchProgress, utc_now


class SearchJobRepository:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self._db_path = Path(db_path or get_settings().database_path)
        self._initialize()

    async def create(self, request: SearchJobCreate) -> SearchJob:
        now = utc_now()
        job_id = f"job_{uuid4().hex}"
        keyword_expansion = await expand_keywords(request.product_keyword)
        job = SearchJob(
            job_id=job_id,
            product_keyword=request.product_keyword.strip(),
            product_features=request.product_features.strip() if request.product_features else None,
            target_price=request.target_price,
            moq_preference=request.moq_preference,
            supplier_preference=request.supplier_preference,
            status=SearchJobStatus.COMPLETED,
            progress=SearchProgress(
                stage="keyword_expansion_completed",
                message="Keyword expansion completed. Made-in-China raw listing retrieval is available.",
            ),
            keyword_expansion=keyword_expansion,
            created_at=now,
            updated_at=now,
        )
        self._save(job)
        return job

    def get(self, job_id: str) -> SearchJob | None:
        with self._connect() as connection:
            row = connection.execute("SELECT payload FROM search_jobs WHERE job_id = ?", (job_id,)).fetchone()
        if row is None:
            return None
        return SearchJob.model_validate_json(row[0])

    def save_supplier_result(self, job_id: str, payload: dict) -> None:
        self._save_result(job_id=job_id, result_type="suppliers", payload=payload)

    def get_supplier_result(self, job_id: str) -> dict | None:
        return self._get_result(job_id=job_id, result_type="suppliers")

    def save_raw_listing_result(self, job_id: str, payload: dict) -> None:
        self._save_result(job_id=job_id, result_type="raw_listings", payload=payload)

    def get_raw_listing_result(self, job_id: str) -> dict | None:
        return self._get_result(job_id=job_id, result_type="raw_listings")

    def _initialize(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS search_jobs (
                    job_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS search_results (
                    job_id TEXT NOT NULL,
                    result_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (job_id, result_type)
                )
                """
            )

    def _save(self, job: SearchJob) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO search_jobs (job_id, payload, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    job.job_id,
                    job.model_dump_json(),
                    job.created_at.isoformat(),
                    job.updated_at.isoformat(),
                ),
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _save_result(self, job_id: str, result_type: str, payload: dict) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO search_results (job_id, result_type, payload, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (job_id, result_type, json.dumps(payload), utc_now().isoformat()),
            )

    def _get_result(self, job_id: str, result_type: str) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM search_results WHERE job_id = ? AND result_type = ?",
                (job_id, result_type),
            ).fetchone()
        if row is None:
            return None
        return json.loads(row[0])
