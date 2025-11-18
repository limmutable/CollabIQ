"""Integration tests for LLM prompt variations and A/B testing.

Tests cover:
- Prompt variation functionality
- A/B testing framework
- Benchmarking suite with real-world scenarios
- Performance comparison between prompts
- Korean and English text handling
"""

import pytest

from src.collabiq.llm_benchmarking import (
    BASELINE,
    EXPLICIT_FORMAT,
    FEW_SHOT,
    KOREAN_OPTIMIZED,
    STRUCTURED_OUTPUT,
    ABTestFramework,
    BenchmarkSuite,
    get_all_prompts,
    get_prompt_by_id,
    list_prompt_ids,
)


class TestPromptVariations:
    """Tests for prompt variation functionality."""

    def test_all_prompts_available(self):
        """Test that all prompt variations are available."""
        prompts = get_all_prompts()

        assert BASELINE in prompts
        assert KOREAN_OPTIMIZED in prompts
        assert EXPLICIT_FORMAT in prompts
        assert FEW_SHOT in prompts
        assert STRUCTURED_OUTPUT in prompts

        # At least 5 prompt variations
        assert len(prompts) >= 5

    def test_list_prompt_ids(self):
        """Test listing all prompt IDs."""
        ids = list_prompt_ids()

        assert isinstance(ids, list)
        assert len(ids) >= 5
        assert BASELINE in ids
        assert KOREAN_OPTIMIZED in ids

    def test_get_prompt_by_id_baseline(self):
        """Test getting baseline prompt."""
        prompt = get_prompt_by_id(BASELINE)

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "{email_text}" in prompt
        assert "person_in_charge" in prompt.lower() or "담당자" in prompt

    def test_get_prompt_by_id_korean_optimized(self):
        """Test getting Korean-optimized prompt."""
        prompt = get_prompt_by_id(KOREAN_OPTIMIZED)

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "{email_text}" in prompt
        # Should contain Korean text
        assert "담당자" in prompt or "스타트업" in prompt

    def test_get_prompt_by_id_explicit_format(self):
        """Test getting explicit format prompt."""
        prompt = get_prompt_by_id(EXPLICIT_FORMAT)

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "{email_text}" in prompt
        # Should have detailed instructions
        assert len(prompt) > 500  # Longer than baseline

    def test_get_prompt_by_id_few_shot(self):
        """Test getting few-shot prompt."""
        prompt = get_prompt_by_id(FEW_SHOT)

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "{email_text}" in prompt
        # Should contain examples
        assert "example" in prompt.lower()

    def test_get_prompt_by_id_structured_output(self):
        """Test getting structured output prompt."""
        prompt = get_prompt_by_id(STRUCTURED_OUTPUT)

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "{email_text}" in prompt
        # Should emphasize structure
        assert "json" in prompt.lower() or "schema" in prompt.lower()

    def test_get_prompt_by_id_invalid(self):
        """Test error handling for invalid prompt ID."""
        with pytest.raises(ValueError) as exc_info:
            get_prompt_by_id("nonexistent_prompt")

        assert "Unknown prompt ID" in str(exc_info.value)
        assert "Valid IDs" in str(exc_info.value)

    def test_prompt_formatting(self):
        """Test that prompts can be formatted with email text."""
        prompt_template = get_prompt_by_id(BASELINE)
        email_text = "어제 신세계와 본봄 킥오프 미팅"

        formatted = prompt_template.format(email_text=email_text)

        assert email_text in formatted
        assert "{email_text}" not in formatted


