"""
TEFAS FonAnaliz sayfasından Highcharts script bloğunu parse ederek fon verisi çeker.
"""

import re
import requests
import logging
from bs4 import BeautifulSoup
from datetime import datetime

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _fetch_script(fund_code: str) -> str | None:
    url = f"https://www.tefas.gov.tr/FonAnaliz.aspx?FonKod={fund_code}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        script_block = soup.find("script", string=lambda t: t and "FonFiyatGrafik" in t)
        if script_block:
            return script_block.string
        logger.warning(f"{fund_code}: FonFiyatGrafik script bloğu bulunamadı.")
        return None
    except Exception as e:
        logger.error(f"{fund_code}: Sayfa alınamadı: {e}")
        return None


def _parse_prices(script: str) -> list[float]:
    data_match = re.search(r'"data"\s*:\s*\[([^\]]+)\]', script)
    if not data_match:
        return []
    prices_raw = data_match.group(1)
    prices = []
    for x in prices_raw.split(","):
        x = x.strip()
        if x:
            try:
                prices.append(float(x))
            except ValueError:
                pass
    return prices


def _parse_title(script: str, fund_code: str) -> str:
    # Fon adını subtitle veya başka bir alandan çekmeye çalış
    match = re.search(r'"subtitle"\s*:\s*\{[^}]*"text"\s*:\s*"([^"]+)"', script)
    if match:
        return match.group(1)
    return fund_code


def get_fund_data(fund_code: str) -> dict | None:
    script = _fetch_script(fund_code)
    if not script:
        return None

    prices = _parse_prices(script)
    if not prices:
        logger.warning(f"{fund_code}: Fiyat verisi parse edilemedi.")
        return None

    latest_price = prices[-1]
    prev_price = prices[-2] if len(prices) > 1 else None
    title = _parse_title(script, fund_code)

    return {
        "code": fund_code.upper(),
        "title": title,
        "price": latest_price,
        "prev_price": prev_price,
        "date": datetime.today().strftime("%d.%m.%Y"),
    }


def get_fund_history(fund_code: str, days: int = 30) -> list[dict]:
    script = _fetch_script(fund_code)
    if not script:
        return []

    prices = _parse_prices(script)
    if not prices:
        return []

    # Son `days` günü döndür
    return [{"price": p} for p in prices[-days:]]
