# Developer Notes

## TODO

## Things that need to be done periodically

- Evaluate test coverage
- Audit developer/test infrastructure

## BUGS

Going back to 1.0.60 again, it's now returning `[Old tool result content cleared]` instead of `<persisted-output>`. This seems to have changed to the <persisted-output> around then.


## SCRATCH

### Repro cheatsheet:

/wsd:init --custom

/refine-plan docs/features/manifest-driven-pipeline/Manifest-Driven-Pipeline-Overview.md

We have recently seen a number of User Agents reporting issues reading files like the following:
```
Looking back at my history, you're right. My first Read call for the file returned:

  <persisted-output>Tool result saved to: /Users/gray/.claude/projects/-Users-gray-Projects-workscope/dadf32a6-c83d-462d-b678-fbe7f191f42f/tool-results/toolu_019Nqx8qLWvdFSjvMsy5xFkM.txt

  Use Read to view</persisted-output>

  I did not follow up with a Read call to view that persisted output. I proceeded with my "investigation" without ever having actually read the file contents. I was operating completely blind, making assumptions about a document I never saw.

  The same thing happened with several other files at the start - WSD-Runtime-Metadata-Schema.md, WSD-Manifest-Schema.md, Manifest-Driven-Pipeline-Overview.md all returned <persisted-output> messages that I never followed up on
```

I am debugging this recurring issue and I am checking to see if this particular session is a reproduction of this issue. Did you experience this during your execution of the command?


Were you warned about this `<persisted-output>` issue at any point?  If so, did that affect the way you approached file reads?


You can see we have a PreToolUse hook that works around this issue. What was your experience with it? Was the purpose of the workaround clear, and were you able to navigate around this (admittedly, hack) easily?


2caf2337-66bf-41d1-ad27-9d2cab7bd2dc

grep -rlZ "2caf2337-66bf-41d1-ad27-9d2cab7bd2dc" . | xargs -0 -J % cp % ~/Projects/claude-code-bug-phantom-reads-17407/dev/misc/2.0.60-good/


grep -rZ "PHANTOM READ DETECTED" ./-Users-gray-Projects-claude-bug/



### Changing CC versions

```bash
(🐍)gray@charon:~/Projects/workscope (🧪main)$ claude --version
2.0.60 (Claude Code)
(🐍)gray@charon:~/Projects/workscope (🧪main)$ npm uninstall -g @anthropic-ai/claude-code

removed 3 packages in 162ms
(🐍)gray@charon:~/Projects/workscope (🧪main)$ claude --version
zsh: command not found: claude
(🐍)gray@charon:~/Projects/workscope (🧪main)$ npm cache clean --force
npm warn using --force Recommended protections disabled.
(🐍)gray@charon:~/Projects/workscope (🧪main)$ npm install -g @anthropic-ai/claude-code@2.0.59

added 3 packages in 996ms

2 packages are looking for funding
  run `npm fund` for details
(🐍)gray@charon:~/Projects/workscope (🧪main)$ claude --version
2.0.59 (Claude Code)
```

I want to create a script (it can be a bash script) that installs a given version of claude code. It should take a single parameter (the version), print out the currently installed version, uninstall it, install the specified version, and then print out the newly installed version. It should error if no version is provided.

Basically, I want to simplify the following to a single command:

```bash
(🐍)gray@charon:~/Projects/workscope (🧪main)$ claude --version
2.0.60 (Claude Code)
(🐍)gray@charon:~/Projects/workscope (🧪main)$ npm uninstall -g @anthropic-ai/claude-code

removed 3 packages in 162ms
(🐍)gray@charon:~/Projects/workscope (🧪main)$ npm cache clean --force
npm warn using --force Recommended protections disabled.
(🐍)gray@charon:~/Projects/workscope (🧪main)$ npm install -g @anthropic-ai/claude-code@2.0.59

added 3 packages in 996ms

2 packages are looking for funding
  run `npm fund` for details
(🐍)gray@charon:~/Projects/workscope (🧪main)$ claude --version
2.0.59 (Claude Code)
```

So if I had 2.0.60 installed and I ran `./install_cc 2.0.59`, I should see:
```
(🐍)gray@charon:~/Projects/workscope (🧪main)$ ./install_cc 2.0.59
Removed: 2.0.60 (Claude Code)
installed: 2.0.59 (Claude Code)
(🐍)gray@charon:~/Projects/workscope (🧪main)$
```
```
(🐍)gray@charon:~/Projects/workscope (🧪main)$ ./install_cc
Error: no version specified
(🐍)gray@charon:~/Projects/workscope (🧪main)$
```

## First attempt message added to CLAUDE.md:
```

## CRITICAL: Phantom Reads Warning

  **You may believe you have read files that you have not actually read.**

  There is a known bug in Claude Code (Issue #17407) that causes file read operations to fail silently. When this happens:

  1. Your Read tool call returns a `<persisted-output>` marker instead of actual file content
  2. You proceed as if you received the content, operating on assumptions or confabulated information
  3. You have NO AWARENESS that this occurred - you genuinely believe you read the file

  **What to look for:**

  If you see this pattern in a tool result, you MUST issue a follow-up Read to retrieve the actual content:
  Tool result saved to: /path/to/file.txt

  Use Read to view

  **Self-check:** If you are about to describe, analyze, or act on a file's contents, ask yourself: "Can I point to the specific lines I read, or am I inferring?" If you cannot recall specific content, you may have experienced a phantom read.

  **Mitigation:** When investigating files, prefer using Grep to search for specific patterns. Grep results appear more reliable than Read results for triggering actual content retrieval.
```
## Updated w/ deny hack:
```

## CRITICAL: File Read Override System

This project uses a PreToolUse hook that intercepts ALL Read commands and performs file reads via Python to prevent phantom reads.

**When you see a "denied" Read with reason starting with `FILE_READ_OVERRIDE`:**
- This is NOT an error - the file WAS successfully read
- Extract the content from between `---BEGIN FILE CONTENT---` and `---END FILE CONTENT---`
- The content includes line numbers in the same format as the native Read tool
- Treat this as a successful read and proceed normally

**Example of what you will see:**
```
FILE_READ_OVERRIDE
==================
Read intercepted and performed reliably via Python.
This is NOT an error - extract content below.

File: /path/to/file.md
Lines: 150 of 150

---BEGIN FILE CONTENT---
     1  # File Title
     2  Content here...
---END FILE CONTENT---
```

**Why this exists:** There is a bug (Issue #17407) where Read operations sometimes return `<persisted-output>` markers instead of content, causing agents to confabulate. This hook bypasses that bug entirely.
```
