import re
from typing import Dict, List

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://fintables.com/fonlar/{fund_code}"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _extract_cash_flow(soup: BeautifulSoup) -> str | None:
    cash_flow_title = "Nakit Giri\u015f \u00c7\u0131k\u0131\u015f\u0131"
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
            "En B\u00fcy\u00fck Pozisyonlar",
            "Art\u0131r\u0131lan Pozisyonlar",
            "Azalt\u0131lan Pozisyonlar",
            "Getiri Kar\u015f\u0131la\u015ft\u0131rma",
            "Tarihsel Volatilite",
            "Fon Bilgileri",
        } and current_text != title:
            break

        if tag.name != "a":
            continue

        text = current_text
        if not text or text in {"Sembol", "A\u011f\u0131rl\u0131k/De\u011fi\u015fim"}:
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
    response = requests.get(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        },
        timeout=20,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    return {
        "fund_code": fund_code.upper(),
        "url": url,
        "nakit_giris_cikisi": _extract_cash_flow(soup),
        "en_buyuk_pozisyonlar": _extract_positions_section(soup, "En B\u00fcy\u00fck Pozisyonlar"),
        "artirilan_pozisyonlar": _extract_positions_section(soup, "Art\u0131r\u0131lan Pozisyonlar"),
        "azaltilan_pozisyonlar": _extract_positions_section(soup, "Azalt\u0131lan Pozisyonlar"),
    }


if __name__ == "__main__":
    import json
    import sys

    code = sys.argv[1] if len(sys.argv) > 1 else "TLY"
    print(json.dumps(get_fund_snapshot(code), ensure_ascii=False, indent=2))
