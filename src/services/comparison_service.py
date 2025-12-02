from typing import List, Dict, Any, Optional
from collections import Counter
from scipy import stats
import numpy as np

from src.core.exceptions import NotFoundError
from src.repositories import PanelRepository, LibraryRepository
from src.llm import InsightGenerator
from src.api.schemas.comparison import (
    CohortBasicInfo, MetricComparison, BasicInfoComparison,
    CharacteristicComparison, KeyInsights, RegionDistribution, GenderDistribution
)


COMPARISON_METRICS = [
    ("occupation", "직업 분포"),
    ("marital_status", "결혼 여부"),
    ("phone_brand", "휴대폰 브랜드"),
    ("car_brand", "차량 브랜드"),
    ("gender", "성별 분포"),
    ("age_group", "연령대 분포"),
    ("region", "거주 지역"),
    ("income_range", "소득 구간"),
    ("education", "학력"),
]

BASIC_INFO_METRICS = [
    ("age", "평균 연령"),
    ("family_size", "평균 가족 수"),
    ("children_count", "평균 자녀 수"),
    ("personal_income", "평균 개인 소득 (만원)"),
    ("household_income", "평균 가구 소득 (만원)"),
]

PERCENTAGE_METRICS = [
    ("car_ownership", "차량 보유율", "car_brand"),
]


