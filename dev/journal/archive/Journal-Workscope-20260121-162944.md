# Work Journal - 2026-01-21 16:29
## Workscope ID: Workscope-20260121-162944

## Initialization Phase

### WSD Platform Files Read
- `docs/read-only/Agent-System.md` - Agent collaboration system, User Agents, Special Agents
- `docs/read-only/Agent-Rules.md` - Strict behavioral rules (SOLID, DRY, KISS, YAGNI, forbidden actions)
- `docs/core/Design-Decisions.md` - Project-specific design philosophies (currently minimal)
- `docs/read-only/Documentation-System.md` - Documentation organization (diagnostics, workbench, permanent)
- `docs/read-only/Checkboxlist-System.md` - Checkbox states and Phase 0 blocking system
- `docs/read-only/Workscope-System.md` - Workscope files, selection algorithm, lifecycle

### Project-Specific Files Read
- `docs/core/PRD.md` - Phantom Reads Investigation project overview

## Onboarding Phase (Project-Bootstrapper)

### Mandatory Standards Files Read
1. `docs/read-only/standards/Coding-Standards.md` - Fail aggressively, Chesterton's Fence, Sources of Truth priority, no meta-process references, use comment blocks, 4 spaces indentation
2. `docs/read-only/standards/Python-Standards.md` - Use `uv`, explicit return type annotations, lowercase type params (list not List), Path.open(), Google-style docstrings, pytest fixture documentation

### Project-Specific Context
- **Project Type**: Investigation and documentation project for Claude Code Issue #17407 (Phantom Reads)
- **Dual Audience**: Internal docs (can reference WSD) vs External docs (must NOT reference WSD)
- **Key Terms**:
  - Session Agent: Agent being analyzed in example sessions
  - Phantom Read: Silent read failure where agent believes it read content but didn't
  - Era 1 (≤2.0.59): Phantom reads via `[Old tool result content cleared]`
  - Era 2 (≥2.0.60): Phantom reads via unresolved `<persisted-output>` markers
  - Reset Timing Theory: Mid-session context resets (50-90%) predict phantom reads with 100% accuracy

### Key Files to Be Aware Of
- `docs/core/Action-Plan.md` - Implementation checkboxlist
- `docs/core/Investigation-Journal.md` - Running log of discoveries
- `docs/core/Experiment-Methodology-02.md` - Current controlled trial protocol
- `src/cc_version.py` - Claude Code version management
- `src/collect_trials.py` - Trial data collection
- `dev/karpathy/extract_trial_data.py` - Trial preprocessing script
- `README.md` - External documentation (NO WSD references allowed)
- `WORKAROUND.md` - MCP bypass workaround

### Critical Rules to Remember
- **Rule 5.1**: NO backward compatibility (no migration, legacy support, fallbacks)
- **Rule 3.4**: NO meta-commentary in shipping code (no phase numbers, task IDs)
- **Rule 3.11**: Use `dev/diagnostics/` for temporary artifacts if blocked from read-only dirs
- **Rule 4.4**: `cat >> file << EOF` is FORBIDDEN
- **Sources of Truth**: Documentation > Test > Code

### Pre-Work Checklist Verified
- [x] Internal vs external docs distinction understood
- [x] Session Agents vs User Agents vs Special Agents understood
- [x] Era 1 vs Era 2 phantom read mechanisms understood
- [x] Reset Timing Theory as current working hypothesis understood
- [x] Python typing requirements understood (lowercase params, explicit returns)
- [x] Agent Rule 5.1 (no backward compatibility) understood
- [x] Agent Rule 3.4 (no meta-commentary) understood
- [x] Agent Rule 3.11 (dev/diagnostics for temp artifacts) understood

## Custom Workscope Status
Awaiting custom workscope assignment from the User.

