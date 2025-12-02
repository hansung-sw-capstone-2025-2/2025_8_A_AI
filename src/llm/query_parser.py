import json
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from src.core.config import settings
from src.domain.enums import SearchMode
from .client import LLMClientFactory


class QueryFilter(BaseModel):
    age_group: Any = Field(default=None)
    gender: str = Field(default=None)
    region: Any = Field(default=None)
    occupation: List[str] = Field(default=None)
    income_min: int = Field(default=None)
    income_max: int = Field(default=None)
    marital_status: str = Field(default=None)
    lifestyle_tags: List[str] = Field(default=None)
    search_keywords: List[str] = Field(default=None)
    device_count_min: int = Field(default=None)
    brands: List[str] = Field(default=None)
    phone_brand: List[str] = Field(default=None)
    car_brand: List[str] = Field(default=None)
    limit: int = Field(default=100, ge=1, le=1000)
    survey_health: Dict[str, Any] = Field(default=None)
    survey_consumption: Dict[str, Any] = Field(default=None)
    survey_lifestyle: Dict[str, Any] = Field(default=None)
    survey_digital: Dict[str, Any] = Field(default=None)


FREQUENCY_EXPANSION_MAP = {
    "혼밥빈도": {
        "high": ["거의 매일", "주 2~3회"],
        "medium": ["주 1회", "월 1~2회"],
        "low": ["하지 않"],
    },
    "OTT개수": {
        "high": ["3개", "4개 이상"],
        "medium": ["2개"],
        "low": ["1개"],
    },
    "전통시장": {
        "high": ["일주일에 1회", "2주에 1회"],
        "medium": ["한 달에 1회"],
        "low": ["3개월에 1회"],
    },
}

FREQUENCY_KEYWORDS = {
    "high": ["자주", "많이", "즐겨", "매일", "항상", "빈번"],
    "medium": ["가끔", "종종", "때때로", "보통"],
    "low": ["거의 안", "별로 안", "드물게", "안 하"],
}


