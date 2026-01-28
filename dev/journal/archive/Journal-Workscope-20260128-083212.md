# Work Journal - 2026-01-28 08:32
## Workscope ID: Workscope-20260128-083212

## Initialization

- **Mode**: Custom workscope (`/wsd:init --custom`)
- **Time**: 2026-01-28 08:32:12

## Project Context

This is the **Phantom Reads Investigation** project - a repository documenting and investigating Claude Code Issue #17407. The bug causes Claude to believe it has successfully read file contents when it has not.

**Critical Workaround**: Native `Read` tool is disabled. Must use MCP filesystem tools:
- `mcp__filesystem__read_text_file`
- `mcp__filesystem__read_multiple_files`
- `mcp__filesystem__list_directory`
- `mcp__filesystem__search_files`

## Project-Bootstrapper Onboarding

### Files Read During Onboarding

**TIER 1 - System Documentation (read during /wsd:boot):**
1. `docs/read-only/Agent-System.md` - Agent collaboration model
2. `docs/read-only/Agent-Rules.md` - Strict behavioral rules
3. `docs/core/Design-Decisions.md` - Project design philosophies
4. `docs/read-only/Documentation-System.md` - Document organization
5. `docs/read-only/Checkboxlist-System.md` - Task tracking system
6. `docs/read-only/Workscope-System.md` - Work assignment system

**TIER 2 - Coding Standards (read during /wsd:onboard):**
7. `docs/read-only/standards/Coding-Standards.md` - Universal coding standards
8. `docs/read-only/standards/Python-Standards.md` - Python-specific standards
9. `docs/read-only/standards/Process-Integrity-Standards.md` - Tool integrity standards
10. `docs/read-only/standards/Specification-Maintenance-Standards.md` - Spec sync requirements

**TIER 3 - Project Context (read during initialization):**
11. `docs/core/PRD.md` - Project requirements document
12. `CLAUDE.md` - Project overview and commands

### Key Rules to Remember

1. **Rule 5.1** - NO backward compatibility support (most violated rule)
2. **Rule 3.4** - No meta-process references in product artifacts
3. **Rule 3.11** - If write access blocked, copy to docs/workbench/
4. **Rule 4.4** - Do NOT use `cat >>` or `echo >>` to write files
5. **Rule 4.5** - Retry file reads before claiming file doesn't exist

### QA Agents with Veto Power

- **Documentation-Steward** - Specification compliance
- **Rule-Enforcer** - Agent-Rules.md compliance
- **Test-Guardian** - Test coverage verification
- **Health-Inspector** - Code quality checks

### Source of Truth Priority

Documentation (Specification) > Test > Code

---

## Custom Workscope Assignment

**Task**: Analyze Barebones-2120 experiment trials, specifically RQ-BB2120-2 (context consumption comparison)

**Context Files Read**:
- `docs/core/Investigation-Journal.md` - Full investigation history
- `docs/core/Research-Questions.md` - Research questions catalog
- `docs/experiments/planning/Barebones-2120.md` - Experiment planning document
- `docs/experiments/results/Barebones-2120-Analysis.md` - Analysis document (target for updates)
- `docs/experiments/guides/Trial-Analysis-Guide.md` - Trial analysis methodology

---

## RQ-BB2120-2 Analysis: Context Consumption Patterns

### Data Extraction

**Source**: Chat exports (grep for `/context` output) and trial_data.json files

**Barebones-2120 (v2.1.20) - All 5 trials**:
| Trial ID | Baseline | Post-Setup (X) | Post-Analysis | Peak Tokens |
|----------|----------|----------------|---------------|-------------|
| 095002   | 20k (10%) | 114k (57%)    | 195k (97%)    | 159,633     |
| 100209   | 20k (10%) | 114k (57%)    | 195k (97%)    | 172,990     |
| 100701   | 20k (10%) | 114k (57%)    | 195k (97%)    | 172,999     |
| 100944   | 20k (10%) | 114k (57%)    | 195k (97%)    | 173,000     |
| 101305   | 20k (10%) | 114k (57%)    | 195k (97%)    | 159,921     |

**Barebones-216 (v2.1.6) comparison**:
- Baseline: 20k (10%) - IDENTICAL
- Post-Setup: 116k (58%) - ~2% higher
- Post-Analysis: 175-177k (87-89%) - **20k LOWER than v2.1.20**

### Key Finding

**Counter-Intuitive Result**: v2.1.20 achieves HIGHER final context utilization (97% vs 87-89%) yet experiences ZERO phantom reads.

**Interpretation**: 
- The extra ~20k tokens in v2.1.20 represent content that was previously persisted to `tool-results/` directories in v2.1.6
- v2.1.20 keeps tool results inline rather than persisting them
- This **rules out the threshold shift hypothesis** - if thresholds simply increased, we'd see LOWER utilization, not higher

### Analysis Document Updated

Updated `docs/experiments/results/Barebones-2120-Analysis.md`:
- Filled in RQ-BB2120-2 section with complete data tables
- Added peak tokens from session files
- Added comparison summary table
- Added finding and conclusion
- Updated Cross-Collection Comparison table

---

**STATUS**: RQ-BB2120-2 analysis complete. Ready for User review and next RQ.

