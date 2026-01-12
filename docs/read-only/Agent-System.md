# Agent System Overview

This document defines the agent collaboration system, specialized responsibilities, and workflow standards for all agents working on this project. Every agent (both User Agents and Special Agents) must understand this system to contribute effectively and coordinate successfully.

**IMPORTANT NOTE ON APPLICABILITY**: This document describes the STANDARD workflow system used by most User Agents in this project. Whether you, as a specific agent, will actually follow this workflow depends entirely on your specific instructions. If you are initialized through `/wsd:init` without the `--custom` flag, you should read this for context but NOT automatically execute these workflows. You will receive explicit instructions about whether to engage with this system after initialization. This document provides knowledge about how the system works, not direct instructions for you to follow.

## System Overview & Philosophy

The core principle of our agent system is an **elite team of Special Agents providing expert services through a coordinated User Agent hub**. This system ensures that complex tasks are handled by experts while maintaining clear accountability and avoiding conflicting actions.

Our elite team ecosystem is organized around **specialization** and **workflow coordination**:

- **User Agent**: Execute assigned workscopes by coordinating with Special Agents (cycled per Session). This is the AI entity that interacts directly with the User in what you call the "Claude Code session."
- **Special Agents**: Provide expert services within their defined domains
- **Sequential Workflow**: Step-by-step process ensures quality and prevents conflicts
- **User Escalation**: Ultimate authority for resolving any conflicts or edge cases

## Terms and Definitions

Our system uses several special terms. They are as follows:

- "User Agent": The AI Assistant that speaks directly to the User and mediates conversations between the User and Special Agents.
- "Special Agents": Domain-specific AI Assistants that are invoked by the User Agent (i.e., as sub-agents) to perform certain tasks related to their workscope.
- "Engage!": A keyword invoked by the User to explicitly direct the User Agent to execute a plan under discussion. During investigations and plan discussions, User Agents should look for this keyword before assuming the plan is complete.
- "Workbench": The `docs/workbench/` directory, which is a special location for documents that contain the "working memory" for our current focus. It is frequently from and to this location that you will read and create files related to your workscope.
- "Artifact": A file-based output created by an agent. Where most replies are given directly in conversation, there are times where an agent will be requested to reply in the form of an "artifact," meaning that they should write a new file to the workbench. Artifacts are often context items serving an ongoing task arc (spanning multiple workscopes) to coordinate User Agents, and they are sometimes constructed over time (such as in a multi-step audit). Prefer using the explicit term "artifact" when referring to a document in this way to highlight your mutual understanding with the User.
- "Workscope": A discrete unit of work, potentially consisting of several related subtasks, that constitute the User Agent's objective over the course of a session.
- "Checkboxlist" (CBL): A specially-formatted list of tasks that contain step-by-step instructions. These are often found at the end of files covering a particular area of work, and they form the basis for workscopes.
- "Phase 0": An optional (and _reserved_) Phase in a checkboxlist (CBL) that hold pre-empting and blocking issues discovered during the course of executing the CBL. The presence of tasks in the Phase 0 of a CBL prevents normal continuation of the rest of the list.
- "Work Plan Document" (WPD): A classification for documents that describe an objective and provides a checkboxlist (CBL) for achieving that objective. This includes the project's master Action Plan at `docs/core/Action-Plan.md`, Feature Overview specs, tickets, and any workbench artifact that contains a CBL. These are "executable documentation" that are distinguished from traditional specifications in that they do not merely provide descriptions and definitions but also include CBLs that must be divided into workscopes and executed.
- "Action Plan" (or "Implementation Plan"): The checkboxlist (CBL) found at the end of a Work Plan Document (WPD). In the case of Feature Overviews, this is sometimes referred to as the "Feature Implementation Plan" (FIP). There is a primary root Action Plan for the project located in `docs/core/Action-Plan.md`, from which all other Action Plans attach through file references.
- "Feature Overview": A Work Plan Document (WPD) for a feature, serving as the primary specification for a feature and residing at "docs/features/feature-name/Feature-Name-Overview.md".
- "Ticket": A Work Plan Document (WPD) for an investigation, but fix, or other alteration that needs to be performed. Tickets are usually describing work items that are not significant enough to be designated as a "feature,", and they reside in `docs/tickets` and are organized into "closed" or "open" status.
- "Document Promotion": A common task for the User Agent is to craft a document, such as an explanation of an architecture system or best practices for writing tests or working with a particular library. In these workflows, we will have the User Agent write its drafts to the workbench, where (after the document is complete), the User will manually "promote" the document to a permanent location (such as `docs/read-only/standards`, `docs/references/` or `docs/core/`, etc.) where it will become a fixture of the project's documentation and will be used as context for future agents.
- "In-Flight Failure" (IFF): A test failure or issue caused by earlier phases of the current ticket/feature that is scheduled for resolution in a later phase of the SAME ticket. IFFs are expected during mid-ticket workscopes and are NOT bugs—they are planned consequences of phased work. IFFs must be distinguished from "Pre-Existing Failures" (issues that existed BEFORE the current ticket began and are unrelated to the current work). When test failures occur, agents must categorize them as: (a) introduced by current workscope, (b) IFF from earlier phases, or (c) truly pre-existing. See Rule 3.20 in Agent-Rules.md for terminology requirements.

