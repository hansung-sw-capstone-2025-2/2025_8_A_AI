from typing import Optional, List
from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.services import RecommendationService


router = APIRouter(prefix="/api/quick-search", tags=["recommendations"])
recommendation_service = RecommendationService()


class RecommendationRequest(BaseModel):
    member_id: Optional[int] = Field(default=None)
    search_history: Optional[List[str]] = Field(default=None)
    industry: str = Field(default="마케팅/광고/홍보")
    limit: int = Field(default=6, ge=1, le=20)


class MemberRecommendationRequest(BaseModel):
    member_id: int
    industry: str = Field(default="마케팅/광고/홍보")
    limit: int = Field(default=6, ge=1, le=20)


@router.post("/recommendations")
async def get_recommendations(request: RecommendationRequest):
    return await recommendation_service.get_recommendations(
        search_history=request.search_history,
        industry=request.industry,
        limit=request.limit
    )


@router.post("/recommendations/by-member")
async def get_recommendations_by_member(request: MemberRecommendationRequest):
    return await recommendation_service.get_recommendations_by_member(
        member_id=request.member_id,
        industry=request.industry,
        limit=request.limit
    )


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "recommendations"}
