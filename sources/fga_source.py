import httpx
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from framework.models import EventPayload
from framework.sources.base import EventSource, event_source

logger = logging.getLogger(__name__)

FGA_URL = "https://atletismo.gal/competicions/"


@event_source(source_id="fga", enabled=True)
class FGASource(EventSource):

    def fetch(self):
        """Descarga o HTML da páxina de competicións da FGA."""
        try:
            response = httpx.get(
                FGA_URL,
                timeout=15,
                headers={"User-Agent": "CarreirasGalicia/1.0"},
                follow_redirects=True,
            )
            response.raise_for_status()
            logger.info(f"FGA: HTML obtido ({len(response.text)} chars)")
            return response.text
        except httpx.HTTPError as e:
            logger.error(f"FGA: erro HTTP — {e}")
            return ""
        except Exception as e:
            logger.error(f"FGA: erro inesperado — {e}")
            return ""

    def parse(self, raw: str) -> list[EventPayload]:
        if not raw:
            return []

        soup = BeautifulSoup(raw, "lxml")
        articles = soup.select("article.competition")

        payloads = []
        for article in articles:
            try:
                # Data: dentro do div con clase 'bg-red'
                date_span = article.select_one("div.bg-red span")
                event_date_str = date_span.get_text(strip=True) if date_span else ""

                # Tipo: span de texto normal xunto á data
                type_span = article.select_one("div.space-x-2 span.text-sm.font-normal")
                event_type = type_span.get_text(strip=True) if type_span else ""

                # Nome e URL: dentro do h2 > a
                link = article.select_one("h2 a")
                name = link.get_text(strip=True) if link else ""
                url = link["href"] if link and link.has_attr("href") else FGA_URL

                if not name:
                    continue

                # Localización: div con texto solto ao lado do nome
                location_div = article.select_one(
                    "div.text-base.text-black"
                )
                location = location_div.get_text(strip=True) if location_div else ""

                payloads.append(EventPayload(
                    type_="race",
                    name=name,
                    url = str(link["href"]) if link and link.has_attr("href") else FGA_URL,
                    source=self.source_id,
                    event_date=datetime.now(),
                    data={
                        "location": location,
                        "event_type": event_type,
                        "date_text": event_date_str,
                    },
                ))

            except Exception as e:
                logger.warning(f"FGA: artigo ignorado — {e}")

        logger.info(f"FGA: {len(payloads)} competicións parseadas")
        return payloads