class TestPromptVariationContent:
    """Tests for prompt variation content and structure."""

    def test_baseline_prompt_structure(self):
        """Test baseline prompt has required structure."""
        prompt = get_prompt_by_id(BASELINE)

        # Should mention all 5 entities
        assert "person_in_charge" in prompt
        assert "startup_name" in prompt
        assert "partner_org" in prompt
        assert "details" in prompt
        assert "date" in prompt

        # Should request confidence scores
        assert "confidence" in prompt.lower()

    def test_korean_optimized_prompt_korean_content(self):
        """Test Korean-optimized prompt contains Korean language."""
        prompt = get_prompt_by_id(KOREAN_OPTIMIZED)

        # Should have Korean instructions
        korean_chars = ["담당자", "스타트업", "협업", "날짜", "신뢰도"]
        korean_count = sum(1 for char in korean_chars if char in prompt)

        assert korean_count >= 3  # At least 3 Korean terms

    def test_explicit_format_prompt_details(self):
        """Test explicit format prompt has detailed instructions."""
        prompt = get_prompt_by_id(EXPLICIT_FORMAT)

        # Should have field explanations
        assert "WHO:" in prompt or "WHAT:" in prompt or "WHEN:" in prompt

        # Should define confidence scoring
        assert "0.0" in prompt and "1.0" in prompt

    def test_few_shot_prompt_examples(self):
        """Test few-shot prompt includes examples."""
        prompt = get_prompt_by_id(FEW_SHOT)

        # Should have multiple examples
        assert prompt.count("Example") >= 2

        # Examples should show expected output format
        assert prompt.count("Output:") >= 2 or prompt.count("{{") >= 2

    def test_structured_output_prompt_schema(self):
        """Test structured output prompt defines schema."""
        prompt = get_prompt_by_id(STRUCTURED_OUTPUT)

        # Should define output schema
        assert "schema" in prompt.lower() or "format" in prompt.lower()

        # Should have validation rules
        assert "valid" in prompt.lower() or "required" in prompt.lower()


class TestBenchmarkingSuite:
    """Tests for benchmarking suite functionality (without real LLM calls)."""

    def test_benchmark_suite_initialization(self):
        """Test benchmark suite can be initialized."""
        suite = BenchmarkSuite()

        assert suite is not None
        assert suite.output_dir is not None
        assert suite.output_dir.exists()

    def test_benchmark_suite_custom_output_dir(self, tmp_path):
        """Test benchmark suite with custom output directory."""
        custom_dir = tmp_path / "custom_benchmarks"
        suite = BenchmarkSuite(output_dir=custom_dir)

        assert suite.output_dir == custom_dir
        assert custom_dir.exists()


class TestABTestingFramework:
    """Tests for A/B testing framework (without real LLM calls)."""

    def test_ab_framework_initialization(self):
        """Test A/B testing framework can be initialized."""
        framework = ABTestFramework()

        assert framework is not None
        assert framework.output_dir is not None
        assert framework.output_dir.exists()
        assert framework.suite is not None

    def test_ab_framework_custom_output_dir(self, tmp_path):
        """Test A/B framework with custom output directory."""
        custom_dir = tmp_path / "custom_ab_tests"
        framework = ABTestFramework(output_dir=custom_dir)

        assert framework.output_dir == custom_dir
        assert custom_dir.exists()


class TestPromptComparisonLogic:
    """Tests for prompt comparison logic."""

    def test_improvement_calculation_positive(self):
        """Test improvement calculation for better performance."""
        framework = ABTestFramework()

        # Comparison is better
        improvement = framework._calculate_improvement(
            baseline_value=0.8, comparison_value=0.9, lower_is_better=False
        )

        assert improvement > 0  # Positive improvement
        assert pytest.approx(improvement, abs=0.1) == 12.5  # (0.9-0.8)/0.8 * 100

    def test_improvement_calculation_negative(self):
        """Test improvement calculation for worse performance."""
        framework = ABTestFramework()

        # Comparison is worse
        improvement = framework._calculate_improvement(
            baseline_value=0.9, comparison_value=0.8, lower_is_better=False
        )

        assert improvement < 0  # Negative improvement (degradation)
        assert pytest.approx(improvement, abs=0.1) == -11.1  # (0.8-0.9)/0.9 * 100

    def test_improvement_calculation_lower_is_better(self):
        """Test improvement calculation when lower values are better."""
        framework = ABTestFramework()

        # Lower response time is better
        improvement = framework._calculate_improvement(
            baseline_value=3.0, comparison_value=2.0, lower_is_better=True
        )

        assert improvement > 0  # Positive improvement (faster)
        assert pytest.approx(improvement, abs=0.1) == 33.3  # (3.0-2.0)/3.0 * 100


