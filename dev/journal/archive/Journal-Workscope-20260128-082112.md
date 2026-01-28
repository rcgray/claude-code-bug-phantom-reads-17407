# Work Journal - 2026-01-28 08:21
## Workscope ID: Workscope-20260128-082112

---

## Initialization

- Initialized with `/wsd:init --custom` flag
- Custom workscope to be assigned by User after initialization
- Project: Phantom Reads Investigation (Claude Code Issue #17407)

---

## Project-Bootstrapper Onboarding

### Mandatory Files to Read (Phase 1)

1. `docs/read-only/Agent-Rules.md` - Inviolable rules (MOST IMPORTANT)
2. `docs/read-only/Agent-System.md` - Agent operation protocols
3. `docs/read-only/Checkboxlist-System.md` - Task state system
4. `docs/read-only/Workscope-System.md` - Workscope lifecycle
5. `docs/read-only/Documentation-System.md` - Documentation organization
6. `docs/core/Design-Decisions.md` - Project-specific design philosophies

**Note:** Files 1-5 were already read during `/wsd:boot`. File 6 was also read.

### Task-Specific Standards (Phase 2 - Read when assignment received)

- `docs/read-only/standards/Coding-Standards.md` - If writing any code
- `docs/read-only/standards/Python-Standards.md` - If writing Python
- `docs/read-only/standards/Python-Test-Environment-Isolation-Standards.md` - If working with tests
- `docs/read-only/standards/Python-Testing-Configuration-Variables-Standards.md` - If working with tests
- `docs/read-only/standards/Environment-and-Config-Variable-Standards.md` - If working with config
- `docs/read-only/standards/Specification-Maintenance-Standards.md` - If modifying specs
- `docs/read-only/standards/Data-Structure-Documentation-Standards.md` - If working with data structures
- `docs/read-only/standards/Process-Integrity-Standards.md` - If working with error handling

### Critical Warnings

1. **Rule 5.1 - NO BACKWARD COMPATIBILITY**: This is a research project. No deprecation warnings, migration paths, or "supporting both old and new."

2. **Rule 3.4 - NO META-COMMENTARY IN PRODUCT**: No task IDs, phase numbers, or workscope references in shipping code.

3. **Rule 3.11 - BLOCKED DIRECTORY WRITES**: If permission denied, write to `/private/tmp/` instead.

### Project-Specific Knowledge

- **File Reading**: Use MCP filesystem tools (`mcp__filesystem__read_text_file`, etc.) instead of native Read tool to avoid Phantom Reads bug
- **`[%]` Tasks**: Treat as `[ ]` - full implementation responsibility
- **Source of Truth**: Documentation > Tests > Code
- **Git**: Read-only commands only (status, log, diff)

### QA Agents with Veto Power

1. Documentation-Steward - Spec compliance
2. Rule-Enforcer - Agent-Rules.md compliance
3. Test-Guardian - Test verification
4. Health-Inspector - Code quality checks

---

---

## Custom Workscope Assignment

**Assigned by**: User (direct assignment)
**Task**: Analyze Barebones-2120 experiment trial data and address RQ-BB2120-1

**Context Documents**:
- `docs/core/Investigation-Journal.md` - Investigation journey and discoveries
- `docs/core/Research-Questions.md` - Research questions catalog
- `docs/experiments/planning/Barebones-2120.md` - Experiment planning document
- `docs/experiments/results/Barebones-2120-Analysis.md` - Analysis target document
- `docs/experiments/guides/Trial-Analysis-Guide.md` - Trial analysis procedures

**Objective**: Perform analysis on the Barebones-2120 trial collection, addressing research questions one-at-a-time. Currently analyzing RQ-BB2120-1: "Did Anthropic fix or mitigate the Phantom Reads bug?"

---

## Execution

### Trial Data Collection

Read trial_data.json files from both collections:

**Barebones-2120 (v2.1.20)** - 5 trials:
- 20260127-095002
- 20260127-100209
- 20260127-100701
- 20260127-100944
- 20260127-101305

**Barebones-216 (v2.1.6)** - 4 valid trials:
- 20260127-092743
- 20260127-093127
- 20260127-093818
- 20260127-094145

### RQ-BB2120-1 Analysis: Did Anthropic Fix the Bug?

**Finding**: ANSWERED - Strong evidence of fix or fundamental optimization

**Key Evidence**:

1. **Tool Persistence Mechanism Changed**:
   - v2.1.20: `has_tool_results: false` (100% of trials) - no persistence
   - v2.1.6: `has_tool_results: true` (100% of trials) - always persisted
   - This is the fundamental difference

2. **Failure Rate Reversal**:
   - v2.1.20: 0% (0/5 trials)
   - v2.1.6: 100% (4/4 valid trials)
   - Statistical significance: p < 0.01 (Fisher's exact test)

3. **Reset Behavior Optimized**:
   - v2.1.20: Exactly 1 reset per trial, at 84-87% (SINGLE_LATE pattern)
   - v2.1.6: 2-3 resets per trial, including mid-session resets (50-75%)
   - 50-67% reduction in reset count

4. **Peak Context Similar**:
   - v2.1.20: 159K-173K tokens
   - v2.1.6: 162K-165K tokens
   - Similar context load, completely different outcomes

**Conclusion**: The Phantom Reads bug appears to be **fixed or fundamentally mitigated** in Claude Code version 2.1.20. The complete elimination of tool persistence and dramatic improvement in reset behavior suggest either a deliberate fix or a major optimization that incidentally resolved the issue. A simple threshold shift is unlikely given the categorical nature of the change (0% vs 100% failure) and the fundamental difference in persistence behavior.

**Updated Document**: `docs/experiments/results/Barebones-2120-Analysis.md` (RQ-BB2120-1 section)

---

## Status

RQ-BB2120-1 analysis complete. Ready for User review and next steps.

