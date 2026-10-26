from enum import Enum

from pydantic import BaseModel


class Treatment(str, Enum):
    MITIGATE = "mitigate"
    TRANSFER = "transfer"
    AVOID = "avoid"
    ACCEPT = "accept"


class RiskScore(BaseModel):
    """`proposed_treatment` is always a recommendation. A Treatment of
    `accept` here is a proposal for a named human risk owner to sign off
    on, never a decision this agent has made on anyone's behalf (Standard
    Principle 4)."""

    likelihood: int
    impact: int
    proposed_treatment: Treatment
    rationale: str


class AuditSampleResult(BaseModel):
    agrees_with_compliance: bool
    independent_privilege_level: str
    independent_department_fit: str
    discrepancy_note: str