class QueryParser:
    GENDER_MAPPING = {
        "남성": "MALE",
        "남": "MALE",
        "여성": "FEMALE",
        "여": "FEMALE"
    }

    def __init__(self):
        self.llm = LLMClientFactory.create_sonnet()
        self.parser = PydanticOutputParser(pydantic_object=QueryFilter)
        self.prompt = self._create_prompt()

    def _create_prompt(self) -> PromptTemplate:
        prompt_path = settings.prompts_dir / "parse_query.md"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            base_prompt = f.read()

        template = f"""{base_prompt}

# USER QUERY
```
{{query}}
```

구조화된 필터를 JSON 형식으로 출력하세요. OUTPUT SCHEMA 형식을 정확히 따르세요.
"""

        return PromptTemplate(
            template=template,
            input_variables=["query"]
        )

    def parse(self, query: str) -> QueryFilter:
        chain = self.prompt | self.llm | self.parser
        return chain.invoke({"query": query})

    def parse_to_dict(self, query: str, mode: SearchMode = SearchMode.STRICT) -> Dict[str, Any]:
        multi_condition_keywords = [',', '과 ', '와 ', '그리고', '각각', '및 ']
        has_multi_condition = any(kw in query for kw in multi_condition_keywords)

        if has_multi_condition:
            try:
                result = self._parse_raw(query)
                if 'conditions' in result:
                    for condition in result['conditions']:
                        condition = self._expand_frequency_filters(condition, query)
                        condition.update(self._apply_mode_params(condition, mode))
                    return result
            except Exception:
                pass

        filter_obj = self.parse(query)
        parsed_filter = filter_obj.model_dump()
        parsed_filter = self._expand_frequency_filters(parsed_filter, query)
        return self._apply_mode_params(parsed_filter, mode)

    def _parse_raw(self, query: str) -> Dict[str, Any]:
        result = (self.prompt | self.llm).invoke({"query": query})
        content = result.content.strip()

        if content.startswith("```"):
            lines = content.split("\n")
            json_lines = []
            in_json = False
            for line in lines:
                if line.startswith("```") and not in_json:
                    in_json = True
                    continue
                elif line.startswith("```") and in_json:
                    break
                elif in_json:
                    json_lines.append(line)
            content = "\n".join(json_lines)

        return json.loads(content)

    def _detect_frequency_level(self, query: str) -> str:
        query_lower = query.lower()
        for level, keywords in FREQUENCY_KEYWORDS.items():
            for kw in keywords:
                if kw in query_lower:
                    return level
        return "high"

    def _expand_frequency_filters(self, parsed_filter: Dict[str, Any], query: str) -> Dict[str, Any]:
        survey_fields = ['survey_lifestyle', 'survey_consumption', 'survey_health', 'survey_digital']
        frequency_level = self._detect_frequency_level(query)

        for field in survey_fields:
            if parsed_filter.get(field) and isinstance(parsed_filter[field], dict):
                for question_key, answer_value in parsed_filter[field].items():
                    if question_key in FREQUENCY_EXPANSION_MAP:
                        expansion_values = FREQUENCY_EXPANSION_MAP[question_key].get(frequency_level)
                        if expansion_values:
                            if isinstance(answer_value, dict) and 'include' in answer_value:
                                include_val = answer_value['include']
                                if isinstance(include_val, str):
                                    is_frequency_keyword = any(kw in include_val for kw in sum(FREQUENCY_KEYWORDS.values(), []))
                                    if is_frequency_keyword or include_val in sum(FREQUENCY_EXPANSION_MAP[question_key].values(), []):
                                        parsed_filter[field][question_key] = {"include": expansion_values}
                            elif isinstance(answer_value, str):
                                is_frequency_keyword = any(kw in answer_value for kw in sum(FREQUENCY_KEYWORDS.values(), []))
                                if is_frequency_keyword:
                                    parsed_filter[field][question_key] = {"include": expansion_values}

        return parsed_filter

    def _apply_mode_params(self, parsed_filter: Dict[str, Any], mode: SearchMode) -> Dict[str, Any]:
        if parsed_filter.get("gender") in self.GENDER_MAPPING:
            parsed_filter["gender"] = self.GENDER_MAPPING[parsed_filter["gender"]]

        if mode == SearchMode.STRICT:
            return {
                **parsed_filter,
                "mode": "strict",
                "match_strategy": "all",
                "allow_null_fields": False,
                "exact_match": True,
            }
        else:
            params = {
                "mode": "flexible",
                "match_strategy": "best_match",
                "minimum_match_ratio": 0.6,
                "allow_null_fields": True,
                "exact_match": False,
                "sort_by": "match_score",
            }

            if parsed_filter.get("age_group"):
                params["age_group"] = self._expand_age_group(parsed_filter["age_group"])

            if parsed_filter.get("residence"):
                params["residence"] = self._expand_residence(parsed_filter["residence"])

            if parsed_filter.get("income_min") is not None:
                params["income_min"] = int(parsed_filter["income_min"] * 0.9)

            if parsed_filter.get("income_max") is not None:
                params["income_max"] = int(parsed_filter["income_max"] * 1.1)

            for key, value in parsed_filter.items():
                if key not in params and value is not None:
                    params[key] = value

            return params

    def _expand_age_group(self, age_group) -> list:
        expansions = {
            "10대": ["10대", "20대 초반"],
            "20대": ["10대 후반", "20대", "30대 초반"],
            "30대": ["20대 후반", "30대", "40대 초반"],
            "40대": ["30대 후반", "40대", "50대 초반"],
            "50대": ["40대 후반", "50대", "60대 초반"],
            "60대": ["50대 후반", "60대", "70대 초반"],
        }

        if isinstance(age_group, list):
            expanded = []
            for ag in age_group:
                expanded.extend(expansions.get(ag, [ag]))
            return list(dict.fromkeys(expanded))

        return expansions.get(age_group, [age_group])

    def _expand_residence(self, residence: str) -> list:
        expansions = {
            "서울": ["서울", "경기"],
            "경기": ["서울", "경기", "인천"],
            "부산": ["부산", "경남", "울산"],
            "대구": ["대구", "경북"],
            "광주": ["광주", "전남"],
            "대전": ["대전", "세종", "충남"],
            "인천": ["인천", "경기"],
            "울산": ["울산", "부산", "경남"],
            "세종": ["세종", "대전", "충남"],
        }

        return expansions.get(residence, [residence])
