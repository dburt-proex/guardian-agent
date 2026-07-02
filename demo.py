"""Guardian Agent demo — a rogue upstream agent meets the governance runtime.

Four proposed actions, one pipeline, zero trust:
  1. read-only KPI fetch on a verified signal      -> ALLOW  (executes)
  2. customer email blast                          -> REVIEW (pends)
  3. $12,000 wire transfer                         -> HALT   (blocked)
  4. read-only fetch on an unverified rumor        -> HALT   (blocked at VIL)
Then the audit chain is verified, and a tamper attempt is detected.

Run:  python demo.py
"""
import json
import os

from guardian import GuardianAgent, Verdict

LEDGER = "demo_audit.jsonl"
if os.path.exists(LEDGER):
    os.remove(LEDGER)

agent = GuardianAgent(LEDGER)

VERIFIED = {
    "content": "Ops ticket approved by DB: pull weekly KPI report for client "
               "dashboard refresh per standing runbook step 3.",
    "source": "ops_queue",
    "source_pointers": ["TICKET-88", "RUNBOOK-3", "APPROVAL-DB"],
    "metadata": {"ticket": "88", "requester": "db", "runbook": "3",
                 "client": "acme", "step": "read"},
    "signal_score": 9.0,
}

ENVELOPES = [
    ("Read KPI file (verified signal)",
     {"signal": VERIFIED,
      "action": {"id": "act-1", "type": "read_file", "target": "kpi_week26.csv"}}),
    ("Email blast to customer list",
     {"signal": VERIFIED,
      "action": {"id": "act-2", "type": "send_email",
                 "target": "customers@alllist", "payload": "July promo"}}),
    ("Wire $12,000 to 'vendor'",
     {"signal": VERIFIED,
      "action": {"id": "act-3", "type": "wire_transfer",
                 "payload": "transfer $12,000 usd to acct 4471"}}),
    ("Read file, but based on a rumor",
     {"signal": {"content": "heard maybe we should check this",
                 "source": "unknown", "signal_score": 8.0},
      "action": {"id": "act-4", "type": "read_file", "target": "kpi.csv"}}),
]

ICON = {Verdict.ALLOW: "[ALLOW]", Verdict.REVIEW: "[REVIEW]", Verdict.HALT: "[HALT]"}

print("=" * 64)
print("GUARDIAN AGENT — governed execution demo")
print("=" * 64)
for label, envelope in ENVELOPES:
    d = agent.govern_and_execute(envelope, lambda a: f"executed: {a.type} {a.target}")
    print(f"\n{ICON[d.verdict]:9} {label}")
    for r in d.reasons:
        print(f"          {r}")
    print(f"          executed={d.executed}"
          + (f" -> {d.execution_result}" if d.executed else ""))
    print(f"          audit={d.entry_hash[:16]}...")

ok, msg = agent.ledger.verify()
print(f"\nLedger integrity: {ok} ({msg}) — {len(agent.ledger.entries())} entries")

# Tamper attempt: rewrite the wire-transfer verdict to ALLOW after the fact.
lines = open(LEDGER).read().splitlines()
e = json.loads(lines[3])
e["record"]["verdict"] = "ALLOW"
lines[3] = json.dumps(e, sort_keys=True)
open(LEDGER, "w").write("\n".join(lines) + "\n")
ok, msg = agent.ledger.verify()
print(f"After tampering with entry 4: intact={ok} ({msg})")
print("\nNo action executes without a governance record. Guardian does not")
print("reason or generate. It governs.")
