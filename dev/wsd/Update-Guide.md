# Workscope-Dev Update Guide

**Version:** 1.0.0
**Audience:** Developers updating WSD installations

## Introduction

This guide shows you how to update your Workscope-Dev (WSD) installation to receive improvements and bug fixes while preserving your customizations.

## How Content Preservation Works

When you run a WSD update, the system intelligently merges new template improvements with your existing customizations. Understanding this process helps you confidently update knowing your work is safe.

### Tag-Based Preservation

WORKSCOPE-DEV tags mark sections of files that contain your project-specific content. During an update, the system performs the following process for each file containing tags:

1. **Read your current file** - The update system examines your installed file and identifies all WORKSCOPE-DEV tags
2. **Extract your content** - For each tag, it captures exactly what you've written between the opening and closing markers
3. **Apply the template update** - The new template version replaces the file structure
4. **Restore your content** - Your extracted content is placed back into the corresponding tags in the updated file

This means the template structure around your tags can change (bug fixes, improved instructions, new sections), while your customized content remains exactly as you wrote it.

For example, if you customized the project introduction in `.claude/commands/wsd/init.md`, an update might change the instructions above and below your content, but your project description stays intact.

### What Happens to Each Tag Type

**Existing tags with your content:** Your content is preserved byte-for-byte. The surrounding template text may change, but what's inside your tags remains untouched.

**New tags in the update:** If a new WSD version adds a tag that didn't exist before, you'll receive the template's default content for that tag. You can then customize it as needed.

**Removed tags:** If a tag is removed from the template in a new version, any content you had in that tag will be discarded. This is rare and typically only happens during major structural changes.

### File-Level Protection

