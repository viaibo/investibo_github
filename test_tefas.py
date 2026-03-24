import requests
from datetime import datetime

TEFAS_API_URL = "https://www.tefas.gov.tr/api/DB/BindHistoryInfo"
TEFAS_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Referer": "https://www.tefas.gov.tr/FonAnaliz.aspx",
    "User-Agent": "Mozilla/5.0 (compatible; FonTakipBot/1.0)",
    "X-Requested-With": "XMLHttpRequest",
}

date_str = datetime.today().strftime("%d.%m.%Y")
fund_code = "ATA"  # test için

payload = {
    "fontip": "YAT",
    "sfonkod": fund_code,
    "bastarih": date_str,
    "bittarih": date_str,
    "fonturkod": "",
    "fonkod": fund_code,
}

print(f"İstek gönderiliyor: {fund_code} - {date_str}")
resp = requests.post(TEFAS_API_URL, data=payload, headers=TEFAS_HEADERS, timeout=15)
print(f"HTTP Status: {resp.status_code}")
print(f"Yanıt:\n{resp.text[:2000]}")
