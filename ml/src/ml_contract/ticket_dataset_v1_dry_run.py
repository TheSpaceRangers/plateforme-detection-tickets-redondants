"""CLI entrypoint for the ticket dataset v1 contract dry-run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

try:  # pragma: no cover - supports module and direct script execution.
    from .dry_run_report import build_ticket_dataset_v1_dry_run_report
    from .synthetic_source import synthetic_ticket_source_records
except ImportError:  # pragma: no cover
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from src.ml_contract.dry_run_report import build_ticket_dataset_v1_dry_run_report
    from src.ml_contract.synthetic_source import synthetic_ticket_source_records


def main(argv: Sequence[str] | None = None) -> int:
    """Run the synthetic dry-run and print an aggregate-only JSON report."""

    parser = argparse.ArgumentParser(description="Ticket dataset v1 contract dry-run without export.")
    parser.add_argument("--synthetic", action="store_true", default=True, help="Use built-in non-sensitive records.")
    parser.add_argument("--output", "--output-path", dest="output_path", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if args.output_path:
        report = build_ticket_dataset_v1_dry_run_report([], output_path_attempted=True)
        print(json.dumps(report, ensure_ascii=True, sort_keys=True))
        return 2

    report = build_ticket_dataset_v1_dry_run_report(synthetic_ticket_source_records())
    print(json.dumps(report, ensure_ascii=True, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
