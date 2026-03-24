"""
TEFAS üzerinden fon verisi çeken modül.
"""

import requests
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

TEFAS_API_URL = "https://www.tefas.gov.tr/api/DB/BindHistoryInfo"
TEFAS_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Referer": "https://www.tefas.gov.tr/FonAnaliz.aspx",
    "User-Agent": "Mozilla/5.0 (compatible; FonTakipBot/1.0)",
    "X-Requested-With": "XMLHttpRequest",
}


def get_fund_data(fund_code: str) -> dict | None:
    today = datetime.today()
    for days_back in range(0, 5):
        target_date = today - timedelta(days=days_back)
        date_str = target_date.strftime("%d.%m.%Y")

        try:
            payload = {
                "fontip": "YAT",
                "sfonkod": fund_code.upper(),
                "bastarih": date_str,
                "bittarih": date_str,
                "fonturkod": "",
                "fonkod": fund_code.upper(),
            }

            resp = requests.post(
                TEFAS_API_URL,
                data=payload,
                headers=TEFAS_HEADERS,
                timeout=15
            )
            resp.raise_for_status()
            data = resp.json()

            records = data.get("data", [])
            if not records:
                continue

            # Dönen kayıtlar içinde doğru fon kodunu bul
            for rec in records:
                if rec.get("FONKODU", "").upper() == fund_code.upper():
                    price = float(rec.get("FIYAT", 0))
                    if price == 0:
                        continue
                    return {
                        "code": fund_code.upper(),
                        "title": rec.get("FONUNVAN", fund_code),
                        "price": price,
                        "date": rec.get("TARIH", date_str),
                        "number_of_shares": float(rec.get("TEDPAYSAYISI", 0)),
                        "number_of_investors": int(rec.get("KISISAYISI", 0)),
                    }

        except requests.exceptions.RequestException as e:
            logger.error(f"TEFAS isteği başarısız ({fund_code}): {e}")
            return None
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"TEFAS veri ayrıştırma hatası ({fund_code}): {e}")
            return None

    logger.warning(f"{fund_code} için son 5 günde veri bulunamadı.")
    return None


def get_fund_history(fund_code: str, days: int = 30) -> list[dict]:
    today = datetime.today()
    start = today - timedelta(days=days)

    payload = {
        "fontip": "YAT",
        "sfonkod": fund_code.upper(),
        "bastarih": start.strftime("%d.%m.%Y"),
        "bittarih": today.strftime("%d.%m.%Y"),
        "fonturkod": "",
        "fonkod": fund_code.upper(),
    }

    try:
        resp = requests.post(
            TEFAS_API_URL,
            data=payload,
            headers=TEFAS_HEADERS,
            timeout=15
        )
        resp.raise_for_status()
        data = resp.json()
        records = data.get("data", [])

        result = []
        for rec in records:
            if rec.get("FONKODU", "").upper() == fund_code.upper():
                result.append({
                    "date": rec.get("TARIH"),
                    "price": float(rec.get("FIYAT", 0)),
                })
        return result

    except Exception as e:
        logger.error(f"Geçmiş veri alınamadı ({fund_code}): {e}")
        return []
