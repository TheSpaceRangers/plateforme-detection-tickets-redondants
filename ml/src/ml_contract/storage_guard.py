"""Storage guardrails for controlled ML contract exports."""

from __future__ import annotations

import importlib.util
import os
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Sequence


DIRECTORY_MODE = 0o700
FILE_MODE = 0o600
SECURE_UMASK = 0o077
PARQUET_EXTENSION = ".parquet"


class StorageGuardError(ValueError):
    """Raised when an export destination violates storage guardrails."""


@dataclass(frozen=True)
class SecureStorageTarget:
    """Validated destination and permission policy for a controlled export."""

    path: Path
    directory_mode: int = DIRECTORY_MODE
    file_mode: int = FILE_MODE
    umask: int = SECURE_UMASK


@contextmanager
def secure_umask() -> Iterator[None]:
    """Apply the restrictive export umask for the current write operation."""

    previous_umask = os.umask(SECURE_UMASK)
    try:
        yield
    finally:
        os.umask(previous_umask)


def validate_secure_output_path(output_path: str | Path, *, repo_root: Path | None = None) -> SecureStorageTarget:
    """Validate a Parquet output path outside the current repository and Git workspaces."""

    candidate = Path(output_path).expanduser()
    if candidate.suffix.lower() != PARQUET_EXTENSION:
        raise StorageGuardError("Export path must use the .parquet extension.")

    resolved_path = _resolve_without_requiring_file(candidate)
    if _is_relative_to(resolved_path, (repo_root or _default_repo_root()).resolve()):
        raise StorageGuardError("Export path must be outside the repository.")
    if _is_inside_git_workspace(resolved_path):
        raise StorageGuardError("Export path must be outside any Git workspace.")
    return SecureStorageTarget(path=resolved_path)


def prepare_secure_parent_directory(target: SecureStorageTarget) -> None:
    """Create and restrict the export parent directory to owner-only access."""

    target.path.parent.mkdir(mode=target.directory_mode, parents=True, exist_ok=True)
    os.chmod(target.path.parent, target.directory_mode)


def write_parquet_securely(rows: Sequence[dict[str, object]], target: SecureStorageTarget) -> None:
    """Write Parquet rows with restrictive directory, file permissions, and umask."""

    _ensure_parquet_support()
    prepare_secure_parent_directory(target)
    temporary_path = target.path.with_name(f".{target.path.name}.tmp")
    with secure_umask():
        try:
            _write_parquet(rows, temporary_path)
            os.chmod(temporary_path, target.file_mode)
            temporary_path.replace(target.path)
            os.chmod(target.path, target.file_mode)
        except Exception:
            purge_file(temporary_path)
            raise


def read_parquet_rows(path: Path) -> list[dict[str, object]]:
    """Read persisted Parquet rows for aggregate-only post-write scanning."""

    _ensure_parquet_support()
    import pandas as pd

    dataframe = pd.read_parquet(path)
    return list(dataframe.to_dict(orient="records"))


def purge_file(path: str | Path) -> bool:
    """Remove a single export file if present and report whether it was purged."""

    try:
        Path(path).unlink()
        return True
    except FileNotFoundError:
        return False


def _write_parquet(rows: Sequence[dict[str, object]], output_path: Path) -> None:
    """Write rows through pandas after storage dependencies have been checked."""

    import pandas as pd

    pd.DataFrame(list(rows)).to_parquet(output_path, index=False)


def _ensure_parquet_support() -> None:
    """Fail safely when the local environment cannot write/read Parquet."""

    if importlib.util.find_spec("pandas") is None:
        raise StorageGuardError("Parquet export requires pandas installed locally.")
    if importlib.util.find_spec("pyarrow") is None and importlib.util.find_spec("fastparquet") is None:
        raise StorageGuardError("Parquet export requires pyarrow or fastparquet installed locally.")


def _resolve_without_requiring_file(path: Path) -> Path:
    """Resolve the nearest existing parent while allowing a missing target file."""

    existing_parent = path.parent
    while not existing_parent.exists() and existing_parent != existing_parent.parent:
        existing_parent = existing_parent.parent
    resolved_parent = existing_parent.resolve()
    missing_parts = path.parent.relative_to(existing_parent).parts if path.parent != existing_parent else ()
    return resolved_parent.joinpath(*missing_parts, path.name)


def _default_repo_root() -> Path:
    """Return the repository root from the ML contract module location."""

    return Path(__file__).resolve().parents[3]


def _is_relative_to(path: Path, parent: Path) -> bool:
    """Return whether path is nested under parent."""

    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _is_inside_git_workspace(path: Path) -> bool:
    """Return whether the path is inside a directory containing a .git marker."""

    current = path if path.is_dir() else path.parent
    for parent in (current, *current.parents):
        if (parent / ".git").exists():
            return True
    return False
