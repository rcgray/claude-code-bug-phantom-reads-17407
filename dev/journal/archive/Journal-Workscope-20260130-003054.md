# Work Journal - 2026-01-30 00:31
## Workscope ID: Workscope-20260130-003054

### Initialization

- Read project introduction (PRD.md) - Phantom Reads Investigation project for Claude Code Issue #17407
- Completed WSD Platform boot - read all 6 system documents (Agent-System, Agent-Rules, Design-Decisions, Documentation-System, Checkboxlist-System, Workscope-System)
- Generated Workscope ID: 20260130-003054
- Created Work Journal at `dev/journal/archive/Journal-Workscope-20260130-003054.md`
- Mode: `--custom` (awaiting User assignment)

### Custom Workscope: Analyze schema-13-216 Collection (Step 2.3)

- Read planning document: `docs/experiments/planning/Build-Scan-Discrepancy-Investigation.md`
- Read analysis document: `docs/experiments/results/Build-Scan-Discrepancy-Analysis.md`
- Read Trial Analysis Guide: `docs/experiments/guides/Trial-Analysis-Guide.md`
- Task: Analyze 6 trials in `dev/misc/schema-13-216/` (build 2.1.6) for Step 2.3

### Step 2.3 Analysis: schema-13-216 Trial Data

Read all 6 `trial_data.json` files. Summary:

| Trial ID | Outcome | has_tool_results | has_subagents | Main-Session Reads | Resets | Pattern | Peak total_input | 1st Reset From | Compaction Loss (1st) | Initial Cache |
| -------- | ------- | ---------------- | ------------- | ------------------ | ------ | ------- | ---------------- | -------------- | --------------------- | ------------- |
| 230228 | FAILURE | true | false | 10 (9 + WPD re-read) | 2 | OTHER | 175,225 | 133,899 | −20,026 | 14,053 |
| 230236 | SUCCESS | false | true | 1 (delegation) | 1 | SINGLE_LATE | 145,671 | 140,978 | −4,690 | 15,825 |
| 230244 | SUCCESS | true | false | 14 (9 + 5 recovery) | 2 | EARLY_PLUS_LATE | 176,683 | 133,894 | −9,181 | 15,825 |
| 231053 | SUCCESS | false | true | 4 (delegation) | 1 | SINGLE_LATE | 158,809 | 153,444 | −5,362 | 15,825 |
| 231100 | FAILURE | true | false | 10 (9 + WPD recovery) | 2 | OTHER | 166,477 | 125,286 | −17,856 | 15,825 |
| 231108 | SUCCESS | false | true | 4 (delegation) | 1 | SINGLE_LATE | 157,204 | 152,387 | −4,814 | 15,825 |

Outcome Distribution:
- FAILURE (persistence, phantom reads): 2 (230228, 231100)
- SUCCESS (sub-agent delegation): 3 (230236, 231053, 231108)
- SUCCESS (persistence + recovery): 1 (230244)

Key findings:
1. Build 2.1.6 exhibits both delegation (3/6) AND persistence (3/3 direct-reads) — definitive server-side confirmation
2. 100% persistence among direct-read trials; 0% among delegation trials
3. Second confirmed recovery SUCCESS (trial 230244) — now 2/20 classified persistence trials
4. Reset bands (~125K, ~134K) consistent with all prior collections
5. Build 2.1.6 behaviorally indistinguishable from 2.1.20 and 2.1.22 on same day

### Documents Updated

1. `docs/experiments/results/Build-Scan-Discrepancy-Analysis.md` — Step 2.3 section written (7 observations + interpretation), Phase 2 Synthesis updated (now complete), Document History updated
2. `docs/experiments/planning/Build-Scan-Discrepancy-Investigation.md` — Success Criterion #5 answered, Priority/Sequencing updated (Phase 2 complete, Step 3.2 is NEXT)
3. `docs/theories/Server-Side-Variability-Theory.md` — Evidence base expanded to include 2.1.6 (55+ trials, 8 collections); Evidence 4 updated (4 server states); Evidence 5 updated (formal trial data for 2.1.6); OQ-SSV-4 answered; Theory Status Summary upgraded (delegation now "Strongly supported" at High confidence; mitigation-not-fix now "Strongly supported" at High confidence)

