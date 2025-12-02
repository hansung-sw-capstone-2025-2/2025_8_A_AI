from typing import Dict, Any, List, Optional
import re
import random

from src.llm import InsightGenerator
from src.repositories import SearchHistoryRepository


INDUSTRY_TO_JOB_MAPPING = {
    "IT,인터넷,소프트웨어": "IT/개발/데이터",
    "전자,제조,기계": "생산/제조/품질",
    "금융,보험,핀테크": "금융/회계/법률",
    "유통,소비재,식품": "서비스/유통",
    "문화,미디어,엔터테인먼트": "디자인/미디어",
    "의료,제약,바이오": "의료/보건/복지",
    "교육,에듀테크": "교육/컨설팅",
    "공공,비영리,행정": "경영/기획/전략",
    "건설,부동산,인프라": "경영/기획/전략",
    "에너지,환경,화학": "연구/R&D",
    "관광,여행,항공": "서비스/유통",
    "기타 산업군": "기타/프리랜서",
    "마케팅/광고/홍보": "마케팅/광고/홍보",
    "IT/개발/데이터": "IT/개발/데이터",
    "영업/고객관리": "영업/고객관리",
    "의료/보건/복지": "의료/보건/복지",
    "교육/컨설팅": "교육/컨설팅",
    "디자인/미디어": "디자인/미디어",
    "경영/기획/전략": "경영/기획/전략",
    "생산/제조/품질": "생산/제조/품질",
    "연구/R&D": "연구/R&D",
    "금융/회계/법률": "금융/회계/법률",
    "서비스/유통": "서비스/유통",
    "기타/프리랜서": "기타/프리랜서",
}

INDUSTRY_RECOMMENDATIONS = {
    "마케팅/광고/홍보": [
        {"query": "20대 30대 여성 300명", "category": "연령대"},
        {"query": "서울 경기 거주 사무직 200명", "category": "지역"},
        {"query": "아이폰 사용자 150명", "category": "브랜드"},
        {"query": "30대 미혼 여성 100명", "category": "연령대"},
        {"query": "대학생 대학원생 100명", "category": "직업"},
        {"query": "20대 여성 서울 거주 200명", "category": "지역"},
    ],
    "IT/개발/데이터": [
        {"query": "전문직 20대 30대 남성 100명", "category": "직업"},
        {"query": "아이폰 사용자 전문직 150명", "category": "브랜드"},
        {"query": "경기 거주 사무직 전문직 200명", "category": "지역"},
        {"query": "20대 남성 대학생 100명", "category": "연령대"},
        {"query": "30대 남성 미혼 전문직 100명", "category": "직업"},
        {"query": "서울 경기 전문직 150명", "category": "지역"},
    ],
    "영업/고객관리": [
        {"query": "30대 40대 사무직 500명", "category": "연령대"},
        {"query": "차량 보유 기혼 남성 300명", "category": "브랜드"},
        {"query": "서울 경기 거주 사무직 400명", "category": "지역"},
        {"query": "40대 기혼 남성 200명", "category": "연령대"},
        {"query": "현대 기아 차량 보유 200명", "category": "브랜드"},
        {"query": "경영 관리직 50명", "category": "직업"},
    ],
    "의료/보건/복지": [
        {"query": "의료 간호 보건 복지 전문직 100명", "category": "직업"},
        {"query": "30대 40대 전문직 여성 150명", "category": "연령대"},
        {"query": "서울 경기 전문직 200명", "category": "지역"},
        {"query": "기혼 전문직 100명", "category": "직업"},
        {"query": "40대 여성 기혼 200명", "category": "연령대"},
        {"query": "전문직 월 500만원 이상 100명", "category": "소득"},
    ],
    "교육/컨설팅": [
        {"query": "대학생 대학원생 200명", "category": "직업"},
        {"query": "교직 교사 강사 100명", "category": "직업"},
        {"query": "20대 미혼 대학생 150명", "category": "연령대"},
        {"query": "전문직 사무직 200명", "category": "직업"},
        {"query": "서울 경기 대학생 100명", "category": "지역"},
        {"query": "30대 40대 기혼 자녀 있음 200명", "category": "가족"},
    ],
    "디자인/미디어": [
        {"query": "20대 30대 전문직 150명", "category": "연령대"},
        {"query": "아이폰 사용자 20대 30대 200명", "category": "브랜드"},
        {"query": "서울 거주 전문직 사무직 150명", "category": "지역"},
        {"query": "미혼 20대 30대 200명", "category": "연령대"},
        {"query": "대학생 대학원생 100명", "category": "직업"},
        {"query": "경기 서울 거주 150명", "category": "지역"},
    ],
    "경영/기획/전략": [
        {"query": "30대 40대 사무직 관리직 200명", "category": "연령대"},
        {"query": "경영 관리직 100명", "category": "직업"},
        {"query": "월 500만원 이상 전문직 150명", "category": "소득"},
        {"query": "서울 경기 사무직 400명", "category": "지역"},
        {"query": "40대 기혼 남성 사무직 200명", "category": "연령대"},
        {"query": "BMW 벤츠 제네시스 보유 50명", "category": "브랜드"},
    ],
    "생산/제조/품질": [
        {"query": "30대 40대 남성 생산 노무직 400명", "category": "연령대"},
        {"query": "생산 정비 기능 노무 200명", "category": "직업"},
        {"query": "경기 인천 거주 300명", "category": "지역"},
        {"query": "차량 보유 기혼 남성 300명", "category": "브랜드"},
        {"query": "40대 50대 기혼 남성 200명", "category": "연령대"},
        {"query": "현대 기아 차량 보유 250명", "category": "브랜드"},
    ],
    "연구/R&D": [
        {"query": "전문직 30대 40대 150명", "category": "직업"},
        {"query": "대학교 졸업 이상 전문직 200명", "category": "학력"},
        {"query": "아이폰 사용자 전문직 150명", "category": "브랜드"},
        {"query": "서울 경기 전문직 사무직 200명", "category": "지역"},
        {"query": "30대 남성 전문직 100명", "category": "연령대"},
        {"query": "전자 기계 기술 연구개발 100명", "category": "직업"},
    ],
    "금융/회계/법률": [
        {"query": "전문직 30대 40대 200명", "category": "직업"},
        {"query": "월 500만원 이상 150명", "category": "소득"},
        {"query": "서울 거주 사무직 전문직 150명", "category": "지역"},
        {"query": "재무 회계 경리 100명", "category": "직업"},
        {"query": "대학교 졸업 이상 250명", "category": "학력"},
        {"query": "BMW 벤츠 제네시스 보유 50명", "category": "브랜드"},
    ],
    "서비스/유통": [
        {"query": "20대 30대 여성 300명", "category": "연령대"},
        {"query": "전업주부 200명", "category": "직업"},
        {"query": "서울 경기 거주 400명", "category": "지역"},
        {"query": "서비스직 200명", "category": "직업"},
        {"query": "유통 물류 운송 150명", "category": "직업"},
        {"query": "무역 영업 판매 매장관리 150명", "category": "직업"},
    ],
    "기타/프리랜서": [
        {"query": "20대 남성 100명", "category": "연령대"},
        {"query": "30대 여성 150명", "category": "연령대"},
        {"query": "서울 거주 200명", "category": "지역"},
        {"query": "아이폰 사용자 300명", "category": "브랜드"},
        {"query": "자영업 150명", "category": "직업"},
        {"query": "미혼 20대 30대 200명", "category": "연령대"},
    ],
}