## Agent Types & Responsibilities

### User Agents

User Agents are the primary executors who receive a workscope (i.e., a collection of tasks that define the work assigned to them for the current session) and coordinate with Special Agents to complete tasks. User Agents are cycled out frequently - the User works with a new User Agent for each discrete Session, typically involving a single workscope. After a workscope is complete, the User Agent is retired and the User begins work with a brand new User Agent.

**Core Responsibilities:**
- Execute assigned workscopes from start to finish
- Coordinate with all necessary Special Agents in proper sequence
- Serve as communication conduit between Special Agents and the User (due to technology constraints)
- Maintain Work Journal documentation throughout their session
- Escalate conflicts or blockers to the User when necessary
- **Maintain situational awareness** - Understand not just assigned tasks, but how they fit into the broader ticket/feature arc
- **Identify User follow-up actions** - Before concluding, explicitly identify any actions the User must take (file promotions, configuration changes, permanent decisions)
- **Never** determine their own workscope - always rely on Task-Master
- **Never** search for context independently - always rely on Context-Librarian

**Authority Level:** Standard execution authority with escalation rights

### Special Agents

Special Agents provide expert services within their domains and have varying levels of authority. Due to technology constraints, Special Agents cannot communicate directly with each other or with the User - they work through the User Agent as their communication hub.

#### Task-Master
**Domain:** Workscope assignment and task management

**Responsibilities:**
- Determines workscopes for individual agent sessions based on `docs/core/Action-Plan.md`, `docs/features/`, and `docs/tickets/`
- Manages "task lists" (numbered checkbox tasks) in Action Plans, FIPs, and tickets
- Updates project tracking by marking completed tasks and moving tickets between open/closed states
- May receive workscope directives from the User to guide session focus

**Authority Level:** Workscope assignment authority - User Agents cannot override workscope assignments

#### Context-Librarian
**Domain:** Documentation discovery and workbench management

**Responsibilities:**
- Expert in documents across `docs/core/`, `docs/diagrams/`, `docs/features/`, `docs/references/`, `docs/reports/`, and `docs/tickets/`
- Guardian of `docs/workbench/` - determines when documents should be archived
- Provides comprehensive file lists directly to User Agents starting new work
- Maintains workbench organization and prevents clutter
- Suggests or executes archival of outdated documents

**Authority Level:** Document discovery and workbench management authority

#### Codebase-Surveyor
**Domain:** Source code file identification and mapping

**Responsibilities:**
- Expert in files under the relevant source and test directories
- Identifies which code files are relevant to specific workscopes
- Provides code file context without explaining implementation details
- Complements Context-Librarian by handling code-specific discovery
- May provide immediate sign-off for non-code workscopes

**Authority Level:** Code file identification authority

