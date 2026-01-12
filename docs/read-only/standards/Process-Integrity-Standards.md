# Process Integrity Standards

**Last Updated:** 2025-08-25
**Managed By:** Inspector Agent
**Purpose:** Ensure development tools and automation maintain accuracy and transparency

## Core Principle

**Automation Fidelity**: All automated development tools (health checks, CI scripts, convenience wrappers) MUST produce functionally equivalent results to running the underlying tools directly, unless explicitly documented exceptions are approved by the user.

## Standards

### 1. Tool Accuracy Requirements

**1.1 Direct Equivalence**
- Automated tools must match the exit codes of their underlying tools
- Output filtering or interpretation requires explicit approval
- Default behavior must be complete pass-through of tool results

**1.2 Transparency Mandate**
- Users must be able to understand what tools are actually doing
- Any filtering, processing, or interpretation must be clearly documented
- Tools must not silently suppress errors or warnings

**1.3 Exception Approval Process**
- All exceptions to direct equivalence must be explicitly approved by the user
- Exceptions must include clear justification and review schedule
- No "emergency" or undocumented exceptions are permitted

### 2. Approved Exceptions

This section documents all approved deviations from direct tool equivalence:

#### 2.1 Future Exceptions

*No other exceptions approved other than those listed below (2.2+).*

*Process for requesting new exceptions:*
1. Submit detailed justification including:
   - Why the underlying tool's behavior needs modification
   - Exact nature of the filtering/interpretation needed
   - Risk assessment of potential masked issues
2. Require explicit user approval before implementation
3. Include review schedule and expiration criteria

#### 2.2 Health Check Script

- Active exceptions to health script are recorded in `docs/read-only/Health-Check-Exceptions.md`

### 3. Audit Schedule

**Periodic Audits:** Inspector agent should be invoked:
- After any changes to automation scripts or tools
- Monthly during active development periods
- When discrepancies are suspected between tools and automation
- Before major releases or milestones

**Audit Checklist:**
- [ ] Compare health check results to direct tool execution
- [ ] Verify all approved exceptions are still necessary
- [ ] Check for unauthorized filtering or suppression
- [ ] Validate documentation accuracy
- [ ] Test edge cases and error scenarios

### 4. Tool Integrity Verification Commands

The following commands verify tool integrity by comparing automated vs direct execution:

#### 4.1 Health Check vs Direct Tools

**Python Example:**
```bash
# Health check version
python scripts/health_check.py

# Direct equivalent tests
uv run mypy src/
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run bandit -r src/ -f screen -ll
uv run pip-audit
```

**TypeScript Example:**
```bash
# Health check version
node scripts/health_check.js

# Direct equivalent tests
npm run tsc --noEmit
npm run eslint src/ tests/
npm run prettier --check src/ tests/
npm audit
```

#### 4.2 Expected Behavior
- Exit codes should match between automated and direct versions
- Error counts should be equivalent
- No suppression of legitimate issues

### 5. Violation Response

**Critical Violations (Immediate Action Required):**
- Silent error suppression without approved exception
- Reporting success when direct tool execution fails
- Undocumented filtering or interpretation

**Response Protocol:**
1. Flag tool as COMPROMISED
2. Disable or add warning to affected automation
3. Require immediate fix before continued use
4. Document incident and prevention measures

**Minor Issues (Schedule for Fix):**
- Formatting differences in output presentation
- Performance optimizations that don't affect accuracy
- Minor discrepancies in non-error scenarios

### 6. Emergency Override

In rare cases where a tool must be temporarily modified due to external factors (e.g., upstream tool bugs), emergency overrides may be implemented with:

1. **Immediate Documentation**: Add entry to this file within same commit
2. **Clear Justification**: Explain why override is necessary
3. **Expiration Date**: Set specific date for review/removal
4. **User Notification**: Clearly inform users of temporary deviation

**Current Emergency Overrides:** None

## Maintenance

This document is maintained by the Inspector agent and should be updated whenever:
- New exceptions are approved
- Tools are modified or added
- Violations are discovered and remediated
- Audit schedules need adjustment

**Version History:**
- v1.0 (2025-08-25): Initial version created in response to a health check accuracy violation
