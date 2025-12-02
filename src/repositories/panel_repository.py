from typing import List, Dict, Any, Optional
import json

from src.core.database import Database
from src.domain.models import Panel


class PanelRepository:
    SEMANTIC_FIELDS = [
        'lifestyle_tags', 'search_keywords',
        'survey_health', 'survey_consumption',
        'survey_lifestyle', 'survey_digital', 'survey_environment'
    ]

    VALID_COLUMNS = {
        'age', 'age_group', 'gender', 'residence', 'occupation',
        'marital_status', 'phone_brand', 'car_brand',
        'smoking_experience', 'drinking_experience', 'electronic_devices',
        'cigarette_brands', 'e_cigarette'
    }

    SURVEY_FIELDS = [
        'smoking_experience', 'drinking_experience', 'electronic_devices',
        'cigarette_brands', 'e_cigarette'
    ]

    SURVEY_JSONB_FIELDS = {
        'survey_health': 'survey_health',
        'survey_consumption': 'survey_consumption',
        'survey_environment': 'survey_environment',
        'survey_digital': 'survey_digital',
        'survey_lifestyle': 'survey_lifestyle'
    }

    NEGATIVE_RESPONSES = {
        'smoking_experience': '담배를 피워본 적이 없다',
        'drinking_experience': '최근 1년 이내 술을 마시지 않음'
    }

    async def search(
        self,
        filters: Dict[str, Any],
        query_embedding: Optional[List[float]] = None,
        limit: int = 100
    ) -> List[Panel]:
        where_clauses, params, param_index = self._build_where_clauses(filters, query_embedding)
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        if query_embedding is not None:
            query_sql = f"""
                SELECT
                    id as panel_id, age, gender, residence, occupation,
                    marital_status, phone_brand, car_brand, profile_summary,
                    hash_tags as hashtags, electronic_devices, smoking_experience,
                    cigarette_brands, e_cigarette, drinking_experience,
                    survey_health, survey_consumption, survey_lifestyle,
                    survey_digital, survey_environment,
                    CASE WHEN embedding IS NOT NULL
                        THEN 1 - (embedding <=> $1::vector)
                        ELSE NULL
                    END AS similarity
                FROM panel
                WHERE {where_sql}
                ORDER BY
                    CASE WHEN embedding IS NOT NULL
                        THEN embedding <=> $1::vector
                        ELSE 999
                    END
                LIMIT ${param_index}
            """
        else:
            query_sql = f"""
                SELECT
                    id as panel_id, age, gender, residence, occupation,
                    marital_status, phone_brand, car_brand, profile_summary,
                    hash_tags as hashtags, electronic_devices, smoking_experience,
                    cigarette_brands, e_cigarette, drinking_experience,
                    survey_health, survey_consumption, survey_lifestyle,
                    survey_digital, survey_environment,
                    NULL as similarity
                FROM panel
                WHERE {where_sql}
                LIMIT ${param_index}
            """

        params.append(limit)
        rows = await Database.fetch(query_sql, *params)
        return [self._row_to_panel(row) for row in rows]

    async def search_by_ids(
        self,
        panel_ids: List[str],
        additional_filters: Dict[str, Any],
        query_embedding: Optional[List[float]] = None
    ) -> List[Panel]:
        if not panel_ids:
            return []

        where_clauses = []
        params = []
        param_index = 1

        if query_embedding is not None:
            vector_str = '[' + ','.join(map(str, query_embedding)) + ']'
            params.append(vector_str)
            param_index += 1

        params.append(panel_ids)
        where_clauses.append(f"id = ANY(${param_index}::text[])")
        param_index += 1

        for key, value in additional_filters.items():
            if key == 'similarity_threshold' or value is None:
                continue

            if isinstance(value, list):
                if key in ['residence', 'occupation', 'phone_brand', 'car_brand']:
                    like_conditions = []
                    for item in value:
                        like_conditions.append(f"{key} LIKE ${param_index}")
                        params.append(f'%{item}%')
                        param_index += 1
                    where_clauses.append(f"({' OR '.join(like_conditions)})")
                else:
                    placeholders = ', '.join([f'${i}' for i in range(param_index, param_index + len(value))])
                    where_clauses.append(f"{key} IN ({placeholders})")
                    params.extend(value)
                    param_index += len(value)
            else:
                if key in ['residence', 'occupation', 'phone_brand', 'car_brand']:
                    where_clauses.append(f"{key} LIKE ${param_index}")
                    params.append(f'%{value}%')
                else:
                    where_clauses.append(f"{key} = ${param_index}")
                    params.append(value)
                param_index += 1

        where_sql = " AND ".join(where_clauses)

        if query_embedding is not None:
            query_sql = f"""
                SELECT
                    id as panel_id, age, gender, residence, occupation,
                    marital_status, phone_brand, car_brand, profile_summary,
                    hash_tags as hashtags, electronic_devices, smoking_experience,
                    cigarette_brands, e_cigarette, drinking_experience,
                    CASE WHEN embedding IS NOT NULL
                        THEN 1 - (embedding <=> $1::vector)
                        ELSE NULL
                    END AS similarity
                FROM panel
                WHERE {where_sql}
                ORDER BY
                    CASE WHEN embedding IS NOT NULL
                        THEN embedding <=> $1::vector
                        ELSE 999
                    END
            """
        else:
            query_sql = f"""
                SELECT
                    id as panel_id, age, gender, residence, occupation,
                    marital_status, phone_brand, car_brand, profile_summary,
                    hash_tags as hashtags, electronic_devices, smoking_experience,
                    cigarette_brands, e_cigarette, drinking_experience,
                    NULL as similarity
                FROM panel
                WHERE {where_sql}
            """

        rows = await Database.fetch(query_sql, *params)
        return [self._row_to_panel(row) for row in rows]

    async def get_by_ids(self, panel_ids: List[str]) -> List[Panel]:
        if not panel_ids:
            return []

        rows = await Database.fetch(
            "SELECT * FROM panel WHERE id = ANY($1::text[])",
            panel_ids
        )
        return [self._row_to_panel(row) for row in rows]

    async def aggregate_metric(self, panel_ids: List[str], metric: str) -> Dict[str, int]:
        if not panel_ids:
            return {}

        rows = await Database.fetch(f"""
            SELECT {metric}, COUNT(*) as count
            FROM panel
            WHERE id = ANY($1::text[]) AND {metric} IS NOT NULL
            GROUP BY {metric}
            ORDER BY count DESC
        """, panel_ids)

        return {str(row[metric]): row['count'] for row in rows}

    async def calculate_average(self, panel_ids: List[str], metric: str) -> Optional[float]:
        if not panel_ids:
            return None

        if metric in ["age", "children_count"]:
            result = await Database.fetchrow(
                f"SELECT AVG(CAST({metric} AS FLOAT)) as avg_value FROM panel WHERE id = ANY($1::text[]) AND {metric} IS NOT NULL",
                panel_ids
            )
            return float(result['avg_value']) if result and result['avg_value'] is not None else None

        if metric == "family_size":
            rows = await Database.fetch(f"""
                SELECT {metric} FROM panel
                WHERE id = ANY($1::text[]) AND {metric} IS NOT NULL AND {metric} != ''
            """, panel_ids)

            if not rows:
                return None

            numeric_values = []
            for row in rows:
                value = row[metric]
                if "1명" in value or "혼자" in value:
                    numeric_values.append(1)
                elif "2명" in value:
                    numeric_values.append(2)
                elif "3명" in value:
                    numeric_values.append(3)
                elif "4명" in value:
                    numeric_values.append(4)
                elif "5명" in value or "이상" in value:
                    numeric_values.append(5)

            return sum(numeric_values) / len(numeric_values) if numeric_values else None

        if metric in ["personal_income", "household_income"]:
            rows = await Database.fetch(f"""
                SELECT {metric} FROM panel
                WHERE id = ANY($1::text[]) AND {metric} IS NOT NULL AND {metric} != ''
            """, panel_ids)

            if not rows:
                return None

            numeric_values = []
            for row in rows:
                converted = self._parse_income_range(row[metric])
                if converted is not None:
                    numeric_values.append(converted)

            return sum(numeric_values) / len(numeric_values) if numeric_values else None

        return None

    async def calculate_ownership_rate(self, panel_ids: List[str], field: str) -> Optional[float]:
        if not panel_ids:
            return None

        total_count = len(panel_ids)
        result = await Database.fetchrow(f"""
            SELECT COUNT(*) as ownership_count FROM panel
            WHERE id = ANY($1::text[]) AND {field} IS NOT NULL AND {field} != ''
        """, panel_ids)

        if result and total_count > 0:
            return round(result['ownership_count'] / total_count * 100, 2)

        return 0.0

    async def count_by_condition(self, panel_ids: List[str], condition: str, params: List[Any] = None) -> int:
        if not panel_ids:
            return 0

        query = f"""
            SELECT COUNT(*) as cnt FROM panel
            WHERE id = ANY($1::text[]) AND {condition}
        """

        all_params = [panel_ids] + (params or [])
        result = await Database.fetchrow(query, *all_params)
        return result['cnt'] if result else 0

    async def get_hashtags_sample(self, panel_ids: List[str], limit: int = 50) -> List[List[str]]:
        if not panel_ids:
            return []

        rows = await Database.fetch("""
            SELECT hash_tags FROM panel
            WHERE id = ANY($1::text[]) AND hash_tags IS NOT NULL AND hash_tags != ''
            LIMIT $2
        """, panel_ids, limit)

        result = []
        for row in rows:
            tags = row['hash_tags']
            if isinstance(tags, list):
                result.append([str(t) for t in tags if t])
            elif isinstance(tags, str):
                result.append([tags])
        return result

    def _build_where_clauses(
        self,
        filters: Dict[str, Any],
        query_embedding: Optional[List[float]]
    ) -> tuple:
        where_clauses = []
        params = []
        param_index = 1

        if query_embedding is not None:
            vector_str = '[' + ','.join(map(str, query_embedding)) + ']'
            params.append(vector_str)
            param_index += 1

        if 'region' in filters and filters['region'] is not None:
            filters['residence'] = filters['region']
            del filters['region']

        if 'brands' in filters and filters['brands'] is not None:
            if filters.get('phone_brand') is None:
                filters['phone_brand'] = filters['brands']
            del filters['brands']

        survey_fields_to_filter = set()
        if 'lifestyle_tags' in filters and filters['lifestyle_tags'] is not None:
            lifestyle_tags = filters['lifestyle_tags']
            if not isinstance(lifestyle_tags, list):
                lifestyle_tags = [lifestyle_tags]

            for tag in lifestyle_tags:
                tag_lower = str(tag).lower()
                if any(keyword in tag_lower for keyword in ['흡연', '담배', '시가', '파이프', '궐련']):
                    survey_fields_to_filter.add('smoking_experience')
                if any(keyword in tag_lower for keyword in ['음주', '술', '알코올', '주류', '음료']):
                    survey_fields_to_filter.add('drinking_experience')

        for survey_field in self.SURVEY_FIELDS:
            if (survey_field in filters and filters[survey_field] is not None) or survey_field in survey_fields_to_filter:
                where_clauses.append(f"{survey_field} IS NOT NULL")
                where_clauses.append(f"{survey_field} != '{{}}'")
                if survey_field in self.NEGATIVE_RESPONSES:
                    negative_value = self.NEGATIVE_RESPONSES[survey_field]
                    where_clauses.append(f"NOT ('{negative_value}' = ANY({survey_field}))")

        for filter_key, db_column in self.SURVEY_JSONB_FIELDS.items():
            if filter_key in filters and filters[filter_key] is not None:
                survey_filter = filters[filter_key]
                if isinstance(survey_filter, dict):
                    for question_key, answer_value in survey_filter.items():
                        if isinstance(answer_value, dict):
                            if 'exclude' in answer_value:
                                clause = f"({db_column}->>'{question_key}' IS NOT NULL AND {db_column}->>'{question_key}' NOT LIKE ${param_index})"
                                param_value = f'%{answer_value["exclude"]}%'
                                where_clauses.append(clause)
                                params.append(param_value)
                                param_index += 1
                            elif 'include' in answer_value:
                                include_val = answer_value["include"]
                                if isinstance(include_val, list):
                                    or_clauses = []
                                    for val in include_val:
                                        or_clauses.append(f"{db_column}->>'{question_key}' LIKE ${param_index}")
                                        params.append(f'%{val}%')
                                        param_index += 1
                                    if or_clauses:
                                        where_clauses.append(f"({' OR '.join(or_clauses)})")
                                else:
                                    clause = f"{db_column}->>'{question_key}' LIKE ${param_index}"
                                    where_clauses.append(clause)
                                    params.append(f'%{include_val}%')
                                    param_index += 1
                        else:
                            clause = f"{db_column}->>'{question_key}' LIKE ${param_index}"
                            where_clauses.append(clause)
                            params.append(f'%{answer_value}%')
                            param_index += 1

        for key, value in filters.items():
            if key in ['mode', 'match_strategy', 'allow_null_fields', 'exact_match', 'minimum_match_ratio', 'sort_by', 'limit', 'similarity_threshold']:
                continue

            if key not in self.VALID_COLUMNS:
                continue

            if value is None:
                continue

            if isinstance(value, list):
                if key in ['residence', 'occupation', 'phone_brand', 'car_brand']:
                    if value == ["any"] or (len(value) == 1 and value[0] == "any"):
                        where_clauses.append(f"({key} IS NOT NULL AND {key} != '')")
                    else:
                        like_conditions = []
                        for item in value:
                            like_conditions.append(f"{key} LIKE ${param_index}")
                            params.append(f'%{item}%')
                            param_index += 1
                        where_clauses.append(f"({' OR '.join(like_conditions)})")
                else:
                    placeholders = ', '.join([f'${i}' for i in range(param_index, param_index + len(value))])
                    where_clauses.append(f"{key} = ANY(ARRAY[{placeholders}])")
                    params.extend(value)
                    param_index += len(value)
            else:
                if key in ['residence', 'occupation', 'phone_brand', 'car_brand']:
                    where_clauses.append(f"{key} LIKE ${param_index}")
                    params.append(f'%{value}%')
                else:
                    where_clauses.append(f"{key} = ${param_index}")
                    params.append(value)
                param_index += 1

        return where_clauses, params, param_index

    def _row_to_panel(self, row: dict) -> Panel:
        return Panel(
            panel_id=row['panel_id'],
            age=row.get('age'),
            gender=row.get('gender'),
            residence=row.get('residence'),
            occupation=row.get('occupation'),
            marital_status=row.get('marital_status'),
            phone_brand=row.get('phone_brand'),
            car_brand=row.get('car_brand'),
            profile_summary=row.get('profile_summary'),
            hashtags=row.get('hashtags'),
            electronic_devices=row.get('electronic_devices'),
            smoking_experience=row.get('smoking_experience'),
            cigarette_brands=row.get('cigarette_brands'),
            e_cigarette=row.get('e_cigarette'),
            drinking_experience=row.get('drinking_experience'),
            survey_health=self._parse_jsonb(row.get('survey_health')),
            survey_consumption=self._parse_jsonb(row.get('survey_consumption')),
            survey_lifestyle=self._parse_jsonb(row.get('survey_lifestyle')),
            survey_digital=self._parse_jsonb(row.get('survey_digital')),
            survey_environment=self._parse_jsonb(row.get('survey_environment')),
            similarity=row.get('similarity')
        )

    def _parse_jsonb(self, value) -> Optional[dict]:
        if value is None:
            return None
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None

    def _parse_income_range(self, income_str: str) -> Optional[float]:
        import re
        try:
            if "미만" in income_str:
                match = re.search(r'(\d+)', income_str)
                if match:
                    return float(match.group(1)) / 2
            elif "이상" in income_str:
                match = re.search(r'(\d+)', income_str)
                if match:
                    return float(match.group(1))
            else:
                match = re.findall(r'(\d+)', income_str)
                if len(match) >= 2:
                    return (float(match[0]) + float(match[1])) / 2
                elif len(match) == 1:
                    return float(match[0])
            return None
        except Exception:
            return None