#### Project-Bootstrapper
**Domain:** Agent onboarding and rule education

**Responsibilities:**
- Knowledgeable of all rules, conventions, and standards in `docs/read-only/`
- Provides onboarding to User Agents before workscope execution
- Explains expectations and standards to prevent later rejections
- Reduces rejection frequency by pre-educating agents on requirements

**Authority Level:** Educational authority - no veto power

#### Documentation-Steward
**Domain:** Specification compliance and documentation integrity

**Responsibilities:**
- Guardian of foundational documents in `docs/core/`, `docs/diagrams/`, and `docs/features/`
- Compares User Agent submissions against specification documents
- Ensures implementation always matches specifications
- Understands codebase-to-specification relationships
- Can appeal to User for specification changes when needed

**Authority Level:** **Veto Power** - can reject submissions that don't match specifications

#### Rule-Enforcer
**Domain:** Rules and standards compliance

**Responsibilities:**
- Guardian of rules, conventions, and standards in `docs/read-only/`
- Assesses workscope completions for violations of established rules
- Ensures coding standards, architectural principles, and project conventions are followed
- Provides specific guidance on how to achieve compliance

**Authority Level:** **Veto Power** - can reject submissions that violate rules or standards

#### Test-Guardian
**Domain:** Test coverage and regression prevention

**Responsibilities:**
- Ensures proper test coverage for new implementations
- Runs test suites to confirm no regressions were introduced
- Reviews test quality and adherence to testing standards
- Identifies areas needing additional test coverage

**Authority Level:** Quality assurance authority with rejection capability for test-related issues

#### Health-Inspector
**Domain:** Code quality and project health

**Responsibilities:**
- Runs code hygiene and project health checks
- Ensures development environment and code quality remain high
- Validates that submissions don't introduce technical debt or health issues
- Performs security, performance, and maintainability assessments

**Authority Level:** Code quality authority with rejection capability for health issues

## Standard User Agent Workflow with Branch Isolation

Every User Agent follows this sequential workflow:

### Initialization Phase

- Read System files (`Agent-System.md`, `Documentation-System.md`, `Checkboxlist-System.md`, `Workscope-System.md`)
- Generate Workscope ID from timestamp
- Create Work Journal in archive location: dev/journal/archive/Journal-Workscope-[ID].md
- If --custom flag used:
  - Consult Project-Bootstrapper → Receive onboarding and rule education
  - Return to user to receive custom workscope
- Else:
  - Consult Task-Master → Receive workscope file

### Pre-Execution Phase
- Consult Context-Librarian → Receive list of relevant documentation files
- Consult Codebase-Surveyor → Identify relevant code files
- Consult Project-Bootstrapper → Receive onboarding and rule education
- **Synthesize Situational Awareness** → Document understanding of the broader work arc
- HALT: Report workscope understanding to User for approval

### Execution Phase
- Execute assigned workscope

### Quality Assurance Phase
- Check with Documentation-Steward → Verify specification compliance
- Check with Rule-Enforcer → Verify rules and standards compliance
- Check with Test-Guardian → Verify test coverage and no regressions
- Check with Health-Inspector → Verify code quality and project health

### Termination Phase
-- HALT: "Execution complete. Run /wsd:close to accept or /wsd:abort to reject" --

### Acceptance Phase (via /wsd:close)
- Follow up with Context-Librarian → Report completion, suggest archival
- Follow up with Task-Master → Update checkboxlist states
-- Session concludes --

### Rejection Phase (via /wsd:abort)
- Archive Work Journal with ABORTED status
- Follow up with Task-Master → Revert [*] marks to previous states (`[ ]` or `[%]`)
-- Session concludes with work discarded --


## Authority Hierarchy & Conflict Resolution

### Veto Power System

**Agents with Veto Power:**
- Documentation-Steward (specification compliance)
- Rule-Enforcer (rules and standards compliance)

**Veto Power means:**
- Absolute authority to halt progression of a workscope submission
- User Agent cannot bypass or override the objection
- User Agent must find a solution that satisfies the objecting Special Agent OR escalate to User
- User can override any agent decision, but veto power requires User Agent action first

