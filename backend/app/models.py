from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class SupplierPreference(StrEnum):
    FACTORY_ONLY = "Factory Only"
    FACTORY_PREFERRED = "Factory Preferred"
    ANY_SUPPLIER = "Any Supplier"


class SearchJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    PARTIALLY_COMPLETED = "partially_completed"
    COMPLETED = "completed"
    FAILED = "failed"


class SearchJobCreate(BaseModel):
    product_keyword: str = Field(min_length=1, max_length=120)
    target_price: float | None = Field(default=None, gt=0)
    moq_preference: int | None = Field(default=None, gt=0)
    supplier_preference: SupplierPreference = SupplierPreference.FACTORY_PREFERRED
    product_image_id: str | None = None


class KeywordExpansion(BaseModel):
    english_keywords: list[str]
    chinese_keywords: list[str]
    variation_keywords: list[str]
    confidence: float = Field(ge=0, le=1)
    source: Literal["deterministic_v1", "openai_compatible"]


class SearchProgress(BaseModel):
    stage: str
    message: str


class SearchJob(BaseModel):
    job_id: str
    product_keyword: str
    target_price: float | None
    moq_preference: int | None
    supplier_preference: SupplierPreference
    status: SearchJobStatus
    progress: SearchProgress
    keyword_expansion: KeywordExpansion
    created_at: datetime
    updated_at: datetime
    error_summary: str | None = None


class RawListingsResponse(BaseModel):
    job_id: str
    status: str
    listings: list[dict[str, Any]]
    failures: list[dict[str, Any]]


class SuppliersResponse(BaseModel):
    job_id: str
    status: str
    suppliers: list[dict[str, Any]]
    platform_supplier_groups: list[dict[str, Any]] = Field(default_factory=list)
    failures: list[dict[str, Any]]
    cache_version: int | None = None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
