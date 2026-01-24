# Work Journal - 2026-01-24 12:22
## Workscope ID: Workscope-20260124-122237

## Initialization

**Mode**: Custom (--custom flag provided)
**Status**: Awaiting custom workscope from User

## Onboarding - Project Bootstrapper Report

### Mandatory Files Read

**System Rules:**
1. `docs/read-only/Agent-Rules.md` - Agent behavioral rules (read during /wsd:boot)
2. `docs/read-only/Agent-System.md` - Agent collaboration system (read during /wsd:boot)
3. `docs/read-only/Documentation-System.md` - Documentation organization (read during /wsd:boot)
4. `docs/read-only/Checkboxlist-System.md` - Task management system (read during /wsd:boot)
5. `docs/read-only/Workscope-System.md` - Work assignment system (read during /wsd:boot)

**Applicable Standards:**
6. `docs/read-only/standards/Coding-Standards.md` - Universal coding principles
7. `docs/read-only/standards/Python-Standards.md` - Python-specific requirements

**Project Context:**
8. `docs/core/PRD.md` - Project requirements document
9. `docs/core/Design-Decisions.md` - Project design philosophies

### Key Rules to Remember

**Most Violated Rules (causing rejections):**
1. **Rule 5.1** - No backward compatibility code (app hasn't shipped)
2. **Rule 3.4** - No meta-process references in product artifacts (code/tests)
3. **Rule 3.11** - Copy to workbench if can't edit read-only files

**Critical Behaviors:**
- Rule 3.12: Reject Special Agent approvals without proof of work
- Rules 3.15-3.16: Report ALL discoveries to User (not just workscope items)
- Rule 3.17: No tool exceptions without User approval
- Rule 4.7: Own and resolve all warnings introduced

**Python Standards:**
- All functions need explicit return types
- Type parameters lowercase: `list[int]` not `List[int]`
- Google-style docstrings with Args/Returns/Raises
- Use `uv` for dependency management
- Prefer `Path.open()` over `open()`

