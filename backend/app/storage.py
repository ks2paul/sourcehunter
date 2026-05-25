from uuid import uuid4

from app.keyword_expansion import expand_keywords
from app.models import SearchJob, SearchJobCreate, SearchJobStatus, SearchProgress, utc_now


class SearchJobRepository:
    def __init__(self) -> None:
        self._jobs: dict[str, SearchJob] = {}

    def create(self, request: SearchJobCreate) -> SearchJob:
        now = utc_now()
        job_id = f"job_{uuid4().hex}"
        keyword_expansion = expand_keywords(request.product_keyword)
        job = SearchJob(
            job_id=job_id,
            product_keyword=request.product_keyword.strip(),
            target_price=request.target_price,
            moq_preference=request.moq_preference,
            supplier_preference=request.supplier_preference,
            status=SearchJobStatus.COMPLETED,
            progress=SearchProgress(
                stage="keyword_expansion_completed",
                message="Keyword expansion completed. Supplier scraping is not enabled in the foundation build.",
            ),
            keyword_expansion=keyword_expansion,
            created_at=now,
            updated_at=now,
        )
        self._jobs[job_id] = job
        return job

    def get(self, job_id: str) -> SearchJob | None:
        return self._jobs.get(job_id)
