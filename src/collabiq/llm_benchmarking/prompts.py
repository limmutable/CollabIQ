"""Prompt variations for LLM benchmarking.

This module defines different prompt templates for testing and optimizing
LLM performance on Korean and English text extraction.

Each prompt variation is designed to test different aspects:
- Baseline: Standard extraction prompt
- Korean-optimized: Enhanced for Korean language patterns
- Explicit-format: Clear field definitions and examples
- Few-shot: Includes examples for better accuracy
"""

from typing import Dict, List


# Prompt variation IDs
BASELINE = "baseline"
KOREAN_OPTIMIZED = "korean_optimized"
EXPLICIT_FORMAT = "explicit_format"
FEW_SHOT = "few_shot"
STRUCTURED_OUTPUT = "structured_output"


def get_baseline_prompt() -> str:
    """Get baseline extraction prompt.

    Standard prompt without special optimization.

    Returns:
        Prompt template string
    """
    return """Extract the following 5 entities from this email:

1. person_in_charge (담당자): Person responsible
2. startup_name (스타트업명): Startup company name
3. partner_org (협업기관): Partner organization
4. details (협업내용): Collaboration details
5. date (날짜): Date mentioned in the email

Provide confidence scores (0.0-1.0) for each field.

Return as JSON with this structure:
{{
    "person_in_charge": "Name or null",
    "startup_name": "Name or null",
    "partner_org": "Name or null",
    "details": "Description",
    "date": "YYYY-MM-DD or null",
    "confidence": {{
        "person": 0.95,
        "startup": 0.90,
        "partner": 0.85,
        "details": 0.92,
        "date": 0.88
    }}
}}

Email text:
{email_text}"""


def get_korean_optimized_prompt() -> str:
    """Get Korean-optimized extraction prompt.

    Enhanced prompt specifically designed for Korean language patterns,
    cultural context, and naming conventions.

    Returns:
        Prompt template string
    """
    return """다음 이메일에서 5가지 핵심 정보를 추출해주세요.

한국어 텍스트 분석 가이드라인:
- 인명: 한글 이름 (예: 김철수, 이영희) 또는 영문 이름
- 회사명: 한글 또는 영문 스타트업/기업명
- 기관명: 파트너 조직 (정부기관, 대기업, 단체 등)
- 날짜: 한국어 날짜 표현 (예: 2024년 11월 13일, 11월 1주, 어제)

추출할 정보:
1. person_in_charge (담당자): 책임자 또는 연락 담당자
2. startup_name (스타트업명): 협업 대상 스타트업 이름
3. partner_org (협업기관): 파트너 조직/기관
4. details (협업내용): 구체적인 협업 내용과 맥락
5. date (날짜): 언급된 날짜 (YYYY-MM-DD 형식으로 변환)

각 필드의 신뢰도 (0.0-1.0)를 함께 제공하세요.

JSON 형식으로 반환:
{{{{
    "person_in_charge": "이름 또는 null",
    "startup_name": "이름 또는 null",
    "partner_org": "이름 또는 null",
    "details": "상세 설명",
    "date": "YYYY-MM-DD 또는 null",
    "confidence": {{{{
        "person": 0.95,
        "startup": 0.90,
        "partner": 0.85,
        "details": 0.92,
        "date": 0.88
    }}}}
}}}}

이메일 텍스트:
{email_text}"""


