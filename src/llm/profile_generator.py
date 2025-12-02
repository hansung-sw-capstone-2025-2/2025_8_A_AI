import json
from typing import Dict, Any
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from src.core.config import settings
from src.domain.schemas import PanelProfileSchema, HashtagSchema
from src.llm.client import LLMClientFactory


class ProfileGenerator:

    def __init__(self, prompt_path: str = None):
        self.custom_prompt_path = prompt_path

        self.llm = LLMClientFactory.create_haiku(max_tokens=2000)
        self.llm_hashtag = LLMClientFactory.create_haiku(max_tokens=1000)

        self.profile_parser = PydanticOutputParser(pydantic_object=PanelProfileSchema)
        self.hashtag_parser = PydanticOutputParser(pydantic_object=HashtagSchema)

        self.profile_prompt = self._create_profile_prompt()
        self.hashtag_prompt = self._create_hashtag_prompt()

        self.profile_chain = self.profile_prompt | self.llm | self.profile_parser
        self.hashtag_chain = self.hashtag_prompt | self.llm_hashtag | self.hashtag_parser

    def _load_prompt_file(self, filename: str) -> str:
        prompt_path = settings.prompts_dir / filename
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _create_profile_prompt(self) -> PromptTemplate:
        if self.custom_prompt_path:
            with open(self.custom_prompt_path, 'r', encoding='utf-8') as f:
                base_prompt = f.read()
        else:
            base_prompt = self._load_prompt_file("generate_profile.md")

        template = f"""{base_prompt}

# INPUT DATA
```json
{{panel_data}}
```

{{format_instructions}}

"""

        return PromptTemplate(
            template=template,
            input_variables=["panel_data", "format_instructions"]
        ).partial(format_instructions=self.profile_parser.get_format_instructions())

    def _create_hashtag_prompt(self) -> PromptTemplate:
        base_prompt = self._load_prompt_file("generate_hashtags.md")

        template = f"""{base_prompt}

# INPUT DATA
```json
{{hashtag_input}}
```

{{format_instructions}}

"""

        return PromptTemplate(
            template=template,
            input_variables=["hashtag_input", "format_instructions"]
        ).partial(format_instructions=self.hashtag_parser.get_format_instructions())

    def _prepare_input_data(self, panel: dict) -> dict:
        input_data = {
            "panel_id": panel.get("panel_id"),
            "성별": panel.get("성별"),
            "나이": panel.get("나이"),
            "연령대": panel.get("연령대"),
            "거주지역": panel.get("거주지역"),
            "결혼여부": panel.get("결혼여부"),
            "자녀수": panel.get("자녀수"),
            "최종학력": panel.get("최종학력"),
            "직업": panel.get("직업"),
            "개인소득": panel.get("개인소득"),
            "가구소득": panel.get("가구소득"),
            "보유전자제품": panel.get("보유전자제품", []),
            "휴대폰브랜드": panel.get("휴대폰브랜드"),
            "휴대폰모델": panel.get("휴대폰모델"),
            "차량브랜드": panel.get("차량브랜드"),
            "차량모델": panel.get("차량모델"),
            "설문응답": panel.get("설문응답", {})
        }

        def is_empty(value):
            if value is None:
                return True
            if isinstance(value, (list, dict, str)) and not value:
                return True
            return False

        return {k: v for k, v in input_data.items() if not is_empty(v)}

    def generate_profile(self, panel: dict) -> Dict[str, Any]:
        input_data = self._prepare_input_data(panel)
        panel_json = json.dumps(input_data, ensure_ascii=False, indent=2)

        try:
            validated_profile = self.profile_chain.invoke({"panel_data": panel_json})

            return {
                "panel_id": panel.get("panel_id"),
                "profile": validated_profile.model_dump(),
                "model": settings.model_haiku,
                "temperature": 0,
                "input_data": input_data
            }

        except Exception as e:
            raise ValueError(f"프로필 생성 실패: {e}")

    def generate_hashtags(self, profile: dict, raw_data: dict) -> Dict[str, Any]:
        devices = raw_data.get("보유전자제품", [])
        device_count = len(devices) if devices else 0

        input_data = {
            "profile_summary": profile.get("profile_summary"),
            "demographic_summary": profile.get("demographic_summary"),
            "lifestyle_summary": profile.get("lifestyle_summary"),
            "consumption_summary": profile.get("consumption_summary"),
            "key_characteristics": profile.get("key_characteristics", []),
            "search_keywords": profile.get("search_keywords", []),
            "lifestyle_tags": profile.get("lifestyle_tags", []),
            "device_count": device_count,
            "devices": devices
        }

        input_json = json.dumps(input_data, ensure_ascii=False, indent=2)

        try:
            validated_hashtags = self.hashtag_chain.invoke({"hashtag_input": input_json})
            return validated_hashtags.model_dump()

        except Exception as e:
            raise ValueError(f"해시태그 생성 실패: {e}")
