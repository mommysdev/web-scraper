"""Universal Web Scraper — CLI entry point."""

import asyncio
import csv
import json
import logging
import time
from pathlib import Path

import click
import requests
import yaml
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> dict:
    """Load scraping configuration from YAML file."""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def extract_field(element, field_config) -> str:
    """Extract a field value from a BeautifulSoup element."""
    if isinstance(field_config, str):
        # Simple text selector
        found = element.select_one(field_config)
        return found.get_text(strip=True) if found else ""
    elif isinstance(field_config, dict):
        selector = field_config.get("selector", "")
        attribute = field_config.get("attribute", None)
        found = element.select_one(selector)
        if not found:
            return ""
        if attribute:
            value = found.get(attribute, "")
            if isinstance(value, list):
                return " ".join(value)
            return str(value)
        return found.get_text(strip=True)
    return ""


def scrape_page(url: str, config: dict, session: requests.Session) -> list[dict]:
    """Scrape a single page and return extracted items."""
    settings = config.get("settings", {})
    timeout = settings.get("timeout", 30)
    retry_count = settings.get("retry_count", 3)

    for attempt in range(retry_count):
        try:
            resp = session.get(url, timeout=timeout)
            resp.raise_for_status()
            break
        except requests.RequestException as e:
            if attempt < retry_count - 1:
                wait = 2 ** attempt
                logger.warning(f"Retry {attempt + 1}/{retry_count} for {url} (wait {wait}s): {e}")
                time.sleep(wait)
            else:
                logger.error(f"Failed to fetch {url}: {e}")
                return []

    soup = BeautifulSoup(resp.text, "lxml")
    selectors = config.get("selectors", {})
    container_selector = selectors.get("container", "")
    fields = selectors.get("fields", {})

    items = []
    containers = soup.select(container_selector)
    logger.info(f"  Found {len(containers)} items on {url}")

    for element in containers:
        item = {}
        for field_name, field_config in fields.items():
            item[field_name] = extract_field(element, field_config)
        items.append(item)

    return items


def export_data(data: list[dict], output_config: dict):
    """Export scraped data to file."""
    fmt = output_config.get("format", "csv")
    filename = output_config.get("filename", f"output.{fmt}")

    if not data:
        logger.warning("No data to export.")
        return

    Path(filename).parent.mkdir(parents=True, exist_ok=True)

    if fmt == "csv":
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    elif fmt == "json":
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    elif fmt == "xlsx":
        try:
            from openpyxl import Workbook

            wb = Workbook()
            ws = wb.active
            ws.append(list(data[0].keys()))
            for item in data:
                ws.append(list(item.values()))
            wb.save(filename)
        except ImportError:
            logger.error("openpyxl not installed. Use: pip install openpyxl")
            return

    logger.info(f"✅ Exported {len(data)} items to {filename}")


@click.command()
@click.option("--config", "config_path", help="Path to YAML config file")
@click.option("--url", help="Single URL to scrape (quick mode)")
@click.option("--selector", help="CSS selector for items (quick mode)")
@click.option("--output", default="output.csv", help="Output file path")
def main(config_path, url, selector, output):
    """Universal Web Scraper — parse any website with ease."""

    if config_path:
        config = load_config(config_path)
    elif url and selector:
        config = {
            "base_url": url,
            "selectors": {"container": selector, "fields": {"text": ""}},
            "settings": {"delay": 1.0},
            "pagination": {"max_pages": 1},
            "output": {"format": output.split(".")[-1], "filename": output},
        }
    else:
        click.echo("Provide --config or both --url and --selector")
        return

    # Override output if specified
    if output != "output.csv":
        config.setdefault("output", {})
        config["output"]["filename"] = output
        config["output"]["format"] = output.split(".")[-1]

    logger.info(f"🕷️ Starting: {config.get('name', 'Scraping')}")

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": config.get("settings", {}).get(
                "user_agent",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            )
        }
    )

    all_data = []
    pagination = config.get("pagination", {})
    max_pages = pagination.get("max_pages", 1)
    delay = config.get("settings", {}).get("delay", 1.0)
    base_url = config["base_url"]

    for page in range(1, max_pages + 1):
        page_url = base_url.format(page=page)
        logger.info(f"📄 Page {page}/{max_pages}: {page_url}")

        items = scrape_page(page_url, config, session)
        if not items:
            logger.info("  No more items, stopping.")
            break

        all_data.extend(items)

        if page < max_pages:
            time.sleep(delay)

    logger.info(f"📊 Total items scraped: {len(all_data)}")
    export_data(all_data, config.get("output", {"format": "csv", "filename": "output.csv"}))


if __name__ == "__main__":
    main()