class RecommendationService:
    def __init__(self):
        self.insight_generator = InsightGenerator()
        self.search_history_repo = SearchHistoryRepository()

    async def get_recommendations(
        self,
        search_history: Optional[List[str]] = None,
        industry: str = "마케팅/광고/홍보",
        limit: int = 6
    ) -> Dict[str, Any]:
        if not search_history or len(search_history) == 0:
            return self._get_static_recommendations(limit, industry)

        try:
            patterns = self.insight_generator.extract_patterns(search_history)
        except Exception:
            patterns = {}

        if len(search_history) <= 2 or len(patterns) < 2:
            recommendations = self._filter_by_patterns(patterns, limit, industry)
            return {
                "recommendations": self._format_recommendations(recommendations, industry),
                "strategy": "pattern",
                "total": len(recommendations),
                "patterns": patterns,
                "industry": industry
            }

        try:
            recommendations = self.insight_generator.generate_recommendations(
                search_history, patterns
            )

            if not recommendations:
                raise Exception("LLM returned empty")

            return {
                "recommendations": self._format_recommendations(recommendations, industry),
                "strategy": "llm",
                "total": len(recommendations),
                "patterns": patterns,
                "industry": industry
            }

        except Exception:
            recommendations = self._filter_by_patterns(patterns, limit, industry)
            return {
                "recommendations": self._format_recommendations(recommendations, industry),
                "strategy": "pattern_fallback",
                "total": len(recommendations),
                "patterns": patterns,
                "industry": industry
            }

    async def get_recommendations_by_member(
        self,
        member_id: int,
        industry: str = "마케팅/광고/홍보",
        limit: int = 6
    ) -> Dict[str, Any]:
        search_history = await self.search_history_repo.get_recent_queries(member_id)
        return await self.get_recommendations(search_history, industry, limit)

    def _get_static_recommendations(self, limit: int, industry: str) -> Dict[str, Any]:
        random.seed(None)
        mapped_industry = INDUSTRY_TO_JOB_MAPPING.get(industry, industry)

        recommendations = INDUSTRY_RECOMMENDATIONS.get(
            mapped_industry,
            INDUSTRY_RECOMMENDATIONS.get("마케팅/광고/홍보", [])
        )

        if not recommendations:
            recommendations = INDUSTRY_RECOMMENDATIONS["마케팅/광고/홍보"]

        if len(recommendations) > limit:
            shuffled = list(recommendations)
            random.shuffle(shuffled)
            recommendations = shuffled[:limit]
        else:
            recommendations = list(recommendations)

        return {
            "recommendations": self._format_recommendations(recommendations, industry),
            "strategy": "static_industry",
            "total": len(recommendations),
            "industry": industry,
            "mapped_job": mapped_industry
        }

    def _filter_by_patterns(
        self,
        patterns: Dict[str, Dict[str, List[str]]],
        limit: int,
        industry: str
    ) -> List[Dict[str, Any]]:
        mapped_industry = INDUSTRY_TO_JOB_MAPPING.get(industry, industry)
        industry_recs = INDUSTRY_RECOMMENDATIONS.get(
            mapped_industry,
            INDUSTRY_RECOMMENDATIONS.get("마케팅/광고/홍보", [])
        )

        scored = []
        for rec in industry_recs:
            score = 0
            query_lower = rec['query'].lower()

            for category, field_dict in patterns.items():
                for _, value_list in field_dict.items():
                    for value in value_list:
                        if value.lower() in query_lower:
                            score += 10
                        elif self._is_similar(value, query_lower):
                            score += 5

            scored.append((score, rec))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [rec for score, rec in scored[:limit]]

    def _is_similar(self, pattern: str, query: str) -> bool:
        if pattern in ["20대", "30대"] and any(age in query for age in ["20대", "30대"]):
            return True
        if pattern in ["40대", "50대"] and any(age in query for age in ["40대", "50대"]):
            return True
        if pattern == "서울" and "경기" in query:
            return True
        return False

    def _format_recommendations(
        self,
        recommendations: List[Dict],
        industry: str = None
    ) -> List[Dict]:
        formatted = []
        description = f"{industry} 전용 추천" if industry else "추천 쿼리"

        for idx, rec in enumerate(recommendations, 1):
            query_text = rec['query']
            count_from_query = self._extract_count_from_query(query_text)

            search_params = rec.get('search_params')
            if not search_params:
                search_params = self._extract_search_params(query_text)

            formatted.append({
                "id": idx,
                "query": rec['query'],
                "count": f"약 {count_from_query:,}명" if count_from_query else None,
                "description": rec.get('reason', description),
                "category": rec['category'],
                "personalized": rec.get('personalized', False),
                "search_params": search_params,
                "recommended_mode": "flexible"
            })

        return formatted

    def _extract_count_from_query(self, query: str) -> Optional[int]:
        match = re.search(r'(\d+)\s*명', query)
        if match:
            return int(match.group(1))
        return None

    def _extract_search_params(self, query: str) -> Dict[str, Any]:
        params = {}

        age_groups = ["10대", "20대", "30대", "40대", "50대", "60대"]
        for age in age_groups:
            if age in query:
                params["age_group"] = age
                break

        if "남성" in query:
            params["gender"] = "남성"
        elif "여성" in query:
            params["gender"] = "여성"

        regions = ["서울", "경기", "인천", "부산", "대구", "광주", "대전", "울산", "세종"]
        for region in regions:
            if region in query:
                params["region"] = region
                break

        occupations = {
            "전문직": "전문직", "사무직": "사무직", "대학생": "학생",
            "학생": "학생", "주부": "주부", "개발자": "전문직",
            "의료": "전문직", "간호": "전문직", "교사": "전문직", "강사": "전문직",
        }
        for keyword, occupation in occupations.items():
            if keyword in query:
                if "occupation" not in params:
                    params["occupation"] = []
                if occupation not in params["occupation"]:
                    params["occupation"].append(occupation)

        if "기혼" in query:
            params["marital_status"] = "기혼"
        elif "미혼" in query:
            params["marital_status"] = "미혼"

        brands = ["아이폰", "삼성", "갤럭시", "BMW", "벤츠", "현대", "기아", "테슬라", "제네시스"]
        found_brands = [brand for brand in brands if brand in query]
        if found_brands:
            params["brands"] = found_brands

        count_match = re.search(r'(\d+)\s*명', query)
        if count_match:
            params["limit"] = int(count_match.group(1))

        income_match = re.search(r'(\d+)\s*만원\s*이상', query)
        if income_match:
            params["income_min"] = int(income_match.group(1))

        return params
