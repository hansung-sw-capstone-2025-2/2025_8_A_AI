from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import json
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from src.core.config import settings
from .client import LLMClientFactory


class KeyInsights(BaseModel):
    main_differences: str
    commonalities: str
    implications: str


class ExtractedPatterns(BaseModel):
    demographic: Dict[str, List[str]] = Field(default={})
    occupation: Dict[str, List[str]] = Field(default={})
    brand: Dict[str, List[str]] = Field(default={})
    survey_health: Dict[str, List[str]] = Field(default={})
    survey_digital: Dict[str, List[str]] = Field(default={})
    survey_lifestyle: Dict[str, List[str]] = Field(default={})
    survey_consumption: Dict[str, List[str]] = Field(default={})


class PersonalizedRecommendationItem(BaseModel):
    query: str
    reason: str
    estimated_count: int
    category: str
    search_params: Dict[str, Any]


class RecommendationList(BaseModel):
    recommendations: List[PersonalizedRecommendationItem]


class InsightGenerator:
    def __init__(self):
        self.llm = LLMClientFactory.create_sonnet(temperature=0.3)

    async def generate_cohort_insights(
        self,
        cohort_1_info: dict,
        cohort_2_info: dict,
        comparisons: List[dict],
        basic_info: List[dict],
        characteristics: List[dict]
    ) -> Optional[KeyInsights]:
        input_data = {
            "cohort_1": cohort_1_info,
            "cohort_2": cohort_2_info,
            "comparisons": comparisons,
            "basic_info": basic_info,
            "characteristics": characteristics
        }

        prompt_path = settings.prompts_dir / "analyze_cohort_insights.md"
        if not prompt_path.exists():
            return None

        prompt_template_str = prompt_path.read_text(encoding="utf-8")
        escaped_prompt = prompt_template_str.replace("{", "{{").replace("}", "}}")

        prompt_template = PromptTemplate(
            template=escaped_prompt + "\n\n{input_json}\n\n",
            input_variables=["input_json"]
        )

        parser = PydanticOutputParser(pydantic_object=KeyInsights)
        chain = prompt_template | self.llm | parser

        result = await chain.ainvoke({
            "input_json": json.dumps(input_data, ensure_ascii=False, indent=2)
        })

        return result

    def extract_patterns(self, queries: List[str]) -> Dict[str, Any]:
        prompt_path = settings.prompts_dir / "extract_patterns.md"
        template = prompt_path.read_text(encoding="utf-8")

        prompt = PromptTemplate(
            template=template,
            input_variables=["search_history", "format_instructions"]
        )

        parser = PydanticOutputParser(pydantic_object=ExtractedPatterns)
        llm = LLMClientFactory.create_haiku(max_tokens=2000)
        chain = prompt | llm | parser

        history_str = "\n".join([f"- {q}" for q in queries])
        result = chain.invoke({
            "search_history": history_str,
            "format_instructions": parser.get_format_instructions()
        })

        patterns = {}
        for category in ['demographic', 'occupation', 'brand', 'survey_health', 'survey_digital', 'survey_lifestyle', 'survey_consumption']:
            category_data = getattr(result, category, {})
            if category_data:
                patterns[category] = category_data

        return patterns

    def generate_recommendations(
        self,
        search_history: List[str],
        patterns: Dict[str, List[str]]
    ) -> List[Dict[str, Any]]:
        prompt_path = settings.prompts_dir / "generate_personalized_recommendations.md"
        template = prompt_path.read_text(encoding="utf-8")

        prompt = PromptTemplate(
            template=template,
            input_variables=["search_history", "patterns", "format_instructions"]
        )

        parser = PydanticOutputParser(pydantic_object=RecommendationList)
        chain = prompt | self.llm | parser

        history_str = "\n".join([f"- {q}" for q in search_history])
        patterns_str = "\n".join([f"- {k}: {', '.join(v)}" for k, v in patterns.items()])

        result = chain.invoke({
            "search_history": history_str,
            "patterns": patterns_str,
            "format_instructions": parser.get_format_instructions()
        })

        recommendations = []
        for rec in result.recommendations:
            recommendations.append({
                "query": rec.query,
                "category": rec.category,
                "count": rec.estimated_count,
                "reason": rec.reason,
                "personalized": True,
                "search_params": rec.search_params
            })

        return recommendations