Some files are completely protected from updates and never modified after the initial install (they are marked with the `no_overwrite` policy). Examples include:
- Action-Plan.md (your project plan)
- PRD.md (your product requirements)
- Design-Decisions.md (your project's architectural philosophies)
- README.md and LICENSE (your project identity)

The complete list of protected files is defined in `wsd.json` under the `no_overwrite` array. Inspect this file in your WSD source to see all protected paths.

The dry-run output shows protected files in the "Files to Skip" section, so you know exactly what will and won't be touched.

## Prerequisites

- **Git**: Strongly recommended for safe rollback
- **WSD source**: Official WSD distribution

## Obtaining the Latest WSD

Get the latest WSD distribution, and be sure to use the official WSD source, not another project where WSD is already installed.

## Update Workflow

### Update Commands

WSD provides two ways to perform updates:

**Using `install` (recommended):** The `install` command auto-detects whether you have an existing WSD installation. If a `.wsd` manifest exists, it automatically performs an update instead of a fresh installation.

```bash
python /path/to/wsd-source/wsd.py install .
```

**Using `update` (explicit):** The `update` command is an explicit update-only mode. It requires an existing `.wsd` manifest and will error immediately if none exists. Use this when you want the command to fail fast if your assumption about having WSD installed is wrong.

```bash
python /path/to/wsd-source/wsd.py update .
```

Both commands accept `--dry-run` and `--verbose` flags. The `--force` flag is only available with `install` (to force a fresh installation over an existing one).

### How Updates Work

When you run an update, WSD compares your installed files against the new WSD source and categorizes each file into one of four actions:

**Files to Add (+):** New files in the WSD source that don't exist in your installation. These are copied directly to your project.

**Files to Delete (-):** Files that exist in your installation (tracked in the manifest) but are no longer part of WSD. These are removed from your project.

**Files to Update (~):** Files that exist in both your installation and the new source. The update applies tag preservation to maintain your customizations while updating the template structure.

**Files to Skip (=):** Files marked with the `no_overwrite` policy that are never modified after initial installation, regardless of changes in the WSD source.

### Update Process Steps

The update system follows this sequence:

1. **Validation** - Checks that your project has a valid `.wsd` manifest and the WSD source has valid metadata
2. **File Categorization** - Compares manifest files against source files to determine actions
3. **Dry-Run Preview** (if requested) - Shows planned changes without modifying anything
4. **File Deletions** - Removes files no longer in WSD
5. **File Additions** - Copies new files to your project
6. **File Updates** - Updates existing files with tag preservation
7. **Manifest Update** - Records the new state in your `.wsd` manifest

### Recommended Process

```bash
# 1. Commit current work (safety checkpoint)
git add -A && git commit -m "Checkpoint before WSD update"

# 2. Preview changes (recommended)
python /path/to/wsd-source/wsd.py install --dry-run .

# 3. Review the preview output carefully
# Look for unexpected deletions or files you want to protect

# 4. Apply update
python /path/to/wsd-source/wsd.py install .

# 5. Review changes
git diff

# 6. Verify customizations survived
grep -A 5 "WORKSCOPE-DEV" .claude/commands/wsd/init.md

# 7. Commit the update
git add -A && git commit -m "Update WSD to version X.Y.Z"
```

## Using Dry-Run

The `--dry-run` flag lets you preview exactly what an update will do before making any changes. This is the safest way to understand the impact of an update.

**Important:** The `--dry-run` flag is only available for updates, not fresh installations. This is because updates operate on known WSD files (tracked in the manifest), while fresh installations must use collision detection to protect potentially unrelated user files that happen to share names with WSD files.

### When to Use Dry-Run

**Always use dry-run before your first update** to understand what will change. After you're familiar with the update process, you can skip it for routine updates, but it remains valuable when:

- Updating after a long time (many changes accumulated)
- Unsure if your customizations are properly tagged
- Wanting to verify protected files won't be touched
- Checking if files you added will be deleted

### Running Dry-Run

```bash
python /path/to/wsd-source/wsd.py install --dry-run .
```

### Understanding the Output

The dry-run preview organizes files into categories, each marked with a symbol:

```
WSD Update Preview (--dry-run)
==============================

Current Version: 1.0.0
Update Version:  1.1.0

Changes Summary
------------------------------
Files to delete:  2
Files to add:     2
Files to update:  2
Files to skip:    2

Files to Delete
------------------------------
  - .claude/commands/old-command.md
  - scripts/deprecated-script.py

Files to Add
------------------------------
  + .claude/commands/new-command.md
  + docs/references/new-guide.md

Files to Update (with content preservation)
------------------------------
  ~ .claude/commands/wsd/init.md
  ~ docs/read-only/Agent-Rules.md

Files to Skip (protected by no_overwrite)
------------------------------
  = docs/core/Action-Plan.md (user-owned content)
  = docs/core/PRD.md (user-owned content)

Statistics
------------------------------
Current file count: 87
Updated file count: 87
Total changes:      6

To proceed with this update, run:
  wsd.py install .

To cancel, take no action.
```

**Symbol Reference:**

| Symbol | Category        | Description                                  |
| ------ | --------------- | -------------------------------------------- |
| `-`    | Files to Delete | Files removed from your project              |
| `+`    | Files to Add    | New files added to your project              |
| `~`    | Files to Update | Existing files updated with tag preservation |
| `=`    | Files to Skip   | Protected files that won't be modified       |

### What Dry-Run Guarantees

**Dry-run makes NO changes to your project.** It only reads files and calculates what would happen. Your files, manifest, and customizations remain exactly as they were before running the command.

### After Reviewing

If the preview looks correct, run the same command without `--dry-run`:

```bash
python /path/to/wsd-source/wsd.py install .
```

If something looks wrong (unexpected deletions, files you want protected), address the issue before proceeding. See the Troubleshooting section for common scenarios.

## Verifying Customizations

After updating, check that your customizations survived:

```bash
# Check project introduction
grep -A 10 "wsd-init-project-introduction" .claude/commands/wsd/init.md

# Check custom rules
grep -A 10 "agent-rules-project-specific" docs/read-only/Agent-Rules.md
```

You should see your custom content, not template placeholders.

## Protected Files

Some files are completely skipped during updates because they contain your project-specific content. Examples include Action-Plan.md, PRD.md, Design-Decisions.md, README.md, and LICENSE. The complete list is defined in `wsd.json` under the `no_overwrite` array.

The dry-run output shows which files are protected in the "Files to Skip" section.

## Error Recovery

WSD includes built-in protections and recovery options for when things go wrong during updates.

### Automatic Rollback Protection

If an update fails during file operations (permission error, disk full, etc.), WSD automatically attempts to restore your `.wsd` manifest to its pre-update state. This prevents your installation from being left in an inconsistent state where the manifest doesn't match actual files.

When automatic rollback occurs, you'll see a message like:

```
Error: Permission denied writing to 'docs/read-only/Agent-Rules.md'

Rollback: Manifest restored to pre-update state

Your installation remains in its previous state. Fix the error and retry.
```

### Git-Based Recovery (Recommended)

If you committed before updating (as recommended), git provides the most reliable recovery:

**Full rollback to pre-update state:**
```bash
git reset --hard HEAD~1
```

**Restore a specific file:**
```bash
git checkout HEAD~1 .claude/commands/wsd/init.md
```

**View what changed:**
```bash
git diff HEAD~1
```

**Selective rollback (keep some changes, revert others):**
```bash
# Restore specific files while keeping other changes
git checkout HEAD~1 -- docs/read-only/Agent-Rules.md
git checkout HEAD~1 -- .claude/commands/wsd/init.md
```

### Recovering Without Git

If you didn't commit before updating:

**Option 1: Re-run the update**
If the update completed but produced unexpected results, you can run it again. Updates are idempotent—running the same update twice produces the same result.

**Option 2: Restore from backup**
If you have a backup of your project, restore the affected files.

**Option 3: Manual reconstruction**
For customizations lost due to malformed tags:
1. Find the original WSD template file in the WSD source
2. Copy the file structure
3. Re-add your customizations with proper tag syntax

### Concurrent Update Detection

If WSD detects that another update may be running (manifest modified within the last 5 minutes), it warns you:

```
Warning: The .wsd manifest was modified 2 minutes ago.
Another update may be in progress.

Continue anyway? [y/N]
```

If you see this unexpectedly (no other update is running), it may indicate a previous update was interrupted. Check for any `.wsd.tmp` or `.wsd.bak` files and remove them before proceeding.

### Interrupted Update Detection

If a previous update was interrupted before completion, WSD detects this and provides recovery guidance:

```
Warning: Detected signs of an interrupted update.

Found: .wsd.tmp (temporary manifest file)

This may indicate a previous update did not complete successfully.

Recovery options:
  1. Use git to restore to a known good state:
     git status
     git checkout .

  2. Manually verify your installation matches the manifest:
     - Check that files listed in .wsd exist
     - Remove any .wsd.tmp or .wsd.bak files

  3. Force a fresh installation:
     python /path/to/wsd-source/wsd.py install --force .
```

### When to Use --force

The `--force` flag bypasses normal update checks and performs a fresh installation. Use it when:

- Your installation is corrupted beyond repair
- You want to reset WSD to default state
- Recovery options above haven't worked

```bash
python /path/to/wsd-source/wsd.py install --force .
```

**Warning:** Using `--force` will overwrite all WSD files. Your customizations in WORKSCOPE-DEV tags are preserved, but any modifications outside of tags will be lost.

## Troubleshooting

### Lost Customizations

**Symptoms:** After an update, your custom content is replaced with template defaults.

**Common Causes:**

1. **Malformed tag syntax** - Missing closing tag or typo in tag markers
2. **Modified tag ID** - Changed the tag identifier (e.g., `wsd-init-project-introduction` to something else)
3. **Nested tags** - Tags placed inside other tags (not supported)

**Diagnosis:**
```bash
# Check if your tags are properly formed
grep -B 1 -A 1 "WORKSCOPE-DEV" .claude/commands/wsd/init.md

# You should see pairs like:
# <WORKSCOPE‑DEV tag-id>
# ... your content ...
# </WORKSCOPE‑DEV>
```

**Recovery:**
```bash
# View the previous version
git show HEAD~1:.claude/commands/wsd/init.md

# Copy your content and add it back with correct tag syntax:
# <WORKSCOPE‑DEV tag-id>
# Your content here
# </WORKSCOPE‑DEV>
```

**Prevention:** Always verify tag syntax after editing. Both the opening `<WORKSCOPE‑DEV tag-id>` and closing `</WORKSCOPE‑DEV>` markers must be present and properly formatted.

### Permission Errors

**Symptoms:** Update fails with "Permission denied" errors.

**Diagnosis:**
```bash
# Check file permissions
ls -la .claude/commands/
ls -la docs/read-only/
```

**Fix:**
```bash
# Grant write permissions
chmod -R u+w .claude/ docs/read-only/ scripts/

# Retry the update
python /path/to/wsd-source/wsd.py install .
```

**Prevention:** Ensure your user has write access to all WSD directories before updating.

### Unexpected File Deletions

**Symptoms:** Dry-run shows files being deleted that you want to keep.

**Cause:** Files you created in WSD directories aren't tracked in the manifest, so WSD doesn't know they exist. When the source no longer has a file, WSD marks the manifest's version for deletion.

**Understanding the Behavior:** WSD only deletes files that are tracked in your `.wsd` manifest AND no longer exist in the WSD source. Files you created yourself are not in the manifest and won't be deleted.

**If you see unexpected deletions in dry-run:**
1. Check if the file is actually yours (created by you) or a WSD template file
2. If it's a WSD file being removed from the template, that's expected behavior
3. If you modified a WSD file outside of tags, those changes will be lost during update

**Recovery after update:**
```bash
git checkout HEAD~1 -- path/to/deleted/file
```

### Version Downgrade Warnings

**Symptoms:** Warning message about downgrading to an older version.

**Cause:** You're running an update from an older WSD source than what's currently installed.

**Example warning:**
```
Warning: Downgrade detected (1.2.0 → 1.1.0)

Downgrading may cause issues if the newer version added features
your project now depends on.

Continue with downgrade? [y/N]
```

**Recommendations:**
- Downgrading is generally safe but not recommended
- If you need specific older behavior, consider if there's another solution
- Always use dry-run first when downgrading to see what will change

### Update Shows No Changes

**Symptoms:** Running an update produces no changes, even though you expected updates.

**Possible causes:**

1. **Already up to date** - Your installation matches the source version
2. **Wrong source path** - You're pointing to the wrong WSD source directory
3. **Using installed copy as source** - You're accidentally using your project's wsd.py instead of the WSD distribution

**Verification:**
```bash
# Check your installed version
cat .wsd | grep version

# Check the source version
cat /path/to/wsd-source/wsd.json | grep version
```

### Manifest Corruption

**Symptoms:** Errors about invalid or corrupted `.wsd` manifest file.

**Recovery:**
```bash
# Option 1: Force reinstall (preserves tag customizations)
python /path/to/wsd-source/wsd.py install --force .

# Option 2: Restore from git
git checkout HEAD~1 -- .wsd
python /path/to/wsd-source/wsd.py install .
```

### Large File Warnings

**Symptoms:** Warning about large files during update.

**Cause:** WSD detected files larger than 100 MB that may impact memory during tag preservation.

**Behavior:** For large files, WSD:
- Warns you about the memory implications
- Skips tag preservation for large binary files
- Uses streaming copy to avoid memory exhaustion

**Action:** Review the warning and confirm to proceed. Large binary files shouldn't contain WORKSCOPE-DEV tags anyway.

### Verbose Mode for Debugging

If you're having trouble understanding what's happening during an update, use verbose mode:

```bash
python /path/to/wsd-source/wsd.py install --verbose --dry-run .
```

This shows detailed information about each file operation, helping you identify where issues occur.

## Quick Reference

### Commands

```bash
# Preview update (always recommended first)
python /path/to/wsd-source/wsd.py install --dry-run .

# Apply update
python /path/to/wsd-source/wsd.py install .

# Verbose update (for debugging)
python /path/to/wsd-source/wsd.py install --verbose .

# Force reinstall (resets WSD, preserves tag content)
python /path/to/wsd-source/wsd.py install --force .
```

### Recovery

```bash
# Full rollback
git reset --hard HEAD~1

# Restore single file
git checkout HEAD~1 -- path/to/file

# View changes
git diff HEAD~1
```

### Verification

```bash
# Check customizations survived
grep -r "WORKSCOPE-DEV" .claude/ docs/

# Run health check
./wsd.py health

# Check installed version
cat .wsd | grep version
```

### Dry-Run Output Symbols

| Symbol | Meaning                                      |
| ------ | -------------------------------------------- |
| `-`    | File will be deleted                         |
| `+`    | File will be added                           |
| `~`    | File will be updated (with tag preservation) |
| `=`    | File is protected (skipped)                  |

## Practical Examples

The following examples demonstrate common update scenarios you'll encounter when maintaining your WSD installation.

### Example: Basic Update Workflow

This example shows the simplest update path where you have a standard WSD installation with typical customizations in WORKSCOPE-DEV tags.

**Scenario:** You installed WSD a month ago, customized the project introduction and agent rules, and now want to update to receive the latest improvements.

**Step 1: Create a safety checkpoint**

Before any update, commit your current work so you can easily roll back if needed:

```bash
cd /path/to/my-project
git add -A && git commit -m "Checkpoint before WSD update"
```

**Step 2: Preview the update**

Run dry-run to see exactly what will change:

```bash
python /path/to/wsd-source/wsd.py install --dry-run .
```

**Expected output:**
```
WSD Update Preview (--dry-run)
==============================

Current Version: 1.0.0
Update Version:  1.1.0

Changes Summary
------------------------------
Files to delete:  0
Files to add:     2
Files to update:  15
Files to skip:    3

Files to Add
------------------------------
  + .claude/agents/new-validator.md
  + scripts/diagnostics.py

Files to Update (with content preservation)
------------------------------
  ~ .claude/commands/wsd/init.md
  ~ .claude/commands/wsd/execute.md
  ~ docs/read-only/Agent-Rules.md
  ~ docs/read-only/Agent-System.md
  [... more files ...]

Files to Skip (protected by no_overwrite)
------------------------------
  = docs/core/Action-Plan.md (user-owned content)
  = docs/core/PRD.md (user-owned content)
  = dev/prompts/Developer-Notes.md (user-owned content)

Statistics
------------------------------
Current file count: 85
Updated file count: 87
Total changes:      17

To proceed with this update, run:
  wsd.py install .

To cancel, take no action.
```

**Step 3: Review and apply the update**

The preview shows your protected files will be skipped and files with tags will preserve your content. Apply the update:

```bash
python /path/to/wsd-source/wsd.py install .
```

**Step 4: Verify your customizations**

Check that your project-specific content survived:

```bash
# Verify project introduction
grep -A 5 "wsd-init-project-introduction" .claude/commands/wsd/init.md

# Verify custom rules
grep -A 5 "agent-rules-project-specific" docs/read-only/Agent-Rules.md
```

You should see your custom content, not template placeholders.

**Step 5: Commit the update**

```bash
git add -A && git commit -m "Update WSD to version 1.1.0"
```

### Example: Update with Customizations

This example demonstrates updating when you have extensive customizations and want to verify everything is preserved correctly.

**Scenario:** You've heavily customized your WSD installation with project-specific rules, custom workflow steps, and detailed project descriptions. You want to update while being extra careful about preservation.

**Step 1: Audit your customizations before updating**

First, identify all your customized tags:

```bash
# Find all WORKSCOPE-DEV tags in your installation
grep -r "WORKSCOPE-DEV" .claude/ docs/ --include="*.md" | grep -v ".wsd"
```

**Sample output:**
```
.claude/commands/wsd/init.md:<WORKSCOPE‑DEV wsd-init-project-introduction>
.claude/commands/wsd/execute.md:<WORKSCOPE‑DEV wsd-execute-workflow>
docs/read-only/Agent-Rules.md:<WORKSCOPE‑DEV agent-rules-project-specific>
docs/read-only/Agent-Rules.md:<WORKSCOPE‑DEV agent-rules-pre-release>
docs/read-only/Agent-Rules.md:<WORKSCOPE‑DEV agent-model-quirks>
```

**Step 2: Document your key customizations**

For critical customizations, capture the current content:

```bash
# Save a snapshot of your project introduction
grep -A 50 "wsd-init-project-introduction" .claude/commands/wsd/init.md > /tmp/my-intro-backup.txt

# Save your custom rules
grep -A 100 "agent-rules-project-specific" docs/read-only/Agent-Rules.md > /tmp/my-rules-backup.txt
```

**Step 3: Verify tag syntax is correct**

Malformed tags won't be preserved. Check that all tags are properly formed:

```bash
# Check for opening tags
grep -n "<WORKSCOPE‑DEV" .claude/commands/wsd/init.md

# Check for closing tags
grep -n "</WORKSCOPE‑DEV>" .claude/commands/wsd/init.md
```

Each opening tag should have a corresponding closing tag. If counts don't match, fix the syntax before updating.

**Step 4: Preview and apply update**

```bash
# Preview
python /path/to/wsd-source/wsd.py install --dry-run .

# Apply
python /path/to/wsd-source/wsd.py install .
```

**Step 5: Compare before and after**

Use git to see exactly what changed in your customized files:

```bash
# See all changes
git diff

# Focus on a specific customized file
git diff .claude/commands/wsd/init.md
```

In the diff, you should see:
- Template text around your tags may have changed
- Content inside your WORKSCOPE-DEV tags should be unchanged

**Step 6: Verify critical customizations**

Compare against your backups:

```bash
# Current content
grep -A 50 "wsd-init-project-introduction" .claude/commands/wsd/init.md

# Compare with backup
diff /tmp/my-intro-backup.txt <(grep -A 50 "wsd-init-project-introduction" .claude/commands/wsd/init.md)
```

If the diff is empty, your customizations were preserved exactly.

### Example: Recovering from Errors

This example shows how to handle and recover from common update errors.

**Scenario 1: Permission denied during update**

You attempt an update but receive a permission error:

```bash
$ python /path/to/wsd-source/wsd.py install .

Error: Permission denied writing to 'docs/read-only/Agent-Rules.md'

Rollback: Manifest restored to pre-update state

Your installation remains in its previous state. Fix the error and retry.
```

**Recovery steps:**

```bash
# Check file permissions
ls -la docs/read-only/Agent-Rules.md

# Grant write permission
chmod u+w docs/read-only/Agent-Rules.md

# If multiple files need fixing
chmod -R u+w docs/read-only/

# Retry the update
python /path/to/wsd-source/wsd.py install .
```

**Scenario 2: Interrupted update**

Your update was interrupted (network issue, terminal closed, etc.) and you see warnings on the next attempt:

```bash
$ python /path/to/wsd-source/wsd.py install .

Warning: Detected signs of an interrupted update.

Found: .wsd.tmp (temporary manifest file)

This may indicate a previous update did not complete successfully.

Recovery options:
  1. Use git to restore to a known good state:
     git status
     git checkout .

  2. Manually verify your installation matches the manifest:
     - Check that files listed in .wsd exist
     - Remove any .wsd.tmp or .wsd.bak files

  3. Force a fresh installation:
     python /path/to/wsd-source/wsd.py install --force .
```

**Recovery using git (recommended):**

```bash
# See what's changed
git status

# Restore all WSD files to pre-update state
git checkout .

# Remove temporary files
rm -f .wsd.tmp .wsd.bak

# Retry the update
python /path/to/wsd-source/wsd.py install .
```

**Recovery without git:**

```bash
# Remove temporary files
rm -f .wsd.tmp .wsd.bak

# Force a clean installation (preserves tag content)
python /path/to/wsd-source/wsd.py install --force .

# Verify your customizations
grep -A 5 "wsd-init-project-introduction" .claude/commands/wsd/init.md
```

**Scenario 3: Lost customizations due to malformed tags**

After an update, you notice your project introduction is gone:

```bash
$ grep -A 5 "wsd-init-project-introduction" .claude/commands/wsd/init.md

<WORKSCOPE‑DEV wsd-init-project-introduction>
Describe your project here
</WORKSCOPE‑DEV>
```

This shows template default content instead of your customization, indicating the tag was malformed before the update.

**Recovery:**

```bash
# Check what your content was before the update
git show HEAD~1:.claude/commands/wsd/init.md | grep -A 50 "wsd-init-project-introduction"

# If you see your content was there but the closing tag was missing,
# restore the file and fix the tag syntax
git checkout HEAD~1 -- .claude/commands/wsd/init.md

# Edit to fix the malformed tag (add missing closing tag)
# Then run the update again
python /path/to/wsd-source/wsd.py install .
```

### Example: Version Downgrade

This example shows how to intentionally install an older WSD version, which may be necessary if a newer version introduces issues for your specific use case.

**Scenario:** You updated to WSD 1.2.0 but discovered it has a problem with your workflow. You want to downgrade to 1.1.0 while you wait for a fix.

**Step 1: Commit current state**

```bash
git add -A && git commit -m "Checkpoint before WSD downgrade"
```

**Step 2: Preview the downgrade**

Point to your older WSD source and preview:

```bash
python /path/to/wsd-1.1.0/wsd.py install --dry-run .
```

**Expected output:**
```
Warning: Downgrade detected (1.2.0 → 1.1.0)

Downgrading may cause issues if the newer version added features
your project now depends on.

Continue with downgrade? [y/N]
```

If you proceed with the preview (enter `y`), you'll see:

```
WSD Update Preview (--dry-run)
==============================

Current Version: 1.2.0
Update Version:  1.1.0

Changes Summary
------------------------------
Files to delete:  3
Files to add:     0
Files to update:  12
Files to skip:    3

Files to Delete
------------------------------
  - .claude/agents/new-feature.md
  - scripts/new-utility.py
  - docs/read-only/standards/New-Standard.md

Files to Update (with content preservation)
------------------------------
  ~ .claude/commands/wsd/init.md
  ~ .claude/commands/wsd/execute.md
  [... more files ...]

Statistics
------------------------------
Current file count: 90
Updated file count: 87
Total changes:      15
```

**Step 3: Understand the implications**

The preview shows:
- **Files to Delete**: Features added in 1.2.0 that don't exist in 1.1.0
- **Files to Update**: Files that will revert to 1.1.0 versions (your tag content preserved)

Consider whether your project uses any of the files being deleted.

**Step 4: Apply the downgrade**

```bash
python /path/to/wsd-1.1.0/wsd.py install .
```

You'll see the downgrade warning again:

```
Warning: Downgrade detected (1.2.0 → 1.1.0)

Downgrading may cause issues if the newer version added features
your project now depends on.

Continue with downgrade? [y/N]
```

Enter `y` to proceed.

**Step 5: Verify the downgrade**

```bash
# Check version
cat .wsd | grep version

# Verify your customizations survived
grep -A 5 "wsd-init-project-introduction" .claude/commands/wsd/init.md

# Run health check
./wsd.py health
```

**Step 6: Commit the downgrade**

```bash
git add -A && git commit -m "Downgrade WSD to version 1.1.0 (temporary)"
```

**Alternative: Selective file restoration**

If you only need to revert specific behavior, consider using git to restore individual files instead of a full downgrade:

```bash
# Restore just the problematic file from before the update
git checkout HEAD~1 -- .claude/commands/wsd/execute.md

# Or restore multiple specific files
git checkout HEAD~1 -- .claude/agents/task-master.md docs/read-only/Agent-System.md
```

This approach preserves other 1.2.0 improvements while reverting specific files.

---

*For installation, see Integration-Guide.md.*
