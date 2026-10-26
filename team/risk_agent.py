"""Risk agent: the Standard's 'Risk prioritises' function.

Takes findings the Compliance agent already flagged and scores
likelihood and impact, proposing a treatment. It never finalises
acceptance, a proposed 'accept' is always a recommendation for a named
human risk owner to sign off on separately.
"""
from anthropic import Anthropic

from access_review.models import AccessRecord, Classification, ReviewVerdict

from .models import RiskScore
from .standard_loader import build_system_prompt

ROLE_INSTRUCTION = (
    "You are the Risk agent on a GRC agent team operating under the "
    "Agentic GRC Standard above. You receive findings the Compliance "
    "agent has already flagged. Score likelihood and impact on a 1-5 "
    "scale and propose a treatment. You do not decide whether a risk is "
    "accepted, you propose a treatment; a named human risk owner signs "
    "off on acceptance separately."
)

_SCORE_TOOL = {
    "name": "score_risk",
    "description": (
        "Score the likelihood and impact of a flagged access-review "
        "finding and propose a treatment. A proposed 'accept' is a "
        "recommendation, never a decision already made."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "likelihood": {"type": "integer", "minimum": 1, "maximum": 5},
            "impact": {"type": "integer", "minimum": 1, "maximum": 5},
            "proposed_treatment": {
                "type": "string",
                "enum": ["mitigate", "transfer", "avoid", "accept"],
            },
            "rationale": {"type": "string"},
        },
        "required": ["likelihood", "impact", "proposed_treatment", "rationale"],
    },
}


class RiskAgent:
    registry_id = "risk-agent-v1"

    def __init__(self):
        self._client = Anthropic()

    def score(
        self,
        record: AccessRecord,
        classification: Classification,
        verdict: ReviewVerdict,
        model: str = "claude-sonnet-5",
    ) -> RiskScore:
        response = self._client.messages.create(
            model=model,
            max_tokens=300,
            system=build_system_prompt(ROLE_INSTRUCTION),
            tools=[_SCORE_TOOL],
            tool_choice={"type": "tool", "name": "score_risk"},
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"User: {record.display_name}\n"
                        f"Role/policy: {record.role_or_policy}\n"
                        f"Privilege level: {classification.privilege_level.value}\n"
                        f"Department fit: {classification.department_fit.value}\n"
                        f"Flag reasons: {'; '.join(verdict.reasons)}\n"
                        "Score this finding."
                    ),
                }
            ],
        )
        tool_use = next(block for block in response.content if block.type == "tool_use")
        return RiskScore(**tool_use.input)
