"""
Fon listesi ve fiyat geçmişini JSON dosyalarında saklar.
"""

import json
import os
import logging

logger = logging.getLogger(__name__)

DATA_DIR = os.environ.get("DATA_DIR", "data")
FUNDS_FILE = os.path.join(DATA_DIR, "funds.json")
PRICES_FILE = os.path.join(DATA_DIR, "prices.json")


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def load_funds() -> list[str]:
    """Takip edilen fon kodlarını yükle."""
    _ensure_data_dir()
    if not os.path.exists(FUNDS_FILE):
        return []
    try:
        with open(FUNDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Fon listesi okunamadı: {e}")
        return []


def save_funds(funds: list[str]):
    """Takip edilen fon kodlarını kaydet."""
    _ensure_data_dir()
    try:
        with open(FUNDS_FILE, "w", encoding="utf-8") as f:
            json.dump(funds, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Fon listesi kaydedilemedi: {e}")


def load_previous_prices() -> dict[str, float]:
    """Son kaydedilen fiyatları yükle."""
    _ensure_data_dir()
    if not os.path.exists(PRICES_FILE):
        return {}
    try:
        with open(PRICES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Fiyat geçmişi okunamadı: {e}")
        return {}


def save_prices(prices: dict[str, float]):
    """Güncel fiyatları kaydet (ertesi gün karşılaştırma için)."""
    _ensure_data_dir()
    try:
        with open(PRICES_FILE, "w", encoding="utf-8") as f:
            json.dump(prices, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Fiyatlar kaydedilemedi: {e}")
