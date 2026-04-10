"""Tests for the PerformanceTracker and related utilities."""

import time

from src.performance import (
    PerformanceTracker,
    TimingRecord,
    get_performance_tracker,
    reset_performance_tracker,
    track_performance,
)


class TestTimingRecord:
    """Tests for TimingRecord dataclass."""

    def test_initial_state(self):
        """Test that a new TimingRecord has no end time or duration."""
        record = TimingRecord(name="test_op", stage="test", start_time=time.time())
        assert record.end_time is None
        assert record.duration is None

    def test_complete(self):
        """Test that complete() sets end_time and duration."""
        start = time.time()
        record = TimingRecord(name="test_op", stage="test", start_time=start)
        time.sleep(0.01)
        record.complete()
        assert record.end_time is not None
        assert record.duration is not None
        assert record.duration >= 0.01
        assert record.end_time >= start


class TestPerformanceTracker:
    """Tests for PerformanceTracker."""

    def test_start_and_stop_timer(self):
        """Test starting and stopping a timer."""
        tracker = PerformanceTracker()
        tracker.start_timer("download", stage="build")
        time.sleep(0.01)
        record = tracker.stop_timer("download", stage="build")
        assert record is not None
        assert record.name == "download"
        assert record.stage == "build"
        assert record.duration >= 0.01
        assert len(tracker.records) == 1

    def test_stop_nonexistent_timer(self):
        """Test that stopping a nonexistent timer returns None."""
        tracker = PerformanceTracker()
        result = tracker.stop_timer("nonexistent", stage="test")
        assert result is None

    def test_context_manager(self):
        """Test the track context manager."""
        tracker = PerformanceTracker()
        with tracker.track("extract", stage="iso") as record:
            time.sleep(0.01)
        assert record.duration is not None
        assert record.duration >= 0.01
        assert len(tracker.records) == 1

    def test_multiple_records(self):
        """Test tracking multiple operations."""
        tracker = PerformanceTracker()
        with tracker.track("step1", stage="build"):
            pass
        with tracker.track("step2", stage="build"):
            pass
        with tracker.track("step3", stage="test"):
            pass
        assert len(tracker.records) == 3

    def test_stage_summary(self):
        """Test that stage summary aggregates correctly."""
        tracker = PerformanceTracker()
        with tracker.track("a", stage="build"):
            time.sleep(0.01)
        with tracker.track("b", stage="build"):
            time.sleep(0.01)
        with tracker.track("c", stage="test"):
            time.sleep(0.01)

        summary = tracker.get_stage_summary()
        assert "build" in summary
        assert "test" in summary
        assert summary["build"] >= 0.02
        assert summary["test"] >= 0.01

    def test_total_time(self):
        """Test total time calculation."""
        tracker = PerformanceTracker()
        with tracker.track("a", stage="x"):
            time.sleep(0.01)
        with tracker.track("b", stage="y"):
            time.sleep(0.01)

        total = tracker.get_total_time()
        assert total >= 0.02

    def test_format_duration_seconds(self):
        """Test duration formatting for seconds."""
        tracker = PerformanceTracker()
        assert tracker.format_duration(5.5) == "5.50s"
        assert tracker.format_duration(0.123) == "0.12s"

    def test_format_duration_minutes(self):
        """Test duration formatting for minutes."""
        tracker = PerformanceTracker()
        result = tracker.format_duration(125.5)
        assert "2m" in result

    def test_format_duration_hours(self):
        """Test duration formatting for hours."""
        tracker = PerformanceTracker()
        result = tracker.format_duration(3661.0)
        assert "1h" in result

    def test_to_dict(self):
        """Test export to dictionary."""
        tracker = PerformanceTracker()
        with tracker.track("op1", stage="s1"):
            pass

        data = tracker.to_dict()
        assert "records" in data
        assert "stage_summary" in data
        assert "total_time" in data
        assert len(data["records"]) == 1
        assert data["records"][0]["name"] == "op1"

    def test_print_summary_empty(self, capsys):
        """Test print summary with no records."""
        tracker = PerformanceTracker()
        tracker.print_summary()
        captured = capsys.readouterr()
        assert "No performance data" in captured.out

    def test_print_summary_with_data(self, capsys):
        """Test print summary with records."""
        tracker = PerformanceTracker()
        with tracker.track("test_op", stage="test_stage"):
            time.sleep(0.01)
        tracker.print_summary()
        captured = capsys.readouterr()
        assert "Performance Summary" in captured.out


class TestGlobalTracker:
    """Tests for the global performance tracker."""

    def test_get_performance_tracker_singleton(self):
        """Test that get_performance_tracker returns consistent instance."""
        reset_performance_tracker()
        t1 = get_performance_tracker()
        t2 = get_performance_tracker()
        assert t1 is t2

    def test_reset_performance_tracker(self):
        """Test that reset creates a new instance."""
        t1 = get_performance_tracker()
        with t1.track("x"):
            pass
        assert len(t1.records) == 1
        reset_performance_tracker()
        t2 = get_performance_tracker()
        assert len(t2.records) == 0
        assert t1 is not t2

    def test_track_performance_context(self):
        """Test the convenience track_performance function."""
        reset_performance_tracker()
        with track_performance("global_op", stage="global_stage"):
            time.sleep(0.01)
        tracker = get_performance_tracker()
        assert len(tracker.records) == 1
        assert tracker.records[0].name == "global_op"
        assert tracker.records[0].stage == "global_stage"
