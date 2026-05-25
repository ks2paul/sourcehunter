from fastapi import APIRouter, HTTPException, status

from app.models import RawListingsResponse, SearchJob, SearchJobCreate
from app.storage import SearchJobRepository

router = APIRouter(prefix="/api/search-jobs", tags=["search-jobs"])
repository = SearchJobRepository()


@router.post("", response_model=SearchJob, status_code=status.HTTP_201_CREATED)
async def create_search_job(request: SearchJobCreate) -> SearchJob:
    return await repository.create(request)


@router.get("/{job_id}", response_model=SearchJob)
def get_search_job(job_id: str) -> SearchJob:
    job = repository.get(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search job not found")
    return job


@router.get("/{job_id}/raw-listings", response_model=RawListingsResponse)
def get_raw_listings(job_id: str) -> RawListingsResponse:
    job = repository.get(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search job not found")
    return RawListingsResponse(
        job_id=job.job_id,
        status="scraping_not_enabled",
        listings=[],
        failures=[],
    )
