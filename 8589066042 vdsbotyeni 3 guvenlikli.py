# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════════════════════════════════════╗
║                    X4L VIP VDS HOSTING BOT v8.1 - FULLY WORKING                              ║
║                         TÜRKİYE'NİN 1 NUMARALI BOT HOSTİNG SİSTEMİ                           ║
║                              @Tekmisim | x4larsiv | x4lchat                                  ║
╚═══════════════════════════════════════════════════════════════════════════════════════════════╝
"""

import telebot
import subprocess
import os
import zipfile
import tempfile
import shutil
from telebot import types
import time
from datetime import datetime, timedelta
import sqlite3
import logging
import threading
import sys
import atexit
import random

# ================================
# KONFİGÜRASYON
# ================================
TOKEN = '8670868291:AAH_bD8EhDcbZBVEYDp_fXe_3vQveuS-6Tw'
OWNER_ID = 8589066042
ADMIN_ID = 8589066042
ADMIN_USERNAME = "@Sikayetsizxd"
BOT_NAME = "Mico Vip vds"
BOT_VERSION = "v1.1"

# ZORUNLU KANALLAR (ilk kurulum seed listesi - sonrasında admin panelden yönetilir, gerçek liste DB'den okunur)
REQUIRED_CHANNELS = [
    {'name': 'MİCO BİO', 'url': 'https://t.me/sanalintekgerceksahibi', 'emoji': '📚'},
    {'name': 'MİCO BİO SOHBET', 'url': 'https://t.me/+Xc9Gq3Sxq_k5Yzg8', 'emoji': '💬'},
]

# DOSYA YAPILARI
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_BOTS_DIR = os.path.join(BASE_DIR, 'x4l_bots')
DATABASE_DIR = os.path.join(BASE_DIR, 'x4l_data')
LOGS_DIR = os.path.join(BASE_DIR, 'x4l_logs')
BACKUP_DIR = os.path.join(BASE_DIR, 'x4l_backups')
TEMP_DIR = os.path.join(BASE_DIR, 'x4l_temp')

for d in [UPLOAD_BOTS_DIR, DATABASE_DIR, LOGS_DIR, BACKUP_DIR, TEMP_DIR]:
    os.makedirs(d, exist_ok=True)

DB_PATH = os.path.join(DATABASE_DIR, 'x4l_vds.db')
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

# LOG
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# VERİ YAPILARI
bot_processes = {}
pending_approvals = {}
user_sessions = {}
verified_users = set()
admin_ids = {OWNER_ID, ADMIN_ID}

# ================================
# VERİTABANI (HATASIZ)
# ================================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Kullanıcılar tablosu - premium_plan sütunu eklendi
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total_bots INTEGER DEFAULT 0,
        is_banned INTEGER DEFAULT 0,
        ban_reason TEXT,
        is_premium INTEGER DEFAULT 0,
        premium_plan TEXT DEFAULT 'free',
        premium_until TIMESTAMP
    )''')
    
    # Botlar tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS bots (
        bot_id TEXT PRIMARY KEY,
        user_id INTEGER,
        bot_name TEXT,
        file_name TEXT,
        bot_type TEXT,
        status TEXT DEFAULT 'pending',
        port INTEGER,
        start_time TIMESTAMP,
        error_count INTEGER DEFAULT 0
    )''')
    
    # Bot paylaşımları
    c.execute('''CREATE TABLE IF NOT EXISTS bot_shares (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bot_id TEXT,
        shared_with INTEGER,
        shared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(bot_id, shared_with)
    )''')
    
    # Bot logları
    c.execute('''CREATE TABLE IF NOT EXISTS bot_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bot_id TEXT,
        log_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Admin logları
    c.execute('''CREATE TABLE IF NOT EXISTS admin_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER,
        action TEXT,
        target TEXT,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Ticketler
    c.execute('''CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        subject TEXT,
        message TEXT,
        status TEXT DEFAULT 'open',
        admin_response TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Premium talepleri
    c.execute('''CREATE TABLE IF NOT EXISTS premium_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        plan TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Duyurular
    c.execute('''CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        message TEXT,
        sent_to INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Blacklist
    c.execute('''CREATE TABLE IF NOT EXISTS blacklist (
        user_id INTEGER PRIMARY KEY,
        reason TEXT,
        banned_by INTEGER,
        banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Yedekler
    c.execute('''CREATE TABLE IF NOT EXISTS backups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        backup_name TEXT,
        backup_size INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Zorunlu kanallar
    c.execute('''CREATE TABLE IF NOT EXISTS required_channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        url TEXT,
        emoji TEXT DEFAULT '📢',
        added_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Buton özelleştirme (emoji + etiket)
    c.execute('''CREATE TABLE IF NOT EXISTS button_config (
        button_key TEXT PRIMARY KEY,
        emoji TEXT,
        label TEXT,
        updated_by INTEGER,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # İlk kurulumda seed listesiyle doldur (tablo boşsa)
    c.execute('SELECT COUNT(*) FROM required_channels')
    if c.fetchone()[0] == 0:
        for ch in REQUIRED_CHANNELS:
            c.execute('INSERT INTO required_channels (name, url, emoji, added_by) VALUES (?, ?, ?, ?)',
                      (ch['name'], ch['url'], ch.get('emoji', '📢'), OWNER_ID))
    
    # Eğer premium_plan sütunu yoksa ekle (eski veritabanları için)
    try:
        c.execute('ALTER TABLE users ADD COLUMN premium_plan TEXT DEFAULT "free"')
    except:
        pass
    try:
        c.execute('ALTER TABLE users ADD COLUMN premium_until TIMESTAMP')
    except:
        pass
    
    # Owner ve admin ekle
    c.execute('INSERT OR IGNORE INTO users (user_id, username, is_premium, premium_plan) VALUES (?, ?, 1, "diamond")', (OWNER_ID, ADMIN_USERNAME[1:]))
    c.execute('INSERT OR IGNORE INTO users (user_id, username, is_premium, premium_plan) VALUES (?, ?, 1, "diamond")', (ADMIN_ID, ADMIN_USERNAME[1:]))
    
    conn.commit()
    conn.close()
    logger.info("Veritabanı hazır")

init_db()

def load_required_channels():
    """Zorunlu kanal listesini DB'den okuyup global REQUIRED_CHANNELS'i günceller."""
    global REQUIRED_CHANNELS
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, name, url, emoji FROM required_channels ORDER BY id ASC')
        rows = c.fetchall()
        conn.close()
        REQUIRED_CHANNELS = [{'id': r[0], 'name': r[1], 'url': r[2], 'emoji': r[3] or '📢'} for r in rows]
    except Exception as e:
        logger.error(f"Zorunlu kanal yükleme hatası: {e}")

def add_required_channel(name, url, emoji='📢', admin_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO required_channels (name, url, emoji, added_by) VALUES (?, ?, ?, ?)',
              (name, url, emoji, admin_id))
    conn.commit()
    conn.close()
    load_required_channels()

def delete_required_channel(channel_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM required_channels WHERE id=?', (channel_id,))
    conn.commit()
    deleted = c.rowcount > 0
    conn.close()
    load_required_channels()
    return deleted

def delete_all_required_channels():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM required_channels')
    conn.commit()
    conn.close()
    load_required_channels()

load_required_channels()


# ================================
# YARDIMCI FONKSİYONLAR
# ================================
def get_user_folder(user_id):
    f = os.path.join(UPLOAD_BOTS_DIR, str(user_id))
    os.makedirs(f, exist_ok=True)
    return f

def gen_bot_id():
    return f"bot_{int(time.time())}_{random.randint(1000,9999)}"

def get_free_port():
    import socket
    for p in range(10000, 20000):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', p))
                return p
            except:
                continue
    return None

def log_admin(admin_id, action, target, details=""):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('INSERT INTO admin_logs (admin_id, action, target, details) VALUES (?, ?, ?, ?)',
                  (admin_id, action, target, details))
        conn.commit()
        conn.close()
    except:
        pass

# ================================
# GÜVENLİK TARAMASI (YASAKLI MODÜL/IMPORT KONTROLÜ)
# ================================
import re

# Yasaklı desenler: (etiket, regex)
# NOT: Statik bir tarayıcıdır; kararlı biçimde gizlenmiş (obfuscate) kodu
# %100 yakalayacağının garantisi yoktur, ama yaygın kötüye kullanım
# örüntülerini engeller.
SECURITY_BANNED_PATTERNS = [
    ("subprocess",                 r'\bimport\s+subprocess\b|\bfrom\s+subprocess\s+import\b'),
    ("os.system",                  r'\bos\s*\.\s*system\s*\('),
    ("os.popen",                   r'\bos\s*\.\s*popen\s*\('),
    ("os.execv/execve/execl",      r'\bos\s*\.\s*exec(v|ve|l)\s*\('),
    ("multiprocessing",            r'\bimport\s+multiprocessing\b|\bfrom\s+multiprocessing\s+import\b'),
    ("ctypes",                     r'\bimport\s+ctypes\b|\bfrom\s+ctypes\s+import\b'),
    ("__import__",                 r'__import__\s*\('),
    ("eval()",                     r'\beval\s*\('),
    ("exec()",                     r'\bexec\s*\('),
    ("compile()",                  r'\bcompile\s*\('),
    ("importlib",                  r'\bimport\s+importlib\b|\bfrom\s+importlib\s+import\b'),
    ("pickle.loads",               r'\bpickle\s*\.\s*loads\s*\('),
    ("socket.socket/connect/bind", r'\bsocket\s*\.\s*(socket|connect|bind)\s*\('),
    ("shutil.copy/move",           r'\bshutil\s*\.\s*(copy2?|move)\s*\('),
    ("urllib.request/urlopen",     r'\burllib\s*\.\s*(request|urlopen)\b'),
    ("httpx get/post/Client",      r'\bhttpx\s*\.\s*(get|post|Client)\s*\('),
    ("pathlib.Path read/write",    r'Path\s*\([^)]*\)\s*\.\s*(read_text|read_bytes|write_text|write_bytes)\s*\('),
    ("base64.b64decode",           r'\bbase64\s*\.\s*b64decode\s*\('),
    ("zlib.decompress",            r'\bzlib\s*\.\s*decompress\s*\('),
    ("marshal.loads",              r'\bmarshal\s*\.\s*loads\s*\('),
    ("codecs.decode",              r'\bcodecs\s*\.\s*decode\s*\('),
]
_SECURITY_BANNED_COMPILED = [(label, re.compile(pat)) for label, pat in SECURITY_BANNED_PATTERNS]


def scan_code_for_violations(code_text):
    """Verilen kaynak kodu metninde yasaklı desenleri arar.
    Bulunan tüm etiketlerin listesini döner (boşsa temiz demektir)."""
    hits = []
    for label, rx in _SECURITY_BANNED_COMPILED:
        if rx.search(code_text):
            hits.append(label)
    return hits


def scan_path_for_violations(path):
    """Tek bir dosyayı ya da bir klasörü (recursive) .py/.js dosyaları için tarar.
    Dönüş: {dosya_adi: [yasaklı_etiketler]} sözlüğü (temizse boş dict)."""
    results = {}
    targets = []
    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            for fn in files:
                if fn.lower().endswith(('.py', '.js')):
                    targets.append(os.path.join(root, fn))
    else:
        targets.append(path)

    for fp in targets:
        try:
            with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            continue
        hits = scan_code_for_violations(content)
        if hits:
            results[os.path.basename(fp)] = hits
    return results


def is_user_security_banned(user_id):
    """DB'den kullanıcının banlı olup olmadığını kontrol eder."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT is_banned, ban_reason FROM users WHERE user_id=?', (user_id,))
        r = c.fetchone()
        conn.close()
        if r and r[0]:
            return True, r[1]
        return False, None
    except Exception:
        return False, None


