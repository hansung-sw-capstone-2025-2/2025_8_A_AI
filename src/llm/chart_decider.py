from typing import Dict, Any, Tuple, Optional, List
from pydantic import BaseModel, Field
import json
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from src.core.config import settings
from .client import LLMClientFactory


class SubChartInfo(BaseModel):
    metric: str
    reasoning: str


class ChartDecision(BaseModel):
    main_metric: str
    main_title: str
    reasoning: str
    confidence: float = Field(ge=0, le=1)
    sub_charts: List[SubChartInfo] = Field(max_length=2)


class ChartDecider:
    METRIC_TITLES = {
        "car_brand": "차량 브랜드 분포",
        "phone_brand": "휴대폰 브랜드 분포",
        "occupation": "직업 분포",
        "region": "지역 분포",
        "age_group": "연령대 분포",
        "gender": "성별 분포",
        "marital_status": "결혼 여부 분포",
        "device_count": "전자기기 보유 개수 분포",
        "income": "소득 분포",
        "education": "학력 분포",
    }

    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm
        if use_llm:
            self.llm = LLMClientFactory.create_sonnet(max_tokens=500)
            self.parser = PydanticOutputParser(pydantic_object=ChartDecision)
            self.prompt = self._create_prompt()

    def _create_prompt(self) -> PromptTemplate:
        prompt_path = settings.prompts_dir / "decide_main_chart.md"
        template = prompt_path.read_text(encoding="utf-8")

        return PromptTemplate(
            template=template,
            input_variables=["original_query", "query_filters", "cohort_stats_summary", "format_instructions"]
        )

    async def decide_main_chart(
        self,
        original_query: Optional[str],
        query_filter: dict,
        cohort_stats: Dict[str, Any]
    ) -> Tuple[str, str, Optional[str]]:
        if not self.use_llm or not original_query:
            return self._rule_based_decision(query_filter, cohort_stats)

        try:
            return await self._llm_based_decision(original_query, query_filter, cohort_stats)
        except Exception:
            return self._rule_based_decision(query_filter, cohort_stats)

    async def _llm_based_decision(
        self,
        original_query: str,
        query_filter: dict,
        cohort_stats: Dict[str, Any]
    ) -> Tuple[str, str, str]:
        filters_summary = {k: v for k, v in query_filter.items() if v is not None and k != 'limit'}

        stats_summary = {}
        for metric, data in cohort_stats.items():
            if isinstance(data, dict):
                stats_summary[metric] = {
                    "categories": len(data),
                    "top_3": list(data.items())[:3],
                    "total": sum(data.values()) if all(isinstance(v, (int, float)) for v in data.values()) else None
                }

        chain = self.prompt | self.llm | self.parser
        result = chain.invoke({
            "original_query": original_query,
            "query_filters": json.dumps(filters_summary, ensure_ascii=False, indent=2),
            "cohort_stats_summary": json.dumps(stats_summary, ensure_ascii=False, indent=2),
            "format_instructions": self.parser.get_format_instructions()
        })

        return result.main_metric, result.main_title, result.reasoning

    def _rule_based_decision(
        self,
        query_filter: dict,
        cohort_stats: Dict[str, Any]
    ) -> Tuple[str, str, str]:
        METRIC_PRIORITY_MAP = {
            "brands": ("car_brand", 1, "차량 브랜드 분포"),
            "occupation": ("occupation", 2, "직업 분포"),
            "device_count_min": ("device_count", 3, "전자기기 보유 개수"),
        }

        DEFAULT_PRIORITY = [
            ("occupation", "직업 분포"),
            ("marital_status", "결혼 여부"),
            ("phone_brand", "휴대폰 브랜드"),
            ("car_brand", "차량 브랜드"),
            ("gender", "성별 분포")
        ]

        for field, (metric, priority, title) in METRIC_PRIORITY_MAP.items():
            field_value = query_filter.get(field)
            if field_value is not None:
                if metric in cohort_stats and cohort_stats[metric]:
                    return metric, title, f"{field} 필터 조건 기반 (우선순위 {priority})"

        for metric, title in DEFAULT_PRIORITY:
            if metric in cohort_stats and cohort_stats[metric]:
                return metric, title, "기본 우선순위 기반"

        return "age_group", "연령대 분포", "기본값"

    async def get_all_chart_metrics(
        self,
        original_query: Optional[str],
        query_filter: dict,
        cohort_stats: Dict[str, Any],
        max_charts: int = 3
    ) -> Dict[str, Any]:
        main_metric, main_title, reasoning = await self.decide_main_chart(
            original_query, query_filter, cohort_stats
        )

        if not self._is_valid_for_chart(cohort_stats.get(main_metric)):
            valid_metrics = [
                (metric, data)
                for metric, data in cohort_stats.items()
                if self._is_valid_for_chart(data)
            ]

            if valid_metrics:
                main_metric = max(valid_metrics, key=lambda x: len(x[1]))[0]
                main_title = self.METRIC_TITLES.get(main_metric, f"{main_metric} 분포")
                reasoning = "원본 메트릭이 유효하지 않아 대안으로 선택됨"
            else:
                raise ValueError("차트 생성 가능한 메트릭이 없습니다")

        sub_metrics = self._get_sub_charts_rule_based(main_metric, cohort_stats, max_charts)

        return {
            "main": {"metric": main_metric, "title": main_title, "reasoning": reasoning},
            "subs": sub_metrics
        }

    def _is_valid_for_chart(self, data: Any) -> bool:
        if isinstance(data, dict):
            return len(data) >= 2
        elif isinstance(data, list):
            return len(data) >= 2
        return False

    def _get_sub_charts_rule_based(
        self,
        main_metric: str,
        cohort_stats: Dict[str, Any],
        max_charts: int
    ) -> List[Dict[str, str]]:
        DEFAULT_PRIORITY = [
            "occupation", "region", "car_brand", "marital_status",
            "phone_brand", "age_group", "gender", "device_count", "income", "residence"
        ]

        sub_charts = []
        for metric in DEFAULT_PRIORITY:
            if metric == main_metric:
                continue

            if metric in cohort_stats and self._is_valid_for_chart(cohort_stats[metric]):
                data = cohort_stats[metric]
                reasoning = self._generate_reasoning(metric, data)
                sub_charts.append({
                    "metric": metric,
                    "title": self.METRIC_TITLES.get(metric, f"{metric} 분포"),
                    "reasoning": reasoning
                })

            if len(sub_charts) >= max_charts - 1:
                break

        return sub_charts

    def _generate_reasoning(self, metric: str, data: Dict[str, int]) -> str:
        num_categories = len(data)
        sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)
        top_item = sorted_items[0] if sorted_items else None

        templates = {
            "occupation": f"{num_categories}개 직업군 중 '{top_item[0]}'이 {top_item[1]}명으로 가장 많음" if top_item else "직업 분포",
            "region": f"{num_categories}개 지역으로 분산되어 지��별 타겟팅에 유용",
            "residence": f"{num_categories}개 거주지로 분산되어 생활권 타겟팅 가능",
            "car_brand": f"차량 브랜드 {num_categories}개로 소비 성향 확인 가능",
            "phone_brand": f"'{top_item[0]}' {top_item[1]}명으로 기술 친화도 파악" if top_item else "휴대폰 브랜드 분포",
            "marital_status": "결혼 여부로 라이프스타일 단계 파악",
            "age_group": f"{num_categories}개 연령대로 세대 다양성 확인",
            "gender": "성별 분포로 타겟 그룹 특성 파악",
        }

        return templates.get(metric, f"{self.METRIC_TITLES.get(metric, metric)} 분석")
