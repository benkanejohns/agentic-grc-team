# The Agentic GRC Team

Three agents, Compliance, Risk, and Audit, built to [the Agentic GRC Standard](https://agenticgrc.io/standard/), running a real GRC use case together. Not a single tool, a team: each agent has its own registry entry, its own autonomy level, and its own line of defence, and the independence between them is enforced in code, not asserted in a README.

## The team

| Agent | Standard function | Does | Never does |
|---|---|---|---|
| **Compliance** | operates | Executes control-testing use cases (today: [User Access Review](https://github.com/benkanejohns/agentic-grc-access-review)) | Decide a finding is accepted |
| **Risk** | prioritises | Scores likelihood/impact of what Compliance flagged, proposes a treatment | Finalise a risk acceptance, a human risk owner signs off |
| **Audit** | verifies | Independently re-samples and re-classifies a subset of *all* records, flagged and not, reports any discrepancy | Import or call anything Compliance's module defines |

Registry entries, with owner, purpose, autonomy level, and scope, live in [`registry/agents.yaml`](./registry/agents.yaml).

## Deliberately not a fourth, Governance agent

Governance in this project is the registry plus the shared Standard every agent's prompt is built on, not a worker. Raising an agent's autonomy level, or accepting a risk, is a human decision the Standard does not let any agent make for itself. Building a "Governance agent" that made those calls would violate the thing this whole project exists to get right.

## How "built to the Standard" is actually implemented, not just claimed

Every agent's system prompt is Part 1 of the Standard, vendored at [`standard/agentic-grc-standard.md`](./standard/agentic-grc-standard.md), verbatim, with a short role-specific instruction appended (see `team/standard_loader.py`). One shared file, three thin role wrappers.

The independence the Standard requires between Compliance and Audit is structural: `audit_agent.py` never imports `compliance_agent.py`, and redefines its own classification tool schema rather than reusing `access_review.classify`'s. Audit reproduces Compliance's work independently; it does not check Compliance's math with Compliance's calculator.

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
| `--model` | `claude-sonnet-5` | Model every agent calls |
| `--audit-sample-size` | `5` | How many records Audit independently re-classifies |
| `--audit-seed` | none | Fix it for a reproducible sample across runs |

**What it costs to run once:** against the 16-row sample file, Compliance makes 16 model calls (one per record), Risk makes one per flagged finding (up to 8 more), and Audit makes 5 more by default, around 30 calls total. All short, tool-use-only calls (a few hundred tokens each), not expensive, but worth knowing before pointing `--input` at a much larger real export.

Output: Compliance's flagged findings and run log (in `runs/`), Risk's likelihood/impact score and proposed treatment for each one, and Audit's independent re-classification of a random sample, flagged and not, with any discrepancy from Compliance's recorded verdict called out by name.

## Honest limitations

- The registry (`registry/agents.yaml`) is documentation today, not an enforced runtime gate. Nothing in the code currently refuses to run an agent missing from it. That's the natural next step before this touches a live cloud account.
- Audit's independence is enforced by not sharing code, not by a hard process/sandbox boundary. In this demo both agents still run in the same Python process. A production deployment should run them as genuinely separate services with separate credentials.
- Risk's likelihood/impact scoring is a first pass; it isn't calibrated against any real incident history, treat the numbers as a starting point for a human risk owner's judgement, not a finished model.

## License

MIT. See [LICENSE](./LICENSE).

---

Part of [Agentic GRC](https://agenticgrc.io). See [the manifesto](https://agenticgrc.io/) and [the Standard](https://agenticgrc.io/standard/) this team is built to.
