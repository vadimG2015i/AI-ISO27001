"""End-to-end integration test verifying component contracts and data flow."""

from iso_assistant.ai.client import AIClient
from iso_assistant.ai.schemas import AIGapAssessmentOutput
from iso_assistant.config import settings
from iso_assistant.security.file_validator import FileValidator


def test_offline_mock_pipeline_flow():
    """Verify that file validation, mock AI client, and schema validation function in offline mode."""
    # 1. Configuration check
    assert settings.app_name is not None
    assert settings.llm_provider == "mock"

    # 2. File security validation
    mock_pdf = b"%PDF-1.4\nSynthetic security policy content\n%%EOF"
    val_result = FileValidator.validate_file("Information_Security_Policy.pdf", mock_pdf)
    assert val_result.is_valid

    # 3. Mock AI assessment generation
    client = AIClient()
    result = client.generate_structured(
        prompt="Analyze policy against access control requirements.",
        system_instruction="You are an ISO 27001 Lead Auditor.",
        response_model=AIGapAssessmentOutput,
    )

    assert isinstance(result, AIGapAssessmentOutput)
    assert result.compliance_status in ["Compliant", "Partially Compliant", "Non-Compliant", "Not Applicable"]
    assert 0.0 <= result.compliance_score <= 1.0

