import pytest
from pydantic import ValidationError

from app.llm.base import LLMClient
from app.schemas.log_analysis import LogInput
from app.services.log_analysis_service import LogAnalysisService


class FakeLLMClient(LLMClient):
    def __init__(self, response: str) -> None:
        self.response = response

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        return self.response


def sample_input() -> LogInput:
    return LogInput(
        title="Checkout payment failure",
        language="java",
        source="production",
        raw_log="ERROR PaymentService NullPointerException at PaymentService.java:87",
    )


def test_analyze_valid_json() -> None:
    response = """
    {
      "incident_type": "application_error",
      "severity": "high",
      "affected_component": "checkout / payment service",
      "short_summary": "Payment capture fails with a NullPointerException.",
      "probable_root_cause": "A null coupon object is used during discount calculation.",
      "important_log_lines": ["NullPointerException at PaymentService.java:87"],
      "recommended_debug_steps": ["Inspect PaymentService.applyDiscount", "Add null handling"],
      "possible_fix_direction": "Validate the coupon object before reading discount data.",
      "test_cases": ["checkout without coupon", "checkout with invalid coupon"],
      "confidence": 0.86
    }
    """
    service = LogAnalysisService(FakeLLMClient(response))

    analysis = service.analyze(sample_input())

    assert analysis.incident_type == "application_error"
    assert analysis.severity == "high"
    assert analysis.confidence == pytest.approx(0.86)


def test_analyze_json_wrapped_in_text() -> None:
    response = """
    Here is the result:
    {
      "incident_type": "database_error",
      "severity": "medium",
      "affected_component": "database",
      "short_summary": "Database timeout during query execution.",
      "probable_root_cause": "Slow query or overloaded database connection pool.",
      "important_log_lines": ["SQLTimeoutException"],
      "recommended_debug_steps": ["Check query plan"],
      "possible_fix_direction": "Optimize query and review pool settings.",
      "test_cases": ["load test query endpoint"],
      "confidence": 0.72
    }
    """
    service = LogAnalysisService(FakeLLMClient(response))

    analysis = service.analyze(sample_input())

    assert analysis.incident_type == "database_error"
    assert analysis.severity == "medium"


def test_invalid_schema_raises_validation_error() -> None:
    response = """
    {
      "incident_type": "invalid_type",
      "severity": "extreme",
      "affected_component": "checkout",
      "short_summary": "x",
      "probable_root_cause": "x",
      "important_log_lines": [],
      "recommended_debug_steps": [],
      "possible_fix_direction": "x",
      "test_cases": [],
      "confidence": 1.5
    }
    """
    service = LogAnalysisService(FakeLLMClient(response))

    with pytest.raises(ValidationError):
        service.analyze(sample_input())
