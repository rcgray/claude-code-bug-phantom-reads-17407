# [Feature Name] Specification

**Version:** 1.0.0
**Date:** YYYY-MM-DD
**Status:** Draft

<!--
INSTRUCTIONS FOR USING THIS TEMPLATE:

This template provides the structural pattern for Feature Overview documents.
For guidance on WRITING effective specifications (meta best practices), see:
docs/references/Feature-Overview-Writing-Guide.md

MANDATORY SECTIONS (must appear in every Feature Overview):
- Document Metadata (this header)
- Overview
- Purpose
- Core Technical Section(s)
- Error Handling
- Testing Scenarios
- Related Specifications
- Feature Implementation Plan (FIP)

CONDITIONAL SECTIONS (include when applicable):
- Edge Cases (if feature has boundary conditions)
- Implementation Requirements (if technical constraints exist)
- Best Practices (strongly recommended for most features)
- Algorithm Specifications (if feature involves algorithms)
- Scenario Specifications (if distinct usage patterns)
- File/Data Format Specifications (if feature defines formats)
- Design Philosophy (if decisions need justification)
- Validation (if validation required)
- Examples (strongly recommended for most features)

Remove these instruction comments before finalizing the document.
-->

## Overview

<!-- MANDATORY SECTION
Write 1-2 paragraphs that:
1. Describe WHAT this feature/system is
2. Explain its primary PURPOSE
3. Reference broader architectural context

See Writing Guide § Overview Section for detailed guidance.
-->

The [Feature Name] [primary function description]. It provides [key capability] for [target users/use case] while [key constraint or benefit].

This specification defines [scope of what this document covers] for [context/purpose of the specification].

For broader architectural context and how [Feature Name] integrates with other [System] components, see [System-Architecture.md or equivalent reference].

## Purpose

<!-- MANDATORY SECTION - CRITICAL FOR OWNERSHIP
List 3-5 critical functions this feature serves.
This section DECLARES OWNERSHIP of concepts/mechanisms to prevent duplication.

Format:
- Bold function name (2-4 words)
- Description (1-2 sentences): What it does and WHY it matters

See Writing Guide § Purpose Section and § Domain Ownership Principle.
-->

The [Feature Name] serves [N] critical functions:

1. **[Function Name]**: [Description of what this function does and why it matters to the system]
2. **[Function Name]**: [Description of what this function does and why it matters to the system]
3. **[Function Name]**: [Description of what this function does and why it matters to the system]
4. **[Function Name]**: [Description of what this function does and why it matters to the system]

<!-- Add 4-5 if needed, minimum 3 -->

This specification establishes the authoritative definition of [list the key aspects/concepts/mechanisms this spec OWNS], and [what else it defines or provides].

## [Core Technical Section 1]

<!-- MANDATORY: At least one core technical section required
FLEXIBLE: Organization depends on feature needs

Choose organizational approach based on feature:
- By Component (if feature has distinct components)
- By Process Phase (if feature is workflow-based)
- By Scenario (if feature has distinct usage patterns)
- By Concern (data structures, algorithms, integration points)

See Writing Guide § Technical Content Organization.

Remove this comment and replace with actual technical content.
-->

### Overview

[Brief overview of this aspect of the feature]

### [Subsection]

[Technical content - depth and structure flexible based on feature needs]

### [Subsection]

[Continue organizing content logically for this feature]

## [Core Technical Section 2]

<!-- FLEXIBLE: Number and organization of technical sections
Include as many sections as needed to cover the feature comprehensively.
-->

[Content organized appropriately for this feature]

<!-- ============================================================
CONDITIONAL SECTIONS - Include when applicable
============================================================ -->

## [Algorithm Specification Name]

<!-- CONDITIONAL: Include if feature involves algorithms
Delete this entire section if not applicable.

Standard algorithm pattern:
- Overview
- Algorithm Specification (with pseudocode)
- Rules
- Special Cases
- Examples
-->

### Overview

[Brief description of what this algorithm does and why]

### Algorithm Specification

```python
def algorithm_name(parameters):
    """
    [Docstring describing algorithm]

    Args:
        [parameter descriptions]

    Returns:
        [return value description]
    """

    # Step 1: [Description of step]
    [code/pseudocode]

    # Step 2: [Description of step]
    [code/pseudocode]

    # Step 3: [Description of step]
    [code/pseudocode]

    return result
```

### [Algorithm Name] Rules

1. **Rule One**: [Description of rule and why it exists]
2. **Rule Two**: [Description of rule and why it exists]
3. **Rule Three**: [Description of rule and why it exists]

### Special Cases

#### Case 1: [Special Case Name]

**Scenario:** [When this case occurs]
**Behavior:** [How system behaves]
**Rationale:** [Why this behavior]
**Handling:** [How to handle]

#### Case 2: [Special Case Name]

