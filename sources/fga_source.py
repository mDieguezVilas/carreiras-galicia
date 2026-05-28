import logging
from framework.models import EventPayload
from framework.sources.base import EventSource, event_source
from datetime import date

logger = logging.getLogger(__name__)


@event_source(source_id="fga", enabled=True)
class FGASource(EventSource):

    def fetch(self):
        # En producción: httpx.get("https://fga.gal/carreiras") + BeautifulSoup
        # Para el TFG: datos de ejemplo representativos
        logger.info("FGASource: obtendo carreiras da FGA")
        return [
            {
                "name": "10K Cidade de Santiago",
                "url": "https://fga.gal/carreiras/10k-santiago",
                "location": "Santiago de Compostela",
                "distance": "10K",
                "event_date": "2025-03-10",
                "registration_url": "https://fga.gal/inscricions/10k-santiago",
            },
            {
                "name": "Maratón de Vigo",
                "url": "https://fga.gal/carreiras/maraton-vigo",
                "location": "Vigo",
                "distance": "42K",
                "event_date": "2025-04-06",
                "registration_url": "https://fga.gal/inscricions/maraton-vigo",
            },
            {
                "name": "Trail Serra do Suído",
                "url": "https://fga.gal/carreiras/trail-suido",
                "location": "Covelo",
                "distance": "28K",
                "event_date": "2025-05-18",
                "registration_url": "https://fga.gal/inscricions/trail-suido",
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
                        "distance": item["distance"],
                        "registration_url": item.get("registration_url", ""),
                    },
                ))
            except Exception as e:
                logger.warning(f"fga: fila ignorada — {e}")
        return payloads