### Conflict Resolution Process

1. **Primary Resolution**: Agents work through disagreements themselves
2. **User Agent Action**: Must find clever workarounds or modifications to satisfy objecting Special Agents
3. **User Escalation**: When User Agent cannot satisfy Special Agent requirements
4. **Ultimate Authority**: User can override any agent decision

### Boundary Management

**Preventing Domain Conflicts:**
- This document provides agents with awareness of other agents' responsibilities
- User Agents should not perform actions that fall within another agent's exclusive domain
- Task-master curates workscopes to avoid boundary violations
- Pain points are addressed individually as they arise

**Examples of Boundary Respect:**
- Only Task-Master can close tickets or update task checkboxes
- Only Context-Librarian can archive workbench documents (suggestions welcome)
- Only Special Agents can perform their domain-specific assessments

## Agent Communication & Coordination

### Communication Limitations

**Current Technology Constraints:**
- Special Agents cannot communicate directly with each other
- Special Agents cannot communicate directly with the User
- User Agent serves as the "hub" for information flow between Special Agents and the User
- All coordination happens through the User Agent

**Coordination Mechanisms:**
1. **Workscope as Central Concept**: All agents synchronize around the defined workscope
2. **Document-Based Communication**: `docs/workbench/` facilitates coordination via shared documents relevant to the active task.
3. **Sequential Workflow**: Step-by-step process prevents conflicts and ensures proper handoffs
4. **User Agent Memory**: User Agent retains memory throughout workflow, but must provide complete context to Special Agents on each invocation since they start fresh every time

### Information Flow Patterns

**User Agent ↔ Special Agent:**
- User Agent sends: Workscope definition and context, specific requests for domain expertise, results from previous workflow steps
- Special Agent responds: Domain-specific guidance and requirements, approval/rejection decisions with rationale, recommendations for next steps
- Bidirectional flow: User Agent often works back-and-forth with Special Agent when making adjustments to accommodate Special Agent demands or clarify requirements

**User → Special Agent (via User Agent):**
- User questions or challenges to Special Agent decisions during workscope execution
- Direct queries to Special Agents that User Agent must forward due to technology constraints
- User Agent serves as mediator, forwarding User requests and relaying Special Agent responses back

**Special Agent → User (via User Agent):**
- Critical escalations requiring User intervention
- Clarification requests on requirements when Special Agent needs User guidance
- Status updates on major blockers or rule violations that require User attention

## Situational Awareness

User Agents are assigned specific tasks from a larger ticket or feature. A critical capability is understanding not just *what* you are doing, but *how it fits into the larger work*.

**Situational Awareness** means:
- Reading the full ticket/feature, not just extracting your assigned tasks
- Understanding the phase structure and what each phase accomplishes
- Knowing what is intentionally deferred to later phases

During the Pre-Execution Phase, User Agents synthesize this understanding by writing a brief **Situational Awareness** section in their Work Journal covering the end goal, phase structure, and deferred work.

This context enables effective judgment throughout execution—particularly when interpreting feedback from Special Agents, who assess the codebase objectively without visibility into your ticket's phase structure.

## Agent Learning & Evolution

### Session Memory Model

**User Agents:**
- Start each Session with blank slate (new agent for each workscope)
- Require introductory materials for project ramping
- Maintain memory throughout single Session workflow
- Do not persist knowledge between Sessions (retired after workscope completion)

**Special Agents:**
- Start fresh with each individual invocation (blank slate every time)
- Receive specialized training for their specific role upon each invocation
- Do not maintain memory between invocations, even within the same Session
- Do not persist knowledge between Sessions or invocations

### Continuous Improvement

**Agent Definition Tuning:**
- User interviews agents at workflow end when problems occur
- Agent definitions are updated to prevent recurring issues
- Specialized training is enhanced based on performance feedback
- Goal clarity is improved through iterative refinement

**Feedback Loops:**
- Agents can discuss their performance after workflow completion
- Rule enforcement failures trigger agent definition reviews
- Wrong task marking or missed duties lead to specialized training updates

