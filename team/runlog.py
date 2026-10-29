"""Team-level run logging for Risk and Audit.

Compliance's own run is already logged by agentic-grc-access-review's
runlog.py (a separate file, since that package owns its own logging
independently of this team repo). This covers the gap Standard
Principle 1 flagged on review: Risk's scores and Audit's independent
findings previously existed only in terminal output, with nothing to
replay or cite six months later.

Each entry references the Compliance run log it corresponds to, so the
two files can be cross-referenced even though they're separate.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from access_review.models import AccessRecord

from .models import AuditSampleResult, RiskScore

TEAM_RUNS_DIR = Path("runs")


def new_team_run_path() -> Path:
    TEAM_RUNS_DIR.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return TEAM_RUNS_DIR / f"team-{ts}.jsonl"


def _append(path: Path, entry: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def log_risk_score(
    path: Path,
    record: AccessRecord,
    score: RiskScore,
    model: str,
    compliance_run_log: Path,
) -> None:
    _append(
        path,
        {
            "logged_at": datetime.now(timezone.utc).isoformat(),
            "agent": "risk-agent-v1",
            "model": model,
            "compliance_run_log": str(compliance_run_log),
            "user_id": record.user_id,
            "score": score.model_dump(mode="json"),
        },
    )


def log_audit_result(
    path: Path,
    record: AccessRecord,
    audit_result: AuditSampleResult,
    model: str,
    compliance_run_log: Path,
) -> None:
    _append(
        path,
        {
            "logged_at": datetime.now(timezone.utc).isoformat(),
            "agent": "audit-agent-v1",
            "model": model,
            "compliance_run_log": str(compliance_run_log),
            "user_id": record.user_id,
            "result": audit_result.model_dump(mode="json"),
        },
    )
