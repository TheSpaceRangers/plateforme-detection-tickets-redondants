"""CLI entrypoint for controlled ML ticket contract v1 export tooling."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

try:  # pragma: no cover - supports module and direct script execution.
    from .dry_run_report import build_ticket_dataset_v1_dry_run_report
    from .secure_export import DEFAULT_TTL_HOURS, build_blocked_secure_export_report, normalize_block_reason
    from .storage_guard import validate_secure_output_path
except ImportError:  # pragma: no cover
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from src.ml_contract.dry_run_report import build_ticket_dataset_v1_dry_run_report
    from src.ml_contract.secure_export import DEFAULT_TTL_HOURS, build_blocked_secure_export_report, normalize_block_reason
    from src.ml_contract.storage_guard import validate_secure_output_path


def main(argv: Sequence[str] | None = None) -> int:
    """Run dry-run by default and block real export unless all CLI gates are explicit."""

    return _dispatch(_parse_args(argv))


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    """Parse CLI arguments for controlled export tooling."""

    parser = argparse.ArgumentParser(description="Ticket v1 controlled ML export tooling.")
    parser.add_argument("--real-export", action="store_true", help="Enable guarded real export mode.")
    parser.add_argument("--output", "--output-path", dest="output_path", help="Parquet output path for real export only.")
    parser.add_argument("--ttl-hours", type=int, default=DEFAULT_TTL_HOURS, help="Export TTL in hours, default 24.")
    return parser.parse_args(argv)


def _dispatch(args: argparse.Namespace) -> int:
    """Route CLI execution to dry-run or guarded real-export blocking flow."""

    if not args.real_export:
        return _run_dry_mode(output_path_attempted=bool(args.output_path))
    return _block_or_validate_real_mode(output_path=args.output_path, ttl_hours=args.ttl_hours)


def _run_dry_mode(*, output_path_attempted: bool) -> int:
    """Run the default dry-run mode without writing any output file."""

    report = build_ticket_dataset_v1_dry_run_report(_synthetic_safe_records(), output_path_attempted=output_path_attempted)
    _emit_report(report)
    return 0 if report["status"] == "pass" else 2


def _block_or_validate_real_mode(*, output_path: str | None, ttl_hours: int) -> int:
    """Validate real-export CLI gates, then block due to unavailable source provider."""

    if not output_path:
        _emit_report(build_blocked_secure_export_report("missing_required_output_path"))
        return 2
    if ttl_hours <= 0:
        _emit_report(build_blocked_secure_export_report("invalid_ttl_hours"))
        return 2
    if not _emit_storage_guard_report_if_blocked(output_path):
        return 2
    _emit_report(build_blocked_secure_export_report("source_provider_not_configured"))
    return 2


def _emit_storage_guard_report_if_blocked(output_path: str) -> bool:
    """Validate storage guardrails and emit an aggregate blocked report on failure."""

    try:
        validate_secure_output_path(output_path)
        return True
    except Exception as error:
        _emit_report(build_blocked_secure_export_report(normalize_block_reason(error)))
        return False


def _emit_report(report: dict[str, object]) -> None:
    """Write only aggregate report JSON to stdout."""

    print(json.dumps(report, ensure_ascii=True, sort_keys=True))


def _synthetic_safe_records() -> list[dict[str, object]]:
    """Return non-real ticket-like records for dry-run validation only."""

    return [
        {
            "summary": "Connexion applicative impossible depuis le portail interne",
            "details": "Message d erreur generique apres authentification standard",
            "ticket_created_at": "2025-01-15T09:30:00+00:00",
        },
        {
            "summary": "Lenteur lors de la synchronisation documentaire",
            "details": "Plusieurs utilisateurs signalent un delai sur une operation recurrente",
            "ticket_created_at": "2025-02-03",
        },
        {
            "summary": "Archive historique hors scope",
            "details": "Cas synthetique exclu par date de cadrage",
            "ticket_created_at": "2024-12-31",
        },
        {
            "summary": "Date absente exclue",
            "details": "Cas synthetique sans date de creation exploitable",
            "ticket_created_at": None,
        },
    ]


if __name__ == "__main__":
    raise SystemExit(main())
