from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    member_id: Optional[int] = Field(default=None)
    search_history: Optional[List[str]] = Field(default=None)
    industry: str = Field(default="마케팅/광고/홍보")
    limit: int = Field(default=6, ge=1, le=20)


class PersonalizedRecommendation(BaseModel):
    id: int
    query: str
    count: Optional[str] = None
    description: str
    category: str
    personalized: bool = False
    search_params: Dict[str, Any] = {}
    recommended_mode: str = "flexible"


class RecommendationResponse(BaseModel):
    recommendations: List[PersonalizedRecommendation]
    strategy: str
    total: int
    patterns: Optional[Dict[str, Any]] = None
    industry: str
    mapped_job: Optional[str] = None
