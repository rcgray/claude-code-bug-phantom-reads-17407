#!/usr/bin/env python
"""Extract structured trial data from Phantom Reads trial folder.

This script parses session JSONL files and chat exports to generate trial_data.json
with comprehensive metrics about context resets, file reads, token analysis,
persistence mapping, and derived context metrics.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

# Reset detection: minimum cache token drop to qualify as a context reset
_RESET_TOKEN_DROP_THRESHOLD = 10000

# Reset pattern classification boundaries (percentage of session)
_EARLY_MID_BOUNDARY_PCT = 50
_LATE_CLUSTER_THRESHOLD_PCT = 80
_LATE_BOUNDARY_PCT = 90


def extract_trial_data(trial_folder: Path) -> dict[str, Any]:
    """Extract all trial data from a trial folder.

    Parses session JSONL files and chat exports to produce a comprehensive
    trial_data.json with token progression (including full usage data from
    assistant messages), context resets, file reads, token analysis,
    persistence mapping (correlating tool-results files with file reads),
    and derived context metrics (initial_cache_read, total_input_at_peak,
    peak_cache_read).

    Args:
        trial_folder: Path to the trial directory containing chat export
            (.txt) and session (.jsonl) files.

    Returns:
        Dictionary containing all extracted trial data, structured per the
        trial_data.json schema.
    """
    meta = _extract_metadata(trial_folder)
    session = _parse_session_file(meta["session_file"])
    chat = _parse_chat_export(meta["chat_export_file"])
    metrics = _compute_derived_metrics(session, chat["context_snapshots"])

    # Token analysis
    token_analysis: dict[str, Any] = {"available": False, "token_counts_file": None}
    if meta["token_counts_data"]:
        print("Computing token analysis...")
        token_analysis = compute_token_analysis(
            session["file_reads"],
            session["resets"],
            meta["token_counts_data"],
            str(meta["token_counts_file"].resolve().relative_to(Path.cwd())),
            metrics["context_metrics"]["pre_operation_tokens"] or 0,
        )
        matched = len([r for r in token_analysis["reads_with_tokens"] if r["token_count"] > 0])
        print(f"  Matched {matched}/{len(session['file_reads'])} files to token counts")

    # Persistence mapping
    persistence_mapping = build_persistence_mapping(
        meta["uuid_dir"], meta["has_tool_results"], session["file_reads"]
    )
    print(
        f"  Persistence mapping: {persistence_mapping['persisted_count']} persisted, "
        f"{persistence_mapping['non_persisted_count']} non-persisted"
    )

    return {
        "schema_version": "1.3",
        "generated_at": datetime.now().isoformat(),
        "metadata": {
            "workscope_id": meta["workscope_id"],
            "session_uuid": meta["session_uuid"],
            "chat_export_file": meta["chat_export_file"].name,
            "session_file": meta["session_file"].name,
            "has_subagents": meta["has_subagents"],
            "has_tool_results": meta["has_tool_results"],
        },
        "outcome": {
            "self_reported": chat["self_reported"],
            "affected_files": chat["affected_files"],
            "notes": "PENDING_NLP",
        },
        "context_metrics": metrics["context_metrics"],
        "reset_analysis": metrics["reset_analysis"],
        "file_reads": metrics["file_reads_summary"],
        "persistence_mapping": persistence_mapping,
        "timeline": session["timeline"],
        "token_progression": session["token_progression"],
        "token_analysis": token_analysis,
    }


def _extract_metadata(trial_folder: Path) -> dict[str, Any]:
    """Validate trial folder and extract session metadata.

    Args:
        trial_folder: Path to the trial directory.

    Returns:
        Dictionary containing workscope_id, chat_export_file, session_file,
        session_uuid, uuid_dir, has_subagents, has_tool_results,
        token_counts_data, and token_counts_file.
    """
    workscope_id = trial_folder.name

    chat_files = list(trial_folder.glob("*.txt"))
    if not chat_files:
        raise FileNotFoundError(f"No chat export (.txt) found in {trial_folder}")
    chat_export_file = chat_files[0]

    jsonl_files = list(trial_folder.glob("*.jsonl"))
    if not jsonl_files:
        raise FileNotFoundError(f"No session file (.jsonl) found in {trial_folder}")
    session_file = jsonl_files[0]
    session_uuid = session_file.stem

    uuid_dir = trial_folder / session_uuid
    has_subagents = (uuid_dir / "subagents").exists() if uuid_dir.exists() else False
    has_tool_results = (uuid_dir / "tool-results").exists() if uuid_dir.exists() else False

    collection_dir = trial_folder.parent
    token_counts_file = collection_dir / "file_token_counts.json"
    token_counts_data = None
    if token_counts_file.exists():
        with token_counts_file.open() as f:
            token_counts_data = json.load(f)

    return {
        "workscope_id": workscope_id,
        "chat_export_file": chat_export_file,
        "session_file": session_file,
        "session_uuid": session_uuid,
        "uuid_dir": uuid_dir,
        "has_subagents": has_subagents,
        "has_tool_results": has_tool_results,
        "token_counts_data": token_counts_data,
        "token_counts_file": token_counts_file,
    }


def _unwrap_event(event: dict[str, Any]) -> tuple[Any, Any, dict[str, Any]]:
    """Extract role, content, and usage from a session event.

    Handles both Claude Code session format (wrapper with type/message keys)
    and API format (direct role/content).

    Args:
        event: A parsed JSONL event dict.

    Returns:
        Tuple of (role, content, usage).
    """
    event_type = event.get("type")
    if event_type in ("user", "assistant", "human"):
        message = event.get("message", {})
        if isinstance(message, dict):
            role = message.get("role", event_type)
            content = message.get("content", [])
            usage = message.get("usage", {})
        else:
            role = event_type
            content = event.get("content", [])
            usage = event.get("usage", {})
    else:
        role = event.get("role")
        content = event.get("content", [])
        usage = event.get("usage", {})
    return role, content, usage


def _process_user_event(
    content: Any,
    sequence_counter: int,
    line_num: int,
    tool_results_map: dict[str, Any],
    timeline: list[dict[str, Any]],
) -> None:
    """Process a user/human event, extracting tool results and timeline entries.

    Args:
        content: The message content (string, list of blocks, or other).
        sequence_counter: Current event sequence number.
        line_num: Session file line number.
        tool_results_map: Mutable map of tool_use_id to result content.
        timeline: Mutable timeline event list.
    """
    # Check for tool_result blocks
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                tool_use_id = block.get("tool_use_id")
                if tool_use_id is not None:
                    result_content = block.get("content", "")
                    tool_results_map[tool_use_id] = result_content

    # Extract text content for timeline
    if isinstance(content, str):
        text_content = content
        has_text = bool(text_content)
    elif isinstance(content, list):
        has_text = any(isinstance(b, dict) and b.get("type") == "text" for b in content)
        text_content = next(
            (b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"),
            "",
        )
    else:
        has_text = False
        text_content = ""

    if has_text:
        preview = text_content[:50]

        # Detect phase
        phase = None
        if "/wsd:init" in text_content:
            phase = "init"
        elif "/refine-plan" in text_content:
            phase = "trigger"
        elif "phantom read" in text_content.lower() or "persisted-output" in text_content:
            phase = "inquiry"

        timeline.append(
            {
                "sequence": sequence_counter,
                "type": "user_input",
                "session_line": line_num,
                "preview": preview,
                "phase": phase,
            }
        )


def _process_assistant_event(
    content: Any,
    usage: dict[str, Any],
    line_num: int,
    state: dict[str, Any],
) -> None:
    """Process an assistant event, tracking tokens, resets, and read operations.

    Args:
        content: The message content (typically a list of blocks).
        usage: Token usage data from the assistant message.
        line_num: Session file line number.
        state: Mutable parse state dict containing token_progression, resets,
            timeline, file_reads, usage_by_session_line, sequence_counter,
            last_cache_tokens, and batch_id.
    """
    cache_tokens = usage.get("cache_read_input_tokens")
    cache_creation_tokens = usage.get("cache_creation_input_tokens", 0)
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)

    # Track token progression
    if cache_tokens and cache_tokens > 0:
        total_input = cache_tokens + cache_creation_tokens + input_tokens
        state["token_progression"].append(
            {
                "sequence": len(state["token_progression"]) + 1,
                "cache_read_tokens": cache_tokens,
                "cache_creation_tokens": cache_creation_tokens,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_input": total_input,
                "session_line": line_num,
            }
        )

        state["usage_by_session_line"][line_num] = {
            "cache_read_tokens": cache_tokens,
            "cache_creation_tokens": cache_creation_tokens,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_input": total_input,
        }

        # Detect resets
        if state["last_cache_tokens"] is not None:
            if state["last_cache_tokens"] - cache_tokens > _RESET_TOKEN_DROP_THRESHOLD:
                state["resets"].append(
                    {
                        "from_tokens": state["last_cache_tokens"],
                        "to_tokens": cache_tokens,
                        "session_line": line_num,
                    }
                )
                state["timeline"].append(
                    {
                        "sequence": state["sequence_counter"],
                        "type": "context_reset",
                        "session_line": line_num,
                        "from_tokens": state["last_cache_tokens"],
                        "to_tokens": cache_tokens,
                    }
                )

        state["last_cache_tokens"] = cache_tokens

    # Track Read operations
    if isinstance(content, list):
        current_batch_files: list[dict[str, Any]] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                if block.get("name") == "Read":
                    tool_input = block.get("input", {})
                    file_path = tool_input.get("file_path", "")
                    tool_use_id = block.get("id", "")

                    current_batch_files.append(
                        {
                            "file_path": file_path,
                            "session_line": line_num,
                            "tool_use_id": tool_use_id,
                            "batch_id": state["batch_id"],
                        }
                    )

        if current_batch_files:
            state["file_reads"].extend(current_batch_files)
            state["timeline"].append(
                {
                    "sequence": state["sequence_counter"],
                    "type": "tool_batch",
                    "session_line": line_num,
                    "read_count": len(current_batch_files),
                    "files": [f["file_path"] for f in current_batch_files],
                }
            )
            state["batch_id"] += 1


def _resolve_read_results(
    file_reads: list[dict[str, Any]], tool_results_map: dict[str, Any]
) -> None:
    """Determine success/failure for each file read and assign sequence numbers.

    Args:
        file_reads: Mutable list of file read dicts to annotate.
        tool_results_map: Map of tool_use_id to result content strings.
    """
    for read in file_reads:
        tool_use_id = read["tool_use_id"]
        result_content = tool_results_map.get(tool_use_id, "")

        if "<tool_use_error>" in result_content:
            read["success"] = False
            match = re.search(r"<tool_use_error>(.*?)</tool_use_error>", result_content, re.DOTALL)
            if match:
                read["error"] = match.group(1).strip()
            else:
                read["error"] = "Unknown error"
        else:
            read["success"] = True

    for idx, read in enumerate(file_reads, 1):
        read["sequence"] = idx


def _parse_session_file(session_file: Path) -> dict[str, Any]:
    """Parse a session JSONL file into structured trial data.

    Reads each line of the session file, extracting token progression,
    context resets, file read operations, timeline events, and tool
    result mappings. Also resolves read success/failure from tool results.

    Args:
        session_file: Path to the session .jsonl file.

    Returns:
        Dictionary containing token_progression, resets, file_reads,
        timeline, usage_by_session_line, and sequence_counter.
    """
    print(f"Parsing session file ({session_file.stat().st_size // 1024}KB)...")

    state: dict[str, Any] = {
        "token_progression": [],
        "resets": [],
        "file_reads": [],
        "timeline": [],
        "tool_results_map": {},
        "usage_by_session_line": {},
        "sequence_counter": 0,
        "batch_id": 0,
        "last_cache_tokens": None,
    }
    line_num = 0

    with session_file.open() as f:
        for line_num, line in enumerate(f, 1):
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            state["sequence_counter"] += 1
            role, content, usage = _unwrap_event(event)

            if role in ("human", "user"):
                _process_user_event(
                    content,
                    state["sequence_counter"],
                    line_num,
                    state["tool_results_map"],
                    state["timeline"],
                )
            elif role == "assistant":
                _process_assistant_event(content, usage, line_num, state)

    _resolve_read_results(state["file_reads"], state["tool_results_map"])

    successful_reads = sum(1 for r in state["file_reads"] if r["success"])
    failed_reads = sum(1 for r in state["file_reads"] if not r["success"])
    print(f"  Processed {line_num} lines")
    print(f"  Found {len(state['token_progression'])} assistant messages with usage data")
    print(
        f"  Found {len(state['file_reads'])} Read operations "
        f"({successful_reads} successful, {failed_reads} failed)"
    )
    print(f"  Detected {len(state['resets'])} context resets")

    return {
        "token_progression": state["token_progression"],
        "resets": state["resets"],
        "file_reads": state["file_reads"],
        "timeline": state["timeline"],
        "usage_by_session_line": state["usage_by_session_line"],
        "sequence_counter": state["sequence_counter"],
    }


def _parse_chat_export(chat_export_file: Path) -> dict[str, Any]:
    """Parse a chat export file for context snapshots and outcome data.

    Args:
        chat_export_file: Path to the chat export .txt file.

    Returns:
        Dictionary containing context_snapshots, self_reported, and
        affected_files.
    """
    print("Parsing chat export...")

    context_snapshots: list[dict[str, int]] = []
    # Outcome and notes fields are populated by the executing agent via NLP analysis
    # of the chat export. The script outputs placeholder values for agent processing.
    self_reported = "PENDING_NLP"
    affected_files: list[str] = []

    with chat_export_file.open() as f:
        chat_text = f.read()

        # Extract context snapshots
        for match in re.finditer(r"(\d+)k/\d+k tokens \((\d+)%\)", chat_text):
            tokens = int(match.group(1)) * 1000
            percent = int(match.group(2))
            context_snapshots.append({"tokens": tokens, "percent": percent})

    print(f"  Found {len(context_snapshots)} context snapshots")
    print(f"  Outcome: {self_reported}")

    return {
        "context_snapshots": context_snapshots,
        "self_reported": self_reported,
        "affected_files": affected_files,
    }


def _compute_derived_metrics(
    session: dict[str, Any],
    context_snapshots: list[dict[str, int]],
) -> dict[str, Any]:
    """Compute derived metrics from parsed session and chat data.

    Calculates pre/post operation token counts, enriches reset events with
    position and usage data, classifies the reset pattern, computes file
    read statistics, and derives token progression summary metrics.

    Args:
        session: Parsed session data from _parse_session_file, containing
            timeline, resets, file_reads, sequence_counter,
            usage_by_session_line, and token_progression.
        context_snapshots: Context snapshots from chat export.

    Returns:
        Dictionary containing context_metrics, reset_analysis, and
        file_reads_summary sections ready for output assembly.
    """
    print("Computing metrics...")

    timeline = session["timeline"]
    resets = session["resets"]
    file_reads = session["file_reads"]
    sequence_counter = session["sequence_counter"]
    usage_by_session_line = session["usage_by_session_line"]
    token_progression = session["token_progression"]

    # Find pre/post operation tokens
    pre_operation_tokens = None
    pre_operation_percent = None
    post_operation_tokens = None
    post_operation_percent = None

    trigger_event = next((e for e in timeline if e.get("phase") == "trigger"), None)
    if trigger_event and context_snapshots:
        # Find snapshot before trigger
        for snapshot in context_snapshots:
            if pre_operation_tokens is None:
                pre_operation_tokens = snapshot["tokens"]
                pre_operation_percent = snapshot["percent"]

        # Post-operation is the last snapshot
        if context_snapshots:
            post_operation_tokens = context_snapshots[-1]["tokens"]
            post_operation_percent = context_snapshots[-1]["percent"]

    headroom = (200000 - pre_operation_tokens) if pre_operation_tokens else None

    # Enrich resets with position and usage data
    total_events = sequence_counter
    for _, reset in enumerate(resets, 1):
        reset["sequence_position"] = reset["session_line"]
        reset["total_events"] = total_events
        reset["position_percent"] = (reset["session_line"] / total_events) * 100

        # Enrich with usage data at the reset point
        usage_at_reset = usage_by_session_line[reset["session_line"]]
        reset["cache_creation_at_reset"] = usage_at_reset["cache_creation_tokens"]
        reset["total_input_at_reset"] = usage_at_reset["total_input"]
        reset["compaction_loss"] = reset["from_tokens"] - (
            reset["to_tokens"] + reset["cache_creation_at_reset"]
        )

    reset_positions_percent = [r["position_percent"] for r in resets]
    pattern = classify_reset_pattern(resets, total_events)

    # File read stats
    unique_files = list({r["file_path"] for r in file_reads if r["success"]})
    successful_reads = sum(1 for r in file_reads if r["success"])
    failed_reads = sum(1 for r in file_reads if not r["success"])
    failed_read_list = [
        {
            "sequence": r["sequence"],
            "file_path": r["file_path"],
            "error": r.get("error", "Unknown error"),
        }
        for r in file_reads
        if not r["success"]
    ]

    print(f"  Pattern: {pattern}")
    print(f"  Unique files: {len(unique_files)}")

    # Token progression derived metrics
    initial_cache_read = token_progression[0]["cache_read_tokens"] if token_progression else None
    total_input_at_peak = (
        max(entry["total_input"] for entry in token_progression) if token_progression else None
    )
    peak_cache_read = (
        max(entry["cache_read_tokens"] for entry in token_progression)
        if token_progression
        else None
    )

    return {
        "context_metrics": {
            "pre_operation_tokens": pre_operation_tokens,
            "pre_operation_percent": pre_operation_percent,
            "post_operation_tokens": post_operation_tokens,
            "post_operation_percent": post_operation_percent,
            "headroom_at_trigger": headroom,
            "context_window_size": 200000,
            "initial_cache_read": initial_cache_read,
            "total_input_at_peak": total_input_at_peak,
            "peak_cache_read": peak_cache_read,
        },
        "reset_analysis": {
            "total_resets": len(resets),
            "reset_positions_percent": reset_positions_percent,
            "pattern_classification": pattern,
            "resets": resets,
        },
        "file_reads_summary": {
            "total_operations": len(file_reads),
            "successful_operations": successful_reads,
            "failed_operations": failed_reads,
            "unique_files": len(unique_files),
            "unique_file_list": sorted(unique_files),
            "failed_reads": failed_read_list,
            "reads": file_reads,
        },
    }


def build_persistence_mapping(
    uuid_dir: Path, has_tool_results: bool, file_reads: list[dict[str, Any]]
) -> dict[str, Any]:
    """Build persistence mapping from tool-results directory and file reads.

    Enumerates persisted tool-result files and cross-references them against
    file_reads entries to categorize each into persisted_reads,
    non_persisted_reads, or persisted_non_reads.

    Args:
        uuid_dir: Path to the session subdirectory (may not exist).
        has_tool_results: Whether a tool-results/ directory exists.
        file_reads: List of file read entries with tool_use_id fields.

    Returns:
        Dictionary containing the persistence_mapping section with
        persisted_tool_ids, persisted_count, non_persisted_count,
        persisted_reads, non_persisted_reads, and persisted_non_reads.
    """
    tool_results_dir = uuid_dir / "tool-results" if uuid_dir.exists() else None

    if not has_tool_results or tool_results_dir is None or not tool_results_dir.exists():
        # No persistence: all file reads are non-persisted
        non_persisted_reads = [
            {
                "sequence": r["sequence"],
                "file_path": r["file_path"],
                "tool_use_id": r["tool_use_id"],
            }
            for r in file_reads
        ]
        return {
            "persisted_tool_ids": [],
            "persisted_count": 0,
            "non_persisted_count": len(non_persisted_reads),
            "persisted_reads": [],
            "non_persisted_reads": non_persisted_reads,
            "persisted_non_reads": [],
        }

    # Enumerate tool-results files and extract tool IDs
    persisted_tool_ids = sorted(f.stem for f in tool_results_dir.iterdir() if f.suffix == ".txt")
    persisted_id_set = set(persisted_tool_ids)

    # Build lookup of file_reads by tool_use_id
    reads_by_tool_id: dict[str, dict[str, Any]] = {r["tool_use_id"]: r for r in file_reads}

    # Cross-reference: persisted reads vs persisted non-reads
    persisted_reads = []
    persisted_non_reads = []
    for tool_id in persisted_tool_ids:
        if tool_id in reads_by_tool_id:
            read = reads_by_tool_id[tool_id]
            persisted_reads.append(
                {
                    "sequence": read["sequence"],
                    "file_path": read["file_path"],
                    "tool_use_id": tool_id,
                }
            )
        else:
            persisted_non_reads.append(tool_id)

    # Non-persisted reads: file_reads whose tool_use_id is NOT in persisted set
    non_persisted_reads = [
        {
            "sequence": r["sequence"],
            "file_path": r["file_path"],
            "tool_use_id": r["tool_use_id"],
        }
        for r in file_reads
        if r["tool_use_id"] not in persisted_id_set
    ]

    return {
        "persisted_tool_ids": persisted_tool_ids,
        "persisted_count": len(persisted_reads) + len(persisted_non_reads),
        "non_persisted_count": len(non_persisted_reads),
        "persisted_reads": persisted_reads,
        "non_persisted_reads": non_persisted_reads,
        "persisted_non_reads": persisted_non_reads,
    }


def classify_reset_pattern(resets: list[dict[str, Any]], total_events: int) -> str:
    """Classify the reset pattern based on position within the session.

    Categorizes the distribution of context resets into named patterns
    (e.g., SINGLE_EARLY, EARLY_PLUS_LATE, LATE_CLUSTERED) used for
    predicting phantom read outcomes.

    Args:
        resets: List of reset event dicts, each containing a "session_line" key.
        total_events: Total number of events in the session, used to compute
            position percentages.

    Returns:
        A string label for the reset pattern (e.g., "NO_RESETS", "SINGLE_EARLY",
        "SINGLE_LATE", "LATE_CLUSTERED", "EARLY_PLUS_LATE", "EARLY_PLUS_MID_LATE",
        "OTHER").
    """
    if not resets:
        return "NO_RESETS"

    positions = [(r["session_line"] / total_events) * 100 for r in resets]

    if len(positions) == 1:
        return "SINGLE_EARLY" if positions[0] < _EARLY_MID_BOUNDARY_PCT else "SINGLE_LATE"

    # All resets late
    if all(p > _LATE_CLUSTER_THRESHOLD_PCT for p in positions):
        return "LATE_CLUSTERED"

    # Early + late pattern
    if positions[0] < _EARLY_MID_BOUNDARY_PCT and positions[-1] > _LATE_BOUNDARY_PCT:
        # Check for mid-session resets
        mid_resets = [
            p for p in positions[1:-1] if _EARLY_MID_BOUNDARY_PCT <= p <= _LATE_BOUNDARY_PCT
        ]
        if not mid_resets:
            return "EARLY_PLUS_LATE"
        return "EARLY_PLUS_MID_LATE"

    return "OTHER"


def compute_token_analysis(
    file_reads: list[dict[str, Any]],
    resets: list[dict[str, Any]],
    token_counts_data: dict[str, Any],
    token_counts_file: str,
    pre_operation_tokens: int,
) -> dict[str, Any]:
    """Compute token-based analysis of file reads and context resets.

    Cross-references file reads against known token counts to produce
    cumulative token estimates and annotates resets with surrounding
    read context.

    Args:
        file_reads: List of file read dicts with "success", "sequence",
            "file_path", and "session_line" keys.
        resets: List of reset event dicts with "session_line" keys.
        token_counts_data: Parsed file_token_counts.json with a
            "project_files" mapping of relative paths to token counts.
        token_counts_file: Relative path to the token counts JSON file,
            recorded in the output for provenance.
        pre_operation_tokens: Baseline token count before file read
            operations began.

    Returns:
        Dictionary containing token analysis results with "available",
        "token_counts_file", "statistics", "reads_with_tokens", and
        "resets_with_context" keys.
    """
    project_files = token_counts_data.get("project_files", {})

    reads_with_tokens = []
    cumulative = pre_operation_tokens

    for read in file_reads:
        if not read["success"]:
            continue

        file_path = read["file_path"]

        # Normalize path
        rel_path = None
        for pattern in [
            "/Users/gray/Projects/claude-bug/",
            "/Users/gray/Projects/claude-code-bug-phantom-reads-17407/",
        ]:
            if pattern in file_path:
                rel_path = file_path.split(pattern, 1)[1]
                break

        # Look up token count
        token_count = 0
        if rel_path and rel_path in project_files:
            token_count = project_files[rel_path]

        cumulative += token_count

        reads_with_tokens.append(
            {
                "sequence": read["sequence"],
                "file_path": rel_path or file_path,
                "token_count": token_count,
                "cumulative_estimate": cumulative,
                "session_line": read["session_line"],
            }
        )

    # Annotate resets with context
    resets_with_context = []
    for idx, reset in enumerate(resets, 1):
        reset_line = reset["session_line"]

        # Find last read before this reset
        last_read = None
        for read_with_tokens in reversed(reads_with_tokens):
            if read_with_tokens["session_line"] < reset_line:
                last_read = read_with_tokens
                break

        resets_with_context.append(
            {
                "reset_sequence": idx,
                "session_line": reset_line,
                "cumulative_tokens_before": last_read["cumulative_estimate"]
                if last_read
                else pre_operation_tokens,
                "last_file_read": last_read["file_path"] if last_read else None,
                "last_file_tokens": last_read["token_count"] if last_read else None,
            }
        )

    # Compute statistics
    known_tokens = [r["token_count"] for r in reads_with_tokens if r["token_count"] > 0]

    total_tokens_read = sum(known_tokens)
    largest_file_tokens = max(known_tokens) if known_tokens else 0
    largest_file = None
    if largest_file_tokens > 0:
        largest_file = next(
            (r["file_path"] for r in reads_with_tokens if r["token_count"] == largest_file_tokens),
            None,
        )

    unknown_count = sum(1 for r in reads_with_tokens if r["token_count"] == 0)

    return {
        "available": True,
        "token_counts_file": token_counts_file,
        "statistics": {
            "total_tokens_read": total_tokens_read,
            "largest_file_tokens": largest_file_tokens,
            "largest_file_path": largest_file or "",
            "unknown_token_files": unknown_count,
        },
        "reads_with_tokens": reads_with_tokens,
        "resets_with_context": resets_with_context,
    }


def _format_changed_key(key: str, existing: dict[str, Any], new: dict[str, Any]) -> str:
    """Format a change description for a key that differs between data versions.

    Args:
        key: The top-level key that changed.
        existing: Previously saved trial_data.json contents.
        new: Newly extracted trial data.

    Returns:
        A formatted change description string.
    """
    detail = ""
    if key == "schema_version":
        detail = f"({existing[key]} → {new[key]})"
    elif key == "outcome":
        old_status = existing[key].get("self_reported", "UNKNOWN")
        new_status = new[key].get("self_reported", "UNKNOWN")
        if old_status != new_status:
            detail = f"(self_reported: {old_status} → {new_status})"
    elif key == "reset_analysis":
        old_resets = existing[key].get("total_resets", 0)
        new_resets = new[key].get("total_resets", 0)
        if old_resets != new_resets:
            detail = f"(total_resets: {old_resets} → {new_resets})"
    elif key == "token_analysis" and new[key].get("available"):
        reads = len(new[key].get("reads_with_tokens", []))
        resets_count = len(new[key].get("resets_with_context", []))
        detail = f"({reads} reads with tokens, {resets_count} resets with context)"

    suffix = f" {detail}" if detail else ""
    return f"  - {key}: UPDATED{suffix}"


def compare_data(existing: dict[str, Any], new: dict[str, Any]) -> list[str]:
    """Compare existing and new trial data, returning a list of changes.

    Performs a key-by-key comparison between previously saved and newly
    extracted trial data, producing human-readable change descriptions
    for each top-level key.

    Args:
        existing: Previously saved trial_data.json contents.
        new: Newly extracted trial data to compare against.

    Returns:
        List of human-readable change description strings, one per
        top-level key (e.g., "  - schema_version: UPDATED (1.2 -> 1.3)").
    """
    changes = []

    all_keys = set(existing.keys()) | set(new.keys())

    for key in sorted(all_keys):
        if key not in existing:
            changes.append(f"  - {key}: NEW")
        elif key not in new:
            changes.append(f"  - {key}: REMOVED")
        elif existing[key] != new[key]:
            changes.append(_format_changed_key(key, existing, new))
        else:
            changes.append(f"  - {key}: UNCHANGED")

    return changes


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:  # noqa: PLR2004
        print("Usage: python extract_trial_data.py <trial-folder-path>")
        sys.exit(1)

    trial_folder = Path(sys.argv[1])

    if not trial_folder.exists():
        print(f"Error: Trial folder not found: {trial_folder}")
        sys.exit(1)

    print("Validating trial folder...")

    try:
        # Extract data
        new_data = extract_trial_data(trial_folder)

        # Check for existing file
        output_file = trial_folder / "trial_data.json"
        existing_data = None

        if output_file.exists():
            print("\nChecking for existing trial_data.json... Found")
            with output_file.open() as f:
                existing_data = json.load(f)
        else:
            print("\nChecking for existing trial_data.json... Not found")

        # Compare if existing
        if existing_data:
            print("\nChanges to trial_data.json:")
            changes = compare_data(existing_data, new_data)
            for change in changes:
                print(change)
        else:
            print("\nCreating new trial_data.json with all sections.")

        # Write output
        with output_file.open("w") as f:
            json.dump(new_data, f, indent=2)

        # Report summary
        metadata = new_data["metadata"]
        outcome = new_data["outcome"]
        context_metrics = new_data["context_metrics"]
        reset_analysis = new_data["reset_analysis"]
        file_reads_data = new_data["file_reads"]
        token_analysis = new_data["token_analysis"]

        print("\n" + "=" * 50)
        print("Trial Data Extraction Complete")
        print("=" * 50)
        print(f"Trial: {metadata['workscope_id']}")
        print(f"Session: {metadata['session_uuid']}")
        print()
        print(f"Outcome: {outcome['self_reported']}")
        print()
        print("Context Metrics:")
        if context_metrics["pre_operation_tokens"]:
            print(
                f"  Pre-operation:  {context_metrics['pre_operation_tokens'] // 1000}K tokens ({context_metrics['pre_operation_percent']}%)"
            )
            print(
                f"  Post-operation: {context_metrics['post_operation_tokens'] // 1000}K tokens ({context_metrics['post_operation_percent']}%)"
            )
            print(f"  Headroom:       {context_metrics['headroom_at_trigger'] // 1000}K tokens")
        else:
            print("  Not available")
        print()
        print("Reset Analysis:")
        print(f"  Total resets: {reset_analysis['total_resets']}")
        print(f"  Pattern: {reset_analysis['pattern_classification']}")
        if reset_analysis["reset_positions_percent"]:
            positions = ", ".join(f"{p:.0f}%" for p in reset_analysis["reset_positions_percent"])
            print(f"  Positions: {positions}")
        print()
        print("File Reads:")
        print(
            f"  Total operations: {file_reads_data['total_operations']} ({file_reads_data['successful_operations']} successful, {file_reads_data['failed_operations']} failed)"
        )
        print(f"  Unique files: {file_reads_data['unique_files']}")
        print()

        if token_analysis["available"]:
            stats = token_analysis["statistics"]
            print("Token Analysis: AVAILABLE")
            print(f"  Total tokens read: {stats['total_tokens_read']:,}")
            print(
                f"  Largest file: {stats['largest_file_path']} ({stats['largest_file_tokens']:,} tokens)"
            )
            print(f"  Unknown files: {stats['unknown_token_files']}")
        else:
            print("Token Analysis: NOT AVAILABLE")
            print("  (No file_token_counts.json found in collection directory)")
        print()
        print(f"Timeline Events: {len(new_data['timeline'])}")
        print()
        print(f"Output: {output_file}")
        print(f"Status: {'UPDATED' if existing_data else 'CREATED'}")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
