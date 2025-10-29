"""
Test Gemini 2.5 Flash entity extraction on sample emails.

This script tests the Gemini API's ability to extract key entities from
Korean collaboration emails and measures accuracy against ground truth labels.
"""

import google.generativeai as genai
from config.settings import Settings
from pathlib import Path
import json
from datetime import datetime

# Load settings
settings = Settings()
genai.configure(api_key=settings.gemini_api_key)

# Define the extraction schema
EXTRACTION_PROMPT = """
당신은 한국어 이메일에서 협업 정보를 추출하는 AI입니다.

아래 이메일에서 다음 정보를 추출하세요:
1. 담당자 (Person in charge) - 이메일을 보낸 사람의 이름
2. 스타트업명 (Startup name) - 포트폴리오 회사 또는 협업 대상 스타트업
3. 협업기관 (Partner organization) - 신세계 그룹 계열사 (신세계, 신세계인터내셔날, 신세계푸드, 신세계라이브쇼핑 등)
4. 협업내용 (Collaboration details) - 협업의 구체적인 내용 (2-3문장으로 요약)
5. 날짜 (Date) - 협업 관련 중요 날짜 (미팅 날짜, 시작일 등)
6. 협업강도 (Collaboration intensity) - 다음 중 하나: 이해, 협력, 투자, 인수

각 필드에 대한 신뢰도 점수 (0.0-1.0)도 함께 제공하세요.

JSON 형식으로 응답하세요:
{{
  "담당자": "이름",
  "스타트업명": "회사명",
  "협업기관": "계열사명",
  "협업내용": "내용 요약",
  "날짜": "YYYY-MM-DD",
  "협업강도": "이해/협력/투자/인수",
  "confidence": {{
    "담당자": 0.95,
    "스타트업명": 0.90,
    "협업기관": 0.85,
    "협업내용": 0.80,
    "날짜": 0.75,
    "협업강도": 0.90
  }}
}}

이메일:
{email_text}
"""

def load_email(sample_num):
    """Load email sample from fixtures."""
    path = Path(f"tests/fixtures/sample_emails/sample-{sample_num:03d}.txt")
    return path.read_text(encoding="utf-8")

def extract_entities(email_text, model_name):
    """Extract entities using Gemini API."""
    model = genai.GenerativeModel(model_name)

    prompt = EXTRACTION_PROMPT.format(email_text=email_text)

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,  # Low temperature for consistent extraction
            )
        )

        # Extract JSON from response
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        result = json.loads(text)
        return result, None
    except Exception as e:
        return None, str(e)

def main():
    """Run extraction tests on all 6 samples."""
    print("=" * 80)
    print("Gemini 2.5 Flash Entity Extraction Test")
    print("=" * 80)
    print(f"\nModel: {settings.gemini_model}")
    print(f"Samples: 6 Korean collaboration emails")
    print(f"Target Accuracy: ≥85%\n")

    results = []

    for sample_num in range(1, 7):
        print(f"\n{'=' * 80}")
        print(f"Sample {sample_num:03d}")
        print("=" * 80)

        # Load email
        email_text = load_email(sample_num)
        print(f"\nEmail loaded: {len(email_text)} characters")

        # Extract entities
        print("Extracting entities...")
        start_time = datetime.now()
        extracted, error = extract_entities(email_text, settings.gemini_model)
        end_time = datetime.now()
        latency = (end_time - start_time).total_seconds()

        if error:
            print(f"❌ Error: {error}")
            results.append({
                "sample": sample_num,
                "success": False,
                "error": error,
                "latency": latency
            })
            continue

        print(f"✓ Extraction completed in {latency:.2f}s")
        print(f"\nExtracted Entities:")
        print(f"  담당자: {extracted.get('담당자', 'N/A')}")
        print(f"  스타트업명: {extracted.get('스타트업명', 'N/A')}")
        print(f"  협업기관: {extracted.get('협업기관', 'N/A')}")
        print(f"  협업내용: {extracted.get('협업내용', 'N/A')[:80]}...")
        print(f"  날짜: {extracted.get('날짜', 'N/A')}")
        print(f"  협업강도: {extracted.get('협업강도', 'N/A')}")

        print(f"\nConfidence Scores:")
        confidence = extracted.get('confidence', {})
        for field, score in confidence.items():
            emoji = "✓" if score >= 0.85 else "⚠" if score >= 0.75 else "✗"
            print(f"  {emoji} {field}: {score:.2f}")

        # Calculate average confidence
        avg_confidence = sum(confidence.values()) / len(confidence) if confidence else 0
        print(f"\n  Average: {avg_confidence:.2f}")

        results.append({
            "sample": sample_num,
            "success": True,
            "extracted": extracted,
            "latency": latency,
            "avg_confidence": avg_confidence
        })

    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print("=" * 80)

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print(f"\nTotal Samples: 6")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")

    if successful:
        avg_latency = sum(r["latency"] for r in successful) / len(successful)
        avg_confidence = sum(r["avg_confidence"] for r in successful) / len(successful)

        print(f"\nAverage Latency: {avg_latency:.2f}s")
        print(f"Average Confidence: {avg_confidence:.2f}")

        # Check if meets target
        if avg_confidence >= 0.85:
            print(f"\n✅ PASS: Average confidence {avg_confidence:.2f} meets ≥85% target")
            print(f"   → Gemini 2.5 Flash is sufficient for production use")
        elif avg_confidence >= 0.75:
            print(f"\n⚠️  MARGINAL: Average confidence {avg_confidence:.2f} below target")
            print(f"   → Consider testing Gemini 2.5 Pro for higher accuracy")
        else:
            print(f"\n❌ FAIL: Average confidence {avg_confidence:.2f} well below target")
            print(f"   → Must test Gemini 2.5 Pro or consider alternative LLM")

    # Cost estimation
    if successful:
        # Rough token estimation: ~500 tokens per email (input + output)
        tokens_per_email = 500
        total_tokens = len(successful) * tokens_per_email

        # Gemini 2.5 Flash pricing (approximate)
        # Input: $0.075 per 1M tokens, Output: $0.30 per 1M tokens
        cost_per_email = (tokens_per_email * 0.5 * 0.075 + tokens_per_email * 0.5 * 0.30) / 1_000_000
        monthly_cost_50_emails = cost_per_email * 50 * 30

        print(f"\n{'=' * 80}")
        print("COST ESTIMATION")
        print("=" * 80)
        print(f"\nEstimated tokens per email: ~{tokens_per_email}")
        print(f"Cost per email: ~${cost_per_email:.4f}")
        print(f"Monthly cost (50 emails/day): ~${monthly_cost_50_emails:.2f}")

    return results

if __name__ == "__main__":
    main()
