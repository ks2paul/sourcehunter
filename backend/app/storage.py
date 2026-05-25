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
