# The Agentic GRC Team

Three agents, Compliance, Risk, and Audit, built to [the Agentic GRC Standard](https://agenticgrc.io/standard/), running a real GRC use case together. Not a single tool, a team: each agent has its own registry entry, its own autonomy level, and its own line of defence, and the independence between them is enforced in code, not asserted in a README.

## The team

| Agent | Standard function | Does | Never does |
|---|---|---|---|
| **Compliance** | operates | Reads the governing policy once per run, executes control-testing use cases (today: [User Access Review](https://github.com/benkanejohns/agentic-grc-access-review)), cites the specific policy control behind every flag | Decide a finding is accepted |
| **Risk** | prioritises | Scores likelihood/impact of what Compliance flagged, citing the same policy controls, proposes a treatment | Finalise a risk acceptance, a human risk owner signs off |
| **Audit** | verifies | Independently re-classifies the full population by default (flagged and not), reports any discrepancy | Import or call anything Compliance's module defines; sample instead of auditing everything, without being told to |

Registry entries, with owner, purpose, autonomy level, and scope, live in [`registry/agents.yaml`](./registry/agents.yaml).

## Deliberately not a fourth, Governance agent

Governance in this project is the registry plus the shared Standard every agent's prompt is built on, not a worker. Raising an agent's autonomy level, or accepting a risk, is a human decision the Standard does not let any agent make for itself. Building a "Governance agent" that made those calls would violate the thing this whole project exists to get right.

## How "built to the Standard" is actually implemented, not just claimed

Every agent's system prompt is Part 1 of the Standard, vendored at [`standard/agentic-grc-standard.md`](./standard/agentic-grc-standard.md), verbatim, with a short role-specific instruction appended (see `team/standard_loader.py`). One shared file, three thin role wrappers.

The independence the Standard requires between Compliance and Audit is structural: `audit_agent.py` never imports `compliance_agent.py`, and redefines its own classification tool schema rather than reusing `access_review.classify`'s. Audit reproduces Compliance's work independently; it does not check Compliance's math with Compliance's calculator.

## Every flag cites the actual policy, not a hardcoded number

`ComplianceAgent` reads the governing IAM policy once per run (not per record, that would risk the same run-to-run inconsistency already seen in department-fit classification) and extracts its controls via `access_review.policy.parse_policy`. `rules.py` cites the specific control ID behind every flag, `"No activity in 990 days (IAM-POL-4.2: threshold 90 days)"`, not an unsourced `"(threshold: 90)"`. Risk receives the same parsed controls and is instructed to cite them in its own rationale rather than reasoning from generic security judgement alone. If the policy doesn't define a control this logic looks for, the run prints a warning naming the gap instead of silently applying no check or a guessed default.

Point `--policy` at your own organisation's actual IAM policy to get findings that cite your real control IDs. The bundled `access_review/default_policy.md` is a sample.

## Running it

```bash
git clone https://github.com/benkanejohns/agentic-grc-team.git
cd agentic-grc-team

python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt
export ANTHROPIC_API_KEY=your-key-here   # Windows: set ANTHROPIC_API_KEY=your-key-here

curl -O https://raw.githubusercontent.com/benkanejohns/agentic-grc-access-review/main/sample_data/aws_iam_sample.csv

python run_team.py --input aws_iam_sample.csv
```

Or point `--input` at your own AWS IAM credential-report-shaped export instead of the sample file.

**Flags:**

| Flag | Default | What it does |
|---|---|---|
| `--input` | required | Path to the access export file |
| `--use-case` | `user_access_review` | Only one exists today |
| `--policy` | bundled sample policy | Path to the governing policy document; point this at your own organisation's actual IAM policy |
| `--model` | `claude-sonnet-5` | Model every agent calls |
| `--audit-sample-size` | full population | Deliberately reduce how many records Audit independently re-classifies, an opt-in reduction for cost or latency at genuine scale, not the default. See the Standard's "Audit coverage: exhaustive by default." |
| `--audit-seed` | none | Only relevant alongside `--audit-sample-size`: fix the reduced sample for a reproducible run |

**What it costs to run once:** against the 16-row sample file, policy parsing is one call (once per run, not per record), Compliance makes 16 model calls (one per record), Risk makes one per flagged finding (up to 8 more), and Audit, auditing the full population by default, makes another 16, around 41 calls total. All short, tool-use-only calls (a few hundred tokens each), not expensive at this size, but worth knowing before pointing `--input` at a much larger real export, exhaustive audit scales with population size, see the Standard's guidance on right-sizing the model for this rather than reducing coverage.

Output: Compliance's flagged findings and run log (in `runs/<timestamp>.jsonl`, with every reason citing a policy control ID), Risk's likelihood/impact score and policy-citing proposed treatment for each flagged finding, and Audit's independent re-classification of the full population by default (flagged and not), with any discrepancy from Compliance's recorded verdict called out by name. Risk's and Audit's findings are logged too, to `runs/team-<timestamp>.jsonl`, cross-referencing the Compliance run they correspond to.

## Honest limitations

- The registry (`registry/agents.yaml`) is documentation today, not an enforced runtime gate. Nothing in the code currently refuses to run an agent missing from it. That's the natural next step before this touches a live cloud account.
- Audit's independence is enforced by not sharing code, not by a hard process/sandbox boundary. In this demo both agents still run in the same Python process. A production deployment should run them as genuinely separate services with separate credentials.
- Risk's likelihood/impact scoring is a first pass; it isn't calibrated against any real incident history, treat the numbers as a starting point for a human risk owner's judgement, not a finished model.
- The bundled policy (`access_review/default_policy.md`) is a sample, four clauses, written for this demo. It's parsed with the same rigour a real policy would be, but it isn't one. Point `--policy` at your own organisation's actual IAM policy before trusting the citations this produces.

## License

MIT. See [LICENSE](./LICENSE).

---

Part of [Agentic GRC](https://agenticgrc.io). See [the manifesto](https://agenticgrc.io/) and [the Standard](https://agenticgrc.io/standard/) this team is built to.