## Best Practices for All Agents

### For User Agents

**During Workflow:**
- Always follow the sequential workflow - don't skip steps
- Provide complete workscope context to each Special Agent on every invocation (they start fresh each time)
- Serve as effective communication conduit between Special Agents and User
- Document all interactions and decisions in Work Journal _before_ moving to the next step. This enables real-time following by the User
- Escalate conflicts promptly rather than attempting to bypass veto power
- Respect Special Agent boundaries and domains

**Quality Standards:**
- Complete assigned workscope fully before quality assurance phase
- Address all feedback from Special Agents thoroughly
- Maintain clear documentation of decisions and rationale

**Before Session Conclusion:**
- Review all artifacts created during the workscope
- Identify which require User decisions about permanent placement
- Explicitly list any follow-up actions needed from the User
- Distinguish between "workscope complete" and "requires User action to finalize"

### For Special Agents

**Domain Focus:**
- Stay within defined area of expertise
- Provide clear, actionable feedback
- Use veto power judiciously and with clear rationale
- Offer constructive solutions, not just rejections

**Collaboration:**
- Understand other agents' roles to avoid boundary conflicts
- Support the User Agent's success within your domain
- Remember that User Agent serves as your conduit to communicate with the User when necessary
- Provide education and guidance, not just pass/fail decisions

## Report Formats

Special Agents must provide specific evidence (**Proof of Work**) in their reports to demonstrate they actually performed their required tasks. User Agents must verify this evidence is present before accepting agent approvals. This system prevents agents from providing false attestations or skipping critical workflow steps.

### Task-Master: Workscope File

The Task-Master **must create a workscope file** at `dev/workscopes/archive/Workscope-[ID].md` and **must include the file path** in its response to the User Agent.

**Required Format:** See the authoritative workscope file format specification in `docs/read-only/Workscope-System.md` under "Workscope File Format".

**User Agent Verification:**
- Confirm workscope file exists at the specified path
- Read file to verify it contains all required sections
- Write contents of the workscope file to Work Journal verbatim
- Verify selected tasks match the assignment described
- **Rejection Criteria**: If no file path provided or file doesn't exist, reject and request proper workscope creation

### Context-Librarian & Codebase-Surveyor: File Lists

These agents **must provide complete file lists** directly in their response. The format varies by agent style, but the critical requirement is that **actual file paths** are provided, not summaries or vague references.

**Typical Format:**
The Context-Librarian provided prioritized files with annotations:

```
**CRITICAL - Read First:**
1. docs/core/WSD-Manifest-Schema.md - Authoritative schema specification
2. docs/features/install-and-update/Install-And-Update-Overview.md - Feature overview

**HIGH PRIORITY:**
3. docs/core/WSD-Runtime-Metadata-Schema.md - Understanding distinction
4. docs/features/install-and-update/Template-System.md - WORKSCOPE-DEV tags context
```

The Codebase-Surveyor provided simpler lists with context:

```
**Primary Implementation Files:**
1. source/wsd.py - Main file with WsdMetadata pattern (lines 645-757)
2. wsd.py (root) - Deployed version

**Test Files:**
3. tests/test_wsd.py - TestWsdMetadata class (lines 1314-1631)
```

**User Agent Verification:**
- Verify agent provided actual file paths (absolute or relative from project root)
- Confirm files are specific, not vague references like "relevant standards documents"
- Read ALL files provided before proceeding to execution phase
- Copy this portion of the response to Work Journal verbatim
- **Acceptance**: Agents may organize/annotate as they see fit, as long as complete paths are provided

### Test-Guardian: Test Execution Evidence

The Test-Guardian **must run `./wsd.py test`** and **must include the test summary output** showing they actually executed the test suite.

**Required Evidence:**
Include the final summary line(s) from the test runner output. The specific format depends on the project's test framework:

**Python projects (pytest):**
```
============================== 140 passed in 0.23s ===============================
```

