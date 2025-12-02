from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class MainSearchRequest(BaseModel):
    member_id: Optional[int] = Field(default=None)
    query: Optional[str] = Field(default=None)
    search_params: Optional[Dict[str, Any]] = Field(default=None)
    structured_filters: Optional[Dict[str, Any]] = Field(default=None)
    search_mode: str = Field(default="strict")
    limit: int = Field(default=100, ge=1, le=1000)


class PanelInfo(BaseModel):
    panel_id: str
    age: Optional[int] = None
    gender: Optional[str] = None
    residence: Optional[str] = None
    occupation: Optional[str] = None
    marital_status: Optional[str] = None
    phone_brand: Optional[str] = None
    car_brand: Optional[str] = None
    profile_summary: Optional[str] = None
    hashtags: Optional[List[str]] = None
    electronic_devices: Optional[List[str]] = None
    smoking_experience: Optional[List[str]] = None
    cigarette_brands: Optional[List[str]] = None
    e_cigarette: Optional[List[str]] = None
    drinking_experience: Optional[List[str]] = None
    survey_health: Optional[Dict[str, Any]] = None
    survey_consumption: Optional[Dict[str, Any]] = None
    survey_lifestyle: Optional[Dict[str, Any]] = None
    survey_digital: Optional[Dict[str, Any]] = None
    survey_environment: Optional[Dict[str, Any]] = None
    similarity: Optional[float] = None


class MainSearchResponse(BaseModel):
    search_id: str
    query: Optional[str] = None
    panels: List[PanelInfo]
    total_count: int
    search_mode: str
    applied_filters: Dict[str, Any]
    search_method: str


class RefineSearchRequest(BaseModel):
    additional_filters: Dict[str, Any]


class RefineSearchResponse(BaseModel):
    original_count: int
    filtered_count: int
    panels: List[PanelInfo]
    applied_filters: Dict[str, Any]


class SearchInfoResponse(BaseModel):
    search_id: str
    query: Optional[str] = None
    panel_count: int
    panel_ids: List[str]
    concordance_rates: List[float]
    panels_with_rates: List[Dict[str, Any]]
    created_at: Optional[str] = None


class AvailableFiltersResponse(BaseModel):
    filters: Dict[str, Any]