class ComparisonService:
    def __init__(self):
        self.panel_repo = PanelRepository()
        self.library_repo = LibraryRepository()
        self.insight_generator = InsightGenerator()

    async def compare_cohorts(
        self,
        cohort_1_id: int,
        cohort_2_id: int,
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        cohort_1 = await self.library_repo.get_by_id(cohort_1_id)
        cohort_2 = await self.library_repo.get_by_id(cohort_2_id)

        if not cohort_1:
            raise NotFoundError("Cohort", str(cohort_1_id))
        if not cohort_2:
            raise NotFoundError("Cohort", str(cohort_2_id))

        cohort_1_info = CohortBasicInfo(
            cohort_id=cohort_1.cohort_id,
            cohort_name=cohort_1.cohort_name,
            panel_count=cohort_1.panel_count,
            created_at=cohort_1.created_at
        )
        cohort_2_info = CohortBasicInfo(
            cohort_id=cohort_2.cohort_id,
            cohort_name=cohort_2.cohort_name,
            panel_count=cohort_2.panel_count,
            created_at=cohort_2.created_at
        )

        panel_ids_1 = cohort_1.panel_ids
        panel_ids_2 = cohort_2.panel_ids

        if not metrics:
            metrics = [m[0] for m in COMPARISON_METRICS[:5]]

        comparisons = await self._compare_metrics(
            panel_ids_1, panel_ids_2, metrics,
            cohort_1.panel_count, cohort_2.panel_count
        )

        basic_info = await self._compare_basic_info(panel_ids_1, panel_ids_2)

        characteristics = await self._find_characteristics(
            panel_ids_1, panel_ids_2,
            cohort_1.panel_count, cohort_2.panel_count
        )

        region_distribution = await self._calculate_region_distribution(
            panel_ids_1, panel_ids_2,
            cohort_1.panel_count, cohort_2.panel_count
        )

        gender_distribution = await self._calculate_gender_distribution(
            panel_ids_1, panel_ids_2,
            cohort_1.panel_count, cohort_2.panel_count
        )

        key_insights = await self._generate_insights(
            cohort_1_info, cohort_2_info,
            panel_ids_1, panel_ids_2,
            comparisons, basic_info, characteristics
        )

        summary = self._generate_summary(cohort_1_info, cohort_2_info, comparisons)

        return {
            "cohort_1": cohort_1_info,
            "cohort_2": cohort_2_info,
            "comparisons": comparisons,
            "basic_info": basic_info,
            "characteristics": characteristics,
            "region_distribution": region_distribution,
            "gender_distribution": gender_distribution,
            "key_insights": key_insights,
            "summary": summary
        }

    async def _compare_metrics(
        self,
        panel_ids_1: List[str],
        panel_ids_2: List[str],
        metrics: List[str],
        count_1: int,
        count_2: int
    ) -> List[MetricComparison]:
        comparisons = []

        for metric in metrics:
            metric_label = next(
                (m[1] for m in COMPARISON_METRICS if m[0] == metric),
                metric
            )

            data_1 = await self.panel_repo.aggregate_metric(panel_ids_1, metric)
            data_2 = await self.panel_repo.aggregate_metric(panel_ids_2, metric)

            if not data_1 or not data_2:
                continue

            percentage_1 = {k: round(v / count_1 * 100, 2) for k, v in data_1.items()}
            percentage_2 = {k: round(v / count_2 * 100, 2) for k, v in data_2.items()}

            statistical_test = self._perform_chi_square_test(data_1, data_2)

            comparisons.append(MetricComparison(
                metric_name=metric,
                metric_label=metric_label,
                cohort_1_data=data_1,
                cohort_2_data=data_2,
                cohort_1_percentage=percentage_1,
                cohort_2_percentage=percentage_2,
                statistical_test=statistical_test
            ))

        return comparisons

    async def _compare_basic_info(
        self,
        panel_ids_1: List[str],
        panel_ids_2: List[str]
    ) -> List[BasicInfoComparison]:
        basic_info = []

        for metric, label in BASIC_INFO_METRICS:
            try:
                avg_1 = await self.panel_repo.calculate_average(panel_ids_1, metric)
                avg_2 = await self.panel_repo.calculate_average(panel_ids_2, metric)

                difference = None
                difference_pct = None
                if avg_1 is not None and avg_2 is not None:
                    difference = round(avg_2 - avg_1, 2)
                    if avg_1 > 0:
                        difference_pct = round((avg_2 - avg_1) / avg_1 * 100, 2)

                basic_info.append(BasicInfoComparison(
                    metric_name=metric,
                    metric_label=label,
                    cohort_1_value=round(avg_1, 2) if avg_1 is not None else None,
                    cohort_2_value=round(avg_2, 2) if avg_2 is not None else None,
                    difference=difference,
                    difference_percentage=difference_pct
                ))
            except Exception:
                continue

        for metric_name, label, field in PERCENTAGE_METRICS:
            try:
                rate_1 = await self.panel_repo.calculate_ownership_rate(panel_ids_1, field)
                rate_2 = await self.panel_repo.calculate_ownership_rate(panel_ids_2, field)

                difference = None
                difference_pct = None
                if rate_1 is not None and rate_2 is not None:
                    difference = round(rate_2 - rate_1, 2)
                    if rate_1 > 0:
                        difference_pct = round((rate_2 - rate_1) / rate_1 * 100, 2)

                basic_info.append(BasicInfoComparison(
                    metric_name=metric_name,
                    metric_label=label,
                    cohort_1_value=rate_1,
                    cohort_2_value=rate_2,
                    difference=difference,
                    difference_percentage=difference_pct
                ))
            except Exception:
                continue

        return basic_info

    async def _find_characteristics(
        self,
        panel_ids_1: List[str],
        panel_ids_2: List[str],
        count_1: int,
        count_2: int
    ) -> List[CharacteristicComparison]:
        characteristics = []

        checks = [
            ("외제차 보유 여부", "car_brand = ANY($2::text[])",
             ['BMW', 'Mercedes-Benz', 'Audi', 'Lexus', 'Porsche', 'Volvo', 'Tesla', 'Volkswagen']),
            ("전문직/경영관리직 비율", "occupation = ANY($2::text[])",
             ['전문직 (의사, 간호사, 변호사, 회계사, 예술가, 종교인, 엔지니어, 프로그래머, 기술사 등)',
              '경영/관리직 (사장, 대기업 간부, 고위 공무원 등)']),
            ("삼성전자 휴대폰 선호", "phone_brand = ANY($2::text[])",
             ['삼성전자 (갤럭시, 노트)']),
            ("대학생/대학원생 비율", "occupation = ANY($2::text[])",
             ['대학생/대학원생']),
        ]

        for name, condition, values in checks:
            try:
                cnt_1 = await self.panel_repo.count_by_condition(panel_ids_1, condition, [values])
                cnt_2 = await self.panel_repo.count_by_condition(panel_ids_2, condition, [values])

                if cnt_1 + cnt_2 > 0:
                    total = cnt_1 + cnt_2
                    pct_1 = round(cnt_1 / total * 100, 2)
                    pct_2 = round(cnt_2 / total * 100, 2)
                    diff = abs(pct_1 - pct_2)

                    if diff >= 10:
                        characteristics.append({
                            "characteristic": name,
                            "cohort_1_percentage": pct_1,
                            "cohort_2_percentage": pct_2,
                            "cohort_1_count": cnt_1,
                            "cohort_2_count": cnt_2,
                            "difference_percentage": diff,
                            "sort_key": diff
                        })
            except Exception:
                continue

        try:
            from src.core.database import Database
            result_1 = await Database.fetchrow("""
                SELECT COUNT(*) as cnt FROM panel
                WHERE id = ANY($1::text[])
                AND (residence LIKE '서울%' OR region LIKE '서울%')
            """, panel_ids_1)
            result_2 = await Database.fetchrow("""
                SELECT COUNT(*) as cnt FROM panel
                WHERE id = ANY($1::text[])
                AND (residence LIKE '서울%' OR region LIKE '서울%')
            """, panel_ids_2)

            seoul_1 = result_1['cnt'] if result_1 else 0
            seoul_2 = result_2['cnt'] if result_2 else 0

            if seoul_1 + seoul_2 > 0:
                total = seoul_1 + seoul_2
                pct_1 = round(seoul_1 / total * 100, 2)
                pct_2 = round(seoul_2 / total * 100, 2)
                diff = abs(pct_1 - pct_2)

                if diff >= 10:
                    characteristics.append({
                        "characteristic": "서울 거주 비율",
                        "cohort_1_percentage": pct_1,
                        "cohort_2_percentage": pct_2,
                        "cohort_1_count": seoul_1,
                        "cohort_2_count": seoul_2,
                        "difference_percentage": diff,
                        "sort_key": diff
                    })
        except Exception:
            pass

        try:
            from src.core.database import Database
            result_1 = await Database.fetchrow("""
                SELECT COUNT(*) as cnt FROM panel
                WHERE id = ANY($1::text[]) AND marital_status = '기혼'
            """, panel_ids_1)
            result_2 = await Database.fetchrow("""
                SELECT COUNT(*) as cnt FROM panel
                WHERE id = ANY($1::text[]) AND marital_status = '기혼'
            """, panel_ids_2)

            married_1 = result_1['cnt'] if result_1 else 0
            married_2 = result_2['cnt'] if result_2 else 0

            if married_1 + married_2 > 0:
                total = married_1 + married_2
                pct_1 = round(married_1 / total * 100, 2)
                pct_2 = round(married_2 / total * 100, 2)
                diff = abs(pct_1 - pct_2)

                if diff >= 10:
                    characteristics.append({
                        "characteristic": "기혼자 비율",
                        "cohort_1_percentage": pct_1,
                        "cohort_2_percentage": pct_2,
                        "cohort_1_count": married_1,
                        "cohort_2_count": married_2,
                        "difference_percentage": diff,
                        "sort_key": diff
                    })
        except Exception:
            pass

        characteristics.sort(key=lambda x: x["sort_key"], reverse=True)

        return [
            CharacteristicComparison(**{k: v for k, v in c.items() if k != "sort_key"})
            for c in characteristics[:3]
        ]

    async def _calculate_region_distribution(
        self,
        panel_ids_1: List[str],
        panel_ids_2: List[str],
        count_1: int,
        count_2: int
    ) -> Optional[RegionDistribution]:
        try:
            from src.core.database import Database
            major_provinces = ["서울", "경기", "부산"]

            rows_1 = await Database.fetch("""
                SELECT COALESCE(region, residence) as region_value, COUNT(*) as cnt
                FROM panel
                WHERE id = ANY($1::text[])
                AND (region IS NOT NULL OR residence IS NOT NULL)
                GROUP BY COALESCE(region, residence)
            """, panel_ids_1)

            region_stats_1 = {}
            other_count_1 = 0

            for row in rows_1:
                region_value = row['region_value']
                count = row['cnt']
                province = None

                if region_value:
                    parts = str(region_value).split()
                    if parts:
                        first_part = parts[0]
                        if first_part in major_provinces:
                            province = first_part
                        else:
                            for p in major_provinces:
                                if first_part.startswith(p) or p in first_part:
                                    province = p
                                    break

                if province:
                    region_stats_1[province] = region_stats_1.get(province, 0) + count
                else:
                    other_count_1 += count

            rows_2 = await Database.fetch("""
                SELECT COALESCE(region, residence) as region_value, COUNT(*) as cnt
                FROM panel
                WHERE id = ANY($1::text[])
                AND (region IS NOT NULL OR residence IS NOT NULL)
                GROUP BY COALESCE(region, residence)
            """, panel_ids_2)

            region_stats_2 = {}
            other_count_2 = 0

            for row in rows_2:
                region_value = row['region_value']
                count = row['cnt']
                province = None

                if region_value:
                    parts = str(region_value).split()
                    if parts:
                        first_part = parts[0]
                        if first_part in major_provinces:
                            province = first_part
                        else:
                            for p in major_provinces:
                                if first_part.startswith(p) or p in first_part:
                                    province = p
                                    break

                if province:
                    region_stats_2[province] = region_stats_2.get(province, 0) + count
                else:
                    other_count_2 += count

            region_pct_1 = {r: round(c / count_1 * 100, 2) for r, c in region_stats_1.items()}
            if other_count_1 > 0:
                region_pct_1["기타"] = round(other_count_1 / count_1 * 100, 2)

            region_pct_2 = {r: round(c / count_2 * 100, 2) for r, c in region_stats_2.items()}
            if other_count_2 > 0:
                region_pct_2["기타"] = round(other_count_2 / count_2 * 100, 2)

            if not region_pct_1 and not region_pct_2:
                return None

            return RegionDistribution(cohort_1=region_pct_1, cohort_2=region_pct_2)

        except Exception:
            return None

    async def _calculate_gender_distribution(
        self,
        panel_ids_1: List[str],
        panel_ids_2: List[str],
        count_1: int,
        count_2: int
    ) -> Optional[GenderDistribution]:
        try:
            from src.core.database import Database

            rows_1 = await Database.fetch("""
                SELECT gender, COUNT(*) as cnt FROM panel
                WHERE id = ANY($1::text[]) AND gender IS NOT NULL AND gender != ''
                GROUP BY gender
            """, panel_ids_1)

            gender_stats_1 = {}
            for row in rows_1:
                gender = str(row['gender']).upper()
                gender_stats_1[gender] = row['cnt']

            rows_2 = await Database.fetch("""
                SELECT gender, COUNT(*) as cnt FROM panel
                WHERE id = ANY($1::text[]) AND gender IS NOT NULL AND gender != ''
                GROUP BY gender
            """, panel_ids_2)

            gender_stats_2 = {}
            for row in rows_2:
                gender = str(row['gender']).upper()
                gender_stats_2[gender] = row['cnt']

            gender_pct_1 = {}
            if count_1 > 0:
                gender_pct_1["남성"] = round(gender_stats_1.get('MALE', 0) / count_1 * 100, 2)
                gender_pct_1["여성"] = round(gender_stats_1.get('FEMALE', 0) / count_1 * 100, 2)

            gender_pct_2 = {}
            if count_2 > 0:
                gender_pct_2["남성"] = round(gender_stats_2.get('MALE', 0) / count_2 * 100, 2)
                gender_pct_2["여성"] = round(gender_stats_2.get('FEMALE', 0) / count_2 * 100, 2)

            if not gender_pct_1 and not gender_pct_2:
                return None

            return GenderDistribution(cohort_1=gender_pct_1, cohort_2=gender_pct_2)

        except Exception:
            return None

    async def _generate_insights(
        self,
        cohort_1: CohortBasicInfo,
        cohort_2: CohortBasicInfo,
        panel_ids_1: List[str],
        panel_ids_2: List[str],
        comparisons: List[MetricComparison],
        basic_info: List[BasicInfoComparison],
        characteristics: List[CharacteristicComparison]
    ) -> Optional[KeyInsights]:
        try:
            hashtags_1 = await self.panel_repo.get_hashtags_sample(panel_ids_1, 50)
            hashtags_2 = await self.panel_repo.get_hashtags_sample(panel_ids_2, 50)

            flat_tags_1 = [tag for tags in hashtags_1 for tag in tags]
            flat_tags_2 = [tag for tags in hashtags_2 for tag in tags]

            top_tags_1 = [tag for tag, _ in Counter(flat_tags_1).most_common(5)]
            top_tags_2 = [tag for tag, _ in Counter(flat_tags_2).most_common(5)]

            cohort_1_info = {
                "name": cohort_1.cohort_name,
                "panel_count": cohort_1.panel_count,
                "hash_tags_summary": top_tags_1
            }
            cohort_2_info = {
                "name": cohort_2.cohort_name,
                "panel_count": cohort_2.panel_count,
                "hash_tags_summary": top_tags_2
            }

            comparisons_data = [
                {
                    "metric_label": c.metric_label,
                    "cohort_1_data": c.cohort_1_data,
                    "cohort_2_data": c.cohort_2_data,
                    "is_significant": c.statistical_test.get("is_significant", False) if c.statistical_test else False
                }
                for c in comparisons
            ]

            basic_info_data = [
                {
                    "metric_label": b.metric_label,
                    "cohort_1_value": b.cohort_1_value,
                    "cohort_2_value": b.cohort_2_value,
                    "difference": b.difference
                }
                for b in basic_info if b.cohort_1_value is not None and b.cohort_2_value is not None
            ]

            characteristics_data = [
                {
                    "characteristic": ch.characteristic,
                    "cohort_1_percentage": ch.cohort_1_percentage,
                    "cohort_2_percentage": ch.cohort_2_percentage
                }
                for ch in characteristics
            ]

            return await self.insight_generator.generate_cohort_insights(
                cohort_1_info, cohort_2_info,
                comparisons_data, basic_info_data, characteristics_data
            )

        except Exception:
            return None

    def _generate_summary(
        self,
        cohort_1: CohortBasicInfo,
        cohort_2: CohortBasicInfo,
        comparisons: List[MetricComparison]
    ) -> Dict[str, Any]:
        significant_count = sum(
            1 for c in comparisons
            if c.statistical_test and c.statistical_test.get('is_significant')
        )

        return {
            "total_metrics": len(comparisons),
            "significant_differences": significant_count,
            "comparison_summary": f"{cohort_1.cohort_name} ({cohort_1.panel_count}명) vs {cohort_2.cohort_name} ({cohort_2.panel_count}명)",
            "interpretation": f"{len(comparisons)}개 메트릭 중 {significant_count}개에서 유의미한 차이가 발견되었습니다."
        }

    def _perform_chi_square_test(self, data_1: Dict, data_2: Dict) -> Dict[str, Any]:
        try:
            categories = sorted(set(data_1.keys()) | set(data_2.keys()))

            if len(categories) < 2:
                return {
                    "test_type": "chi_square",
                    "error": "Not enough categories",
                    "is_significant": False
                }

            observed = [
                [data_1.get(cat, 0) for cat in categories],
                [data_2.get(cat, 0) for cat in categories]
            ]

            if all(val == 0 for row in observed for val in row):
                return {
                    "test_type": "chi_square",
                    "error": "All values are zero",
                    "is_significant": False
                }

            chi2, p_value, dof, _ = stats.chi2_contingency(observed)

            p_value_float = float(p_value)
            is_significant = bool(p_value_float < 0.05)

            return {
                "test_type": "chi_square",
                "chi_square": round(float(chi2), 4),
                "p_value": round(p_value_float, 4),
                "degrees_of_freedom": int(dof),
                "is_significant": is_significant,
                "interpretation": "두 그룹 간 유의미한 차이가 있습니다." if is_significant else "두 그룹 간 유의미한 차이가 없습니다."
            }

        except Exception as e:
            return {
                "test_type": "chi_square",
                "error": str(e),
                "is_significant": False
            }

    def get_available_metrics(self) -> List[Dict[str, str]]:
        return [{"name": m[0], "label": m[1]} for m in COMPARISON_METRICS]