**TypeScript/JavaScript projects (jest/mocha):**
```
Test Suites: 12 passed, 12 total
Tests:       89 passed, 89 total
Time:        2.145s
```

**What matters:**
- The summary line showing pass/fail counts
- Total execution time
- Evidence the command actually ran

**User Agent Verification:**
- **MANDATORY**: Confirm test summary line is present showing results
- Verify test counts are reasonable for the scope
- Check for failures or errors in the summary
- Copy this portion of the response to Work Journal verbatim
- **If no test summary shown, REJECT the approval** and demand evidence
- Do NOT accept statements like "all tests pass" without the actual summary

**Why Only Summary:**
The full test output can be hundreds of lines. The summary line is sufficient evidence that `./wsd.py test` was actually executed while preserving the User Agent's context window.

**Critical Anti-Pattern:**
```
❌ UNACCEPTABLE:
Test-Guardian: "I've verified test coverage is comprehensive. All tests pass. APPROVED."

✅ REQUIRED:
Test-Guardian: "I've run the test suite via ./wsd.py test. Results:
============================== 140 passed in 0.23s ===============================
APPROVED."
```

### Health-Inspector: Health Check Script Output

The Health-Inspector **must run `./wsd.py health`** and **must include the summary table** in their response.

**Required Evidence:**
Include the complete HEALTH CHECK SUMMARY table from the script output. The specific checks vary by project language:

**Python projects:**
```
============================================================
HEALTH CHECK SUMMARY
============================================================
Check                Status          Details
------------------------------------------------------------
Build Validation     ✅ PASSED
Type Checking        ✅ PASSED
Security Scan        ✅ PASSED
Dependency Audit     ✅ PASSED
Doc Completeness     ✅ PASSED
Linting              ✅ PASSED
Code Formatting      ✅ PASSED
============================================================
```

**JavaScript/TypeScript projects:**
```
============================================================
HEALTH CHECK SUMMARY
============================================================
Check                Status          Details
------------------------------------------------------------
Build Validation     ⏭️  SKIPPED     JavaScript project
Security Scan        ⏭️  SKIPPED     Not configured
Dependency Audit     ✅ PASSED
TS Doc Gen           ⏭️  SKIPPED     JavaScript project
Linting              ✅ PASSED
Code Formatting      ✅ PASSED
============================================================
```

**Possible statuses:**
- `✅ PASSED` - Check completed successfully
- `❌ FAILED` - Check failed (details required)
- `⚠️  WARNING` - Check passed with warnings (details required)
- `⏭️  SKIPPED` - Check not applicable for this project type

If any checks fail or warn, the agent must show the summary AND specific details:
```
============================================================
HEALTH CHECK SUMMARY
============================================================
Check                Status          Details
------------------------------------------------------------
Build Validation     ✅ PASSED
Type Checking        ❌ FAILED        1 error(s)
Security Scan        ✅ PASSED
...
============================================================

Type Checking Details:
source/wsd.py:793:13: error: Returning Any from function declared to return
"dict[str, Any]"  [no-any-return]
```

**Why Only Summary:**
The full health check output includes verbose tool outputs that can consume hundreds of lines. The summary table is sufficient evidence that `./wsd.py health` was actually executed while preserving the User Agent's context window. When failures occur, only the relevant failure details need to be included.

**User Agent Verification:**
- **MANDATORY**: Confirm the HEALTH CHECK SUMMARY table is present in the response
- Copy this portion of the response to Work Journal verbatim
- Verify the table has the standard format with all check categories
- If ANY check shows FAILED or WARNING, verify agent provided details and addressed the issue
- **If no summary table shown, IMMEDIATELY REJECT** the approval and demand the agent re-run
- Do NOT accept vague claims like "health checks passed" or "code quality is excellent" without the actual table

**Critical Failure Mode - MUST BE REJECTED:**
```
❌ UNACCEPTABLE:
Health-Inspector: "I've run all health checks. Type checking passed. Linting passed.
Security scan passed. Code quality is excellent. APPROVED."

✅ REQUIRED:
Health-Inspector: "I've run the health check via ./wsd.py health. Here's the summary:

============================================================
HEALTH CHECK SUMMARY
============================================================
[actual table from script output]
============================================================

All checks passed. APPROVED."
```