[Continue as needed]

### Examples

#### Example 1: [Example Name]

**Setup:** [Initial conditions]
**Action:** [What happens]
**Result:** [Outcome]

```
[Code or output example]
```

## [Scenario Specifications]

<!-- CONDITIONAL: Include if feature has distinct usage patterns
Delete this entire section if not applicable.

Use scenario-based organization when:
- Feature has multiple distinct usage patterns
- User workflows are central
- Examples make feature clearer than abstract description
-->

### Scenario 1: [Scenario Name]

**Context:** [When/why this scenario occurs]

**User Command/Action:**
```bash
[command or action]
```

**Preconditions:**
- [Condition that must be true]
- [Condition that must be true]

**Process Flow:**
1. [Step description]
2. [Step description]
3. [Step description]

**Expected Outcome:**
[What results from this scenario]

**Example Output:**
```
[Example output]
```

### Scenario 2: [Scenario Name]

[Continue pattern for additional scenarios]

## [File Format / Data Structure Specification]

<!-- CONDITIONAL: Include if feature defines file formats or data structures
Delete this entire section if not applicable.
-->

### Purpose

[Why this format/structure exists]

### Structure

```json
{
    "field_name": "example_value",
    "another_field": 123,
    "nested": {
        "field": "value"
    }
}
```

### Fields

#### field_name

**Type:** [data type]
**Purpose:** [what this field is for]
**Required:** [Yes/No]
**Default:** [default value if optional]
**Example:** `"example_value"`

#### another_field

[Continue for all fields]

## Edge Cases

<!-- CONDITIONAL: Include if feature has non-obvious boundary conditions
Delete this entire section if not applicable.

Include when:
- Feature has boundary conditions
- Special cases need different handling
- Non-obvious scenarios exist
-->

### Edge Case 1: [Edge Case Name]

**Scenario:** [Description of the edge case situation]

**Behavior:** [How the system behaves in this case]

**Rationale:** [Why this behavior was chosen]

**Handling:** [How implementers should handle this]

### Edge Case 2: [Edge Case Name]

[Continue as needed]

## Error Handling

<!-- MANDATORY SECTION
Every feature can fail - must specify how.

Organize by error category.
Include error messages, recovery procedures, and guarantees.

See Writing Guide § Error Handling.
-->

### Error Categories

#### 1. [Error Category Name]

**Error:** [Description of error condition]

**Example Message:**
```
[Example error message text]
```

**Recovery:** [How users/systems should recover from this error]

#### 2. [Error Category Name]

**Error:** [Description of error condition]

**Example Message:**
```
[Example error message text]
```

**Recovery:** [How to recover]

[Continue for all error categories]

### Error Recovery

<!-- Optional subsection for general recovery guidance -->

[General error recovery procedures if applicable]

**Automatic Recovery:**
[If system provides automatic recovery mechanisms]

**Manual Recovery:**
[Steps users must take to recover]

## Design Philosophy

<!-- CONDITIONAL: Include when design decisions need justification
Delete this entire section if not applicable.

Include when:
- Non-obvious design choices made
- Trade-offs need explanation
- Alternatives were considered
- Future maintainers need context
-->

[Explanation of design approach and reasoning]

**Why This Design:**
- [Reason for design choice]
- [Reason for design choice]
- [Reason for design choice]

**Alternatives Considered:**
- **[Alternative Approach]**: [Why not chosen]
- **[Alternative Approach]**: [Why not chosen]

## Validation

<!-- CONDITIONAL: Include if feature involves validation
Delete this entire section if not applicable.
-->

### Validation Rules

1. **Rule Name**: [What to validate and how]
2. **Rule Name**: [What to validate and how]

### Validation Process

[When and how validation occurs]

## Implementation Requirements

<!-- CONDITIONAL: Include if feature has specific technical requirements
Delete this entire section if not applicable.
-->

### Performance Requirements

[Performance requirements and metrics]

### Platform Requirements

[Platform/environment requirements]

### Dependencies

**Required Dependencies:**
- [Dependency]: [Version/specification]
- [Dependency]: [Version/specification]

**Optional Dependencies:**
- [Dependency]: [Purpose]

## Testing Scenarios

<!-- MANDATORY SECTION
Provides verification guidance for feature.

Minimum categories: Basic, Edge Case, Integration
Add feature-specific categories as needed.

See Writing Guide § Testing Scenarios.
-->

### Basic [Feature] Tests

1. **Test Name**: [Brief description of test and expected outcome]
2. **Test Name**: [Brief description of test and expected outcome]
3. **Test Name**: [Brief description of test and expected outcome]

### Edge Case Tests

1. **Test Name**: [Brief description of test and expected outcome]
2. **Test Name**: [Brief description of test and expected outcome]

### Integration Tests

1. **Test Name**: [Brief description of test and expected outcome]
2. **Test Name**: [Brief description of test and expected outcome]

