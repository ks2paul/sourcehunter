from fastapi import APIRouter, HTTPException, status

from app.deduplication import deduplicate_suppliers
from app.models import RawListingsResponse, SearchJob, SearchJobCreate, SuppliersResponse
from app.scraping.platforms.made_in_china import MadeInChinaAdapter
from app.scraping.worker import ScrapingWorker
from app.storage import SearchJobRepository

router = APIRouter(prefix="/api/search-jobs", tags=["search-jobs"])
repository = SearchJobRepository()


def create_scraping_worker() -> ScrapingWorker:
    return ScrapingWorker(adapters=[MadeInChinaAdapter()])


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
async def get_raw_listings(job_id: str) -> RawListingsResponse:
    job = repository.get(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search job not found")
    scrape_result = await create_scraping_worker().search_all(job.product_keyword)
    return RawListingsResponse(
        job_id=job.job_id,
        status="completed" if scrape_result.listings else "no_results",
        listings=[listing.model_dump(mode="json") for listing in scrape_result.listings],
        failures=[failure.model_dump(mode="json") for failure in scrape_result.failures],
    )


@router.get("/{job_id}/suppliers", response_model=SuppliersResponse)
async def get_unique_suppliers(job_id: str) -> SuppliersResponse:
    job = repository.get(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search job not found")

    scrape_result = await create_scraping_worker().search_all(job.product_keyword)
    suppliers = deduplicate_suppliers(scrape_result.listings)
    return SuppliersResponse(
        job_id=job.job_id,
        status="completed" if suppliers else "no_results",
        suppliers=[supplier.model_dump(mode="json") for supplier in suppliers],
        failures=[failure.model_dump(mode="json") for failure in scrape_result.failures],
    )
