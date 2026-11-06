"""Unit tests for ISO 27005 risk matrix calculation and severity classification."""

from iso_assistant.constants import RiskLevel
from iso_assistant.services.risk_service import RiskService


def test_risk_calculation_score_and_levels():
    """Verify 5x5 likelihood x impact scoring formula and qualitative bands."""
    # Score 1x1 = 1 (Very Low)
    score, level = RiskService.calculate_score_and_level(1, 1)
    assert score == 1
    assert level == RiskLevel.VERY_LOW.value

    # Score 3x3 = 9 (Medium)
    score, level = RiskService.calculate_score_and_level(3, 3)
    assert score == 9
    assert level == RiskLevel.MEDIUM.value

    # Score 4x4 = 16 (High)
    score, level = RiskService.calculate_score_and_level(4, 4)
    assert score == 16
    assert level == RiskLevel.HIGH.value

    # Score 5x5 = 25 (Critical)
    score, level = RiskService.calculate_score_and_level(5, 5)
    assert score == 25
    assert level == RiskLevel.CRITICAL.value

