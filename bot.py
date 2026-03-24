import os
import logging
from datetime import datetime
import pytz
from fintables_scraper import get_fund_snapshot


from telegram import Bot
from telegram.ext import Application, CommandHandler, ContextTypes

from tefas_client import get_fund_data
from storage import load_funds, save_funds

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")
TIMEZONE = "Europe/Istanbul"
REPORT_HOUR = int(os.environ.get("REPORT_HOUR", "19"))
REPORT_MINUTE = int(os.environ.get("REPORT_MINUTE", "0"))


async def send_daily_report(bot: Bot = None):
    if bot is None:
        bot = Bot(token=TELEGRAM_TOKEN)

    funds = load_funds()
    if not funds:
        await bot.send_message(
            chat_id=CHAT_ID,
            text="⚠️ Takip edilen fon bulunamadı.\n/ekle <FON_KODU> komutuyla fon ekleyebilirsin."
        )
        return

    lines = []
    lines.append("📊 *Günlük Fon Raporu*")
    lines.append(f"🕐 {datetime.now(pytz.timezone(TIMEZONE)).strftime('%d.%m.%Y %H:%M')}")
    lines.append("─" * 30)

    for code in funds:
        try:
            data = get_fund_data(code)
            if not data:
                lines.append(f"\n❌ *{code}*: Veri alınamadı")
                continue

            price = data["price"]
            prev_price = data.get("prev_price")
            title = data.get("title", code)

            if prev_price and prev_price > 0:
                change_pct = ((price - prev_price) / prev_price) * 100
                arrow = "🟢 ▲" if change_pct > 0 else ("🔴 ▼" if change_pct < 0 else "⚪ ━")
                change_str = f"{arrow} %{change_pct:+.2f}"
                prev_str = f"Dün: ₺{prev_price:.4f} → Bugün: ₺{price:.4f}"
            else:
                change_str = "⚪ Veri yok"
                prev_str = f"Bugün: ₺{price:.4f}"

            lines.append(f"\n*{code}* — {title[:35]}")
            lines.append(f"  {change_str}")
            lines.append(f"  {prev_str}")

        except Exception as e:
            logger.error(f"Hata ({code}): {e}")
            lines.append(f"\n❌ *{code}*: Hata oluştu")

    lines.append("\n─" * 30)
    lines.append("_Veriler TEFAS üzerinden alınmaktadır._")

    await bot.send_message(chat_id=CHAT_ID, text="\n".join(lines), parse_mode="Markdown")
    logger.info("Günlük rapor gönderildi.")


