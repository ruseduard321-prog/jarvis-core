from __future__ import annotations

import threading
import time
from typing import Callable, Dict, Iterable, Protocol


class MetricsProvider(Protocol):
    def increment_counter(self, name: str, labels: dict[str, str] | None = None) -> None:
        ...

    def observe_histogram(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        ...

    def set_gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        ...

    def collect(self) -> str:
        ...


def _format_labels(labels: dict[str, str]) -> str:
    if not labels:
        return ""
    entries = [f'{key}="{value}"' for key, value in sorted(labels.items())]
    return "{" + ",".join(entries) + "}"


class InMemoryMetricsProvider:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[tuple[str, tuple[tuple[str, str], ...]], int] = {}
        self._gauges: dict[tuple[str, tuple[tuple[str, str], ...]], float] = {}
        self._histograms: dict[tuple[str, tuple[tuple[str, str], ...]], dict[str, float]] = {}
        self._buckets = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]

    def _key(self, name: str, labels: dict[str, str] | None) -> tuple[str, tuple[tuple[str, str], ...]]:
        labels_tuple = tuple(sorted(labels.items())) if labels else ()
        return name, labels_tuple

    def increment_counter(self, name: str, labels: dict[str, str] | None = None) -> None:
        key = self._key(name, labels)
        with self._lock:
            self._counters[key] = self._counters.get(key, 0) + 1

    def observe_histogram(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        key = self._key(name, labels)
        with self._lock:
            histogram = self._histograms.setdefault(key, {"count": 0.0, "sum": 0.0, **{f"bucket_{b}": 0.0 for b in self._buckets}})
            histogram["count"] += 1.0
            histogram["sum"] += value
            for bucket in self._buckets:
                if value <= bucket:
                    histogram[f"bucket_{bucket}"] += 1.0

    def set_gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        key = self._key(name, labels)
        with self._lock:
            self._gauges[key] = value

    def collect(self) -> str:
        lines: list[str] = []
        with self._lock:
            for (name, labels) in sorted(self._counters.keys()):
                value = self._counters[(name, labels)]
                labels_str = _format_labels(dict(labels))
                lines.append(f"{name}{labels_str} {value}")
            for (name, labels) in sorted(self._gauges.keys()):
                value = self._gauges[(name, labels)]
                labels_str = _format_labels(dict(labels))
                lines.append(f"{name}{labels_str} {value}")
            for (name, labels), histogram in sorted(self._histograms.items()):
                label_dict = dict(labels)
                count = histogram["count"]
                summation = histogram["sum"]
                cumulative = 0.0
                for bucket in self._buckets:
                    cumulative += histogram[f"bucket_{bucket}"]
                    bucket_labels = {**label_dict, "le": str(bucket)}
                    labels_str = _format_labels(bucket_labels)
                    lines.append(f"{name}_bucket{labels_str} {int(cumulative)}")
                labels_inf = {**label_dict, "le": "+Inf"}
                labels_str = _format_labels(labels_inf)
                lines.append(f"{name}_bucket{labels_str} {int(count)}")
                lines.append(f"{name}_count{_format_labels(label_dict)} {int(count)}")
                lines.append(f"{name}_sum{_format_labels(label_dict)} {summation}")
        return "\n".join(lines) + "\n"


metrics_provider = InMemoryMetricsProvider()


def get_metrics_provider() -> MetricsProvider:
    try:
        from backend.core.service_registry import service_registry
        return service_registry.get(MetricsProvider)
    except Exception:
        return metrics_provider
