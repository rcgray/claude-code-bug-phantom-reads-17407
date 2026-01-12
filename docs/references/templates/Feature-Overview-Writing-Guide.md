# Feature Overview Writing Guide: Meta Best Practices

**Version:** 1.0.0
**Date:** 2025-11-13
**Status:** Draft

## Introduction

This guide provides **meta best practices** for writing effective Feature Overview specifications. These principles are **orthogonal to structure** - they apply regardless of which section you're writing or how your technical content is organized.

**Companion Documents:**
- **Feature-Overview-Template.md**: Structural pattern (which sections, what format)
- **Feature-Overview-Checklist.md**: Quick verification checklist
- **Feature-Overview-Template-Elements.md**: Detailed element analysis

**Key Distinction:**
- **Structural Best Practices**: Which sections to include (covered by template)
- **Meta Best Practices**: How to write effective specifications (covered by this guide)

**Example:**
- Structural: "Every Feature Overview must have an Error Handling section"
- Meta: "Write specs to be evergreen - avoid details that will frequently change"

The meta practices in this guide apply while writing ANY section of your Feature Overview.

## Core Principles

### Principle 1: Source of Truth (No Duplication)

**The Problem:**
When the same information appears in multiple specifications, it creates:
- **Waste**: Duplicated effort maintaining same content in multiple places
- **Confusion**: Which version is correct when they differ?
- **Spec Drift**: One spec gets updated, others don't, creating inconsistency

**The Principle:**
Every concept, definition, algorithm, or mechanism should be defined in **exactly one** authoritative specification. Other specs reference it, never duplicate it.

**How to Apply:**

**Bad - Duplication:**
```markdown
<!-- In Feature-A-Overview.md -->
## File Permissions

Files are marked executable using the following process:
[detailed explanation of permission setting]

<!-- In Feature-B-Overview.md -->
## Setting Permissions

When files need executable permission, we:
[same explanation, slightly different wording]
```

**Good - Single Source, Cross-Reference:**
```markdown
<!-- In Template-System.md (authoritative source) -->
## File Permission Model

[Complete, authoritative specification of permission system]

<!-- In Installation-System.md (references it) -->
## File Permission Handling

For complete file permission model including declaration rationale and
conservative approach, see **Template-System.md § File Permission Model**.

**Installation Implementation:**
[Installation-specific behavior only, references Template spec for details]
```

**When You're Writing:**
1. **Before defining something**: Search existing specs - has this been defined?
2. **If already defined**: Reference it with § notation, don't re-explain
3. **If not defined**: This spec may be the right place to own it
4. **Declare ownership**: Use Purpose section to claim this concept

**Cross-Referencing Format:**
```markdown
For [complete/authoritative] [topic] specification, see **[Document-Name.md § Section Name]**.
```

---

### Principle 2: Domain Ownership (Clear Boundaries)

**The Problem:**
Without clear ownership, multiple specs might partially define the same concept, leading to:
- Ambiguity about which spec is authoritative
- Incomplete definitions scattered across documents
- Difficulty finding complete information

**The Principle:**
Each Feature Overview should **declare ownership** of specific concepts, mechanisms, and responsibilities. The Purpose section exists precisely for this declaration.

**How to Apply:**

**Purpose Section as Ownership Declaration:**

The Purpose section serves two functions:
1. Explains WHY the feature exists (user-facing purpose)
2. Declares WHAT aspects the spec owns (ownership declaration)

**Example - Template System Purpose:**
```markdown
## Purpose

The WSD Template System serves three critical functions:

1. **Distribution**: Provides complete file set implementing workscope workflow
2. **Customization**: Allows users to adapt WSD to their project needs
3. **Preservation**: Maintains user customizations across WSD updates

This specification establishes the authoritative definition of:
- Template file organization
- WORKSCOPE-DEV tag syntax and preservation
- .wsdkeep placeholder files
- File permission model
- no_overwrite policy
- wsd.json metadata format
```

**Ownership Benefits:**
- AI agents know where to find .wsdkeep definition
- Other specs know to reference Template spec for tag syntax
- Prevents installation spec from duplicating tag syntax

**Ownership Test:**
Ask: "If someone needs to know how [X] works, which ONE spec should they read?"

If the answer isn't clear, you have an ownership problem.

**When You're Writing:**
1. **In Purpose section**: List concepts/mechanisms this spec owns
2. **In technical sections**: Provide complete definition of owned concepts
3. **When referencing**: Point to owner spec for concepts you don't own

---

### Principle 3: Evergreen Writing (Accommodate Evolution)

