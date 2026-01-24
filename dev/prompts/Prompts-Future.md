
## Immediate

## Future

---

Actually, let's take a brief aside and dig into the "25k discrepancy" a little bit more. Given the simplicity of these scenarios, it's shocking to think that 120kb (~25k tokens) of data is being used for "Messages" that is unaccounted for.

Here is the final (post-operation) call to `/context` for the Hard scenario:

Baseline (fresh session):
```
/context
  ⎿   Context Usage
     ⛁ ⛀ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁   claude-opus-4-5-20251101 · 23k/200k tokens (12%)
     ⛁ ⛀ ⛀ ⛀ ⛀ ⛀ ⛶ ⛶ ⛶ ⛶   ⛁ System prompt: 3.0k tokens (1.5%)
     ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶   ⛁ System tools: 17.8k tokens (8.9%)
     ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶   ⛁ MCP tools: 293 tokens (0.1%)
     ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶   ⛁ Custom agents: 883 tokens (0.4%)
     ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶   ⛁ Memory files: 1.1k tokens (0.5%)
     ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶   ⛁ Skills: 309 tokens (0.2%)
     ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶   ⛁ Messages: 8 tokens (0.0%)
     ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶   ⛁ Compact buffer: 3.0k tokens (1.5%)
     ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛁ ⛀   ⛶ Free space: 174k (86.8%)
```
After `/setup-hard` loads 68112 tokens:
```
/context
  ⎿   Context Usage
     ⛁ ⛀ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁   claude-opus-4-5-20251101 · 120k/200k tokens (60%)
     ⛁ ⛀ ⛀ ⛀ ⛀ ⛁ ⛁ ⛁ ⛁ ⛁   ⛁ System prompt: 3.0k tokens (1.5%)
     ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁   ⛁ System tools: 17.8k tokens (8.9%)
     ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁   ⛁ MCP tools: 293 tokens (0.1%)
     ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁   ⛁ Custom agents: 883 tokens (0.4%)
     ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁   ⛁ Memory files: 1.1k tokens (0.5%)
     ⛁ ⛁ ⛁ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶   ⛁ Skills: 309 tokens (0.2%)
     ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶   ⛁ Messages: 96.9k tokens (48.5%)
     ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶   ⛁ Compact buffer: 3.0k tokens (1.5%)
     ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛁ ⛀   ⛶ Free space: 77k (38.3%)
```
After `/analyze-wpd docs/wpds/pipeline-refactor.md` reads 39960 tokens:
```
/context
  ⎿   Context Usage
     ⛁ ⛀ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁   claude-opus-4-5-20251101 · 180k/200k tokens (90%)
     ⛁ ⛀ ⛀ ⛀ ⛀ ⛁ ⛁ ⛁ ⛁ ⛁   ⛁ System prompt: 3.0k tokens (1.5%)
     ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁   ⛁ System tools: 17.8k tokens (8.9%)
     ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁   ⛁ MCP tools: 293 tokens (0.1%)
     ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁   ⛁ Custom agents: 883 tokens (0.4%)
     ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁   ⛁ Memory files: 1.1k tokens (0.5%)
     ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁   ⛁ Skills: 309 tokens (0.2%)
     ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁   ⛁ Messages: 156.5k tokens (78.2%)
     ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁   ⛁ Compact buffer: 3.0k tokens (1.5%)
     ⛁ ⛁ ⛁ ⛶ ⛶ ⛶ ⛶ ⛶ ⛁ ⛀   ⛶ Free space: 17k (8.6%)
```

There are a few oddities in the changing data: we see that `/setup-hard`, which hoists 4 files (totaling 68112 tokens) increase our "Messages" context from 8 to 96.9k tokens (96.9k increase). Yes, this also includes the command text itself and the operation for creating the Workscope ID, but does that (and additional thinking?) really account for an extra 28.8k tokens? The `/analyze-wpd` operation (reading 39960 tokens) increase our "Messages" content from 96.9k to 156.5k (59.6k increase). Yes, there is much more loss to "thinking" tokens as well as the audit reply, but does that really account for an extra 19.9k tokens?

That's 48.7k "unknown" tokens to account for.  The sizes of the `/setup-hard` and `/analyze-wpd` commands are 1k tokens combined.  Looking at the exported chats of other trials, these `.txt` files (an estimate for the amount of conversational text) range from 49kb-66kb in size (10.1k-13.6k tokens).

156.5k reported Messages content = 108k (total file data) + 13.6k (chat, high estimate) + 1k (commands) + 33.8k (unaccounted).

I then ran an investigation to see if model "thinking" could truly account for these missing 34k tokens.  I disabled "thinking" in Claude Code and re-ran the Hard scenario.  With all the same steps as previous, I saw the following:

