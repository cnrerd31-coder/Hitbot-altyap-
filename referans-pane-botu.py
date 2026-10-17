print("botun yarragım gibi çalışıyo✅✅✅")

import requests
from bs4 import BeautifulSoup
import os
import json
import io
import asyncio
import httpx
from pathlib import Path
from datetime import datetime, timezone, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
try:
    from telegram.ext import JobQueue
except ImportError:
    JobQueue = None
from functools import wraps
import logging
import tempfile
import aiohttp
import aiofiles
import base64
from telegram import InputFile

# Kullanıcının kanala katılıp katılmadığını kontrol eden fonksiyon
async def is_user_in_channel(user_id, bot) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception as e:
        logger.error(f"Error checking user in channel: {e}")
    return False


# Komut öncesinde kanal kontrolü yapan yardımcı fonksiyon
def ensure_channel_join(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.message.from_user.id
        if not await is_user_in_channel(user_id, context.bot):
            keyboard = [[InlineKeyboardButton("Gruba Katıl🧧", url=GROUP_INVITE_LINK2)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f'Botu kullanmak için lütfen önce kanalına katılın ve /start komutu ile tekrar deneyin.',
                reply_markup=reply_markup
            )
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

# Kullanıcının daha önce geçerli bir anahtar girip girmediğini kontrol eden fonksiyon
def has_user_entered_key(user_id):
    try:
        with open(LOG_DIR / 'keys.json', 'r') as file:
            keys = json.load(file)
            for key in keys.values():
                if user_id in key['users']:
                    return True
    except FileNotFoundError:
        return False
    return False

# Hem kanal katılımını hem de anahtar doğrulamasını kontrol eden yardımcı fonksiyon
def ensure_channel_and_key(func):
     @wraps(func)
     async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
         user_id = update.message.from_user.id
         if not await is_user_in_channel(user_id, context.bot):
             keyboard = [[InlineKeyboardButton("Gruba Katıl🧧", url=GROUP_INVITE_LINK2)]]
             reply_markup = InlineKeyboardMarkup(keyboard)
             await update.message.reply_text(
                 f'Botu kullanmak için lütfen önce kanalına katılın ve /start komutu ile tekrar deneyin.',
                 reply_markup=reply_markup
             )
             return
         
         # Anahtarı kontrol et - hem varsa hemde geçerli mi kontrol et
         if not has_user_entered_key(user_id) or not is_user_key_valid(user_id):
             await update.message.reply_text("❌ Anahtar süresi dolmuş veya geçersiz. Lütfen yeni bir anahtar girin: /key <anahtar> \n\n💎 Satın Almak İçin : @lunasloury", parse_mode="Markdown")
             return
         
         return await func(update, context, *args, **kwargs)
     return wrapper

# Kullanıcının yasaklı olup olmadığını kontrol eden fonksiyon
def is_user_banned(user_id):
    try:
        with open(LOG_DIR / 'ban.txt', 'r') as file:
            banned_users = file.readlines()
            banned_users = [line.strip() for line in banned_users]
            return str(user_id) in banned_users
    except FileNotFoundError:
        return False

# Kullanıcıyı yasaklama fonksiyonu
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 1:
        await update.message.reply_text("Lütfen yasaklamak için geçerli bir kullanıcı ID'si belirtin.")
        return
    
    user_id = context.args[0]
    with open(LOG_DIR / 'ban.txt', 'a') as file:
        file.write(f"{user_id}\n")
    logger.info(f"Kullanıcı {user_id} yasaklandı.")
    await update.message.reply_text(f"Kullanıcı {user_id} yasaklandı.")

# Kullanıcıyı yasağı kaldırma fonksiyonu
async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 1:
        await update.message.reply_text("Lütfen yasağı kaldırmak için geçerli bir kullanıcı ID'si belirtin.")
        return
    
    user_id = context.args[0]
    try:
        with open(LOG_DIR / 'ban.txt', 'r') as file:
            lines = file.readlines()
        with open(LOG_DIR / 'ban.txt', 'w') as file:
            for line in lines:
                if line.strip() != user_id:
                    file.write(line)
        logger.info(f"Kullanıcı {user_id} yasağı kaldırıldı.")
        await update.message.reply_text(f"Kullanıcı {user_id} yasağı kaldırıldı.")
    except FileNotFoundError:
        await update.message.reply_text("Ban listesi bulunamadı.")

# Kullanıcıyı users.txt dosyasına kaydetme fonksiyonu
def save_user(user_id, username):
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    try:
        with open(LOG_DIR / 'users.txt', 'r') as file:
            users = file.readlines()
            users = [line.split(',')[0].strip() for line in users]
            if str(user_id) in users:
                return False
    except FileNotFoundError:
        pass  # If the file does not exist, continue to save the new user

    with open(LOG_DIR / 'users.txt', 'a') as file:
        file.write(f"{user_id},{username},{timestamp}\n")
    return True

# Anahtar doğrulama fonksiyonu
def validate_key(user_id, key):
    try:
        with open(LOG_DIR / 'keys.json', 'r') as file:
            keys = json.load(file)
            if key in keys:
                expiry_date = datetime.fromisoformat(keys[key]['expiry'])
                if expiry_date > datetime.now(timezone.utc):
                    if user_id not in keys[key]['users']:
                        if len(keys[key]['users']) < keys[key]['max_users']:
                            keys[key]['users'].append(user_id)
                        else:
                            return False
                    with open(LOG_DIR / 'keys.json', 'w') as file:
                        json.dump(keys, file)
                    return True
    except FileNotFoundError:
        return False
    return False

# Anahtar oluşturma fonksiyonu (sadece admin)
async def create_key(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id != int(ADMIN_ID):
        await update.message.reply_text("Bu komutu sadece admin kullanabilir.")
        return

    if len(context.args) != 2:
        await update.message.reply_text("Kullanım: /keyolustur <gün sayısı> <kullanıcı sayısı>")
        return

    days = int(context.args[0])
    max_users = int(context.args[1])
    key = os.urandom(16).hex()
    expiry_date = datetime.now(timezone.utc) + timedelta(days=days)

    try:
        with open(LOG_DIR / 'keys.json', 'r') as file:
            keys = json.load(file)
    except FileNotFoundError:
        keys = {}

    keys[key] = {'expiry': expiry_date.isoformat(), 'max_users': max_users, 'users': []}
    with open(LOG_DIR / 'keys.json', 'w') as file:
        json.dump(keys, file)

    await update.message.reply_text(f"Anahtar oluşturuldu: {key}")

# Tüm Keyleri Göster (Admin) - /keys ve /user komutları
async def show_keys_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin - Tüm keyleri ve kullanıcıları göster (/keys komutu)"""
    if update.message.from_user.id != int(ADMIN_ID):
        await update.message.reply_text("🚫 Bu komutu sadece admin kullanabilir.")
        return
    
    # JSON dosyasını doğrudan gönder
    keys_file = LOG_DIR / 'keys.json'
    if keys_file.exists():
        with open(keys_file, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename="keys.json",
                caption="📋 Tüm anahtarlar (JSON dosyası)"
            )
    else:
        await update.message.reply_text("❌ Keys.json dosyası bulunamadı.")

# Tüm Keyleri Göster (Admin)
async def show_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin - Tüm keyleri ve kullanıcıları göster (/user komutu)"""
    if update.message.from_user.id != int(ADMIN_ID):
        await update.message.reply_text("🚫 Bu komutu sadece admin kullanabilir.")
        return
    
    await show_all_keys(update, context)

# Ortak anahtarları gösterme fonksiyonu
async def show_all_keys(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tüm anahtarları göster"""
    
    try:
        with open(LOG_DIR / 'keys.json', 'r') as file:
            keys = json.load(file)
    except FileNotFoundError:
        await update.message.reply_text("🚫 Key dosyası bulunamadı.")
        return
    
    if not keys:
        await update.message.reply_text("📭 Henüz hiç key oluşturulmamış.")
        return
    
    # Mesaj oluştur
    message_text = (
        "🔐 TÜM ANAHTARLAR (KEYS)\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    
    for idx, (key_id, key_data) in enumerate(keys.items(), 1):
        expiry = datetime.fromisoformat(key_data['expiry'])
        now = datetime.now(timezone.utc)
        days_left = (expiry - now).days
        status = "✅ Aktif" if expiry > now else "❌ Süresi Doldu"
        
        message_text += (
            f"#{idx}\n"
            f"🔑 Key ID: `{key_id}`\n"
            f"👥 Kullanıcı: {len(key_data['users'])}/{key_data['max_users']}\n"
            f"📅 Bitiş: {expiry.strftime('%d.%m.%Y %H:%M')}\n"
            f"⏳ Kalan: {days_left} gün\n"
            f"🔔 Durum: {status}\n"
        )
        
        if key_data['users']:
            message_text += f"👤 Kullanıcı IDs: {', '.join(map(str, key_data['users']))}\n"
        
        message_text += "─────────────────────────────\n\n"
    
    # Toplam istatistikler
    total_users = sum(len(key_data['users']) for key_data in keys.values())
    active_keys = sum(1 for key_data in keys.values() if datetime.fromisoformat(key_data['expiry']) > datetime.now(timezone.utc))
    
    message_text += (
        f"\n📊 İSTATİSTİKLER\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔑 Toplam Key: {len(keys)}\n"
        f"✅ Aktif Key: {active_keys}\n"
        f"👥 Toplam Kullanıcı: {total_users}\n"
    )
    
    # Telegram 4096 karakter limiti kontrolü
    if len(message_text) > 4090:
        # Dosya olarak gönder
        output_file = LOG_DIR / 'keys_list.txt'
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(message_text.replace('**', '').replace('`', '').replace('_', ''))
        
        with open(output_file, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename="Tum_Anahtarlar.txt",
                caption="📋 Tüm anahtarların listesi dosya olarak gönderildi."
            )
    else:
        await update.message.reply_text(message_text, parse_mode="Markdown")

# Async API Request Helper
async def async_api_request(url, timeout=15):
    """Async API çağrısı - blocking'den kaçınır"""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            return response
    except httpx.TimeoutException:
        raise Exception("Zaman aşımı")
    except Exception as e:
        raise e

# Başlangıç komutu
@ensure_channel_join
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    if is_user_banned(user_id):
        await update.message.reply_text('Ban yediniz, botu kullanamazsınız.')
        return

    if not await is_user_in_channel(user_id, context.bot):
        
        keyboard = [[InlineKeyboardButton("Gruba Katıl🧧", url=GROUP_INVITE_LINK2)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f'Botu kullanmak için lütfen önce kanalına katılın ve /start komutu ile tekrar deneyin.',
            reply_markup=reply_markup
        )
        return

    if has_user_entered_key(user_id):
        await update.message.reply_text("🔑 Anahtarınız zaten doğrulandı! Luna Vip Sorgu paneline hoş geldiniz.", parse_mode="Markdown")
        await send_join_buttons(update, context)  # Menü gösterimi
    else:
        await update.message.reply_text('🔒 Lütfen bir anahtar girin: /key <anahtar> \n\n 💎 Satın Almak İçin : @lunasloury', parse_mode="Markdown")

# Anahtar girme komutu
@ensure_channel_join
async def key(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if len(context.args) != 1:
        await update.message.reply_text("🔒 Lütfen geçerli bir anahtar girin: /key <anahtar> \n\n 💎 Satın Almak İçin : @lunasloury", parse_mode="Markdown")
        return
    
    key = context.args[0]
    if validate_key(user_id, key):
        await update.message.reply_text("✅ Anahtar doğrulandı! Artık premium sorgu panelini kullanabilirsiniz.", parse_mode="Markdown")
        await send_join_buttons(update, context)  # Menü gösterimi
    else:
        await update.message.reply_text("❌ Geçersiz anahtar veya süresi dolmuş. Lütfen yeni bir anahtar alın.", parse_mode="Markdown")

# Kullanıcının kalan süresini al ve süresi dolmuş anahtarları kontrol et
def get_user_remaining_time(user_id):
     """Kullanıcının anahtarının kalan süresini hesapla ve süresi dolmuş anahtarları sil"""
     try:
         with open(LOG_DIR / 'keys.json', 'r') as file:
             keys = json.load(file)
         
         now = datetime.now(timezone.utc)
         keys_updated = False
         
         for key, value in keys.items():
             if user_id in value['users']:
                 expiry_date = datetime.fromisoformat(value['expiry'])
                 remaining = expiry_date - now
                 
                 # Süresi dolmuş anahtarı kullanıcıdan kaldır
                 if remaining.total_seconds() <= 0:
                     value['users'].remove(user_id)
                     keys_updated = True
                     continue
                 
                 days = remaining.days
                 seconds = remaining.seconds
                 hours = seconds // 3600
                 minutes = (seconds % 3600) // 60
                 
                 # Veritabanı güncellenirse kaydet
                 if keys_updated:
                     with open(LOG_DIR / 'keys.json', 'w') as file:
                         json.dump(keys, file)
                 
                 return f"⏳ Kalan Süre: {days} gün {hours:02d}:{minutes:02d}"
         
         # Veritabanı güncellenirse kaydet
         if keys_updated:
             with open(LOG_DIR / 'keys.json', 'w') as file:
                 json.dump(keys, file)
         
         return None
     except Exception as e:
         logger.error(f"get_user_remaining_time hatası: {e}")
         return None

# Kullanıcının anahtarının süresi dolup dolmadığını kontrol et
def is_user_key_valid(user_id):
     """Kullanıcının geçerli bir anahtarı olup olmadığını kontrol et"""
     try:
         with open(LOG_DIR / 'keys.json', 'r') as file:
             keys = json.load(file)
         
         now = datetime.now(timezone.utc)
         
         for key, value in keys.items():
             if user_id in value['users']:
                 expiry_date = datetime.fromisoformat(value['expiry'])
                 
                 # Anahtar geçerli mi?
                 if expiry_date > now:
                     return True
                 else:
                     # Süresi dolmuş, kaldır
                     value['users'].remove(user_id)
                     with open(LOG_DIR / 'keys.json', 'w') as file:
                         json.dump(keys, file)
                     return False
         
         return False
     except Exception as e:
         logger.error(f"is_user_key_valid hatası: {e}")
         return False

# Butonlu katılım mesajları
async def send_join_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('ban yedin babamla danış @lunasloury.')
        return
    
    keyboard = [
        [InlineKeyboardButton("🌟 Gruba Katıl", url=GROUP_INVITE_LINK2)],
        [InlineKeyboardButton("🔍 Premium Sorgu Paneli", callback_data='sorgu_paneli')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    remaining_time = get_user_remaining_time(user_id)
    message_text = '🌟 Hoş Geldiniz! Premium sorgu panelimizi kullanmak için butonlara tıklayın:\n\nhttps://t.me/lunabioo'
    if remaining_time:
        message_text = f"{remaining_time}\n\n{message_text}"
    
    await update.message.reply_text(message_text, reply_markup=reply_markup, parse_mode="Markdown")

# 24 saatte bir anahtar süresini kontrol eden iş
async def check_key_expiration(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        with open(LOG_DIR / 'keys.json', 'r') as file:
            keys = json.load(file)
        
        expired_keys = []
        expiring_soon_keys = []
        now = datetime.now(timezone.utc)
        one_day_later = now + timedelta(days=1)
        
        # Daha önce bildirilen anahtarları tut
        notified_file = LOG_DIR / 'notified_keys.txt'
        notified_keys = set()
        if notified_file.exists():
            with open(notified_file, 'r') as f:
                notified_keys = set(line.strip() for line in f if line.strip())
        
        for key, value in keys.items():
            expiry_date = datetime.fromisoformat(value['expiry'])
            
            # Süresi dolmuş anahtarlar
            if expiry_date <= now:
                expired_keys.append((key, value))
            # 1 gün kalan anahtarlar
            elif expiry_date <= one_day_later:
                expiring_soon_keys.append((key, value, expiry_date))
        
        # Süresi dolmuş anahtarları sil
        for key, _ in expired_keys:
            keys.pop(key)
            # Bildirilen listeden de kaldır
            if key in notified_keys:
                notified_keys.discard(key)
        
        # Veritabanını güncelle
        if expired_keys:
            with open(LOG_DIR / 'keys.json', 'w') as file:
                json.dump(keys, file)
            logger.info(f"Expired keys removed: {[k[0] for k in expired_keys]}")
        
        # 1 gün kalan anahtarları SADECE ÖNCEDEKİ BİLDİRİM YOKSA admin'e bildir
        keys_to_notify = [k for k in expiring_soon_keys if k[0] not in notified_keys]
        
        if keys_to_notify:
            message = "⚠️ SURELERİ YAKLAŞAN ANAHTARLAR ⚠️\n"
            message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            for key, value, expiry_date in keys_to_notify:
                hours_left = (expiry_date - now).total_seconds() / 3600
                message += f"🔑 Anahtar: `{key}`\n"
                message += f"📊 ID: `{key}`\n"
                message += f"👥 Kullanıcı: {len(value['users'])}/{value['max_users']}\n"
                message += f"⏳ Kalan: {hours_left:.1f} saat\n"
                message += f"📅 Bitiş: {expiry_date.strftime('%d.%m.%Y %H:%M')}\n"
                message += "─────────────────────────────────\n\n"
                # Bildirilen listesine ekle
                notified_keys.add(key)
            
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=message,
                    parse_mode="Markdown"
                )
                logger.info(f"Admin bildirildi: {len(keys_to_notify)} anahtar süresi yaklaşıyor")
            except Exception as e:
                logger.error(f"Admin bildirimi gönderirken hata: {e}")
        
        # Bildirilen anahtarları dosyaya kaydet
        with open(notified_file, 'w') as f:
            for key in notified_keys:
                f.write(f"{key}\n")
    
    except FileNotFoundError:
        logger.error("keys.json file not found")

# Bot token ve admin ID'sini buraya ekleyin
TOKENS = [
    '8200302313:AAHNnN0A4pIy9YcmlEV8H5T7Cf-6ANfEfyA',
    '8074806476:AAHVa9hYULQC0qFpMEaK4OE9k7_J-n1r4hU',
    '7299932513:AAH9Xgg2yIExBUEKtwXNGmkfYm75gZFA9xI',
]
ADMIN_ID = '6401348044'
GROUP_INVITE_LINK2 = 'https://t.me/+aQXhakQKLgswMWI0'
CHANNEL_ID = '-1001504372194'  # Kanal ID'si (örnek: @your_channel_id)
LOG_DIR = Path(__file__).parent / 'logs_bot2'
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Loglama ayarları
logging.basicConfig(
    filename=LOG_DIR / 'soyagaci_log.txt',  # Log dosyası adı
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Admin'e bildiri gönderme fonksiyonu
async def notify_admin(context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(chat_id=ADMIN_ID, text="Bot çalışıyor")

# Sorgu paneli butonları - Kategori seçimi
async def send_sorgu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Premium Sorgulama Paneli - Kategori Seçimi"""
    
    # Kullanıcı ID'sini al
    if update.callback_query:
        user_id = update.callback_query.from_user.id
    else:
        user_id = update.message.from_user.id
    
    keyboard = [
        [InlineKeyboardButton("👤 Kişi", callback_data='cat_kisi_aile'), InlineKeyboardButton("📱 GSM", callback_data='cat_gsm')],
        [InlineKeyboardButton("🏠 Adres", callback_data='cat_adres'), InlineKeyboardButton("🏛️ Tapu", callback_data='cat_tapu')],
        [InlineKeyboardButton("🏢 İşyeri", callback_data='cat_isyeri'), InlineKeyboardButton("💳 Mali", callback_data='cat_mali')],
        [InlineKeyboardButton("⚖️ Hukuki", callback_data='cat_hukuki'), InlineKeyboardButton("📷 Vesika", callback_data='vesika_sorgu')],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    remaining_time = get_user_remaining_time(user_id)
    remaining_info = ""
    if remaining_time:
        remaining_info = f"⏳ {remaining_time}\n"
    
    message_text = (
        f"{remaining_info}"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔍 PREMIUM SORGULAMA PANELİ\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Kategoriyi seçin:"
    )
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(message_text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(message_text, reply_markup=reply_markup, parse_mode="Markdown")

# Kişi & Aile Sorgularını Göster
async def show_kisi_aile_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("👤 Ad Soyad", callback_data='ad_soyad_sorgu')],
        [InlineKeyboardButton("🪪 TC Sorgusu", callback_data='tc_sorgu')],
        [InlineKeyboardButton("👥 2 İsimli", callback_data='iki_isim_sorgu')],
        [InlineKeyboardButton("🔰 Sülale", callback_data='sulale_tc_sorgu')],
        [InlineKeyboardButton("👨‍👩‍👧 Aile", callback_data='aile_sorgu')],
        [InlineKeyboardButton("🚀 Aile Pro", callback_data='ailepro_sorgu')],
        [InlineKeyboardButton("🔎 Aile Detay", callback_data='ailedetay_sorgu')],
        [InlineKeyboardButton("🌳 Soy Ağacı", callback_data='soyagaci_sorgu')],
        [InlineKeyboardButton("👧 Çocuk", callback_data='cocuksorgu_sorgu')],
        [InlineKeyboardButton("🌟TC Pro", callback_data='tcpro_sorgu')],
        [InlineKeyboardButton("◀️ Geri", callback_data='sorgu_paneli')],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text("👤 Kişi & Aile Sorgularını Seçin:", reply_markup=reply_markup, parse_mode="Markdown")

# GSM Sorgularını Göster
async def show_gsm_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📞 GSM→TC", callback_data='gsm_tc_sorgu')],
        [InlineKeyboardButton("🆔 TC→GSM", callback_data='tc_gsm_sorgu')],
        [InlineKeyboardButton("⭐ GSM Pro", callback_data='gsmpro_sorgu')],
        [InlineKeyboardButton("🔄 GSM Güncel", callback_data='gsmnew_sorgu')],
        [InlineKeyboardButton("📍 GSM Adres", callback_data='gsmadres_sorgu')],
        [InlineKeyboardButton("🔑 GSM Çözümle", callback_data='gsmcoz_sorgu')],
        [InlineKeyboardButton("📦 Multi GSM", callback_data='gsmcoklu_sorgu')],
        [InlineKeyboardButton("📋 Multi TC+GSM", callback_data='coklutcgsm_sorgu')],
        [InlineKeyboardButton("💎 TC-GSM-TC", callback_data='tcgsmgsmtc_sorgu')],
        [InlineKeyboardButton("🚀 V2 TC-GSM", callback_data='tcgsmgsmtcv2_sorgu')],
        [InlineKeyboardButton("◀️ Geri", callback_data='sorgu_paneli')],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text("📱 GSM Sorgularını Seçin:", reply_markup=reply_markup, parse_mode="Markdown")

# Adres Sorgularını Göster
async def show_adres_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🏠 Adres", callback_data='adres_sorgu')],
        [InlineKeyboardButton("📍 Konum", callback_data='konum_sorgu')],
        [InlineKeyboardButton("🔄 Adres Güncel", callback_data='adresnew_sorgu')],
        [InlineKeyboardButton("📊 Adres 2025", callback_data='adresv_sorgu')],
        [InlineKeyboardButton("◀️ Geri", callback_data='sorgu_paneli')],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text("🏠 Adres Sorgularını Seçin:", reply_markup=reply_markup, parse_mode="Markdown")

# Tapu Sorgularını Göster
async def show_tapu_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📋 Tapu", callback_data='tapu_sorgu')],
        [InlineKeyboardButton("📦 Ada Parsel", callback_data='parsel_sorgu')],
        [InlineKeyboardButton("🗾 Parsel İl-İlçe", callback_data='parselililce_sorgu')],
        [InlineKeyboardButton("◀️ Geri", callback_data='sorgu_paneli')],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text("🏛️ Tapu Sorgularını Seçin:", reply_markup=reply_markup, parse_mode="Markdown")

# İşyeri Sorgularını Göster
async def show_isyeri_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🏢 İşyeri Sahibi", callback_data='isyeriyt_sorgu')],
        [InlineKeyboardButton("👨‍💼 Çalışan", callback_data='calisan_sorgu')],
        [InlineKeyboardButton("💼 SGK", callback_data='sgk_sorgu')],
        [InlineKeyboardButton("◀️ Geri", callback_data='sorgu_paneli')],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text("🏢 İşyeri Sorgularını Seçin:", reply_markup=reply_markup, parse_mode="Markdown")

# Mali Sorgularını Göster
async def show_mali_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("💳 İBAN", callback_data='iban_sorgu')],
        [InlineKeyboardButton("🎓 Okul No", callback_data='okulno_sorgu')],
        [InlineKeyboardButton("🚗 Plaka", callback_data='plaka_sorgu')],
        [InlineKeyboardButton("◀️ Geri", callback_data='sorgu_paneli')],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text("💳 Mali Sorgularını Seçin:", reply_markup=reply_markup, parse_mode="Markdown")

# Hukuki Sorgularını Göster
async def show_hukuki_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("⚖️ Polis", callback_data='polis_sorgu')],
        [InlineKeyboardButton("🌐 Mülteci", callback_data='multeci_sorgu')],
        [InlineKeyboardButton("◀️ Geri", callback_data='sorgu_paneli')],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text("⚖️ Hukuki Sorgularını Seçin:", reply_markup=reply_markup, parse_mode="Markdown")

# Ad Soyad sorgulama
async def ad_soyad_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.answer("🚫 Ban yediniz, botu kullanamazsınız!", show_alert=True)
        return
    
    if not has_user_entered_key(user_id):
        await query.answer("🔑 Lütfen önce anahtar girin!", show_alert=True)
        return
    
    await query.answer()
    await query.message.reply_text("🔍 Lütfen geçerli bir ad ve soyad belirtin. İsteğe bağlı olarak nüfus ili de ekleyebilirsiniz.\n\nÖrnek: /sorgu GAZAL BAYRAM ŞIRNAK", parse_mode="Markdown")

# TC sorgulama
async def tc_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.answer("🚫 Ban yediniz, botu kullanamazsınız!", show_alert=True)
        return
    
    if not has_user_entered_key(user_id):
        await query.answer("🔑 Lütfen önce anahtar girin!", show_alert=True)
        return

    await query.answer()
    await query.message.reply_text("🔍 Lütfen geçerli bir TC kimlik numarası belirtin.\n\nÖrnek: /tcsorgu 11111111110", parse_mode="Markdown")
    
# Aile sorgulama
async def aile_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.answer("🚫 Ban yediniz, botu kullanamazsınız!", show_alert=True)
        return
    
    if not has_user_entered_key(user_id):
        await query.answer("🔑 Lütfen önce anahtar girin!", show_alert=True)
        return

    await query.answer()
    await query.message.reply_text("🔍 Lütfen geçerli bir TC kimlik numarası belirtin.\n\nÖrnek: /aile 11111111110", parse_mode="Markdown")

# TC Pro sorgulama
async def tcpro_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.answer("🚫 Ban yediniz, botu kullanamazsınız!", show_alert=True)
        return
    
    if not has_user_entered_key(user_id):
        await query.answer("🔑 Lütfen önce anahtar girin!", show_alert=True)
        return

    await query.answer()
    await query.message.reply_text("🔍 Lütfen geçerli bir TC kimlik numarası belirtin.\n\nÖrnek: /tcpro 11111111110", parse_mode="Markdown")
    
#Soyagacı sorgulama
async def soyagaci_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.answer("🚫 Ban yediniz, botu kullanamazsınız!", show_alert=True)
        return
    
    if not has_user_entered_key(user_id):
        await query.answer("🔑 Lütfen önce anahtar girin!", show_alert=True)
        return

    await query.answer()
    await query.message.reply_text("🔍 Lütfen geçerli bir TC kimlik numarası belirtin.\n\nÖrnek: /soyagaci 11111111110", parse_mode="Markdown")

# İki isimli sorgu
async def iki_isim_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.answer("🚫 Ban yediniz, botu kullanamazsınız!", show_alert=True)
        return
    
    if not has_user_entered_key(user_id):
        await query.answer("🔑 Lütfen önce anahtar girin!", show_alert=True)
        return
    
    await query.answer()
    await query.message.reply_text("🔍 Lütfen geçerli bir ad, ikinci ad ve soyad belirtin. İsteğe bağlı olarak nüfus ili de ekleyebilirsiniz.\n\nÖrnek: /ad2sorgu MUHAMMED GAZAL BAYRAM ŞIRNAK", parse_mode="Markdown")

# Adres Sorgulama 
async def adres_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.answer("🚫 Ban yediniz, botu kullanamazsınız!", show_alert=True)
        return
    if not has_user_entered_key(user_id):
        await query.answer("🔑 Lütfen önce anahtar girin!", show_alert=True)
        return
    await query.answer()
    await query.message.reply_text("🔍 Lütfen geçerli bir TC kimlik numarası belirtin.\n\nÖrnek: /adres 11111111110", parse_mode="Markdown")
    
# Tapu Sorgulama
async def tapu_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.answer("🚫 Ban yediniz, botu kullanamazsınız!", show_alert=True)
        return
    if not has_user_entered_key(user_id):
        await query.answer("🔑 Lütfen önce anahtar girin!", show_alert=True)
        return
    await query.answer()
    await query.message.reply_text("🔍 Lütfen geçerli bir TC kimlik numarası belirtin.\n\nÖrnek: /tapu 11111111110", parse_mode="Markdown")
    
# İşyeri Yöneticisi
async def isyeriyt_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.answer("🚫 Ban yediniz, botu kullanamazsınız!", show_alert=True)
        return
    if not has_user_entered_key(user_id):
        await query.answer("🔑 Lütfen önce anahtar girin!", show_alert=True)
        return
    await query.answer()
    await query.message.reply_text("🔍 Lütfen geçerli bir TC kimlik numarası belirtin.\n\nÖrnek: /isyeriyt 11111111110", parse_mode="Markdown")
    
# Polis Sorgulaması
async def polis_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.answer("🚫 Ban yediniz, botu kullanamazsınız!", show_alert=True)
        return
    if not has_user_entered_key(user_id):
        await query.answer("🔑 Lütfen önce anahtar girin!", show_alert=True)
        return
    await query.answer()
    await query.message.reply_text("🔍 Lütfen geçerli bir TC kimlik numarası belirtin.\n\nÖrnek: /polis 11111111110", parse_mode="Markdown")
    
# TC-GSM-TC Sorgulaması
async def tcgsmgsmtc_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.answer("🚫 Ban yediniz, botu kullanamazsınız!", show_alert=True)
        return
    if not has_user_entered_key(user_id):
        await query.answer("🔑 Lütfen önce anahtar girin!", show_alert=True)
        return
    await query.answer()
    await query.message.reply_text("🔍 Lütfen geçerli bir TC kimlik numarası belirtin.\n\nÖrnek: /tcgsmgsmtc 11111111110", parse_mode="Markdown")

# TC-GSM-TC v2 Sorgulaması
async def tcgsmgsmtcv2_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.answer("🚫 Ban yediniz, botu kullanamazsınız!", show_alert=True)
        return
    if not has_user_entered_key(user_id):
        await query.answer("🔑 Lütfen önce anahtar girin!", show_alert=True)
        return
    await query.answer()
    await query.message.reply_text("🔍 Lütfen geçerli bir TC kimlik numarası belirtin.\n\nÖrnek: /tcgsmgsmtcv2 11111111110", parse_mode="Markdown")

# Okul Numarası Sorgulaması
async def okulno_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.answer("🚫 Ban yediniz, botu kullanamazsınız!", show_alert=True)
        return
    if not has_user_entered_key(user_id):
        await query.answer("🔑 Lütfen önce anahtar girin!", show_alert=True)
        return
    await query.answer()
    await query.message.reply_text("🔍 Lütfen geçerli bir TC kimlik numarası belirtin.\n\nÖrnek: /okulno 11111111110", parse_mode="Markdown")
    
# SGK Sorgulaması
async def sgk_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.answer("🚫 Ban yediniz, botu kullanamazsınız!", show_alert=True)
        return
    if not has_user_entered_key(user_id):
        await query.answer("🔑 Lütfen önce anahtar girin!", show_alert=True)
        return
    await query.answer()
    await query.message.reply_text("🔍 Lütfen geçerli bir TC kimlik numarası belirtin.\n\nÖrnek: /sgk 11111111110", parse_mode="Markdown")

# Plaka Sorgulaması
async def plaka_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.answer("🚫 Ban yediniz, botu kullanamazsınız!", show_alert=True)
        return
    if not has_user_entered_key(user_id):
        await query.answer("🔑 Lütfen önce anahtar girin!", show_alert=True)
        return
    await query.answer()
    await query.message.reply_text("🔍 Lütfen geçerli bir plaka belirtin.\n\nÖrnek: /plaka 34bu6666", parse_mode="Markdown")

# İban Sorgulaması
async def iban_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.answer("🚫 Ban yediniz, botu kullanamazsınız!", show_alert=True)
        return
    if not has_user_entered_key(user_id):
        await query.answer("🔑 Lütfen önce anahtar girin!", show_alert=True)
        return
    
    await query.answer()
    await query.message.reply_text("🔍 Lütfen geçerli bir IBAN belirtin.\n\nÖrnek: /iban TR310006400000163180184752", parse_mode="Markdown")


         # Gsm Çözümle
async def gsmcoz_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    await query.answer()
    await query.message.reply_text("🔍 Lütfen geçerli bir GSM numarası belirtin.\n\nÖrnek: /gsmcoz 53685944524", parse_mode="Markdown")

         # Multeci Sorgu
async def multeci_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    await query.answer()
    await query.message.reply_text("🔍 Lütfen geçerli bir TC belirtin.\n\nÖrnek: /multeci 99000100650", parse_mode="Markdown")

         # gsm adres 2025
async def gsmadres_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    await query.answer()
    await query.message.reply_text("🔍 Lütfen geçerli bir GSM numarası belirtin.\n\nÖrnek: /gsmadres 53685944524", parse_mode="Markdown")

         # Parsel Sorgu
async def parsel_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    await query.answer()
    await query.message.reply_text("🔍 Lütfen geçerli bir ada-parsel belirtin.\n\nÖrnek: /parsel 20905-2", parse_mode="Markdown")

#Gsm Pro
async def gsmpro_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    await query.answer()
    await query.message.reply_text("🔍 Lütfen geçerli bir GSM numarası belirtin.\n\nÖrnek: /gsmpro 53685944524", parse_mode="Markdown")

#Çocuk Sorgu
async def cocuksorgu_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    await query.answer()
    await query.message.reply_text("🔍 Lütfen geçerli bir TC belirtin.\n\nÖrnek: /cocuksorgu 53685944524", parse_mode="Markdown")


#Ada Parsel İL iLCE
async def parselililce_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    await query.answer()
    await query.message.reply_text("🔍 Lütfen geçerli bir ada-parsel ve il-ilçe belirtin.\n\nÖrnek: /parselililce 20905-2-ANKARA-ALTINDAĞ", parse_mode="Markdown")
    
#adres konum
async def konum_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    await query.answer()
    await query.message.reply_text("🔍 Lütfen geçerli bir TC belirtin.\n\nÖrnek: /konum 16901342354", parse_mode="Markdown")

#aile Pro
async def ailepro_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    await query.answer()
    await query.message.reply_text("🔍 Lütfen geçerli bir TC belirtin.\n\nÖrnek: /ailepro 16901342354", parse_mode="Markdown")

#aile detay
async def ailedetay_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    await query.answer()
    await query.message.reply_text("🔍 Lütfen geçerli bir TC belirtin.\n\nÖrnek: /ailedetay 16901342354", parse_mode="Markdown")

#calışan Detay
async def calisan_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    await query.answer()
    await query.message.reply_text("🔍 Lütfen geçerli bir TC belirtin.\n\nÖrnek: /calisan 16901342354", parse_mode="Markdown")
    
    
#vesika
async def vesika_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    await query.answer()
    await query.message.reply_text("🔍 Lütfen geçerli bir TC belirtin.\n\nÖrnek: /vesika 16901342354", parse_mode="Markdown")
    
    
 #adres 2025
async def adresv_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    await query.answer()
    await query.message.reply_text("🔍 Lütfen geçerli bir TC belirtin.\n\nÖrnek: /adresv 16901342354", parse_mode="Markdown")


 #multi gsm
async def gsmcoklu_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    await query.answer()
    await query.message.reply_text("🔍 Lütfen birden fazla GSM numarası belirtin (alt alta).\n\nÖrnek:\n/gsmcoklu\n53685944524\n53685944525", parse_mode="Markdown")

 #multi Tc
async def coklutcgsm_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    await query.answer()
    await query.message.reply_text("🔍 Lütfen birden fazla GSM numarası belirtin (alt alta).\n\nÖrnek:\n/coklutcgsm\n53685944524\n53685944525", parse_mode="Markdown")


@ensure_channel_and_key
async def sorgu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Ad-Soyad Sorgulaması - Modern ve geliştirilmiş versiyon
    
    Kullanım: /sorgu AD SOYAD [İL]
    Örnek: /sorgu GAZAL BAYRAM ŞIRNAK
    """
    user_id = update.message.from_user.id
    
    # Parametreleri kontrol et
    if len(context.args) < 2:
        await update.message.reply_text(
            "🔍 Ad-Soyad Sorgulaması\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Doğru Kullanım:\n"
            "`/sorgu AD SOYAD [İL]`\n\n"
            "Örnekler:\n"
            "• `/sorgu GAZAL BAYRAM`\n"
            "• `/sorgu GAZAL BAYRAM ŞIRNAK`\n"
            "• `/sorgu MEHMET YILDIRIM İSTANBUL`",
            parse_mode="Markdown"
        )
        return
    
    adi = context.args[0].upper()
    soyadi = context.args[1].upper()
    nufusil = context.args[2].upper() if len(context.args) > 2 else ""
    
    # Status mesajı gönder
    status_msg = await update.message.reply_text(
        f"🔍 Sorgulanıyor...\n"
        f"👤 Ad: `{adi}`\n"
        f"👤 Soyad: `{soyadi}`\n"
        f"{'📍 İl: `' + nufusil + '`' if nufusil else ''}"
    )
    
    # API URL'sini oluştur
    url = f'http://localhost/101m/101m-ad-soyad.php?adi={adi}&soyadi={soyadi}'
    if nufusil:
        url += f'&nufusil={nufusil}'
    
    try:
        # API'ye istek yap (timeout: 120 saniye)
        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                data = await response.json()
        
        # Sonuç kontrolü
        if not data or (isinstance(data, list) and len(data) == 0):
            await status_msg.edit_text("🚫 Sorguya ait sonuç bulunamadı.")
            return
        
        # Dosya oluştur
        output_file = LOG_DIR / 'sonuc_adsoyad.txt'
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        
        # Formatlı çıktı hazırla
        content_lines = [
            "═" * 70,
            "🌟 PREMIUM AD-SOYAD SORGU SONUCU 🌟",
            "═" * 70,
            f"\n📊 Sorgu Bilgileri:",
            f"👤 Ad        : {adi}",
            f"👤 Soyad     : {soyadi}",
            f"{'📍 İl        : ' + nufusil if nufusil else ''}",
            f"\n📋 Bulunan Kişiler: {len(data)}\n",
            "═" * 70,
            ""
        ]
        
        if isinstance(data, list):
            for idx, user in enumerate(data, 1):
                content_lines.extend([
                    f"👤 KİŞİ #{idx}",
                    "─" * 70,
                    f"🆔 ID               : {user.get('id', '-')}",
                    f"🪪 TC               : {user.get('TC', '-')}",
                    f"👤 Adı              : {user.get('ADI', '-')}",
                    f"👤 Soyadı           : {user.get('SOYADI', '-')}",
                    f"📅 Doğum Tarihi     : {user.get('DOGUMTARIHI', '-')}",
                    f"\n📍 NÜFUS BİLGİLERİ:",
                    f"   ├─ İl   : {user.get('NUFUSIL', '-')}",
                    f"   └─ İlçe : {user.get('NUFUSILCE', '-')}",
                    f"\n👨‍👩‍👧 AİLE BİLGİLERİ:",
                    f"   ├─ Anne Adı  : {user.get('ANNEADI', '-')}",
                    f"   ├─ Anne TC   : {user.get('ANNETC', '-')}",
                    f"   ├─ Baba Adı  : {user.get('BABAADI', '-')}",
                    f"   ├─ Baba TC   : {user.get('BABATC', '-')}",
                    f"   └─ Uyruk     : {user.get('UYRUK', '-')}",
                    "",
                    "═" * 70,
                    ""
                ])
        
        content_lines.extend([
            f"\n🔐API-BY-LUNA",
            f"⏰ Sorgu Zamanı: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
        ])
        
        # Dosyaya yaz
        async with aiofiles.open(output_file, 'w', encoding='utf-8') as file:
            await file.write("\n".join(content_lines))
        
        # Dosyayı gönder
        with open(output_file, 'rb') as f:
            await update.message.reply_document(
                document=InputFile(f, filename=f"adsoyad_{adi}_{soyadi}.txt"),
                caption=(
                    f"✅ Ad-Soyad Sorgusu Tamamlandı!\n"
                    f"📊 {len(data)} kişi bulundu"
                ),
                parse_mode="Markdown"
            )
        
        # Satır sayısını kontrol et
        with open(output_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            line_count = len(lines)
        
        # 90 satırdan az ise metin olarak da gönder
        if line_count <= 90:
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 4096 karakterden büyükse parçalara böl
                if len(content) > 4090:
                    for i in range(0, len(content), 4090):
                        chunk = content[i:i+4090]
                        await update.message.reply_text(f"```\n{chunk}\n```", parse_mode='Markdown')
                else:
                    await update.message.reply_text(f"```\n{content}\n```", parse_mode='Markdown')
        
        await status_msg.delete()
    
    except asyncio.TimeoutError:
        await status_msg.edit_text("⏱️ Zaman Aşımı!\nSorgu 3 dakikadan uzun sürdü.\nLütfen daha sonra tekrar deneyiniz.")
    except ValueError:
        await status_msg.edit_text("🚫 API Hatası!\nSunucudan geçersiz veri alındı (JSON parse hatası).")
    except aiohttp.ClientError as e:
        await status_msg.edit_text(f"🚫 Bağlantı Hatası!\n{str(e)[:100]}")
    except Exception as e:
        logger.error(f"Sorgu command error: {e}")
        await status_msg.edit_text(f"🚫 Beklenmeyen Hata!\n{str(e)[:100]}")

# TC - SORGU 
@ensure_channel_and_key
async def tcsorgu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    if len(context.args) != 1:
        await update.message.reply_text("🔍 Lütfen geçerli bir TC kimlik numarası belirtin.\n\nÖrnek: /tcsorgu 11111111110", parse_mode="Markdown")
        return
    
    tc = context.args[0]
    url = f'http://localhost/101m/101m-tc-sorgulama.php?tc={tc}'
    
    try:
        response = await async_api_request(url, timeout=15)
        response_text = response.text  # API'den gelen ham yanıt

        # Uzun mesajları böl ve güzel formatla
        MAX_LENGTH = 4000
        for i in range(0, len(response_text), MAX_LENGTH):
            await update.message.reply_text(f"```markdown\n🌟 Premium API Yanıtı:\n{response_text[i:i+MAX_LENGTH]}\n```", parse_mode="Markdown")

    except Exception as e:
        error_msg = "Zaman aşımı" if "Zaman aşımı" in str(e) else str(e)
        await update.message.reply_text(f"🚫 Hata oluştu:\n```{error_msg}```", parse_mode="Markdown")

# Tc GSM 
@ensure_channel_and_key
async def tcgsm_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    if len(context.args) != 1:
        await update.message.reply_text("🔍 Lütfen geçerli bir TC kimlik numarası belirtin.\n\nÖrnek: /tcgsm 5466324433", parse_mode="Markdown")
        return
    
    gsm = context.args[0]
    url = f'http://localhost/116m/116m-tc-sorgu.php?numara={gsm}'
        
    try:
        response = await async_api_request(url, timeout=15)
        response_text = response.text  # API'den gelen ham yanıt

        await update.message.reply_text(f"```markdown\n🌟 Premium API Yanıtı:\n{response_text}\n```", parse_mode="Markdown")
        

    except Exception as e:
        error_msg = "Zaman aşımı" if "Zaman aşımı" in str(e) else str(e)
        await update.message.reply_text(f"🚫 Hata oluştu:\n```{error_msg}```", parse_mode="Markdown")

# Kullanıcıdan GSM TC sorgu komutunu işleme
@ensure_channel_and_key
async def gsmtc_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    if len(context.args) != 1:
        await update.message.reply_text("🔍 Lütfen geçerli bir numara belirtin.\n\nÖrnek: /gsmtc 5356834458", parse_mode="Markdown")
        return
    
    numara = context.args[0]
    
    url = f'http://localhost/116m/gsmdetay.php?gsm={numara}'
    
    try:
        response = await async_api_request(url, timeout=15)
    except Exception as e:
        error_msg = "Zaman aşımı" if "Zaman aşımı" in str(e) else str(e)
        await update.message.reply_text(f"🚫 Hata: {error_msg}", parse_mode="Markdown")
        return
    
    try:
        # Yanıtı UTF-8 olarak çöz ve BOM'u kaldır
        content = response.content.decode('utf-8-sig')
        # JSON yanıtı çözümle
        data = json.loads(content)
    except json.JSONDecodeError:
        await update.message.reply_text("🚫 Geçersiz JSON yanıtı alındı.", parse_mode="Markdown")
        return

    # API yanıtını kontrol et ve kullanıcıya ilet
    if not data.get("success"):
        await update.message.reply_text("🚫 Sorguya ait sonuç bulunamadı.", parse_mode="Markdown")
        return

    user_data = data.get("Data", [])
    if not user_data:
        await update.message.reply_text("🚫 Sorguya ait sonuç bulunamadı.", parse_mode="Markdown")
        return

    user_info = user_data[0]
    mesaj = (
        f"🌟 Premium Sorgu Sonucu 🌟\n\n"
        f"🔹 TC: {user_info.get('TC', 'Bilinmiyor')}\n"
        f"🔹 ADI: {user_info.get('ADI', 'Bilinmiyor')}\n"
        f"🔹 SOYADI: {user_info.get('SOYADI', 'Bilinmiyor')}\n"
        f"🔹 DOGUMTARIHI: {user_info.get('DOGUMTARIHI', 'Bilinmiyor')}\n"
        f"🔹 NUFUSIL: {user_info.get('NUFUSIL', 'Bilinmiyor')}\n"
        f"🔹 NUFUSILCE: {user_info.get('NUFUSILCE', 'Bilinmiyor')}\n"
        f"🔹 ANNEADI: {user_info.get('ANNEADI', 'Bilinmiyor')}\n"
        f"🔹 ANNETC: {user_info.get('ANNETC', 'Bilinmiyor')}\n"
        f"🔹 BABAADI: {user_info.get('BABAADI', 'Bilinmiyor')}\n"
        f"🔹 BABATC: {user_info.get('BABATC', 'Bilinmiyor')}\n"
        f"🔹 UYRUK: {user_info.get('UYRUK', 'Bilinmiyor')}\n"
    )
    await update.message.reply_text(mesaj, parse_mode="Markdown")


@ensure_channel_and_key
async def ad2_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Modern 2 İsimli Sorgu - Async & Formatted"""
   
    if not update.message:
        return
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text("🚫 Banlandınız, botu kullanamazsınız.")
        return

    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "👥 2 İsimli Sorgu\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Doğru Kullanım:\n"
            "`/ad2sorgu Ad İkinciAd Soyad [İl]`\n\n"
            "Örnekler:\n"
            "• `/ad2sorgu MEHMET EMRE YILDIRIM`\n"
            "• `/ad2sorgu AYŞE FATMA KAYA İSTANBUL`",
            parse_mode="Markdown"
        )
        return

    # SOYAD HER ZAMAN SON KELİME
    if len(args) >= 4:
        # 4+ args: Ad(lar) İkinciAd(lar) Soyad İl
        nufusil = args[-1].upper()
        soyadi = args[-2].upper()
        adi = " ".join(args[:-2]).upper()
    else:
        # 3 args: Ad(lar) İkinciAd(lar) Soyad
        nufusil = ""
        soyadi = args[-1].upper()
        adi = " ".join(args[:-1]).upper()

    url = f"http://localhost/101m/101m-ad-ad2-soyad.php?adi={adi}&soyadi={soyadi}"
    if nufusil:
        url += f"&nufusil={nufusil}"

    # Status mesajı
    searching_msg = await update.message.reply_text(
        "🔍 Aranıyor...\n"
        f"👤 Ad: `{adi}`\n"
        f"👤 Soyad: `{soyadi}`\n"
        f"{'📍 İl: `' + nufusil + '`' if nufusil else ''}\n\n"
        "⏳ Lütfen bekleyin, bu işlem biraz sürebilir.",
        parse_mode="Markdown"
    )

    try:
        # Async API çağrısı (120 saniye timeout)
        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                data = await response.json()

        if isinstance(data, dict) and "hata" in data:
            await searching_msg.edit_text(f"🚫 {data['hata']}")
            return
        if not data:
            await searching_msg.edit_text("🚫 Bu isimle eşleşen kimse bulunamadı.")
            return

    except asyncio.TimeoutError:
        await searching_msg.edit_text("⏱️ Zaman Aşımı!\nSorgu 2 dakikadan uzun sürdü.\nDaha spesifik sorgu deneyin (İl ekleyin).")
        return
    except Exception as e:
        await searching_msg.edit_text(f"🚫 Hata: {str(e)[:100]}")
        return

    # Güncellemeleri başlat
    await searching_msg.edit_text(f"📊 {len(data)} kişi bulundu!\n📝 Dosya hazırlanıyor...")

    # DOSYA OLUŞTUR
    dosya_yolu = LOG_DIR / 'sonuc_ad2.txt'
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(dosya_yolu, "w", encoding="utf-8") as f:
            # Header
            f.write("╔" + "═" * 68 + "╗\n")
            f.write("║" + " 🌟 PREMIUM 2 İSİMLİ SORGU SONUCU 🌟 ".center(68) + "║\n")
            f.write("╚" + "═" * 68 + "╝\n\n")
            
            # Sorgu Bilgileri
            f.write("📋 SORGU BİLGİLERİ:\n")
            f.write(f"👤 Ad Bilgisi    : {adi}\n")
            f.write(f"👤 Soyadı        : {soyadi}\n")
            if nufusil:
                f.write(f"📍 Nüfus İli     : {nufusil}\n")
            f.write(f"📊 Bulunan Kişi  : {len(data)}\n")
            f.write("⏰ Sorgu Zamanı  : " + datetime.now().strftime('%d.%m.%Y %H:%M:%S') + "\n")
            f.write("\n" + "─" * 70 + "\n\n")
            
            # Kişi Verileri
            for i, kisi in enumerate(data, 1):
                f.write(f"👤 KİŞİ #{i}\n")
                f.write("├─ " + "─" * 66 + "\n")
                f.write(f"├─ 🆔 TC Kimlik   : {kisi.get('TC', '-')}\n")
                f.write(f"├─ 👤 Adı        : {kisi.get('ADI', '-')}\n")
                f.write(f"├─ 👤 Soyadı     : {kisi.get('SOYADI', '-')}\n")
                f.write(f"├─ 📅 Doğum      : {kisi.get('DOGUMTARIHI', '-')}\n")
                f.write(f"├─ 📍 Nüfus İl   : {kisi.get('NUFUSIL', '-')}\n")
                f.write(f"├─ 📍 Nüfus İlçe : {kisi.get('NUFUSILCE', '-')}\n")
                f.write(f"├─ 👩 Anne Adı   : {kisi.get('ANNEADI', '-')}\n")
                f.write(f"├─ 👩 Anne TC    : {kisi.get('ANNETC', '-')}\n")
                f.write(f"├─ 👨 Baba Adı   : {kisi.get('BABAADI', '-')}\n")
                f.write(f"├─ 👨 Baba TC    : {kisi.get('BABATC', '-')}\n")
                f.write(f"└─ 🌍 Uyruk      : {kisi.get('UYRUK', '-')}\n\n")
            
            f.write("─" * 70 + "\n")
            f.write("🔐 API-BY-LUNA\n")

        # 49 MB kontrol
        if os.path.getsize(dosya_yolu) > 49 * 1024 * 1024:
            os.remove(dosya_yolu)
            await searching_msg.edit_text("🚫 Sonuç Çok Büyük!\n\nDosya 49MB'dan büyük.\nDaha spesifik sorgu yapın:\n• İl ekleyin\n• Tam ad yazın")
            return

        # Dosyayı gönder
        with open(dosya_yolu, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=f"Ad2_{adi.replace(' ', '_')}_{soyadi}_{nufusil or 'TUM'}.txt",
                caption=(
                    f"✅ 2 İsimli Sorgu Tamamlandı!\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 {adi} {soyadi}\n"
                    f"📊 {len(data)} kişi bulundu\n"
                    f"{'📍 İl: ' + nufusil + '' if nufusil else ''}"
                ),
                parse_mode="Markdown",
                reply_to_message_id=update.message.message_id
            )

        await searching_msg.delete()

    except Exception as e:
        await searching_msg.edit_text(f"🚫 Dosya yazılırken hata: {str(e)[:100]}")

# Sülale Sorgu Komutu
@ensure_channel_and_key
async def sulale_tc_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    if len(context.args) != 1:
        await update.message.reply_text("🔍 Lütfen geçerli bir TC kimlik numarası belirtin.\n\nÖrnek: /sulale 11111111110", parse_mode="Markdown")
        return
    
    tc = context.args[0]
    
    url = f'http://localhost/101m/101m-tc-sorgulama-sulale.php?tc={tc}'
    
    try:
        response = requests.get(url, timeout=180)
    except requests.Timeout:
        await update.message.reply_text("🚫 Zaman aşımı! Sorgu 3 dakikadan uzun sürdü.", parse_mode="Markdown")
        return
    data = response.json()
    
    output_file = "C:\\Users\\ACER\\Desktop\\loglar\\sonuc_sulale.txt"
    
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write("🌟 Premium Sülale Sorgu Sonucu 🌟\n\n")
        if 'error' in data:
            file.write(f"🚫 Hata: {data['error']}\n")
        else:
            for user in data:
                file.write(f"🔹 ID: {user['id']}\n")
                file.write(f"🔹 TC: {user['TC']}\n")
                file.write(f"🔹 ADI: {user['ADI']}\n")
                file.write(f"🔹 SOYADI: {user['SOYADI']}\n")
                file.write(f"🔹 DOGUMTARIHI: {user['DOGUMTARIHI']}\n")
                file.write(f"🔹 NUFUSIL: {user['NUFUSIL']}\n")
                file.write(f"🔹 NUFUSILCE: {user['NUFUSILCE']}\n")
                file.write(f"🔹 ANNEADI: {user['ANNEADI']}\n")
                file.write(f"🔹 ANNETC: {user['ANNETC']}\n")
                file.write(f"🔹 BABAADI: {user['BABAADI']}\n")
                file.write(f"🔹 BABATC: {user['BABATC']}\n")
                file.write(f"🔹 UYRUK: {user['UYRUK']}\n")
                file.write(f"🔐 API-BY-LUNA\n")
                file.write("─────────────────────\n")
    
    await update.message.reply_document(document=open(output_file, 'rb'), filename='sonuc_sulale.txt', caption="✅ Premium Sülale Sorgu Tamamlandı!", parse_mode="Markdown")
    
# Aile Sorgu
@ensure_channel_and_key
async def aile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """👨‍👩‍👧 Aile - Modernleştirilmiş Aile Sorgulaması"""
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    if len(context.args) != 1:
        await update.message.reply_text(
            "👨‍👩‍👧 AİLE SORGULAMASI\n"
            "═════════════════════════════\n\n"
            "📌 Kullanım: `/aile <TC>`\n"
            "📝 Örnek: `/aile 46024967042`\n\n"
            "ℹ️ Kişinin tüm aile üyelerini getir",
            parse_mode="Markdown"
        )
        return
    
    tc = context.args[0].strip()
    
    if not (tc.isdigit() and len(tc) == 11):
        await update.message.reply_text("❌ Geçersiz TC! 11 haneli rakam giriniz.")
        return
    
    # Progress mesajı
    progress_msg = await update.message.reply_text(
        "🔄 Aile bilgileri sorgulanıyor...\n⏳ Bağlantı kuruluyor..."
    )
    
    url = f'http://localhost/101m/aile.php?tc={tc}'
    
    try:
        response = requests.get(url, timeout=180)
        await progress_msg.edit_text("🔄 Veriler işleniyor...")
        response.raise_for_status()
    except requests.Timeout:
        await progress_msg.edit_text("🚫 Zaman Aşımı!\nSunucu yavaş yanıt veriyor (180s+)")
        return
    except requests.ConnectionError:
        await progress_msg.edit_text("🚫 Bağlantı Hatası!\nSunucuya erişilemiyor")
        return
    except Exception as e:
        await progress_msg.edit_text(f"🚫 Hata: {str(e)[:100]}")
        return
    
    try:
        data = json.loads(response.content.decode('utf-8-sig'))
    except json.JSONDecodeError:
        await progress_msg.edit_text("🚫 *JSON Hatası!\nAPI yanıtı geçersiz")
        return
    
    # Hata kontrolü
    if 'error' in data:
        await progress_msg.edit_text(f"⚠️ Hata!\n{data['error']}")
        return
    
    if 'data' not in data or not data['data']:
        await progress_msg.edit_text("⚠️ Bu TC'ye ait aile bilgisi bulunamadı.")
        return
    
    # Dosya hazırlama
    await progress_msg.edit_text("🔄 Dosya hazırlanıyor...")
    
    family_count = len(data['data'])
    dosya_adi = f"Aile_{tc}_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt"
    dosya_yolu = LOG_DIR / 'aile_results'
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    dosya_yolu.mkdir(parents=True, exist_ok=True)
    dosya_tam_yol = dosya_yolu / dosya_adi
    
    with open(dosya_tam_yol, 'w', encoding='utf-8') as file:
        # Header
        file.write("╔" + "═" * 58 + "╗\n")
        file.write("║" + " 👨‍👩‍👧 AİLE SORGULAMASI SONUCU ".center(58) + "║\n")
        file.write("╚" + "═" * 58 + "╝\n\n")
        
        # Bilgiler
        file.write("📋 SORGU DETAYLARI\n")
        file.write("─" * 60 + "\n")
        file.write(f"🔹 Ana TC Kimlik : {tc}\n")
        file.write(f"🔹 Sorgulama Tarihi : {datetime.now().strftime('%d.%m.%Y - %H:%M:%S')}\n")
        file.write(f"🔹 Toplam Aile Üyesi : {family_count}\n")
        file.write("─" * 60 + "\n\n")
        
        # Aile üyeleri
        file.write("👥 AİLE AĞACI VERİLERİ\n")
        file.write("═" * 60 + "\n\n")
        
        for idx, person in enumerate(data['data'], 1):
            file.write(f"┌─ [{idx:03d}] 👥 {person.get('Yakınlık', '-').upper()}\n")
            file.write(f"├─ 🆔 TC Kimlik      : {person.get('TC', '-')}\n")
            file.write(f"├─ 👤 Ad-Soyad      : {person.get('ADI', '-').upper()} {person.get('SOYADI', '-').upper()}\n")
            file.write(f"├─ 📅 Doğum Tarihi   : {person.get('DOGUMTARIHI', '-')}\n")
            file.write(f"├─ 👩 Anne Adı       : {person.get('ANNEADI', '-').upper() if person.get('ANNEADI') else '-'}\n")
            file.write(f"├─ 🆔 Anne TC        : {person.get('ANNETC', '-')}\n")
            file.write(f"├─ 👨 Baba Adı       : {person.get('BABAADI', '-').upper() if person.get('BABAADI') else '-'}\n")
            file.write(f"├─ 🆔 Baba TC        : {person.get('BABATC', '-')}\n")
            file.write(f"├─ 📍 Nüfus Yeri     : {person.get('NUFUSIL', '-')}/{person.get('NUFUSILCE', '-')}\n")
            file.write(f"└─ 🌍 Uyruk          : {person.get('UYRUK', '-')}\n\n")
        
        # Footer
        file.write("═" * 60 + "\n")
        file.write("📊 İSTATİSTİKLER\n")
        file.write("─" * 60 + "\n")
        file.write(f"✅ Sorgu Başarılı\n")
        file.write(f"👥 Toplam Aile Üyesi: {family_count}\n")
        file.write(f"⏰ İşlem Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n")
        file.write("🔐 API-BY-LUNA | Luna Vip Sorgu\n")
        file.write("═" * 60 + "\n")
    
    # Mesajı sil ve dosyayı gönder
    await progress_msg.delete()
    
    caption = (
        "✅ AİLE SORGULAMASI BAŞARIYLLA TESLİM EDİLDİ\n"
        "═════════════════════════════════════════════════\n\n"
        f"🆔 Ana TC: `{tc}`\n"
        f"👥 Aile Üyeleri: `{family_count} kişi`\n"
        f"📅 Tarih: `{datetime.now().strftime('%d.%m.%Y')}`\n\n"
        "📄 Detaylı rapor aşağıda gönderilmiştir."
    )
    
    try:
        # Dosyayı gönder
        with open(dosya_tam_yol, 'rb') as file:
            await update.message.reply_document(
                document=file,
                filename=dosya_adi,
                caption=caption,
                parse_mode='Markdown'
            )
        
        # Satır sayısını kontrol et
        with open(dosya_tam_yol, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            line_count = len(lines)
        
        # 90 satırdan az ise metin olarak da gönder
        if line_count <= 90:
            with open(dosya_tam_yol, 'r', encoding='utf-8') as f:
                content = f.read()
                # 4096 karakterden büyükse parçalara böl
                if len(content) > 4090:
                    for i in range(0, len(content), 4090):
                        chunk = content[i:i+4090]
                        await update.message.reply_text(f"```\n{chunk}\n```", parse_mode='Markdown')
                else:
                    await update.message.reply_text(f"```\n{content}\n```", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"🚫 Dosya gönderilirken hata oluştu: {str(e)[:150]}")

# TC PRO
@ensure_channel_and_key
async def tcpro_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    if len(context.args) != 1:
        await update.message.reply_text("🔍 Lütfen geçerli bir TC kimlik numarası belirtin.\n\nÖrnek: /tcpro 46024967042", parse_mode="Markdown")
        return
    
    tc = context.args[0]
    
    url = f'http://localhost/109m/tcpro.php?tc={tc}'
    
    try:
        response = requests.get(url, timeout=180)
        response.raise_for_status()  # Raise an error for bad status codes
        data = json.loads(response.content.decode('utf-8-sig'))  # Use utf-8-sig to handle BOM
    except requests.Timeout:
        await update.message.reply_text("🚫 Zaman aşımı! Sorgu 3 dakikadan uzun sürdü.", parse_mode="Markdown")
        return
    except requests.RequestException as e:
        await update.message.reply_text(f"🚫 API isteği başarısız oldu: {e}", parse_mode="Markdown")
        return
    except json.JSONDecodeError:
        await update.message.reply_text("🚫 API yanıtı geçerli bir JSON değil.", parse_mode="Markdown")
        return

    # Check if the required keys are in the response
    required_keys = ['TC', 'ADI', 'SOYADI', 'ANNEADI', 'ANNETC', 'BABAADI', 'BABATC', 'DOGUMTARIHI', 'OLUMTARIHI', 'DOGUMYERI', 'MEMLEKETIL', 'MEMLEKETILCE', 'MEMLEKETKOY', 'ADRESIL', 'ADRESILCE', 'AILESIRANO', 'BIREYSIRANO', 'MEDENIHAL', 'CINSIYET', 'GSM']
    if not all(key in data for key in required_keys):
        await update.message.reply_text("🚫 Sorgu bulunamadı.", parse_mode="Markdown")
        return

    # Directly use the data to format the message
    user = data
    line = "═" * 60
    result = (
        f"{line}\n"
        f"🌟 PREMIUM TC PRO SORGU SONUCU 🌟\n"
        f"{line}\n\n"
        f"🔹 TC: {user['TC']}\n"
        f"🔹 ADI: {user['ADI']}\n"
        f"🔹 SOYADI: {user['SOYADI']}\n"
        f"🔹 ANNEADI: {user['ANNEADI']}\n"
        f"🔹 ANNETC: {user['ANNETC']}\n"
        f"🔹 BABAADI: {user['BABAADI']}\n"
        f"🔹 BABATC: {user['BABATC']}\n"
        f"🔹 DOGUMTARIHI: {user['DOGUMTARIHI']}\n"
        f"🔹 OLUMTARIHI: {user['OLUMTARIHI']}\n"
        f"🔹 DOGUMYERI: {user['DOGUMYERI']}\n"
        f"🔹 MEMLEKETIL: {user['MEMLEKETIL']}\n"
        f"🔹 MEMLEKETILCE: {user['MEMLEKETILCE']}\n"
        f"🔹 MEMLEKETKOY: {user['MEMLEKETKOY']}\n"
        f"🔹 ADRESIL: {user['ADRESIL']}\n"
        f"🔹 ADRESILCE: {user['ADRESILCE']}\n"
        f"🔹 AILESIRANO: {user['AILESIRANO']}\n"
        f"🔹 BIREYSIRANO: {user['BIREYSIRANO']}\n"
        f"🔹 MEDENIHAL: {user['MEDENIHAL']}\n"
        f"🔹 CINSIYET: {user['CINSIYET']}\n"
        f"🔹 GSM: {user['GSM']}\n"
        f"{line}\n"
        f"🔐 API-BY-LUNA\n"
        f"⏰ Sorgu Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
    )
    
    # Dosyaya kaydet
    dosya_yolu = LOG_DIR / 'tcpro_results'
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    dosya_yolu.mkdir(parents=True, exist_ok=True)
    dosya_adi = f"TCPro_{tc}_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt"
    dosya_tam_yol = dosya_yolu / dosya_adi
    
    with open(dosya_tam_yol, 'w', encoding='utf-8') as f:
        f.write(result)
    
    try:
        # Dosyayı gönder
        with open(dosya_tam_yol, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=dosya_adi,
                caption="✅ TC PRO Sorgusu Tamamlandı",
                parse_mode='Markdown'
            )
        
        # 90 satırdan az ise metin olarak da gönder
        with open(dosya_tam_yol, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if len(content) <= 4090:
            await update.message.reply_text(f"```\n{content}\n```", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"🚫 Hata oluştu: {str(e)[:150]}")

# Soyagaci Sorgu
@ensure_channel_and_key
async def soyagaci_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """🌳 Soy Ağacı - Modern Aile Ağacı Sorgulaması"""
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return

    if len(context.args) != 1:
        await update.message.reply_text(
            "🌳 SOY AĞACI SORGULAMASI\n"
            "═════════════════════════════\n\n"
            "📌 Kullanım: `/soyagaci <TC>`\n"
            "📝 Örnek: `/soyagaci 11111111110`\n\n"
            "ℹ️ Aile ağacındaki tüm bireyleri getir",
            parse_mode="Markdown"
        )
        return

    tc = context.args[0].strip()

    if not (tc.isdigit() and len(tc) == 11):
        await update.message.reply_text("❌ Geçersiz TC! 11 haneli rakam giriniz.")
        return

    # Bekleme mesajı (progress gösteriyor)
    progress_msg = await update.message.reply_text(
        "🔄 Soy ağacı sorgulanıyor...\n⏳ Bağlantı kuruluyor..."
    )

    url = f"http://localhost/101m/soyagaci.php?key=lunaxcarma&tc={tc}"

    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        await progress_msg.edit_text("🔄 Veriler işleniyor...")
    except requests.Timeout:
        await progress_msg.edit_text("🚫 **Zaman Aşımı!**\nSunucu yavaş yanıt veriyor (60s+)")
        return
    except requests.ConnectionError:
        await progress_msg.edit_text("🚫 **Bağlantı Hatası!**\nSunucuya erişilemiyor")
        return
    except Exception as e:
        await progress_msg.edit_text(f"🚫 **Hata:** {str(e)[:100]}")
        return

    try:
        html_content = response.content.decode('utf-8-sig')
    except Exception:
        html_content = response.text

    # Hata kontrolü
    if "Gerekli parametreler eksik" in html_content or "hata" in html_content.lower():
        await progress_msg.edit_text(
            "⚠️ **Veri Bulunamadı!**\n\n"
            "Bu TC'ye ait soy ağacı kayıtları sunucuda mevcut değil."
        )
        return

    soup = BeautifulSoup(html_content, 'html.parser')
    rows = soup.find_all('tr')

    if len(rows) <= 1:
        await progress_msg.edit_text("⚠️ Bu TC'ye ait aile bilgisi bulunamadı.")
        return

    # Dosya hazırlama
    await progress_msg.edit_text("🔄 Dosya hazırlanıyor...")
    
    person_count = len(rows) - 1
    dosya_adi = f"Soyagaci_{tc}_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt"
    dosya_yolu = LOG_DIR / 'soyagaci_results'
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    dosya_yolu.mkdir(parents=True, exist_ok=True)
    dosya_tam_yol = dosya_yolu / dosya_adi

    # Dosya oluşturma
    with open(dosya_tam_yol, "w", encoding="utf-8") as f:
        # Header
        f.write("╔" + "═" * 58 + "╗\n")
        f.write("║" + " 🌳 SOY AĞACI - AİLE AĞACI SORGULAMA SONUCU ".center(58) + "║\n")
        f.write("╚" + "═" * 58 + "╝\n\n")
        
        # Bilgiler
        f.write(f"📋 SORGU DETAYLARI\n")
        f.write("─" * 60 + "\n")
        f.write(f"🔹 TC Kimlik     : {tc}\n")
        f.write(f"🔹 Sorgulama Tarihi : {datetime.now().strftime('%d.%m.%Y - %H:%M:%S')}\n")
        f.write(f"🔹 Toplam Kişi    : {person_count}\n")
        f.write("─" * 60 + "\n\n")

        # Kişi bilgileri
        f.write("📊 AİLE AĞACI VERİLERİ\n")
        f.write("═" * 60 + "\n\n")

        for index, row in enumerate(rows[1:], 1):
            cols = row.find_all('td')
            if len(cols) < 12:
                continue

            yakinlik   = cols[0].get_text(strip=True)
            tckn       = cols[1].get_text(strip=True)
            adi        = cols[2].get_text(strip=True)
            soyadi     = cols[3].get_text(strip=True)
            dogumtarih = cols[4].get_text(strip=True)
            anneadi    = cols[5].get_text(strip=True)
            annetc     = cols[6].get_text(strip=True)
            babaadi    = cols[7].get_text(strip=True)
            babatc     = cols[8].get_text(strip=True)
            il         = cols[9].get_text(strip=True)
            ilce       = cols[10].get_text(strip=True)
            uyruk      = cols[11].get_text(strip=True)

            # Modern tasarım
            f.write(f"┌─ [{index:03d}] 👥 {yakinlik.upper()}\n")
            f.write(f"├─ 🆔 TC Kimlik      : {tckn}\n")
            f.write(f"├─ 👤 Ad-Soyad      : {adi.upper()} {soyadi.upper()}\n")
            f.write(f"├─ 📅 Doğum Tarihi   : {dogumtarih}\n")
            f.write(f"├─ 👩 Anne Adı       : {anneadi.upper() if anneadi else '-'}\n")
            f.write(f"├─ 🆔 Anne TC        : {annetc if annetc else '-'}\n")
            f.write(f"├─ 👨 Baba Adı       : {babaadi.upper() if babaadi else '-'}\n")
            f.write(f"├─ 🆔 Baba TC        : {babatc if babatc else '-'}\n")
            f.write(f"├─ 📍 Nüfus Yeri     : {il}/{ilce}\n")
            f.write(f"└─ 🌍 Uyruk          : {uyruk}\n\n")

        # Footer
        f.write("═" * 60 + "\n")
        f.write("📊 İSTATİSTİKLER\n")
        f.write("─" * 60 + "\n")
        f.write(f"✅ Sorgu Başarılı\n")
        f.write(f"👥 Toplam Aile Üyesi: {person_count}\n")
        f.write(f"⏰ İşlem Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n")
        f.write("🔐 API-BY-LUNA | Luna Vip Sorgu\n")
        f.write("═" * 60 + "\n")

    # Mesajı güncelle ve dosyayı gönder
    await progress_msg.delete()

    caption = (
        "✅ SOY AĞACI BAŞARIYLLA ÇEKİLDİ\n"
        "═════════════════════════════════════\n\n"
        f"🆔 TC: `{tc}`\n"
        f"👥 Aile Üyesi: `{person_count} kişi`\n"
        f"📅 Tarih: `{datetime.now().strftime('%d.%m.%Y')}`\n\n"
        "📄 Detaylı rapor aşağıda gönderilmiştir."
    )

    try:
        # Dosyayı gönder
        with open(dosya_tam_yol, 'rb') as dosya:
            await update.message.reply_document(
                document=dosya,
                filename=dosya_adi,
                caption=caption,
                parse_mode='Markdown'
            )
        
        # Satır sayısını kontrol et
        with open(dosya_tam_yol, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            line_count = len(lines)
        
        # 90 satırdan az ise metin olarak da gönder
        if line_count <= 90:
            with open(dosya_tam_yol, 'r', encoding='utf-8') as f:
                content = f.read()
                # 4096 karakterden büyükse parçalara böl
                if len(content) > 4090:
                    for i in range(0, len(content), 4090):
                        chunk = content[i:i+4090]
                        await update.message.reply_text(f"```\n{chunk}\n```", parse_mode='Markdown')
                else:
                    await update.message.reply_text(f"```\n{content}\n```", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"🚫 Dosya gönderilirken hata oluştu: {str(e)[:150]}")


# Adres Sorgu
@ensure_channel_and_key
async def adres_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """🏠 Adres - Detaylı Adres Sorgulaması"""
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    if len(context.args) != 1:
        await update.message.reply_text(
            "🏠 ADRES SORGULAMASI\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔍 Lütfen geçerli bir TC kimlik numarası belirtin.\n\n"
            "📝 Örnek: `/adres 11111111110`",
            parse_mode="Markdown"
        )
        return
    
    tc = context.args[0]
    
    # Bekleme mesajı
    status_msg = await update.message.reply_text("⏳ Adres sorgulanıyor...")
    
    url = f'http://localhost/82m/82m-api-adres.php?kimlikNo={tc}'
    
    try:
        response = requests.get(url, timeout=180)
        response.raise_for_status()
        # UTF-8 BOM'u kaldır
        response.encoding = 'utf-8-sig'
        data = response.json()
    except requests.Timeout:
        await status_msg.edit_text("🚫 Zaman aşımı! Sorgu 3 dakikadan uzun sürdü.")
        return
    except requests.RequestException as e:
        await status_msg.edit_text(f"🚫 API isteği başarısız oldu: {e}")
        return
    except json.JSONDecodeError as e:
        logger.error(f"JSON Decode Error: {response.text}")
        try:
            # BOM sorununu çözmek için manual olarak decode et
            data = json.loads(response.content.decode('utf-8-sig'))
        except Exception:
            await status_msg.edit_text("🚫 API yanıtı geçerli bir JSON değil.")
            return
    
    # Debug: yanıtı logla
    logger.info(f"Adres API Response: {data}")
    
    if isinstance(data, dict) and data.get('error'):
        await status_msg.edit_text(f"🚫 Hata: {data.get('error')}")
        return
    
    try:
        # Veri yapısı farklı olabilir - dict veya list
        if isinstance(data, list) and len(data) > 0:
            user_data = data[0]
        elif isinstance(data, dict):
            user_data = data
        else:
            await status_msg.edit_text("🚫 Sonuç bulunamadı.")
            return
        
        # API tarafından döndürülen alanları al
        tc = user_data.get('KimlikNo', user_data.get('TC', user_data.get('tc', '-')))
        ad_soyad = user_data.get('AdSoyad', '-')
        dogum_yeri = user_data.get('DogumYeri', '-')
        vergi_no = user_data.get('VergiNumarasi', '-')
        ikametgah = user_data.get('Ikametgah', user_data.get('ikametgah', '-'))
        
        line = "═" * 60
        mesaj = (
            f"{line}\n"
            f"🏠 PREMIUM ADRES SORGU SONUCU\n"
            f"{line}\n\n"
            f"👤 KİŞİSEL BİLGİLER\n"
            f"┣ 🆔 TC: {tc}\n"
            f"┣ 📛 Ad Soyad: {ad_soyad}\n"
            f"┗ 📍 Doğum Yeri: {dogum_yeri}\n\n"
            f"📋 ADRES VE VERGİ BİLGİLERİ\n"
            f"┣ 🏠 İkametgah: {ikametgah}\n"
            f"┗ 💼 Vergi No: {vergi_no}\n\n"
            f"{line}\n"
            f"📅 Sorgulama: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            f"🔐 API-BY-LUNA\n"
        )
        
        # Dosyaya kaydet
        dosya_yolu = LOG_DIR / 'adres_results'
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        dosya_yolu.mkdir(parents=True, exist_ok=True)
        dosya_adi = f"Adres_{tc}_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt"
        dosya_tam_yol = dosya_yolu / dosya_adi
        
        with open(dosya_tam_yol, 'w', encoding='utf-8') as f:
            f.write(mesaj)
        
        try:
            # Dosyayı gönder
            with open(dosya_tam_yol, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=dosya_adi,
                    caption="✅ Adres Sorgusu Tamamlandı",
                    parse_mode='Markdown'
                )
            
            # Metin olarak da gönder (kısa olduğu için)
            await status_msg.edit_text(f"```\n{mesaj}\n```", parse_mode="Markdown")
        except Exception as e:
            await status_msg.edit_text(f"🚫 Hata: {str(e)[:150]}")
    except (KeyError, IndexError, TypeError) as e:
        logger.error(f"Adres sorgu hatası: {e}, Data: {data}")
        await status_msg.edit_text(f"🚫 Hata: Veri işlenemiyor. {str(e)}")

# TC - TAPU - SORGU 
@ensure_channel_and_key
async def tapu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """📋 Tapu - Tapu Kaydı Sorgulaması"""
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    if len(context.args) != 1:
        await update.message.reply_text(
            "📋 TAPU SORGULAMASI\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔍 Lütfen geçerli bir TC kimlik numarası belirtin.\n\n"
            "📝 Örnek: `/tapu 11111111110`",
            parse_mode="Markdown"
        )
        return
    
    tc = context.args[0]
    
    # Bekleme mesajı
    status_msg = await update.message.reply_text("⏳ Tapu kaydı sorgulanıyor...")
    
    url = f'http://localhost/tapu/taputc.php?tc={tc}'
    
    try:
        response = requests.get(url, timeout=180)
        response.raise_for_status()
        response_text = response.text

        # Sonuç mesajı
        header = (
            "📋 PREMIUM TAPU SORGU SONUCU\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🆔 Sorgulanan TC: `{tc}`\n"
            f"📅 Sorgulama Zamanı: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📄 SORGU SONUCU:\n\n"
        )
        
        # Uzun mesajları böl
        MAX_LENGTH = 3500
        total_length = len(response_text)
        chunks = []
        
        for i in range(0, total_length, MAX_LENGTH):
            chunk = response_text[i:i+MAX_LENGTH]
            chunks.append(chunk)
        
        # İlk chunk'a header ekle
        if chunks:
            full_message = header + chunks[0]
            if len(full_message) > 4096:
                # Çok uzunsa dosya olarak gönder
                dosya_adi = f"tapu_{tc}_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt"
                dosya_yolu = LOG_DIR / dosya_adi
                LOG_DIR.mkdir(parents=True, exist_ok=True)
                
                with open(dosya_yolu, "w", encoding="utf-8") as f:
                    f.write(f"TAPU SORGU SONUCU - {tc}\n")
                    f.write(f"Sorgulama: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
                    f.write("="*60 + "\n\n")
                    f.write(response_text)
                
                await status_msg.delete()
                with open(dosya_yolu, 'rb') as dosya:
                    await update.message.reply_document(
                        document=dosya,
                        filename=dosya_adi,
                        caption=header.replace("**", "").replace("`", ""),
                        parse_mode="Markdown"
                    )
            else:
                await status_msg.edit_text(full_message, parse_mode="Markdown")
                
                # Kalan chunks'ları gönder
                for chunk in chunks[1:]:
                    if chunk.strip():
                        await update.message.reply_text(f"```\n{chunk}\n```", parse_mode="Markdown")

    except requests.Timeout:
        await status_msg.edit_text("🚫 Zaman aşımı! Sorgu 3 dakikadan uzun sürdü.")
    except requests.RequestException as e:
        await status_msg.edit_text(f"🚫 API isteği başarısız oldu: {e}")
    except Exception as e:
        await status_msg.edit_text(f"🚫 Hata oluştu: {str(e)}")



# İşyeri Tc Yönetici Sorgu
@ensure_channel_and_key
async def isyeriyt_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """🏢 İşyeri YT - İşyeri Yöneticisi Sorgulaması"""
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    if len(context.args) != 1:
        await update.message.reply_text(
            "🏢 İŞYERİ YÖNETİCİ SORGULAMASI\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔍 Lütfen geçerli bir TC kimlik numarası belirtin.\n\n"
            "📝 Örnek: `/isyeriyt 11111111110`",
            parse_mode="Markdown"
        )
        return
    
    tc = context.args[0]
    
    # Bekleme mesajı
    status_msg = await update.message.reply_text("⏳ İşyeri bilgileri sorgulanıyor...")
    
    url = f'http://localhost/isyeri/işyeriyt.php?tc={tc}'
    
    try:
        response = requests.get(url, timeout=180)
        response.raise_for_status()
        response_text = response.text

        # Sonuç mesajı
        header = (
            "🏢 PREMIUM İŞYERİ YÖNETİCİ SORGU SONUCU\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🆔 Sorgulanan TC: `{tc}`\n"
            f"📅 Sorgulama Zamanı: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📄 SORGU SONUCU:\n\n"
        )
        
        full_message = header + response_text
        
        # Mesaj uzunluğu kontrolü
        if len(full_message) > 4096:
            # Dosya olarak gönder
            dosya_adi = f"isyeriyt_{tc}_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt"
            dosya_yolu = LOG_DIR / dosya_adi
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            
            with open(dosya_yolu, "w", encoding="utf-8") as f:
                f.write(f"İŞYERİ YÖNETİCİ SORGU SONUCU - {tc}\n")
                f.write(f"Sorgulama: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
                f.write("="*60 + "\n\n")
                f.write(response_text)
            
            await status_msg.delete()
            with open(dosya_yolu, 'rb') as dosya:
                await update.message.reply_document(
                    document=dosya,
                    filename=dosya_adi,
                    caption=header.replace("**", "").replace("`", ""),
                    parse_mode="Markdown"
                )
        else:
            await status_msg.edit_text(full_message, parse_mode="Markdown")

    except requests.Timeout:
        await status_msg.edit_text("🚫 Zaman aşımı! Sorgu 3 dakikadan uzun sürdü.")
    except requests.RequestException as e:
        await status_msg.edit_text(f"🚫 API isteği başarısız oldu: {e}")
    except Exception as e:
        await status_msg.edit_text(f"🚫 Hata oluştu: {str(e)}")



# Polis Modu
@ensure_channel_and_key
async def polis_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    if len(context.args) != 1:
        await update.message.reply_text("🔍 Lütfen geçerli bir TC kimlik numarası belirtin.\n\nÖrnek: /polis 46024967042", parse_mode="Markdown")
        return
    
    tc = context.args[0]
    
    url = f'http://localhost/109m/tcproadres.php?tc={tc}'
    
    try:
        response = requests.get(url, timeout=180)
        response.raise_for_status()  # Raise an error for bad status codes
        data = json.loads(response.content.decode('utf-8-sig'))  # Use utf-8-sig to handle BOM
    except requests.Timeout:
        await update.message.reply_text("🚫 Zaman aşımı! Sorgu 3 dakikadan uzun sürdü.", parse_mode="Markdown")
        return
    except requests.RequestException as e:
        await update.message.reply_text(f"🚫 API isteği başarısız oldu: {e}", parse_mode="Markdown")
        return
    except json.JSONDecodeError:
        await update.message.reply_text("🚫 API yanıtı geçerli bir JSON değil.", parse_mode="Markdown")
        return

    # Check if the required keys are in the response
    required_keys = ['TC', 'AD', 'SOYAD', 'GSM', 'ANNEADI', 'ANNETC', 'BABAADI', 'BABATC', 'MEMLEKETIL', 'MEMLEKETILCE', 'MEMLEKETKOY', 'ADRESIL', 'ADRESILCE', 'AILESIRANO', 'BIREYSIRANO', 'MEDENIHAL', 'CINSIYET', 'VergiNumarasi', 'Ikametgah']
    if not all(key in data for key in required_keys):
        await update.message.reply_text("🚫 Sorgu bulunamadı.", parse_mode="Markdown")
        return

    # Directly use the data to format the message
    user = data
    line = "═" * 60
    result = (
        f"{line}\n"
        f"🌟 PREMIUM POLİS MODU SORGU SONUCU 🌟\n"
        f"{line}\n\n"
        f"🔹 TC: {user['TC']}\n"
        f"🔹 ADI: {user['AD']}\n"
        f"🔹 SOYADI: {user['SOYAD']}\n"
        f"🔹 GSM: {user['GSM']}\n"
        f"🔹 ANNEADI: {user['ANNEADI']}\n"
        f"🔹 ANNETC: {user['ANNETC']}\n"
        f"🔹 BABAADI: {user['BABAADI']}\n"
        f"🔹 BABATC: {user['BABATC']}\n"
        f"🔹 MEMLEKETIL: {user['MEMLEKETIL']}\n"
        f"🔹 MEMLEKETILCE: {user['MEMLEKETILCE']}\n"
        f"🔹 MEMLEKETKOY: {user['MEMLEKETKOY']}\n"
        f"🔹 ADRESIL: {user['ADRESIL']}\n"
        f"🔹 ADRESILCE: {user['ADRESILCE']}\n"
        f"🔹 AILESIRANO: {user['AILESIRANO']}\n"
        f"🔹 BIREYSIRANO: {user['BIREYSIRANO']}\n"
        f"🔹 MEDENIHAL: {user['MEDENIHAL']}\n"
        f"🔹 CINSIYET: {user['CINSIYET']}\n"
        f"🔹 Vergi Numarası: {user['VergiNumarasi']}\n"
        f"🔹 İkametgah: {user['Ikametgah']}\n"
        f"{line}\n"
        f"🔐 API-BY-LUNA\n"
    )
    
    # Dosyaya kaydet
    dosya_yolu = LOG_DIR / 'polis_results'
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    dosya_yolu.mkdir(parents=True, exist_ok=True)
    dosya_adi = f"Polis_{tc}_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt"
    dosya_tam_yol = dosya_yolu / dosya_adi
    
    with open(dosya_tam_yol, 'w', encoding='utf-8') as f:
        f.write(result)
    
    try:
        # Dosyayı gönder
        with open(dosya_tam_yol, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=dosya_adi,
                caption="✅ Polis Sorgusu Tamamlandı",
                parse_mode='Markdown'
            )
        
        # Metin olarak da gönder
        if len(result) <= 4090:
            await update.message.reply_text(f"```\n{result}\n```", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"🚫 Hata: {str(e)[:150]}")
    
    
 # 2024 tc gsm gsm tc
@ensure_channel_and_key
async def tcgsmgsmtc_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    if len(context.args) != 1:
        await update.message.reply_text("🔍 Lütfen geçerli bir TC kimlik numarası belirtin.\n\nÖrnek: /tcgsmgsmtc 11111111110", parse_mode="Markdown")
        return
    
    tc = context.args[0]
    
    if not (tc.isdigit() and len(tc) == 11):
        await update.message.reply_text("❌ Geçersiz TC! 11 haneli rakam giriniz.")
        return
    
    progress_msg = await update.message.reply_text("🔄 TC-GSM-GSM-TC zinciri sorgulanıyor...")
    
    url = f'http://localhost/116m/gsmtctcgsm.php?query={tc}'
    
    try:
        response = requests.get(url, timeout=180)
        response.raise_for_status()
        response_text = response.text

        # Dosyaya kaydet
        dosya_yolu = LOG_DIR / 'tcgsmgsmtc_results'
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        dosya_yolu.mkdir(parents=True, exist_ok=True)
        dosya_adi = f"TCGSMGSMTC_{tc}_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt"
        dosya_tam_yol = dosya_yolu / dosya_adi
        
        with open(dosya_tam_yol, 'w', encoding='utf-8') as f:
            f.write(f"═" * 60 + "\n")
            f.write("TC-GSM-GSM-TC ZİNCİR SORGU SONUCU\n")
            f.write(f"═" * 60 + "\n\n")
            f.write(response_text)
            f.write(f"\n\n{'═' * 60}\n")
            f.write(f"🔐 API-BY-LUNA | Sorgu Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
        
        # Dosyayı gönder
        with open(dosya_tam_yol, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=dosya_adi,
                caption=f"✅ TC-GSM Zincir Sorgusu Tamamlandı\n🆔 TC: `{tc}`",
                parse_mode='Markdown'
            )
        
        # Metin olarak da gönder
        with open(dosya_tam_yol, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if len(content) <= 4090:
            await update.message.reply_text(f"```\n{content}\n```", parse_mode='Markdown')
        
        await progress_msg.delete()

    except requests.Timeout:
        await progress_msg.edit_text("🚫 Zaman aşımı! Sorgu 3 dakikadan uzun sürdü.")
    except requests.ConnectionError:
        await progress_msg.edit_text("🚫 Bağlantı hatası! Sunucuya erişilemiyor.")
    except Exception as e:
        await progress_msg.edit_text(f"🚫 Hata oluştu: {str(e)[:150]}")


 # 2024 tc gsm gsm tc v2
@ensure_channel_and_key
async def tcgsmgsmtcv2_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    if len(context.args) != 1:
        await update.message.reply_text("🔍 Lütfen geçerli bir TC kimlik numarası belirtin.\n\nÖrnek: /tcgsmgsmtcv2 11111111110", parse_mode="Markdown")
        return
    
    tc = context.args[0]
    
    if not (tc.isdigit() and len(tc) == 11):
        await update.message.reply_text("❌ Geçersiz TC! 11 haneli rakam giriniz.")
        return
    
    progress_msg = await update.message.reply_text("🔄 TC-GSM-GSM-TC V2 zinciri sorgulanıyor...")
    
    url = f'http://localhost/116m/gsmtctcgsm_v2.php?query={tc}'
    
    try:
        response = requests.get(url, timeout=180)
        response.raise_for_status()
        response_text = response.text

        # Dosyaya kaydet
        dosya_yolu = LOG_DIR / 'tcgsmgsmtcv2_results'
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        dosya_yolu.mkdir(parents=True, exist_ok=True)
        dosya_adi = f"TCGSMGSMTCV2_{tc}_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt"
        dosya_tam_yol = dosya_yolu / dosya_adi
        
        with open(dosya_tam_yol, 'w', encoding='utf-8') as f:
            f.write(f"═" * 60 + "\n")
            f.write("TC-GSM-GSM-TC V2 ZİNCİR SORGU SONUCU\n")
            f.write(f"═" * 60 + "\n\n")
            f.write(response_text)
            f.write(f"\n\n{'═' * 60}\n")
            f.write(f"🔐 API-BY-LUNA | Sorgu Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
        
        # Dosyayı gönder
        with open(dosya_tam_yol, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=dosya_adi,
                caption=f"✅ TC-GSM V2 Zincir Sorgusu Tamamlandı\n🆔 TC: `{tc}`",
                parse_mode='Markdown'
            )
        
        # Metin olarak da gönder
        with open(dosya_tam_yol, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if len(content) <= 4090:
            await update.message.reply_text(f"```\n{content}\n```", parse_mode='Markdown')
        
        await progress_msg.delete()

    except requests.Timeout:
        await progress_msg.edit_text("🚫 Zaman aşımı! Sorgu 3 dakikadan uzun sürdü.")
    except requests.ConnectionError:
        await progress_msg.edit_text("🚫 Bağlantı hatası! Sunucuya erişilemiyor.")
    except Exception as e:
        await progress_msg.edit_text(f"🚫 Hata oluştu: {str(e)[:150]}")


# okul no sorgu
@ensure_channel_and_key
async def okulno_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """🎓 Okul No - Okul Numarası Sorgulaması"""
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    if len(context.args) != 1:
        await update.message.reply_text(
            "🎓 OKUL NUMARASI SORGULAMASI\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔍 Lütfen geçerli bir TC kimlik numarası belirtin.\n\n"
            "📝 Örnek: `/okulno 11111111110`",
            parse_mode="Markdown"
        )
        return
    
    tc = context.args[0]
    
    # Bekleme mesajı
    status_msg = await update.message.reply_text("⏳ Okul numarası sorgulanıyor...")
    
    url = f'http://localhost/25m/okulno.php?tc={tc}'
    
    try:
        response = requests.get(url, timeout=180)
        response.raise_for_status()
        response_json = response.json()
        
        # Sonuç mesajı
        header = (
            "🎓 PREMIUM OKUL NUMARASI SORGU SONUCU\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🆔 Sorgulanan TC: `{tc}`\n"
            f"📅 Sorgulama Zamanı: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📄 SORGU SONUCU:\n\n"
        )
        
        # JSON'u düzgün formatla
        response_str = json.dumps(response_json, indent=2, ensure_ascii=False)
        full_message = header + f"```json\n{response_str}\n```"
        
        # Mesaj uzunluğu kontrolü
        if len(full_message) > 4096:
            # Dosya olarak gönder
            dosya_adi = f"okulno_{tc}_{datetime.now().strftime('%d%m%Y_%H%M%S')}.json"
            dosya_yolu = LOG_DIR / dosya_adi
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            
            with open(dosya_yolu, "w", encoding="utf-8") as f:
                f.write(f"OKUL NUMARASI SORGU SONUCU - {tc}\n")
                f.write(f"Sorgulama: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
                f.write("="*60 + "\n\n")
                f.write(response_str)
            
            await status_msg.delete()
            with open(dosya_yolu, 'rb') as dosya:
                await update.message.reply_document(
                    document=dosya,
                    filename=dosya_adi,
                    caption=header.replace("**", "").replace("`", ""),
                    parse_mode="Markdown"
                )
        else:
            await status_msg.edit_text(full_message, parse_mode="Markdown")

    except requests.Timeout:
        await status_msg.edit_text("🚫 Zaman aşımı! Sorgu 3 dakikadan uzun sürdü.")
    except requests.RequestException as e:
        await status_msg.edit_text(f"🚫 API isteği başarısız oldu: {e}")
    except Exception as e:
        await status_msg.edit_text(f"🚫 Hata oluştu: {str(e)}") 
        
# Sgk Sorgu - Çalışan Bilgisi ile
@ensure_channel_and_key
async def sgk_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """💼 SGK - SGK Çalışan ve Kayıt Bilgileri Sorgulaması"""
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    if len(context.args) != 1:
        await update.message.reply_text(
            "💼 SGK SORGULAMASI\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔍 Lütfen geçerli bir TC kimlik numarası belirtin.\n\n"
            "📝 Örnek: `/sgk 11111111110`",
            parse_mode="Markdown"
        )
        return
    
    tc = context.args[0]
    
    # Bekleme mesajı
    status_msg = await update.message.reply_text("⏳ SGK bilgileri sorgulanıyor...")
    
    sgk_url = f'http://localhost/sgk/sgk.php?tc={tc}'
    tcpro_url = f'http://localhost/109m/tcpro.php?tc={tc}'
    
    try:
        # Her iki API'yi çağır
        sgk_response = requests.get(sgk_url, timeout=180)
        tcpro_response = requests.get(tcpro_url, timeout=180)
        
        sgk_response.raise_for_status()
        tcpro_response.raise_for_status()
        
        sgk_text = sgk_response.text
        tcpro_data = json.loads(tcpro_response.content.decode('utf-8-sig'))
        
        # Sonuç mesajı
        result = (
            "💼 PREMIUM SGK SORGU SONUCU\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            "👤 KİŞİSEL BİLGİLER\n"
            f"┣ 🆔 TC: `{tcpro_data.get('TC', '-')}`\n"
            f"┣ 📛 Ad: {tcpro_data.get('Adı', '-')}\n"
            f"┣ 📛 Soyadı: {tcpro_data.get('Soyadı', '-')}\n"
            f"┣ 📅 Doğum Tarihi: {tcpro_data.get('Doğum Tarihi', '-')}\n"
            f"┗ 👥 Cinsiyet: {tcpro_data.get('Cinsiyet', '-')}\n\n"
            
            "👨‍👩‍👧 AİLE BİLGİLERİ\n"
            f"┣ 👩 Anne: {tcpro_data.get('Anne Adı', '-')}\n"
            f"┣ 👩 Anne TC: {tcpro_data.get('Anne TC', '-')}\n"
            f"┣ 👨 Baba: {tcpro_data.get('Baba Adı', '-')}\n"
            f"┗ 👨 Baba TC: {tcpro_data.get('Baba TC', '-')}\n\n"
            
            "📍 NÜFUS BİLGİLERİ\n"
            f"┣ 📍 İl: {tcpro_data.get('Nüfus İl', '-')}\n"
            f"┣ 🏢 İlçe: {tcpro_data.get('Nüfus İlçe', '-')}\n"
            f"┗ 🌍 Uyruk: {tcpro_data.get('Uyruk', '-')}\n\n"
            
            "💼 SGK KAYIT BİLGİLERİ\n"
            f"┗ 📊 SGK Verisi:\n```\n{sgk_text}\n```\n\n"
            
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔐 API-BY-LUNA"
        )
        
        # Mesaj uzunluğu kontrolü
        if len(result) > 4096:
            # Dosya olarak gönder
            dosya_adi = f"sgk_{tc}_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt"
            dosya_yolu = LOG_DIR / dosya_adi
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            
            with open(dosya_yolu, "w", encoding="utf-8") as f:
                f.write(result.replace("**", "").replace("`", "").replace("┣", "").replace("┗", "").replace("┃", ""))
            
            await status_msg.delete()
            with open(dosya_yolu, 'rb') as dosya:
                await update.message.reply_document(
                    document=dosya,
                    filename=dosya_adi,
                    caption=f"💼 SGK Sorgusu - TC: {tc}",
                    parse_mode="Markdown"
                )
        else:
            await status_msg.edit_text(result, parse_mode="Markdown")

    except requests.Timeout:
        await status_msg.edit_text("🚫 Zaman aşımı! Sorgu 3 dakikadan uzun sürdü.")
    except requests.RequestException as e:
        await status_msg.edit_text(f"🚫 API isteği başarısız oldu: {e}")
    except json.JSONDecodeError:
        await status_msg.edit_text("🚫 API yanıtı geçerli bir JSON değil.")
    except Exception as e:
        await status_msg.edit_text(f"🚫 Hata oluştu: {str(e)}")


 # Plaka sorgu 
@ensure_channel_and_key
async def plaka_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    if len(context.args) != 1:
        await update.message.reply_text("🔍 Lütfen geçerli bir plaka belirtin.\n\nÖrnek: /plaka 34bu6666", parse_mode="Markdown")
        return
    
    tc = context.args[0]
    url = f'http://localhost/plaka/plakaceza.php?plaka={tc}'
    
    try:
        response = requests.get(url, timeout=180)
        response_text = response.text  # API'den gelen ham yanıt

        await update.message.reply_text(f"```markdown\n🌟 Premium API Yanıtı:\n{response_text}\n```", parse_mode="Markdown")
        

    except requests.Timeout:
        await update.message.reply_text("🚫 Zaman aşımı! Sorgu 3 dakikadan uzun sürdü.", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"🚫 Hata oluştu:\n```{str(e)}```", parse_mode="Markdown")


 # İban Çözümle 
@ensure_channel_and_key
async def iban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    if len(context.args) != 1:
        await update.message.reply_text("🔍 Lütfen geçerli bir IBAN belirtin.\n\nÖrnek: /iban TR310006400000163180184752", parse_mode="Markdown")
        return
    
    ib = context.args[0]
    url = f'http://localhost/iban/iban.php?iban={ib}'
    
    try:
        response = requests.get(url, timeout=180)
        response_text = response.text  # API'den gelen ham yanıt

        await update.message.reply_text(f"```markdown\n🌟 Premium API Yanıtı:\n{response_text}\n```", parse_mode="Markdown")
        

    except requests.Timeout:
        await update.message.reply_text("🚫 Zaman aşımı! Sorgu 3 dakikadan uzun sürdü.", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"🚫 Hata oluştu:\n```{str(e)}```", parse_mode="Markdown")



 # Gsm Coz
@ensure_channel_and_key
async def gsmcoz_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    if len(context.args) != 1:
        await update.message.reply_text("🔍 Lütfen geçerli bir GSM numarası belirtin.\n\nÖrnek: /gsmcoz 5368554486", parse_mode="Markdown")
        return
    
    gsm = context.args[0]
    url = f'http://localhost/116m/operator.php?gsm={gsm}'
        
    try:
        response = requests.get(url, timeout=180)
        data = response.json()
        
        operator = data.get('operator', 'Bilinmiyor')
        gsm_num = data.get('gsm', gsm)
        
        message = (
            "📱 GSM ÇÖZÜMLEME SONUCU\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📞 GSM Numarası: `{gsm_num}`\n"
            f"🏢 İşletmeci: {operator}\n"
            f"📅 Sorgulama: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )
        
        await update.message.reply_text(message, parse_mode="Markdown")

    except requests.Timeout:
        await update.message.reply_text("🚫 Zaman aşımı! Sorgu 3 dakikadan uzun sürdü.", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"🚫 Hata oluştu:\n`{str(e)}`", parse_mode="Markdown")


# multeci sorgu
@ensure_channel_and_key
async def multeci_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """🌍 Mülteci Sorgulaması"""
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    if len(context.args) != 1:
        await update.message.reply_text(
            "🌍 MÜLTECI SORGULAMASI\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔍 Lütfen geçerli bir TC kimlik numarası belirtin.\n\n"
            "📝 Örnek: `/multeci 99000100650`",
            parse_mode="Markdown"
        )
        return
    
    tc = context.args[0]
    url = f'http://localhost/6m/multeci.php?tc={tc}'
    
    status_msg = await update.message.reply_text("⏳ Mülteci bilgileri sorgulanıyor...")
        
    try:
        response = requests.get(url, timeout=180)
        response.raise_for_status()
        
        # Raw JSON response
        data = response.json()
        response_text = json.dumps(data, ensure_ascii=False, indent=2)
        
        message = (
            "🌍 PREMIUM MÜLTECI SORGU SONUCU\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🆔 Sorgulanan TC: `{tc}`\n"
            f"📅 Sorgulama Zamanı: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📄 SORGU SONUCU:\n\n"
            f"```json\n{response_text}\n```"
        )
        
        # Mesaj uzunluğu kontrolü
        if len(message) > 4096:
            # Dosya olarak gönder
            dosya_adi = f"multeci_{tc}_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt"
            dosya_yolu = LOG_DIR / dosya_adi
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            
            with open(dosya_yolu, "w", encoding="utf-8") as f:
                f.write(f"MÜLTECI SORGU SONUCU - {tc}\n")
                f.write(f"Sorgulama: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
                f.write("="*60 + "\n\n")
                f.write(response_text)
            
            await status_msg.delete()
            with open(dosya_yolu, 'rb') as dosya:
                await update.message.reply_document(
                    document=dosya,
                    filename=dosya_adi,
                    caption=f"🌍 MÜLTECI SORGUSU TAMAMLANDI\n🆔 TC: `{tc}`\n📅 Saat: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
                    parse_mode="Markdown"
                )
        else:
            await status_msg.edit_text(message, parse_mode="Markdown")

    except requests.Timeout:
        await status_msg.edit_text("🚫 Zaman aşımı! Sorgu 3 dakikadan uzun sürdü.", parse_mode="Markdown")
    except requests.RequestException as e:
        await status_msg.edit_text(f"🚫 API isteği başarısız oldu: {e}", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"multeci_command error: {str(e)}")
        await status_msg.edit_text(f"🚫 Hata oluştu: {str(e)}", parse_mode="Markdown")

# gsm adres 2025
@ensure_channel_and_key
async def gsmadres_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    if len(context.args) != 1:
        await update.message.reply_text("🔍 Lütfen geçerli bir GSM numarası belirtin.\n\nÖrnek: /gsmadres 5466324433", parse_mode="Markdown")
        return
    
    gsm = context.args[0]
    url = f'http://localhost/ttnet/ttnet.php?gsm={gsm}'
        
    try:
        response = requests.get(url, timeout=180)
        response_text = response.text  # API'den gelen ham yanıt

        await update.message.reply_text(f"```markdown\n🌟 Premium API Yanıtı:\n{response_text}\n```", parse_mode="Markdown")
        

    except requests.Timeout:
        await update.message.reply_text("🚫 Zaman aşımı! Sorgu 3 dakikadan uzun sürdü.", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"🚫 Hata oluştu:\n```{str(e)}```", parse_mode="Markdown")


# Parsel sorgu
@ensure_channel_and_key
async def parsel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parsel sorgulaması - Ada-Parsel formatında"""
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    if len(context.args) != 1:
        await update.message.reply_text(
            "🔍 PARSEL SORGULAMASI\n\n"
            "Kullanım: `/parsel ADA-PARSEL`\n\n"
            "📌 Örnek: `/parsel 20905-2`",
            parse_mode="Markdown"
        )
        return
    
    param = context.args[0]
    parts = param.split('-', 1)
    
    if len(parts) != 2:
        await update.message.reply_text("❌ Format: `/parsel ADA-PARSEL`\nÖrnek: `/parsel 20905-2`")
        return
    
    ada = parts[0].strip()
    parsel = parts[1].strip()
    
    # Validation
    if not ada or not parsel:
        await update.message.reply_text("❌ Ada ve parsel boş olamaz!")
        return
    
    url = f'http://localhost/tapu/adaparsel-il-ilce.php?ada={ada}&parsel={parsel}'
    
    status = await update.message.reply_text("🔍 Sorgulanıyor...")
    
    try:
        logger.info(f"Parsel sorgusu: Ada={ada}, Parsel={parsel}")
        
        # API çağrısı
        resp = requests.get(url, timeout=180, allow_redirects=True)
        
        logger.info(f"Response status: {resp.status_code}")
        
        if resp.status_code == 404:
            await status.edit_text("❌ Kayıt bulunamadı")
            return
        
        if resp.status_code != 200:
            error_msg = resp.text[:200] if resp.text else f"HTTP {resp.status_code}"
            await status.edit_text(f"❌ Hata: {error_msg}")
            logger.error(f"HTTP {resp.status_code}: {resp.text}")
            return
        
        # JSON parse
        try:
            json_data = resp.json()
        except Exception as e:
            await status.edit_text(f"❌ JSON Hatası: {str(e)[:50]}")
            logger.error(f"JSON Error: {e}, Response: {resp.text[:200]}")
            return
        
        # API yanıtını kontrol et
        if isinstance(json_data, dict):
            if json_data.get("status") == "error":
                error_msg = json_data.get("error", "Bilinmeyen hata")
                await status.edit_text(f"❌ {error_msg}")
                logger.warning(f"API Error: {error_msg}")
                return
            
            data = json_data.get("data", [])
            if not data:
                await status.edit_text("❌ Sonuç bulunamadı")
                return
        else:
            data = json_data if isinstance(json_data, list) else []
            if not data:
                await status.edit_text("❌ Sonuç bulunamadı")
                return
        
        # TXT dosyası oluştur
        output_file = LOG_DIR / 'parsel_sorgu_simple.txt'
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("🌟 PREMIUM PARSEL SORGU SONUCU 🌟\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"📊 Toplam {len(data)} sonuç bulundu\n")
            f.write(f"Sorgu Zamanı: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n")
            f.write("=" * 70 + "\n\n")
            
            for idx, row in enumerate(data, 1):
                f.write(f"📍 KAYIT #{idx}\n")
                f.write("─" * 70 + "\n")
                f.write(f"🏛️  İL        : {row.get('il', '-')}\n")
                f.write(f"🏘️  İLÇE      : {row.get('ilce', '-')}\n")
                f.write(f"🏘️  MAH/KÖY   : {row.get('Mahalle/Köy', '-')}\n")
                f.write(f"🏠 ZEMIN TİPİ : {row.get('Zemin Tipi', '-')}\n")
                f.write(f"📐 ADA       : {row.get('Ada', '-')}\n")
                f.write(f"📐 PARSEL    : {row.get('Parsel', '-')}\n")
                f.write(f"📏 YÜZÖLÇÜM  : {row.get('Yüzölçüm', '-')}\n")
                f.write(f"🏷️  NİTELİK   : {row.get('Nitelik', '-')}\n")
                f.write(f"\n👤 SAHİP BİLGİLERİ:\n")
                f.write(f"   ├─ Adı       : {row.get('Adı', '-')}\n")
                f.write(f"   ├─ Soyadı    : {row.get('Soyadı', '-')}\n")
                f.write(f"   ├─ Baba Adı  : {row.get('Baba Adı', '-')}\n")
                f.write(f"   └─ TC No     : {row.get('TC Kimlik No', '-')}\n")
                f.write(f"\n📋 TAPİL BİLGİSİ:\n")
                f.write(f"   ├─ Edinme S.: {row.get('Edinme Sebebi', '-')}\n")
                f.write(f"   ├─ Tarih     : {row.get('Tarih', '-')}\n")
                f.write(f"   └─ Yevmiye   : {row.get('Yevmiye', '-')}\n")
                f.write("\n" + "=" * 70 + "\n\n")
            
            f.write("\n🔐 API-BY-LUNA | Sorgu Zamanı: " + 
                   datetime.now().strftime('%d.%m.%Y %H:%M:%S') + "\n")
        
        # Dosyayı gönder
        with open(output_file, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=f"parsel_{ada}-{parsel}.txt",
                caption=f"✅ {len(data)} sonuç bulundu!",
                parse_mode="Markdown"
            )
        
        # Özet
        text = f"✅ **{len(data)} Sonuç Bulundu**\n\n"
        for i, row in enumerate(data[:3], 1):
            text += f"{i}. Ada: {row.get('Ada')}, Parsel: {row.get('Parsel')}\n"
            text += f"   👤 {row.get('Adi', '-')} {row.get('Soyadi', '-')}\n"
        if len(data) > 3:
            text += f"\n... +{len(data)-3} daha (dosyada)"
        
        await status.edit_text(text)

    except requests.Timeout:
        await status.edit_text("⏱️ Zaman aşımı (180+ saniye)")
        logger.warning("Request timeout")
    except Exception as e:
        logger.error(f"Parsel error: {str(e)}")
        await status.edit_text(f"❌ Hata oluştu: {str(e)[:100]}")



# Gsm Pro
@ensure_channel_and_key
async def gsmpro_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    if len(context.args) != 1:
        await update.message.reply_text("🔍 Lütfen geçerli bir GSM numarası belirtin.\n\nÖrnek: /gsmpro 53685944524", parse_mode="Markdown")
        return
    
    gsm = context.args[0]
    url = f'http://localhost/109m/gsmpro.php?gsm={gsm}'
        
    try:
        response = requests.get(url, timeout=180)
        response_text = response.text  # API'den gelen ham yanıt

        await update.message.reply_text(f"```markdown\n🌟 Premium API Yanıtı:\n{response_text}\n```", parse_mode="Markdown")
        

    except requests.Timeout:
        await update.message.reply_text("🚫 Zaman aşımı! Sorgu 3 dakikadan uzun sürdü.", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"🚫 Hata oluştu:\n```{str(e)}```", parse_mode="Markdown")



# Çocuk Sorgu
@ensure_channel_and_key
async def cocuksorgu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """👧 Çocuk - Çocuk Sorgulaması"""
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    if len(context.args) != 1:
        await update.message.reply_text("🔍 Lütfen geçerli bir TC kimlik numarası belirtin.\n\nÖrnek: /cocuksorgu 111111111110", parse_mode="Markdown")
        return
    
    tc = context.args[0]
    
    if not (tc.isdigit() and len(tc) == 11):
        await update.message.reply_text("❌ Geçersiz TC! 11 haneli rakam giriniz.")
        return
    
    # Progress mesajı
    progress_msg = await update.message.reply_text("🔄 Çocuk bilgileri sorgulanıyor...")
    
    url = f'http://localhost/109m/cocuk-sorgu.php?tc={tc}'
        
    try:
        response = requests.get(url, timeout=180)
        response.raise_for_status()
        response_text = response.text
        
        # Dosyaya kaydet
        dosya_yolu = LOG_DIR / 'cocuk_results'
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        dosya_yolu.mkdir(parents=True, exist_ok=True)
        dosya_adi = f"Cocuk_{tc}_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt"
        dosya_tam_yol = dosya_yolu / dosya_adi
        
        with open(dosya_tam_yol, 'w', encoding='utf-8') as f:
            f.write(f"═" * 60 + "\n")
            f.write("👧 ÇOCUK SORGU SONUCU\n")
            f.write(f"═" * 60 + "\n\n")
            f.write(response_text)
            f.write(f"\n\n{'═' * 60}\n")
            f.write(f"🔐 API-BY-LUNA | Sorgu Zamanı: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
        
        # Dosyayı gönder
        with open(dosya_tam_yol, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=dosya_adi,
                caption=f"✅ Çocuk Sorgusu Tamamlandı\n🆔 TC: `{tc}`",
                parse_mode='Markdown'
            )
        
        # Metin olarak da gönder
        with open(dosya_tam_yol, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if len(content) <= 4090:
            await update.message.reply_text(f"```\n{content}\n```", parse_mode='Markdown')
        
        await progress_msg.delete()

    except requests.Timeout:
        await progress_msg.edit_text("🚫 Zaman aşımı! Sorgu 3 dakikadan uzun sürdü.")
    except requests.ConnectionError:
        await progress_msg.edit_text("🚫 Bağlantı hatası! Sunucuya erişilemiyor.")
    except Exception as e:
        await progress_msg.edit_text(f"🚫 Hata oluştu: {str(e)[:150]}")


# Parsel sorgu - ADA-PARSEL-[IL-[ILCE]]
@ensure_channel_and_key
async def parselililce_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parsel sorgulaması"""
    user_id = update.message.from_user.id
    
    if not context.args or len(context.args) != 1:
        await update.message.reply_text(
            "🔍 PARSEL İL-İLÇE SORGULAMASI\n\n"
            "Kullanım: `/parselililce ADA-PARSEL-[IL-[ILCE]]`\n\n"
            "📌 Örnekler:\n"
            "  • `/parselililce 186-1` (Ada-Parsel)\n"
            "  • `/parselililce 186-1-ADANA` (+ İl)\n"
            "  • `/parselililce 186-1-ADANA-ALADAĞ` (+ İlçe)",
            parse_mode="Markdown"
        )
        return
    
    # Parametreleri parse et (ADA-PARSEL-IL-ILCE formatında)
    param = context.args[0]
    parts = param.split('-', 3)
    
    if len(parts) < 2:
        await update.message.reply_text(
            "❌ Minimum ada ve parsel gerekli!\n\n"
            "Format: `/parselililce ADA-PARSEL-[IL-[ILCE]]`\n"
            "Örnek: `/parselililce 20905-2-ANKARA-ALTINDAĞ`"
        )
        return
    
    # Parametreleri ayıkla ve normalize et
    ada = parts[0].strip()
    parsel = parts[1].strip()
    il = parts[2].strip() if len(parts) > 2 else None
    ilce = parts[3].strip() if len(parts) > 3 else None
    
    # Validation
    if not ada or not parsel:
        await update.message.reply_text("❌ Ada ve parsel boş olamaz!")
        return
    
    # URL oluştur
    url = f"http://localhost/tapu/adaparsel-il-ilce.php?ada={ada}&parsel={parsel}"
    if il:
        url += f"&il={il}"
    if ilce:
        url += f"&ilce={ilce}"
    
    status = await update.message.reply_text("🔍 Sorgulanıyor...")
    
    try:
        logger.info(f"Parsel query: {url}")
        
        # 180 saniye timeout (PHP'nin bitmesini bekle)
        resp = requests.get(url, timeout=180, allow_redirects=True)
        
        logger.info(f"Response status: {resp.status_code}")
        
        if resp.status_code == 404:
            await status.edit_text("❌ Kayıt bulunamadı")
            logger.warning(f"404 - Ada: {ada}, Parsel: {parsel}")
            return
        
        if resp.status_code != 200:
            error_msg = resp.text[:200] if resp.text else f"HTTP {resp.status_code}"
            await status.edit_text(f"❌ Hata: {error_msg}")
            logger.error(f"HTTP {resp.status_code}: {resp.text}")
            return
        
        # JSON parse
        try:
            json_data = resp.json()
        except Exception as e:
            await status.edit_text(f"❌ JSON Hatası: {str(e)[:50]}")
            logger.error(f"JSON Error: {e}, Response: {resp.text[:200]}")
            return
        
        # API hatasını kontrol et
        if isinstance(json_data, dict):
            if json_data.get("status") == "error":
                error_msg = json_data.get("error", "Bilinmeyen hata")
                await status.edit_text(f"❌ {error_msg}")
                logger.warning(f"API Error: {error_msg}")
                return
            
            # Başarılı yanıt - data array'i al
            data = json_data.get("data", [])
            if not data:
                await status.edit_text("❌ Sonuç bulunamadı")
                logger.info(f"No results for Ada: {ada}, Parsel: {parsel}")
                return
        else:
            # Direkt array dönüş (eski format uyumluluğu)
            data = json_data if isinstance(json_data, list) else []
            if not data:
                await status.edit_text("❌ Sonuç bulunamadı")
                return
        
        # TXT dosyası oluştur
        output_file = LOG_DIR / 'parsel_sorgu.txt'
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("🌟 PREMIUM PARSEL İL-İLÇE SORGU SONUCU 🌟\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"📊 Toplam {len(data)} sonuç bulundu\n")
            f.write(f"Sorgu Zamanı: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n")
            f.write("=" * 70 + "\n\n")
            
            for idx, row in enumerate(data, 1):
                f.write(f"📍 KAYIT #{idx}\n")
                f.write("─" * 70 + "\n")
                f.write(f"🏛️  İL        : {row.get('il', '-')}\n")
                f.write(f"🏘️  İLÇE      : {row.get('ilce', '-')}\n")
                f.write(f"🏘️  MAH/KÖY   : {row.get('Mahalle/Köy', '-')}\n")
                f.write(f"🏠 ZEMIN TİPİ : {row.get('Zemin Tipi', '-')}\n")
                f.write(f"📐 ADA       : {row.get('Ada', '-')}\n")
                f.write(f"📐 PARSEL    : {row.get('Parsel', '-')}\n")
                f.write(f"📏 YÜZÖLÇÜM  : {row.get('Yüzölçüm', '-')}\n")
                f.write(f"🏷️  NİTELİK   : {row.get('Nitelik', '-')}\n")
                f.write(f"\n👤 SAHİP BİLGİLERİ:\n")
                f.write(f"   ├─ Adı       : {row.get('Adı', '-')}\n")
                f.write(f"   ├─ Soyadı    : {row.get('Soyadı', '-')}\n")
                f.write(f"   ├─ Baba Adı  : {row.get('Baba Adı', '-')}\n")
                f.write(f"   └─ TC No     : {row.get('TC Kimlik No', '-')}\n")
                f.write(f"\n📋 TAPİL BİLGİSİ:\n")
                f.write(f"   ├─ Edinme S.: {row.get('Edinme Sebebi', '-')}\n")
                f.write(f"   ├─ Tarih     : {row.get('Tarih', '-')}\n")
                f.write(f"   └─ Yevmiye   : {row.get('Yevmiye', '-')}\n")
                f.write("\n" + "=" * 70 + "\n\n")
            
            f.write("\n🔐 API-BY-LUNA    | Sorgu Zamanı: " + 
                   datetime.now().strftime('%d.%m.%Y %H:%M:%S') + "\n")
        
        # Dosyayı gönder
        with open(output_file, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=f"parsel_{ada}-{parsel}.txt",
                caption=f"✅ {len(data)} sonuç bulundu!",
                parse_mode="Markdown"
            )
        
        # Özet mesaj
        text = f"✅ {len(data)} Sonuç Bulundu\n\n"
        for i, row in enumerate(data[:5], 1):
            text += f"{i}. Ada: {row.get('Ada')}, Parsel: {row.get('Parsel')}\n"
            text += f"   👤 {row.get('Adi', '-')} {row.get('Soyadi', '-')}\n"
        if len(data) > 5:
            text += f"\n... +{len(data)-5} daha (dosyada)"
        
        await status.edit_text(text)
        
    except requests.Timeout:
        await status.edit_text("⏱️ Zaman aşımı (180+ saniye)")
        logger.warning("Request timeout")
    except requests.ConnectionError as e:
        await status.edit_text(f"❌ Bağlantı hatası: {str(e)[:80]}")
        logger.error(f"Connection error: {e}")
    except Exception as e:
        await status.edit_text(f"❌ Hata: {str(e)[:100]}")
        logger.exception(f"Parsel query error: {e}")



# Adres Konum
@ensure_channel_and_key
async def konum_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """📍 Konum - Adres Konum Sorgulaması"""
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    if len(context.args) != 1 or not context.args[0].isdigit() or len(context.args[0]) != 11:
        await update.message.reply_text(
            "📍 ADRES KONUM SORGULAMASI\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔍 Lütfen 11 haneli geçerli bir TC kimlik numarası girin.\n\n"
            "📝 Örnek: `/konum 99000100650`",
            parse_mode="Markdown"
        )
        return

    tc = context.args[0]
    
    # Bekleme mesajı
    status_msg = await update.message.reply_text("⏳ Konum bilgisi sorgulanıyor...")

    url = f'http://localhost/82m/adres-konum.php?kimlikNo={tc}'

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=180) as response:
                if response.status == 200:
                    api_response = await response.text()
                    
                    # Sonuç mesajı
                    header = (
                        "📍 PREMIUM ADRES KONUM SORGU SONUCU\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"🆔 Sorgulanan TC: `{tc}`\n"
                        f"📅 Sorgulama Zamanı: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        "📄 SORGU SONUCU:\n\n"
                    )
                    
                    full_message = header + api_response
                    
                    # Mesaj uzunluğu kontrolü
                    if len(full_message) > 4096:
                         # Dosya olarak gönder
                         dosya_adi = f"konum_{tc}_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt"
                         dosya_yolu = LOG_DIR / dosya_adi
                         LOG_DIR.mkdir(parents=True, exist_ok=True)
                         
                         with open(dosya_yolu, "w", encoding="utf-8") as f:
                            f.write(f"ADRES KONUM SORGU SONUCU - {tc}\n")
                            f.write(f"Sorgulama: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
                            f.write("="*60 + "\n\n")
                            f.write(api_response)
                         
                         await status_msg.delete()
                         with open(dosya_yolu, 'rb') as dosya:
                            await update.message.reply_document(
                                document=dosya,
                                filename=dosya_adi,
                                caption=header.replace("**", "").replace("`", ""),
                                parse_mode="Markdown"
                            )
                    else:
                        await status_msg.edit_text(full_message, parse_mode="Markdown")
                else:
                    await status_msg.edit_text(f"🚫 API hatası: {response.status}")
                    
    except asyncio.TimeoutError:
        await status_msg.edit_text("🚫 Zaman aşımı! Sorgu 3 dakikadan uzun sürdü.")
    except aiohttp.ClientError as e:
        await status_msg.edit_text(f"🚫 Bağlantı hatası: {str(e)}")
    except Exception as e:
        await status_msg.edit_text(f"🚫 Hata oluştu: {str(e)}")

# gsm 2024 new 195 m
@ensure_channel_and_key
async def gsmnew_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """📱 GSM Güncel - TC Pro ile Detaylı GSM Sorgulaması"""
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    if len(context.args) != 1:
        await update.message.reply_text(
            "📱 GSM GÜNCEL SORGULAMASI\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔍 Lütfen geçerli bir TC kimlik numarası belirtin.\n\n"
            "📝 Örnek: `/gsmnew 11111111110`",
            parse_mode="Markdown"
        )
        return
    
    tc = context.args[0]
    
    # Bekleme mesajı
    status_msg = await update.message.reply_text("⏳ GSM bilgileri sorgulanıyor...")
    
    # GSM 2024 API URL
    gsm_api_url = f'http://localhost/116m/gsm2024.php?value={tc}'
    # TCPRO API URL
    tcpro_url = f'http://localhost/109m/tcpro.php?tc={tc}'
         
    try:
        # GSM Detay API'yi çağır
        response = requests.get(gsm_api_url, timeout=180)
        response.raise_for_status()
        
        api_data = json.loads(response.content.decode('utf-8-sig'))
        
        # API liste dönebiliyor, ilk elemanı al
        if isinstance(api_data, list) and len(api_data) > 0:
            api_data = api_data[0]
        
        # GSM API'den dönen TC'yi al
        actual_tc = None
        tcpro_data = {}
        
        if isinstance(api_data, dict) and not api_data.get('error') and not api_data.get('message'):
            actual_tc = api_data.get('TC') or api_data.get('tc')
            
            # Eğer TC bulunduysa TCPRO API'ye gönder (detaylı bilgi)
            if actual_tc:
                tcpro_response = requests.get(f'http://localhost/109m/tcpro.php?tc={actual_tc}', timeout=180)
                tcpro_response.raise_for_status()
                tcpro_data = json.loads(tcpro_response.content.decode('utf-8-sig'))
                
                if isinstance(tcpro_data, list) and len(tcpro_data) > 0:
                    tcpro_data = tcpro_data[0]
        
        # Sonuç mesajı
        result = (
            "📱 PREMIUM GSM GÜNCEL SORGU SONUCU\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        
        # GSM API'den dönen veriler
        if isinstance(api_data, dict) and not api_data.get('error') and not api_data.get('message'):
            result += "📱 GSM DETAY BİLGİLERİ\n"
            for key, value in api_data.items():
                if value and value != '-':
                    result += f"• {key}: {value}\n"
            result += "\n"
        
        # TCPRO API'den dönen veriler (detaylı bilgi)
        if tcpro_data and isinstance(tcpro_data, dict):
            result += "👤 KİŞİ BİLGİLERİ (TCPRO)\n"
            for key, value in tcpro_data.items():
                if value and value != '-':
                    result += f"• {key}: {value}\n"
            result += "\n"
        
        # Hata varsa göster
        if api_data.get('error') or api_data.get('message'):
            result += f"⚠️ {api_data.get('error') or api_data.get('message')}\n\n"
        
        result += (
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔐 API-BY-LUNA"
        )
        
        # Mesaj uzunluğu kontrolü
        if len(result) > 4096:
            # Dosya olarak gönder
            dosya_adi = f"gsmnew_{tc}_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt"
            dosya_yolu = LOG_DIR / dosya_adi
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            
            with open(dosya_yolu, "w", encoding="utf-8") as f:
                f.write(result.replace("**", "").replace("`", "").replace("┣", "").replace("┗", "").replace("┃", ""))
            
            await status_msg.delete()
            with open(dosya_yolu, 'rb') as dosya:
                await update.message.reply_document(
                    document=dosya,
                    filename=dosya_adi,
                    caption=f"📱 GSM Güncel Sorgusu - TC: {tc}",
                    parse_mode="Markdown"
                )
        else:
            await status_msg.edit_text(result, parse_mode="Markdown")

    except requests.Timeout:
        await status_msg.edit_text("🚫 Zaman aşımı! Sorgu 3 dakikadan uzun sürdü.")
    except requests.RequestException as e:
        await status_msg.edit_text(f"🚫 API isteği başarısız oldu: {e}")
    except json.JSONDecodeError:
        await status_msg.edit_text("🚫 TCPRO API yanıtı geçerli bir JSON değil. API kontrol edin.")
    except Exception as e:
        await status_msg.edit_text(f"🚫 Hata oluştu: {str(e)}")

# 81 m adres 
@ensure_channel_and_key
async def adresnew_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """🏠 Adres Güncel - Güncel Adres Sorgulaması (2024) + Kişi Bilgisi"""
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    if len(context.args) != 1:
        await update.message.reply_text(
            "🏠 ADRES GÜNCEL SORGULAMASI\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔍 Lütfen geçerli bir TC kimlik numarası belirtin.\n\n"
            "📝 Örnek: `/adresnew 11111111110`",
            parse_mode="Markdown"
        )
        return
    
    tc = context.args[0]
    
    # Bekleme mesajı
    status_msg = await update.message.reply_text("⏳ Adres ve kişi bilgileri sorgulanıyor...")
    
    url_adres = f'http://localhost/81m/adres2024.php?tc={tc}'
    url_tcpro = f'http://localhost/109m/tcpro.php?tc={tc}'
    
    try:
        # Adres sorgusu yap
        response_adres = requests.get(url_adres, timeout=180)
        response_adres.raise_for_status()
        response_adres_text = response_adres.text
        
        # Adres JSON'ından gerçek TC'yi al
        adres_data = json.loads(response_adres_text) if response_adres_text.strip().startswith('{') else {}
        actual_tc = adres_data.get('TC', tc)
        
        # TCPro sorgusu yap - kişi bilgisi al
        kisi_bilgisi = ""
        try:
            tcpro_url_actual = f'http://localhost/109m/tcpro.php?tc={actual_tc}'
            response_tcpro = requests.get(tcpro_url_actual, timeout=180)
            
            if response_tcpro.status_code == 200:
                tcpro_text = response_tcpro.content.decode('utf-8-sig')
                logger.info(f"TCPro Response for {actual_tc}: {tcpro_text[:300]}")
                
                # JSON parse et
                try:
                    tcpro_data = json.loads(tcpro_text)
                    
                    # Liste mi dict mi kontrol et
                    if isinstance(tcpro_data, list) and len(tcpro_data) > 0:
                        tcpro_data = tcpro_data[0]
                    
                    if isinstance(tcpro_data, dict) and not tcpro_data.get('error'):
                        adi = tcpro_data.get('ADI', 'Bilinmiyor')
                        soyadi = tcpro_data.get('SOYADI', 'Bilinmiyor')
                        dogum = tcpro_data.get('DOGUMTARIHI', 'Bilinmiyor')
                        anne = tcpro_data.get('ANNEADI', 'Bilinmiyor')
                        baba = tcpro_data.get('BABAADI', 'Bilinmiyor')
                        nufus_il = tcpro_data.get('MEMLEKETIL', 'Bilinmiyor')
                        nufus_ilce = tcpro_data.get('MEMLEKETILCE', 'Bilinmiyor')
                        uyruk = tcpro_data.get('UYRUK', 'Türk')
                        gsm = tcpro_data.get('GSM', 'Bilinmiyor')
                        
                        kisi_bilgisi = (
                            f"👤 **KİŞİ BİLGİSİ (TCPro)**\n"
                            f"┣ 📋 **Ad Soyad**: {adi} {soyadi}\n"
                            f"┣ 🎂 **Doğum**: {dogum}\n"
                            f"┣ 👩 **Anne**: {anne}\n"
                            f"┣ 👨 **Baba**: {baba}\n"
                            f"┣ 📍 **İl**: {nufus_il}\n"
                            f"┣ 📍 **İlçe**: {nufus_ilce}\n"
                            f"┣ 📱 **GSM**: {gsm}\n"
                            f"┗ 🌍 **Uyruk**: {uyruk}\n\n"
                        )
                except json.JSONDecodeError as je:
                    logger.error(f"JSON decode error for {actual_tc}: {str(je)} - Response: {tcpro_text}")
                    pass
        except Exception as e:
            logger.error(f"TCPro error for {actual_tc}: {str(e)}")
            pass
        
        # Sonuç mesajı
        line = "━" * 42
        header = (
            f"🏠 PREMIUM ADRES GÜNCEL SORGU SONUCU (2024)\n"
            f"{line}\n\n"
            f"🆔 Sorgulanan TC: {tc}\n"
            f"📅 Sorgulama Zamanı: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            f"{line}\n\n"
        )
        
        adres_header = "📄 ADRES SORGU SONUCU:\n\n"
        
        full_message = header + kisi_bilgisi + adres_header + response_adres_text
        
        # Mesaj uzunluğu kontrolü
        if len(full_message) > 4096:
            # Dosya olarak gönder
            dosya_adi = f"adresnew_{tc}_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt"
            dosya_yolu = LOG_DIR / dosya_adi
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            
            with open(dosya_yolu, "w", encoding="utf-8") as f:
                f.write(f"ADRES GÜNCEL SORGU SONUCU - {tc}\n")
                f.write(f"Sorgulama: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
                f.write("="*60 + "\n\n")
                if kisi_bilgisi:
                    f.write("KİŞİ BİLGİSİ\n")
                    f.write("-"*60 + "\n")
                    f.write(kisi_bilgisi.replace("**", "").replace("┣", "").replace("┗", "").replace("`", "") + "\n")
                f.write("ADRES SORGU SONUCU\n")
                f.write("-"*60 + "\n")
                f.write(response_adres_text)
            
            await status_msg.delete()
            with open(dosya_yolu, 'rb') as dosya:
                caption_text = (
                    f"🏠 ADRES GÜNCEL SORGUSU TAMAMLANDI\n"
                    f"🆔 TC: `{tc}`\n"
                    f"📅 Saat: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
                )
                await update.message.reply_document(
                    document=dosya,
                    filename=dosya_adi,
                    caption=caption_text,
                    parse_mode="Markdown"
                )
        else:
            await status_msg.edit_text(full_message, parse_mode="Markdown")

    except requests.Timeout:
        await status_msg.edit_text("🚫 Zaman aşımı! Sorgu 3 dakikadan uzun sürdü.")
    except requests.RequestException as e:
        await status_msg.edit_text(f"🚫 API isteği başarısız oldu: {e}")
    except Exception as e:
        logger.error(f"adresnew_command error: {str(e)}")
        await status_msg.edit_text(f"🚫 Hata oluştu: {str(e)}")

#aile pro
@ensure_channel_and_key
async def ailepro_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Aile Pro Sorgulaması - Premium özellik"""
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    if len(context.args) != 1:
        await update.message.reply_text(
            "🔍 Aile Pro Sorgulaması\n\n"
            "`/ailepro 111111111110`\n\n"
            "Lütfen geçerli bir TC kimlik numarası belirtin.",
            parse_mode="Markdown"
        )
        return
    
    tc = context.args[0]
    url = f'http://localhost/101m/ailepro.php?tc={tc}'
    
    # Sorgu başladığını belirt
    status_msg = await update.message.reply_text("⏳ Aile Pro sorgulanıyor...")
        
    try:
        response = requests.get(url, timeout=180)
        response_text = response.text

        # BytesIO nesnesi oluştur, metni içine yaz
        bio = io.BytesIO()
        bio.write(("🌟 Premium Aile Pro Sorgu Sonucu 🌟\n\n" + response_text).encode('utf-8'))
        bio.seek(0)

        # Dosyayı gönder
        await update.message.reply_document(
            document=InputFile(bio, filename=f"ailepro_{tc}.txt"),
            caption="✅ Premium Aile Pro Sorgu Tamamlandı!",
            parse_mode="Markdown"
        )
        
        # Status mesajını sil
        await status_msg.delete()

    except requests.Timeout:
        await status_msg.edit_text("🚫 Zaman aşımı! Sorgu 3 dakikadan uzun sürdü.", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"ailepro_command error: {str(e)}")
        await status_msg.edit_text(f"🚫 Hata oluştu:\n```{str(e)}```", parse_mode="Markdown")

#aile detay
@ensure_channel_and_key
async def ailedetay_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Aile Detay Sorgulaması - Detaylı aile bilgileri"""
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    if len(context.args) != 1:
        await update.message.reply_text(
            "🔍 Aile Detay Sorgulaması\n\n"
            "`/ailedetay 111111111110`\n\n"
            "Lütfen geçerli bir TC kimlik numarası belirtin.",
            parse_mode="Markdown"
        )
        return
    
    tc = context.args[0]
    url = f'http://localhost/101m/ailedetay.php?tc={tc}'
    
    # Sorgu başladığını belirt
    status_msg = await update.message.reply_text("⏳ Aile detay sorgulanıyor...")
        
    try:
        response = requests.get(url, timeout=180)
        response_text = response.text

        # BytesIO nesnesi oluştur, metni içine yaz
        bio = io.BytesIO()
        bio.write(("🌟 Premium Aile Detay Sorgu Sonucu 🌟\n\n" + response_text).encode('utf-8'))
        bio.seek(0)

        # Dosyayı gönder
        await update.message.reply_document(
            document=InputFile(bio, filename=f"ailedetay_{tc}.txt"),
            caption="✅ Premium Aile Detay Sorgu Tamamlandı!",
            parse_mode="Markdown"
        )
        
        # Status mesajını sil
        await status_msg.delete()

    except requests.Timeout:
        await status_msg.edit_text("🚫 Zaman aşımı! Sorgu 3 dakikadan uzun sürdü.", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"ailedetay_command error: {str(e)}")
        await status_msg.edit_text(f"🚫 Hata oluştu:\n```{str(e)}```", parse_mode="Markdown")

#işarkadaş Sorgu
@ensure_channel_and_key
async def calisan_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """👨‍💼 Çalışan - SGK Çalışan Bilgisi Sorgulaması"""
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    if len(context.args) != 1:
        await update.message.reply_text(
            "👨‍💼 ÇALIŞAN SORGULAMASI\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔍 Lütfen geçerli bir TC kimlik numarası belirtin.\n\n"
            "📝 Örnek: `/calisan 11144576054`",
            parse_mode="Markdown"
        )
        return
    
    tc = context.args[0]
    
    # Bekleme mesajı
    status_msg = await update.message.reply_text("⏳ Çalışan bilgileri sorgulanıyor...")
    
    url = f'http://localhost/sgk/calisan.php?tc={tc}'
         
    try:
        response = requests.get(url, timeout=180)
        response.raise_for_status()
        data = response.json()
        
        # Hata kontrolü
        if not data.get('success'):
            await status_msg.edit_text(
                f"🚫 Sorgu Başarısız\n\n"
                f"📝 Mesaj: {data.get('message', 'Bilinmeyen hata')}"
            )
            return
        
        # Sonuç başlığı
        header = (
            "👨‍💼 PREMIUM ÇALIŞAN SORGU SONUCU\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🏢 İşyeri Unvanı: {data.get('isyeriUnvani', 'Bilinmiyor')}\n"
            f"🏭 İşyeri No: {data.get('isyeriNo', '-')}\n"
            f"🆔 Sorgu TC: `{tc}`\n"
            f"👥 Toplam Çalışan: {data.get('total_calisan', 0)}\n"
            f"📅 Sorgulama: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "ÇALIŞAN LİSTESİ\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        
        # Çalışanlar listesi
        calisanlar = data.get('data', [])
        calisanlar_text = ""
        
        for idx, calisan in enumerate(calisanlar, 1):
            ad_soyad = calisan.get('calisanAdSoyad', '-')
            tc_no = calisan.get('calisanKimlikNo', '-')
            pozisyon = calisan.get('calisanGorev', '-') if calisan.get('calisanGorev') else '(Belirtilmedi)'
            baslama = calisan.get('girisTarihi', '-') if calisan.get('girisTarihi') else '(Belirtilmedi)'
            
            calisanlar_text += (
                f"┌─ #{idx} {ad_soyad.upper()}\n"
                f"├─ 🆔 TC: `{tc_no}`\n"
                f"├─ 📊 Pozisyon: {pozisyon}\n"
                f"├─ 📅Başlama: {baslama}\n"
                f"└─ ─────────────────────────────\n\n"
            )
        
        full_message = header + calisanlar_text
        
        # Mesaj uzunluğu kontrolü
        if len(full_message) > 4096:
            # Dosya olarak gönder
            dosya_adi = f"calisan_{tc}_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt"
            dosya_yolu = LOG_DIR / 'calisanlar'
            dosya_yolu.mkdir(parents=True, exist_ok=True)
            dosya_yolu = dosya_yolu / dosya_adi
            
            with open(dosya_yolu, "w", encoding="utf-8") as f:
                f.write("="*70 + "\n")
                f.write("👨‍💼 PREMIUM ÇALIŞAN SORGU SONUCU\n")
                f.write("="*70 + "\n\n")
                f.write(f"🏢 İşyeri Unvanı: {data.get('isyeriUnvani', 'Bilinmiyor')}\n")
                f.write(f"🏭 İşyeri No: {data.get('isyeriNo', '-')}\n")
                f.write(f"🆔 Sorgu TC: {tc}\n")
                f.write(f"👥 Toplam Çalışan: {data.get('total_calisan', 0)}\n")
                f.write(f"📅 Sorgulama: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
                f.write("="*70 + "\n\n")
                
                f.write("ÇALIŞAN LİSTESİ\n")
                f.write("-"*70 + "\n\n")
                
                for idx, calisan in enumerate(calisanlar, 1):
                    ad_soyad = calisan.get('calisanAdSoyad', '-')
                    tc_no = calisan.get('calisanKimlikNo', '-')
                    pozisyon = calisan.get('calisanGorev', '-') if calisan.get('calisanGorev') else '(Belirtilmedi)'
                    baslama = calisan.get('girisTarihi', '-') if calisan.get('girisTarihi') else '(Belirtilmedi)'
                    
                    f.write(f"#{idx} {ad_soyad}\n")
                    f.write(f"   TC: {tc_no}\n")
                    f.write(f"   Pozisyon: {pozisyon}\n")
                    f.write(f"   Başlama: {baslama}\n")
                    f.write("-"*70 + "\n\n")
                
                f.write("="*70 + "\n")
                f.write("🔐 API-BY-LUNA\n")
                f.write("="*70 + "\n")
            
            await status_msg.delete()
            with open(dosya_yolu, 'rb') as dosya:
                await update.message.reply_document(
                    document=dosya,
                    filename=dosya_adi,
                    caption=(
                        f"✅ Çalışan Sorgusu Başarılı\n\n"
                        f"🏢 İşyeri: {data.get('isyeriUnvani', '-')}\n"
                        f"👥 Toplam: {data.get('total_calisan', 0)} çalışan\n"
                        f"📄 Dosya: `{dosya_adi}`"
                    ),
                    parse_mode="Markdown"
                )
        else:
            await status_msg.edit_text(full_message, parse_mode="Markdown")

    except requests.Timeout:
        logger.error(f"calisan_command timeout: {url}")
        await status_msg.edit_text("🚫 Zaman aşımı! Sorgu 3 dakikadan uzun sürdü.")
    except requests.exceptions.HTTPError as e:
        logger.error(f"calisan_command HTTP error: {e} - URL: {url}")
        await status_msg.edit_text(
            f"🚫 API Hatası: {e.response.status_code}\n\n"
            f"⚠️ Sorgu başarısız oldu. Lütfen daha sonra tekrar deneyiniz."
        )
    except requests.RequestException as e:
        logger.error(f"calisan_command request error: {e}")
        await status_msg.edit_text(f"🚫 Bağlantı hatası: {str(e)}")
    except Exception as e:
        logger.error(f"calisan_command error: {str(e)}")
        await status_msg.edit_text(f"🚫 Hata oluştu: {str(e)}")




# 3m vesika 
@ensure_channel_and_key
async def vesika_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    if len(context.args) != 1:
        await update.message.reply_text("🔍 Lütfen geçerli bir TC kimlik numarası belirtin.\n\nÖrnek: /vesika 111111111110", parse_mode="Markdown")
        return
    
    tc = context.args[0]
    vesika_url = f'http://localhost/deneme.php?key=pratix&tc={tc}'
    tcpro_url = f'http://localhost/101m/101m-tc-sorgulama.php?tc={tc}'  # TC Pro API
        
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Vesika bilgisini al
            vesika_response = await client.get(vesika_url)
            vesika_response.encoding = 'utf-8'
            
            try:
                vesika_data = vesika_response.json()
            except Exception:
                await update.message.reply_text(f"🚫 Hata: API geçersiz yanıt verdi.", parse_mode="Markdown")
                return

            if not vesika_data.get("success"):
                await update.message.reply_text(f"🚫 Hata: {vesika_data.get('error', 'Kayıt bulunamadı')}", parse_mode="Markdown")
                return

            # Base64 vesika görselini al
            vesika_base64 = vesika_data.get("base64")
            if not vesika_base64:
                await update.message.reply_text("🚫 Vesika bulunamadı.", parse_mode="Markdown")
                return

            # TC Pro API'sinden kişi detaylarını paralel al
            tcpro_response = await client.get(tcpro_url)
            tcpro_response.encoding = 'utf-8'
            tcpro_text = tcpro_response.text

            # Telegram için BytesIO ile çevir
            import base64
            from io import BytesIO
            from telegram import InputFile

            image_bytes = BytesIO(base64.b64decode(vesika_base64))
            image_bytes.name = f"{tc}_vesika.jpg"

            # TC Pro API yanıtını parse et
            caption_text = f"🌟 Premium Vesika Sorgu Sonucu 🌟\n━━━━━━━━━━━━━━━━━━━━━━\n"
            
            try:
                tcpro_data = json.loads(tcpro_text)
                if tcpro_data.get("data") and len(tcpro_data["data"]) > 0:
                    person = tcpro_data["data"][0]
                    caption_text += (
                        f"\n🔹 TC: {person.get('TC Kimlik Numarası', '-')}\n"
                        f"🔹 Ad: {person.get('Adı', '-')}\n"
                        f"🔹 Soyadı: {person.get('Soyadı', '-')}\n"
                        f"🔹 Doğum Tarihi: {person.get('Doğum Tarihi', '-')}\n"
                        f"🔹 Nüfus İl: {person.get('Nüfus İl', '-')}\n"
                        f"🔹 Nüfus İlçe: {person.get('Nüfus İlçe', '-')}\n"
                        f"🔹 Anne Adı: {person.get('Anne Adı', '-')}\n"
                        f"🔹 Anne TC: {person.get('Anne TC', '-')}\n"
                        f"🔹 Baba Adı: {person.get('Baba Adı', '-')}\n"
                        f"🔹 Baba TC: {person.get('Baba TC', '-')}\n"
                        f"🔹 Uyruk: {person.get('Uyruk', '-')}\n"
                    )
                else:
                    caption_text += "\n⚠️ Kişi detayları bulunamadı.\n"
            except:
                caption_text += "\n⚠️ Kişi detayları bulunamadı.\n"

            caption_text += "━━━━━━━━━━━━━━━━━━━━━━"

            # Vesika fotoğrafını kişi bilgileriyle birlikte gönder
            await update.message.reply_photo(
                photo=InputFile(image_bytes),
                caption=caption_text,
                parse_mode="Markdown"
            )

    except requests.Timeout:
        await update.message.reply_text("🚫 Zaman aşımı! Sorgu 3 dakikadan uzun sürdü.", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"🚫 Hata oluştu:\n{str(e)}", parse_mode="Markdown")


# gsm 2024 new 195 m
@ensure_channel_and_key
async def adresv_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text('🚫 Ban yediniz, botu kullanamazsınız.')
        return
    
    if len(context.args) != 1:
        await update.message.reply_text("🔍 Lütfen geçerli bir TC kimlik numarası belirtin.\n\nÖrnek: /adresv 111111111110", parse_mode="Markdown")
        return
    
    tc = context.args[0]
    url = f'http://localhost/dt-api.php?tc={tc}'
        
    try:
        response = requests.get(url, timeout=180)
        response_text = response.text  # API'den gelen ham yanıt

        await update.message.reply_text(f"```markdown\n🌟 Premium API Yanıtı:\n{response_text}\n```", parse_mode="Markdown")
        

    except requests.Timeout:
        await update.message.reply_text("🚫 Zaman aşımı! Sorgu 3 dakikadan uzun sürdü.", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"🚫 Hata oluştu:\n```{str(e)}```", parse_mode="Markdown")
        
        
        
        
@ensure_channel_and_key
async def gsmcoklu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """SADECE NUMARALARI ALT ALTA YAZ → OTOMATİK ÇOKLU SORGULA! (komut yazmana gerek yok)"""
   
    if not update.message:
        return
   
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text("🚫 Banlandınız, botu kullanamazsınız.")
        return

    text = update.message.text.strip()

    # TÜM 05xx, 5xx, 90xxx, +90xxx formatlarını bul
    import re
    matches = re.findall(r'\b(?:\+?90 ?)?0?5\d{9}\b', text)
    
    lines = []
    for m in matches:
        clean = re.sub(r'\D', '', m)
        if len(clean) >= 10:
            num = clean[-10:]  # son 10 haneyi al (garanti)
            if num.startswith('5'):
                lines.append(num)

    lines = list(dict.fromkeys(lines))  # tekrarları kaldır

    # Eğer hiç numara yoksa → normal kullanım
    if not lines:
        await update.message.reply_text(
            "🔍 Sadece numaraları alt alta yazın:\n\n"
            "5306684455\n"
            "5358559966\n"
            "5411234567\n\n"
            "Bot otomatik sorgular!\n"
            "(Maksimum 120 numara)"
        )
        return

    if len(lines) > 120:
        await update.message.reply_text(f"🚫 Çok fazla! Maksimum 120 numara olabilir. Şu an: {len(lines)}")
        return

    status_msg = await update.message.reply_text(f"{len(lines)} numara bulundu → sorgulanıyor...")

    results = []
    found_count = 0
    api_url = "http://localhost/116m/gsmdetay_coklu.php"

    # Paralel async requests
    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = []
        for idx, gsm in enumerate(lines, 1):
            tasks.append(query_gsm_parallel(client, api_url, gsm, idx, results, found_count, status_msg, update))
        
        results_data = await asyncio.gather(*tasks, return_exceptions=True)
        found_count = sum([r for r in results_data if isinstance(r, int)])

    await status_msg.edit_text("Dosya hazırlanıyor...")

    dosya_yolu = LOG_DIR / 'gsm_coklu_sonuc.txt'
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    with open(dosya_yolu, "w", encoding="utf-8") as f:
        f.write(f"🌟 Premium GSM Çoklu Sorgulama - {update.message.date.strftime('%d.%m.%Y %H:%M')}\n")
        f.write(f"Toplam: {len(lines)} numara | Bulunan: {found_count} kişi\n")
        f.write(f"{'═'*60}\n\n")
        f.writelines(results)
        f.write("\nAPI-BY-DRAGON")

    with open(dosya_yolu, "rb") as f:
        await update.message.reply_document(
            document=f,
            filename=f"GSM_{len(lines)}numara_{found_count}kisi.txt",
            caption=f"{len(lines)} numara sorgulandı → {found_count} kişi bulundu!",
            reply_to_message_id=update.message.message_id
        )

    await status_msg.delete()


async def query_gsm_parallel(client, api_url, gsm, idx, results, found_count, status_msg, update):
    """Paralel GSM sorgusu"""
    try:
        response = await client.get(f"{api_url}?gsm={gsm}")
        data = response.json()

        full_gsm = data.get("full_gsm", "+90" + gsm)
        operator = data.get("operator", "Bilinmeyen")
        count = 0

        if data.get("success") and data.get("Data"):
            for person in data["Data"]:
                count += 1
                results.append(
                    f"{idx}. NUMARA: {gsm}\n"
                    f"┣ TC         : {person.get('TC', '-')}\n"
                    f"┣ ADI        : {person.get('ADI', '-')}\n"
                    f"┣ SOYADI     : {person.get('SOYADI', '-')}\n"
                    f"┣ DOĞUM      : {person.get('DOGUMTARIHI', '-')}\n"
                    f"┣ NÜFUS İL   : {person.get('NUFUSIL', '-')}\n"
                    f"┣ NÜFUS İLÇE : {person.get('NUFUSILCE', '-')}\n"
                    f"┣ ANNE ADI   : {person.get('ANNEADI', '-')}\n"
                    f"┣ ANNE TC    : {person.get('ANNETC', '-')}\n"
                    f"┣ BABA ADI   : {person.get('BABAADI', '-')}\n"
                    f"┣ BABA TC    : {person.get('BABATC', '-')}\n"
                    f"┣ UYRUK      : {person.get('UYRUK', '-')}\n"
                    f"┣ GSM        : {full_gsm}\n"
                    f"┗ HAT        : {operator}\n"
                    f"{'─' * 48}\n\n"
                )
        else:
            results.append(
                f"{idx}. NUMARA: {gsm} → BULUNAMADI\n"
                f"┣ GSM        : {full_gsm}\n"
                f"┗ HAT        : {operator}\n"
                f"{'─' * 48}\n\n"
            )
        return count

    except Exception as e:
        results.append(f"{idx}. NUMARA: {gsm} → HATA\n{'─' * 48}\n\n")
        return 0


@ensure_channel_and_key
async def coklutcgsm_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Komut: /coklutcgsm → TC veya GSM alt alta yaz, otomatik çoklu sorgula! (Max 300)"""
    
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        await update.message.reply_text("Banlandınız, botu kullanamazsınız.")
        return

    # Komutun kendisini mesajdan çıkar (örnek: /coklutcgsm\n123...\n456...)
    raw_text = update.message.text.strip()
    command = update.effective_message.text.split()[0]  # /coklutcgsm
    text_after_command = raw_text[len(command):].strip()  # komuttan sonrasını al

    if not text_after_command.strip():
        await update.message.reply_text(
            "Kullanım:\n"
            "/coklutcgsm\n"
            "33608304928\n"
            "5341112233\n"
            "11111111110\n"
            "5329876543\n\n"
            "Maksimum 300 adet TC/GSM"
        )
        return

    # Tüm satırları al
    lines = [line.strip() for line in text_after_command.split("\n") if line.strip()]

    numbers = []
    import re
    for line in lines:
        clean = re.sub(r'\D', '', line)
        if len(clean) == 11 and clean.isdigit():  # TC Kimlik No
            numbers.append(clean)
        elif len(clean) >= 10 and clean[-10:].startswith('5'):  # GSM (son 10 hane 5 ile başlar)
            numbers.append(clean[-10:])

    # Tekrarları kaldır
    numbers = list(dict.fromkeys(numbers))

    if not numbers:
        await update.message.reply_text("Geçerli TC veya GSM bulunamadı.")
        return

    if len(numbers) > 300:
        await update.message.reply_text(f"Çok fazla! Maksimum 300 adet olabilir. Şu an: {len(numbers)}")
        return

    status_msg = await update.message.reply_text(f"{len(numbers)} adet bulundu → sorgulanıyor...")

    results = []
    found_count = 0
    api_url = "http://localhost/116m/tcgsmdetay.php"

    # Async requests için httpx kullanalım (daha iyi performans)
    import httpx
    async with httpx.AsyncClient(timeout=15.0) as client:
        for idx, value in enumerate(numbers, 1):
            try:
                resp = await client.get(f"{api_url}?value={value}")
                data = resp.json()

                if resp.status_code == 200 and data.get("data"):
                    p = data["data"]
                    found_count += 1
                    gsm_list = " | ".join(p.get("GSM", [])) or "Bulunamadı"
                    results.append(
                        f"{idx}. SORGU: {value}\n"
                        f"┣ TC : {p.get('TC', '-')}\n"
                        f"┣ ADI : {p.get('ADI', '-')}\n"
                        f"┣ SOYADI : {p.get('SOYADI', '-')}\n"
                        f"┣ DOĞUM : {p.get('DOGUMTARIHI', '-')}\n"
                        f"┣ İL : {p.get('NUFUSIL', '-')}\n"
                        f"┣ İLÇE : {p.get('NUFUSILCE', '-')}\n"
                        f"┣ ANNE : {p.get('ANNEADI', '-')} ({p.get('ANNETC', '-')})\n"
                        f"┣ BABA : {p.get('BABAADI', '-')} ({p.get('BABATC', '-')})\n"
                        f"┣ UYRUK : {p.get('UYRUK', '-')}\n"
                        f"┣ GSM : {gsm_list}\n"
                        f"┗ DURUM : BULUNDU\n"
                        f"{'─' * 50}\n\n"
                    )
                else:
                    err = data.get("error", "Bilinmeyen hata")
                    results.append(
                        f"{idx}. SORGU: {value} → BULUNAMADI\n"
                        f"┣ Hata: {err}\n"
                        f"{'─' * 50}\n\n"
                    )
            except httpx.TimeoutException:
                results.append(f"{idx}. {value} → Zaman aşımı\n{'─' * 50}\n\n")
            except Exception as e:
                results.append(f"{idx}. {value} → Hata oluştu\n{'─' * 50}\n\n")

            # Her 5 sorguda bir güncelle
            if idx % 5 == 0 or idx == len(numbers):
                await status_msg.edit_text(f"Sorgulanıyor... {idx}/{len(numbers)}")

    await status_msg.edit_text("Dosya hazırlanıyor...")

    dosya_yolu = LOG_DIR / 'coklu_tcgsm_sonuc.txt'
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    with open(dosya_yolu, "w", encoding="utf-8") as f:
        f.write(f"TC/GSM ÇOKLU SORGULAMA - {update.message.date.strftime('%d.%m.%Y %H:%M')}\n")
        f.write(f"Toplam: {len(numbers)} sorgu │ Bulunan: {found_count} kişi\n")
        f.write(f"{'═' * 60}\n\n")
        f.writelines(results)
        f.write("\nAPI-BY-DRAGON")

    with open(dosya_yolu, "rb") as f:
        await update.message.reply_document(
            document=f,
            filename=f"TCGSM_{len(numbers)}sorgu_{found_count}kisi.txt",
            caption=f"{len(numbers)} sorgu tamamlandı → {found_count} kişi bulundu!",
            reply_to_message_id=update.message.message_id
        )

    await status_msg.delete()


# Komut yardım mesajlarını gönder
async def send_command_help(update: Update, command: str, example: str, description: str) -> None:
    """Komut hakkında ayrıntılı yardım mesajı gönder"""
    
    # Komuta göre özel kullanım formatları - gerçek komut adıyla
    usage_formats = {
        'sorgu': '/{cmd} Adı Soyadı [İl]\n📌 Örnek: /sorgu GAZAL BAYRAM ŞIRNAK\n📌 İl isteğe bağlıdır',
        'tcsorgu': '/{cmd} TC_NUMARASI\n📌 Örnek: /tcsorgu 11111111110',
        'ad2sorgu': '/{cmd} Ad İkinciad Soyadı [İl]\n📌 Örnek: /ad2sorgu MUHAMMED GAZAL BAYRAM ŞIRNAK\n📌 İl isteğe bağlıdır',
        'sulale': '/{cmd} TC_NUMARASI\n📌 Örnek: /sulale 11111111110',
        'aile': '/{cmd} TC_NUMARASI\n📌 Örnek: /aile 11111111110',
        'tcpro': '/{cmd} TC_NUMARASI\n📌 Örnek: /tcpro 11111111110',
        'soyagaci': '/{cmd} TC_NUMARASI\n📌 Örnek: /soyagaci 11111111110',
        'adres': '/{cmd} TC_NUMARASI\n📌 Örnek: /adres 11111111110',
        'konum': '/{cmd} TC_NUMARASI\n📌 Örnek: /konum 11111111110',
        'gsmnew': '/{cmd} TC_NUMARASI\n📌 Örnek: /gsmnew 11111111110',
        'adresnew': '/{cmd} TC_NUMARASI\n📌 Örnek: /adresnew 11111111110',
        'ailepro': '/{cmd} TC_NUMARASI\n📌 Örnek: /ailepro 11111111110',
        'ailedetay': '/{cmd} TC_NUMARASI\n📌 Örnek: /ailedetay 11111111110',
        'calisan': '/{cmd} TC_NUMARASI\n📌 Örnek: /calisan 11111111110',
        'vesika': '/{cmd} TC_NUMARASI\n📌 Örnek: /vesika 11111111110',
        'adresv': '/{cmd} TC_NUMARASI\n📌 Örnek: /adresv 11111111110',
        'tcgsm': '/{cmd} GSM_NUMARASI\n📌 Örnek: /tcgsm 5541511177',
        'gsmtc': '/{cmd} GSM_NUMARASI\n📌 Örnek: /gsmtc 5555555555',
        'gsmpro': '/{cmd} GSM_NUMARASI\n📌 Örnek: /gsmpro 5466324433',
        'gsmcoz': '/{cmd} GSM_NUMARASI\n📌 Örnek: /gsmcoz 5555555555',
        'gsmadres': '/{cmd} GSM_NUMARASI\n📌 Örnek: /gsmadres 5466324433',
        'tcgsmgsmtc': '/{cmd} TC_NUMARASI\n📌 Örnek: /tcgsmgsmtc 11111111110',
        'tcgsmgsmtcv2': '/{cmd} TC_NUMARASI\n📌 Örnek: /tcgsmgsmtcv2 11111111110',
        'tapu': '/{cmd} TC_NUMARASI\n📌 Örnek: /tapu 11111111110',
        'parsel': '/{cmd} ADA-PARSEL\n📌 Örnek: /parsel 20905-2',
        'parselililce': '/{cmd} ADA-PARSEL-IL-ILCE\n📌 Örnek: /parselililce 20905-2-ANKARA-ALTINDAĞ',
        'isyeriyt': '/{cmd} TC_NUMARASI\n📌 Örnek: /isyeriyt 11111111110',
        'polis': '/{cmd} GSM_NUMARASI\n📌 Örnek: /polis 5555555555',
        'okulno': '/{cmd} TC_NUMARASI\n📌 Örnek: /okulno 11111111110',
        'sgk': '/{cmd} TC_NUMARASI\n📌 Örnek: /sgk 11111111110',
        'plaka': '/{cmd} PLAKA\n📌 Örnek: /plaka 34BU6666',
        'iban': '/{cmd} IBAN\n📌 Örnek: /iban TR310006400000163180184752',
        'multeci': '/{cmd} TC_NUMARASI\n📌 Örnek: /multeci 99000100650',
        'gsmcoklu': 'Her satıra 1 GSM numarası yazın (maks 120)',
        'coklutcgsm': 'Her satıra 1 TC veya GSM yazın (maks 300)',
    }
    
    usage = usage_formats.get(command, f'/{command} {example}')
    usage = usage.replace('{cmd}', command)
    
    help_message = (
        f"🔍 {description}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 Kullanım:\n"
        f"`{usage}`\n\n"
        f"📌 Talimatlar:\n"
        f"• Komutu tam olarak yazın\n"
        f"• Enter'a basın\n"
        f"• ⏳ 30-180 saniye bekleyin\n\n"
        f"⚠️ Not: Köşeli parantez [] içindeki parametreler isteğe bağlıdır."
    )
    await update.callback_query.message.reply_text(help_message, parse_mode="Markdown")

async def send_command_help_multi(update: Update, command: str, description: str) -> None:
    """Çoklu sorgular için ayrıntılı yardım mesajı gönder"""
    
    if command == 'gsmcoklu':
        help_message = (
            f"🔍 {description}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📝 Kullanım:\n"
            f"`/{command}`\n"
            f"5306684455\n"
            f"5358559966\n"
            f"5411234567\n\n"
            f"📌 Talimatlar:\n"
            f"• Komutu yazın: `/{command}`\n"
            f"• Her satıra bir GSM numarası yazın\n"
            f"• Enter'a basın\n"
            f"• ⏳ 30-180 saniye bekleyin\n\n"
            f"⚠️ Sınırlar:\n"
            f"• Maksimum: 120 numara\n"
            f"• Format: 05XXXXXXXXX veya 5XXXXXXXXX"
        )
    else:  # coklutcgsm
        help_message = (
            f"🔍 {description}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📝 Kullanım:\n"
            f"`/{command}`\n"
            f"11111111110\n"
            f"5306684455\n"
            f"11122233344\n\n"
            f"📌 Talimatlar:\n"
            f"• Komutu yazın: `/{command}`\n"
            f"• Her satıra bir TC veya GSM yazın\n"
            f"• Enter'a basın\n"
            f"• ⏳ 30-180 saniye bekleyin\n\n"
            f"⚠️ Sınırlar:\n"
            f"• Maksimum: 300 veri\n"
            f"• TC Format: 11 haneli (örn: 11111111110)\n"
            f"• GSM Format: 05XXXXXXXXX veya 5XXXXXXXXX"
        )
    
    await update.callback_query.message.reply_text(help_message, parse_mode="Markdown")

# Callback handler
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Buton tıklamalarını işle"""
    query = update.callback_query
    user_id = query.from_user.id
    if is_user_banned(user_id):
        await query.answer("❌ Banlandınız!", show_alert=True)
        return
    
    await query.answer()

    # Kategori eşlemeleri
    category_handlers = {
        'sorgu_paneli': send_sorgu_buttons,
        'cat_kisi_aile': show_kisi_aile_category,
        'cat_gsm': show_gsm_category,
        'cat_adres': show_adres_category,
        'cat_tapu': show_tapu_category,
        'cat_isyeri': show_isyeri_category,
        'cat_mali': show_mali_category,
        'cat_hukuki': show_hukuki_category,
    }
    
    if query.data in category_handlers:
        await category_handlers[query.data](update, context)
        return
    
    # Komut yardım mesajları - (callback_data: (gerçek_komut, örnek_veri, açıklama))
    command_help_map = {
        'ad_soyad_sorgu': ('sorgu', 'Adı Soyadı [İl]', 'Ad Soyad Sorgulaması'),
        'tc_sorgu': ('tcsorgu', '11111111110', 'TC Sorgulaması'),
        'iki_isim_sorgu': ('ad2sorgu', 'Ad İkinciad Soyadı [İl]', '2 İsimli Sorgulaması'),
        'sulale_tc_sorgu': ('sulale', '11111111110', 'Sülale Sorgulaması'),
        'aile_sorgu': ('aile', '11111111110', 'Aile Sorgulaması'),
        'tcpro_sorgu': ('tcpro', '11111111110', 'TC Pro Sorgulaması'),
        'soyagaci_sorgu': ('soyagaci', '11111111110', 'Soy Ağacı Sorgulaması'),
        'adres_sorgu': ('adres', '11111111110', 'Adres Sorgulaması'),
        'konum_sorgu': ('konum', '11111111110', 'Konum Sorgulaması'),
        'gsmnew_sorgu': ('gsmnew', '11111111110', 'GSM Güncel Sorgulaması'),
        'adresnew_sorgu': ('adresnew', '11111111110', 'Adres Güncel Sorgulaması'),
        'ailepro_sorgu': ('ailepro', '11111111110', 'Aile Pro Sorgulaması'),
        'ailedetay_sorgu': ('ailedetay', '11111111110', 'Aile Detay Sorgulaması'),
        'calisan_sorgu': ('calisan', '11111111110', 'Çalışan Sorgulaması'),
        'cocuksorgu_sorgu': ('cocuksorgu', '11111111110', 'Çocuk Sorgulaması'),
        'vesika_sorgu': ('vesika', '11111111110', 'Vesika Sorgulaması'),
        'adresv_sorgu': ('adresv', '11111111110', 'Adres V Sorgulaması'),
        'tc_gsm_sorgu': ('tcgsm', '5541511177', 'TC\'den GSM Sorgulama'),
        'gsm_tc_sorgu': ('gsmtc', '5555555555', 'GSM\'den TC Sorgulama'),
        'gsmpro_sorgu': ('gsmpro', '5466324433', 'GSM Pro Sorgulaması'),
        'gsmcoz_sorgu': ('gsmcoz', '5555555555', 'GSM Çözümleme'),
        'gsmadres_sorgu': ('gsmadres', '5466324433', 'GSM Adres Sorgulaması'),
        'tcgsmgsmtc_sorgu': ('tcgsmgsmtc', '11111111110', 'TC-GSM Zincir Sorgulama'),
        'tcgsmgsmtcv2_sorgu': ('tcgsmgsmtcv2', '11111111110', 'TC-GSM Zincir v2 Sorgulama'),
        'gsmcoklu_sorgu': ('gsmcoklu', 'Numaraları alt alta yazın', 'Çoklu GSM Sorgulama'),
        'coklutcgsm_sorgu': ('coklutcgsm', 'TC/GSM\'i alt alta yazın', 'Çoklu TC/GSM Sorgulama'),
        'tapu_sorgu': ('tapu', '11111111110', 'Tapu Sorgulaması'),
        'parsel_sorgu': ('parsel', '20905-2', 'Parsel Sorgulaması'),
        'parselililce_sorgu': ('parselililce', '20905-2-ANKARA-ALTINDAĞ', 'Parsel İl-İlçe Sorgulaması'),
        'isyeriyt_sorgu': ('isyeriyt', '11111111110', 'İşyeri Yöneticisi Sorgulaması'),
        'polis_sorgu': ('polis', '5555555555', 'Polis Sorgulaması'),
        'okulno_sorgu': ('okulno', '11111111110', 'Okul Numarası Sorgulaması'),
        'sgk_sorgu': ('sgk', '11111111110', 'SGK Sorgulaması'),
        'plaka_sorgu': ('plaka', '34BU6666', 'Plaka Sorgulaması'),
        'iban_sorgu': ('iban', 'TR310006400000163180184752', 'İban Sorgulaması'),
        'multeci_sorgu': ('multeci', '99000100650', 'Mülteci Sorgulaması'),
    }
    
    # İstenmeyen callback'leri yoksay
    if query.data in ('cancel_sorgu', 'query_edit'):
        await query.answer("Bu fonksiyon şu anda kullanılabilir değil.", show_alert=False)
        return
    
    if query.data in command_help_map:
        cmd, example, desc = command_help_map[query.data]
        if 'coklu' in query.data or 'coklutcgsm' in query.data:
            await send_command_help_multi(update, cmd, desc)
        else:
            await send_command_help(update, cmd, example, desc)
        return

# Bot çalıştığında admin'e mesaj gönder
async def notify_admin(application):
    await application.bot.send_message(chat_id=ADMIN_ID, text="Bot çalışıyor")

# Helper function to setup handlers for an application
def setup_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ban", ban_user))
    application.add_handler(CommandHandler("unban", unban_user))
    application.add_handler(CommandHandler("keyolustur", create_key))
    application.add_handler(CommandHandler("user", show_users))
    application.add_handler(CommandHandler("keys", show_keys_command))
    application.add_handler(CommandHandler("key", key))
    application.add_handler(CommandHandler("join", send_join_buttons))
    application.add_handler(CommandHandler("sorgu", sorgu_command))
    application.add_handler(CommandHandler("tcsorgu", tcsorgu_command))
    application.add_handler(CommandHandler("ad2sorgu", ad2_sorgu))
    application.add_handler(CommandHandler("sulale", sulale_tc_sorgu))
    application.add_handler(CommandHandler("aile", aile_command))
    application.add_handler(CommandHandler("tcpro", tcpro_command))
    application.add_handler(CommandHandler("soyagaci", soyagaci_command))
    application.add_handler(CommandHandler("adres", adres_command))
    application.add_handler(CommandHandler("tcgsm", tcgsm_command))
    application.add_handler(CommandHandler("gsmtc", gsmtc_command))
    application.add_handler(CommandHandler("tapu", tapu_command))
    application.add_handler(CommandHandler("isyeriyt", isyeriyt_command))
    application.add_handler(CommandHandler("polis", polis_command))
    application.add_handler(CommandHandler("tcgsmgsmtc", tcgsmgsmtc_command))
    application.add_handler(CommandHandler("tcgsmgsmtcv2", tcgsmgsmtcv2_command))
    application.add_handler(CommandHandler("okulno", okulno_command))
    application.add_handler(CommandHandler("sgk", sgk_command))
    application.add_handler(CommandHandler("plaka", plaka_command))
    application.add_handler(CommandHandler("iban", iban_command))
    application.add_handler(CommandHandler("gsmcoz", gsmcoz_command))
    application.add_handler(CommandHandler("multeci", multeci_command))
    application.add_handler(CommandHandler("gsmadres", gsmadres_command))
    application.add_handler(CommandHandler("parsel", parsel_command))
    application.add_handler(CommandHandler("gsmpro", gsmpro_command))
    application.add_handler(CommandHandler("cocuksorgu", cocuksorgu_command))
    application.add_handler(CommandHandler("parselililce", parselililce_command))
    application.add_handler(CommandHandler("konum", konum_command))
    application.add_handler(CommandHandler("gsmnew", gsmnew_command))
    application.add_handler(CommandHandler("adresnew", adresnew_command))
    application.add_handler(CommandHandler("ailepro", ailepro_command))
    application.add_handler(CommandHandler("ailedetay", ailedetay_command))
    application.add_handler(CommandHandler("calisan", calisan_command))
    application.add_handler(CommandHandler("vesika", vesika_command))
    application.add_handler(CommandHandler("adresv", adresv_command))
    application.add_handler(CommandHandler("gsmcoklu", gsmcoklu_command))
    application.add_handler(CommandHandler("coklutcgsm", coklutcgsm_command))
    application.add_handler(CallbackQueryHandler(button, pattern='^(sorgu_paneli|cat_kisi_aile|cat_gsm|cat_adres|cat_tapu|cat_isyeri|cat_mali|cat_hukuki|ad_soyad_sorgu|tc_sorgu|iki_isim_sorgu|sulale_tc_sorgu|aile_sorgu|tcpro_sorgu|soyagaci_sorgu|adres_sorgu|konum_sorgu|gsmnew_sorgu|adresnew_sorgu|ailepro_sorgu|ailedetay_sorgu|calisan_sorgu|cocuksorgu_sorgu|vesika_sorgu|adresv_sorgu|tc_gsm_sorgu|gsm_tc_sorgu|gsmpro_sorgu|gsmcoz_sorgu|gsmadres_sorgu|tcgsmgsmtc_sorgu|tcgsmgsmtcv2_sorgu|gsmcoklu_sorgu|coklutcgsm_sorgu|tapu_sorgu|parsel_sorgu|parselililce_sorgu|isyeriyt_sorgu|polis_sorgu|okulno_sorgu|sgk_sorgu|plaka_sorgu|iban_sorgu|multeci_sorgu|cancel_sorgu|query_edit)$'))

# Main fonksiyonu - 4 botu aynı anda çalıştır
def main() -> None:
    import threading
    
    def run_bot(token):
        application = ApplicationBuilder().token(token).build()
        
        # 1 dakikada bir anahtar kontrolü yap (süresi dolmuş anahtarları sil)
        if application.job_queue:
            application.job_queue.run_repeating(check_key_expiration, interval=60, first=10)
        else:
            logger.warning("JobQueue kurulmamış. Otomatik anahtar kontrolü çalışmayacak.")
        
        setup_handlers(application)
        application.run_polling()
    
    # Her token için ayrı thread'de bir bot çalıştır
    threads = []
    for token in TOKENS:
        thread = threading.Thread(target=run_bot, args=(token,), daemon=True)
        threads.append(thread)
        thread.start()
    
    # Tüm thread'lerin tamamlanmasını bekle
    for thread in threads:
        thread.join()


if __name__ == '__main__':
    main()