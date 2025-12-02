from fastapi import APIRouter, HTTPException, Body

from src.services import SearchService
from src.api.schemas.search import (
    MainSearchRequest, MainSearchResponse,
    RefineSearchRequest, RefineSearchResponse
)


router = APIRouter(prefix="/api/search", tags=["search"])
search_service = SearchService()


@router.post("/", response_model=MainSearchResponse)
async def main_search(
    request: MainSearchRequest = Body(
        openapi_examples={
            "ui_basic": {
                "summary": "UI 기본 (검색어 + 필터)",
                "value": {
                    "query": "30대 여성 ChatGPT 사용자",
                    "structured_filters": {
                        "gender": "FEMALE",
                        "age_group": "30대",
                        "region": "서울",
                        "occupation": ["전문직", "사무직"]
                    },
                    "search_mode": "flexible",
                    "limit": 50
                }
            },
            "query_only": {
                "summary": "검색어만",
                "value": {
                    "query": "30대 서울 거주 여성",
                    "search_mode": "flexible",
                    "limit": 100
                }
            },
            "filter_only": {
                "summary": "필터만",
                "value": {
                    "structured_filters": {
                        "gender": "FEMALE",
                        "age_group": "30대"
                    },
                    "search_mode": "strict",
                    "limit": 100
                }
            },
            "multi_condition": {
                "summary": "복수 조건 (20대 남성 + 40대 여성)",
                "value": {
                    "query": "20대 남성 100명, 40대 여성 100명",
                    "search_mode": "strict",
                    "limit": 200
                }
            }
        }
    )
):
    try:
        result = await search_service.search(
            query=request.query,
            search_params=request.search_params,
            structured_filters=request.structured_filters,
            search_mode=request.search_mode,
            limit=request.limit,
            member_id=request.member_id
        )
        return MainSearchResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/search-result/{search_id}/refine", response_model=RefineSearchResponse)
async def refine_search(search_id: str, request: RefineSearchRequest):
    try:
        result = await search_service.refine_search(
            search_id=int(search_id),
            additional_filters=request.additional_filters
        )
        return RefineSearchResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/search-result/{search_id}/info")
async def get_search_info(search_id: str):
    try:
        return await search_service.get_search_info(int(search_id))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/available-filters")
async def get_available_filters():
    return {
        "filters": {
            "age_group": {
                "type": "select",
                "label": "연령대",
                "options": ["10대", "20대", "30대", "40대", "50대", "60대 이상"]
            },
            "gender": {
                "type": "select",
                "label": "성별",
                "options": ["MALE", "FEMALE"]
            },
            "residence": {
                "type": "select",
                "label": "거주 지역",
                "options": ["서울", "경기", "인천", "부산", "대구", "대전", "광주", "울산", "세종", "기타"]
            },
            "occupation": {
                "type": "multi-select",
                "label": "직업",
                "options": ["학생", "사무직", "전문직", "자영업", "주부", "개발자", "기술직", "서비스직", "기타"]
            },
            "marital_status": {
                "type": "select",
                "label": "결혼 여부",
                "options": ["미혼", "기혼", "이혼", "사별"]
            },
            "phone_brand": {
                "type": "multi-select",
                "label": "휴대폰 브랜드",
                "options": ["삼성", "애플", "LG", "기타"]
            },
            "car_brand": {
                "type": "multi-select",
                "label": "차량 브랜드",
                "options": ["현대", "기아", "제네시스", "벤츠", "BMW", "아우디", "테슬라", "기타", "없음"]
            },
            "income_range": {
                "type": "select",
                "label": "소득 구간",
                "options": ["0-200만원", "200-400만원", "400-600만원", "600-800만원", "800만원 이상"]
            },
            "education": {
                "type": "select",
                "label": "학력",
                "options": ["고졸 이하", "대학 재학/졸업", "석사", "박사"]
            }
        }
    }
