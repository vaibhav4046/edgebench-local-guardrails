import time

from edgebench.runner.memory_monitor import MemoryMonitor


def test_memory_monitor_collects_samples():
    monitor = MemoryMonitor(sample_interval_seconds=0.05)
    monitor.start()
    time.sleep(0.2)
    monitor.stop()

    summary = monitor.summary()
    assert summary["sample_count"] > 0
    assert "global" in summary
