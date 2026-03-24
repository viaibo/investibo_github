"""
TEFAS üzerinden fon verisi çeken modül.
Resmi TEFAS API kullanır: https://www.tefas.gov.tr/api/DB/BindHistoryInfo
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
    """
    TEFAS'tan belirtilen fon kodunun güncel verisini çeker.
    
    Returns:
        {
            "code": "ATA",
            "title": "Fon Adı",
            "price": 1.234567,
            "date": "2024-01-15",
            "number_of_shares": 12345678.0,
            "number_of_investors": 1234
        }
        ya da None (hata durumunda)
    """
    today = datetime.today()
    # Hafta sonu ve tatil günlerinde son iş gününü dene (3 gün geriye git)
    for days_back in range(0, 5):
        target_date = today - timedelta(days=days_back)
        date_str = target_date.strftime("%d.%m.%Y")
        
        try:
            payload = {
                "fontip": "YAT",
                "sfonkod": fund_code,
                "bastarih": date_str,
                "bittarih": date_str,
                "fonturkod": "",
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
                continue  # Bu tarihte veri yok, bir önceki güne git
            
            rec = records[0]
            price = float(rec.get("FIYAT", 0))
            if price == 0:
                continue
            
            return {
                "code": fund_code,
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
    """
    Belirtilen fon için geçmiş fiyat verilerini çeker.
    """
    today = datetime.today()
    start = today - timedelta(days=days)
    
    payload = {
        "fontip": "YAT",
        "sfonkod": fund_code,
        "bastarih": start.strftime("%d.%m.%Y"),
        "bittarih": today.strftime("%d.%m.%Y"),
        "fonturkod": "",
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
            result.append({
                "date": rec.get("TARIH"),
                "price": float(rec.get("FIYAT", 0)),
            })
        return result
    
    except Exception as e:
        logger.error(f"Geçmiş veri alınamadı ({fund_code}): {e}")
        return []
