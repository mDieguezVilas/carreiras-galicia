import logging
from framework.models import EventPayload
from framework.sources.base import EventSource, event_source
from datetime import date

logger = logging.getLogger(__name__)


@event_source(source_id="kronotime", enabled=True)
class KronotimeSource(EventSource):

    def fetch(self):
        # En producción: httpx.get("https://kronotime.com/api/events?region=galicia")
        logger.info("KronotimeSource: obtendo carreiras de Kronotime")
        return [
            {
                "name": "Carreira Popular Baiona",
                "url": "https://kronotime.com/carreiras/baiona",
                "location": "Baiona",
                "distance": "5K",
                "event_date": "2025-06-01",
            },
            {
                "name": "San Silvestre de Ourense",
                "url": "https://kronotime.com/carreiras/san-silvestre-ourense",
                "location": "Ourense",
                "distance": "10K",
                "event_date": "2025-12-31",
            },
            {
                "name": "Volta a Pé á Cidade de Lugo",
                "url": "https://kronotime.com/carreiras/volta-lugo",
                "location": "Lugo",
                "distance": "8K",
                "event_date": "2025-09-14",
            },
        ]

    def parse(self, raw):
        payloads = []
        for item in raw:
            try:
                payloads.append(EventPayload(
                    type_="race",
                    name=item["name"],
                    url=item["url"],
                    source=self.source_id,
                    event_date=date.fromisoformat(item["event_date"]),
                    data={
                        "location": item["location"],
                        "distance": item.get("distance", ""),
                    },
                ))
            except Exception as e:
                logger.warning(f"kronotime: fila ignorada — {e}")
        return payloads