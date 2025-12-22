"""Performance timing utilities for Proxmox ISO builder."""

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Dict, Generator, List, Optional

from rich.console import Console
from rich.table import Table

logger = logging.getLogger(__name__)


@dataclass
class TimingRecord:
    """Record of a single timed operation."""

    name: str
    stage: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None

    def complete(self) -> None:
        """Mark the timing record as complete."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time


@dataclass
class PerformanceTracker:
    """Track and report performance metrics for build stages and actions."""

    records: List[TimingRecord] = field(default_factory=list)
    _active_timers: Dict[str, TimingRecord] = field(default_factory=dict)

    def start_timer(self, name: str, stage: str = "default") -> TimingRecord:
        """
        Start a timer for a named operation.

        Args:
            name: Name of the operation being timed
            stage: Stage category for the operation

        Returns:
            TimingRecord for the started timer
        """
        record = TimingRecord(
            name=name,
            stage=stage,
            start_time=time.time(),
        )
        key = f"{stage}:{name}"
        self._active_timers[key] = record
        logger.debug(f"Started timer for {name} in stage {stage}")
        return record

    def stop_timer(self, name: str, stage: str = "default") -> Optional[TimingRecord]:
        """
        Stop a timer for a named operation.

        Args:
            name: Name of the operation
            stage: Stage category for the operation

        Returns:
            Completed TimingRecord or None if timer not found
        """
        key = f"{stage}:{name}"
        record = self._active_timers.pop(key, None)
        if record:
            record.complete()
            self.records.append(record)
            logger.info(f"[PERF] {record.stage}/{record.name}: {record.duration:.2f}s")
        return record

    @contextmanager
    def track(
        self, name: str, stage: str = "default"
    ) -> Generator[TimingRecord, None, None]:
        """
        Context manager for tracking execution time of an operation.

        Args:
            name: Name of the operation being timed
            stage: Stage category for the operation

        Yields:
            TimingRecord for the operation
        """
        record = self.start_timer(name, stage)
        try:
            yield record
        finally:
            self.stop_timer(name, stage)

    def get_stage_summary(self) -> Dict[str, float]:
        """
        Get total time spent in each stage.

        Returns:
            Dictionary mapping stage names to total duration in seconds
        """
        summary: Dict[str, float] = {}
        for record in self.records:
            if record.duration is not None:
                if record.stage not in summary:
                    summary[record.stage] = 0.0
                summary[record.stage] += record.duration
        return summary

    def get_total_time(self) -> float:
        """
        Get total time for all recorded operations.

        Returns:
            Total duration in seconds
        """
        return sum(
            record.duration for record in self.records if record.duration is not None
        )

    def format_duration(self, seconds: float) -> str:
        """
        Format duration in human-readable format.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted duration string
        """
        if seconds < 60:
            return f"{seconds:.2f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.2f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            return f"{hours}h {minutes}m {secs:.2f}s"

    def print_summary(self, console: Optional[Console] = None) -> None:
        """
        Print a summary table of all timing records.

        Args:
            console: Rich console for output (creates new one if not provided)
        """
        if console is None:
            console = Console()

        if not self.records:
            console.print("[yellow]No performance data recorded[/yellow]")
            return

        # Create detailed timing table
        table = Table(title="Performance Summary")
        table.add_column("Stage", style="cyan")
        table.add_column("Operation", style="green")
        table.add_column("Duration", style="yellow", justify="right")

        for record in self.records:
            if record.duration is not None:
                table.add_row(
                    record.stage,
                    record.name,
                    self.format_duration(record.duration),
                )

        console.print(table)

        # Print stage summary
        stage_summary = self.get_stage_summary()
        if stage_summary:
            summary_table = Table(title="Stage Summary")
            summary_table.add_column("Stage", style="cyan")
            summary_table.add_column("Total Time", style="yellow", justify="right")

            for stage, duration in sorted(
                stage_summary.items(), key=lambda x: x[1], reverse=True
            ):
                summary_table.add_row(stage, self.format_duration(duration))

            console.print(summary_table)

        # Print total time
        total = self.get_total_time()
        console.print(f"\n[bold]Total Build Time: {self.format_duration(total)}[/bold]")

    def to_dict(self) -> Dict:
        """
        Export timing data as a dictionary.

        Returns:
            Dictionary containing all timing records and summaries
        """
        return {
            "records": [
                {
                    "name": r.name,
                    "stage": r.stage,
                    "start_time": r.start_time,
                    "end_time": r.end_time,
                    "duration": r.duration,
                }
                for r in self.records
            ],
            "stage_summary": self.get_stage_summary(),
            "total_time": self.get_total_time(),
        }


# Global performance tracker instance
_global_tracker: Optional[PerformanceTracker] = None


def get_performance_tracker() -> PerformanceTracker:
    """
    Get the global performance tracker instance.

    Returns:
        Global PerformanceTracker instance
    """
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = PerformanceTracker()
    return _global_tracker


def reset_performance_tracker() -> None:
    """Reset the global performance tracker."""
    global _global_tracker
    _global_tracker = PerformanceTracker()


@contextmanager
def track_performance(
    name: str, stage: str = "default"
) -> Generator[TimingRecord, None, None]:
    """
    Convenience context manager for tracking performance.

    Uses the global performance tracker.

    Args:
        name: Name of the operation being timed
        stage: Stage category for the operation

    Yields:
        TimingRecord for the operation
    """
    tracker = get_performance_tracker()
    with tracker.track(name, stage) as record:
        yield record
