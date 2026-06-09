"""
Universal Web Scraper & Data Exporter
======================================
A configurable web scraper that extracts structured data from any website
and exports it to CSV, JSON, or Excel format.

Features:
- Configurable scraping rules via simple dict config
- Pagination support (next-button or URL pattern)
- Rate limiting & polite delays
- Proxy support
- Export to CSV / JSON / Excel
- Duplicate filtering
- Retry logic with exponential back-off
"""

import csv
import json
import logging
import random
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# DATA STRUCTURES
# ──────────────────────────────────────────────

@dataclass
class ScrapeConfig:
    """All settings for a single scraping job."""
    base_url: str
    item_selector: str          # CSS selector for each result row/card
    fields: dict[str, str]      # {"field_name": "css_selector_inside_item"}
    next_page_selector: str = ""  # CSS selector for the "Next" link
    max_pages: int = 10
    delay_range: tuple = (1.0, 3.0)   # random sleep between pages (seconds)
    timeout: int = 15
    headers: dict = field(default_factory=lambda: {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    })
    proxies: dict = field(default_factory=dict)


@dataclass
class ScrapedItem:
    data: dict[str, Any]
    source_url: str
    scraped_at: str = field(
        default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S")
    )


# ──────────────────────────────────────────────
# SCRAPER
# ──────────────────────────────────────────────

class WebScraper:
    def __init__(self, config: ScrapeConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(config.headers)
        if config.proxies:
            self.session.proxies.update(config.proxies)
        self._seen_urls: set[str] = set()

    # ── HTTP helpers ──────────────────────────

    def _get(self, url: str, retries: int = 3) -> requests.Response | None:
        for attempt in range(1, retries + 1):
            try:
                resp = self.session.get(url, timeout=self.config.timeout)
                resp.raise_for_status()
                return resp
            except requests.RequestException as exc:
                wait = 2 ** attempt
                logger.warning(
                    "Attempt %d/%d failed for %s: %s. Retrying in %ds…",
                    attempt, retries, url, exc, wait,
                )
                time.sleep(wait)
        logger.error("All retries exhausted for %s", url)
        return None

    def _polite_sleep(self):
        delay = random.uniform(*self.config.delay_range)
        logger.debug("Sleeping %.1fs…", delay)
        time.sleep(delay)

    # ── Parsing ───────────────────────────────

    def _parse_page(self, html: str, page_url: str) -> list[ScrapedItem]:
        soup = BeautifulSoup(html, "html.parser")
        items = []
        for element in soup.select(self.config.item_selector):
            row: dict[str, Any] = {}
            for field_name, selector in self.config.fields.items():
                node = element.select_one(selector)
                if node:
                    # Prefer href for links, text otherwise
                    if node.name == "a" and node.get("href"):
                        row[field_name] = node["href"].strip()
                    else:
                        row[field_name] = node.get_text(strip=True)
                else:
                    row[field_name] = ""
            if any(row.values()):   # skip fully empty rows
                items.append(ScrapedItem(data=row, source_url=page_url))
        return items

    def _next_page_url(self, html: str, current_url: str) -> str | None:
        if not self.config.next_page_selector:
            return None
        soup = BeautifulSoup(html, "html.parser")
        link = soup.select_one(self.config.next_page_selector)
        if not link:
            return None
        href = link.get("href", "")
        if not href or href == "#":
            return None
        # Resolve relative URLs
        if href.startswith("http"):
            return href
        from urllib.parse import urljoin
        return urljoin(current_url, href)

    # ── Main scrape loop ──────────────────────

    def scrape(self) -> list[ScrapedItem]:
        results: list[ScrapedItem] = []
        url = self.config.base_url
        page = 1

        while url and page <= self.config.max_pages:
            if url in self._seen_urls:
                logger.info("Already visited %s — stopping.", url)
                break
            self._seen_urls.add(url)

            logger.info("Scraping page %d: %s", page, url)
            resp = self._get(url)
            if resp is None:
                break

            page_items = self._parse_page(resp.text, url)
            logger.info("  → Found %d items", len(page_items))
            results.extend(page_items)

            url = self._next_page_url(resp.text, url)
            page += 1
            if url:
                self._polite_sleep()

        logger.info("Scraping complete. Total items: %d", len(results))
        return results


# ──────────────────────────────────────────────
# EXPORTERS
# ──────────────────────────────────────────────

def export_csv(items: list[ScrapedItem], path: str):
    if not items:
        logger.warning("No items to export.")
        return
    fieldnames = list(items[0].data.keys()) + ["source_url", "scraped_at"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            writer.writerow({**item.data,
                             "source_url": item.source_url,
                             "scraped_at": item.scraped_at})
    logger.info("CSV saved → %s", path)


def export_json(items: list[ScrapedItem], path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump([asdict(i) for i in items], f, ensure_ascii=False, indent=2)
    logger.info("JSON saved → %s", path)


def export_excel(items: list[ScrapedItem], path: str):
    if not items:
        return
    wb = Workbook()
    ws = wb.active
    ws.title = "Results"
    headers = list(items[0].data.keys()) + ["source_url", "scraped_at"]
    ws.append(headers)
    for item in items:
        ws.append([item.data.get(h, item.__dict__.get(h, ""))
                   for h in headers])
    # Auto-fit column widths (approximate)
    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 60)
    wb.save(path)
    logger.info("Excel saved → %s", path)


# ──────────────────────────────────────────────
# EXAMPLE USAGE
# ──────────────────────────────────────────────

if __name__ == "__main__":
    # Example: scrape a books catalog site
    config = ScrapeConfig(
        base_url="https://books.toscrape.com/catalogue/page-1.html",
        item_selector="article.product_pod",
        fields={
            "title":  "h3 a",
            "price":  "p.price_color",
            "rating": "p.star-rating",
            "link":   "h3 a",
        },
        next_page_selector="li.next a",
        max_pages=5,
        delay_range=(0.5, 1.5),
    )

    scraper = WebScraper(config)
    results = scraper.scrape()

    # Export in all formats
    out = Path("output")
    out.mkdir(exist_ok=True)
    export_csv(results,   str(out / "books.csv"))
    export_json(results,  str(out / "books.json"))
    export_excel(results, str(out / "books.xlsx"))

    print(f"\n✅ Done! Scraped {len(results)} items.")
    print(f"   Files saved to: {out.resolve()}")
