---
description: Generate a git commit message for recent work
argument-hint: [regarding]
---

# Generate Commit Message

This command generates an appropriate, concise git commit message for the work recently completed. It does not perform any git commit, it merely generates an effective message for the current work if it were to be committed.

**Regarding:** $ARGUMENTS

## Current Repository State

**Staged changes:**
!`git diff --cached --stat 2>/dev/null || echo "No staged changes"`

**Unstaged changes:**
!`git diff --stat 2>/dev/null || echo "No unstaged changes"`

**Recent commits:**
!`git log --oneline -5 2>/dev/null || echo "No commits yet"`

## Usage

```
/commit-msg [regarding]
```

Where:
- `[regarding]` is optional User-provided guidance to help shape the commit message result

## Examples

```
/commit-msg
```

```
/commit-msg for the work performed in this ticket
```

```
/commit-msg regarding just Phases 2 - 4
```

## Description

This command generates a useful, comprehensive (but concise) message that would effectively serve as the git commit message, if the current repository were to be committed right now.

The message is not limited to just the most recent workscope. Git commits are often made by the User following a cohesive unit of work, such as the completion of a phase (which may take place over several workscopes) or even the fulfillment of a ticket, creation of a feature, refactor, or other cohesive unit of work.

Because this project may represent development efforts on multiple fronts (i.e., not just the project code, but also documentation) and may even include changes to tools independent of the project (such as agent or command definitions, development scripts, etc.), it is important to understand the true core and focus of the recent work. A message regarding the current ticket or phases in that ticket will almost always be more appropriate than referencing an agent definition file that received a clarifying instruction. The exception would be when such an unrelated change was the _only_ pending change in the repository.

The `[regarding]` argument may contain guidance from the User that clarifies the aspect of the recent work that should be emphasized in the commit message. For example, the codebase may be undergoing a large refactor, but the `[regarding]` message may specify "just the test updates" because the next git commit is intending to just commit the changes to the test code first.

The agent is encouraged to look at the current ticket, recent workscopes, and may use read-only git commands per **Rule 2.2** to investigate staged changes to gain more insight into what is expected to be committed. See Agent-Rules.md for the complete permitted whitelist and Design-Decisions.md for project-specific design philosophies that may inform commit message content.

**FORBIDDEN (commonly violated):** `git stash`, `git add`, `git commit`, `git checkout`, `git reset`, `git push`, `git pull`, `git fetch`.

**If you believe you need to modify repository state** (e.g., "I need to stage these files"), this indicates you are misunderstanding your role - escalate to the User. This command only GENERATES a commit message; it does NOT perform any git operations.

## Implementation

The command should:

1. Parse the `[regarding]` argument to understand what aspect of the recent work should be emphasized in the message. If this is omitted, you are directed to use your best judgement.
2. Consider the recent conversation, recent ticket, feature, or other area of focus that regard the most recent changes to the project
3. Review recent workscopes and Work Journals to understand what this change entails.
4. Use git tools to understand the file changes about to be committed
5. Craft a message appropriate to use in a git commit command for these changes.
