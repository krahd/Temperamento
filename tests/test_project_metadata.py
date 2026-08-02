import re
import tomllib
from pathlib import Path

import temperamento

ROOT = Path(__file__).resolve().parents[1]


def test_version_is_consistent_across_package_and_citation_metadata() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    citation_version = re.search(r"^version:\s*(\S+)\s*$", citation, re.MULTILINE)
    assert citation_version is not None
    assert pyproject["project"]["version"] == temperamento.__version__
    assert citation_version.group(1) == temperamento.__version__


def test_public_authorship_is_tomas_laurenzo_only() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["authors"] == [{"name": "Tomas Laurenzo"}]

    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    assert "family-names: Laurenzo" in citation
    assert "given-names: Tomas" in citation
    assert "Valeria" not in citation
    assert "Rocha" not in citation
