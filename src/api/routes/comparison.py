from typing import Optional, List
from fastapi import APIRouter, HTTPException

from src.services import ComparisonService
from src.core.exceptions import NotFoundError
from src.api.schemas.comparison import ComparisonResponse


router = APIRouter(prefix="/api/cohort-comparison", tags=["comparison"])
comparison_service = ComparisonService()


@router.post("/compare", response_model=ComparisonResponse)
async def compare_two_cohorts(
    cohort_1_id: int,
    cohort_2_id: int,
    metrics: Optional[List[str]] = None
):
    try:
        result = await comparison_service.compare_cohorts(
            cohort_1_id=cohort_1_id,
            cohort_2_id=cohort_2_id,
            metrics=metrics
        )
        return ComparisonResponse(**result)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.get("/metrics")
async def get_available_metrics():
    return {"metrics": comparison_service.get_available_metrics()}
