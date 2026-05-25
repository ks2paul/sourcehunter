from fastapi import APIRouter, HTTPException, status

from app.models import SearchJob, SearchJobCreate
from app.storage import SearchJobRepository

router = APIRouter(prefix="/api/search-jobs", tags=["search-jobs"])
repository = SearchJobRepository()


@router.post("", response_model=SearchJob, status_code=status.HTTP_201_CREATED)
def create_search_job(request: SearchJobCreate) -> SearchJob:
    return repository.create(request)


@router.get("/{job_id}", response_model=SearchJob)
def get_search_job(job_id: str) -> SearchJob:
    job = repository.get(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search job not found")
    return job