def security_auto_ban(user_id, violations, source_desc, cleanup_paths=None):
    """Yasaklı modül/import tespit edilince kullanıcıyı otomatik banlar,
    yüklenen dosyaları temizler ve admini/kullanıcıyı bilgilendirir."""
    detail_lines = "\n".join([f"  • {fn}: {', '.join(labels)}" for fn, labels in violations.items()])
    reason = f"GÜVENLİK: Yasaklı modül/import tespit edildi ({source_desc}) -\n{detail_lines}"[:900]

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO blacklist (user_id, reason, banned_by) VALUES (?, ?, ?)',
                  (user_id, reason, 0))  # banned_by=0 -> otomatik sistem
        c.execute('UPDATE users SET is_banned=1, ban_reason=? WHERE user_id=?', (reason, user_id))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Otomatik ban DB hatası: {e}")

    # Yüklenen dosyaları/klasörleri temizle
    if cleanup_paths:
        for p in cleanup_paths:
            try:
                if os.path.isdir(p):
                    shutil.rmtree(p, ignore_errors=True)
                elif os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass

    log_admin(0, 'security_auto_ban', str(user_id), reason)

    try:
        bot.send_message(
            user_id,
            f"🚫 <b>HESABIN OTOMATİK OLARAK BANLANDI!</b>\n\n"
            f"⚠️ Yüklediğin dosyada yasaklı modül/import tespit edildi.\n"
            f"📋 Sebep: {reason}\n\n"
            f"İtiraz için: {ADMIN_USERNAME}"
        )
    except Exception:
        pass

    for aid in admin_ids:
        try:
            bot.send_message(
                aid,
                f"🛡️ <b>GÜVENLİK TARAMASI: OTOMATİK BAN</b>\n\n"
                f"🆔 Kullanıcı: {user_id}\n"
                f"📄 Kaynak: {source_desc}\n\n"
                f"{detail_lines}\n\n"
                f"✅ Kullanıcı otomatik banlandı ve dosyalar silindi."
            )
        except Exception:
            pass