**The Problem:**
Specs that are too specific become outdated quickly, requiring constant updates as the system evolves.

**The Principle:**
Write specifications that **accommodate natural evolution** without requiring updates. Focus on patterns and rules rather than enumeration of current instances.

**Anti-Patterns to Avoid:**

**Bad - Too Specific (Brittle):**
```markdown
## User Archetypes

The testing system provides 3 user archetypes:
1. Admin User
2. Regular User
3. Guest User
```

**Why Bad:** Breaks when 4th archetype added. Spec must be updated.

**Good - Evergreen (Resilient):**
```markdown
## User Archetypes

The testing system supports multiple user archetypes for testing different
end-user scenarios. Each archetype defines a distinct permission level and
behavior profile.

Archetypes are defined in `config/test-archetypes.json`, which maps archetype
names to permission sets and behavioral constraints.
```

**Why Good:** New archetypes can be added without spec changes. Spec describes system, not current instances.

---

**Bad - Enumerating Current State:**
```markdown
## Template Files

The WSD template includes the following files:
- .claude/agents/task-master.md
- .claude/agents/rule-enforcer.md
- .claude/agents/health-inspector.md
- docs/core/Action-Plan.md
- docs/core/PRD.md
[... 50 more files ...]
```

**Why Bad:** Every file addition/removal requires spec update. List provides no value over scanning directory.

**Good - Pattern-Based:**
```markdown
## Template File Organization

The WSD Runtime is a self-contained directory containing all files copied to
user projects during installation. Files are organized by concern:

- `.claude/`: Agent definitions, commands, hooks, and settings
- `dev/`: Development artifacts and working directories
- `docs/`: Documentation hierarchy including core specs, features, and standards
- `scripts/`: Utility scripts for health checks and automation

For the complete directory structure, see the source/ directory in the WSD
Development repository or System-Architecture.md.
```

**Why Good:** Describes organization pattern. New files fit into existing structure without spec changes.

---

**Bad - Overly Specific Implementation:**
```markdown
## Cache Size Configuration

The cache size is configured in the .apprc file on line 45, where the value
is set to 100MB. This value should be between 10MB and 500MB.
```

**Why Bad:** Line number changes with edits. Specific value is example, not requirement. Brittle.

**Good - Pattern and Constraints:**
[Note: nested triple-backticks in example below are converted to tag to aid proper markdown rendering of larger, encapsulating file]
```markdown
## Cache Size Configuration

Cache size is configured via the `cache.max_size` setting in the application
configuration file (`.apprc`).

**Configuration:**
<triple-backticks> toml
[cache]
max_size = 100  # Size in MB
</triple-backticks>

**Constraints:**
- **Type**: Integer
- **Range**: 10-500 (MB)
- **Default**: 100MB if not specified
```

**Why Good:** Describes mechanism and constraints. Resilient to code changes.

---

**Evergreen Writing Checklist:**

When writing, ask yourself:
- [ ] Am I describing a **pattern** or listing **current instances**?
- [ ] Will this section need updates when we add new [items]?
- [ ] Am I specifying **constraints** or **current values**?
- [ ] Does this describe **how the system works** or **current system state**?
- [ ] Could this be more abstract without losing clarity?

**Prefer:**
- Patterns over enumerations
- Rules over examples (but provide examples!)
- Constraints over specific values
- Mechanisms over current state
- "Supports multiple..." over "Has 3..."

---

### Principle 4: Appropriate Abstraction (Right Level of Detail)

**The Problem:**
Specs can be too abstract (useless) or too specific (brittle). Finding the right level is critical.

**The Principle:**
Specify **what must be true** for correctness, not **how to implement it**. Define interfaces, constraints, and behaviors - let implementation choose details.

**Abstraction Spectrum:**

```
Too Abstract ←────────────── Appropriate ──────────────→ Too Specific
  (Useless)                   (Useful)                      (Brittle)
```

**Too Abstract:**
```markdown
## Error Handling

The system should handle errors appropriately.
```

**Why Bad:** No actionable guidance. Doesn't constrain implementation.

**Too Specific:**
```markdown
## Error Handling

When a file read fails, the system must:
1. Create an ErrorHandler object
2. Call ErrorHandler.logError() with error code 1042
3. Store the error in errors[] array at position determined by (timestamp % 1000)
4. Display error using the showErrorDialog() function with font size 14
5. Wait exactly 500ms before returning
```

**Why Bad:** Over-constrains implementation. Brittle. Most details irrelevant to correctness.

