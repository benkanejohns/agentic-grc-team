"""Compliance agent: the Standard's 'Compliance operates' function.

Runs control-testing use cases and surfaces flagged findings. This is
the only module in the team that touches agentic-grc-access-review;
Risk and Audit only ever see this agent's output, never its internals.
It never decides whether a finding is accepted (that's Risk proposing
and a human owner deciding), and it never audits its own work (that's
the Audit agent, in a separate module this one is never imported by
and never imports).
"""
from pathlib import Path

from access_review.classify import classify
from access_review.connectors.aws import AWSIAMConnector
from access_review.rules import evaluate
from access_review.runlog import append, new_run_path


class ComplianceAgent:
    registry_id = "compliance-agent-v1"

    def run_user_access_review(self, input_path: Path, model: str = "claude-sonnet-5"):
        """Runs the agentic-grc-access-review pipeline end to end: parse,
        classify, decide, log. Returns the full result set and the run
        log path."""
        connector = AWSIAMConnector()
        records = connector.load(input_path)

        run_path = new_run_path()
        results = []
        for record in records:
            classification = classify(record, model=model)
            verdict = evaluate(record, classification)
            append(run_path, record, classification, verdict, model)
            results.append((record, classification, verdict))
        return results, run_path
