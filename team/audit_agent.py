"""Audit agent: the Standard's 'Audit verifies' function, and the
separation-of-duties rule the Standard is strictest about: 'an agent
never audits controls it operates.'

This module must never import compliance_agent.py or call its classify
function. It redefines its own tool schema and makes its own Claude
calls, independently re-classifying a sample of records Compliance
already reviewed, without seeing Compliance's answer first, then
compares. That is what makes the independence real rather than
asserted: a shared helper here would mean Audit is checking
Compliance's math with Compliance's calculator.

The deterministic rules function (`access_review.rules.evaluate`) is
the one thing both agents legitimately share, it's the shared policy
both are being tested against, not either agent's working.
"""
import random
from typing import Optional

from anthropic import Anthropic

from access_review.models import AccessRecord, Classification
from access_review.rules import evaluate

from .models import AuditSampleResult
from .standard_loader import build_system_prompt

ROLE_INSTRUCTION = (
    "You are the Audit agent on a GRC agent team operating under the "
    "Agentic GRC Standard above. You independently re-classify access "
    "records the Compliance agent already reviewed, without seeing its "
    "answer first, and report whether your independent result agrees. "
    "You do not operate controls and you do not trust the Compliance "
    "agent's working, you reproduce it."
)

_CLASSIFY_TOOL = {
    "name": "classify_access",
    "description": (
        "Classify an access grant's privilege level and whether the "
        "role fits the user's department. Return only values from the "
        "fixed enums; never invent a new category."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "privilege_level": {
                "type": "string",
                "enum": ["read-only", "service-scoped-write", "full-admin", "unknown"],
            },
            "department_fit": {
                "type": "string",
                "enum": ["appropriate", "mismatch", "insufficient-info"],
            },
            "rationale": {"type": "string"},
        },
        "required": ["privilege_level", "department_fit", "rationale"],
    },
}


class AuditAgent:
    registry_id = "audit-agent-v1"

    def __init__(self):
        self._client = Anthropic()

    def sample(
        self,
        results: list,
        sample_size: int = 5,
        model: str = "claude-sonnet-5",
        seed: Optional[int] = None,
    ):
        """Samples from *all* of Compliance's results, flagged and
        not-flagged alike, sampling only the flagged rows would miss
        false negatives, exactly the gap Compliance's own findings
        can't see by definition."""
        rng = random.Random(seed)
        sampled = rng.sample(results, k=min(sample_size, len(results)))

        audit_rows = []
        for record, compliance_classification, compliance_verdict in sampled:
            independent = self._classify_independently(record, model)
            independent_verdict = evaluate(record, independent)
            agrees = (
                independent.privilege_level == compliance_classification.privilege_level
                and independent.department_fit == compliance_classification.department_fit
                and independent_verdict.status == compliance_verdict.status
            )
            note = (
                "Matches Compliance's finding."
                if agrees
                else (
                    f"DISCREPANCY: Compliance recorded "
                    f"{compliance_classification.privilege_level.value}/"
                    f"{compliance_classification.department_fit.value} -> "
                    f"{compliance_verdict.status}; independent audit found "
                    f"{independent.privilege_level.value}/"
                    f"{independent.department_fit.value} -> "
                    f"{independent_verdict.status}."
                )
            )
            audit_rows.append(
                (
                    record,
                    AuditSampleResult(
                        agrees_with_compliance=agrees,
                        independent_privilege_level=independent.privilege_level.value,
                        independent_department_fit=independent.department_fit.value,
                        discrepancy_note=note,
                    ),
                )
            )
        return audit_rows

    def _classify_independently(self, record: AccessRecord, model: str) -> Classification:
        response = self._client.messages.create(
            model=model,
            max_tokens=300,
            system=build_system_prompt(ROLE_INSTRUCTION),
            tools=[_CLASSIFY_TOOL],
            tool_choice={"type": "tool", "name": "classify_access"},
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Role or policy: {record.role_or_policy}\n"
                        f"Department: {record.department or 'unknown'}\n"
                        "Classify this access grant."
                    ),
                }
            ],
        )
        tool_use = next(block for block in response.content if block.type == "tool_use")
        return Classification(**tool_use.input)
