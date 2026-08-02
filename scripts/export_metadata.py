from __future__ import annotations

import io
import json
import re
import subprocess
import sys
from pathlib import Path

import coverage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from temperamento import __version__
from temperamento.opcodes import assigned_opcodes, topology_table

_COLLECTED_LINE = re.compile(r"^.+:\s+(\d+)$")


def _collect_count(nodeid: str | None = None) -> int:
    command = [sys.executable, "-m", "pytest", "--collect-only", "-q"]
    if nodeid is not None:
        command.append(nodeid)
    completed = subprocess.run(command, cwd=ROOT, check=True, text=True, capture_output=True)
    counts = [
        int(match.group(1))
        for line in completed.stdout.splitlines()
        if (match := _COLLECTED_LINE.fullmatch(line.strip()))
    ]
    if not counts:
        target = nodeid or "the test suite"
        raise RuntimeError(f"could not derive the collected pytest case count for {target}")
    return sum(counts)


def _coverage_percent() -> int:
    data_file = ROOT / ".coverage"
    if not data_file.exists():
        raise RuntimeError("coverage data is missing; run the coverage target before metadata")
    cov = coverage.Coverage(data_file=str(data_file))
    cov.load()
    return round(cov.report(file=io.StringIO(), skip_empty=True))


def _count_showcase_directories() -> int:
    root = ROOT / "examples" / "showcase"
    return sum(
        1
        for path in root.rglob("*.musicxml")
        if path.parent.name != "twelve-transpositions" and "twelve-transpositions" not in path.parts
    )


def _count_transposition_variants() -> int:
    root = ROOT / "examples" / "showcase" / "twelve-transpositions"
    return sum(1 for path in root.glob("key-*/*.musicxml") if path.is_file())


def main() -> None:
    topology = topology_table()
    (ROOT / "spec" / "opcode-table.json").write_text(
        json.dumps(topology, indent=2) + "\n", encoding="utf-8"
    )
    assigned = len(assigned_opcodes())
    metrics = {
        "release": __version__,
        "topology_cells": len(topology),
        "assigned_opcodes": assigned,
        "reserved_cells": len(topology) - assigned,
        "cell_recognition_cases": _collect_count(
            "tests/test_harmony.py::test_every_harmonic_cell_decodes"
        ),
        "abstract_transposition_cases": _collect_count(
            "tests/test_harmony.py::test_global_transposition_preserves_cell"
        ),
        "recognition_transposition_voicing_cases": _collect_count(
            "tests/test_harmony.py::test_recognition_with_voicing_transformations_preserves_cell"
        ),
        "end_to_end_assigned_cell_cases": _collect_count(
            "tests/test_end_to_end_topology.py::test_every_assigned_cell_compiles_end_to_end"
        ),
        "whole_program_transposition_cases": _collect_count(
            "tests/test_examples.py::test_whole_score_transposition_preserves_program_and_result"
        ),
        "committed_transposition_variants": _count_transposition_variants(),
        "showcase_compositions": _count_showcase_directories(),
        "tutorial_examples": len(list((ROOT / "examples" / "tutorial").glob("*/*.musicxml"))),
        "collected_tests": _collect_count(),
        "branch_coverage_percent": _coverage_percent(),
    }
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