class TestPromptVariationDifferences:
    """Tests to verify different prompts produce different outputs."""

    def test_baseline_vs_korean_optimized_different(self):
        """Test baseline and Korean-optimized prompts are different."""
        baseline = get_prompt_by_id(BASELINE)
        korean_opt = get_prompt_by_id(KOREAN_OPTIMIZED)

        assert baseline != korean_opt
        assert len(korean_opt) != len(baseline)

    def test_baseline_vs_few_shot_different(self):
        """Test baseline and few-shot prompts are different."""
        baseline = get_prompt_by_id(BASELINE)
        few_shot = get_prompt_by_id(FEW_SHOT)

        assert baseline != few_shot
        # Few-shot should be longer (includes examples)
        assert len(few_shot) > len(baseline)

    def test_all_prompts_unique(self):
        """Test all prompts are unique."""
        prompts = get_all_prompts()
        prompt_texts = list(prompts.values())

        # No duplicates
        assert len(prompt_texts) == len(set(prompt_texts))


class TestIntegrationScenarios:
    """Integration tests for end-to-end scenarios."""

    def test_prompt_selection_workflow(self):
        """Test complete workflow of selecting and using a prompt."""
        # 1. List available prompts
        ids = list_prompt_ids()
        assert len(ids) > 0

        # 2. Select a prompt
        prompt_id = ids[0]

        # 3. Get the prompt
        prompt = get_prompt_by_id(prompt_id)
        assert len(prompt) > 0

        # 4. Format with email text
        email_text = "Test email content"
        formatted = prompt.format(email_text=email_text)
        assert email_text in formatted

    def test_multiple_prompts_for_comparison(self):
        """Test preparing multiple prompts for A/B testing."""
        # Get baseline and alternative
        baseline = get_prompt_by_id(BASELINE)
        korean_opt = get_prompt_by_id(KOREAN_OPTIMIZED)
        few_shot = get_prompt_by_id(FEW_SHOT)

        email_text = "어제 신세계와 본봄 킥오프"

        # Format all with same email
        formatted_baseline = baseline.format(email_text=email_text)
        formatted_korean = korean_opt.format(email_text=email_text)
        formatted_few_shot = few_shot.format(email_text=email_text)

        # All should contain the email text
        assert email_text in formatted_baseline
        assert email_text in formatted_korean
        assert email_text in formatted_few_shot

        # But prompts should be different
        assert formatted_baseline != formatted_korean
        assert formatted_baseline != formatted_few_shot


class TestErrorHandling:
    """Tests for error handling in benchmarking."""

    def test_invalid_prompt_id_raises_error(self):
        """Test that invalid prompt ID raises ValueError."""
        with pytest.raises(ValueError):
            get_prompt_by_id("invalid_prompt_id_xyz")

    def test_error_message_includes_valid_ids(self):
        """Test error message lists valid prompt IDs."""
        try:
            get_prompt_by_id("invalid")
        except ValueError as e:
            error_msg = str(e)
            assert "baseline" in error_msg
            assert "korean_optimized" in error_msg


class TestPromptVariationCoverage:
    """Tests to ensure all required prompt variations are implemented."""

    def test_minimum_three_variations(self):
        """Test that at least 3 prompt variations exist (per T027c requirement)."""
        ids = list_prompt_ids()

        # T027c requires at least 3 prompt variations
        assert len(ids) >= 3

    def test_korean_specific_variation_exists(self):
        """Test that Korean-specific prompt variation exists."""
        ids = list_prompt_ids()

        # Should have a Korean-optimized prompt
        assert KOREAN_OPTIMIZED in ids

    def test_all_required_variations_implemented(self):
        """Test that all required prompt variations are implemented."""
        ids = list_prompt_ids()

        # Per specification, we need these variations:
        required_variations = [
            BASELINE,
            KOREAN_OPTIMIZED,
            EXPLICIT_FORMAT,
            FEW_SHOT,
            STRUCTURED_OUTPUT,
        ]

        for variation in required_variations:
            assert variation in ids, f"Required variation '{variation}' not found"