def get_user_bot_limit(user_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT is_premium, premium_plan FROM users WHERE user_id = ?', (user_id,))
        r = c.fetchone()
        conn.close()
        if r and r[0] == 1:
            plan = r[1] if r[1] else 'gold'
            limits = {'bronze': 15, 'silver': 30, 'gold': 60, 'diamond': 100}
            return limits.get(plan, 60)
        return 1
    except:
        return 1

def get_my_bots(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT bot_id, bot_name, status, bot_type FROM bots WHERE user_id=?', (user_id,))
    own = c.fetchall()
    c.execute('SELECT b.bot_id, b.bot_name, b.status, b.bot_type FROM bots b JOIN bot_shares s ON b.bot_id=s.bot_id WHERE s.shared_with=?', (user_id,))
    shared = c.fetchall()
    conn.close()
    return own, shared

def share_bot(bot_id, target_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('INSERT OR IGNORE INTO bot_shares (bot_id, shared_with) VALUES (?, ?)', (bot_id, target_id))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def start_bot_process(bot_id, user_id, bot_name, file_name, bot_type):
    def target():
        folder = get_user_folder(user_id)
        file_path = os.path.join(folder, file_name)
        if not os.path.exists(file_path):
            return
        port = get_free_port()
        if not port:
            return
        env = os.environ.copy()
        env['BOT_ID'] = bot_id
        env['BOT_OWNER'] = str(user_id)
        env['BOT_PORT'] = str(port)
        try:
            if bot_type == 'py':
                proc = subprocess.Popen([sys.executable, file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
            else:
                proc = subprocess.Popen(['node', file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
            bot_processes[bot_id] = {'process': proc, 'user_id': user_id, 'port': port, 'bot_name': bot_name}
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('UPDATE bots SET status="running", port=?, start_time=CURRENT_TIMESTAMP WHERE bot_id=?', (port, bot_id))
            conn.commit()
            conn.close()
            
            def read_log():
                while True:
                    line = proc.stdout.readline()
                    if line:
                        try:
                            conn = sqlite3.connect(DB_PATH)
                            c = conn.cursor()
                            c.execute('INSERT INTO bot_logs (bot_id, log_text) VALUES (?, ?)', (bot_id, line[:500]))
                            conn.commit()
                            conn.close()
                        except:
                            pass
                    elif proc.poll() is not None:
                        break
                if bot_id in bot_processes:
                    del bot_processes[bot_id]
                try:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute('UPDATE bots SET status="stopped" WHERE bot_id=?', (bot_id,))
                    conn.commit()
                    conn.close()
                except:
                    pass
            threading.Thread(target=read_log, daemon=True).start()
        except Exception as e:
            logger.error(f"Bot başlatma hatası: {e}")
    threading.Thread(target=target, daemon=True).start()

def stop_bot_process(bot_id):
    if bot_id in bot_processes:
        try:
            bot_processes[bot_id]['process'].terminate()
            time.sleep(1)
            del bot_processes[bot_id]
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('UPDATE bots SET status="stopped" WHERE bot_id=?', (bot_id,))
            conn.commit()
            conn.close()
            return True
        except:
            return False
    return False

def restart_bot_process(bot_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT user_id, bot_name, file_name, bot_type FROM bots WHERE bot_id=?', (bot_id,))
    r = c.fetchone()
    conn.close()
    if r:
        stop_bot_process(bot_id)
        time.sleep(2)
        start_bot_process(bot_id, r[0], r[1], r[2], r[3])
        return True
    return False

def delete_bot(bot_id, user_id):
    stop_bot_process(bot_id)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT file_name FROM bots WHERE bot_id=?', (bot_id,))
    r = c.fetchone()
    if r:
        folder = get_user_folder(user_id)
        fp = os.path.join(folder, r[0])
        if os.path.exists(fp):
            os.remove(fp)
    c.execute('DELETE FROM bots WHERE bot_id=?', (bot_id,))
    c.execute('DELETE FROM bot_shares WHERE bot_id=?', (bot_id,))
    c.execute('DELETE FROM bot_logs WHERE bot_id=?', (bot_id,))
    conn.commit()
    conn.close()
    return True

# ================================
# KLAVYELER
# ================================
def main_inline_keyboard(user_id):
    kb = types.InlineKeyboardMarkup(row_width=2)

    # SATIR 1
    kb.add(
        types.InlineKeyboardButton("<tg-emoji emoji-id=\"6206343625232619150\">📊</tg-emoji  Botlarım", callback_data="menu_bots"),
        types.InlineKeyboardButton("📤 Bot Yükle", callback_data="menu_upload", style="success")
    )

    # SATIR 2
    kb.add(
        types.InlineKeyboardButton("<tg-emoji emoji-id=\"6219817246877816475\">😄</tg-emoji> Başlat", callback_data="menu_start"),
        types.InlineKeyboardButton("⏸️ Durdur", callback_data="menu_stop", style="primary")
    )

    # SATIR 3
    kb.add(
        types.InlineKeyboardButton("🔄 Yeniden", callback_data="menu_restart", style="success"),
        types.InlineKeyboardButton("🗑️ Sil", callback_data="menu_delete", style="danger")
    )

    # SATIR 4
    kb.add(
        types.InlineKeyboardButton("📋 Loglar", callback_data="menu_logs", style="danger"),
        types.InlineKeyboardButton("🤝 Paylaş", callback_data="menu_share", style="success")
    )

    # SATIR 5
    kb.add(
        types.InlineKeyboardButton("💎 Premium", callback_data="menu_premium", style="success"),
        types.InlineKeyboardButton("🎫 Destek", callback_data="menu_support", style="success")
    )

    # SATIR 6
    kb.add(
        types.InlineKeyboardButton("📊 Stats", callback_data="menu_stats", style="danger"),
        types.InlineKeyboardButton("⚙️ Ayarlar", callback_data="menu_settings", style="primary")
    )

    # ADMIN
    if user_id in admin_ids:
        kb.add(
            types.InlineKeyboardButton("👑 Admin Panel", callback_data="menu_admin", style="danger")
        )

    # ALT
    kb.add(
        types.InlineKeyboardButton("🔄 Yenile", callback_data="menu_refresh", style="primary")
    )

    return kb


def quick_bot_keyboard(bot_name):
    kb = types.InlineKeyboardMarkup(row_width=2)

    # SATIR 1
    kb.add(
        types.InlineKeyboardButton(
            "🚀 Başlat",
            callback_data=f"quick_start_{bot_name}"
        ),
        types.InlineKeyboardButton(
            "⏸️ Durdur",
            callback_data=f"quick_stop_{bot_name}"
        )
    )

    # SATIR 2
    kb.add(
        types.InlineKeyboardButton(
            "🔄 Yeniden Başlat",
            callback_data=f"quick_restart_{bot_name}"
        ),
        types.InlineKeyboardButton(
            "📋 Loglar",
            callback_data=f"quick_logs_{bot_name}"
        )
    )

    # SATIR 3
    kb.add(
        types.InlineKeyboardButton(
            "🤝 Paylaş",
            callback_data=f"quick_share_{bot_name}"
        ),
        types.InlineKeyboardButton(
            "📊 Durum",
            callback_data=f"quick_status_{bot_name}"
        )
    )

    # SATIR 4
    kb.add(
        types.InlineKeyboardButton(
            "🗑️ Botu Sil",
            callback_data=f"quick_delete_{bot_name}"
        )
    )

    return kb


# ================================
# BUTON ÖZELLEŞTİRME (emoji + etiket)
# ================================
# key -> (varsayılan emoji, varsayılan etiket, callback_data)
CUSTOMIZABLE_BUTTONS = {
    'btn_bots':     ('📂', 'Botlarım',  'menu_bots'),
    'btn_upload':   ('📤', 'Bot Yükle', 'menu_upload'),
    'btn_start':    ('🚀', 'Başlat',    'menu_start'),
    'btn_stop':     ('⏸️', 'Durdur',    'menu_stop'),
    'btn_restart':  ('🔄', 'Yeniden',   'menu_restart'),
    'btn_delete':   ('🗑️', 'Sil',       'menu_delete'),
    'btn_logs':     ('📋', 'Loglar',    'menu_logs'),
    'btn_share':    ('🤝', 'Paylaş',    'menu_share'),
    'btn_premium':  ('💎', 'Premium',   'menu_premium'),
    'btn_stats':    ('📊', 'Stats',     'menu_stats'),
    'btn_support':  ('🎫', 'Destek',    'menu_support'),
    'btn_settings': ('⚙️', 'Ayarlar',   'menu_settings'),
}

def get_button_cfg(key):
    """DB'de özelleştirme varsa onu, yoksa varsayılanı döner: (emoji, label)."""
    default_emoji, default_label, _ = CUSTOMIZABLE_BUTTONS[key]
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT emoji, label FROM button_config WHERE button_key=?', (key,))
        r = c.fetchone()
        conn.close()
        if r:
            return (r[0] or default_emoji, r[1] or default_label)
    except Exception:
        pass
    return (default_emoji, default_label)

def set_button_cfg(key, emoji, label, admin_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO button_config (button_key, emoji, label, updated_by, updated_at)
                 VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                 ON CONFLICT(button_key) DO UPDATE SET
                    emoji=excluded.emoji, label=excluded.label,
                    updated_by=excluded.updated_by, updated_at=CURRENT_TIMESTAMP''',
              (key, emoji, label, admin_id))
    conn.commit()
    conn.close()

def reset_button_cfg(key):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM button_config WHERE button_key=?', (key,))
    conn.commit()
    conn.close()

def button_custom_keyboard():
    k = types.InlineKeyboardMarkup(row_width=1)
    for key in CUSTOMIZABLE_BUTTONS:
        emoji, label = get_button_cfg(key)
        k.add(types.InlineKeyboardButton(f"{emoji} {label}", callback_data=f"btncfg_{key}"))
    k.add(types.InlineKeyboardButton("♻️ TÜMÜNÜ SIFIRLA", callback_data="btncfg_reset_all", style="danger"))
    k.add(types.InlineKeyboardButton("🔙 GERİ", callback_data="menu_admin"))
    return k

def admin_panel_keyboard():
    k = types.InlineKeyboardMarkup(row_width=2)
    k.add(
        types.InlineKeyboardButton("👥 KULLANICILAR", callback_data="admin_users", style="danger"),
        types.InlineKeyboardButton("🔍 KULLANICI ARA", callback_data="admin_search_user", style="primary"),
        types.InlineKeyboardButton("➕ KULLANICI EKLE", callback_data="admin_add_user", style="danger"),
        types.InlineKeyboardButton("🤖 TÜM BOTLAR", callback_data="admin_bots", style="primary"),
        types.InlineKeyboardButton("⏳ BEKLEYEN ONAYLAR", callback_data="admin_pending", style="primary"),
        types.InlineKeyboardButton("🟢 ÇALIŞAN BOTLAR", callback_data="admin_running", style="success"),
        types.InlineKeyboardButton("🔴 DURAN BOTLAR", callback_data="admin_stopped", style="danger"),
        types.InlineKeyboardButton("💎 PREMİUM VER", callback_data="admin_premium", style="primary"),
        types.InlineKeyboardButton("💎 PREMİUM TALEPLERİ", callback_data="admin_premium_requests", style="success"),
        types.InlineKeyboardButton("🚫 BANLA", callback_data="admin_ban", style="danger"),
        types.InlineKeyboardButton("✅ BANI KALDIR", callback_data="admin_unban", style="success"),
        types.InlineKeyboardButton("📋 BLACKLIST", callback_data="admin_blacklist", style="danger"),
        types.InlineKeyboardButton("📊 GENEL STATS", callback_data="admin_stats", style="primary"),
        types.InlineKeyboardButton("📈 GÜNLÜK STATS", callback_data="admin_daily_stats", style="danger"),
        types.InlineKeyboardButton("🎫 TÜM TICKETLER", callback_data="admin_tickets", style="primary"),
        types.InlineKeyboardButton("🆕 AÇIK TICKETLER", callback_data="admin_open_tickets", style="success"),
        types.InlineKeyboardButton("📢 DUYURU", callback_data="admin_announce", style="danger"),
        types.InlineKeyboardButton("🖥️ SİSTEM DURUMU", callback_data="admin_system", style="success"),
        types.InlineKeyboardButton("📝 ADMIN LOGLARI", callback_data="admin_logs", style="danger"),
        types.InlineKeyboardButton("🔄 TÜM BOTLARI BAŞLAT", callback_data="admin_start_all", style="success"),
        types.InlineKeyboardButton("⏸️ TÜM BOTLARI DURDUR", callback_data="admin_stop_all", style="danger"),
        types.InlineKeyboardButton("🧹 ÖLÜ BOT TEMİZLE", callback_data="admin_clean", style="danger"),
        types.InlineKeyboardButton("💾 YEDEK AL", callback_data="admin_backup", style="primary"),
        types.InlineKeyboardButton("➕ ZORUNLU KANAL EKLE", callback_data="admin_add_channel", style="primary"),
        types.InlineKeyboardButton("🗑️ ZORUNLU KANAL SİL", callback_data="admin_del_channel", style="danger"),
        types.InlineKeyboardButton("🧹 TÜM ZORUNLU KANALLARI SİL", callback_data="admin_del_all_channels", style="danger"),
        types.InlineKeyboardButton("⚙️ AYARLAR", callback_data="admin_settings", style="primary"),
        types.InlineKeyboardButton("🎨 BUTON ÖZELLEŞTİR", callback_data="admin_button_custom", style="success"),
        types.InlineKeyboardButton("❓ YARDIM", callback_data="admin_help", style="primary"),
        types.InlineKeyboardButton("🔙 KULLANICI PANELİ", callback_data="admin_to_user", style="danger")
    )
    return k

def channel_keyboard():
    k = types.InlineKeyboardMarkup(row_width=1)
    for ch in REQUIRED_CHANNELS:
        k.add(types.InlineKeyboardButton(f"{ch['emoji']} {ch['name']} - KATIL", url=ch['url']))
    k.add(types.InlineKeyboardButton("✅ KANALLARA KATILDIM", callback_data="check_channels", style="success"))
    return k


def _cbtn(key):
    """Özelleştirilmiş emoji/etiketle InlineKeyboardButton üretir."""
    emoji, label = get_button_cfg(key)
    _, _, callback = CUSTOMIZABLE_BUTTONS[key]
    return types.InlineKeyboardButton(f"{emoji} {label}", callback_data=callback)

def inline_main_menu(user_id):
    kb = types.InlineKeyboardMarkup(row_width=2)

    kb.add(_cbtn('btn_bots'), _cbtn('btn_upload'))
    kb.add(_cbtn('btn_start'), _cbtn('btn_stop'))
    kb.add(_cbtn('btn_restart'), _cbtn('btn_delete'))
    kb.add(_cbtn('btn_logs'), _cbtn('btn_share'))
    kb.add(_cbtn('btn_premium'), _cbtn('btn_stats'))
    kb.add(_cbtn('btn_support'), _cbtn('btn_settings'))

    if user_id in admin_ids:
        kb.add(types.InlineKeyboardButton("👑 Admin Panel", callback_data="menu_admin", style="danger"))

    kb.add(types.InlineKeyboardButton("🔄 Yenile", callback_data="menu_refresh", style="primary"))
    return kb

# ================================
# START KOMUTU
# ================================
@bot.message_handler(commands=['start', 'menu', 'help'])
def cmd_start(message):
    u_id = message.from_user.id
    u_name = message.from_user.first_name
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)',
                  (u_id, message.from_user.username, u_name))
        c.execute('UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id=?', (u_id,))
        conn.commit()
        conn.close()
    except:
        pass

    if u_id not in admin_ids:
        banned, ban_reason = is_user_security_banned(u_id)
        if banned:
            bot.reply_to(message, f"🚫 Hesabın banlı!\n📋 Sebep: {ban_reason or 'Belirtilmemiş'}\n\nİtiraz için: {ADMIN_USERNAME}")
            return
    
    if u_id in admin_ids:
        show_main_menu(message)
        return
    if u_id in verified_users:
        show_main_menu(message)
        return
    
    ch_list = "\n".join([f"{ch['emoji']} {ch['name']}" for ch in REQUIRED_CHANNELS])
    txt = f"""
✨ <b>HOŞ GELDİN {u_name}!</b> ✨

<b>{BOT_NAME}</b>'a hoş geldiniz!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<tg-emoji emoji-id=\"6206080502651164081\">📣</tg-emoji> <b>KANALLARIMIZ</b>
{ch_list}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<tg-emoji emoji-id=\"6206174450765796040\">⚠️</tg-emoji> <b>ÖNEMLİ:</b> Sisteme giriş yapmak için 
lütfen yukarıdaki kanallara katılın!

<tg-emoji emoji-id=\"5240317124295020104\">👍</tg-emoji> Katıldıktan sonra aşağıdaki butona basın.

<i> <tg-emoji emoji-id=\"5436228149081831671\">ℹ️</tg-emoji> Kanallara katılmak zorunludur!</i>
"""
    bot.send_message(u_id, txt, reply_markup=channel_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "check_channels")
def check_channels_callback(call):
    u_id = call.from_user.id
    u_name = call.from_user.first_name
    
    verified_users.add(u_id)
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)',
                  (u_id, call.from_user.username, u_name))
        c.execute('UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id=?', (u_id,))
        conn.commit()
        conn.close()
    except:
        pass
    
    bot.edit_message_text(
        f"<tg-emoji emoji-id=\"5866487896801811945\">🎉</tg-emoji> <b>TEBRİKLER {u_name}!</b> <tg-emoji emoji-id=\"5866487896801811945\">🎉</tg-emoji>\n\n"
        f"<tg-emoji emoji-id=\"5242581542722617083\">👌</tg-emoji> Tüm kanallara başarıyla katıldınız!\n\n"
        f"<tg-emoji emoji-id=\"6219817246877816475\">😄</tg-emoji> Artık {BOT_NAME} sistemini kullanabilirsiniz!\n\n"
        f"<tg-emoji emoji-id=\"6222198028854367391\">👇</tg-emoji> <b>BAŞLAMAK İÇİN BUTONA BAS</b> <tg-emoji emoji-id=\"6222198028854367391\">👇</tg-emoji>",
        call.message.chat.id, call.message.message_id,
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("🚀 DOĞRULANDİ TEKTAR /start", callback_data="enter_system", style="primary")
        )
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "enter_system")
def enter_system(call):
    show_main_menu(call.message)
    bot.answer_callback_query(call.id)

def show_main_menu(message):
    u_id = message.from_user.id if hasattr(message, 'from_user') else message.chat.id
    u_name = message.from_user.first_name if hasattr(message, 'from_user') else "Kullanıcı"
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM bots WHERE user_id=?', (u_id,))
        bot_count = c.fetchone()[0]
        conn.close()
    except:
        bot_count = 0
    
    limit = get_user_bot_limit(u_id)
    running = len([b for b in bot_processes.values() if b.get('user_id') == u_id])
    status = "<tg-emoji emoji-id=\"6206319341487527808\">👑</tg-emoji> SAHİP" if u_id == OWNER_ID else "🔧 ADMIN" if u_id in admin_ids else "<tg-emoji emoji-id=\"5767081411311835729\">🔻</tg-emoji> KULLANICI"
    
    txt = f"""
<tg-emoji emoji-id=\"5242731900937716525\">👋</tg-emoji> <b>ANA MENÜ</b> <tg-emoji emoji-id=\"5242731900937716525\">👋</tg-emoji>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<tg-emoji emoji-id=\"4967925573918655510\">🚮</tg-emoji> <b>Kullanıcı:</b> {u_name}
<tg-emoji emoji-id=\"6206343625232619150\">📊</tg-emoji> <b>Seviye:</b> {status}
<tg-emoji emoji-id=\"5217824874487101321\">😍</tg-emoji> <b>Botlarım:</b> {bot_count}/{limit}
<tg-emoji emoji-id=\"4990298741463319592\">🟢</tg-emoji> <b>Çalışan:</b> {running}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<i>Aşağıdaki butonları kullanarak botlarını yönetebilirsin!</i>
"""
    bot.send_message(u_id, txt, reply_markup=inline_main_menu(u_id))

# ================================
# KULLANICI MESAJ HANDLER
# ================================
@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    u_id = message.from_user.id
    txt = message.text
    if not txt:
        return
    if u_id not in verified_users and u_id not in admin_ids:
        cmd_start(message)
        return
    
    if txt == "🏠 ANA MENÜ" or txt == "🔄 YENİLE":
        show_main_menu(message)
        return
    
    if txt == "❓ YARDIM":
        bot.send_message(u_id, f"❓ YARDIM\n\n📂 BOTLARIM - Botlarını gör\n📤 BOT YÜKLE - Yeni bot yükle\n🚀 BAŞLAT - Bot başlat\n⏸️ DURDUR - Bot durdur\n🔄 YENİDEN - Bot yeniden başlat\n🗑️ SİL - Bot sil\n📋 LOGLAR - Log gör\n🤝 PAYLAŞ - Bot paylaş\n💎 PREMİUM - Premium planlar\n🎫 DESTEK - Destek talebi\n📊 STATS - İstatistikler\n⚙️ AYARLAR - Ayarlar\n\n👑 Admin: {ADMIN_USERNAME}", reply_markup=main_keyboard(u_id))
        return
    
    if txt == "<tg-emoji emoji-id=\"6206343625232619150\">📊</tg-emoji> STATS":
        total_u = len(verified_users)
        total_b = len(bot_processes)
        txt = f"<tg-emoji emoji-id=\"6206343625232619150\">📊</tg-emoji> İSTATİSTİKLER\n\n👥 Kullanıcı: {total_u}\n🚀 Çalışan Bot: {total_b}\n⏳ Bekleyen Onay: {len(pending_approvals)}"
        bot.send_message(u_id, txt, reply_markup=inline_main_menu(u_id))
        return
    
    if txt == "<tg-emoji emoji-id=\"6123171089624340339\">🛍</tg-emoji> PREMİUM":
        plan_txt = """
<tg-emoji emoji-id=\"6125115309650089324\">👑</tg-emoji> BRONZ - 20 TL
   <tg-emoji emoji-id=\"5217824874487101321\">😍</tg-emoji> 2 bot | 💾 256MB | ⚡ %50 CPU

<tg-emoji emoji-id=\"6125115309650089324\">👑</tg-emoji> GÜMÜŞ - 40 TL
   <tg-emoji emoji-id=\"5217824874487101321\">😍</tg-emoji> 4 bot | 💾 512MB | ⚡ %70 CPU

<tg-emoji emoji-id=\"6125115309650089324\">👑</tg-emoji> ALTIN - 60 TL
   <tg-emoji emoji-id=\"5217824874487101321\">😍</tg-emoji> 6 bot | 💾 1024MB | ⚡ %100 CPU

<tg-emoji emoji-id=\"6125115309650089324\">👑</tg-emoji> ELMAS - 100 TL
   <tg-emoji emoji-id=\"5217824874487101321\">😍</tg-emoji> 10 bot | 💾 2048MB | ⚡ %100 CPU
"""
        bot.send_message(u_id, f"💎 PREMİUM PLANLAR\n{plan_txt}\n\n💎 Premium satın almak için /premium yazın veya adminle iletişime geçin:\n{ADMIN_USERNAME}", reply_markup=main_keyboard(u_id))
        return
    
    if txt == "<tg-emoji emoji-id=\"6269426709011895930\">👩‍💻</tg-emoji> DESTEK":
        bot.send_message(u_id, "<tg-emoji emoji-id=\"6269426709011895930\">👩‍💻</tg-emoji> DESTEK TALEBİ\n\nDestek talebi oluşturmak için /ticket komutunu kullanın.\n\nÖrnek: /ticket Botum çalışmıyor", reply_markup=main_keyboard(u_id))
        return
    
    if txt == "⚙️ AYARLAR":
        limit = get_user_bot_limit(u_id)
        bot.send_message(u_id, f"<tg-emoji emoji-id=\"6221939111045895344\">📈</tg-emoji> AYARLARIM\n\n<tg-emoji emoji-id=\"6224129999633388168\">📈</tg-emoji> Bot Limiti: {limit}\n<tg-emoji emoji-id=\"6251345820113707698\">🎁</tg-emoji> Max Dosya: 20MB\n<tg-emoji emoji-id=\"6327678689022579783\">😄</tg-emoji> Desteklenen: .py .js .zip\n\n<tg-emoji emoji-id=\"6222240153893606670\">👹</tg-emoji> Daha fazla özellik için premium planlara göz atın!", reply_markup=main_keyboard(u_id))
        return
    
    if txt == "👑 ADMIN" and u_id in admin_ids:
        bot.send_message(u_id, "🔧 ADMIN PANELİ", reply_markup=admin_panel_keyboard())
        return
    
    if txt == "📂 BOTLARIM":
        own, shared = get_my_bots(u_id)
        if not own and not shared:
            bot.send_message(u_id, "<tg-emoji emoji-id=\"6224185666704511761\">❌</tg-emoji> Henüz botun yok! <tg-emoji emoji-id=\"6222141833502266367\">💎</tg-emoji> BOT YÜKLE butonuna bas.", reply_markup=main_keyboard(u_id))
            return
        msg = "🤖 BOTLARIM\n\n"
        for b in own:
            emoji = "<tg-emoji emoji-id=\"4990298741463319592\">🟢</tg-emoji>" if b[2] == "running" else "<tg-emoji emoji-id=\"4990182601252668309\">🔴</tg-emoji>"
            msg += f"{emoji} 👑 {b[1]} [{b[3].upper()}]\n"
        for b in shared:
            emoji = "<tg-emoji emoji-id=\"4990298741463319592\">🟢</tg-emoji>" if b[2] == "running" else "<tg-emoji emoji-id=\"4990182601252668309\">🔴</tg-emoji>"
            msg += f"{emoji} 🤝 {b[1]} [{b[3].upper()}] (PAYLAŞILAN)\n"
        bot.send_message(u_id, msg, reply_markup=main_keyboard(u_id))
        
        for b in own[:10]:
            try:
                status_emoji = "<tg-emoji emoji-id=\"4990298741463319592\">🟢</tg-emoji>" if b[2] == "running" else "<tg-emoji emoji-id=\"4990182601252668309\">🔴</tg-emoji>"
                bot.send_message(
                    u_id,
                    f"{status_emoji} <b>{b[1]}</b>\n<tg-emoji emoji-id=\"6251345820113707698\">🎁</tg-emoji> Tür: {b[3].upper()}\n<tg-emoji emoji-id=\"6206343625232619150\">📊</tg-emoji> Durum: {b[2]}",
                    reply_markup=quick_bot_keyboard(b[1])
                )
            except:
                pass
        return
    
    if txt == "📤 BOT YÜKLE":
        limit = get_user_bot_limit(u_id)
        own, _ = get_my_bots(u_id)
        if len(own) >= limit:
            bot.send_message(u_id, f"<tg-emoji emoji-id=\"6221914376329237010\">⚠️</tg-emoji> Bot limitin doldu! ({limit}/{limit})\n\n💎 Daha fazla bot için premium satın al: {ADMIN_USERNAME}", reply_markup=main_keyboard(u_id))
            return
        bot.send_message(u_id, "📤 BOT YÜKLE\n\nDesteklenen: .py .js .zip\nMax 20MB\n\nDosyanı gönder:", reply_markup=types.ReplyKeyboardRemove())
        return
    
    if txt == "🚀 BAŞLAT":
        own, _ = get_my_bots(u_id)
        stoppable = [b for b in own if b[2] in ['stopped', 'error', 'approved', 'pending']]
        if not stoppable:
            bot.send_message(u_id, "<tg-emoji emoji-id=\"6221914376329237010\">⚠️</tg-emoji> Başlatılacak bot yok!", reply_markup=main_keyboard(u_id))
            return
        k = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        for b in stoppable:
            k.add(f"▶️ {b[1]}")
        k.add("🏠 ANA MENÜ")
        bot.send_message(u_id, "Başlatmak istediğin botu seç:", reply_markup=k)
        return
    
    if txt == "⏸️ DURDUR":
        own, _ = get_my_bots(u_id)
        running = [b for b in own if b[2] == 'running']
        if not running:
            bot.send_message(u_id, "<tg-emoji emoji-id=\"6221914376329237010\">⚠️</tg-emoji> Durdurulacak bot yok!", reply_markup=main_keyboard(u_id))
            return
        k = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        for b in running:
            k.add(f"⏹️ {b[1]}")
        k.add("🏠 ANA MENÜ")
        bot.send_message(u_id, "Durdurmak istediğin botu seç:", reply_markup=k)
        return
    
    if txt == "🔄 YENİDEN":
        own, _ = get_my_bots(u_id)
        restartable = [b for b in own if b[2] in ['running', 'stopped']]
        if not restartable:
            bot.send_message(u_id, "<tg-emoji emoji-id=\"6221914376329237010\">⚠️</tg-emoji> Yeniden başlatılacak bot yok!", reply_markup=main_keyboard(u_id))
            return
        k = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        for b in restartable:
            k.add(f"🔄️ {b[1]}")
        k.add("🏠 ANA MENÜ")
        bot.send_message(u_id, "Yeniden başlatmak istediğin botu seç:", reply_markup=k)
        return
    
    if txt == "🗑️ SİL":
        own, _ = get_my_bots(u_id)
        if not own:
            bot.send_message(u_id, "<tg-emoji emoji-id=\"6221914376329237010\">⚠️</tg-emoji> Silinecek bot yok!", reply_markup=main_keyboard(u_id))
            return
        k = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        for b in own:
            k.add(f"❌ {b[1]}")
        k.add("🏠 ANA MENÜ")
        bot.send_message(u_id, "Silmek istediğin botu seç:", reply_markup=k)
        return
    
    if txt == "📋 LOGLAR":
        own, shared = get_my_bots(u_id)
        all_b = own + [(s[0], s[1], s[2], s[3]) for s in shared]
        if not all_b:
            bot.send_message(u_id, "<tg-emoji emoji-id=\"6221914376329237010\">⚠️</tg-emoji> Botun yok!", reply_markup=main_keyboard(u_id))
            return
        k = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        for b in all_b[:15]:
            k.add(f"📄 {b[1]}")
        k.add("🏠 ANA MENÜ")
        bot.send_message(u_id, "Loglarını görmek istediğin botu seç:", reply_markup=k)
        return
    
    if txt == "🤝 PAYLAŞ":
        own, _ = get_my_bots(u_id)
        if not own:
            bot.send_message(u_id, "<tg-emoji emoji-id=\"6221914376329237010\">⚠️</tg-emoji> Paylaşılacak bot yok!", reply_markup=main_keyboard(u_id))
            return
        k = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        for b in own:
            k.add(f"🤝 {b[1]}")
        k.add("🏠 ANA MENÜ")
        bot.send_message(u_id, "Paylaşmak istediğin botu seç:", reply_markup=k)
        return
    
    # Başlatma
    if txt.startswith("▶️ "):
        bot_name = txt.split(" ", 1)[1]
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT bot_id, user_id, file_name, bot_type FROM bots WHERE user_id=? AND bot_name=?', (u_id, bot_name))
        r = c.fetchone()
        conn.close()
        if r:
            start_bot_process(r[0], r[1], bot_name, r[2], r[3])
            bot.send_message(u_id, f"<tg-emoji emoji-id=\"6030710528324673233\">✔️</tg-emoji> {bot_name} başlatılıyor...", reply_markup=main_keyboard(u_id))
        else:
            bot.send_message(u_id, "<tg-emoji emoji-id=\"6221914376329237010\">⚠️</tg-emoji> Bot bulunamadı!", reply_markup=main_keyboard(u_id))
        return
    
    # Durdurma
    if txt.startswith("⏹️ "):
        bot_name = txt.split(" ", 1)[1]
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT bot_id FROM bots WHERE user_id=? AND bot_name=?', (u_id, bot_name))
        r = c.fetchone()
        conn.close()
        if r:
            if stop_bot_process(r[0]):
                bot.send_message(u_id, f"<tg-emoji emoji-id=\"6224316916610108722\">📉</tg-emoji> {bot_name} durduruldu!", reply_markup=main_keyboard(u_id))
            else:
                bot.send_message(u_id, f"<tg-emoji emoji-id=\"6221914376329237010\">⚠️</tg-emoji> Durdurulamadı!", reply_markup=main_keyboard(u_id))
        else:
            bot.send_message(u_id, "<tg-emoji emoji-id=\"6221914376329237010\">⚠️</tg-emoji> Bot bulunamadı!", reply_markup=main_keyboard(u_id))
        return
    
    # Yeniden başlatma
    if txt.startswith("🔄️ "):
        bot_name = txt.split(" ", 1)[1]
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT bot_id FROM bots WHERE user_id=? AND bot_name=?', (u_id, bot_name))
        r = c.fetchone()
        conn.close()
        if r:
                restart_bot_process(r[0])
                bot.send_message(u_id, f"<tg-emoji emoji-id=\"6030823232561485465\">🖼️</tg-emoji> {bot_name} yeniden başlatılıyor...", reply_markup=main_keyboard(u_id))
        else:
                bot.send_message(u_id, "<tg-emoji emoji-id=\"6221914376329237010\">⚠️</tg-emoji> Bot bulunamadı!", reply_markup=main_keyboard(u_id))
        return
    
    # Silme
    if txt.startswith("<tg-emoji emoji-id=\"6221914376329237010\">⚠️</tg-emoji> "):
        bot_name = txt.split(" ", 1)[1]
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT bot_id FROM bots WHERE user_id=? AND bot_name=?', (u_id, bot_name))
        r = c.fetchone()
        conn.close()
        if r:
            delete_bot(r[0], u_id)
            bot.send_message(u_id, f"<tg-emoji emoji-id=\"5309909355565437763\">🗑</tg-emoji> {bot_name} silindi!", reply_markup=main_keyboard(u_id))
        else:
            bot.send_message(u_id, "<tg-emoji emoji-id=\"6221914376329237010\">⚠️</tg-emoji> Bot bulunamadı!", reply_markup=main_keyboard(u_id))
        return
    
    # Log görüntüleme
    if txt.startswith("📄 "):
        bot_name = txt.split(" ", 1)[1]
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT bot_id FROM bots WHERE bot_name=? AND (user_id=? OR bot_id IN (SELECT bot_id FROM bot_shares WHERE shared_with=?))', (bot_name, u_id, u_id))
        r = c.fetchone()
        conn.close()
        if r:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('SELECT log_text, created_at FROM bot_logs WHERE bot_id=? ORDER BY created_at DESC LIMIT 30', (r[0],))
            logs = c.fetchall()
            conn.close()
            if logs:
                l_txt = f"<tg-emoji emoji-id=\"6206343625232619150\">📊</tg-emoji> {bot_name} LOGLARI\n\n"
                for log, date in logs[:20]:
                    time_str = date[11:19] if date else "??"
                    l_txt += f"🕒 {time_str}\n📝 {log[:100]}\n\n"
                bot.send_message(u_id, l_txt[:4000], reply_markup=main_keyboard(u_id))
            else:
                bot.send_message(u_id, f"<tg-emoji emoji-id=\"6206343625232619150\">📊</tg-emoji> {bot_name} için log yok.", reply_markup=main_keyboard(u_id))
        else:
            bot.send_message(u_id, "<tg-emoji emoji-id=\"6221914376329237010\">⚠️</tg-emoji> Bot bulunamadı!", reply_markup=main_keyboard(u_id))
        return
    
    # Paylaşma
    if txt.startswith("<tg-emoji emoji-id=\"5841191265277841038\">❤</tg-emoji> "):
        bot_name = txt.split(" ", 1)[1]
        user_sessions[u_id] = {'action': 'share', 'bot_name': bot_name}
        bot.send_message(u_id, "<tg-emoji emoji-id=\"5841191265277841038\">❤</tg-emoji> Paylaşmak istediğin kullanıcının ID'sini gönder:\n\nÖrnek: 123456789\n\n@userinfobot ile ID öğrenebilirsin.", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🏠 ANA MENÜ"))
        return

# ================================
# DOSYA YÜKLEME
# ================================
@bot.message_handler(content_types=['document'])
def handle_doc(message):
    u_id = message.from_user.id
    if u_id not in verified_users and u_id not in admin_ids:
        bot.reply_to(message, "<tg-emoji emoji-id=\"6221914376329237010\">⚠️</tg-emoji> Önce /start yap!")
        return

    banned, ban_reason = is_user_security_banned(u_id)
    if banned and u_id not in admin_ids:
        bot.reply_to(message, f"🚫 Hesabın banlı, dosya yükleyemezsin!\n📋 Sebep: {ban_reason or 'Belirtilmemiş'}")
        return
    
    limit = get_user_bot_limit(u_id)
    own, _ = get_my_bots(u_id)
    if len(own) >= limit:
        bot.reply_to(message, f"<tg-emoji emoji-id=\"6221914376329237010\">⚠️</tg-emoji> Bot limitin doldu! ({limit}/{limit})\n<tg-emoji emoji-id=\"6125115309650089324\">👑</tg-emoji> Premium için {ADMIN_USERNAME}")
        return
    
    doc = message.document
    f_name = doc.file_name
    ext = os.path.splitext(f_name)[1].lower()
    if ext not in ['.py', '.js', '.zip']:
        bot.reply_to(message, "<tg-emoji emoji-id=\"6221914376329237010\">⚠️</tg-emoji> Sadece .py, .js, .zip kabul edilir!")
        return
    if doc.file_size > 20 * 1024 * 1024:
        bot.reply_to(message, "<tg-emoji emoji-id=\"6221914376329237010\">⚠️</tg-emoji> Max 20MB!")
        return
    
    msg = bot.reply_to(message, f"<tg-emoji emoji-id=\"6030823232561485465\">🖼️</tg-emoji> {f_name} yükleniyor...")
    try:
        file_info = bot.get_file(doc.file_id)
        downloaded = bot.download_file(file_info.file_path)
        folder = get_user_folder(u_id)
        
        if ext == '.zip':
            temp = tempfile.mkdtemp(dir=TEMP_DIR)
            zip_path = os.path.join(temp, f_name)
            with open(zip_path, 'wb') as f:
                f.write(downloaded)
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(temp)
            files = os.listdir(temp)
            main_f = None
            b_type = None
            for name in ['main.py', 'bot.py', 'app.py', 'index.py', 'run.py']:
                if name in files:
                    main_f = name
                    b_type = 'py'
                    break
            if not main_f:
                for name in ['index.js', 'main.js', 'bot.js', 'app.js']:
                    if name in files:
                        main_f = name
                        b_type = 'js'
                        break
            if not main_f:
                py_f = [f for f in files if f.endswith('.py')]
                js_f = [f for f in files if f.endswith('.js')]
                if py_f:
                    main_f = py_f[0]
                    b_type = 'py'
                elif js_f:
                    main_f = js_f[0]
                    b_type = 'js'
            if main_f:
                # GÜVENLİK TARAMASI: ZIP içeriğini kullanıcı klasörüne taşımadan önce tara
                violations = scan_path_for_violations(temp)
                if violations:
                    security_auto_ban(u_id, violations, f"ZIP: {f_name}", cleanup_paths=[temp])
                    bot.edit_message_text(
                        "🚫 Yasaklı modül/import tespit edildi! Hesabın otomatik banlandı.",
                        msg.chat.id, msg.message_id
                    )
                    return
                for item in os.listdir(temp):
                    src = os.path.join(temp, item)
                    dst = os.path.join(folder, item)
                    if os.path.exists(dst):
                        if os.path.isdir(dst):
                            shutil.rmtree(dst)
                        else:
                            os.remove(dst)
                    shutil.move(src, dst)
                f_name = main_f
            else:
                bot.edit_message_text("<tg-emoji emoji-id=\"6221914376329237010\">⚠️</tg-emoji> ZIP içinde bot bulunamadı!", msg.chat.id, msg.message_id)
                shutil.rmtree(temp)
                return
            shutil.rmtree(temp)
        else:
            target_path = os.path.join(folder, f_name)
            with open(target_path, 'wb') as f:
                f.write(downloaded)
            b_type = 'py' if ext == '.py' else 'js'

            # GÜVENLİK TARAMASI: dosyayı bot listesine eklemeden önce tara
            violations = scan_path_for_violations(target_path)
            if violations:
                security_auto_ban(u_id, violations, f"Dosya: {f_name}", cleanup_paths=[target_path])
                bot.edit_message_text(
                    "🚫 Yasaklı modül/import tespit edildi! Hesabın otomatik banlandı.",
                    msg.chat.id, msg.message_id
                )
                return
        
        bot_name = os.path.splitext(f_name)[0][:30]
        bot_id = gen_bot_id()
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('INSERT INTO bots (bot_id, user_id, bot_name, file_name, bot_type, status) VALUES (?, ?, ?, ?, ?, "pending")',
                  (bot_id, u_id, bot_name, f_name, b_type))
        c.execute('UPDATE users SET total_bots = total_bots + 1 WHERE user_id = ?', (u_id,))
        conn.commit()
        conn.close()
        
        file_id = f"{u_id}_{f_name}_{int(time.time())}"
        pending_approvals[file_id] = {'user_id': u_id, 'user_name': message.from_user.first_name, 'file_name': f_name, 'bot_name': bot_name, 'bot_id': bot_id, 'bot_type': b_type}
        
        for aid in admin_ids:
            try:
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(types.InlineKeyboardButton("✅ ONAYLA", callback_data=f"approve_{file_id}"),
                           types.InlineKeyboardButton("❌ REDDET", callback_data=f"reject_{file_id}"))
                bot.send_message(aid, f"📤 YENİ BOT!\n👤 {message.from_user.first_name}\n📄 {f_name}\n🎯 {b_type.upper()}", reply_markup=keyboard)
            except:
                pass
        
        bot.edit_message_text(f"<tg-emoji emoji-id=\"5332647664049739927\">✅</tg-emoji> {f_name} yüklendi!\n<tg-emoji emoji-id=\"4987817392827532337\">⏳</tg-emoji> Admin onayı bekleniyor...", msg.chat.id, msg.message_id)
        
    except Exception as e:
        bot.edit_message_text(f"❌ Hata: {str(e)[:100]}", msg.chat.id, msg.message_id)

# ================================
# STATE MESAJLARI
# ================================
@bot.message_handler(func=lambda m: m.from_user.id in user_sessions and not user_sessions[m.from_user.id].get('action', '').startswith('admin_'))
def handle_state(m):
    u_id = m.from_user.id
    sess = user_sessions.get(u_id, {})
    action = sess.get('action')
    
    if action == 'share':
        bot_name = sess.get('bot_name')
        try:
            target = int(m.text.strip())
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('SELECT bot_id FROM bots WHERE user_id=? AND bot_name=?', (u_id, bot_name))
            r = c.fetchone()
            if r:
                share_bot(r[0], target)
                try:
                    bot.send_message(target, f"<tg-emoji emoji-id=\"5240416505543281380\">🤝</tg-emoji> BİR BOT SENİNLE PAYLAŞILDI!\n\n🤖 {bot_name}\n👤 Paylaşan: {m.from_user.first_name}\n✅ Botunu BOTLARIM menüsünden başlatabilirsin!")
                except:
                    pass
                bot.send_message(u_id, f"<tg-emoji emoji-id=\"5332647664049739927\">✅</tg-emoji> {bot_name} paylaşıldı!", reply_markup=main_keyboard(u_id))
            else:
                bot.send_message(u_id, "<tg-emoji emoji-id=\"6221914376329237010\">⚠️</tg-emoji> Bot bulunamadı!", reply_markup=main_keyboard(u_id))
        except:
            bot.send_message(u_id, "<tg-emoji emoji-id=\"6221914376329237010\">⚠️</tg-emoji>Geçersiz ID!", reply_markup=main_keyboard(u_id))
        del user_sessions[u_id]

# ================================
# TICKET VE PREMİUM KOMUTLARI
# ================================
@bot.message_handler(commands=['ticket'])
def ticket_cmd(m):
    u_id = m.from_user.id
    if u_id not in verified_users and u_id not in admin_ids:
        cmd_start(m)
        return
    subject = m.text.replace('/ticket', '').strip()
    if not subject:
        bot.reply_to(m, "<tg-emoji emoji-id=\"6221914376329237010\">⚠️</tg-emoji> Kullanım: /ticket <konu>\nÖrnek: /ticket Botum çalışmıyor")
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO tickets (user_id, subject, message) VALUES (?, ?, ?)', (u_id, subject, "Detay bekleniyor"))
    ticket_id = c.lastrowid
    conn.commit()
    conn.close()
    bot.reply_to(m, f"<tg-emoji emoji-id=\"5332647664049739927\">✅</tg-emoji> Ticket #{ticket_id} oluşturuldu! En kısa sürede cevaplanacaktır.")
    for aid in admin_ids:
        try:
            bot.send_message(aid, f"<tg-emoji emoji-id=\"6221914376329237010\">⚠️</tg-emoji> YENİ TICKET #{ticket_id}\n👤 {m.from_user.first_name}\n📝 {subject}")
        except:
            pass

@bot.message_handler(commands=['premium'])
def premium_cmd(m):
    u_id = m.from_user.id
    if u_id not in verified_users and u_id not in admin_ids:
        cmd_start(m)
        return
    plan = m.text.replace('/premium', '').strip().lower()
    if plan not in ['bronze', 'silver', 'gold', 'diamond']:
        bot.reply_to(m, "<tg-emoji emoji-id=\"6221914376329237010\">⚠️</tg-emoji> Kullanım: /premium <plan>\nPlanlar: bronze, silver, gold, diamond\nÖrnek: /premium gold")
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO premium_requests (user_id, plan) VALUES (?, ?)', (u_id, plan))
    req_id = c.lastrowid
    conn.commit()
    conn.close()
    bot.reply_to(m, f"<tg-emoji emoji-id=\"5332647664049739927\">✅</tg-emoji> Premium talebi oluşturuldu! Admin en kısa sürede sizinle iletişime geçecek.")
    for aid in admin_ids:
        try:
            bot.send_message(aid, f"💎 PREMİUM TALEBİ #{req_id}\n👤 {m.from_user.first_name}\n📊 Plan: {plan.upper()}")
        except:
            pass

# ================================
# CALLBACK HANDLER (TÜM ADMIN İŞLEMLERİ)
# ================================
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    u_id = call.from_user.id
    data = call.data

    if u_id not in admin_ids:
        banned, ban_reason = is_user_security_banned(u_id)
        if banned:
            bot.answer_callback_query(call.id, f"🚫 Hesabın banlı! Sebep: {ban_reason or 'Belirtilmemiş'}", True)
            return
    
    # ONAYLA
    if data.startswith("approve_"):
        if u_id not in admin_ids:
            bot.answer_callback_query(call.id, "<tg-emoji emoji-id=\"6221914376329237010\">⚠️</tg-emoji> Yetkin yok!", True)
            return
        fid = data.replace("approve_", "")
        if fid in pending_approvals:
            info = pending_approvals[fid]
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('UPDATE bots SET status="stopped" WHERE bot_id=?', (info['bot_id'],))
            conn.commit()
            conn.close()
            try:
                bot.send_message(info['user_id'], f"<tg-emoji emoji-id=\"5332647664049739927\">✅</tg-emoji> BOTUN ONAYLANDI!\n\n📄 {info['file_name']}\n<tg-emoji emoji-id=\"5332647664049739927\">✅</tg-emoji> Artık başlatabilirsin!")
            except:
                pass
            bot.edit_message_text(f"✅ ONAYLANDI: {info['file_name']}", call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id, "✅ Onaylandı!")
            log_admin(u_id, 'approve_bot', str(info['user_id']), info['file_name'])
            del pending_approvals[fid]
        return
    
    # REDDET
    if data.startswith("reject_"):
        if u_id not in admin_ids:
            bot.answer_callback_query(call.id, "<tg-emoji emoji-id=\"6221914376329237010\">⚠️</tg-emoji> Yetkin yok!", True)
            return
        fid = data.replace("reject_", "")
        if fid in pending_approvals:
            info = pending_approvals[fid]
            folder = get_user_folder(info['user_id'])
            fp = os.path.join(folder, info['file_name'])
            if os.path.exists(fp):
                os.remove(fp)
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('DELETE FROM bots WHERE bot_id=?', (info['bot_id'],))
            conn.commit()
            conn.close()
            try:
                bot.send_message(info['user_id'], f"<tg-emoji emoji-id=\"6221914376329237010\">⚠️</tg-emoji> BOTUN REDDEDİLDİ!\n\n📄 {info['file_name']}")
            except:
                pass
            bot.edit_message_text(f"<tg-emoji emoji-id=\"6221914376329237010\">⚠️</tg-emoji> REDDEDİLDİ: {info['file_name']}", call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id, "<tg-emoji emoji-id=\"6221914376329237010\">⚠️</tg-emoji> Reddedildi!")
            log_admin(u_id, 'reject_bot', str(info['user_id']), info['file_name'])
            del pending_approvals[fid]
        return
    


    # ANA MENÜ INLINE
    if data == "menu_bots":
        own, shared = get_my_bots(u_id)

        if not own and not shared:
            bot.answer_callback_query(call.id, "Botun yok!", show_alert=True)
            return

        for b in own:
            try:
                emoji = "<tg-emoji emoji-id=\"4990298741463319592\">🟢</tg-emoji>" if b[2] == "running" else "<tg-emoji emoji-id=\"4990182601252668309\">🔴</tg-emoji>"
                bot.send_message(
                    u_id,
                    f"{emoji} <b>{b[1]}</b>\n<tg-emoji emoji-id=\"6206027872121918710\">🎁</tg-emoji> Tür: {b[3].upper()}\n<tg-emoji emoji-id=\"6206343625232619150\">📊</tg-emoji> Durum: {b[2]}",
                    reply_markup=quick_bot_keyboard(b[1])
                )
            except:
                pass

        bot.answer_callback_query(call.id)
        return

    if data == "menu_upload":
        bot.send_message(
            u_id,
            "<tg-emoji emoji-id=\"6206343625232619150\">📊</tg-emoji> Bot yüklemek için .py / .js / .zip dosyanı gönder."
        )
        bot.answer_callback_query(call.id)
        return

    if data == "menu_start":
        bot.send_message(u_id, "<tg-emoji emoji-id=\"5240317124295020104\">👍</tg-emoji> Başlatmak için BOTLARIM bölümünden bot seç.")
        bot.answer_callback_query(call.id)
        return

    if data == "menu_stop":
        bot.send_message(u_id, "<tg-emoji emoji-id=\"5217824874487101321\">😍</tg-emoji> Durdurmak için BOTLARIM bölümünden bot seç.")
        bot.answer_callback_query(call.id)
        return

    if data == "menu_restart":
        bot.send_message(u_id, "<tg-emoji emoji-id=\"5217824874487101321\">😍</tg-emoji> Yeniden başlatmak için BOTLARIM bölümünden bot seç.")
        bot.answer_callback_query(call.id)
        return

    if data == "menu_delete":
        bot.send_message(u_id, "<tg-emoji emoji-id=\"5217824874487101321\">😍</tg-emoji> Silmek için BOTLARIM bölümünden bot seç.")
        bot.answer_callback_query(call.id)
        return

    if data == "menu_logs":
        bot.send_message(u_id, "<tg-emoji emoji-id=\"5217824874487101321\">😍</tg-emoji> Log görmek için BOTLARIM bölümünden bot seç.")
        bot.answer_callback_query(call.id)
        return

    if data == "menu_share":
        bot.send_message(u_id, "<tg-emoji emoji-id=\"5217824874487101321\">😍</tg-emoji> Paylaşmak için BOTLARIM bölümünden bot seç.")
        bot.answer_callback_query(call.id)
        return

    if data == "menu_premium":
        bot.send_message(
            u_id,
            "💎 Premium Planlar\n\n<tg-emoji emoji-id=\"6125115309650089324\">👑</tg-emoji> Bronze\n<tg-emoji emoji-id=\"6125115309650089324\">👑</tg-emoji> Silver\n<tg-emoji emoji-id=\"6125115309650089324\">👑</tg-emoji> Gold\n<tg-emoji emoji-id=\"6125115309650089324\">👑</tg-emoji> Diamond"
        )
        bot.answer_callback_query(call.id)
        return

    if data == "menu_stats":
        bot.send_message(
            u_id,
            f"<tg-emoji emoji-id=\"6206343625232619150\">📊</tg-emoji> Stats\n\n<tg-emoji emoji-id=\"4969794872534893204\">🫥</tg-emoji> Kullanıcı: {len(verified_users)}\n<tg-emoji emoji-id=\"6219817246877816475\">😄</tg-emoji> Çalışan Bot: {len(bot_processes)}"
        )
        bot.answer_callback_query(call.id)
        return

    if data == "menu_support":
        bot.send_message(
            u_id,
            "<tg-emoji emoji-id=\"6269426709011895930\">👩‍💻</tg-emoji> Destek için /ticket kullan."
        )
        bot.answer_callback_query(call.id)
        return

    if data == "menu_settings":
        bot.send_message(
            u_id,
            "<tg-emoji emoji-id=\"5242581542722617083\">👌</tg-emoji> Ayarlar\n\n<tg-emoji emoji-id=\"6251345820113707698\">🎁</tg-emoji> Max Dosya: 20MB\n<tg-emoji emoji-id=\"6327678689022579783\">😄</tg-emoji> Desteklenen: .py .js .zip"
        )
        bot.answer_callback_query(call.id)
        return

    if data == "menu_admin":
        if u_id in admin_ids:
            bot.send_message(u_id, "👑 Admin Panel", reply_markup=admin_panel_keyboard())
        bot.answer_callback_query(call.id)
        return

    if data == "menu_refresh":
        show_main_menu(call.message)
        bot.answer_callback_query(call.id, "🔄 Menü yenilendi!")
        return

    # HIZLI BOT İŞLEMLERİ
    if data.startswith("quick_start_"):
        bot_name = data.replace("quick_start_", "")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT bot_id, user_id, file_name, bot_type FROM bots WHERE user_id=? AND bot_name=?', (u_id, bot_name))
        r = c.fetchone()
        conn.close()
        
        if r:
            start_bot_process(r[0], r[1], bot_name, r[2], r[3])
            bot.answer_callback_query(call.id, "Bot başlatılıyor!")
        else:
            bot.answer_callback_query(call.id, "Bot bulunamadı!", show_alert=True)
        return

    if data.startswith("quick_stop_"):
        bot_name = data.replace("quick_stop_", "")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT bot_id FROM bots WHERE user_id=? AND bot_name=?', (u_id, bot_name))
        r = c.fetchone()
        conn.close()
        
        if r and stop_bot_process(r[0]):
            bot.answer_callback_query(call.id, "Bot durduruldu!")
        else:
            bot.answer_callback_query(call.id, "İşlem başarısız!", show_alert=True)
        return

    if data.startswith("quick_restart_"):
        bot_name = data.replace("quick_restart_", "")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT bot_id FROM bots WHERE user_id=? AND bot_name=?', (u_id, bot_name))
        r = c.fetchone()
        conn.close()
        
        if r:
            restart_bot_process(r[0])
            bot.answer_callback_query(call.id, "Bot yeniden başlatılıyor!")
        else:
            bot.answer_callback_query(call.id, "Bot bulunamadı!", show_alert=True)
        return

    if data.startswith("quick_delete_"):
        bot_name = data.replace("quick_delete_", "")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT bot_id FROM bots WHERE user_id=? AND bot_name=?', (u_id, bot_name))
        r = c.fetchone()
        conn.close()
        
        if r:
            delete_bot(r[0], u_id)
            bot.answer_callback_query(call.id, "<tg-emoji emoji-id=\"4958534924278694938\">🗑</tg-emoji> Bot silindi!")
        else:
            bot.answer_callback_query(call.id, "<tg-emoji emoji-id=\"6224185666704511761\">❌</tg-emoji> Bot bulunamadı!", show_alert=True)
        return

    if data.startswith("quick_logs_"):
        bot_name = data.replace("quick_logs_", "")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT bot_id FROM bots WHERE user_id=? AND bot_name=?', (u_id, bot_name))
        r = c.fetchone()
        
        if r:
            c.execute('SELECT log_text FROM bot_logs WHERE bot_id=? ORDER BY created_at DESC LIMIT 15', (r[0],))
            logs = c.fetchall()
            conn.close()
            
            if logs:
                text = f"<tg-emoji emoji-id=\"5217824874487101321\">😍</tg-emoji> {bot_name} LOG\n\n"
                for lg in logs:
                    text += f"📝 {lg[0][:120]}\n"
                bot.send_message(u_id, text[:4000])
            else:
                bot.send_message(u_id, "<tg-emoji emoji-id=\"6224185666704511761\">❌</tg-emoji> Log bulunamadı.")
        else:
            conn.close()
            bot.send_message(u_id, "<tg-emoji emoji-id=\"6224185666704511761\">❌</tg-emoji> Bot bulunamadı.")
        
        bot.answer_callback_query(call.id)
        return

    if data.startswith("delch_"):
        if u_id not in admin_ids:
            bot.answer_callback_query(call.id, "⚠️ Yetkin yok!", True)
            return
        try:
            ch_id = int(data.replace("delch_", ""))
        except ValueError:
            bot.answer_callback_query(call.id, "❌ Geçersiz kanal!", True)
            return
        ch = next((c for c in REQUIRED_CHANNELS if c['id'] == ch_id), None)
        deleted = delete_required_channel(ch_id)
        if deleted:
            bot.edit_message_text(f"✅ Kanal silindi: {ch['name'] if ch else ch_id}", call.message.chat.id, call.message.message_id)
            log_admin(u_id, 'delete_required_channel', str(ch_id), ch['name'] if ch else '')
        else:
            bot.edit_message_text("❌ Kanal bulunamadı!", call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
        return

    # ADMIN PANEL İŞLEMLERİ
    if data.startswith("admin_") and u_id not in admin_ids:
        bot.answer_callback_query(call.id, "⚠️ Yetkin yok!", True)
        return

    if data == "admin_users":
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT user_id, first_name, username, join_date, total_bots FROM users ORDER BY join_date DESC LIMIT 30')
        users = c.fetchall()
        conn.close()
        txt = "👥 KULLANICILAR (Son 30)\n\n"
        for u in users:
            txt += f"🆔 {u[0]} | {u[1] or 'İsimsiz'} | @{u[2] or 'yok'} | {u[4]} bot | 📅 {u[3][:10]}\n"
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
    
    elif data == "admin_search_user":
        bot.edit_message_text("🔍 Kullanıcı ID'sini gönder:", call.message.chat.id, call.message.message_id)
        user_sessions[u_id] = {'action': 'admin_search'}
        bot.answer_callback_query(call.id)
    
    elif data == "admin_add_user":
        bot.edit_message_text("➕ Kullanıcı ID'sini gönder:", call.message.chat.id, call.message.message_id)
        user_sessions[u_id] = {'action': 'admin_add_user'}
        bot.answer_callback_query(call.id)
    
    elif data == "admin_bots":
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT bot_id, user_id, bot_name, status, bot_type FROM bots ORDER BY start_time DESC LIMIT 50')
        bots = c.fetchall()
        conn.close()
        txt = "🤖 TÜM BOTLAR (Son 50)\n\n"
        for b in bots:
            emoji = "🟢" if b[3] == "running" else "🔴" if b[3] == "stopped" else "⏳"
            txt += f"{emoji} {b[2]} [{b[4].upper()}] | 👤 {b[1]}\n"
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
    
    elif data == "admin_pending":
        if not pending_approvals:
            bot.edit_message_text("✅ Bekleyen onay yok!", call.message.chat.id, call.message.message_id)
        else:
            txt = f"⏳ BEKLEYEN ONAYLAR ({len(pending_approvals)})\n\n"
            for fid, info in list(pending_approvals.items()):
                txt += f"📄 {info['file_name']} | 👤 {info['user_name']} | 🆔 {info['user_id']}\n"
            bot.edit_message_text(txt, call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
    
    elif data == "admin_running":
        txt = f"🟢 ÇALIŞAN BOTLAR ({len(bot_processes)})\n\n"
        for bid, info in bot_processes.items():
            txt += f"🤖 {info.get('bot_name', bid)} | 👤 {info.get('user_id', '?')}\n"
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
    
    elif data == "admin_stopped":
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT bot_name, user_id FROM bots WHERE status="stopped"')
        bots = c.fetchall()
        conn.close()
        txt = f"🔴 DURAN BOTLAR ({len(bots)})\n\n"
        for b in bots:
            txt += f"🤖 {b[0]} | 👤 {b[1]}\n"
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
    
    elif data == "admin_premium":
        bot.edit_message_text("💎 Premium vermek istediğin kullanıcı ID'sini gönder:", call.message.chat.id, call.message.message_id)
        user_sessions[u_id] = {'action': 'admin_premium'}
        bot.answer_callback_query(call.id)
    
    elif data == "admin_premium_requests":
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, user_id, plan, status, created_at FROM premium_requests WHERE status="pending" ORDER BY created_at DESC')
        reqs = c.fetchall()
        conn.close()
        if not reqs:
            bot.edit_message_text("✅ Bekleyen premium talebi yok!", call.message.chat.id, call.message.message_id)
        else:
            txt = "💎 PREMİUM TALEPLERİ\n\n"
            for r in reqs:
                txt += f"📌 #{r[0]} | 👤 {r[1]} | {r[2]} | 📅 {r[4][:10]}\n"
            bot.edit_message_text(txt, call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
    
    elif data == "admin_ban":
        bot.edit_message_text("🚫 Banlamak istediğin kullanıcı ID'sini ve sebebini gönder:\nÖrnek: 123456789 Spam", call.message.chat.id, call.message.message_id)
        user_sessions[u_id] = {'action': 'admin_ban'}
        bot.answer_callback_query(call.id)
    
    elif data == "admin_unban":
        bot.edit_message_text("✅ Banını kaldırmak istediğin kullanıcı ID'sini gönder:", call.message.chat.id, call.message.message_id)
        user_sessions[u_id] = {'action': 'admin_unban'}
        bot.answer_callback_query(call.id)
    
    elif data == "admin_blacklist":
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT user_id, reason, banned_at FROM blacklist ORDER BY banned_at DESC')
        bans = c.fetchall()
        conn.close()
        if not bans:
            txt = "✅ BLACKLIST BOŞ"
        else:
            txt = "🚫 BLACKLIST\n\n"
            for b in bans:
                txt += f"🆔 {b[0]} | {b[1]} | 📅 {b[2][:10]}\n"
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
    
    elif data == "admin_stats":
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM users')
        total_u = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM bots')
        total_b = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM bots WHERE status="running"')
        running = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM bots WHERE status="pending"')
        pending = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM bot_shares')
        shares = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM tickets WHERE status="open"')
        tickets = c.fetchone()[0]
        conn.close()
        txt = f"📊 GENEL STATS\n\n👥 Kullanıcı: {total_u}\n🤖 Toplam Bot: {total_b}\n🟢 Çalışan: {running}\n⏳ Bekleyen: {pending}\n🤝 Paylaşım: {shares}\n🎫 Açık Ticket: {tickets}\n🚀 Process: {len(bot_processes)}"
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
    
    elif data == "admin_daily_stats":
        today = datetime.now().strftime('%Y-%m-%d')
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM users WHERE DATE(join_date)=?', (today,))
        new_u = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM bots WHERE DATE(start_time)=?', (today,))
        new_b = c.fetchone()[0]
        conn.close()
        txt = f"📈 GÜNLÜK STATS ({today})\n\n• Yeni Kullanıcı: {new_u}\n• Yeni Bot: {new_b}\n• Çalışan Bot: {len(bot_processes)}"
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
    
    elif data == "admin_tickets":
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, user_id, subject, status, created_at FROM tickets ORDER BY created_at DESC LIMIT 30')
        tickets = c.fetchall()
        conn.close()
        if not tickets:
            txt = "🎫 TICKET YOK"
        else:
            txt = "🎫 TÜM TICKETLER\n\n"
            for t in tickets:
                emoji = "🟢" if t[3] == "open" else "🔴"
                txt += f"{emoji} #{t[0]} | 👤 {t[1]} | {t[2][:30]} | {t[4][:10]}\n"
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
    
    elif data == "admin_open_tickets":
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, user_id, subject, created_at FROM tickets WHERE status="open" ORDER BY created_at DESC')
        tickets = c.fetchall()
        conn.close()
        if not tickets:
            txt = "✅ AÇIK TICKET YOK"
        else:
            txt = f"🆕 AÇIK TICKETLER ({len(tickets)})\n\n"
            for t in tickets:
                txt += f"#{t[0]} | 👤 {t[1]} | {t[2][:30]} | {t[3][:10]}\n"
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
    
    elif data == "admin_announce":
        bot.edit_message_text("📢 Duyuru mesajını gönder:", call.message.chat.id, call.message.message_id)
        user_sessions[u_id] = {'action': 'admin_announce'}
        bot.answer_callback_query(call.id)
    
    elif data == "admin_system":
        import psutil
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        txt = f"🖥️ SİSTEM DURUMU\n\n💻 CPU: %{cpu}\n🧠 RAM: %{ram}\n💾 Disk: %{disk}\n🚀 Process: {len(bot_processes)}"
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
    
    elif data == "admin_logs":
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT admin_id, action, target, created_at FROM admin_logs ORDER BY created_at DESC LIMIT 30')
        logs = c.fetchall()
        conn.close()
        txt = "📝 ADMIN LOGLARI (Son 30)\n\n"
        for l in logs:
            txt += f"👤 {l[0]} | {l[1]} | {l[2]} | {l[3][:10]}\n"
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
    
    elif data == "admin_start_all":
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT bot_id, user_id, bot_name, file_name, bot_type FROM bots WHERE status="stopped"')
        bots = c.fetchall()
        conn.close()
        count = 0
        for b in bots:
            start_bot_process(b[0], b[1], b[2], b[3], b[4])
            count += 1
            time.sleep(0.3)
        bot.edit_message_text(f"🚀 {count} bot başlatıldı!", call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
        log_admin(u_id, 'start_all_bots', 'all', f"{count} bot")
    
    elif data == "admin_stop_all":
        count = len(bot_processes)
        for bid in list(bot_processes.keys()):
            stop_bot_process(bid)
        bot.edit_message_text(f"⏸️ {count} bot durduruldu!", call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
        log_admin(u_id, 'stop_all_bots', 'all', f"{count} bot")
    
    elif data == "admin_clean":
        dead = []
        for bid in list(bot_processes.keys()):
            try:
                if bot_processes[bid]['process'].poll() is not None:
                    dead.append(bid)
            except:
                dead.append(bid)
        for bid in dead:
            if bid in bot_processes:
                del bot_processes[bid]
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('UPDATE bots SET status="stopped" WHERE bot_id=?', (bid,))
            conn.commit()
            conn.close()
        bot.edit_message_text(f"🧹 {len(dead)} ölü process temizlendi!", call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
    
    elif data == "admin_backup":
        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        backup_path = os.path.join(BACKUP_DIR, backup_name)
        try:
            shutil.copy2(DB_PATH, backup_path)
            size = os.path.getsize(backup_path)
            bot.edit_message_text(f"💾 Yedek alındı: {backup_name} ({size//1024} KB)", call.message.chat.id, call.message.message_id)
            log_admin(u_id, 'backup', backup_name, f"{size//1024} KB")
        except Exception as e:
            bot.edit_message_text(f"❌ Yedek hatası: {e}", call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
    
    elif data == "admin_settings":
        txt = f"⚙️ AYARLAR\n\n📌 Bot Limiti: {get_user_bot_limit(OWNER_ID)}\n📦 Max Dosya: 20MB\n🎯 Desteklenen: .py .js .zip\n👑 Owner: {OWNER_ID}\n🔧 Admin: {ADMIN_ID}"
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
    
    elif data == "admin_help":
        txt = "❓ ADMIN YARDIM\n\n👥 KULLANICILAR - Liste/Ara/Ekle\n🤖 BOTLAR - Tüm/Çalışan/Duran/Bekleyen\n💎 PREMİUM - Ver/Talepler\n🚫 BAN - Banla/Unban/Blacklist\n📊 STATS - Genel/Günlük\n🎫 TICKET - Tüm/Açık\n📢 DUYURU - Gönder\n🖥️ SİSTEM - Durum/Loglar\n⚡ TOPLU - Başlat/Durdur/Temizle\n💾 YEDEK - Al\n👑 İletişim: @BerkeX4L"
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
    
    elif data == "admin_add_channel":
        bot.edit_message_text(
            "➕ ZORUNLU KANAL EKLE\n\nŞu formatta gönder:\nİsim | https://t.me/kanal | Emoji(opsiyonel)\n\nÖrnek:\nX4L Duyuru | https://t.me/x4lduyuru | 📢",
            call.message.chat.id, call.message.message_id
        )
        user_sessions[u_id] = {'action': 'admin_add_channel'}
        bot.answer_callback_query(call.id)

    elif data == "admin_del_channel":
        if not REQUIRED_CHANNELS:
            bot.edit_message_text("📭 Kayıtlı zorunlu kanal yok.", call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id)
        else:
            k = types.InlineKeyboardMarkup(row_width=1)
            for ch in REQUIRED_CHANNELS:
                k.add(types.InlineKeyboardButton(f"🗑️ {ch['emoji']} {ch['name']}", callback_data=f"delch_{ch['id']}"))
            k.add(types.InlineKeyboardButton("🔙 GERİ", callback_data="menu_admin", style="success"))
            bot.edit_message_text("🗑️ Silmek istediğin kanalı seç:", call.message.chat.id, call.message.message_id, reply_markup=k)
            bot.answer_callback_query(call.id)

    elif data == "admin_del_all_channels":
        if not REQUIRED_CHANNELS:
            bot.edit_message_text("📭 Kayıtlı zorunlu kanal yok.", call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id)
        else:
            k = types.InlineKeyboardMarkup(row_width=2)
            k.add(
                types.InlineKeyboardButton("✅ EVET, HEPSİNİ SİL", callback_data="admin_del_all_channels_confirm", style="primary"),
                types.InlineKeyboardButton("❌ VAZGEÇ", callback_data="menu_admin")
            )
            bot.edit_message_text(
                f"⚠️ {len(REQUIRED_CHANNELS)} zorunlu kanalın TAMAMINI silmek üzeresin. Emin misin?",
                call.message.chat.id, call.message.message_id, reply_markup=k
            )
            bot.answer_callback_query(call.id)

    elif data == "admin_del_all_channels_confirm":
        count = len(REQUIRED_CHANNELS)
        delete_all_required_channels()
        bot.edit_message_text(f"✅ {count} zorunlu kanalın tamamı silindi!", call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
        log_admin(u_id, 'delete_all_required_channels', 'all', f"{count} kanal")

    elif data == "admin_to_user":
        bot.edit_message_text("✅ Kullanıcı paneline yönlendiriliyorsunuz...", call.message.chat.id, call.message.message_id)
        show_main_menu(call.message)
        bot.answer_callback_query(call.id)

    elif data == "admin_button_custom":
        bot.edit_message_text(
            "🎨 BUTON ÖZELLEŞTİR\n\nAna menüdeki hangi butonu değiştirmek istersin?\n\n"
            "ℹ️ Not: Telegram'ın Bot API'si buton rengini değiştirmeye izin vermiyor "
            "(inline butonlar hep aynı gri Telegram teması ile gösterilir) ve buton "
            "yazısının içine premium/özel emoji koymayı desteklemiyor — bu platform "
            "kısıtı, kodda düzeltilebilecek bir şey değil. Değiştirebildiğimiz: buton "
            "üzerindeki normal emoji ve yazı.",
            call.message.chat.id, call.message.message_id, reply_markup=button_custom_keyboard()
        )
        bot.answer_callback_query(call.id)

    elif data == "btncfg_reset_all":
        for key in CUSTOMIZABLE_BUTTONS:
            reset_button_cfg(key)
        bot.edit_message_text("♻️ Tüm butonlar varsayılana döndürüldü.", call.message.chat.id, call.message.message_id,
                               reply_markup=button_custom_keyboard())
        bot.answer_callback_query(call.id)
        log_admin(u_id, 'reset_all_buttons', 'all', '')

    elif data.startswith("btncfg_"):
        key = data[len("btncfg_"):]
        if key not in CUSTOMIZABLE_BUTTONS:
            bot.answer_callback_query(call.id, "❌ Geçersiz buton!")
        else:
            emoji, label = get_button_cfg(key)
            k = types.InlineKeyboardMarkup(row_width=1)
            k.add(types.InlineKeyboardButton("♻️ VARSAYILANA DÖNDÜR", callback_data=f"btncfgreset_{key}", style="danger"))
            k.add(types.InlineKeyboardButton("🔙 GERİ", callback_data="admin_button_custom"))
            bot.edit_message_text(
                f"🎨 Şu an: {emoji} {label}\n\n"
                f"Yeni değeri şu formatta gönder:\nEmoji | Yazı\n\nÖrnek:\n🌟 | Botlarım",
                call.message.chat.id, call.message.message_id, reply_markup=k
            )
            user_sessions[u_id] = {'action': 'admin_button_edit', 'key': key}
            bot.answer_callback_query(call.id)

    elif data.startswith("btncfgreset_"):
        key = data[len("btncfgreset_"):]
        if key in CUSTOMIZABLE_BUTTONS:
            reset_button_cfg(key)
            log_admin(u_id, 'reset_button', key, '')
        bot.edit_message_text("✅ Buton varsayılana döndürüldü.", call.message.chat.id, call.message.message_id,
                               reply_markup=button_custom_keyboard())
        bot.answer_callback_query(call.id)

# ================================
# ADMIN STATE İŞLEMLERİ
# ================================
@bot.message_handler(func=lambda m: m.from_user.id in user_sessions and user_sessions[m.from_user.id].get('action', '').startswith('admin_'))
def handle_admin_state(m):
    u_id = m.from_user.id
    sess = user_sessions.get(u_id, {})
    action = sess.get('action')
    
    if action == 'admin_search':
        try:
            target = int(m.text.strip())
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('SELECT user_id, first_name, username, join_date, total_bots, is_banned FROM users WHERE user_id=?', (target,))
            r = c.fetchone()
            conn.close()
            if r:
                txt = f"🔍 KULLANICI BULUNDU\n\n🆔 {r[0]}\n👤 {r[1] or 'İsimsiz'}\n📝 @{r[2] or 'yok'}\n📅 {r[3][:10]}\n🤖 {r[4]} bot\n🚫 {'BANLI' if r[5] else 'AKTİF'}"
                bot.send_message(u_id, txt)
            else:
                bot.send_message(u_id, "❌ Kullanıcı bulunamadı!")
        except:
            bot.send_message(u_id, "❌ Geçersiz ID!")
        del user_sessions[u_id]
    
    elif action == 'admin_add_user':
        try:
            target = int(m.text.strip())
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (target,))
            conn.commit()
            conn.close()
            bot.send_message(u_id, f"✅ Kullanıcı eklendi: {target}")
            log_admin(u_id, 'add_user', str(target), 'Yeni kullanıcı')
        except:
            bot.send_message(u_id, "❌ Geçersiz ID!")
        del user_sessions[u_id]
    
    elif action == 'admin_premium':
        try:
            target = int(m.text.strip())
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('UPDATE users SET is_premium=1, premium_plan="gold", premium_until=? WHERE user_id=?', (datetime.now() + timedelta(days=30), target))
            conn.commit()
            conn.close()
            bot.send_message(u_id, f"✅ {target} ID'li kullanıcıya PREMİUM verildi!")
            try:
                bot.send_message(target, "🎉 TEBRİKLER! Premium üye oldunuz! Artık daha fazla bot yükleyebilirsiniz!")
            except:
                pass
            log_admin(u_id, 'give_premium', str(target), '30 gün')
        except:
            bot.send_message(u_id, "❌ Geçersiz ID!")
        del user_sessions[u_id]
    
    elif action == 'admin_ban':
        try:
            parts = m.text.split(maxsplit=1)
            target = int(parts[0])
            reason = parts[1] if len(parts) > 1 else "Kuralları ihlal"
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('INSERT OR REPLACE INTO blacklist (user_id, reason, banned_by) VALUES (?, ?, ?)', (target, reason, u_id))
            c.execute('UPDATE users SET is_banned=1, ban_reason=? WHERE user_id=?', (reason, target))
            conn.commit()
            conn.close()
            bot.send_message(u_id, f"✅ {target} ID'li kullanıcı BANLANDI!\nSebep: {reason}")
            try:
                bot.send_message(target, f"🚫 HESABINIZ BANLANDI!\nSebep: {reason}\nYetkili: {ADMIN_USERNAME}")
            except:
                pass
            log_admin(u_id, 'ban', str(target), reason)
        except:
            bot.send_message(u_id, "❌ Hatalı format! Kullanım: ID Sebep")
        del user_sessions[u_id]
    
    elif action == 'admin_unban':
        try:
            target = int(m.text.strip())
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('DELETE FROM blacklist WHERE user_id=?', (target,))
            c.execute('UPDATE users SET is_banned=0, ban_reason=NULL WHERE user_id=?', (target,))
            conn.commit()
            conn.close()
            bot.send_message(u_id, f"✅ {target} ID'li kullanıcının BANI KALDIRILDI!")
            try:
                bot.send_message(target, "✅ Hesabınızın banı kaldırıldı! Artık botu kullanabilirsiniz.")
            except:
                pass
            log_admin(u_id, 'unban', str(target), 'Ban kaldırıldı')
        except:
            bot.send_message(u_id, "❌ Geçersiz ID!")
        del user_sessions[u_id]
    
    elif action == 'admin_announce':
        msg = m.text
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT user_id FROM users')
        users = c.fetchall()
        conn.close()
        success = 0
        for (uid,) in users:
            try:
                bot.send_message(uid, f"📢 DUYURU\n\n{msg}\n\n- {ADMIN_USERNAME}")
                success += 1
                time.sleep(0.05)
            except:
                pass
        bot.send_message(u_id, f"✅ Duyuru {success} kişiye gönderildi!")
        log_admin(u_id, 'announce', 'all', f"{success} kişi")
        del user_sessions[u_id]

    elif action == 'admin_add_channel':
        try:
            parts = [p.strip() for p in m.text.split('|')]
            if len(parts) < 2 or not parts[0] or not parts[1]:
                raise ValueError("format")
            name = parts[0]
            url = parts[1]
            emoji = parts[2] if len(parts) > 2 and parts[2] else '📢'
            if not (url.startswith('https://t.me/') or url.startswith('http://t.me/') or url.startswith('@')):
                bot.send_message(u_id, "❌ URL 'https://t.me/...' ile başlamalı!")
            else:
                add_required_channel(name, url, emoji, admin_id=u_id)
                bot.send_message(u_id, f"✅ Zorunlu kanal eklendi!\n\n{emoji} {name}\n{url}")
                log_admin(u_id, 'add_required_channel', name, url)
        except Exception:
            bot.send_message(u_id, "❌ Hatalı format! Kullanım: İsim | https://t.me/kanal | Emoji(opsiyonel)")
        del user_sessions[u_id]

    elif action == 'admin_button_edit':
        key = sess.get('key')
        try:
            parts = [p.strip() for p in m.text.split('|', 1)]
            if len(parts) != 2 or not parts[0] or not parts[1]:
                raise ValueError("format")
            emoji, label = parts[0], parts[1]
            if key not in CUSTOMIZABLE_BUTTONS:
                raise ValueError("key")
            set_button_cfg(key, emoji, label, u_id)
            bot.send_message(u_id, f"✅ Buton güncellendi: {emoji} {label}", reply_markup=button_custom_keyboard())
            log_admin(u_id, 'edit_button', key, f"{emoji} {label}")
        except Exception:
            bot.send_message(u_id, "❌ Hatalı format! Kullanım: Emoji | Yazı\nÖrnek: 🌟 | Botlarım")
        del user_sessions[u_id]

# ================================
# TEMİZLİK VE BAŞLATMA
# ================================
def shutdown_cleanup():
    logger.info("🔴 Bot kapatılıyor...")
    for bid in list(bot_processes.keys()):
        try:
            bot_processes[bid]['process'].terminate()
        except:
            pass
    bot_processes.clear()
    logger.info("✅ Temizlik tamamlandı!")

atexit.register(shutdown_cleanup)

if __name__ == '__main__':
    print("=" * 70)
    print(" APOCAN BUİLDER - ULTRA PREMIUM BAŞLATILIYOR")
    print("=" * 70)
    print(f"👑 Owner ID: {OWNER_ID}")
    print(f"🔧 Admin ID: {ADMIN_ID}")
    print(f"📁 Bot Klasörü: {UPLOAD_BOTS_DIR}")
    print(f"💾 Veritabanı: {DB_PATH}")
    print("=" * 70)
    
    try:
        bot_info = bot.get_me()
        print(f"✅ Bot: @{bot_info.username}")
        print(f"🆔 Bot ID: {bot_info.id}")
    except Exception as e:
        print(f"❌ Bot bağlantı hatası: {e}")
        exit(1)
    
    print("🔄 Polling başlatılıyor...")
    print("✅ BASLADİ OE!")
    print("=" * 70)
    
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=60)
        except KeyboardInterrupt:
            print("⚠️ Bot kapatılıyor...")
            shutdown_cleanup()
            break
        except Exception as e:
            print(f"❌ Polling hatası: {e}")
            time.sleep(10)