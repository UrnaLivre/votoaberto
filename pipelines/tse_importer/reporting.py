"""Exact aggregate reconciliation counts and explicitly bounded optional detail."""

import json
from collections import Counter

from .workspace import ACTIVE_WORK


class DivergenceReport:
    def __init__(self, detail, summary, limit):
        self.detail, self.summary, self.limit = detail, summary, limit
        self.counts = Counter()
        self.scopes = Counter()
        self.stats = {}
        self.written_bytes = self.written_records = self.omitted = self.aggregated = 0

    def __enter__(self):
        self.stream = self.detail.open("w", encoding="utf8", newline="\n")
        return self

    def aggregate(self, code, uf, turn, count, sections=None):
        self.counts[code] += count
        self.scopes[(uf, turn, code)] += count
        self.aggregated += count

    def emit(self, severity, code, data, turn):
        self.counts[code] += 1
        self.scopes[(data[1], turn, code)] += 1
        encoded = (
            json.dumps({"severity": severity, "code": code, "record": data}, ensure_ascii=False)
            + "\n"
        )
        size = len(encoded.encode("utf8"))
        if self.written_bytes + size <= self.limit:
            if work := ACTIVE_WORK.get():
                work.check(size)
            self.stream.write(encoded)
            self.written_bytes += size
            self.written_records += 1
        else:
            self.omitted += 1

    def add_stats(self, stats):
        for key, value in stats.items():
            self.stats[key] = self.stats.get(key, 0) + value

    def __exit__(self, kind, error, traceback):
        self.stream.close()
        result = {
            "summary_version": 1,
            "complete": kind is None,
            "reconciliation": self.stats,
            "exact_occurrences": dict(sorted(self.counts.items())),
            "by_scope": [
                {"uf": uf, "round": turn, "code": code, "occurrences": count}
                for (uf, turn, code), count in sorted(self.scopes.items())
            ],
            "detail": {
                "limit_bytes": self.limit,
                "bytes": self.written_bytes,
                "written_records": self.written_records,
                "omitted_due_to_limit": self.omitted,
                "truncated": self.omitted > 0,
                "aggregated_source_absence_rows": self.aggregated,
            },
            "scope": "Compared source records; source absence aggregated; counts are exact only for completed partitions",
        }
        self.summary.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
        )
        return False
