"""Lot 3 preparation checks without model training or real extraction."""

from __future__ import annotations

from dataclasses import dataclass



@dataclass(frozen=True)
class Lot3ReadinessReport:
    """Aggregate readiness status for future supervised/pairwise ML work."""

    training_enabled: bool
    labels_required: bool
    pairwise_generation_possible: bool
    split_strategy: str
    anti_leak_strategy: str
    minimum_included_rows_for_split: int
    blocking_reason: str | None

    def to_safe_output(self) -> dict[str, object]:
        """Return a safe planning report with no labels or row-level values."""

        return {
            "training_enabled": self.training_enabled,
            "labels_required": self.labels_required,
            "pairwise_generation_possible": self.pairwise_generation_possible,
            "split_strategy": self.split_strategy,
            "anti_leak_strategy": self.anti_leak_strategy,
            "minimum_included_rows_for_split": self.minimum_included_rows_for_split,
            "blocking_reason": self.blocking_reason,
        }


def build_lot3_readiness_report(included_count: int) -> Lot3ReadinessReport:
    """Frame Lot 3 entry criteria while keeping training disabled by default."""

    minimum_rows = 4
    enough_rows = included_count >= minimum_rows
    return Lot3ReadinessReport(
        training_enabled=False,
        labels_required=True,
        pairwise_generation_possible=enough_rows,
        split_strategy=(
            "planned_stratified_group_split_70_30_random_state_42_"
            "by_redundancy_or_source_ticket_group_after_go_and_labels"
        ),
        anti_leak_strategy=(
            "keep_duplicate_pair_directions_and_same_redundancy_or_source_ticket_group_"
            "in_one_split_only"
        ),
        minimum_included_rows_for_split=minimum_rows,
        blocking_reason="awaiting_compliance_go_and_validated_labels",
    )
