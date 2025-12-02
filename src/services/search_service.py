from typing import Dict, Any, List, Optional, Tuple
import uuid
from datetime import datetime

from src.core.config import settings
from src.domain.models import Panel
from src.domain.enums import SearchMode
from src.repositories import PanelRepository, SearchHistoryRepository
from src.llm import QueryParser, EmbeddingService
from src.api.schemas.search import PanelInfo


class SearchService:
    SEMANTIC_FIELDS = [
        'lifestyle_tags', 'search_keywords',
        'survey_health', 'survey_consumption',
        'survey_lifestyle', 'survey_digital', 'survey_environment'
    ]

    def __init__(self):
        self.panel_repo = PanelRepository()
        self.search_history_repo = SearchHistoryRepository()
        self.query_parser = QueryParser()
        self.embedding_service = EmbeddingService()

    async def search(
        self,
        query: Optional[str] = None,
        search_params: Optional[Dict[str, Any]] = None,
        structured_filters: Optional[Dict[str, Any]] = None,
        search_mode: str = "strict",
        limit: int = 100,
        member_id: Optional[int] = None
    ) -> Dict[str, Any]:
        mode = SearchMode.STRICT if search_mode == "strict" else SearchMode.FLEXIBLE
        search_method, original_query, filters = self._prepare_filters(
            query, search_params, structured_filters, mode, limit
        )

        is_multi_condition = 'conditions' in filters and isinstance(filters['conditions'], list)

        query_embedding = None
        if original_query:
            try:
                query_embedding = self.embedding_service.embed_text(original_query)
            except Exception:
                query_embedding = None

        if is_multi_condition:
            panels = await self._execute_multi_condition_search(
                filters['conditions'], query_embedding
            )
        else:
            panels = await self._execute_single_search(
                filters, query_embedding, filters.get('limit', limit)
            )

        panel_infos = self._convert_to_panel_info(panels, filters)

        search_id = await self._save_search_history(
            member_id, original_query, panel_infos
        )

        return {
            "search_id": search_id,
            "query": original_query,
            "panels": panel_infos,
            "total_count": len(panel_infos),
            "search_mode": search_mode,
            "applied_filters": filters,
            "search_method": search_method
        }

    async def refine_search(
        self,
        search_id: int,
        additional_filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        search_history = await self.search_history_repo.get_by_id(search_id)
        if not search_history:
            raise ValueError(f"Search {search_id} not found")

        panel_ids = search_history.panel_ids
        if not panel_ids:
            return {
                "original_count": 0,
                "filtered_count": 0,
                "panels": [],
                "applied_filters": additional_filters
            }

        original_query = search_history.content
        query_embedding = None
        if original_query:
            try:
                query_embedding = self.embedding_service.embed_text(original_query)
            except Exception:
                query_embedding = None

        panels = await self.panel_repo.search_by_ids(
            panel_ids, additional_filters, query_embedding
        )

        panel_infos = self._convert_to_panel_info(panels, additional_filters)

        return {
            "original_count": len(panel_ids),
            "filtered_count": len(panel_infos),
            "panels": panel_infos,
            "applied_filters": additional_filters
        }

    async def get_search_info(self, search_id: int) -> Dict[str, Any]:
        search_history = await self.search_history_repo.get_by_id(search_id)
        if not search_history:
            raise ValueError(f"Search {search_id} not found")

        panel_ids = search_history.panel_ids
        concordance_rates = search_history.concordance_rate

        panels_with_rates = []
        for i, panel_id in enumerate(panel_ids):
            rate = concordance_rates[i] if i < len(concordance_rates) else 0.0
            panels_with_rates.append({
                "panel_id": panel_id,
                "concordance_rate": float(rate) if rate is not None else 0.0
            })

        return {
            "search_id": str(search_history.id),
            "query": search_history.content,
            "panel_count": len(panel_ids),
            "panel_ids": panel_ids,
            "concordance_rates": concordance_rates,
            "panels_with_rates": panels_with_rates,
            "created_at": str(search_history.date) if search_history.date else None
        }

    def _prepare_filters(
        self,
        query: Optional[str],
        search_params: Optional[Dict[str, Any]],
        structured_filters: Optional[Dict[str, Any]],
        mode: SearchMode,
        limit: int
    ) -> Tuple[str, Optional[str], Dict[str, Any]]:
        if query:
            search_method = "natural_language"
            original_query = query
            filters = self.query_parser.parse_to_dict(query, mode)

            parsed_limit = filters.get('limit', 100)
            if parsed_limit == 100 and limit != 100:
                filters['limit'] = limit

            if structured_filters:
                structured = self._apply_mode_to_filters(structured_filters, mode)
                for key, value in structured.items():
                    if value is not None and key not in ['mode', 'match_strategy', 'allow_null_fields', 'exact_match', 'limit']:
                        filters[key] = value

        elif search_params:
            search_method = "recommendation"
            original_query = None
            filters = self._apply_mode_to_filters(search_params, mode)

        elif structured_filters:
            search_method = "structured_filter"
            original_query = None
            filters = self._apply_mode_to_filters(structured_filters, mode)

        else:
            raise ValueError("query, search_params, structured_filters 중 하나는 필수입니다")

        if 'limit' not in filters:
            filters['limit'] = limit

        return search_method, original_query, filters

    def _apply_mode_to_filters(self, filters: Dict[str, Any], mode: SearchMode) -> Dict[str, Any]:
        gender_mapping = {"남성": "MALE", "남": "MALE", "여성": "FEMALE", "여": "FEMALE"}

        if filters.get("gender") in gender_mapping:
            filters["gender"] = gender_mapping[filters["gender"]]

        if mode == SearchMode.STRICT:
            return {
                **filters,
                "mode": "strict",
                "match_strategy": "all",
                "allow_null_fields": False,
                "exact_match": True,
            }
        else:
            return {
                **filters,
                "mode": "flexible",
                "match_strategy": "best_match",
                "minimum_match_ratio": 0.6,
                "allow_null_fields": True,
                "exact_match": False,
            }

    async def _execute_single_search(
        self,
        filters: Dict[str, Any],
        query_embedding: Optional[List[float]],
        limit: int
    ) -> List[Panel]:
        return await self.panel_repo.search(filters, query_embedding, limit)

    async def _execute_multi_condition_search(
        self,
        conditions: List[Dict[str, Any]],
        query_embedding: Optional[List[float]]
    ) -> List[Panel]:
        all_panels = []
        seen_ids = set()

        for condition in conditions:
            condition_limit = condition.get('limit', 100)
            panels = await self.panel_repo.search(
                condition.copy(),
                query_embedding,
                condition_limit
            )

            for panel in panels:
                if panel.panel_id not in seen_ids:
                    seen_ids.add(panel.panel_id)
                    all_panels.append(panel)

        return all_panels

    def _convert_to_panel_info(
        self,
        panels: List[Panel],
        filters: Dict[str, Any]
    ) -> List[PanelInfo]:
        result = []
        is_simple = self._is_simple_filter_query(filters)

        for panel in panels:
            if panel.similarity is not None:
                concordance = 1.0 if is_simple else self._normalize_concordance(panel.similarity)
            else:
                concordance = 1.0 if is_simple else None

            profile_summary = panel.profile_summary
            if not profile_summary:
                profile_summary = self._generate_fallback_summary(panel)

            result.append(PanelInfo(
                panel_id=panel.panel_id,
                age=panel.age,
                gender=panel.gender,
                residence=panel.residence,
                occupation=panel.occupation,
                marital_status=panel.marital_status,
                phone_brand=panel.phone_brand,
                car_brand=panel.car_brand,
                profile_summary=profile_summary,
                hashtags=panel.hashtags,
                electronic_devices=panel.electronic_devices,
                smoking_experience=panel.smoking_experience,
                cigarette_brands=panel.cigarette_brands,
                e_cigarette=panel.e_cigarette,
                drinking_experience=panel.drinking_experience,
                survey_health=panel.survey_health,
                survey_consumption=panel.survey_consumption,
                survey_lifestyle=panel.survey_lifestyle,
                survey_digital=panel.survey_digital,
                survey_environment=panel.survey_environment,
                similarity=concordance
            ))

        return result

    def _is_simple_filter_query(self, filters: Dict[str, Any]) -> bool:
        for field in self.SEMANTIC_FIELDS:
            if filters.get(field) is not None:
                return False
        return True

    def _normalize_concordance(self, similarity: float) -> float:
        min_sim = settings.similarity_min
        max_sim = settings.similarity_max
        min_conc = settings.concordance_min
        max_conc = settings.concordance_max

        clipped = max(min_sim, min(similarity, max_sim))
        normalized = (clipped - min_sim) / (max_sim - min_sim) * (max_conc - min_conc) + min_conc

        return round(normalized, 2)

    def _generate_fallback_summary(self, panel: Panel) -> str:
        parts = []

        if panel.age and panel.gender:
            gender_str = '남성' if panel.gender == 'MALE' else '여성' if panel.gender == 'FEMALE' else panel.gender
            parts.append(f'{panel.age}세 {gender_str}')
        elif panel.age:
            parts.append(f'{panel.age}세')
        elif panel.gender:
            gender_str = '남성' if panel.gender == 'MALE' else '여성' if panel.gender == 'FEMALE' else panel.gender
            parts.append(gender_str)

        if panel.residence:
            parts.append(f'{panel.residence} 거주')

        if panel.occupation:
            parts.append(panel.occupation)

        if panel.marital_status:
            parts.append(panel.marital_status)

        if parts:
            return ', '.join(parts) + ' (AI 프로필 생성 전)'
        else:
            return '기본 정보만 등록된 패널입니다 (AI 프로필 생성 전)'

    async def _save_search_history(
        self,
        member_id: Optional[int],
        query: Optional[str],
        panels: List[PanelInfo]
    ) -> str:
        panel_ids = [p.panel_id for p in panels]
        concordance_rates = [float(p.similarity) if p.similarity else 0.0 for p in panels]

        try:
            search_id = await self.search_history_repo.create(
                member_id=member_id,
                content=query or "",
                panel_ids=panel_ids,
                concordance_rates=concordance_rates
            )
            return str(search_id)
        except Exception:
            return str(uuid.uuid4())
