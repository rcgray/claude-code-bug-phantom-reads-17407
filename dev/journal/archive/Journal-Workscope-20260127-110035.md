# Work Journal - 2026-01-27 11:00
## Workscope ID: Workscope-20260127-110035

---

## Initialization Phase

### Project Context
This is the "Phantom Reads Investigation" project - a git repository documenting and investigating the Phantom Reads bug in Claude Code (Issue #17407). The bug causes Claude to believe it has successfully read file contents when it has not.

### WSD Platform Documentation Read
- `docs/read-only/Agent-System.md` ✓
- `docs/read-only/Agent-Rules.md` ✓
- `docs/core/Design-Decisions.md` ✓
- `docs/read-only/Documentation-System.md` ✓
- `docs/read-only/Checkboxlist-System.md` ✓
- `docs/read-only/Workscope-System.md` ✓
- `docs/core/PRD.md` ✓

---

## Onboarding Phase (Project-Bootstrapper)

### Mandatory Reading Files Completed
1. `docs/read-only/Agent-Rules.md` ✓
2. `docs/read-only/standards/Coding-Standards.md` ✓
3. `docs/read-only/standards/Python-Standards.md` ✓
4. `docs/read-only/standards/Specification-Maintenance-Standards.md` ✓
5. `docs/read-only/standards/Process-Integrity-Standards.md` ✓
6. `docs/read-only/standards/Data-Structure-Documentation-Standards.md` ✓
7. `CLAUDE.md` ✓

### Critical Rules to Remember

**THREE MOST VIOLATED RULES:**

1. **Rule 5.1 - NO Backward Compatibility**: This app has NOT shipped. No migration notes, no legacy support, no backward compatibility code.

2. **Rule 3.4 - NO Meta-Process References in Product Artifacts**: Code, tests, scripts must NOT contain phase numbers, task references, ticket numbers, or development timeline references.

3. **Rule 4.1 - Use `dev/diagnostics/` for Temporary Files**: NOT the project root.

**PROJECT-SPECIFIC CRITICAL REQUIREMENT:**
- **DO NOT use the native `Read` tool** - Use MCP filesystem tools instead:
  - `mcp__filesystem__read_text_file`
  - `mcp__filesystem__read_multiple_files`
  - `mcp__filesystem__list_directory`
  - `mcp__filesystem__search_files`

**Source of Truth Priority:** Documentation (Specification) > Test > Code

### Key Standards Summary

**Python Requirements:**
- Type hints MANDATORY on ALL functions including return types
- Lowercase generic types (`list[int]`, NOT `List[int]`)
- Google-style docstrings with `Args:`, `Returns:`, `Raises:`
- Use `Path.open()` over `open()`
- Document ALL pytest fixtures in test methods
- Dataclasses require complete field documentation in Attributes sections

**Specification Maintenance:**
- If code changes, specs MUST be updated in same workscope
- Configuration, environment variable, and interface changes require spec updates
- Drift between spec and implementation is a critical violation

**Process Integrity:**
- Automated tools must produce equivalent results to direct tool execution
- No silent error suppression

---

## Custom Workscope Mode

Initialized with `--custom` flag. Awaiting workscope assignment from User.

