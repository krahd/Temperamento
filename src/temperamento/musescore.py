from __future__ import annotations

import os
import platform
import shutil
import subprocess
import tempfile
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from .errors import IntegrationError

_NATIVE_SUFFIXES = {".mscz", ".mscx"}
_MUSICXML_SUFFIXES = {".musicxml", ".xml", ".mxl"}


@dataclass(frozen=True)
class MuseScoreInstallation:
    executable: Path
    version: str | None

    @property
    def available(self) -> bool:
        return self.executable.is_file()


def _candidate_paths() -> list[Path]:
    candidates: list[Path] = []
    explicit = os.environ.get("TEMPERAMENTO_MUSESCORE")
    if explicit:
        candidates.append(Path(explicit).expanduser())

    for name in (
        "mscore",
        "musescore",
        "MuseScore4",
        "MuseScore4.exe",
        "mscore4portable",
    ):
        found = shutil.which(name)
        if found:
            candidates.append(Path(found))

    system = platform.system()
    if system == "Darwin":
        candidates.extend(
            [
                Path("/Applications/MuseScore 4.app/Contents/MacOS/mscore"),
                Path("/Applications/MuseScore Studio 4.app/Contents/MacOS/mscore"),
                Path.home() / "Applications/MuseScore 4.app/Contents/MacOS/mscore",
                Path.home() / "Applications/MuseScore Studio 4.app/Contents/MacOS/mscore",
            ]
        )
    elif system == "Windows":
        for root_name in ("PROGRAMFILES", "PROGRAMFILES(X86)"):
            root = os.environ.get(root_name)
            if root:
                candidates.extend(
                    [
                        Path(root) / "MuseScore 4/bin/MuseScore4.exe",
                        Path(root) / "MuseScore Studio 4/bin/MuseScore4.exe",
                    ]
                )
    else:
        candidates.extend(
            [
                Path("/usr/bin/mscore"),
                Path("/usr/bin/musescore"),
                Path("/usr/local/bin/mscore"),
                Path("/app/bin/mscore"),
            ]
        )

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key not in seen:
            unique.append(candidate)
            seen.add(key)
    return unique


def _run(
    command: Sequence[str | os.PathLike[str]],
    *,
    timeout: int = 120,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(
            [os.fspath(part) for part in command],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except OSError as exc:
        raise IntegrationError(f"cannot start MuseScore Studio: {exc}") from exc
    except subprocess.TimeoutExpired as exc:
        raise IntegrationError("MuseScore Studio did not finish before the timeout") from exc

    if check and completed.returncode != 0:
        details = (completed.stderr or completed.stdout).strip()
        suffix = f": {details}" if details else ""
        raise IntegrationError(
            f"MuseScore Studio exited with status {completed.returncode}{suffix}"
        )
    return completed


def _version(executable: Path) -> str | None:
    for option in ("--long-version", "--version", "-v"):
        try:
            completed = _run([executable, option], timeout=15, check=False)
        except IntegrationError:
            continue
        text = (completed.stdout or completed.stderr).strip()
        if completed.returncode == 0 and text:
            return text.splitlines()[0].strip()
    return None


def find_musescore(explicit: str | Path | None = None) -> MuseScoreInstallation | None:
    candidates = [Path(explicit).expanduser()] if explicit is not None else _candidate_paths()
    for candidate in candidates:
        if candidate.is_file():
            return MuseScoreInstallation(candidate.resolve(), _version(candidate.resolve()))
    return None


def require_musescore(explicit: str | Path | None = None) -> MuseScoreInstallation:
    installation = find_musescore(explicit)
    if installation is None:
        raise IntegrationError(
            "MuseScore Studio was not found. Install MuseScore Studio 4, add its executable "
            "to PATH, set TEMPERAMENTO_MUSESCORE, or pass --musescore."
        )
    return installation


def _paths_identify_same_file(first: Path, second: Path) -> bool:
    try:
        if first.exists() and second.exists() and os.path.samefile(first, second):
            return True
    except OSError:
        pass
    try:
        return first.resolve() == second.resolve()
    except OSError:
        return first.absolute() == second.absolute()


def export_score(
    source: str | Path,
    output: str | Path,
    *,
    executable: str | Path | None = None,
    timeout: int = 180,
) -> Path:
    source_path = Path(source)
    output_path = Path(output)
    if not source_path.is_file():
        raise IntegrationError(f"score does not exist: {source_path}")
    if _paths_identify_same_file(source_path, output_path):
        raise IntegrationError("MuseScore export source and destination must be different files")
    if output_path.is_symlink():
        raise IntegrationError(f"refusing to overwrite symbolic link: {output_path}")
    if output_path.exists() and not output_path.is_file():
        raise IntegrationError(f"MuseScore export destination is not a regular file: {output_path}")

    installation = require_musescore(executable)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(
            prefix=f".{output_path.name}-",
            dir=output_path.parent,
        ) as directory:
            temporary_output = Path(directory) / output_path.name
            _run(
                [installation.executable, "-o", temporary_output, source_path],
                timeout=timeout,
            )
            if not temporary_output.is_file() or temporary_output.stat().st_size == 0:
                raise IntegrationError(
                    f"MuseScore Studio did not create the requested export: {output_path}"
                )
            os.replace(temporary_output, output_path)
    except IntegrationError:
        raise
    except OSError as exc:
        raise IntegrationError(f"cannot finalize MuseScore export {output_path}: {exc}") from exc
    return output_path


@contextmanager
def musicxml_source(
    source: str | Path,
    *,
    executable: str | Path | None = None,
) -> Iterator[Path]:
    source_path = Path(source)
    suffix = source_path.suffix.lower()
    if suffix in _MUSICXML_SUFFIXES:
        yield source_path
        return
    if suffix not in _NATIVE_SUFFIXES:
        raise IntegrationError(
            f"unsupported score extension {source_path.suffix!r}; expected MusicXML, MXL, "
            "MSCX, or MSCZ"
        )
    with tempfile.TemporaryDirectory(prefix="temperamento-musescore-") as directory:
        converted = Path(directory) / f"{source_path.stem}.musicxml"
        export_score(source_path, converted, executable=executable)
        yield converted


def render_score(
    source: str | Path,
    output_directory: str | Path,
    formats: Sequence[str],
    *,
    executable: str | Path | None = None,
) -> tuple[Path, ...]:
    normalised: list[str] = []
    aliases = {"midi": "mid", "musicxml": "musicxml", "mxl": "mxl"}
    allowed = {
        "pdf",
        "svg",
        "png",
        "mid",
        "midi",
        "wav",
        "mp3",
        "flac",
        "mxl",
        "musicxml",
        "mscz",
        "mscx",
    }
    for raw in formats:
        extension = raw.lower().lstrip(".")
        if extension not in allowed:
            raise IntegrationError(f"unsupported MuseScore export format: {raw}")
        extension = aliases.get(extension, extension)
        if extension not in normalised:
            normalised.append(extension)
    if not normalised:
        raise IntegrationError("at least one MuseScore export format is required")

    source_path = Path(source)
    destination = Path(output_directory)
    destination.mkdir(parents=True, exist_ok=True)
    outputs = []
    for extension in normalised:
        output = destination / f"{source_path.stem}.{extension}"
        outputs.append(export_score(source_path, output, executable=executable))
    return tuple(outputs)
