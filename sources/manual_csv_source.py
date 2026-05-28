import csv
import logging
from pathlib import Path
from datetime import date
from framework.models import EventPayload
from framework.sources.base import EventSource, event_source

logger = logging.getLogger(__name__)


@event_source(source_id="manual", enabled=True)
class ManualCSVSource(EventSource):

    def __init__(self, csv_path: str = "data/carreiras_manual.csv"):
        self._csv_path = Path(csv_path)

    def fetch(self):
        if not self._csv_path.exists():
            logger.warning(f"CSV manual non atopado: {self._csv_path}")
            return []
        with open(self._csv_path, encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def parse(self, raw):
        payloads = []
        for row in raw:
            try:
                event_date = None
                if row.get("event_date"):
                    event_date = date.fromisoformat(row["event_date"])
                payloads.append(EventPayload(
                    type_="race",
                    name=row["name"],
                    url=row["url"],
                    source=self.source_id,
                    event_date=event_date,
                    data={
                        "location": row.get("location", ""),
                        "distance": row.get("distance", ""),
                    },
                ))
            except Exception as e:
                logger.warning(f"manual: fila ignorada — {e}")
        return payloads