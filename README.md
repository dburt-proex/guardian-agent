# guardian-agent

![python](https://img.shields.io/badge/python-3.10%2B-blue) ![deps](https://img.shields.io/badge/dependencies-0-brightgreen) ![tests](https://img.shields.io/badge/tests-23%20passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-lightgrey)

**Deterministic AI governance runtime.** Guardian sits between any AI reasoning layer and real-world execution. It does not reason or generate — it governs. Every proposed action passes through a two-gate deterministic pipeline and lands in a tamper-evident audit ledger before anything runs.

Built from the governed-agentic-execution ecosystem: **VIL** (signal scoring) + **CASA** policy enforced by **Diffwall** rules + hash-chained audit — one `govern()` call.

## Problem

Agentic AI fails in production for one reason more than any other: actions execute without governance. Gartner projects 40%+ of agentic AI projects will be canceled by end-2027 due to inadequate risk controls. Probabilistic models cannot be their own safety layer.

## System

```
envelope { signal, action }
    │
    ▼
[1] VIL signal gate      evidence-capped scoring: vil = min(claim, verifiability)
    │                    weak/rumor signals never reach the policy layer
    ▼
[2] CASA policy gate     six deterministic rules (Diffwall engine)
    │                    most-restrictive merge · unknown → REVIEW, never ALLOW
    ▼
[3] Audit ledger         sha256 hash-chained JSONL — record precedes execution
    │
    ▼
[4] Gated executor       ALLOW runs · REVIEW pends for a human · HALT never runs
```

## Decision Logic

| Rule | Trigger | Gate |
|------|---------|------|
| R1 | Irreversible destruction (`rm -rf`, `drop table`, wipe) | HALT |
| R2 | Financial transfer (wire, payment, crypto) | HALT |
| R3 | Exposed secret (API keys, private keys, tokens) | HALT |
| R4 | Public broadcast (email blast, social post) | REVIEW* |
| R5 | Data mutation (db/file write, deploy, config) | REVIEW |
| R6 | Read-only operation | ALLOW |
| — | Unknown action type | REVIEW (fail-safe) |

Cross-stage merge is most-restrictive: VIL can only tighten a CASA verdict, never loosen it. \*R4 tier is a config constant (`guardian/rules.py: R4_TIER`); strict deployments set HALT.

## Output

```bash
pip install .                       # or run straight from the repo, zero deps
python demo.py                      # 4-action governed run + tamper detection
python -m unittest discover -s tests -v
guardian check examples/halt_wire_transfer.json   # exit 2
guardian check examples/allow_read_kpi.json       # exit 0
guardian verify                                    # audit chain integrity
```

Exit codes are CI-composable: `0` ALLOW · `1` REVIEW · `2` HALT/error.

## Proof

From `python demo.py` — same verified signal, three different actions, plus one high-claim/low-evidence signal:

```
[ALLOW]   Read KPI file (verified signal)      → executed
[REVIEW]  Email blast to customer list         → pends for human
[HALT]    Wire $12,000 to 'vendor'             → blocked, never called
[HALT]    Read file, but based on a rumor      → blocked at VIL (policy said ALLOW)

Ledger integrity: True (chain intact) — 5 entries
After tampering with entry 4: intact=False (tamper detected at entry 4)
```

Case 4 is the point: the policy layer approved a harmless read, and the signal gate still blocked it because the claim outran its evidence. Two independent deterministic gates; the strictest one wins.

## Library use

```python
from guardian import GuardianAgent

agent = GuardianAgent("audit.jsonl")
decision = agent.govern_and_execute(envelope, executor=my_tool_runner)
# decision.verdict ∈ {ALLOW, REVIEW, HALT}; decision.entry_hash seals the record
```

## Relevance

This is the reference runtime for the governed-agentic-execution stack: [Diffwall](https://github.com/dburt-proex/diffwall) (rule enforcement) · CASA (policy architecture) · [VIL](https://github.com/dburt-proex/VIL_deterministic_scoring_engine) (deterministic scoring) · [PromptBP](https://github.com/dburt-proex/PromptBP) (instruction contracts, the envelope's upstream discipline).

## Limitations

- Rules are pattern/type-based, not semantic — a determined adversary can phrase around regexes; Guardian is a floor, not a ceiling.
- The ledger is tamper-*evident*, not tamper-*proof* — pair with append-only storage or external anchoring for hostile environments.
- VIL default weights/thresholds are transparent starting points, not tuned to any one domain.
- REVIEW tier requires an actual human loop; Guardian queues, it does not adjudicate.

MIT © Drew D. Burt
