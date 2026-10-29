#!/usr/bin/env python3
"""The Agentic GRC Team: Compliance, Risk, and Audit agents, built to
the Agentic GRC Standard (https://agenticgrc.io/standard/), running a
GRC use case end to end.

Compliance reads the governing policy once, executes the use case
(today: User Access Review, via agentic-grc-access-review), and cites
the specific policy control behind every flag. Risk scores and
proposes a treatment for whatever Compliance flagged, citing the same
policy controls. Audit independently re-samples and re-classifies a
subset of *all* records, flagged and not, and reports any discrepancy
with Compliance's recorded verdict. Risk's and Audit's findings are
logged alongside Compliance's run, not left as terminal output only.

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
from team.runlog import log_audit_result, log_risk_score, new_team_run_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--use-case", choices=["user_access_review"], default="user_access_review"
    )
    parser.add_argument("--input", required=True, help="Path to the export file")
    parser.add_argument(
        "--policy",
        default=None,
        help="Path to a policy document; defaults to the bundled sample IAM policy",
    )
    parser.add_argument("--model", default="claude-sonnet-5")
    parser.add_argument(
        "--audit-sample-size",
        type=int,
        default=None,
        help=(
            "Audits the full population by default (see the Standard's "
            "'Audit coverage: exhaustive by default'). Pass a number here "
            "to deliberately reduce coverage for cost or latency at "
            "genuine scale, an explicit opt-in, not the default."
        ),
    )
    parser.add_argument(
        "--audit-seed",
        type=int,
        default=None,
        help="Fix the audit sample for a reproducible run (only relevant with --audit-sample-size)",
    )
    args = parser.parse_args()

    policy_path = Path(args.policy) if args.policy else None
    team_run_path = new_team_run_path()

    compliance = ComplianceAgent()
    results, compliance_run_path, policy = compliance.run_user_access_review(
        Path(args.input), policy_path=policy_path, model=args.model
    )
    flagged = [r for r in results if r[2].status == "FLAG"]
    print(f"=== Compliance agent ({compliance.registry_id}) ===")
    print(f"{len(flagged)}/{len(results)} flagged. Run logged to {compliance_run_path}\n")

    risk = RiskAgent()
    print(f"=== Risk agent ({risk.registry_id}): scoring flagged findings ===")
    for record, classification, verdict in flagged:
        score = risk.score(record, classification, verdict, policy, model=args.model)
        log_risk_score(team_run_path, record, score, args.model, compliance_run_path)
        print(
            f"{record.display_name}: likelihood={score.likelihood} "
            f"impact={score.impact} proposed={score.proposed_treatment.value} "
            f"(pending human risk-owner sign-off)"
        )
        print(f"  {score.rationale}")
    print()

    audit = AuditAgent()
    if args.audit_sample_size is None:
        coverage = f"independently re-classifying the full population ({len(results)} records)"
    else:
        coverage = (
            f"independently re-classifying a REDUCED sample of "
            f"{min(args.audit_sample_size, len(results))}/{len(results)} records "
            f"(coverage reduced via --audit-sample-size, not the default)"
        )
    print(f"=== Audit agent ({audit.registry_id}): {coverage} ===")
    audit_rows = audit.sample(
        results,
        policy,
        sample_size=args.audit_sample_size,
        model=args.model,
        seed=args.audit_seed,
    )
    for record, audit_result in audit_rows:
        log_audit_result(team_run_path, record, audit_result, args.model, compliance_run_path)
        flag = "OK" if audit_result.agrees_with_compliance else "DISCREPANCY"
        print(f"{record.display_name}: [{flag}] {audit_result.discrepancy_note}")

    print(f"\nRisk and Audit findings logged to {team_run_path}")


if __name__ == "__main__":
    main()
