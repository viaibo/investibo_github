# 📈 Telegram Fon Takip Botu

TEFAS üzerinden yatırım fonu verilerini çekerek her gün Telegram'a rapor gönderen bot.

## Özellikler

- Her gün belirlenen saatte otomatik rapor
- Günlük getiri yüzdesi (▲/▼)
- Dünkü ve bugünkü fiyat karşılaştırması
- `/ekle`, `/cikar`, `/liste` komutlarıyla fon yönetimi
- `/rapor` ile istediğin zaman anlık rapor

---

## Kurulum

### 1. Telegram Bot Token Al

1. Telegram'da **@BotFather**'a git
2. `/newbot` yaz ve adımları takip et
3. Sana verilen token'ı kopyala

### 2. Chat ID'ni Öğren

1. Telegram'da **@userinfobot**'a git
2. `/start` yaz
3. Sana gösterilen **Id** numarasını kopyala

### 3. Bağımlılıkları Yükle (lokal test için)

```bash
pip install -r requirements.txt
```

### 4. .env Dosyasını Oluştur

```bash
cp .env.example .env
```

`.env` dosyasını aç ve değerleri doldur:

```
TELEGRAM_TOKEN=123456:ABCdef...
CHAT_ID=123456789
REPORT_HOUR=19
REPORT_MINUTE=0
```

### 5. Botu Başlat (lokal)

```bash
python bot.py
```

---

## Railway.app ile Ücretsiz Deploy

1. [railway.app](https://railway.app) adresine git ve GitHub ile giriş yap
2. **New Project → Deploy from GitHub repo** seç
3. Bu klasörü GitHub'a yükle ve seç
4. **Variables** sekmesine git, şu değişkenleri ekle:
   - `TELEGRAM_TOKEN`
   - `CHAT_ID`
   - `REPORT_HOUR` (varsayılan: 19)
   - `REPORT_MINUTE` (varsayılan: 0)
5. Deploy!

> ⚠️ Railway'de `data/` klasörü her deploy'da sıfırlanır. Kalıcı veri için Railway Volume ekle ya da Render.com tercih et.

---

## Render.com ile Ücretsiz Deploy

1. [render.com](https://render.com) adresine git
2. **New → Background Worker** seç
3. GitHub reposunu bağla
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `python bot.py`
6. Environment Variables'a token ve chat_id ekle
7. Deploy!

---

## Komutlar

| Komut | Açıklama |
|-------|----------|
| `/start` veya `/yardim` | Komut listesi |
| `/ekle ATA` | ATA fonunu takibe al |
| `/cikar ATA` | ATA fonunu listeden çıkar |
| `/liste` | Takip edilen fonlar |
| `/rapor` | Anlık rapor al |

---

## Örnek Rapor Mesajı

```
📊 Günlük Fon Raporu
🕐 15.01.2025 19:00

ATA — Ak Portföy Birinci BIST...
  🟢 ▲ %1.23
  Dün: ₺2.1456 → Bugün: ₺2.1720

YAS — Yapı Kredi Portföy...
  🔴 ▼ %-0.45
  Dün: ₺5.3210 → Bugün: ₺5.2971

Veriler TEFAS üzerinden alınmaktadır.
```

---

## Notlar

- TEFAS verileri genellikle saat 18:00-19:00 arasında güncellenir
- Hafta sonu fiyat güncellenmez, bot son iş günü fiyatını gösterir
- Fon kodları TEFAS'taki 2-6 karakterli kodlardır (örn: ATA, YAS, GAF)