**Hard Scenario (Thinking OFF)**:
```
Baseline (fresh session):
- Total: 23k (12%)
- Messages: 0.0k (0.0%)

After `/setup-hard`:
- Loaded (via @ hoisting) 68112 tokens:
  - `docs/specs/operations-manual-standard.md` (963 lines, 19323 tokens)
  - `docs/specs/operations-manual-exceptions.md` (1593 lines, 15636 tokens)
  - `docs/specs/architecture-deep-dive.md` (1071 lines, 14676 tokens)
  - `docs/specs/troubleshooting-compendium.md` (2006 lines, 18477 tokens)
- Total: 120k (60%)
- Messages: 96.9k (48.5%)

After `/analyze-wpd docs/wpds/pipeline-refactor.md`:
- Loaded (via self-initiated Read calls) 39960 tokens:
  - `Read(docs/wpds/pipeline-refactor.md)` (393 lines, 5034 tokens)
  - `Read(docs/specs/data-pipeline-overview.md)` (426 lines, 6041 tokens)
  - `Read(docs/specs/integration-layer.md)` (531 lines, 4886 tokens)
  - `Read(docs/specs/compliance-requirements.md)` (393 lines, 3939 tokens)
  - `Read(docs/specs/module-alpha.md)` (743 lines, 6204 tokens)
  - `Read(docs/specs/module-beta.md)` (742 lines, 6198 tokens)
  - `Read(docs/specs/module-gamma.md)` (772 lines, 7658 tokens)
- Total: 181k (90%)
- Messages: 157.3k (78.6%)

Note: Harness warning popped up: "Context low (0% remaining) - Run /compact to compact & continue"

Outcome (via self-report prompt): Success (no self-reported phantom reads)
```

So there was nearly zero change, other than the self-initiated Read calls being performed in a slightly different order.

---

This repository has now been published to GitHub to share our investigation progress publicly. The main objectives of this work are as follows:

1) Explore potential workarounds and identify one that works reliably.
2) Create a method for reproducing the issue (runnint Trials with both failure and success) using _this repo_.
3) Continue to investigate the issue (analysis scripts, journal, etc.)

Objective 1 has been met. Objective 2 has not been met. Objective 3 is probably unbounded, but we continue.

I'd like to focus on Objective 2 now. I've attempted to run the following experiment several times on a clone of this repo ("Experiment-02" to distinguish it from the original experiment "Experiment-01" performed prior to this repository's creation):

<experiment-02>
### Preparation

1. See `docs/core/Experiment-Methodology-01.md` for setup details regarding disabling Claude Code auto-updates.
2. Ensure Filesystem MCP workaround is disabled
3. Installed Claude Code 2.1.6: ./scripts/install_cc.sh 2.1.6

### Experimental Trial

1. Launch Claude code
2. Submit the following prompts:

```
/wsd:init --custom
```

```
/refine-plan docs/features/session-analysis-scripts/Session-Analysis-Scripts-Overview.md
```

```
We have recently seen a number of User Agents reporting issues reading files like the following:

<session-agent-response>
Looking back at my history, you're right. My first Read call for the file returned:

  <persisted-output>Tool result saved to: /Users/gray/.claude/projects/-Users-gray-Projects-workscope/dadf32a6-c83d-462d-b678-fbe7f191f42f/tool-results/toolu_019Nqx8qLWvdFSjvMsy5xFkM.txt

  Use Read to view</persisted-output>

  I did not follow up with a Read call to view that persisted output. I proceeded with my "investigation" without ever having actually read the file contents. I was operating completely blind, making assumptions about a document I never saw.

  The same thing happened with several other files at the start - WSD-Runtime-Metadata-Schema.md, WSD-Manifest-Schema.md, Manifest-Driven-Pipeline-Overview.md all returned <persisted-output> messages that I never followed up on
</session-agent-response>

I am debugging this recurring issue and I am checking to see if this particular session is a reproduction of this issue. Did you experience this during your execution of the command?
```

3. Record whether the Session Agent reports evidence of a phantom read or not.
4. Run `/export` and provide a filename to mark the Trial. You can run `/status` ahead of time and copy the session id for `SESSION_ID.txt`.
5. `/exit` Claude Code.
6. Repeat.
</experiment-02>

All of my runs of Experiment-02 on this repo (build 2.1.6) have been successes.  Based on the most recent findings (in `docs/core/Example-Session-Analysis.md`), it may be that resets are what is causing the issue. It may be that our current "sample" WPD is not sufficiently complex to trigger a reset.

For an experiment, we need to come up with two WSDs:
