from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import require_authenticated_user
from app.deduplication import deduplicate_suppliers
from app.models import RawListingsResponse, SearchJob, SearchJobCreate, SuppliersResponse
from app.scraping.platforms.elimapi_1688 import Elimapi1688Adapter
from app.scraping.platforms.made_in_china import MadeInChinaAdapter
from app.scraping.worker import ScrapingWorker
from app.sourcing_intent import china_1688_finished_product_keyword, made_in_china_feature_terms, made_in_china_finished_product_keyword
from app.storage import SearchJobRepository

router = APIRouter(prefix="/api/search-jobs", tags=["search-jobs"], dependencies=[Depends(require_authenticated_user)])
repository = SearchJobRepository()
SUPPLIER_CACHE_VERSION = 15


def create_scraping_worker() -> ScrapingWorker:
    return ScrapingWorker(adapters=[MadeInChinaAdapter(), Elimapi1688Adapter()])


@router.post("", response_model=SearchJob, status_code=status.HTTP_201_CREATED)
async def create_search_job(request: SearchJobCreate) -> SearchJob:
    return await repository.create(request)


@router.get("", response_model=list[SearchJob])
def list_search_jobs() -> list[SearchJob]:
    return repository.list_recent(limit=20)


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
    cached_result = repository.get_raw_listing_result(job.job_id)
    if cached_result is not None:
        return RawListingsResponse(job_id=job.job_id, **cached_result)

    scrape_result = await _search_for_job(job)
    payload = {
        "status": "completed" if scrape_result.listings else "no_results",
        "listings": [listing.model_dump(mode="json") for listing in scrape_result.listings],
        "failures": [failure.model_dump(mode="json") for failure in scrape_result.failures],
    }
    repository.save_raw_listing_result(job.job_id, payload)
    return RawListingsResponse(
        job_id=job.job_id,
        **payload,
    )


@router.get("/{job_id}/suppliers", response_model=SuppliersResponse)
async def get_unique_suppliers(job_id: str) -> SuppliersResponse:
    job = repository.get(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search job not found")
    cached_result = repository.get_supplier_result(job.job_id)
    if cached_result is not None and cached_result.get("cache_version") == SUPPLIER_CACHE_VERSION:
        return SuppliersResponse(job_id=job.job_id, **cached_result)

    scrape_result = await _search_for_job(job)
    platform_keywords = _platform_search_keywords(job)
    platform_match_keywords = _platform_match_keywords(job)
    suppliers = deduplicate_suppliers(
        scrape_result.listings,
        product_keyword=job.product_keyword,
        product_features=job.product_features,
        target_price=job.target_price,
        moq_preference=job.moq_preference,
        supplier_preference=job.supplier_preference,
    )
    platform_supplier_groups = _platform_supplier_groups(
        listings=scrape_result.listings,
        product_keyword=job.product_keyword,
        product_features=job.product_features,
        platform_keywords=platform_match_keywords,
        target_price=job.target_price,
        moq_preference=job.moq_preference,
        supplier_preference=job.supplier_preference,
    )
    payload = {
        "cache_version": SUPPLIER_CACHE_VERSION,
        "status": "completed" if suppliers else "no_results",
        "suppliers": [supplier.model_dump(mode="json") for supplier in suppliers],
        "platform_supplier_groups": platform_supplier_groups,
        "platform_diagnostics": _platform_diagnostics(
            listings=scrape_result.listings,
            platform_supplier_groups=platform_supplier_groups,
            platform_keywords=platform_keywords,
            failures=[failure.model_dump(mode="json") for failure in scrape_result.failures],
        ),
        "failures": [failure.model_dump(mode="json") for failure in scrape_result.failures],
    }
    repository.save_supplier_result(job.job_id, payload)
    return SuppliersResponse(
        job_id=job.job_id,
        **payload,
    )


async def _search_for_job(job: SearchJob):
    worker = create_scraping_worker()
    if not hasattr(worker, "search_with_platform_keywords"):
        return await worker.search_all(job.product_keyword)
    return await worker.search_with_platform_keywords(
        default_keyword=job.product_keyword,
        platform_keywords=_platform_search_keywords(job),
    )


def _platform_search_keywords(job: SearchJob) -> dict[str, str]:
    return {
        platform: _append_features(keyword, job.product_features, platform=platform)
        for platform, keyword in _platform_match_keywords(job).items()
    }


def _platform_match_keywords(job: SearchJob) -> dict[str, str]:
    return {
        "Made-in-China": made_in_china_finished_product_keyword(
            job.product_keyword,
            job.keyword_expansion.english_keywords,
        ),
        "1688": china_1688_finished_product_keyword(
            job.product_keyword,
            job.keyword_expansion.chinese_keywords,
            job.supplier_preference,
        ),
    }


def _append_features(keyword: str, product_features: str | None, platform: str | None = None) -> str:
    if platform == "Made-in-China":
        features = made_in_china_feature_terms(product_features)
    else:
        features = " ".join((product_features or "").split())
    if not features:
        return keyword
    normalized_keyword = keyword.lower()
    if features.lower() in normalized_keyword:
        return keyword
    if platform == "Made-in-China":
        feature_parts = [part for part in features.split() if part.lower() not in normalized_keyword]
        if not feature_parts:
            return keyword
        return f"{keyword} {' '.join(feature_parts)}"
    return f"{keyword} {features}"


def _platform_supplier_groups(
    listings,
    product_keyword: str,
    product_features: str | None,
    platform_keywords: dict[str, str],
    target_price: float | None,
    moq_preference: int | None,
    supplier_preference: str | None,
) -> list[dict]:
    groups = []
    for platform in ("Made-in-China", "1688"):
        platform_listings = [listing for listing in listings if listing.platform == platform]
        suppliers = deduplicate_suppliers(
            platform_listings,
            limit=5,
            product_keyword=platform_keywords.get(platform, product_keyword),
            product_features=product_features,
            target_price=target_price,
            moq_preference=moq_preference,
            supplier_preference=supplier_preference,
        )
        groups.append(
            {
                "platform": platform,
                "suppliers": [supplier.model_dump(mode="json") for supplier in suppliers],
            }
        )
    return groups


def _platform_diagnostics(
    listings,
    platform_supplier_groups: list[dict],
    platform_keywords: dict[str, str],
    failures: list[dict],
) -> list[dict]:
    diagnostics = []
    for group in platform_supplier_groups:
        platform = group["platform"]
        failure = next((item for item in failures if item.get("platform") == platform), None)
        diagnostics.append(
            {
                "platform": platform,
                "searched_keyword": platform_keywords.get(platform),
                "raw_listing_count": sum(1 for listing in listings if listing.platform == platform),
                "unique_supplier_count": len(group["suppliers"]),
                "failure": failure,
            }
        )
    return diagnostics
