from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import date

from .enums import SearchMode


class Panel(BaseModel):
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


class SearchFilter(BaseModel):
    age_group: Optional[Union[str, List[str]]] = None
    gender: Optional[str] = None
    region: Optional[Union[str, List[str]]] = None
    occupation: Optional[List[str]] = None
    income_min: Optional[int] = None
    income_max: Optional[int] = None
    marital_status: Optional[str] = None
    lifestyle_tags: Optional[List[str]] = None
    search_keywords: Optional[List[str]] = None
    device_count_min: Optional[int] = None
    brands: Optional[List[str]] = None
    phone_brand: Optional[List[str]] = None
    car_brand: Optional[List[str]] = None
    survey_health: Optional[Dict[str, Any]] = None
    survey_consumption: Optional[Dict[str, Any]] = None
    survey_lifestyle: Optional[Dict[str, Any]] = None
    survey_digital: Optional[Dict[str, Any]] = None
    limit: int = Field(default=100, ge=1, le=1000)

    class Config:
        json_schema_extra = {
            "example": {
                "age_group": "40대",
                "gender": "여성",
                "region": "서울",
                "occupation": ["전문직"],
                "limit": 100
            }
        }


class Cohort(BaseModel):
    cohort_id: str
    cohort_name: str
    panel_count: int
    panel_ids: List[str] = []
    created_at: Optional[str] = None


class SearchHistory(BaseModel):
    id: int
    member_id: Optional[int] = None
    content: str
    panel_ids: List[str] = []
    concordance_rate: List[float] = []
    date: Optional[date] = None
