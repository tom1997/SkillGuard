from __future__ import annotations

import json

from skillguard.core.models import BatchScanResult, ScanResult


class JsonReporter:
    def render(self, result: BatchScanResult | ScanResult) -> str:
        return json.dumps(result.to_dict(), indent=2, sort_keys=True)
