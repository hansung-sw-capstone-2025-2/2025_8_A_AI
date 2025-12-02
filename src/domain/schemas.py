from typing import List
from pydantic import BaseModel, Field, field_validator


class PanelProfileSchema(BaseModel):
    profile_summary: str = Field(
        min_length=50,
        max_length=600,
        description="패널의 전체적인 프로필 요약 (200-400자)"
    )
    demographic_summary: str = Field(
        min_length=10,
        max_length=150,
        description="인구통계학적 특성 요약"
    )
    lifestyle_summary: str = Field(
        max_length=300,
        description="라이프스타일 패턴 요약"
    )
    consumption_summary: str = Field(
        max_length=200,
        description="소비 성향 요약"
    )
    key_characteristics: List[str] = Field(
        max_length=5,
        description="핵심 특징 (최대 5개)"
    )
    search_keywords: List[str] = Field(
        min_length=3,
        max_length=20,
        description="검색 키워드 (3-20개)"
    )
    lifestyle_tags: List[str] = Field(
        max_length=15,
        description="라이프스타일 태그"
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="프로필 완성도 점수 (0-1)"
    )
    missing_fields: List[str] = Field(
        default_factory=list,
        description="누락된 주요 필드"
    )

    @field_validator('search_keywords')
    @classmethod
    def validate_keywords(cls, v):
        return list(dict.fromkeys(v))


class HashtagSchema(BaseModel):
    primary_hashtags: List[str] = Field(
        min_length=5,
        max_length=7,
        description="핵심 해시태그 5-7개"
    )
    demographic_hashtags: List[str] = Field(
        min_length=3,
        max_length=5,
        description="인구통계 해시태그 3-5개"
    )
    lifestyle_hashtags: List[str] = Field(
        min_length=5,
        max_length=8,
        description="라이프스타일 해시태그 5-8개"
    )
    brand_hashtags: List[str] = Field(
        min_length=0,
        max_length=6,
        description="브랜드/제품 해시태그 3-6개"
    )
    trending_hashtags: List[str] = Field(
        min_length=2,
        max_length=4,
        description="트렌드 해시태그 2-4개"
    )
    long_tail_hashtags: List[str] = Field(
        min_length=3,
        max_length=5,
        description="롱테일 해시태그 3-5개"
    )
    campaign_suggestions: List[str] = Field(
        min_length=2,
        max_length=3,
        description="캠페인 제안 해시태그 2-3개"
    )

    @field_validator('primary_hashtags', 'demographic_hashtags', 'lifestyle_hashtags',
                     'brand_hashtags', 'trending_hashtags', 'long_tail_hashtags',
                     'campaign_suggestions')
    @classmethod
    def validate_hashtags(cls, v):
        validated = []
        for tag in v:
            if not tag.startswith('#'):
                tag = f'#{tag}'
            tag = tag.strip()
            if 2 <= len(tag) <= 20:
                validated.append(tag)
        return list(dict.fromkeys(validated))