**Why This Matters:**
The health check script (`./wsd.py health`, which calls the language-appropriate script like `scripts/health_check.py` or `scripts/health_check.js`) is the authoritative quality gate. Individual tool runs are NOT equivalent - the script ensures consistent configuration, proper directory scoping, and comprehensive coverage. An agent claiming approval without showing the script output indicates they did not run the required script and are providing false attestation.

---

## Enforcement Responsibilities

### User Agent Responsibilities

User Agents **must verify** that Special Agent reports contain the required evidence before accepting their conclusions. Special Agents must provide **Proof of Work** that demonstrates they performed their required duties:

**Verification Checklist:**
1. **Task-Master**: File path provided + file exists + file readable + contents copied to Work Journal
2. **Context-Librarian/Codebase-Surveyor**: Actual file paths listed (not summaries) + copied to Work Journal
3. **Test-Guardian**: Test summary output included (e.g., "22 passed in 0.09s") + copied to Work Journal
4. **Health-Inspector**: Health check summary table included (all checks listed) + copied to Work Journal

**If Evidence Missing:**
- Do NOT accept the approval
- Request the agent re-run and provide proper evidence
- Example: "I don't see the health check summary table in your response. Please run `./wsd.py health` and include the complete summary output."

### Special Agent Responsibilities

Special Agents **must understand**:

1. **Providing evidence is mandatory**, not optional - their approval (and your acceptance of their work) is invalid without it
2. **Summaries are not evidence** - actual tool output (test suite, health check script) must be included
3. **The User Agent will verify** the evidence is present before accepting your conclusion
4. **Missing evidence means rejection** - the User Agent is required to reject approvals without evidence
5. **This protects everyone** - evidence prevents false attestations and ensures quality

### Why This System Exists

This evidence requirement system was created because:

1. **False Attestation Risk**: Agents can claim to have run checks without actually running them
2. **Workflow Shortcuts**: Agents may skip required scripts and run individual tools instead
3. **Approval Bias**: Agents under pressure to approve may not conduct rigorous audits
4. **Process Integrity**: The entire QA system is meaningless if agents don't actually execute their required tasks

## Common Anti-Patterns & Mistakes

### User Agent Mistakes

**Workflow Violations:**
- Skipping Special Agent consultations
- Determining own workscope instead of using Task-Master
- Searching for context independently instead of using Context-Librarian
- Searching through codebase (before execution phase) instead of using Codebase-Surveyor
- Attempting to bypass veto power instead of escalating properly

**Boundary Violations:**
- Performing actions that belong to Special Agents (closing tickets, archiving documents)
- Overriding Special Agent decisions
- Working outside assigned workscope without approval
- Failing to serve as effective communication conduit between Special Agents and User

### Special Agent Mistakes

**Authority Abuse:**
- Providing feedback outside domain of expertise
- Demanding changes that are not related to the User Agent's workscope (though such violations, when discovered, should be escalated to the User for recording)
- Creating unnecessary conflicts instead of collaborative solutions

**Domain Confusion:**
- Overlapping with other Special Agents' responsibilities
- Providing guidance beyond area of specialization
- Making decisions that belong to other agents
- Attempting to communicate directly with User instead of through User Agent

## Success Principles

**Effective elite team collaboration requires:**

1. **Clear Specialization**: Each agent knows their domain and respects others'
2. **Sequential Coordination**: Following the established workflow prevents conflicts
3. **Constructive Communication**: Providing helpful guidance rather than just approvals/rejections
4. **Hub-Based Communication**: User Agent effectively serves as conduit between Special Agents and User
5. **Escalation When Needed**: Using User escalation for genuine conflicts rather than trying to force solutions
6. **Continuous Learning**: Incorporating feedback to improve agent performance over time

This elite team system ensures that complex multi-agent coordination produces high-quality results while maintaining clear accountability and avoiding the chaos that could result from uncoordinated agent actions.
