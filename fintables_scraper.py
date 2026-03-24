import re
from typing import Dict, List

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


BASE_URL = "https://fintables.com/fonlar/{fund_code}"


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _extract_cash_flow(soup: BeautifulSoup) -> str | None:
    title = "Nakit Giriş Çıkışı"
    label = soup.find(string=lambda text: text and title in text)
    if not label:
        return None

    for sibling in label.parent.find_all_next():
        text = _normalize_text(sibling.get_text(" ", strip=True))
        if text and text != title:
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


async def get_fund_snapshot(fund_code: str) -> Dict[str, object]:
    url = BASE_URL.format(fund_code=fund_code.upper())

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
            locale="tr-TR",
        )

        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(5000)

        html = await page.content()
        await browser.close()

    soup = BeautifulSoup(html, "html.parser")

    return {
        "fund_code": fund_code.upper(),
        "url": url,
        "nakit_giris_cikisi": _extract_cash_flow(soup),
        "en_buyuk_pozisyonlar": _extract_positions_section(soup, "En Büyük Pozisyonlar"),
        "artirilan_pozisyonlar": _extract_positions_section(soup, "Artırılan Pozisyonlar"),
        "azaltilan_pozisyonlar": _extract_positions_section(soup, "Azaltılan Pozisyonlar"),
    }
