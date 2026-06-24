import json
import re

from app.llm.base import LLMClient
from app.schemas.log_analysis import LogAnalysis, LogInput


SYSTEM_PROMPT = """
You are a senior backend engineer and incident analyst.
Analyze application logs and stacktraces.
Return only valid JSON. Do not wrap the response in Markdown.
Do not invent facts that are not supported by the log input.
If uncertain, lower the confidence score.
""".strip()


def _extract_json_object(text: str) -> str:
    """Extract the first JSON object from an LLM response."""
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return text

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("LLM response did not contain a JSON object")
    return match.group(0)


class LogAnalysisService:
    """Creates structured incident analyses from raw logs."""

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    def analyze(self, log_input: LogInput) -> LogAnalysis:
        user_prompt = self._build_user_prompt(log_input)
        raw_response = self.llm_client.complete(SYSTEM_PROMPT, user_prompt)
        json_text = _extract_json_object(raw_response)
        payload = json.loads(json_text)
        return LogAnalysis.model_validate(payload)

    @staticmethod
    def _build_user_prompt(log_input: LogInput) -> str:
        return f"""
Analyze the following log or stacktrace and return JSON matching this schema:

{{
  "incident_type": "application_error | database_error | network_error | configuration_error | performance_issue | security_related | unknown",
  "severity": "low | medium | high | critical",
  "affected_component": "string",
  "short_summary": "string",
  "probable_root_cause": "string",
  "important_log_lines": ["string"],
  "recommended_debug_steps": ["string"],
  "possible_fix_direction": "string",
  "test_cases": ["string"],
  "confidence": 0.0
}}

Rules:
- Keep the analysis technical and concise.
- Extract important log lines exactly or nearly exactly when possible.
- Severity must consider production impact, payment/auth/security impact and repeated failures.
- Test cases should be concrete and useful for a developer.
- Return JSON only.

Title: {log_input.title}
Language: {log_input.language}
Source: {log_input.source}

Raw log:
{log_input.raw_log}
""".strip()
