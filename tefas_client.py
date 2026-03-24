"""
borsapy kütüphanesi üzerinden fon verisi çeken modül.
"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def get_fund_data(fund_code: str) -> dict | None:
    try:
        import borsapy as bp
        fon = bp.Fund(fund_code.upper())
        info = fon.info

        if info is None or info.empty:
            logger.warning(f"{fund_code} için veri bulunamadı.")
            return None

        row = info.iloc[0]

        price = None
        for col in ["FIYAT", "price", "Price", "fiyat", "last_price"]:
            if col in row.index and row[col] not in (None, "", float("nan")):
                try:
                    price = float(row[col])
                    break
                except (ValueError, TypeError):
                    continue

        if price is None or price == 0:
            logger.warning(f"{fund_code}: fiyat verisi bulunamadı. Kolonlar: {list(row.index)}")
            return None

        title = ""
        for col in ["FONUNVAN", "title", "Title", "name", "Name", "FON ADI"]:
            if col in row.index and row[col]:
                title = str(row[col])
                break

        return {
            "code": fund_code.upper(),
            "title": title or fund_code.upper(),
            "price": price,
            "date": datetime.today().strftime("%d.%m.%Y"),
        }

    except Exception as e:
        logger.error(f"borsapy ile veri alınamadı ({fund_code}): {e}")
        return None


def get_fund_history(fund_code: str, days: int = 30) -> list[dict]:
    try:
        import borsapy as bp
        fon = bp.Fund(fund_code.upper())
        end = datetime.today()
        start = end - timedelta(days=days)
        history = fon.history(
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d")
        )
        if history is None or history.empty:
            return []

        result = []
        for _, row in history.iterrows():
            try:
                result.append({
                    "date": str(row.get("date", "")),
                    "price": float(row.get("price", 0)),
                })
            except (ValueError, TypeError):
                continue
        return result

    except Exception as e:
        logger.error(f"Geçmiş veri alınamadı ({fund_code}): {e}")
        return []