async def cmd_start(update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 *Fon Takip Botuna Hoş Geldin!*\n\n"
        "Komutlar:\n"
        "/ekle <FON\\_KODU> — Fon ekle\n"
        "/cikar <FON\\_KODU> — Fon çıkar\n"
        "/liste — Takip edilen fonlar\n"
        "/rapor — Hemen rapor al\n"
        "/yardim — Bu menü\n\n"
        "Örnek: `/ekle TLY`"
        "/pozisyon <FON\\_KODU> — Fintables pozisyon verisi\n"

    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_ekle(update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Kullanım: /ekle <FON_KODU>\nÖrnek: /ekle TLY")
        return

    code = context.args[0].upper().strip()
    funds = load_funds()

    if code in funds:
        await update.message.reply_text(f"ℹ️ *{code}* zaten listede.", parse_mode="Markdown")
        return

    await update.message.reply_text(f"⏳ *{code}* kontrol ediliyor...", parse_mode="Markdown")
    data = get_fund_data(code)
    if not data:
        await update.message.reply_text(f"❌ *{code}* bulunamadı. Fon kodunu kontrol et.", parse_mode="Markdown")
        return

    funds.append(code)
    save_funds(funds)
    await update.message.reply_text(
        f"✅ *{code}* eklendi!\nBugünkü fiyat: ₺{data['price']:.4f}",
        parse_mode="Markdown"
    )


async def cmd_cikar(update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Kullanım: /cikar <FON_KODU>")
        return

    code = context.args[0].upper().strip()
    funds = load_funds()

    if code not in funds:
        await update.message.reply_text(f"ℹ️ *{code}* listede yok.", parse_mode="Markdown")
        return

    funds.remove(code)
    save_funds(funds)
    await update.message.reply_text(f"🗑️ *{code}* listeden çıkarıldı.", parse_mode="Markdown")


async def cmd_liste(update, context: ContextTypes.DEFAULT_TYPE):
    funds = load_funds()
    if not funds:
        await update.message.reply_text("📭 Henüz fon eklenmemiş.\n/ekle <FON_KODU> ile ekleyebilirsin.")
        return

    lines = ["📋 *Takip Edilen Fonlar:*\n"]
    for code in funds:
        data = get_fund_data(code)
        if data:
            lines.append(f"• *{code}* — ₺{data['price']:.4f}")
        else:
            lines.append(f"• *{code}* — veri alınamadı")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_rapor(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Rapor hazırlanıyor...")
    await send_daily_report(bot=context.bot)

async def cmd_test(update, context: ContextTypes.DEFAULT_TYPE):
    import requests
    from bs4 import BeautifulSoup
    fund_code = context.args[0].upper() if context.args else "TLY"

    try:
        url = f"https://www.tefas.gov.tr/FonAnaliz.aspx?FonKod={fund_code}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "tr-TR,tr;q=0.9",
        }
        resp = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Sadece tablo sayısını ve ilk tablonun başlıklarını göster
        tables = soup.find_all("table")
        msg = f"Status: {resp.status_code}\nToplam {len(tables)} tablo\n\n"
        for i, table in enumerate(tables[:6]):
            rows = table.find_all("tr")
            msg += f"Tablo {i+1} ({len(rows)} satır): "
            # Sadece ilk satırı göster
            if rows:
                cells = [td.get_text(strip=True) for td in rows[0].find_all(["td","th"])]
                msg += " | ".join(cells[:4])
            msg += "\n"
        
        await update.message.reply_text(msg[:2000])
    except requests.exceptions.Timeout:
        await update.message.reply_text("❌ Timeout")
    except Exception as e:
        await update.message.reply_text(f"Hata: {e}")
async def cmd_pozisyon(update, context: ContextTypes.DEFAULT_TYPE):
    fund_code = context.args[0].upper().strip() if context.args else "TLY"

    try:
        data = get_fund_snapshot(fund_code)

        lines = [
            f"📌 *{fund_code}* Fintables Özeti",
            f"🔗 {data['url']}",
            "",
            f"💸 *Nakit Giriş Çıkışı:* {data['nakit_giris_cikisi'] or 'Bulunamadı'}",
            "",
            "*En Büyük Pozisyonlar:*"
        ]

        if data["en_buyuk_pozisyonlar"]:
            for item in data["en_buyuk_pozisyonlar"][:5]:
                lines.append(
                    f"• {item['symbol']} | Ağırlık: %{item['weight_percent']} | Değişim: %{item['change_percent']}"
                )
        else:
            lines.append("• Veri bulunamadı")

        lines.append("")
        lines.append("*Artırılan Pozisyonlar:*")
        if data["artirilan_pozisyonlar"]:
            for item in data["artirilan_pozisyonlar"][:5]:
                lines.append(
                    f"• {item['symbol']} | Ağırlık: %{item['weight_percent']} | Değişim: %{item['change_percent']}"
                )
        else:
            lines.append("• Veri bulunamadı")

        lines.append("")
        lines.append("*Azaltılan Pozisyonlar:*")
        if data["azaltilan_pozisyonlar"]:
            for item in data["azaltilan_pozisyonlar"][:5]:
                lines.append(
                    f"• {item['symbol']} | Ağırlık: %{item['weight_percent']} | Değişim: %{item['change_percent']}"
                )
        else:
            lines.append("• Veri bulunamadı")

        message = "\n".join(lines)
        await update.message.reply_text(message[:4000], parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"❌ Hata oluştu: {str(e)}")


def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN env değişkeni ayarlanmamış!")
    if not CHAT_ID:
        raise ValueError("CHAT_ID env değişkeni ayarlanmamış!")

    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("yardim", cmd_start))
    app.add_handler(CommandHandler("ekle", cmd_ekle))
    app.add_handler(CommandHandler("cikar", cmd_cikar))
    app.add_handler(CommandHandler("liste", cmd_liste))
    app.add_handler(CommandHandler("rapor", cmd_rapor))
    app.add_handler(CommandHandler("test", cmd_test))
    app.add_handler(CommandHandler("pozisyon", cmd_pozisyon))


    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(send_daily_report, trigger="cron", hour=REPORT_HOUR, minute=REPORT_MINUTE)
    scheduler.start()
    logger.info(f"Zamanlayıcı başlatıldı: her gün {REPORT_HOUR:02d}:{REPORT_MINUTE:02d} (İstanbul saati)")

    logger.info("Bot başlatılıyor...")
    app.run_polling()


if __name__ == "__main__":
    main()