<!-- Optional additional test categories -->

### Performance Tests

<!-- Include if performance requirements specified -->

1. **Test Name**: [Description and metrics]

### Security Tests

<!-- Include if security concerns exist -->

1. **Test Name**: [Description and expected outcome]

## Examples

<!-- CONDITIONAL but STRONGLY RECOMMENDED
Include practical examples that demonstrate feature usage.
Delete this entire section if truly not needed (rare).
-->

### Example 1: [Example Name]

**Context:** [Setup/situation]

**Action:** [What happens]

**Result:** [Outcome]

```
[Code/command/output example]
```

**Analysis:** [Explanation of what the example demonstrates]

### Example 2: [Example Name]

[Continue pattern for additional examples]

## Best Practices

<!-- CONDITIONAL but STRONGLY RECOMMENDED
Include for most features.
Delete this entire section if feature has no established best practices yet.

Organize by stakeholder type.
See Writing Guide § Best Practices.
-->

### For Users

1. **[Practice Name]**: [Description and rationale]
2. **[Practice Name]**: [Description and rationale]

**Recommended Workflow:**
```bash
# Step 1: [Action]
[command]

# Step 2: [Action]
[command]

# Step 3: [Action]
[command]
```

### For [Feature] Designers

1. **[Practice Name]**: [Description and rationale]
2. **[Practice Name]**: [Description and rationale]

### For Implementers

1. **[Practice Name]**: [Description and rationale]
2. **[Practice Name]**: [Description and rationale]

## Related Specifications

<!-- MANDATORY SECTION
List related specifications with brief descriptions.
Minimum: One related spec (or reference to broader architecture doc).

Use this format:
- **[Spec-Name.md]**: [Brief description of relationship/what it covers]

See Writing Guide § Cross-Referencing Strategy.
-->

- **[System-Architecture.md]**: [High-level system architecture and component integration]
- **[Related-Spec.md]**: [Brief description of how it relates to this spec]
- **[Another-Spec.md]**: [Brief description of relationship]

---

<!-- MANDATORY: Specification footer statement -->

*This specification defines the authoritative rules for [Feature/System Name] including [key aspects covered]. All implementations must conform to these specifications.*

## In-Flight Failures (IFF)

<!-- This section is required and should be left blank -->

## Feature Implementation Plan (FIP)

<!-- MANDATORY SECTION - ALWAYS LAST
Phase-based checkboxlist for implementation tracking.
Must follow standard checkboxlist format (see Checkboxlist-System.md).

Include testing tasks within implementation phases.
Use hierarchical numbering: Phase.Task.Subtask (e.g., 1.1.1)

IMPORTANT:
- FIP always appears at the END of the document
- No content after FIP
- Remove this comment before finalizing

WARNING: NEVER START WITH PHASE 0
  ❌ WRONG - Phase 0: Core Implementation
  ✅ RIGHT - Phase 1: Core Implementation

  Phase 0 is ONLY for emergencies discovered DURING work, not planned work!
  If you're creating a new ticket, you CANNOT know what emergencies will arise.

  Do not include tasks that would cause the agent to violate a Rule in Agent-Rules.md
  Do not EVER list git commands (e.g. `git commit`) as a work item (violates Rule 2.2)
  Do not include ticket management ("close this ticket") as a work item
-->

### Phase 1: [Phase Name - e.g., "Core Data Structures"]

- [ ] **1.1** - [Task description - action-oriented]
  - [ ] **1.1.1** - [Subtask description]
  - [ ] **1.1.2** - [Subtask description]
  - [ ] **1.1.3** - [Subtask description]
- [ ] **1.2** - [Task description]
  - [ ] **1.2.1** - [Subtask description]
  - [ ] **1.2.2** - [Subtask description]

### Phase 2: [Phase Name - e.g., "Algorithm Implementation"]

- [ ] **2.1** - [Task description]
  - [ ] **2.1.1** - [Subtask description]
  - [ ] **2.1.2** - [Subtask description]
- [ ] **2.2** - [Task description]
  - [ ] **2.2.1** - [Subtask description]

### Phase 3: [Phase Name - e.g., "Error Handling"]

- [ ] **3.1** - [Task description]
- [ ] **3.2** - [Task description]

### Phase 4: [Phase Name - e.g., "Testing and Validation"]

- [ ] **4.1** - [Task description related to testing]
  - [ ] **4.1.1** - [Specific test implementation]
  - [ ] **4.1.2** - [Specific test implementation]
- [ ] **4.2** - [Task description related to integration testing]
- [ ] **4.3** - [Task description related to validation]

### Phase 5: [Phase Name - e.g., "Documentation and Polish"]

- [ ] **5.1** - [Task description]
- [ ] **5.2** - [Task description]
- [ ] **5.3** - [Task description]
