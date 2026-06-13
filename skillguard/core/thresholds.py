from __future__ import annotations

from skillguard.core.models import BatchScanResult, ScanResult, Severity


THRESHOLD_ORDER = {
    "never": 99,
    Severity.INFO.value: 0,
    Severity.LOW.value: 1,
    Severity.MEDIUM.value: 2,
    Severity.HIGH.value: 3,
    Severity.CRITICAL.value: 4,
}


def should_fail(result: BatchScanResult | ScanResult, fail_on: str) -> bool:
    threshold = THRESHOLD_ORDER[fail_on]
    if threshold == 99:
        return False
    return THRESHOLD_ORDER[result.max_severity.value] >= threshold
