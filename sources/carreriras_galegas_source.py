import re
import httpx
import logging
from datetime import datetime
from framework.models import EventPayload
from framework.sources.base import EventSource, event_source

logger = logging.getLogger(__name__)

CARREIRAS_GALEGAS_API = "https://api.web.carreirasgalegas.com/competitions-by-month"
CARREIRAS_GALEGAS_BASE = "https://www.carreirasgalegas.com/competicion"


def _editar_url(text):
    text = text.lower()
    text = re.sub(r'[áéíóúÁÉÍÓÚ]', '', text)
    text = re.sub(r'[^a-z0-9]', '-', text)
    text = re.sub(r'-+', '-', text)
    text = text.strip('-')
    return text


@event_source(source_id="carreiras_galegas", enabled=True)
class CarreirasGalegasSource(EventSource):

    def fetch(self):
        try:
            response = httpx.get(
                CARREIRAS_GALEGAS_API,
                timeout=15,
                headers={"User-Agent": "CarreirasGalicia/1.0"},
            )
            response.raise_for_status()
            data = response.json()
            logger.info(f"carreiras_galegas: {len(data)} meses obtidos")
            return data
        except httpx.HTTPError as e:
            logger.error(f"carreiras_galegas: erro HTTP — {e}")
            return []
        except Exception as e:
            logger.error(f"carreiras_galegas: erro inesperado — {e}")
            return []

    def parse(self, raw: list) -> list[EventPayload]:
        payloads = []
        for month in raw:
            competitions = month.get("competitions", [])
            for item in competitions:
                try:
                    if item.get("status") != "published":
                        continue

                    name = item.get("name", "").strip()
                    if not name:
                        continue

                    url = f"{CARREIRAS_GALEGAS_BASE}/{_editar_url(name)}"
                    place = item.get("place", "")
                    date_text = item.get("date", "")

                    payloads.append(EventPayload(
                        type_="race",
                        name=name,
                        url=url,
                        source=self.source_id,
                        event_date=datetime.now(),
                        data={
                            "location": place,
                            "date_text": date_text,
                        },
                    ))
                except Exception as e:
                    logger.warning(f"carreiras_galegas: item ignorado — {e}")

        logger.info(f"carreiras_galegas: {len(payloads)} carreiras parseadas")
        return payloads