"""
TEFAS FonAnaliz sayfasından fon verisi çeker.
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


def _fetch_page(fund_code: str):
    url = f"https://www.tefas.gov.tr/FonAnaliz.aspx?FonKod={fund_code}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        logger.error(f"{fund_code}: Sayfa alınamadı: {e}")
        return None


def _parse_prices(soup: BeautifulSoup) -> list[float]:
    script_block = soup.find("script", string=lambda t: t and "FonFiyatGrafik" in t)
    if not script_block:
        return []
    data_match = re.search(r'"data"\s*:\s*\[([^\]]+)\]', script_block.string)
    if not data_match:
        return []
    prices = []
    for x in data_match.group(1).split(","):
        x = x.strip()
        if x:
            try:
                prices.append(float(x))
            except ValueError:
                pass
    return prices


def _parse_li_value(soup: BeautifulSoup, keyword: str) -> str | None:
    tag = soup.find(string=lambda t: t and keyword in t)
    if not tag:
        return None
    span = tag.parent.find("span")
    if span:
        return span.get_text(strip=True)
    return None


def get_fund_data(fund_code: str) -> dict | None:
    soup = _fetch_page(fund_code)
    if not soup:
        return None

    prices = _parse_prices(soup)
    if not prices:
        logger.warning(f"{fund_code}: Fiyat verisi parse edilemedi.")
        return None

    latest_price = prices[-1]
    prev_price = prices[-2] if len(prices) > 1 else None

    # Fon adı
    title_tag = soup.find("span", {"id": lambda x: x and "FonUnvan" in x}) or \
                soup.find("h3", class_=lambda x: x and "fon" in str(x).lower())
    title = title_tag.get_text(strip=True) if title_tag else fund_code

    # Ek veriler
    total_value = _parse_li_value(soup, "Fon Toplam Değer")
    investor_count = _parse_li_value(soup, "Yatırımcı Sayısı")
    risk_value = None
    risk_td = soup.find("td", class_="fund-profile-header", string=lambda t: t and "Risk" in str(t))
    if risk_td:
        next_td = risk_td.find_next_sibling("td")
        if next_td:
            risk_value = next_td.get_text(strip=True)

    return {
        "code": fund_code.upper(),
        "title": title,
        "price": latest_price,
        "prev_price": prev_price,
        "date": datetime.today().strftime("%d.%m.%Y"),
        "total_value": total_value,
        "investor_count": investor_count,
        "risk_value": risk_value,
    }


def get_fund_history(fund_code: str, days: int = 30) -> list[dict]:
    soup = _fetch_page(fund_code)
    if not soup:
        return []
    prices = _parse_prices(soup)
    return [{"price": p} for p in prices[-days:]]