def get_explicit_format_prompt() -> str:
    """Get explicit format prompt with clear field definitions.

    Detailed prompt with explicit instructions and field definitions.

    Returns:
        Prompt template string
    """
    return """You are an expert at extracting structured information from collaboration emails.

Extract exactly 5 entities with high accuracy:

**1. person_in_charge (담당자)**
   - WHO: Person's full name mentioned in the email
   - Could be: Sender, contact person, or person managing the collaboration
   - Korean names: 2-4 characters (예: 김철수)
   - English names: First and last name
   - Return null if no person is mentioned

**2. startup_name (스타트업명)**
   - WHAT: Name of the startup company involved
   - Look for: Company names, startup brands, service names
   - Korean: 한글 이름 (예: 본봄, 데이블매니저)
   - English: Service/company names
   - Return null if no startup is mentioned

**3. partner_org (협업기관)**
   - WHO: Partner organization or institution
   - Could be: Large companies (신세계), government agencies, institutions
   - Return null if no partner is mentioned

**4. details (협업내용)**
   - WHAT: Specific collaboration activities and context
   - Include: Type of work, pilot programs, meetings, projects
   - Preserve original wording when possible
   - Required field - extract main topic if no details given

**5. date (날짜)**
   - WHEN: Date mentioned in email
   - Formats: Korean (2024년 11월 13일, 11월 1주, 어제)
   - Formats: English (January 15, 2025, yesterday)
   - Convert to: YYYY-MM-DD
   - Return null if no date is mentioned

**Confidence Scores (0.0-1.0):**
- 1.0: Explicitly stated, no ambiguity
- 0.9: Very clear from context
- 0.7-0.8: Somewhat clear, minor ambiguity
- 0.5-0.6: Uncertain, guessing
- 0.0: No information found

Return JSON:
{{{{
    "person_in_charge": "Name or null",
    "startup_name": "Name or null",
    "partner_org": "Name or null",
    "details": "Description",
    "date": "YYYY-MM-DD or null",
    "confidence": {{{{
        "person": 0.0-1.0,
        "startup": 0.0-1.0,
        "partner": 0.0-1.0,
        "details": 0.0-1.0,
        "date": 0.0-1.0
    }}}}
}}}}

Email:
{email_text}"""


def get_few_shot_prompt() -> str:
    """Get few-shot prompt with examples.

    Includes example extractions to improve accuracy through demonstration.

    Returns:
        Prompt template string
    """
    return """Extract 5 key entities from the email text. Here are examples:

**Example 1:**
Email: "어제 신세계와 본봄 파일럿 킥오프 미팅을 진행했습니다. 담당자는 김철수입니다."
Output:
{{{{
    "person_in_charge": "김철수",
    "startup_name": "본봄",
    "partner_org": "신세계",
    "details": "파일럿 킥오프 미팅",
    "date": "2024-11-12",
    "confidence": {{{{
        "person": 0.95,
        "startup": 0.98,
        "partner": 0.98,
        "details": 0.92,
        "date": 0.85
    }}}}
}}}}

**Example 2:**
Email: "TableManager kicked off pilot with Shinsegae yesterday. Contact: John Kim."
Output:
{{{{
    "person_in_charge": "John Kim",
    "startup_name": "TableManager",
    "partner_org": "Shinsegae",
    "details": "kicked off pilot",
    "date": "2024-11-12",
    "confidence": {{{{
        "person": 0.95,
        "startup": 0.92,
        "partner": 0.90,
        "details": 0.88,
        "date": 0.85
    }}}}
}}}}

**Example 3:**
Email: "11월 1주에 스마트시티 프로젝트 관련 회의 예정"
Output:
{{{{
    "person_in_charge": null,
    "startup_name": null,
    "partner_org": null,
    "details": "스마트시티 프로젝트 관련 회의",
    "date": "2024-11-01",
    "confidence": {{{{
        "person": 0.0,
        "startup": 0.0,
        "partner": 0.0,
        "details": 0.90,
        "date": 0.88
    }}}}
}}}}

Now extract from this email:
{email_text}

Return JSON with same structure as examples above."""


