


@patch.dict("os.environ", {}, clear=True)
class TestIntegrationMultipleTrials:
    """Integration tests for batch collection with mixed outcomes.

    Tests scenarios with multiple trials having different outcomes including
    successful collection, skipped duplicates, and missing session files.
    """

    def test_batch_collection_with_mixed_outcomes(
        self,
        tmp_path: Path,
        sample_export_content: Callable[[str], str],
        sample_session_content: Callable[[str], str],
    ) -> None:
        """Test batch collection with successful, skipped, and failed trials.

        Verifies script continues processing after individual trial failures
        and correctly tracks counts for each outcome type.

        Args:
            tmp_path: Pytest fixture providing temporary directory for test files.
            sample_export_content: Pytest fixture providing factory for export content.
            sample_session_content: Pytest fixture providing factory for session content.
        """
        # Setup directories
        exports_dir = tmp_path / "exports"
        destination_dir = tmp_path / "trials"
        session_dir = tmp_path / "sessions"
        exports_dir.mkdir()
        destination_dir.mkdir()
        session_dir.mkdir()

        # Trial 1: Will succeed
        workscope_1 = "20260119-110000"
        session_1 = "uuid-trial-1"
        (exports_dir / "trial1.txt").write_text(sample_export_content(workscope_1))
        (session_dir / f"{session_1}.jsonl").write_text(sample_session_content(workscope_1))

        # Trial 2: Will skip (already exists)
        workscope_2 = "20260119-111000"
        session_2 = "uuid-trial-2"
        (exports_dir / "trial2.txt").write_text(sample_export_content(workscope_2))
        (session_dir / f"{session_2}.jsonl").write_text(sample_session_content(workscope_2))
        # Pre-create trial directory
        (destination_dir / workscope_2).mkdir()

        # Trial 3: Will fail (no session file)
        workscope_3 = "20260119-112000"
        (exports_dir / "trial3.txt").write_text(sample_export_content(workscope_3))
        # No session file created

        # Execute collections
        result_1 = collect_single_trial(
            workscope_id=workscope_1,
            export_path=exports_dir / "trial1.txt",
            session_dir=session_dir,
            destination_dir=destination_dir,
            verbose=False,
        )

        result_2 = collect_single_trial(
            workscope_id=workscope_2,
            export_path=exports_dir / "trial2.txt",
            session_dir=session_dir,
            destination_dir=destination_dir,
            verbose=False,
        )

        result_3 = collect_single_trial(
            workscope_id=workscope_3,
            export_path=exports_dir / "trial3.txt",
            session_dir=session_dir,
            destination_dir=destination_dir,
            verbose=False,
        )

        # Verify results
        assert result_1.status == "collected"
        assert result_1.error is None

        assert result_2.status == "skipped"
        assert result_2.error is None

        assert result_3.status == "failed"
        assert result_3.error is not None
        assert "No session file found" in result_3.error

        # Verify trial directories
        assert (destination_dir / workscope_1).exists()
        assert (destination_dir / workscope_2).exists()
        assert not (destination_dir / workscope_3).exists()

        # Verify export cleanup
        assert not (exports_dir / "trial1.txt").exists()  # Collected
        assert not (exports_dir / "trial2.txt").exists()  # Skipped
        assert (exports_dir / "trial3.txt").exists()  # Failed (not deleted)

    def test_multiple_exports_same_workscope_id(
        self,
        tmp_path: Path,
        sample_export_content: Callable[[str], str],
        sample_session_content: Callable[[str], str],
    ) -> None:
        """Test handling of duplicate Workscope ID in multiple exports.

        Verifies that second export with same Workscope ID is skipped due to
        existing trial directory.

        Args:
            tmp_path: Pytest fixture providing temporary directory for test files.
            sample_export_content: Pytest fixture providing factory for export content.
            sample_session_content: Pytest fixture providing factory for session content.
        """
        # Setup directories
        exports_dir = tmp_path / "exports"
        destination_dir = tmp_path / "trials"
        session_dir = tmp_path / "sessions"
        exports_dir.mkdir()
        destination_dir.mkdir()
        session_dir.mkdir()

        # Same Workscope ID, different export files
        workscope_id = "20260119-120000"
        session_uuid = "uuid-duplicate"

        export_1 = exports_dir / "export-first.txt"
        export_1.write_text(sample_export_content(workscope_id))

        export_2 = exports_dir / "export-second.txt"
        export_2.write_text(sample_export_content(workscope_id))

        # Session file
        (session_dir / f"{session_uuid}.jsonl").write_text(sample_session_content(workscope_id))

        # Collect first export
        result_1 = collect_single_trial(
            workscope_id=workscope_id,
            export_path=export_1,
            session_dir=session_dir,
            destination_dir=destination_dir,
            verbose=False,
        )

        # Collect second export (should skip)
        result_2 = collect_single_trial(
            workscope_id=workscope_id,
            export_path=export_2,
            session_dir=session_dir,
            destination_dir=destination_dir,
            verbose=False,
        )

        # Verify results
        assert result_1.status == "collected"
        assert result_2.status == "skipped"

        # Verify only one trial directory
        assert (destination_dir / workscope_id).exists()

        # Verify first export deleted, second also deleted on skip
        assert not export_1.exists()
        assert not export_2.exists()
