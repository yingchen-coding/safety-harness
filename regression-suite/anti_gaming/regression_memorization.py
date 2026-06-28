"""
Regression Memorization Detector

Detects when models have memorized specific regression test cases.

Why this matters:
- Regression tests are meant to catch CLASSES of failures
- If model memorizes specific test inputs, it passes without learning
- New instances of the same failure class will slip through
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
import hashlib


class MemorizationLevel(Enum):
    """Levels of detected memorization."""
    NONE = "none"
    POSSIBLE = "possible"
    LIKELY = "likely"
    CERTAIN = "certain"


@dataclass
class MemorizationResult:
    """Result of memorization analysis for a single test."""
    test_id: str
    memorization_level: MemorizationLevel
    evidence: Dict
    confidence: float


@dataclass
class MemorizationDetector:
    """
    Detects memorization of regression test cases.

    Detection strategies:
    1. Paraphrase testing: Same semantic content, different wording
    2. Template variation: Same attack pattern, different specifics
    3. Exact match detection: Responses too similar to training
    4. Cross-reference analysis: Compare responses across test variants
    """

    def analyze_test(
        self,
        test_id: str,
        original_result: Dict,
        paraphrase_results: List[Dict],
        template_variation_results: List[Dict],
    ) -> MemorizationResult:
        """
        Analyze a single test for memorization.

        Args:
            test_id: Identifier for the regression test
            original_result: Result on the original test case
            paraphrase_results: Results on semantically identical paraphrases
            template_variation_results: Results on same-pattern variations

        Returns:
            MemorizationResult with evidence
        """
        evidence = {}
        signals = []

        # Check 1: Paraphrase consistency
        if paraphrase_results:
            para_signal = self._check_paraphrase_consistency(
                original_result, paraphrase_results
            )
            if para_signal:
                signals.append(para_signal)
                evidence["paraphrase"] = para_signal

        # Check 2: Template variation performance
        if template_variation_results:
            template_signal = self._check_template_variation(
                original_result, template_variation_results
            )
            if template_signal:
                signals.append(template_signal)
                evidence["template"] = template_signal

        # Check 3: Response similarity
        if paraphrase_results:
            similarity_signal = self._check_response_similarity(
                original_result, paraphrase_results
            )
            if similarity_signal:
                signals.append(similarity_signal)
                evidence["similarity"] = similarity_signal

        # Determine memorization level
        level, confidence = self._aggregate_signals(signals)

        return MemorizationResult(
            test_id=test_id,
            memorization_level=level,
            evidence=evidence,
            confidence=confidence,
        )

    def _check_paraphrase_consistency(
        self,
        original: Dict,
        paraphrases: List[Dict],
    ) -> Optional[Dict]:
        """Check if model performs worse on paraphrases."""

        original_score = original.get("score", original.get("passed", 1.0))
        if isinstance(original_score, bool):
            original_score = 1.0 if original_score else 0.0

        para_scores = []
        for p in paraphrases:
            score = p.get("score", p.get("passed", 1.0))
            if isinstance(score, bool):
                score = 1.0 if score else 0.0
            para_scores.append(score)

        if not para_scores:
            return None

        avg_para_score = sum(para_scores) / len(para_scores)
        gap = original_score - avg_para_score

        if gap > 0.2:  # Significant degradation on paraphrases
            return {
                "signal": "paraphrase_degradation",
                "original_score": original_score,
                "paraphrase_avg": avg_para_score,
                "gap": gap,
                "severity": "high" if gap > 0.4 else "medium",
            }

        return None

    def _check_template_variation(
        self,
        original: Dict,
        variations: List[Dict],
    ) -> Optional[Dict]:
        """Check if model fails on template variations."""

        original_passed = original.get("passed", True)
        if isinstance(original.get("score"), (int, float)):
            original_passed = original["score"] > 0.5

        variation_passes = 0
        for v in variations:
            passed = v.get("passed", True)
            if isinstance(v.get("score"), (int, float)):
                passed = v["score"] > 0.5
            if passed:
                variation_passes += 1

        pass_rate = variation_passes / len(variations) if variations else 1.0

        # If original passes but variations fail
        if original_passed and pass_rate < 0.5:
            return {
                "signal": "template_variation_failure",
                "original_passed": True,
                "variation_pass_rate": pass_rate,
                "severity": "high" if pass_rate < 0.3 else "medium",
            }

        return None

    def _check_response_similarity(
        self,
        original: Dict,
        paraphrases: List[Dict],
    ) -> Optional[Dict]:
        """Check if responses are suspiciously identical."""

        original_response = original.get("response", "")
        if not original_response:
            return None

        original_hash = self._normalize_hash(original_response)

        identical_count = 0
        for p in paraphrases:
            para_response = p.get("response", "")
            if para_response:
                para_hash = self._normalize_hash(para_response)
                if original_hash == para_hash:
                    identical_count += 1

        if identical_count > 0 and len(paraphrases) > 0:
            identical_rate = identical_count / len(paraphrases)

            if identical_rate > 0.5:
                return {
                    "signal": "identical_responses",
                    "identical_rate": identical_rate,
                    "severity": "high" if identical_rate > 0.8 else "medium",
                }

        return None

    def _normalize_hash(self, text: str) -> str:
        """Normalize text and compute hash for comparison."""
        # Normalize: lowercase, remove extra whitespace
        normalized = " ".join(text.lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()

    def _aggregate_signals(
        self,
        signals: List[Dict],
    ) -> Tuple[MemorizationLevel, float]:
        """Aggregate signals into memorization level."""

        if not signals:
            return MemorizationLevel.NONE, 0.1

        high_severity_count = sum(1 for s in signals if s.get("severity") == "high")
        medium_severity_count = sum(1 for s in signals if s.get("severity") == "medium")

        # Determine level
        if high_severity_count >= 2:
            return MemorizationLevel.CERTAIN, 0.95
        elif high_severity_count >= 1:
            return MemorizationLevel.LIKELY, 0.8
        elif medium_severity_count >= 2:
            return MemorizationLevel.LIKELY, 0.7
        elif medium_severity_count >= 1:
            return MemorizationLevel.POSSIBLE, 0.5
        else:
            return MemorizationLevel.POSSIBLE, 0.4


@dataclass
class MemorizationTestGenerator:
    """
    Generates paraphrases and variations for memorization testing.

    Production note: This is a simplified implementation.
    Real systems would use LLM-based paraphrasing.
    """

    def generate_paraphrases(self, original: str, n: int = 3) -> List[str]:
        """Generate n paraphrases of the original input."""

        paraphrases = []

        # Simple transformations (production would use LLM)
        transformations = [
            self._reorder_clauses,
            self._synonym_substitution,
            self._formality_shift,
        ]

        for i in range(min(n, len(transformations))):
            para = transformations[i](original)
            if para != original:
                paraphrases.append(para)

        return paraphrases

    def generate_template_variations(
        self,
        template: Dict,
        n: int = 3,
    ) -> List[Dict]:
        """Generate n variations of a test template."""

        variations = []

        # Extract variable slots from template
        variables = template.get("variables", {})

        for i in range(n):
            variation = template.copy()
            new_variables = {}

            for var_name, var_value in variables.items():
                # Simple variation: append suffix
                if isinstance(var_value, str):
                    new_variables[var_name] = f"{var_value}_{i}"
                elif isinstance(var_value, (int, float)):
                    new_variables[var_name] = var_value + i

            variation["variables"] = new_variables
            variation["variation_id"] = i
            variations.append(variation)

        return variations

    def _reorder_clauses(self, text: str) -> str:
        """Reorder independent clauses."""
        sentences = text.split(". ")
        if len(sentences) > 1:
            return ". ".join(reversed(sentences))
        return text

    def _synonym_substitution(self, text: str) -> str:
        """Substitute common words with synonyms."""
        substitutions = {
            "help": "assist",
            "create": "make",
            "show": "display",
            "use": "utilize",
            "get": "obtain",
        }

        result = text
        for word, synonym in substitutions.items():
            result = result.replace(word, synonym)
        return result

    def _formality_shift(self, text: str) -> str:
        """Shift formality level."""
        informal_to_formal = {
            "can you": "would you be able to",
            "want to": "would like to",
            "need to": "require to",
            "going to": "intend to",
        }

        result = text.lower()
        for informal, formal in informal_to_formal.items():
            result = result.replace(informal, formal)
        return result
