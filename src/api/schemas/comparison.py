from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ComparisonRequest(BaseModel):
    cohort_1_id: int
    cohort_2_id: int
    metrics: Optional[List[str]] = None


class CohortBasicInfo(BaseModel):
    cohort_id: str
    cohort_name: str
    panel_count: int
    created_at: Optional[str] = None


class MetricComparison(BaseModel):
    metric_name: str
    metric_label: str
    cohort_1_data: Dict[str, int]
    cohort_2_data: Dict[str, int]
    cohort_1_percentage: Dict[str, float]
    cohort_2_percentage: Dict[str, float]
    statistical_test: Optional[Dict[str, Any]] = None


class BasicInfoComparison(BaseModel):
    metric_name: str
    metric_label: str
    cohort_1_value: Optional[float] = None
    cohort_2_value: Optional[float] = None
    difference: Optional[float] = None
    difference_percentage: Optional[float] = None


class CharacteristicComparison(BaseModel):
    characteristic: str
    cohort_1_percentage: float
    cohort_2_percentage: float
    cohort_1_count: int
    cohort_2_count: int
    difference_percentage: float


class KeyInsights(BaseModel):
    main_differences: str
    commonalities: str
    implications: str


class RegionDistribution(BaseModel):
    cohort_1: Dict[str, float]
    cohort_2: Dict[str, float]


class GenderDistribution(BaseModel):
    cohort_1: Dict[str, float]
    cohort_2: Dict[str, float]


class ComparisonResponse(BaseModel):
    cohort_1: CohortBasicInfo
    cohort_2: CohortBasicInfo
    comparisons: List[MetricComparison]
    basic_info: List[BasicInfoComparison] = []
    characteristics: List[CharacteristicComparison] = []
    region_distribution: Optional[RegionDistribution] = None
    gender_distribution: Optional[GenderDistribution] = None
    key_insights: Optional[KeyInsights] = None
    summary: Dict[str, Any]
