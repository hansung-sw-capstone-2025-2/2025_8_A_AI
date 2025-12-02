SEMANTIC_FIELDS = [
    'lifestyle_tags', 'search_keywords',
    'survey_health', 'survey_consumption',
    'survey_lifestyle', 'survey_digital', 'survey_environment'
]

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

VALID_COLUMNS = {
    'age', 'age_group', 'gender', 'residence', 'occupation',
    'marital_status', 'phone_brand', 'car_brand',
    'smoking_experience', 'drinking_experience', 'electronic_devices',
    'cigarette_brands', 'e_cigarette'
}

NEGATIVE_RESPONSES = {
    'smoking_experience': '담배를 피워본 적이 없다',
    'drinking_experience': '최근 1년 이내 술을 마시지 않음'
}

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

AGE_GROUP_EXPANSIONS = {
    "10대": ["10대", "20대 초반"],
    "20대": ["10대 후반", "20대", "30대 초반"],
    "30대": ["20대 후반", "30대", "40대 초반"],
    "40대": ["30대 후반", "40대", "50대 초반"],
    "50대": ["40대 후반", "50대", "60대 초반"],
    "60대": ["50대 후반", "60대", "70대 초반"],
}

RESIDENCE_EXPANSIONS = {
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

GENDER_MAPPING = {
    "남성": "MALE",
    "남": "MALE",
    "여성": "FEMALE",
    "여": "FEMALE"
}