**Appropriate Abstraction:**
[Note: nested triple-backticks in example below are converted to tag to aid proper markdown rendering of larger, encapsulating file]
```markdown
## Error Handling

When a file read fails, the system MUST:
1. Log the error with sufficient context (file path, error type, timestamp)
2. Display clear error message to user including:
   - What operation failed
   - Why it failed (permission, not found, etc.)
   - How to resolve (actionable steps)
3. Provide recovery mechanism (retry, skip, abort)

**Example Error Message:**
<triple-backticks>
Error: Cannot read file '/path/to/config.toml'
Reason: Permission denied
Action: Grant read permission: chmod u+r /path/to/config.toml
</triple-backticks>
```

**Why Good:** Specifies required behavior and user experience. Implementation details unconstrained. Testable.

---

**Abstraction Guidelines by Section:**

**Algorithm Specifications:**
- Specify the algorithm's logic flow
- Don't specify variable names or data structures (unless critical)
- Focus on correctness constraints

**Error Messages:**
- Specify what information must be included
- Provide examples, don't mandate exact wording
- Focus on user needs (what, why, how to resolve)

**File Formats:**
- Specify field semantics and constraints
- Don't specify field order (unless binary format requires it)
- Use JSON schema or similar for precision

**Integration Points:**
- Specify interfaces and contracts
- Don't specify internal implementation
- Define guarantees and requirements

---

### Principle 5: Requirements Language Precision

**The Problem:**
Vague language like "should", "needs to", "will" creates ambiguity about what's required versus optional.

**The Principle:**
Use RFC 2119 requirements language (MUST/SHOULD/MAY) to create clear obligations.

**Requirement Levels:**

**MUST / REQUIRED / SHALL:**
- Absolute requirement
- No exceptions allowed
- Violation means non-conformance

**Example:**
```markdown
The system MUST validate all user input before processing.

Files in the no_overwrite array MUST never be overwritten during updates.
```

**SHOULD / RECOMMENDED:**
- Strong recommendation
- Exceptions allowed with justification
- Preferred approach

**Example:**
```markdown
The system SHOULD log all file operations for debugging.

Error messages SHOULD include specific resolution steps.
```

**MAY / OPTIONAL:**
- Truly optional
- Implementation choice
- No conformance requirement

**Example:**
```markdown
The system MAY provide progress indication for long operations.

Implementations MAY cache results for performance.
```

---

**Contract/Guarantee/Requirement Labels:**

For critical behaviors, use explicit labels:

**Guarantee:**
```markdown
**Guarantee:** If update fails, manifest MUST be restored to pre-update state.
```

**Contract:**
```markdown
**Contract:** Dry-run report MUST accurately reflect what normal update would do.
```

**Requirement:**
```markdown
**Requirement:** All operations MUST be atomic - either fully succeed or fully fail.
```

---

**Anti-Patterns:**

**Bad - Vague:**
```markdown
The system should probably handle large files efficiently.
```

**Good - Precise:**
```markdown
The system SHOULD detect files larger than 100MB and warn users before loading
into memory.
```

**Bad - False Obligation:**
```markdown
Implementations MUST use the Frobnicator class for all widget processing.
```

**Why Bad:** Over-constrains implementation when not necessary for correctness.

**Good - Appropriate Constraint:**
```markdown
Widget processing MUST be idempotent - processing the same widget multiple
times MUST produce the same result.
```

---

### Principle 6: Cross-Referencing Strategy

**The Problem:**
Without clear cross-referencing, readers and AI agents can't navigate the documentation web effectively.

**The Principle:**
Cross-reference strategically to:
- Avoid duplication (reference instead of re-explain)
- Provide context (link to broader understanding)
- Declare dependencies (what you build upon)
- Guide readers (where to go next)

**Cross-Reference Types:**

**1. Ownership Reference (Avoid Duplication):**

Used when another spec owns a concept you're using.

```markdown
For complete tag syntax specification including validation rules and edge case
handling, see **Template-System.md § WORKSCOPE-DEV Tag System**.
```

**When to use:** You're using a concept defined elsewhere. Don't duplicate - reference.

---

**2. Context Reference (Broader Understanding):**

Used to link to broader architectural understanding.

```markdown
For broader architectural context and how the Update System integrates with
other WSD components, see System-Architecture.md.
```

**When to use:** In Overview section, to connect feature to bigger picture.

---

**3. Forward Reference (Detailed Coverage Later):**

Used when briefly mentioning something covered in detail elsewhere in SAME document.

