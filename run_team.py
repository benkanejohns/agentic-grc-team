#!/usr/bin/env python3
"""The Agentic GRC Team: Compliance, Risk, and Audit agents, built to
the Agentic GRC Standard (https://agenticgrc.io/standard/), running a
GRC use case end to end.

Compliance executes the use case (today: User Access Review, via
agentic-grc-access-review). Risk scores and proposes a treatment for
whatever Compliance flagged. Audit independently re-samples and
re-classifies a subset of *all* records, flagged and not, and reports
any discrepancy with Compliance's recorded verdict.

Deliberately absent: a Governance agent. Governance here is this
registry (registry/agents.yaml) and the shared Standard every agent's
system prompt is built on, not a fourth worker. Raising an agent's
autonomy level or approving a risk acceptance is a human decision the
Standard does not permit any agent to make for itself.
"""
import argparse
from pathlib import Path

from team.audit_agent import AuditAgent
from team.compliance_agent import ComplianceAgent
from team.risk_agent import RiskAgent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--use-case", choices=["user_access_review"], default="user_access_review"
    )
    parser.add_argument("--input", required=True, help="Path to the export file")
    parser.add_argument("--model", default="claude-sonnet-5")
    parser.add_argument("--audit-sample-size", type=int, default=5)
    parser.add_argument(
        "--audit-seed",
        type=int,
        default=None,
        help="Fix the audit sample for a reproducible run",
    )
    args = parser.parse_args()

    compliance = ComplianceAgent()
    results, run_path = compliance.run_user_access_review(
        Path(args.input), model=args.model
    )
    flagged = [r for r in results if r[2].status == "FLAG"]
    print(f"=== Compliance agent ({compliance.registry_id}) ===")
    print(f"{len(flagged)}/{len(results)} flagged. Run logged to {run_path}\n")

    risk = RiskAgent()
    print(f"=== Risk agent ({risk.registry_id}): scoring flagged findings ===")
    for record, classification, verdict in flagged:
        score = risk.score(record, classification, verdict, model=args.model)
        print(
            f"{record.display_name}: likelihood={score.likelihood} "
            f"impact={score.impact} proposed={score.proposed_treatment.value} "
            f"(pending human risk-owner sign-off)"
        )
        print(f"  {score.rationale}")
    print()

    audit = AuditAgent()
    print(
        f"=== Audit agent ({audit.registry_id}): independently re-sampling "
        f"{args.audit_sample_size} records ==="
    )
    audit_rows = audit.sample(
        results,
        sample_size=args.audit_sample_size,
        model=args.model,
        seed=args.audit_seed,
    )
    for record, audit_result in audit_rows:
        flag = "OK" if audit_result.agrees_with_compliance else "DISCREPANCY"
        print(f"{record.display_name}: [{flag}] {audit_result.discrepancy_note}")


if __name__ == "__main__":
    main()
