import re
from typing import Dict, List

import requests
import cloudscraper
from bs4 import BeautifulSoup


BASE_URL = "https://fintables.com/fonlar/{fund_code}"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _fetch_with_requests(url: str) -> str:
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Referer": "https://fintables.com/",
        "Upgrade-Insecure-Requests": "1",
    })

    session.get("https://fintables.com/", timeout=20)
    response = session.get(url, timeout=20)
    response.raise_for_status()
    return response.text


def _fetch_with_cloudscraper(url: str) -> str:
    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "mobile": False}
    )
    response = scraper.get(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://fintables.com/",
        },
        timeout=20,
    )
    response.raise_for_status()
    return response.text


def _fetch_html(url: str) -> str:
    try:
        return _fetch_with_requests(url)
    except requests.HTTPError as e:
        status_code = getattr(e.response, "status_code", None)
        if status_code == 403:
            return _fetch_with_cloudscraper(url)
        raise
    except requests.RequestException:
        return _fetch_with_cloudscraper(url)


def _extract_cash_flow(soup: BeautifulSoup) -> str | None:
    cash_flow_title = "Nakit Giriş Çıkışı"
    label = soup.find(string=lambda text: text and cash_flow_title in text)
    if not label:
        return None

    for sibling in label.parent.find_all_next():
        text = _normalize_text(sibling.get_text(" ", strip=True))
        if text and text != cash_flow_title:
            return text

    return None


def _extract_positions_section(soup: BeautifulSoup, title: str) -> List[Dict[str, str]]:
    header = soup.find(
        lambda tag: tag.name in {"h2", "h3", "h4", "div", "span", "p"}
        and _normalize_text(tag.get_text(" ", strip=True)) == title
    )
    if not header:
        return []

    results: List[Dict[str, str]] = []
    seen = set()

    for tag in header.find_all_next():
        current_text = _normalize_text(tag.get_text(" ", strip=True))

        if current_text in {
            "En Büyük Pozisyonlar",
            "Artırılan Pozisyonlar",
            "Azaltılan Pozisyonlar",
            "Getiri Karşılaştırma",
            "Tarihsel Volatilite",
            "Fon Bilgileri",
        } and current_text != title:
            break

        if tag.name != "a":
            continue

        text = current_text
        if not text or text in {"Sembol", "Ağırlık/Değişim"}:
            continue

        match = re.match(
            r"^(?P<symbol>[A-Z0-9.]+)\s*%\s*(?P<weight>-?[\d.,]+)\s*%\s*(?P<change>-?[\d.,]+)$",
            text,
        )
        if not match:
            continue

        symbol = match.group("symbol")
        if symbol in seen:
            continue

        seen.add(symbol)
        results.append(
            {
                "symbol": symbol,
                "weight_percent": match.group("weight").replace(".", "").replace(",", "."),
                "change_percent": match.group("change").replace(".", "").replace(",", "."),
                "raw_text": text,
            }
        )

    return results


def get_fund_snapshot(fund_code: str) -> Dict[str, object]:
    url = BASE_URL.format(fund_code=fund_code.upper())
    html = _fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")

    return {
        "fund_code": fund_code.upper(),
        "url": url,
        "nakit_giris_cikisi": _extract_cash_flow(soup),
        "en_buyuk_pozisyonlar": _extract_positions_section(soup, "En Büyük Pozisyonlar"),
        "artirilan_pozisyonlar": _extract_positions_section(soup, "Artırılan Pozisyonlar"),
        "azaltilan_pozisyonlar": _extract_positions_section(soup, "Azaltılan Pozisyonlar"),
    }