```markdown
This section specifies WHEN and WHERE preservation applies during updates,
not HOW the algorithm works. For complete algorithm specification, see
§ Content Preservation Algorithm below.
```

**When to use:** Clarify scope boundaries within your spec.

---

**4. Related Specification Reference:**

Used in Related Specifications section to build documentation network.

```markdown
## Related Specifications

- **Template-System.md**: Tag syntax and preservation algorithm
- **Installation-System.md**: Fresh installation process
- **WSD-Manifest-Schema.md**: Detailed manifest format
```

**When to use:** Always, in Related Specifications section. Minimum one reference.

---

**Reference Format Standards:**

**Section Reference (§ notation):**
```markdown
See **Document-Name.md § Section Name**.
```

**Why § notation:** Clear, precise, searchable, used consistently.

**Document Reference:**
```markdown
See Document-Name.md for [what it covers].
```

**Multiple Sections:**
```markdown
See Template-System.md for:
- § WORKSCOPE-DEV Tag System (tag syntax)
- § Content Preservation Algorithm (how preservation works)
- § File Permission Model (permission handling)
```

---

**Cross-Reference Density:**

**Too Few:**
- Readers can't find related information
- Duplication more likely
- Documentation feels isolated

**Too Many:**
- Text becomes cluttered
- Important references lost in noise
- Reading flow disrupted

**Right Amount:**
- Reference instead of duplicate (always)
- Provide context (in Overview)
- Clarify scope (when needed)
- Build network (Related Specifications)

---

### Principle 7: Writing for AI Agents

**The Problem:**
AI agents consume specifications differently than human readers. Specs optimized only for humans may be difficult for agents to navigate.

**The Principle:**
Write specifications that are both human-readable AND AI-agent-navigable.

**AI Agent Needs:**

**1. Quick Ownership Identification:**

AI agents need to quickly answer: "Which spec owns [concept X]?"

**Solution:** Purpose section with clear ownership declaration.

```markdown
## Purpose

The Template System serves three critical functions:
[...]

This specification establishes the authoritative definition of:
- .wsdkeep placeholder files
- WORKSCOPE-DEV tag syntax
- Content preservation algorithm
- File permission model
```

**Why Effective:** Agent can scan Purpose sections to find owner of ".wsdkeep" concept.

---

**2. Hierarchical Structure:**

AI agents parse markdown structure. Clear hierarchy helps navigation.

**Good Structure:**
```markdown
## Major Topic

### Subtopic

#### Detail

##### Fine Detail
```

**Bad Structure:**
```markdown
## Topic

Some content

Another Topic Without Header

### Inconsistent Level
```

**Why Matters:** Agents use header hierarchy to understand document organization.

---

**3. Explicit Section Headers:**

AI agents search by section name. Descriptive headers help.

**Bad - Vague:**
```markdown
## Details
## Information
## Notes
```

**Good - Descriptive:**
```markdown
## Error Handling
## Testing Scenarios
## Algorithm Specification
```

---

**4. Consistent Patterns:**

When specs follow consistent patterns, agents learn the pattern once and apply it everywhere.

**Examples:**
- Algorithm specs always have: Overview, Specification, Rules, Special Cases, Examples
- Error handling always organized by category
- Testing always divided into: Basic, Edge Case, Integration

**Why Matters:** Pattern recognition makes agent navigation more efficient.

---

**5. Explicit Contracts and Guarantees:**

AI agents implementing features need clear behavioral contracts.

**Vague:**
```markdown
The system tries to ensure data consistency.
```

**Explicit:**
```markdown
**Guarantee:** All operations are atomic. If any step fails, all changes are
rolled back to the pre-operation state.

**Contract:** The preservation algorithm MUST preserve user content byte-for-byte,
including whitespace and formatting.
```

---

**6. Searchable Terminology:**

Use consistent terminology that agents can search for.

**Inconsistent:**
```markdown
<!-- In one section -->
The collision detection algorithm...

<!-- In another section -->
The file conflict checker...

<!-- In another section -->
The duplicate file finder...
```

**Why Bad:** Three different terms for same concept. Hard to search.

**Consistent:**
```markdown
<!-- Throughout document -->
The collision detection algorithm...
```

---

### Principle 8: Example Quality

**The Problem:**
Examples can be too trivial (useless) or too complex (overwhelming). Examples should clarify, not confuse.

**The Principle:**
Provide examples that:
- Demonstrate real usage
- Show edge cases
- Clarify abstract concepts
- Are self-contained (understandable without external context)

**Example Quality Levels:**

**Trivial (Not Helpful):**
```markdown
### Example: File Copy

Copy file A to file B.
```

