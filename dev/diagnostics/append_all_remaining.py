#!/usr/bin/env python
"""Append all remaining integration test classes."""

from pathlib import Path

# Read current test file
test_file = Path("tests/test_collect_trials.py")
content = test_file.read_text()

# Read the test class that was just added with cat >> (need to keep it)
# and add the remaining two classes

remaining_classes = """

@patch.dict("os.environ", {}, clear=True)
class TestIntegrationMixedStructures:
    \"\"\"Integration tests for collecting trials with mixed session structures.

    Tests batch collection where different trials have different session
    storage structures in the same collection run.
    \"\"\"

    def test_batch_with_flat_hybrid_hierarchical_structures(
        self,
        tmp_path: Path,
        sample_export_content: Callable[[str], str],
        sample_session_content: Callable[[str], str],
    ) -> None:
        \"\"\"Test batch collection with all three session structures in same run.

        Verifies unified collection algorithm correctly handles flat, hybrid,
        and hierarchical structures without detection logic.

        Args:
            tmp_path: Pytest fixture providing temporary directory for test files.
            sample_export_content: Pytest fixture providing factory for export content.
            sample_session_content: Pytest fixture providing factory for session content.
        \"\"\"
        # Setup directories
        exports_dir = tmp_path / "exports"
        destination_dir = tmp_path / "trials"
        session_dir = tmp_path / "sessions"
        exports_dir.mkdir()
        destination_dir.mkdir()
        session_dir.mkdir()

        # Flat structure trial
        flat_id = "20260119-130000"
        flat_uuid = "uuid-flat-mixed"
        (exports_dir / "flat.txt").write_text(sample_export_content(flat_id))
        (session_dir / f"{flat_uuid}.jsonl").write_text(sample_session_content(flat_id))
        (session_dir / "agent-flat-1.jsonl").write_text(f'{{"sessionId": "{flat_uuid}"}}\\n')

        # Hybrid structure trial
        hybrid_id = "20260119-131000"
        hybrid_uuid = "uuid-hybrid-mixed"
        (exports_dir / "hybrid.txt").write_text(sample_export_content(hybrid_id))
        (session_dir / f"{hybrid_uuid}.jsonl").write_text(sample_session_content(hybrid_id))
        hybrid_subdir = session_dir / hybrid_uuid
        hybrid_subdir.mkdir()
        (hybrid_subdir / "tool-results").mkdir()
        (hybrid_subdir / "tool-results" / "toolu_h1.txt").write_text("tool output")
        (session_dir / "agent-hybrid-1.jsonl").write_text(f'{{"sessionId": "{hybrid_uuid}"}}\\n')

        # Hierarchical structure trial
        hier_id = "20260119-132000"
        hier_uuid = "uuid-hier-mixed"
        (exports_dir / "hier.txt").write_text(sample_export_content(hier_id))
        (session_dir / f"{hier_uuid}.jsonl").write_text(sample_session_content(hier_id))
        hier_subdir = session_dir / hier_uuid
        hier_subdir.mkdir()
        (hier_subdir / "subagents").mkdir()
        (hier_subdir / "subagents" / "agent-hier-1.jsonl").write_text("content")
        (hier_subdir / "tool-results").mkdir()
        (hier_subdir / "tool-results" / "toolu_h1.txt").write_text("tool output")

        # Collect all three
        flat_result = collect_single_trial(
            workscope_id=flat_id,
            export_path=exports_dir / "flat.txt",
            session_dir=session_dir,
            destination_dir=destination_dir,
            verbose=False,
        )

        hybrid_result = collect_single_trial(
            workscope_id=hybrid_id,
            export_path=exports_dir / "hybrid.txt",
            session_dir=session_dir,
            destination_dir=destination_dir,
            verbose=False,
        )

        hier_result = collect_single_trial(
            workscope_id=hier_id,
            export_path=exports_dir / "hier.txt",
            session_dir=session_dir,
            destination_dir=destination_dir,
            verbose=False,
        )

        # Verify all succeeded
        assert flat_result.status == "collected"
        assert hybrid_result.status == "collected"
        assert hier_result.status == "collected"

        # Verify flat structure preserved
        flat_dir = destination_dir / flat_id
        assert (flat_dir / "agent-flat-1.jsonl").exists()
        assert not (flat_dir / flat_uuid).exists()  # No subdirectory

        # Verify hybrid structure preserved
        hybrid_dir = destination_dir / hybrid_id
        assert (hybrid_dir / "agent-hybrid-1.jsonl").exists()
        assert (hybrid_dir / hybrid_uuid / "tool-results" / "toolu_h1.txt").exists()

        # Verify hierarchical structure preserved
        hier_dir = destination_dir / hier_id
        assert (hier_dir / hier_uuid / "subagents" / "agent-hier-1.jsonl").exists()
        assert (hier_dir / hier_uuid / "tool-results" / "toolu_h1.txt").exists()
        assert not (hier_dir / "agent-hier-1.jsonl").exists()  # Not at root


@patch.dict("os.environ", {}, clear=True)
class TestIntegrationErrorRecovery:
    \"\"\"Integration tests for error recovery and idempotent re-runs.

    Tests partial failure scenarios, continuation after errors, and
    idempotent batch processing.
    \"\"\"

    def test_partial_failure_continuation(
        self,
        tmp_path: Path,
        sample_export_content: Callable[[str], str],
        sample_session_content: Callable[[str], str],
    ) -> None:
        \"\"\"Test that collection continues after individual trial failures.

        Verifies script processes all exports even when some fail, enabling
        recovery of successful trials from a mixed batch.

        Args:
            tmp_path: Pytest fixture providing temporary directory for test files.
            sample_export_content: Pytest fixture providing factory for export content.
            sample_session_content: Pytest fixture providing factory for session content.
        \"\"\"
        # Setup directories
        exports_dir = tmp_path / "exports"
        destination_dir = tmp_path / "trials"
        session_dir = tmp_path / "sessions"
        exports_dir.mkdir()
        destination_dir.mkdir()
        session_dir.mkdir()

        # Trial 1: Success
        id_1 = "20260119-140000"
        uuid_1 = "uuid-success-1"
        (exports_dir / "export1.txt").write_text(sample_export_content(id_1))
        (session_dir / f"{uuid_1}.jsonl").write_text(sample_session_content(id_1))

        # Trial 2: Failure (missing session)
        id_2 = "20260119-141000"
        (exports_dir / "export2.txt").write_text(sample_export_content(id_2))

        # Trial 3: Success
        id_3 = "20260119-142000"
        uuid_3 = "uuid-success-3"
        (exports_dir / "export3.txt").write_text(sample_export_content(id_3))
        (session_dir / f"{uuid_3}.jsonl").write_text(sample_session_content(id_3))

        # Collect all three
        results = []
        for export_file in sorted(exports_dir.glob("*.txt")):
            # Extract workscope ID from export
            content = export_file.read_text()
            import re

            match = re.search(r"Workscope ID:?\\s*(?:Workscope-)?(\\d{8}-\\d{6})", content)
            if match:
                workscope_id = match.group(1)
                result = collect_single_trial(
                    workscope_id=workscope_id,
                    export_path=export_file,
                    session_dir=session_dir,
                    destination_dir=destination_dir,
                    verbose=False,
                )
                results.append(result)

        # Verify outcomes
        assert len(results) == 3
        assert results[0].status == "collected"  # Trial 1
        assert results[1].status == "failed"  # Trial 2
        assert results[2].status == "collected"  # Trial 3

        # Verify successful trials collected
        assert (destination_dir / id_1).exists()
        assert (destination_dir / id_3).exists()
        assert not (destination_dir / id_2).exists()

    def test_idempotent_rerun_after_success(
        self,
        tmp_path: Path,
        sample_export_content: Callable[[str], str],
        sample_session_content: Callable[[str], str],
    ) -> None:
        \"\"\"Test idempotent re-run produces zero collected on second run.

        Verifies that running collection twice with same inputs results in
        all trials being skipped on the second run.

        Args:
            tmp_path: Pytest fixture providing temporary directory for test files.
            sample_export_content: Pytest fixture providing factory for export content.
            sample_session_content: Pytest fixture providing factory for session content.
        \"\"\"
        # Setup directories
        exports_dir = tmp_path / "exports"
        destination_dir = tmp_path / "trials"
        session_dir = tmp_path / "sessions"
        exports_dir.mkdir()
        destination_dir.mkdir()
        session_dir.mkdir()

        # Create trial
        workscope_id = "20260119-150000"
        session_uuid = "uuid-idempotent"
        export_1 = exports_dir / "export-run1.txt"
        export_1.write_text(sample_export_content(workscope_id))
        (session_dir / f"{session_uuid}.jsonl").write_text(sample_session_content(workscope_id))

        # First run - should collect
        result_1 = collect_single_trial(
            workscope_id=workscope_id,
            export_path=export_1,
            session_dir=session_dir,
            destination_dir=destination_dir,
            verbose=False,
        )

        assert result_1.status == "collected"
        assert (destination_dir / workscope_id).exists()

        # Create new export with same Workscope ID for second run
        export_2 = exports_dir / "export-run2.txt"
        export_2.write_text(sample_export_content(workscope_id))

        # Second run - should skip
        result_2 = collect_single_trial(
            workscope_id=workscope_id,
            export_path=export_2,
            session_dir=session_dir,
            destination_dir=destination_dir,
            verbose=False,
        )

        assert result_2.status == "skipped"
        assert len(result_2.files_copied) == 0

    def test_rerun_after_partial_failure_collects_remaining(
        self,
        tmp_path: Path,
        sample_export_content: Callable[[str], str],
        sample_session_content: Callable[[str], str],
    ) -> None:
        \"\"\"Test that re-run after partial failure collects only remaining trials.

        Verifies recovery workflow where first run has failures, User fixes
        issues, and second run collects previously failed trials.

        Args:
            tmp_path: Pytest fixture providing temporary directory for test files.
            sample_export_content: Pytest fixture providing factory for export content.
            sample_session_content: Pytest fixture providing factory for session content.
        \"\"\"
        # Setup directories
        exports_dir = tmp_path / "exports"
        destination_dir = tmp_path / "trials"
        session_dir = tmp_path / "sessions"
        exports_dir.mkdir()
        destination_dir.mkdir()
        session_dir.mkdir()

        # Trial 1: Will succeed on first run
        id_1 = "20260119-160000"
        uuid_1 = "uuid-first-success"
        export_1 = exports_dir / "export1.txt"
        export_1.write_text(sample_export_content(id_1))
        (session_dir / f"{uuid_1}.jsonl").write_text(sample_session_content(id_1))

        # Trial 2: Will fail on first run (missing session)
        id_2 = "20260119-161000"
        export_2 = exports_dir / "export2.txt"
        export_2.write_text(sample_export_content(id_2))

        # First run
        result_1_run1 = collect_single_trial(
            workscope_id=id_1,
            export_path=export_1,
            session_dir=session_dir,
            destination_dir=destination_dir,
            verbose=False,
        )

        result_2_run1 = collect_single_trial(
            workscope_id=id_2,
            export_path=export_2,
            session_dir=session_dir,
            destination_dir=destination_dir,
            verbose=False,
        )

        # Verify first run outcomes
        assert result_1_run1.status == "collected"
        assert result_2_run1.status == "failed"

        # Now add missing session file for Trial 2
        uuid_2 = "uuid-second-success"
        (session_dir / f"{uuid_2}.jsonl").write_text(sample_session_content(id_2))

        # Second run (export2 still exists because failed collections don't delete)
        result_2_run2 = collect_single_trial(
            workscope_id=id_2,
            export_path=export_2,
            session_dir=session_dir,
            destination_dir=destination_dir,
            verbose=False,
        )

        # Verify second run collected the previously failed trial
        assert result_2_run2.status == "collected"
        assert (destination_dir / id_2).exists()
"""

# Append to test file
updated_content = content + remaining_classes
test_file.write_text(updated_content)

print("Successfully appended all remaining integration test classes")