def get_structured_output_prompt() -> str:
    """Get structured output prompt with strict schema enforcement.

    Emphasizes JSON structure and schema compliance.

    Returns:
        Prompt template string
    """
    return """TASK: Extract structured data from email in strict JSON format.

REQUIRED OUTPUT SCHEMA:
{{{{
    "person_in_charge": string | null,
    "startup_name": string | null,
    "partner_org": string | null,
    "details": string (required, non-empty),
    "date": string (YYYY-MM-DD format) | null,
    "confidence": {{{{
        "person": float (0.0-1.0),
        "startup": float (0.0-1.0),
        "partner": float (0.0-1.0),
        "details": float (0.0-1.0),
        "date": float (0.0-1.0)
    }}}}
}}}}

EXTRACTION RULES:
1. person_in_charge: Full name of person mentioned (null if none)
2. startup_name: Startup/company name (null if none)
3. partner_org: Partner organization name (null if none)
4. details: Main content/topic (ALWAYS extract, never null)
5. date: Parse to YYYY-MM-DD (null if no date found)

CONFIDENCE GUIDELINES:
- Explicit mention: 0.9-1.0
- Clear from context: 0.7-0.9
- Inferred/guessed: 0.5-0.7
- Not found: 0.0

VALIDATION:
- ALL fields must be present
- Confidence values must be 0.0-1.0
- Date must be valid YYYY-MM-DD or null
- Output must be valid JSON

EMAIL TEXT:
{email_text}

OUTPUT (JSON only, no explanation):"""


def get_all_prompts() -> Dict[str, str]:
    """Get all available prompt variations.

    Returns:
        Dictionary mapping prompt IDs to prompt templates
    """
    return {
        BASELINE: get_baseline_prompt(),
        KOREAN_OPTIMIZED: get_korean_optimized_prompt(),
        EXPLICIT_FORMAT: get_explicit_format_prompt(),
        FEW_SHOT: get_few_shot_prompt(),
        STRUCTURED_OUTPUT: get_structured_output_prompt(),
    }


def get_prompt_by_id(prompt_id: str) -> str:
    """Get prompt template by ID.

    Args:
        prompt_id: Prompt variation ID (e.g., "baseline", "korean_optimized")

    Returns:
        Prompt template string

    Raises:
        ValueError: If prompt_id is not recognized

    Examples:
        >>> prompt = get_prompt_by_id("korean_optimized")
        >>> formatted = prompt.format(email_text="어제 신세계와 본봄 킥오프")
    """
    prompts = get_all_prompts()
    if prompt_id not in prompts:
        valid_ids = ", ".join(prompts.keys())
        raise ValueError(f"Unknown prompt ID '{prompt_id}'. Valid IDs: {valid_ids}")
    return prompts[prompt_id]


def list_prompt_ids() -> List[str]:
    """Get list of all available prompt IDs.

    Returns:
        List of prompt variation IDs

    Examples:
        >>> ids = list_prompt_ids()
        >>> print(ids)
        ['baseline', 'korean_optimized', 'explicit_format', 'few_shot', 'structured_output']
    """
    return list(get_all_prompts().keys())


def get_prompt_description(prompt_id: str) -> str:
    """Get human-readable description of a prompt variation.

    Args:
        prompt_id: Prompt variation ID

    Returns:
        Description string

    Raises:
        ValueError: If prompt_id is not recognized
    """
    descriptions = {
        BASELINE: "Standard extraction prompt without special optimization",
        KOREAN_OPTIMIZED: "Enhanced for Korean language patterns and cultural context",
        EXPLICIT_FORMAT: "Detailed instructions with clear field definitions",
        FEW_SHOT: "Includes example extractions for improved accuracy",
        STRUCTURED_OUTPUT: "Strict JSON schema enforcement with validation rules",
    }

    if prompt_id not in descriptions:
        valid_ids = ", ".join(descriptions.keys())
        raise ValueError(f"Unknown prompt ID '{prompt_id}'. Valid IDs: {valid_ids}")

    return descriptions[prompt_id]


# Public API
__all__ = [
    "BASELINE",
    "KOREAN_OPTIMIZED",
    "EXPLICIT_FORMAT",
    "FEW_SHOT",
    "STRUCTURED_OUTPUT",
    "get_baseline_prompt",
    "get_korean_optimized_prompt",
    "get_explicit_format_prompt",
    "get_few_shot_prompt",
    "get_structured_output_prompt",
    "get_all_prompts",
    "get_prompt_by_id",
    "list_prompt_ids",
    "get_prompt_description",
]
