from __future__ import annotations

import logging
import os
from typing import Iterable, Sequence

import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from etl.core.db import PortXDB

load_dotenv(override=False)

logging.basicConfig(
    level=os.getenv("FX_RATE_LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("fx-rate-job")

EXCHANGE_RATE_API_KEY = os.getenv("EXCHANGERATE_API_KEY")
if not EXCHANGE_RATE_API_KEY:
    raise RuntimeError("Missing EXCHANGERATE_API_KEY environment variable.")

SOURCE_NAME = "ExchangeRate-API"
RUN_HOUR = int(os.getenv("FX_RATE_RUN_HOUR", "17"))  # 5 PM in 24-hour time
RUN_MINUTE = int(os.getenv("FX_RATE_RUN_MINUTE", "30"))
TIMEZONE = os.getenv("FX_RATE_TIMEZONE")  # defaults to local timezone

API_URL_TEMPLATE = "https://v6.exchangerate-api.com/v6/{api_key}/latest/{base_currency}"


def fetch_fx_rates(base_currency: str, targets: Sequence[str]) -> dict[str, float]:
    """Fetch conversion rates for the selected targets from ExchangeRate-API."""
    url = API_URL_TEMPLATE.format(
        api_key=EXCHANGE_RATE_API_KEY,
        base_currency=base_currency.upper(),
    )
    logger.debug("Requesting %s", url)
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    payload = response.json()

    if payload.get("result") != "success":
        raise RuntimeError(f"ExchangeRate-API error: {payload}")

    rates = payload.get("conversion_rates", {})
    return {code: rates[code] for code in targets if code in rates}


def get_currency_pair_codes() -> list[str]:
    """Pull currency pair codes from the PortX reference table."""
    db = PortXDB()
    try:
        rows = db.fetch_all("select code from portx.ref_currency_pair order by code")
    finally:
        db.close()

    return [row[0].strip().upper() for row in rows if row and row[0]]


def split_currency_pair(code: str) -> tuple[str, str]:
    """Normalize a currency pair code into base and quote symbols."""
    normalized = code.replace(" ", "").upper()
    if "/" in normalized:
        base, quote = normalized.split("/", 1)
    elif len(normalized) == 6:
        base, quote = normalized[:3], normalized[3:]
    else:
        raise ValueError(f"Unsupported currency pair format: {code}")
    if not base or not quote:
        raise ValueError(f"Incomplete currency pair: {code}")
    return base, quote


def fetch_rates_for_pairs(codes: Iterable[str]) -> list[tuple[str, float, str]]:
    if not codes:
        logger.info("No currency pairs found in reference table.")
        return []

    pair_lookup: dict[tuple[str, str], list[str]] = {}
    targets_by_base: dict[str, set[str]] = {}
    for code in codes:
        base, quote = split_currency_pair(code)
        pair_lookup.setdefault((base, quote), []).append(code)
        targets_by_base.setdefault(base, set()).add(quote)

    results: list[tuple[str, float, str]] = []
    for base, targets in targets_by_base.items():
        target_list = sorted(targets)
        logger.debug("Fetching rates for base %s -> %s", base, ", ".join(target_list))
        rates = fetch_fx_rates(base, target_list)
        for quote, rate in rates.items():
            for original_code in pair_lookup.get((base, quote), []):
                results.append((original_code, rate, SOURCE_NAME))
    return results


def run_job() -> None:
    codes = get_currency_pair_codes()
    rates_with_source = fetch_rates_for_pairs(codes)
    if not rates_with_source:
        logger.warning("No FX rates retrieved for currency pairs: %s", codes)
        return

    for pair_code, rate, source in rates_with_source:
        logger.info(
            "Currency pair %s rate: %s (source=%s)",
            pair_code,
            rate,
            source,
        )
        # TODO: write the rate to persistent storage (e.g., database table)


def main() -> None:
    scheduler = BlockingScheduler()
    trigger = CronTrigger(
        hour=RUN_HOUR,
        minute=RUN_MINUTE,
        timezone=TIMEZONE,
    )
    scheduler.add_job(
        run_job, trigger=trigger, id="daily-fx-rate", replace_existing=True
    )
    logger.info(
        "Scheduled FX rate job at %02d:%02d (timezone=%s).",
        RUN_HOUR,
        RUN_MINUTE,
        TIMEZONE or "system-local",
    )
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    run_once = os.getenv("FX_RATE_RUN_ONCE")
    if run_once:
        run_job()
    else:
        main()