**Why Bad:** Obvious. Doesn't demonstrate anything useful.

---

**Too Complex (Overwhelming):**
```markdown
### Example: Multi-Phase Enterprise Deployment

Given a distributed system with 47 microservices across 3 availability zones,
with complex dependency graphs, circuit breakers, and service mesh integration...

[300 lines of configuration and setup]
```

**Why Bad:** Reader lost in complexity. Can't extract principle being demonstrated.

---

**Appropriate (Helpful):**
[Note: nested triple-backticks in example below are converted to tag to aid proper markdown rendering of larger, encapsulating file]
```markdown
### Example 1: Update with Tag Preservation

**Destination File** (`.claude/commands/wsd/init.md`):
<triple-backticks> markdown
## PROJECT INTRODUCTION

<WORKSCOPE‑DEV wsd-init-project-introduction>
MyAwesomeProject is a revolutionary SaaS platform for...
We leverage AI-assisted development with Claude Code.
</WORKSCOPE‑DEV>
</triple-backticks>

**Update File** (`.claude/commands/wsd/init.md`):
<triple-backticks> markdown
## PROJECT INTRODUCTION

<WORKSCOPE‑DEV wsd-init-project-introduction>
Describe your project here
</WORKSCOPE‑DEV>

## WORKSCOPE SYSTEM

**IMPORTANT**: You are about to read...
</triple-backticks>

**Result After Update**:
<triple-backticks> markdown
## PROJECT INTRODUCTION

<WORKSCOPE‑DEV wsd-init-project-introduction>
MyAwesomeProject is a revolutionary SaaS platform for...
We leverage AI-assisted development with Claude Code.
</WORKSCOPE‑DEV>

## WORKSCOPE SYSTEM

**IMPORTANT**: You are about to read...
</triple-backticks>

**Analysis:**
- User's project introduction preserved
- New context text added around tag
- Template improvements integrated seamlessly
```

**Why Good:**
- Concrete and specific
- Shows before/after clearly
- Demonstrates key principle (tag preservation)
- Includes analysis explaining what happened
- Self-contained

---

**Example Best Practices:**

**1. Progress Through Complexity:**

Start with simple example, build to complex.

```markdown
### Example 1: Simple Content Preservation (Single Tag)
[Simple case]

### Example 2: Multiple Tags
[More complex]

### Example 3: New Tag with Initial Content
[Edge case]
```

---

**2. Name Examples Descriptively:**

**Bad:**
```markdown
### Example 1
### Example 2
### Example 3
```

**Good:**
```markdown
### Example 1: Simple Direct Selection
### Example 2: Hierarchical Breakdown
### Example 3: Cross-Document Navigation
```

---

**3. Include Analysis:**

Don't just show the example - explain what it demonstrates.

```markdown
**Analysis:**
- User content within tag preserved byte-for-byte
- Template context around tag updated from new version
- Demonstrates core preservation principle
```

---

**4. Use Realistic but Simplified Data:**

**Too Fake:**
```markdown
user: "foo"
project: "bar"
```

**Too Real:**
```markdown
user: "john.smith.contractor.external.dept5847@mega-corp-global-international.com"
project: "fiscal-year-2024-q3-customer-engagement-platform-microservice-refactor-phase-2b"
```

**Right Balance:**
```markdown
user: "john_smith"
project: "customer-platform"
```

---

### Principle 9: Specification Completeness

**The Problem:**
Incomplete specs force implementers to guess, leading to inconsistent implementations.

**The Principle:**
A complete specification addresses:
- Normal operation (happy path)
- Error conditions (what can go wrong)
- Edge cases (boundary conditions)
- Performance expectations (if relevant)
- Integration points (how it fits in)

**Completeness Checklist:**

When writing a specification, ensure you've covered:

**Normal Operation:**
- [ ] Primary use case explained
- [ ] Step-by-step process defined
- [ ] Expected outcomes specified
- [ ] Examples provided

**Error Conditions:**
- [ ] All failure modes identified
- [ ] Error messages specified
- [ ] Recovery procedures defined
- [ ] Guarantees stated (what remains true even on failure)

**Edge Cases:**
- [ ] Boundary conditions identified
- [ ] Special cases specified
- [ ] Non-obvious scenarios covered
- [ ] Handling defined for each

**Integration:**
- [ ] Dependencies identified
- [ ] Interfaces defined
- [ ] Assumptions documented
- [ ] Related specifications referenced

**Testing:**
- [ ] Test scenarios provided
- [ ] Success criteria defined
- [ ] Edge cases included in tests

