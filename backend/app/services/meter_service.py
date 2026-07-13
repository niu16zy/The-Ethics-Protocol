from __future__ import annotations


class MeterService:
    def apply_delta(self, current_meter: int, score_delta: int) -> int:
        return max(0, min(100, current_meter + score_delta))
