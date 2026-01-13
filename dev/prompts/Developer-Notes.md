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


2caf2337-66bf-41d1-ad27-9d2cab7bd2dc

grep -rlZ "2caf2337-66bf-41d1-ad27-9d2cab7bd2dc" . | xargs -0 -J % cp % ~/Projects/claude-code-bug-phantom-reads-17407/dev/misc/2.0.60-good/


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

## FUTURE FEATURES