---

**Incompleteness Example:**

**Incomplete:**
```markdown
## Update Process

The update process compares files and updates changed ones.
```

**Why Incomplete:**
- How are files compared?
- What about deleted files?
- What if update fails midway?
- What about user customizations?
- How are errors handled?

**Complete:**
```markdown
## Update Process

### Update Workflow

The system executes update operations in this specific order:

**Phase 1: Preparation**
1. Read Update manifest from source
2. Read Destination manifest from target
3. Categorize files (to delete, add, update, skip)
4. Validate update can proceed
[...]

**Phase 2: File Operations**
1. Delete obsolete files
2. Add new files
3. Update existing files (with tag preservation)
4. Skip protected files
[...]

**Error Handling:**
If ANY operation fails, system rolls back all changes and restores
previous state.

**Guarantee:** Update is atomic - either fully succeeds or fully fails.

[Continue with detailed specifications...]
```

---

### Principle 10: Maintenance Mindfulness

**The Problem:**
Specs that require constant maintenance become outdated and unreliable.

**The Principle:**
Write specifications that are **low-maintenance** while remaining accurate and useful.

**Low-Maintenance Patterns:**

**1. Avoid Timestamps in Content:**

**Bad:**
```markdown
## Recent Changes

As of 2025-11-13, we support 5 providers.
Last updated: 2025-11-13
```

**Why Bad:** Dates become outdated. "Recent" is relative.

**Good:**
```markdown
## Provider Support

The system supports multiple AI providers defined in `config/providers.json`.
Each provider implements the `ProviderInterface` defined in § Provider Interface.
```

**Why Good:** No dates to update. Describes mechanism, not current state.

---

**2. Reference External Tracking:**

**Bad:**
```markdown
## Open Issues

- Issue #47: Cache corruption bug
- Issue #52: Permission error on Windows
- Issue #61: Update rollback incomplete
```

**Why Bad:** Issue list changes constantly. Spec becomes outdated.

**Good:**
```markdown
## Known Issues

For current known issues and their status, see the project issue tracker at:
[link to issue tracker]

Critical issues affecting specification conformance are documented in
§ Edge Cases or § Error Handling as appropriate.
```

---

**3. Avoid Roadmap Content:**

**Bad:**
```markdown
## Future Plans

- Version 2.0 will add support for remote templates
- Version 2.1 will include automatic conflict resolution
- Version 3.0 will support template inheritance
```

**Why Bad:** Plans change. Version numbers shift. Creates maintenance burden.

**Good:**
```markdown
## Extension Points

The system is designed to support future enhancements:

- **Template Sources**: Current implementation uses local filesystem.
  Interface allows for future remote template sources.

- **Conflict Resolution**: Current implementation requires manual resolution.
  Pluggable resolution strategies supported via ConflictResolver interface.
```

**Why Good:** Describes extension mechanism, not specific future plans.

---

**4. Self-Updating References:**

**Instead of:**
```markdown
There are currently 15 agent definitions in .claude/agents/.
```

**Prefer:**
```markdown
Agent definitions are located in `.claude/agents/`. Each agent has its own
markdown file defining its role and responsibilities.
```

Or even better, if appropriate:
[Note: nested triple-backticks in example below are converted to tag to aid proper markdown rendering of larger, encapsulating file]
```markdown
Agent definitions are located in `.claude/agents/`. To see all available agents:

<triple-backticks> bash
ls .claude/agents/
</triple-backticks>
```

---

## Section-Specific Guidance

### Writing Overview Sections

**Purpose:** Provide immediate context - what is this feature, why it exists, how it fits in.

**Structure:**
1. **What statement** (1-2 sentences): Describe the feature
2. **Purpose statement** (1-2 sentences): What it provides/enables
3. **Scope statement** (1 sentence): What this spec covers
4. **Context reference** (1 sentence): Link to broader architecture

**Example:**
```markdown
## Overview

The WSD Update System enables existing WSD installations to receive new
versions of template files while preserving user customizations. It provides
a robust mechanism for comparing installed files against new template versions,
intelligently preserving content within WORKSCOPE-DEV tags, and maintaining
installation integrity.

This specification defines the complete update process including update detection,
file comparison algorithms, content preservation, and error handling.

For broader architectural context and how the Update System integrates with
other WSD components, see System-Architecture.md.
```

**Common Mistakes:**
- Too vague: "This document describes updates"
- Too detailed: Including technical details that belong in later sections
- Missing context: Not linking to broader architecture
- Missing scope: Not clarifying what this spec covers

---

### Writing Purpose Sections

**Purpose:** Declare ownership and establish specification authority.

**Critical Importance:** This is THE MOST IMPORTANT section for preventing duplication and enabling navigation.

**Structure:**
1. **Introductory statement**: "The [Feature] serves N critical functions:"
2. **Numbered functions** (3-5): Each with bold name and description
3. **Authority statement**: "This specification establishes..."

**Function Format:**
```markdown
**[Function Name]**: [What it does] and [why it matters/who benefits]
```

**Authority Statement Format:**
```markdown
This specification establishes the authoritative definition of [list the concepts/
mechanisms/aspects this spec OWNS], and [any additional scope].
```

**Good Example:**
```markdown
## Purpose

The Template System serves three critical functions:

1. **Distribution**: Provides a complete set of files that implement the
   workscope workflow system for new projects

2. **Customization**: Allows users to adapt WSD to their specific project
   needs through WORKSCOPE-DEV tags

3. **Preservation**: Maintains user customizations across WSD updates,
   preventing loss of project-specific content

This specification establishes the authoritative definition of template
structure, WORKSCOPE-DEV tag syntax, content preservation rules, .wsdkeep
placeholder files, file permission model, and the no_overwrite policy.
```

**Why Good:**
- Functions explain WHY feature exists (for users)
- Authority statement declares WHAT spec owns (for developers/AI agents)
- Clear boundaries prevent duplication

---

### Writing Algorithm Specifications

**Purpose:** Define computational procedures precisely enough for implementation.

**Standard Pattern:**
1. Overview
2. Algorithm Specification (pseudocode)
3. Rules
4. Special Cases
5. Examples

**Abstraction Level:**
- Specify logic flow and correctness constraints
- Don't specify variable names or exact data structures (unless critical)
- Focus on WHAT not HOW (let implementation choose HOW)

**Good Example:**
[Note: nested triple-backticks in example below are converted to tag to aid proper markdown rendering of larger, encapsulating file]
```markdown
## Collision Detection Algorithm

### Overview

The collision detection algorithm identifies files in the target directory
that would be overwritten by template files, enabling atomic installation
operations.

### Algorithm Specification

<triple-backticks> python
def detect_collisions(source_dir, target_dir):
    """
    Detect file collisions between source templates and target directory.

    Args:
        source_dir: Path to template root directory
        target_dir: Path to target installation directory

    Returns:
        list: Relative paths of files that would collide
    """

    # Step 1: Get list of all files to be installed
    source_files = get_all_files(source_dir)

    # Step 2: Initialize collision list
    collisions = []

    # Step 3: Check each source file against target
    for relative_path in source_files:
        target_path = join(target_dir, relative_path)

        if exists(target_path):
            collisions.append(relative_path)

    return collisions
</triple-backticks>

### Collision Detection Rules

1. **File-Level Only**: Only files checked, not directories
2. **Recursive Scan**: All subdirectories scanned
3. **Relative Paths**: Paths stored relative to project root
4. **.wsdkeep Exception**: .wsdkeep files never cause collisions

### Special Cases

#### .wsdkeep Files

**Behavior**: .wsdkeep files never trigger collision warnings
**Rationale**: Placeholder files that can be overwritten freely
[...]
```

---

### Writing Error Handling Sections

**Purpose:** Specify all failure modes and recovery procedures.

**Organization:** By error category (permission errors, filesystem errors, validation errors, etc.)

**For Each Error:**
1. **Description**: What causes this error
2. **Example Message**: What user sees
3. **Recovery**: How to resolve

**Good Example:**
[Note: nested triple-backticks in example below are converted to tag to aid proper markdown rendering of larger, encapsulating file]
```markdown
## Error Handling

### Error Categories

#### 1. Permission Errors

**Error**: Cannot create target directory

**Example Message:**
<triple-backticks>
Error: Permission denied creating directory '/path/to/target'

Check that you have write permissions to the parent directory.
</triple-backticks>

**Recovery**: User must adjust permissions or choose different target

#### 2. Collision Errors

**Error**: Files already exist in target

**Example Message:**
<triple-backticks>
Error: Installation aborted due to file collisions.

The following files already exist in the target directory:
  - README.md
  - scripts/health_check.py

Please resolve these conflicts before installing WSD.
</triple-backticks>

**Recovery**: User must rename/move/delete conflicting files
```

**Key Principles:**
- Cover ALL failure modes
- Provide example messages (don't mandate exact wording)
- Focus on user needs: what happened, why, how to fix
- Include recovery procedures

---

### Writing Testing Scenarios Sections

**Purpose:** Provide verification guidance for feature correctness.

**Organization:** By test category

**Minimum Categories:**
- Basic [Feature] Tests
- Edge Case Tests
- Integration Tests

**Optional Categories:**
- Performance Tests
- Security Tests
- Compatibility Tests
- Regression Tests

**Format for Each Test:**
```markdown
**Test Name**: [Brief description of test and expected outcome]
```

**Good Example:**
```markdown
## Testing Scenarios

### Basic Installation Tests

1. **Empty Directory Installation**: Install into completely empty directory,
   verify all files copied, manifest created, execute permissions set correctly

2. **New Directory Installation**: Install into non-existent directory (created
   during install), verify directory created and populated

3. **Git Repo Installation**: Install into directory with only .git/, verify
   WSD files added without affecting git directory

### Edge Case Tests

1. **.wsdkeep Non-Collision**: Target has existing .wsdkeep files, verify
   these don't trigger collision warnings

2. **Partial Installation Recovery**: Interrupt installation mid-process,
   verify no .wsd manifest created and partial files detected on retry

### Integration Tests

1. **Full Install-Update Cycle**: Fresh install, customize files, update to
   new version, verify customizations preserved
```

**Key Principles:**
- Descriptive test names
- Expected outcomes included
- Cover success and failure paths
- Include edge cases

---

## Common Pitfalls and How to Avoid Them

### Pitfall 1: Implementation Leakage

**Problem:** Spec includes implementation details that belong in code.

**Example:**
```markdown
The cache uses a HashMap<String, CacheEntry> with initial capacity of 16
and load factor 0.75. Entries are stored using FNV-1a hash function.
```

**Why Bad:** Over-constrains implementation. These details don't affect correctness.

**Fix:**
```markdown
The cache MUST provide O(1) average-case lookup performance for cache entries
indexed by string keys.
```

---

### Pitfall 2: Outdated Examples

**Problem:** Examples become outdated as system evolves.

**Example:**
```markdown
### Example

Run the command: `wsd-tool-v2 install --legacy-mode /path`
```

**Why Bad:** Command might change. Flag might be removed.

**Fix:**
[Note: nested triple-backticks in example below are converted to tag to aid proper markdown rendering of larger, encapsulating file]
```markdown
### Example

Install WSD into a project:

<triple-backticks> bash
wsd.py install /path/to/project
</triple-backticks>

For additional options, run: `wsd.py install --help`
```

---

### Pitfall 3: Circular References

**Problem:** Spec A references Spec B which references Spec A.

**Example:**
```markdown
<!-- In Template-System.md -->
For installation process, see Installation-System.md.

<!-- In Installation-System.md -->
For template structure, see Template-System.md.
```

**Why Bad:** Readers get stuck in loop. Unclear which spec owns what.

**Fix:** Establish clear ownership. One spec is authoritative, others reference it.

---

### Pitfall 4: Assuming Context

**Problem:** Spec assumes reader has specific knowledge not documented anywhere.

**Example:**
```markdown
Use the standard FNV algorithm for hashing.
```

**Why Bad:** Which variant? What if reader doesn't know FNV?

**Fix:**
```markdown
Use the FNV-1a hash algorithm (see: https://tools.ietf.org/html/draft-eastlake-fnv-17)
for computing file checksums.
```

---

## Verification

To verify your Feature Overview follows these meta best practices, use the comprehensive verification checklist in **Feature-Overview-Checklist.md § Meta Practices Checklist**.

The checklist covers all 10 principles outlined in this guide and provides quick reference for both structural requirements and meta best practices.

---

## Conclusion

These meta best practices apply across all sections of your Feature Overview. They ensure your specification is:

- **Authoritative**: Clear ownership, no duplication
- **Evergreen**: Accommodates evolution without constant updates
- **Precise**: Uses requirements language appropriately
- **Complete**: Covers normal operation, errors, and edge cases
- **Navigable**: AI agents and humans can find information efficiently
- **Maintainable**: Low-maintenance while remaining accurate

**Remember:** The template tells you WHAT sections to include. This guide tells you HOW to write them effectively.

**Next Steps:**
1. Use Feature-Overview-Template.md for structure
2. Apply these meta practices while writing content
3. Use Feature-Overview-Checklist.md to verify quality
4. Reference Feature-Overview-Template-Elements.md for detailed element specifications

---

*This guide establishes meta best practices for writing effective Feature Overview specifications. These principles apply orthogonally to document structure and ensure specifications are authoritative, evergreen, and navigable.*
