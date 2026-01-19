
    def test_collect_single_trial_hybrid_structure(
        self,
        tmp_path: Path,
        sample_export_content: Callable[[str], str],
        sample_session_content: Callable[[str], str],
    ) -> None:
        """Test end-to-end collection of single trial with hybrid session structure.

        Verifies collection with session subdirectory containing tool-results
        while agent files remain at root level.

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

        # Create export file
        workscope_id = "20260119-102000"
        session_uuid = "def456-hybrid"
        export_file = exports_dir / "hybrid-trial.txt"
        export_file.write_text(sample_export_content(workscope_id))

        # Create hybrid session structure
        main_session = session_dir / f"{session_uuid}.jsonl"
        main_session.write_text(sample_session_content(workscope_id))

        # Session subdirectory with tool-results
        session_subdir = session_dir / session_uuid
        session_subdir.mkdir()
        tool_results_dir = session_subdir / "tool-results"
        tool_results_dir.mkdir()
        (tool_results_dir / "toolu_001.txt").write_text("Tool output 1")
        (tool_results_dir / "toolu_002.txt").write_text("Tool output 2")

        # Agent files at root level
        agent1 = session_dir / "agent-100.jsonl"
        agent1.write_text(f'{{"sessionId": "{session_uuid}"}}\n')

        # Execute collection
        result = collect_single_trial(
            workscope_id=workscope_id,
            export_path=export_file,
            session_dir=session_dir,
            destination_dir=destination_dir,
            verbose=False,
        )

        # Verify result
        assert result.status == "collected"
        assert result.error is None

        # Verify trial directory structure
        trial_dir = destination_dir / workscope_id
        assert trial_dir.exists()
        assert (trial_dir / f"{workscope_id}.txt").exists()
        assert (trial_dir / f"{session_uuid}.jsonl").exists()
        assert (trial_dir / session_uuid / "tool-results" / "toolu_001.txt").exists()
        assert (trial_dir / session_uuid / "tool-results" / "toolu_002.txt").exists()
        assert (trial_dir / "agent-100.jsonl").exists()

        # Verify export was deleted
        assert not export_file.exists()

    def test_collect_single_trial_hierarchical_structure(
        self,
        tmp_path: Path,
        sample_export_content: Callable[[str], str],
        sample_session_content: Callable[[str], str],
    ) -> None:
        """Test end-to-end collection of single trial with hierarchical session structure.

        Verifies collection with all content in session subdirectory including
        both subagents and tool-results.

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

        # Create export file
        workscope_id = "20260119-103000"
        session_uuid = "ghi789-hierarchical"
        export_file = exports_dir / "hierarchical-trial.txt"
        export_file.write_text(sample_export_content(workscope_id))

        # Create hierarchical session structure
        main_session = session_dir / f"{session_uuid}.jsonl"
        main_session.write_text(sample_session_content(workscope_id))

        # Session subdirectory with subagents and tool-results
        session_subdir = session_dir / session_uuid
        session_subdir.mkdir()

        subagents_dir = session_subdir / "subagents"
        subagents_dir.mkdir()
        (subagents_dir / "agent-200.jsonl").write_text("agent content")
        (subagents_dir / "agent-201.jsonl").write_text("agent content")

        tool_results_dir = session_subdir / "tool-results"
        tool_results_dir.mkdir()
        (tool_results_dir / "toolu_010.txt").write_text("Tool output")

        # Execute collection
        result = collect_single_trial(
            workscope_id=workscope_id,
            export_path=export_file,
            session_dir=session_dir,
            destination_dir=destination_dir,
            verbose=False,
        )

        # Verify result
        assert result.status == "collected"
        assert result.error is None

        # Verify trial directory structure
        trial_dir = destination_dir / workscope_id
        assert trial_dir.exists()
        assert (trial_dir / f"{workscope_id}.txt").exists()
        assert (trial_dir / f"{session_uuid}.jsonl").exists()
        assert (trial_dir / session_uuid / "subagents" / "agent-200.jsonl").exists()
        assert (trial_dir / session_uuid / "subagents" / "agent-201.jsonl").exists()
        assert (trial_dir / session_uuid / "tool-results" / "toolu_010.txt").exists()

        # Verify no root-level agent files (harmless search in hierarchical)
        assert not (trial_dir / "agent-200.jsonl").exists()

        # Verify export was deleted
        assert not export_file.exists()
