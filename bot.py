# -*- coding: utf-8 -*-
import telebot
import subprocess
import os
import zipfile
import tempfile
import shutil
from telebot import types
import time
from datetime import datetime, timedelta
import psutil
import sqlite3
import json
import logging
import signal
import threading
import re
import sys
import atexit
import requests
import hashlib
import mimetypes
import struct

# --- Flask Keep Alive ---
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Ben Marco, Dosya Sunucusuyum."

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    print("Flask Canlı Tutma sunucusu başlatıldı.")
# --- End Flask Keep Alive ---

# --- Configuration ---
TOKEN = '8751542887:AAFmBme7Bvqbkh8lDzLx3nTniCFf8FZZfLY'
OWNER_ID = 8589066042
ADMIN_ID = 8589066042
YOUR_USERNAME = '@Sikayetsizxd'
UPDATE_CHANNEL = 'https://t.me/EmreCaner2'

# Klasör kurulumu - mutlak yollar kullanılarak
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_BOTS_DIR = os.path.join(BASE_DIR, 'upload_bots')
IROTECH_DIR = os.path.join(BASE_DIR, 'inf')
DATABASE_PATH = os.path.join(IROTECH_DIR, 'bot_data.db')

# File upload limits
FREE_USER_LIMIT = 3
SUBSCRIBED_USER_LIMIT = 10
ADMIN_LIMIT = 6
OWNER_LIMIT = float('inf')

# Gerekli dizinleri oluştur
os.makedirs(UPLOAD_BOTS_DIR, exist_ok=True)
os.makedirs(IROTECH_DIR, exist_ok=True)

# Botu başlat
bot = telebot.TeleBot(TOKEN)

# --- Veri yapıları ---
bot_scripts = {}
user_subscriptions = {}
user_files = {}
active_users = set()
admin_ids = {ADMIN_ID, OWNER_ID}
bot_locked = False

# --- Kötü Amaçlı Yazılım Algılama Yapılandırması ---
MALWARE_SIGNATURES = [
    b'MZ',  # Windows yürütülebilir dosyası
    b'\x7fELF',  # Linux çalıştırılabilir dosyası
    b'\xfe\xed\xfa',  # Mach-O ikili sistemi
    b'\xce\xfa\xed\xfe',  # Mach-O ikili (ters)
    b'PK',  # ZIP arşivi (şifrelenmiş olabilir)
    b'Rar!',  # RAR arşivi
]

ENCRYPTED_FILE_INDICATORS = [
    b'openssl',
    b'encrypted',
    b'cipher',
    b'AES',
    b'DES',
    b'RSA',
    b'GPG',
    b'PGP',
]

SUSPICIOUS_KEYWORDS = [
    b'ransomware',
    b'trojan',
    b'virus',
    b'malware',
    b'backdoor',
    b'exploit',
    b'payload',
    b'botnet',
    b'keylogger',
    b'rootkit',
]

# --- Günlük Kaydı Ayarları ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Komut Düğmesi Düzenleri (ReplyKeyboardMarkup) ---
COMMAND_BUTTONS_LAYOUT_USER_SPEC = [
    ["📢 Güncelleme Kanalı"],
    ["📤 Dosya Yükle", "📂 Dosyalarım"],
    ["⚡ Bot Hızı", "📊 İstatistikler"],
    ["📤 Komut Gönder", "📞 Sahiple İletişim"]
]
ADMIN_COMMAND_BUTTONS_LAYOUT_USER_SPEC = [
    ["📢 Güncelleme Kanalı"],
    ["📤 Dosya Yükle", "📂 Dosyalarım"],
    ["⚡ Bot Hızı", "📊 İstatistikler"],
    ["💳 Abonelikler", "📢 Duyuru"],
    ["🔒 Botu Kilitle", "🟢 Tüm Kodları Çalıştır"],
    ["📤 Komut Gönder", "👑 Yönetici Paneli"],
    ["📞 Sahiple İletişim"]
]

# --- Database Setup ---
def init_db():
    """Initialize the database with required tables"""
    logger.info(f"Veritabanı başlatılıyor: {DATABASE_PATH}")
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS subscriptions
                     (user_id INTEGER PRIMARY KEY, expiry TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS user_files
                     (user_id INTEGER, file_name TEXT, file_type TEXT,
                      PRIMARY KEY (user_id, file_name))''')
        c.execute('''CREATE TABLE IF NOT EXISTS active_users
                     (user_id INTEGER PRIMARY KEY)''')
        c.execute('''CREATE TABLE IF NOT EXISTS admins
                     (user_id INTEGER PRIMARY KEY)''')
        c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (OWNER_ID,))
        if ADMIN_ID != OWNER_ID:
            c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (ADMIN_ID,))
        conn.commit()
        conn.close()
        logger.info("Veritabanı başarıyla başlatıldı.")
    except Exception as e:
        logger.error(f"❌ Veritabanı başlatma hatası: {e}", exc_info=True)

def load_data():
    """Load data from database into memory"""
    logger.info("Veritabanından veriler yükleniyor...")
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()

        # Load subscriptions
        c.execute('SELECT user_id, expiry FROM subscriptions')
        for user_id, expiry in c.fetchall():
            try:
                user_subscriptions[user_id] = {'expiry': datetime.fromisoformat(expiry)}
            except ValueError:
                logger.warning(f"⚠️ Kullanıcı {user_id} için geçersiz bitiş tarihi formatı: {expiry}. Atlanıyor.")

        # Load user files
        c.execute('SELECT user_id, file_name, file_type FROM user_files')
        for user_id, file_name, file_type in c.fetchall():
            if user_id not in user_files:
                user_files[user_id] = []
            user_files[user_id].append((file_name, file_type))

        # Load active users
        c.execute('SELECT user_id FROM active_users')
        active_users.update(user_id for (user_id,) in c.fetchall())

        # Load admins
        c.execute('SELECT user_id FROM admins')
        admin_ids.update(user_id for (user_id,) in c.fetchall())

        conn.close()
        logger.info(f"Veriler yüklendi: {len(active_users)} kullanıcı, {len(user_subscriptions)} abonelik, {len(admin_ids)} yönetici.")
    except Exception as e:
        logger.error(f"❌ Veri yükleme hatası: {e}", exc_info=True)

# Initialize DB and Load Data at startup
init_db()
load_data()
# --- End Database Setup ---

# --- Malware Detection Functions ---
# Replace the magic import and is_suspicious_file function

def get_file_type(file_content):
    """Determine file type using magic numbers and mimetypes"""
    # Common file signatures
    signatures = {
        b'\x7fELF': 'application/x-executable',
        b'MZ': 'application/x-dosexec',
        b'\xfe\xed\xfa': 'application/x-mach-binary',
        b'\xce\xfa\xed\xfe': 'application/x-mach-binary',
        b'PK': 'application/zip',
        b'Rar!': 'application/x-rar',
    }
    
    for signature, mime_type in signatures.items():
        if file_content.startswith(signature):
            return mime_type
    
    # Fallback to extension-based detection or return unknown
    return 'application/octet-stream'

def is_suspicious_file(file_content, file_name):
    """
    Check if file contains malware signatures, encrypted content, or suspicious keywords.
    Returns (is_suspicious, reason)
    """
    file_lower = file_name.lower()
    
    # Check file extensions first (same as before)
    suspicious_extensions = ['.exe', '.dll', '.bat', '.cmd', '.scr', '.com', '.pif', '.application', '.gadget',
                            '.msi', '.msp', '.com', '.scr', '.hta', '.cpl', '.msc', '.jar', '.bin', '.deb', '.rpm',
                            '.apk', '.app', '.dmg', '.iso', '.img']
    
    if any(file_lower.endswith(ext) for ext in suspicious_extensions):
        return True, f"Şüpheli dosya uzantısı: {file_name}"
    
    # Check for malware signatures in file content
    for signature in MALWARE_SIGNATURES:
        if file_content.startswith(signature):
            return True, f"Kötü amaçlı yazılım imzası tespit edildi: {signature}"
    
    # Check for encrypted file indicators
    sample_size = min(len(file_content), 4096)
    file_sample = file_content[:sample_size]
    
    for indicator in ENCRYPTED_FILE_INDICATORS:
        if indicator in file_sample:
            return True, f"Şifrelenmiş dosya göstergesi: {indicator.decode('utf-8', errors='ignore')}"
    
    # Check for suspicious keywords in first 8KB
    sample_text = file_sample.decode('utf-8', errors='ignore').lower()
    for keyword in SUSPICIOUS_KEYWORDS:
        if keyword.decode('utf-8').lower() in sample_text:
            return True, f"Şüpheli kelime bulundu: {keyword.decode('utf-8')}"
    
    # Check file type using our custom function instead of magic
    try:
        file_type = get_file_type(file_sample)
        if file_type in ['application/x-dosexec', 'application/x-executable', 'application/x-mach-binary']:
            return True, f"Çalıştırılabilir dosya türü tespit edildi: {file_type}"
    except Exception as e:
        logger.warning(f"Dosya türü belirlenemedi: {e}")
    
    return False, "Dosya güvenli görünüyor"

def scan_file_for_malware(file_content, file_name, user_id):
    """
    Comprehensive malware scan for uploaded files.
    Only owner can bypass these checks.
    """
    if user_id == OWNER_ID:
        return True, "Sahip güvenlik kontrolünü atladı"
    
    is_suspicious, reason = is_suspicious_file(file_content, file_name)
    
    if is_suspicious:
        logger.warning(f"🚨 {file_name} dosyasında kötü amaçlı yazılım tespit edildi (kullanıcı {user_id}): {reason}")
        return False, f"Güvenlik ihlali: {reason}"
    
    return True, "Dosya güvenlik kontrolünü geçti"

# --- Helper Functions ---
def get_user_folder(user_id):
    """Get or create user's folder for storing files"""
    user_folder = os.path.join(UPLOAD_BOTS_DIR, str(user_id))
    os.makedirs(user_folder, exist_ok=True)
    return user_folder

def get_user_file_limit(user_id):
    """Get the file upload limit for a user"""
    if user_id == OWNER_ID: return OWNER_LIMIT
    if user_id in admin_ids: return ADMIN_LIMIT
    if user_id in user_subscriptions and user_subscriptions[user_id]['expiry'] > datetime.now():
        return SUBSCRIBED_USER_LIMIT
    return FREE_USER_LIMIT

def get_user_file_count(user_id):
    """Get the number of files uploaded by a user"""
    return len(user_files.get(user_id, []))

def is_bot_running(script_owner_id, file_name):
    """Check if a bot script is currently running for a specific user"""
    script_key = f"{script_owner_id}_{file_name}"
    script_info = bot_scripts.get(script_key)
    if script_info and script_info.get('process'):
        try:
            proc = psutil.Process(script_info['process'].pid)
            is_running = proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
            if not is_running:
                logger.warning(f"{script_key} için PID {script_info['process'].pid} bulundu ancak çalışmıyor/zombi. Temizleniyor.")
                if 'log_file' in script_info and hasattr(script_info['log_file'], 'close') and not script_info['log_file'].closed:
                    try:
                        script_info['log_file'].close()
                    except Exception as log_e:
                        logger.error(f"{script_key} zombie temizliği sırasında log dosyası kapatma hatası: {log_e}")
                if script_key in bot_scripts:
                    del bot_scripts[script_key]
            return is_running
        except psutil.NoSuchProcess:
            logger.warning(f"{script_key} için işlem bulunamadı (NoSuchProcess). Temizleniyor.")
            if 'log_file' in script_info and hasattr(script_info['log_file'], 'close') and not script_info['log_file'].closed:
                try:
                    script_info['log_file'].close()
                except Exception as log_e:
                    logger.error(f"{script_key} var olmayan işlem temizliği sırasında log dosyası kapatma hatası: {log_e}")
            if script_key in bot_scripts:
                del bot_scripts[script_key]
            return False
        except Exception as e:
            logger.error(f"{script_key} için işlem durumu kontrol hatası: {e}", exc_info=True)
            return False
    return False

def kill_process_tree(process_info):
    """Kill a process and all its children, ensuring log file is closed."""
    pid = None
    log_file_closed = False
    script_key = process_info.get('script_key', 'N/A')

    try:
        if 'log_file' in process_info and hasattr(process_info['log_file'], 'close') and not process_info['log_file'].closed:
            try:
                process_info['log_file'].close()
                log_file_closed = True
                logger.info(f"{script_key} için log dosyası kapatıldı (PID: {process_info.get('process', {}).get('pid', 'N/A')})")
            except Exception as log_e:
                logger.error(f"{script_key} öldürme sırasında log dosyası kapatma hatası: {log_e}")

        process = process_info.get('process')
        if process and hasattr(process, 'pid'):
            pid = process.pid
            if pid:
                try:
                    parent = psutil.Process(pid)
                    children = parent.children(recursive=True)
                    logger.info(f"{script_key} için işlem ağacı öldürülüyor (PID: {pid}, Çocuklar: {[c.pid for c in children]})")

                    for child in children:
                        try:
                            child.terminate()
                            logger.info(f"{script_key} için çocuk işlem {child.pid} sonlandırıldı")
                        except psutil.NoSuchProcess:
                            logger.warning(f"{script_key} için çocuk işlem {child.pid} zaten gitmiş.")
                        except Exception as e:
                            logger.error(f"{script_key} için çocuk {child.pid} sonlandırma hatası: {e}. Öldürülüyor...")
                            try:
                                child.kill()
                                logger.info(f"{script_key} için çocuk işlem {child.pid} öldürüldü")
                            except Exception as e2:
                                logger.error(f"{script_key} için çocuk {child.pid} öldürülemedi: {e2}")

                    gone, alive = psutil.wait_procs(children, timeout=1)
                    for p in alive:
                        logger.warning(f"{script_key} için çocuk işlem {p.pid} hala aktif. Öldürülüyor.")
                        try:
                            p.kill()
                        except Exception as e:
                            logger.error(f"{script_key} için çocuk {p.pid} bekleme sonrası öldürülemedi: {e}")

                    try:
                        parent.terminate()
                        logger.info(f"{script_key} için ana işlem {pid} sonlandırıldı")
                        try:
                            parent.wait(timeout=1)
                        except psutil.TimeoutExpired:
                            logger.warning(f"{script_key} için ana işlem {pid} sonlanmadı. Öldürülüyor.")
                            parent.kill()
                            logger.info(f"{script_key} için ana işlem {pid} öldürüldü")
                    except psutil.NoSuchProcess:
                        logger.warning(f"{script_key} için ana işlem {pid} zaten gitmiş.")
                    except Exception as e:
                        logger.error(f"{script_key} için ana {pid} sonlandırma hatası: {e}. Öldürülüyor...")
                        try:
                            parent.kill()
                            logger.info(f"{script_key} için ana işlem {pid} öldürüldü")
                        except Exception as e2:
                            logger.error(f"{script_key} için ana {pid} öldürülemedi: {e2}")

                except psutil.NoSuchProcess:
                    logger.warning(f"{script_key} için işlem {pid or 'N/A'} öldürme sırasında bulunamadı. Zaten sonlanmış?")
            else:
                logger.error(f"{script_key} için işlem PID'i None.")
        elif log_file_closed:
            logger.warning(f"{script_key} için işlem nesnesi eksik, ancak log dosyası kapatıldı.")
        else:
            logger.error(f"{script_key} için işlem nesnesi eksik ve log dosyası yok. Öldürülemez.")
    except Exception as e:
        logger.error(f"❌ PID {pid or 'N/A'} ({script_key}) için işlem ağacı öldürülürken beklenmeyen hata: {e}", exc_info=True)

# --- Automatic Package Installation & Script Running ---

def attempt_install_pip(module_name, message):
    package_name = TELEGRAM_MODULES.get(module_name.lower(), module_name) 
    if package_name is None: 
        logger.info(f"'{module_name}' modülü çekirdek. Pip kurulumu atlanıyor.")
        return False 
    try:
        bot.reply_to(message, f"🐍 `{module_name}` modülü bulunamadı. `{package_name}` kuruluyor...", parse_mode='Markdown')
        command = [sys.executable, '-m', 'pip', 'install', package_name]
        logger.info(f"Kurulum çalıştırılıyor: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore')
        if result.returncode == 0:
            logger.info(f"{package_name} kuruldu. Çıktı:\n{result.stdout}")
            bot.reply_to(message, f"✅ `{package_name}` paketi (`{module_name}` için) kuruldu.", parse_mode='Markdown')
            return True
        else:
            error_msg = f"❌ `{module_name}` için `{package_name}` kurulumu başarısız.\nLog:\n```\n{result.stderr or result.stdout}\n```"
            logger.error(error_msg)
            if len(error_msg) > 4000: error_msg = error_msg[:4000] + "\n... (Log kısaltıldı)"
            bot.reply_to(message, error_msg, parse_mode='Markdown')
            return False
    except Exception as e:
        error_msg = f"❌ `{package_name}` kurulurken hata: {str(e)}"
        logger.error(error_msg, exc_info=True)
        bot.reply_to(message, error_msg)
        return False

def attempt_install_npm(module_name, user_folder, message):
    try:
        bot.reply_to(message, f"🟠 Node paketi `{module_name}` bulunamadı. Yerel olarak kuruluyor...", parse_mode='Markdown')
        command = ['npm', 'install', module_name]
        logger.info(f"npm kurulumu çalıştırılıyor: {' '.join(command)} {user_folder} içinde")
        result = subprocess.run(command, capture_output=True, text=True, check=False, cwd=user_folder, encoding='utf-8', errors='ignore')
        if result.returncode == 0:
            logger.info(f"{module_name} kuruldu. Çıktı:\n{result.stdout}")
            bot.reply_to(message, f"✅ Node paketi `{module_name}` yerel olarak kuruldu.", parse_mode='Markdown')
            return True
        else:
            error_msg = f"❌ Node paketi `{module_name}` kurulumu başarısız.\nLog:\n```\n{result.stderr or result.stdout}\n```"
            logger.error(error_msg)
            if len(error_msg) > 4000: error_msg = error_msg[:4000] + "\n... (Log kısaltıldı)"
            bot.reply_to(message, error_msg, parse_mode='Markdown')
            return False
    except FileNotFoundError:
         error_msg = "❌ Hata: 'npm' bulunamadı. Node.js/npm'in kurulu ve PATH'te olduğundan emin olun."
         logger.error(error_msg)
         bot.reply_to(message, error_msg)
         return False
    except Exception as e:
        error_msg = f"❌ Node paketi `{module_name}` kurulurken hata: {str(e)}"
        logger.error(error_msg, exc_info=True)
        bot.reply_to(message, error_msg)
        return False

def run_script(script_path, script_owner_id, user_folder, file_name, message_obj_for_reply, attempt=1):
    """Run Python script. script_owner_id is used for the script_key. message_obj_for_reply is for sending feedback."""
    max_attempts = 2 
    if attempt > max_attempts:
        bot.reply_to(message_obj_for_reply, f"❌ '{file_name}' {max_attempts} denemeden sonra çalıştırılamadı. Logları kontrol edin.")
        return

    script_key = f"{script_owner_id}_{file_name}"
    logger.info(f"{script_path} Python betiği çalıştırılıyor (Deneme {attempt}) (Anahtar: {script_key}) kullanıcı {script_owner_id} için")

    try:
        if not os.path.exists(script_path):
             bot.reply_to(message_obj_for_reply, f"❌ Hata: '{file_name}' betiği '{script_path}' adresinde bulunamadı!")
             logger.error(f"Betik bulunamadı: {script_path} kullanıcı {script_owner_id} için")
             if script_owner_id in user_files:
                 user_files[script_owner_id] = [f for f in user_files.get(script_owner_id, []) if f[0] != file_name]
             remove_user_file_db(script_owner_id, file_name)
             return

        if attempt == 1:
            check_command = [sys.executable, script_path]
            logger.info(f"Python ön kontrolü çalıştırılıyor: {' '.join(check_command)}")
            check_proc = None
            try:
                check_proc = subprocess.Popen(check_command, cwd=user_folder, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
                stdout, stderr = check_proc.communicate(timeout=5)
                return_code = check_proc.returncode
                logger.info(f"Python Ön kontrol erken. RC: {return_code}. Stderr: {stderr[:200]}...")
                if return_code != 0 and stderr:
                    match_py = re.search(r"ModuleNotFoundError: No module named '(.+?)'", stderr)
                    if match_py:
                        module_name = match_py.group(1).strip().strip("'\"")
                        logger.info(f"Eksik Python modülü tespit edildi: {module_name}")
                        if attempt_install_pip(module_name, message_obj_for_reply):
                            logger.info(f"{module_name} için kurulum tamam. run_script yeniden deneniyor...")
                            bot.reply_to(message_obj_for_reply, f"🔄 Kurulum başarılı. '{file_name}' yeniden deneniyor...")
                            time.sleep(2)
                            threading.Thread(target=run_script, args=(script_path, script_owner_id, user_folder, file_name, message_obj_for_reply, attempt + 1)).start()
                            return
                        else:
                            bot.reply_to(message_obj_for_reply, f"❌ Kurulum başarısız. '{file_name}' çalıştırılamıyor.")
                            return
                    else:
                         error_summary = stderr[:500]
                         bot.reply_to(message_obj_for_reply, f"❌ '{file_name}' için betik ön kontrolünde hata:\n```\n{error_summary}\n```\nBetiği düzeltin.", parse_mode='Markdown')
                         return
            except subprocess.TimeoutExpired:
                logger.info("Python Ön kontrol zaman aşımına uğradı (>5sn), importlar muhtemelen tamam. Kontrol işlemi öldürülüyor.")
                if check_proc and check_proc.poll() is None: check_proc.kill(); check_proc.communicate()
                logger.info("Python Kontrol işlemi öldürüldü. Uzun çalışmaya devam ediliyor.")
            except FileNotFoundError:
                 logger.error(f"Python yorumlayıcı bulunamadı: {sys.executable}")
                 bot.reply_to(message_obj_for_reply, f"❌ Hata: Python yorumlayıcı '{sys.executable}' bulunamadı.")
                 return
            except Exception as e:
                 logger.error(f"{script_key} için Python ön kontrolünde hata: {e}", exc_info=True)
                 bot.reply_to(message_obj_for_reply, f"❌ '{file_name}' için betik ön kontrolünde beklenmeyen hata: {e}")
                 return
            finally:
                 if check_proc and check_proc.poll() is None:
                     logger.warning(f"Python Kontrol işlemi {check_proc.pid} hala çalışıyor. Öldürülüyor.")
                     check_proc.kill(); check_proc.communicate()

        logger.info(f"{script_key} için uzun çalışan Python işlemi başlatılıyor")
        log_file_path = os.path.join(user_folder, f"{os.path.splitext(file_name)[0]}.log")
        log_file = None; process = None
        try: log_file = open(log_file_path, 'w', encoding='utf-8', errors='ignore')
        except Exception as e:
             logger.error(f"{script_key} için '{log_file_path}' log dosyası açılamadı: {e}", exc_info=True)
             bot.reply_to(message_obj_for_reply, f"❌ '{log_file_path}' log dosyası açılamadı: {e}")
             return
        try:
            startupinfo = None; creationflags = 0
            if os.name == 'nt':
                 startupinfo = subprocess.STARTUPINFO(); startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                 startupinfo.wShowWindow = subprocess.SW_HIDE
            process = subprocess.Popen(
                [sys.executable, script_path], cwd=user_folder, stdout=log_file, stderr=log_file,
                stdin=subprocess.PIPE, startupinfo=startupinfo, creationflags=creationflags,
                encoding='utf-8', errors='ignore'
            )
            logger.info(f"{script_key} için Python işlemi {process.pid} başlatıldı")
            bot_scripts[script_key] = {
                'process': process, 'log_file': log_file, 'file_name': file_name,
                'chat_id': message_obj_for_reply.chat.id,
                'script_owner_id': script_owner_id,
                'start_time': datetime.now(), 'user_folder': user_folder, 'type': 'py', 'script_key': script_key
            }
            bot.reply_to(message_obj_for_reply, f"✅ Python betiği '{file_name}' başlatıldı! (PID: {process.pid}) (Kullanıcı: {script_owner_id})")
        except FileNotFoundError:
             logger.error(f"Uzun çalışma için Python yorumlayıcı {sys.executable} bulunamadı {script_key}")
             bot.reply_to(message_obj_for_reply, f"❌ Hata: Python yorumlayıcı '{sys.executable}' bulunamadı.")
             if log_file and not log_file.closed: log_file.close()
             if script_key in bot_scripts: del bot_scripts[script_key]
        except Exception as e:
            if log_file and not log_file.closed: log_file.close()
            error_msg = f"❌ Python betiği '{file_name}' başlatılırken hata: {str(e)}"
            logger.error(error_msg, exc_info=True)
            bot.reply_to(message_obj_for_reply, error_msg)
            if process and process.poll() is None:
                 logger.warning(f"{script_key} için potansiyel olarak başlatılan Python işlemi {process.pid} öldürülüyor")
                 kill_process_tree({'process': process, 'log_file': log_file, 'script_key': script_key})
            if script_key in bot_scripts: del bot_scripts[script_key]
    except Exception as e:
        error_msg = f"❌ Python betiği '{file_name}' çalıştırılırken beklenmeyen hata: {str(e)}"
        logger.error(error_msg, exc_info=True)
        bot.reply_to(message_obj_for_reply, error_msg)
        if script_key in bot_scripts:
             logger.warning(f"run_script'te hata nedeniyle {script_key} temizleniyor.")
             kill_process_tree(bot_scripts[script_key])
             del bot_scripts[script_key]

def run_js_script(script_path, script_owner_id, user_folder, file_name, message_obj_for_reply, attempt=1):
    """Run JS script. script_owner_id is used for the script_key. message_obj_for_reply is for sending feedback."""
    max_attempts = 2
    if attempt > max_attempts:
        bot.reply_to(message_obj_for_reply, f"❌ '{file_name}' {max_attempts} denemeden sonra çalıştırılamadı. Logları kontrol edin.")
        return

    script_key = f"{script_owner_id}_{file_name}"
    logger.info(f"{script_path} JS betiği çalıştırılıyor (Deneme {attempt}) (Anahtar: {script_key}) kullanıcı {script_owner_id} için")

    try:
        if not os.path.exists(script_path):
             bot.reply_to(message_obj_for_reply, f"❌ Hata: '{file_name}' betiği '{script_path}' adresinde bulunamadı!")
             logger.error(f"JS Betik bulunamadı: {script_path} kullanıcı {script_owner_id} için")
             if script_owner_id in user_files:
                 user_files[script_owner_id] = [f for f in user_files.get(script_owner_id, []) if f[0] != file_name]
             remove_user_file_db(script_owner_id, file_name)
             return

        if attempt == 1:
            check_command = ['node', script_path]
            logger.info(f"JS ön kontrolü çalıştırılıyor: {' '.join(check_command)}")
            check_proc = None
            try:
                check_proc = subprocess.Popen(check_command, cwd=user_folder, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
                stdout, stderr = check_proc.communicate(timeout=5)
                return_code = check_proc.returncode
                logger.info(f"JS Ön kontrol erken. RC: {return_code}. Stderr: {stderr[:200]}...")
                if return_code != 0 and stderr:
                    match_js = re.search(r"Cannot find module '(.+?)'", stderr)
                    if match_js:
                        module_name = match_js.group(1).strip().strip("'\"")
                        if not module_name.startswith('.') and not module_name.startswith('/'):
                             logger.info(f"Eksik Node modülü tespit edildi: {module_name}")
                             if attempt_install_npm(module_name, user_folder, message_obj_for_reply):
                                 logger.info(f"{module_name} için NPM Kurulumu tamam. run_js_script yeniden deneniyor...")
                                 bot.reply_to(message_obj_for_reply, f"🔄 NPM Kurulumu başarılı. '{file_name}' yeniden deneniyor...")
                                 time.sleep(2)
                                 threading.Thread(target=run_js_script, args=(script_path, script_owner_id, user_folder, file_name, message_obj_for_reply, attempt + 1)).start()
                                 return
                             else:
                                 bot.reply_to(message_obj_for_reply, f"❌ NPM Kurulumu başarısız. '{file_name}' çalıştırılamıyor.")
                                 return
                        else: logger.info(f"Göreceli/çekirdek modül için npm kurulumu atlanıyor: {module_name}")
                    error_summary = stderr[:500]
                    bot.reply_to(message_obj_for_reply, f"❌ '{file_name}' için JS betik ön kontrolünde hata:\n```\n{error_summary}\n```\nBetiği düzeltin veya manuel kurun.", parse_mode='Markdown')
                    return
            except subprocess.TimeoutExpired:
                logger.info("JS Ön kontrol zaman aşımına uğradı (>5sn), importlar muhtemelen tamam. Kontrol işlemi öldürülüyor.")
                if check_proc and check_proc.poll() is None: check_proc.kill(); check_proc.communicate()
                logger.info("JS Kontrol işlemi öldürüldü. Uzun çalışmaya devam ediliyor.")
            except FileNotFoundError:
                 error_msg = "❌ Hata: 'node' bulunamadı. JS dosyaları için Node.js'in kurulu olduğundan emin olun."
                 logger.error(error_msg)
                 bot.reply_to(message_obj_for_reply, error_msg)
                 return
            except Exception as e:
                 logger.error(f"{script_key} için JS ön kontrolünde hata: {e}", exc_info=True)
                 bot.reply_to(message_obj_for_reply, f"❌ '{file_name}' için JS ön kontrolünde beklenmeyen hata: {e}")
                 return
            finally:
                 if check_proc and check_proc.poll() is None:
                     logger.warning(f"JS Kontrol işlemi {check_proc.pid} hala çalışıyor. Öldürülüyor.")
                     check_proc.kill(); check_proc.communicate()

        logger.info(f"{script_key} için uzun çalışan JS işlemi başlatılıyor")
        log_file_path = os.path.join(user_folder, f"{os.path.splitext(file_name)[0]}.log")
        log_file = None; process = None
        try: log_file = open(log_file_path, 'w', encoding='utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"{script_key} JS betiği için '{log_file_path}' log dosyası açılamadı: {e}", exc_info=True)
            bot.reply_to(message_obj_for_reply, f"❌ '{log_file_path}' log dosyası açılamadı: {e}")
            return
        try:
            startupinfo = None; creationflags = 0
            if os.name == 'nt':
                 startupinfo = subprocess.STARTUPINFO(); startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                 startupinfo.wShowWindow = subprocess.SW_HIDE
            process = subprocess.Popen(
                ['node', script_path], cwd=user_folder, stdout=log_file, stderr=log_file,
                stdin=subprocess.PIPE, startupinfo=startupinfo, creationflags=creationflags,
                encoding='utf-8', errors='ignore'
            )
            logger.info(f"{script_key} için JS işlemi {process.pid} başlatıldı")
            bot_scripts[script_key] = {
                'process': process, 'log_file': log_file, 'file_name': file_name,
                'chat_id': message_obj_for_reply.chat.id,
                'script_owner_id': script_owner_id,
                'start_time': datetime.now(), 'user_folder': user_folder, 'type': 'js', 'script_key': script_key
            }
            bot.reply_to(message_obj_for_reply, f"✅ JS betiği '{file_name}' başlatıldı! (PID: {process.pid}) (Kullanıcı: {script_owner_id})")
        except FileNotFoundError:
             error_msg = "❌ Hata: Uzun çalışma için 'node' bulunamadı. Node.js'in kurulu olduğundan emin olun."
             logger.error(error_msg)
             if log_file and not log_file.closed: log_file.close()
             bot.reply_to(message_obj_for_reply, error_msg)
             if script_key in bot_scripts: del bot_scripts[script_key]
        except Exception as e:
            if log_file and not log_file.closed: log_file.close()
            error_msg = f"❌ JS betiği '{file_name}' başlatılırken hata: {str(e)}"
            logger.error(error_msg, exc_info=True)
            bot.reply_to(message_obj_for_reply, error_msg)
            if process and process.poll() is None:
                 logger.warning(f"{script_key} için potansiyel olarak başlatılan JS işlemi {process.pid} öldürülüyor")
                 kill_process_tree({'process': process, 'log_file': log_file, 'script_key': script_key})
            if script_key in bot_scripts: del bot_scripts[script_key]
    except Exception as e:
        error_msg = f"❌ JS betiği '{file_name}' çalıştırılırken beklenmeyen hata: {str(e)}"
        logger.error(error_msg, exc_info=True)
        bot.reply_to(message_obj_for_reply, error_msg)
        if script_key in bot_scripts:
             logger.warning(f"run_js_script'te hata nedeniyle {script_key} temizleniyor.")
             kill_process_tree(bot_scripts[script_key])
             del bot_scripts[script_key]

# --- Map Telegram import names to actual PyPI package names ---
TELEGRAM_MODULES = {
    'telebot': 'pyTelegramBotAPI',
    'telegram': 'python-telegram-bot',
    'python_telegram_bot': 'python-telegram-bot',
    'aiogram': 'aiogram',
    'pyrogram': 'pyrogram',
    'telethon': 'telethon',
    'telethon.sync': 'telethon',
    'from telethon.sync import telegramclient': 'telethon',
    'telepot': 'telepot',
    'pytg': 'pytg',
    'tgcrypto': 'tgcrypto',
    'telegram_upload': 'telegram-upload',
    'telegram_send': 'telegram-send',
    'telegram_text': 'telegram-text',
    'mtproto': 'telegram-mtproto',
    'tl': 'telethon',
    'telegram_utils': 'telegram-utils',
    'telegram_logger': 'telegram-logger',
    'telegram_handlers': 'python-telegram-handlers',
    'telegram_redis': 'telegram-redis',
    'telegram_sqlalchemy': 'telegram-sqlalchemy',
    'telegram_payment': 'telegram-payment',
    'telegram_shop': 'telegram-shop-sdk',
    'pytest_telegram': 'pytest-telegram',
    'telegram_debug': 'telegram-debug',
    'telegram_scraper': 'telegram-scraper',
    'telegram_analytics': 'telegram-analytics',
    'telegram_nlp': 'telegram-nlp-toolkit',
    'telegram_ai': 'telegram-ai',
    'telegram_api': 'telegram-api-client',
    'telegram_web': 'telegram-web-integration',
    'telegram_games': 'telegram-games',
    'telegram_quiz': 'telegram-quiz-bot',
    'telegram_ffmpeg': 'telegram-ffmpeg',
    'telegram_media': 'telegram-media-utils',
    'telegram_2fa': 'telegram-twofa',
    'telegram_crypto': 'telegram-crypto-bot',
    'telegram_i18n': 'telegram-i18n',
    'telegram_translate': 'telegram-translate',
    'bs4': 'beautifulsoup4',
    'requests': 'requests',
    'pillow': 'Pillow',
    'cv2': 'opencv-python',
    'yaml': 'PyYAML',
    'dotenv': 'python-dotenv',
    'dateutil': 'python-dateutil',
    'pandas': 'pandas',
    'numpy': 'numpy',
    'flask': 'Flask',
    'django': 'Django',
    'sqlalchemy': 'SQLAlchemy',
    'asyncio': None,
    'json': None,
    'datetime': None,
    'os': None,
    'sys': None,
    're': None,
    'time': None,
    'math': None,
    'random': None,
    'logging': None,
    'threading': None,
    'subprocess': None,
    'zipfile': None,
    'tempfile': None,
    'shutil': None,
    'sqlite3': None,
    'psutil': 'psutil',
    'atexit': None
}
# --- End Automatic Package Installation & Script Running ---

# --- Database Operations ---
DB_LOCK = threading.Lock() 

def save_user_file(user_id, file_name, file_type='py'):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR REPLACE INTO user_files (user_id, file_name, file_type) VALUES (?, ?, ?)',
                      (user_id, file_name, file_type))
            conn.commit()
            if user_id not in user_files: user_files[user_id] = []
            user_files[user_id] = [(fn, ft) for fn, ft in user_files[user_id] if fn != file_name]
            user_files[user_id].append((file_name, file_type))
            logger.info(f"{user_id} kullanıcısı için '{file_name}' ({file_type}) dosyası kaydedildi")
        except sqlite3.Error as e: logger.error(f"❌ {user_id}, {file_name} için dosya kaydedilirken SQLite hatası: {e}")
        except Exception as e: logger.error(f"❌ {user_id}, {file_name} için dosya kaydedilirken beklenmeyen hata: {e}", exc_info=True)
        finally: conn.close()

def remove_user_file_db(user_id, file_name):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('DELETE FROM user_files WHERE user_id = ? AND file_name = ?', (user_id, file_name))
            conn.commit()
            if user_id in user_files:
                user_files[user_id] = [f for f in user_files[user_id] if f[0] != file_name]
                if not user_files[user_id]: del user_files[user_id]
            logger.info(f"{user_id} kullanıcısı için '{file_name}' dosyası veritabanından kaldırıldı")
        except sqlite3.Error as e: logger.error(f"❌ {user_id}, {file_name} için dosya kaldırılırken SQLite hatası: {e}")
        except Exception as e: logger.error(f"❌ {user_id}, {file_name} için dosya kaldırılırken beklenmeyen hata: {e}", exc_info=True)
        finally: conn.close()

def add_active_user(user_id):
    active_users.add(user_id) 
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR IGNORE INTO active_users (user_id) VALUES (?)', (user_id,))
            conn.commit()
            logger.info(f"Aktif kullanıcı {user_id} veritabanına eklendi/onaylandı")
        except sqlite3.Error as e: logger.error(f"❌ Aktif kullanıcı {user_id} eklenirken SQLite hatası: {e}")
        except Exception as e: logger.error(f"❌ Aktif kullanıcı {user_id} eklenirken beklenmeyen hata: {e}", exc_info=True)
        finally: conn.close()

def save_subscription(user_id, expiry):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            expiry_str = expiry.isoformat()
            c.execute('INSERT OR REPLACE INTO subscriptions (user_id, expiry) VALUES (?, ?)', (user_id, expiry_str))
            conn.commit()
            user_subscriptions[user_id] = {'expiry': expiry}
            logger.info(f"{user_id} için abonelik kaydedildi, bitiş {expiry_str}")
        except sqlite3.Error as e: logger.error(f"❌ {user_id} için abonelik kaydedilirken SQLite hatası: {e}")
        except Exception as e: logger.error(f"❌ {user_id} için abonelik kaydedilirken beklenmeyen hata: {e}", exc_info=True)
        finally: conn.close()

def remove_subscription_db(user_id):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('DELETE FROM subscriptions WHERE user_id = ?', (user_id,))
            conn.commit()
            if user_id in user_subscriptions: del user_subscriptions[user_id]
            logger.info(f"{user_id} için abonelik veritabanından kaldırıldı")
        except sqlite3.Error as e: logger.error(f"❌ {user_id} için abonelik kaldırılırken SQLite hatası: {e}")
        except Exception as e: logger.error(f"❌ {user_id} için abonelik kaldırılırken beklenmeyen hata: {e}", exc_info=True)
        finally: conn.close()

def add_admin_db(admin_id):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (admin_id,))
            conn.commit()
            admin_ids.add(admin_id) 
            logger.info(f"Yönetici {admin_id} veritabanına eklendi")
        except sqlite3.Error as e: logger.error(f"❌ Yönetici {admin_id} eklenirken SQLite hatası: {e}")
        except Exception as e: logger.error(f"❌ Yönetici {admin_id} eklenirken beklenmeyen hata: {e}", exc_info=True)
        finally: conn.close()

def remove_admin_db(admin_id):
    if admin_id == OWNER_ID:
        logger.warning("Sahip ID'si yöneticilerden kaldırılmaya çalışıldı.")
        return False 
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        removed = False
        try:
            c.execute('SELECT 1 FROM admins WHERE user_id = ?', (admin_id,))
            if c.fetchone():
                c.execute('DELETE FROM admins WHERE user_id = ?', (admin_id,))
                conn.commit()
                removed = c.rowcount > 0 
                if removed: admin_ids.discard(admin_id); logger.info(f"Yönetici {admin_id} veritabanından kaldırıldı")
                else: logger.warning(f"Yönetici {admin_id} bulundu ancak silme 0 satır etkiledi.")
            else:
                logger.warning(f"Yönetici {admin_id} veritabanında bulunamadı.")
                admin_ids.discard(admin_id)
            return removed
        except sqlite3.Error as e: logger.error(f"❌ Yönetici {admin_id} kaldırılırken SQLite hatası: {e}"); return False
        except Exception as e: logger.error(f"❌ Yönetici {admin_id} kaldırılırken beklenmeyen hata: {e}", exc_info=True); return False
        finally: conn.close()
# --- End Database Operations ---

# --- Menu creation (Inline and ReplyKeyboards) ---
def create_main_menu_inline(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton('📢 Güncelleme Kanalı', url=UPDATE_CHANNEL),
        types.InlineKeyboardButton('📤 Dosya Yükle', callback_data='upload'),
        types.InlineKeyboardButton('📂 Dosyalarım', callback_data='check_files'),
        types.InlineKeyboardButton('⚡ Bot Hızı', callback_data='speed'),
        types.InlineKeyboardButton('📤 Komut Gönder', callback_data='send_command'),
        types.InlineKeyboardButton('📞 Sahiple İletişim', url=f'https://t.me/{YOUR_USERNAME.replace("@", "")}')
    ]

    if user_id in admin_ids:
        admin_buttons = [
            types.InlineKeyboardButton('💳 Abonelikler', callback_data='subscription'),
            types.InlineKeyboardButton('📊 İstatistikler', callback_data='stats'),
            types.InlineKeyboardButton('🔒 Botu Kilitle' if not bot_locked else '🔓 Kilidi Aç',
                                     callback_data='lock_bot' if not bot_locked else 'unlock_bot'),
            types.InlineKeyboardButton('📢 Duyuru', callback_data='broadcast'),
            types.InlineKeyboardButton('👑 Yönetici Paneli', callback_data='admin_panel'),
            types.InlineKeyboardButton('🟢 Tüm Kullanıcı Betiklerini Çalıştır', callback_data='run_all_scripts')
        ]
        markup.add(buttons[0])
        markup.add(buttons[1], buttons[2])
        markup.add(buttons[3], admin_buttons[0])
        markup.add(admin_buttons[1], admin_buttons[3])
        markup.add(admin_buttons[2], admin_buttons[5])
        markup.add(buttons[4])
        markup.add(admin_buttons[4])
        markup.add(buttons[5])
    else:
        markup.add(buttons[0])
        markup.add(buttons[1], buttons[2])
        markup.add(buttons[3])
        markup.add(buttons[4])
        markup.add(types.InlineKeyboardButton('📊 İstatistikler', callback_data='stats'))
        markup.add(buttons[5])
    return markup

def create_reply_keyboard_main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    layout_to_use = ADMIN_COMMAND_BUTTONS_LAYOUT_USER_SPEC if user_id in admin_ids else COMMAND_BUTTONS_LAYOUT_USER_SPEC
    for row_buttons_text in layout_to_use:
        markup.add(*[types.KeyboardButton(text) for text in row_buttons_text])
    return markup

def create_control_buttons(script_owner_id, file_name, is_running=True):
    markup = types.InlineKeyboardMarkup(row_width=2)
    if is_running:
        markup.row(
            types.InlineKeyboardButton("🔴 Durdur", callback_data=f'stop_{script_owner_id}_{file_name}'),
            types.InlineKeyboardButton("🔄 Yeniden Başlat", callback_data=f'restart_{script_owner_id}_{file_name}')
        )
        markup.row(
            types.InlineKeyboardButton("🗑️ Sil", callback_data=f'delete_{script_owner_id}_{file_name}'),
            types.InlineKeyboardButton("📜 Loglar", callback_data=f'logs_{script_owner_id}_{file_name}')
        )
    else:
        markup.row(
            types.InlineKeyboardButton("🟢 Başlat", callback_data=f'start_{script_owner_id}_{file_name}'),
            types.InlineKeyboardButton("🗑️ Sil", callback_data=f'delete_{script_owner_id}_{file_name}')
        )
        markup.row(
            types.InlineKeyboardButton("📜 Logları Görüntüle", callback_data=f'logs_{script_owner_id}_{file_name}')
        )
    markup.add(types.InlineKeyboardButton("🔙 Dosyalara Dön", callback_data='check_files'))
    return markup

def create_admin_panel():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton('➕ Yönetici Ekle', callback_data='add_admin'),
        types.InlineKeyboardButton('➖ Yönetici Kaldır', callback_data='remove_admin')
    )
    markup.row(types.InlineKeyboardButton('📋 Yöneticileri Listele', callback_data='list_admins'))
    markup.row(types.InlineKeyboardButton('🔙 Ana Menüye Dön', callback_data='back_to_main'))
    return markup

def create_subscription_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton('➕ Abonelik Ekle', callback_data='add_subscription'),
        types.InlineKeyboardButton('➖ Abonelik Kaldır', callback_data='remove_subscription')
    )
    markup.row(types.InlineKeyboardButton('🔍 Abonelik Sorgula', callback_data='check_subscription'))
    markup.row(types.InlineKeyboardButton('🔙 Ana Menüye Dön', callback_data='back_to_main'))
    return markup

def create_send_command_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton('📝 İşleme Gönder', callback_data='send_to_process'),
        types.InlineKeyboardButton('🔍 Tüm Logları Görüntüle', callback_data='view_all_logs')
    )
    markup.row(types.InlineKeyboardButton('🔙 Ana Menüye Dön', callback_data='back_to_main'))
    return markup
# --- End Menu Creation ---

# --- File Handling with Malware Detection ---
def handle_zip_file(downloaded_file_content, file_name_zip, message):
    user_id = message.from_user.id
    user_folder = get_user_folder(user_id)
    temp_dir = None
    
    # Security check for ZIP files (except owner)
    if user_id != OWNER_ID:
        is_safe, reason = scan_file_for_malware(downloaded_file_content, file_name_zip, user_id)
        if not is_safe:
            bot.reply_to(message, f"🚨 Güvenlik Uyarısı: {reason}\nBu tür dosyayı sadece sahip yükleyebilir.")
            return
    
    try:
        temp_dir = tempfile.mkdtemp(prefix=f"user_{user_id}_zip_")
        logger.info(f"Zip için geçici dizin: {temp_dir}")
        zip_path = os.path.join(temp_dir, file_name_zip)
        with open(zip_path, 'wb') as new_file:
            new_file.write(downloaded_file_content)
        
        # Open Zip to Extract
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Additional security check on content
            if user_id != OWNER_ID:
                for member in zip_ref.infolist():
                    member_name_lower = member.filename.lower()
                    suspicious_extensions = ['.exe', '.dll', '.bat', '.cmd', '.scr', '.com']
                    if any(member_name_lower.endswith(ext) for ext in suspicious_extensions):
                        bot.reply_to(message, f"🚨 Güvenlik Uyarısı: ZIP şüpheli dosya içeriyor: {member.filename}\nBu tür dosyaları sadece sahip yükleyebilir.")
                        return
                    
                    # Check for path traversal
                    member_path = os.path.abspath(os.path.join(temp_dir, member.filename))
                    if not member_path.startswith(os.path.abspath(temp_dir)):
                        raise zipfile.BadZipFile(f"Zip güvensiz yol içeriyor: {member.filename}")
            
            # Extract everything
            zip_ref.extractall(temp_dir)
            logger.info(f"Zip {temp_dir} dizinine çıkarıldı")

        # --- FIX: Recursively find script if not in root (ignores __MACOSX) ---
        target_dir = temp_dir
        root_files = os.listdir(target_dir)
        
        # Check if script exists in root
        if not any(f.endswith(('.py', '.js')) for f in root_files):
            # Recursively search for a folder containing .py or .js
            for root, dirs, files in os.walk(temp_dir):
                # Ignore system/hidden folders like __MACOSX or .git
                dirs[:] = [d for d in dirs if not d.startswith('.') and not d.startswith('__')]
                
                if any(f.endswith(('.py', '.js')) for f in files):
                    target_dir = root
                    break
        
        # If the script is in a subdirectory, move everything up to temp_dir
        if target_dir != temp_dir:
            logger.info(f"Çıkarılan dosyalar {target_dir} konumundan {temp_dir} konumuna düzleştiriliyor")
            for item in os.listdir(target_dir):
                s = os.path.join(target_dir, item)
                d = os.path.join(temp_dir, item)
                # Overwrite if exists (shouldn't happen often in this temp context)
                if os.path.exists(d):
                    if os.path.isdir(d): shutil.rmtree(d)
                    else: os.remove(d)
                shutil.move(s, d)
            # Refresh list after flattening
            extracted_items = os.listdir(temp_dir)
        else:
            extracted_items = root_files
        # --- END FIX ---

        py_files = [f for f in extracted_items if f.endswith('.py')]
        js_files = [f for f in extracted_items if f.endswith('.js')]
        req_file = 'requirements.txt' if 'requirements.txt' in extracted_items else None
        pkg_json = 'package.json' if 'package.json' in extracted_items else None

        if req_file:
            req_path = os.path.join(temp_dir, req_file)
            logger.info(f"requirements.txt bulundu, kurulum: {req_path}")
            bot.reply_to(message, f"🔄 Python bağımlılıkları `{req_file}` dosyasından kuruluyor...")
            try:
                command = [sys.executable, '-m', 'pip', 'install', '-r', req_path]
                result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore')
                logger.info(f"requirements.txt'den pip kurulumu tamam. Çıktı:\n{result.stdout}")
                bot.reply_to(message, f"✅ Python bağımlılıkları `{req_file}` dosyasından kuruldu.")
            except subprocess.CalledProcessError as e:
                error_msg = f"❌ `{req_file}` dosyasından Python bağımlılıkları kurulumu başarısız.\nLog:\n```\n{e.stderr or e.stdout}\n```"
                logger.error(error_msg)
                if len(error_msg) > 4000: error_msg = error_msg[:4000] + "\n... (Log kısaltıldı)"
                bot.reply_to(message, error_msg, parse_mode='Markdown'); return
            except Exception as e:
                 error_msg = f"❌ Python bağımlılıkları kurulurken beklenmeyen hata: {e}"
                 logger.error(error_msg, exc_info=True); bot.reply_to(message, error_msg); return

        if pkg_json:
            logger.info(f"package.json bulundu, npm kurulumu: {temp_dir}")
            bot.reply_to(message, f"🔄 Node bağımlılıkları `{pkg_json}` dosyasından kuruluyor...")
            try:
                command = ['npm', 'install']
                result = subprocess.run(command, capture_output=True, text=True, check=True, cwd=temp_dir, encoding='utf-8', errors='ignore')
                logger.info(f"npm kurulumu tamam. Çıktı:\n{result.stdout}")
                bot.reply_to(message, f"✅ Node bağımlılıkları `{pkg_json}` dosyasından kuruldu.")
            except FileNotFoundError:
                bot.reply_to(message, "❌ 'npm' bulunamadı. Node bağımlılıkları kurulamıyor."); return 
            except subprocess.CalledProcessError as e:
                error_msg = f"❌ `{pkg_json}` dosyasından Node bağımlılıkları kurulumu başarısız.\nLog:\n```\n{e.stderr or e.stdout}\n```"
                logger.error(error_msg)
                if len(error_msg) > 4000: error_msg = error_msg[:4000] + "\n... (Log kısaltıldı)"
                bot.reply_to(message, error_msg, parse_mode='Markdown'); return
            except Exception as e:
                 error_msg = f"❌ Node bağımlılıkları kurulurken beklenmeyen hata: {e}"
                 logger.error(error_msg, exc_info=True); bot.reply_to(message, error_msg); return

        main_script_name = None; file_type = None
        preferred_py = ['main.py', 'bot.py', 'app.py']; preferred_js = ['index.js', 'main.js', 'bot.js', 'app.js']
        for p in preferred_py:
            if p in py_files: main_script_name = p; file_type = 'py'; break
        if not main_script_name:
             for p in preferred_js:
                 if p in js_files: main_script_name = p; file_type = 'js'; break
        if not main_script_name:
            if py_files: main_script_name = py_files[0]; file_type = 'py'
            elif js_files: main_script_name = js_files[0]; file_type = 'js'
        if not main_script_name:
            bot.reply_to(message, "❌ Arşivde `.py` veya `.js` betiği bulunamadı!"); return

        logger.info(f"Çıkarılan dosyalar {temp_dir} konumundan {user_folder} konumuna taşınıyor")
        moved_count = 0
        for item_name in os.listdir(temp_dir):
            if item_name == file_name_zip: continue # Don't move the zip file itself if it's there
            src_path = os.path.join(temp_dir, item_name)
            dest_path = os.path.join(user_folder, item_name)
            if os.path.isdir(dest_path): shutil.rmtree(dest_path)
            elif os.path.exists(dest_path): os.remove(dest_path)
            shutil.move(src_path, dest_path); moved_count +=1
        logger.info(f"{moved_count} öğe {user_folder} konumuna taşındı")

        save_user_file(user_id, main_script_name, file_type)
        logger.info(f"{user_id} için zip'den ana betik '{main_script_name}' ({file_type}) kaydedildi.")
        main_script_path = os.path.join(user_folder, main_script_name)
        bot.reply_to(message, f"✅ Dosyalar çıkarıldı. Ana betik başlatılıyor: `{main_script_name}`...", parse_mode='Markdown')

        if file_type == 'py':
             threading.Thread(target=run_script, args=(main_script_path, user_id, user_folder, main_script_name, message)).start()
        elif file_type == 'js':
             threading.Thread(target=run_js_script, args=(main_script_path, user_id, user_folder, main_script_name, message)).start()

    except zipfile.BadZipFile as e:
        logger.error(f"{user_id} için geçersiz zip dosyası: {e}")
        bot.reply_to(message, f"❌ Hata: Geçersiz/bozuk ZIP. {e}")
    except Exception as e:
        logger.error(f"❌ {user_id} için zip işlenirken hata: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Zip işlenirken hata: {str(e)}")
    finally:
        if temp_dir and os.path.exists(temp_dir):
            try: shutil.rmtree(temp_dir); logger.info(f"Geçici dizin temizlendi: {temp_dir}")
            except Exception as e: logger.error(f"Geçici dizin {temp_dir} temizlenemedi: {e}", exc_info=True)
def handle_js_file(file_path, script_owner_id, user_folder, file_name, message):
    try:
        save_user_file(script_owner_id, file_name, 'js')
        threading.Thread(target=run_js_script, args=(file_path, script_owner_id, user_folder, file_name, message)).start()
    except Exception as e:
        logger.error(f"❌ {script_owner_id} için JS dosyası {file_name} işlenirken hata: {e}", exc_info=True)
        bot.reply_to(message, f"❌ JS dosyası işlenirken hata: {str(e)}")

def handle_py_file(file_path, script_owner_id, user_folder, file_name, message):
    try:
        save_user_file(script_owner_id, file_name, 'py')
        threading.Thread(target=run_script, args=(file_path, script_owner_id, user_folder, file_name, message)).start()
    except Exception as e:
        logger.error(f"❌ {script_owner_id} için Python dosyası {file_name} işlenirken hata: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Python dosyası işlenirken hata: {str(e)}")

# --- Send Command and Enhanced Logs Functions ---
def _logic_send_command(message):
    """Handle send command functionality"""
    user_id = message.from_user.id
    if bot_locked and user_id not in admin_ids:
        bot.reply_to(message, "⚠️ Bot yönetici tarafından kilitlendi.")
        return
        
    bot.reply_to(message, "📤 Komut Gönderme Seçenekleri:", reply_markup=create_send_command_menu())

def send_to_process_init(message):
    """Initialize process for sending command to a running script"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Get user's running processes
    user_running_scripts = []
    for script_key, script_info in bot_scripts.items():
        script_owner_id = script_info['script_owner_id']
        if (user_id == script_owner_id or user_id in admin_ids) and is_bot_running(script_owner_id, script_info['file_name']):
            user_running_scripts.append((script_key, script_info))
    
    if not user_running_scripts:
        bot.reply_to(message, "❌ Çalışan betik bulunamadı.")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for script_key, script_info in user_running_scripts:
        btn_text = f"{script_info['file_name']} (Kullanıcı: {script_info['script_owner_id']})"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f'sendcmd_select_{script_key}'))
    
    markup.add(types.InlineKeyboardButton("🔙 Geri", callback_data='send_command'))
    bot.reply_to(message, "📝 Komut göndermek için çalışan bir betik seçin:", reply_markup=markup)

def process_send_command(message, script_key):
    """Process the actual command to send to the script"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if script_key not in bot_scripts:
        bot.reply_to(message, "❌ Betik artık çalışmıyor.")
        return
    
    script_info = bot_scripts[script_key]
    command_text = message.text
    
    try:
        process = script_info['process']
        if process and process.poll() is None:
            # Send command to process stdin
            process.stdin.write(command_text + '\n')
            process.stdin.flush()
            bot.reply_to(message, f"✅ Komut `{script_info['file_name']}` betiğine gönderildi:\n`{command_text}`", parse_mode='Markdown')
            
            # Wait a bit and check if process is still running
            time.sleep(1)
            if process.poll() is not None:
                bot.reply_to(message, f"⚠️ `{script_info['file_name']}` betiği komut aldıktan sonra durdu.")
        else:
            bot.reply_to(message, f"❌ `{script_info['file_name']}` betiği çalışmıyor.")
    except Exception as e:
        logger.error(f"{script_key} komut gönderme hatası: {e}")
        bot.reply_to(message, f"❌ Komut gönderme hatası: {str(e)}")

def view_all_logs(message):
    """Show all available logs for user"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    user_logs = []
    
    # Get user's folder and all log files
    user_folder = get_user_folder(user_id)
    if os.path.exists(user_folder):
        for file in os.listdir(user_folder):
            if file.endswith('.log'):
                log_path = os.path.join(user_folder, file)
                file_size = os.path.getsize(log_path)
                user_logs.append((file, file_size, log_path))
    
    if not user_logs:
        bot.reply_to(message, "📜 Log dosyası bulunamadı.")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for log_file, size, log_path in sorted(user_logs):
        size_kb = size / 1024
        btn_text = f"{log_file} ({size_kb:.1f} KB)"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f'viewlog_{user_id}_{log_file}'))
    
    markup.add(types.InlineKeyboardButton("🔙 Geri", callback_data='send_command'))
    bot.reply_to(message, "📜 Mevcut Log Dosyaları:", reply_markup=markup)

def send_log_file(message, log_path, log_filename):
    """Send log file as document"""
    try:
        file_size = os.path.getsize(log_path)
        if file_size > 50 * 1024 * 1024:  # 50MB limit
            bot.reply_to(message, f"❌ Log dosyası çok büyük ({file_size/1024/1024:.1f} MB). Maksimum 50MB.")
            return
        
        with open(log_path, 'rb') as log_file:
            bot.send_document(message.chat.id, log_file, caption=f"📜 {log_filename}")
            
    except Exception as e:
        logger.error(f"Log dosyası gönderme hatası {log_path}: {e}")
        bot.reply_to(message, f"❌ Log dosyası gönderme hatası: {str(e)}")

# --- Logic Functions (called by commands and text handlers) ---
def _logic_send_welcome(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    user_name = message.from_user.first_name
    user_username = message.from_user.username

    logger.info(f"Hoş geldin isteği user_id: {user_id}, kullanıcı adı: @{user_username}")

    if bot_locked and user_id not in admin_ids:
        bot.send_message(chat_id, "⚠️ Bot yönetici tarafından kilitlendi. Daha sonra deneyin.")
        return

    user_bio = "Biyografi alınamadı"; photo_file_id = None
    try: user_bio = bot.get_chat(user_id).bio or "Biyografi yok"
    except Exception: pass
    try:
        user_profile_photos = bot.get_user_profile_photos(user_id, limit=1)
        if user_profile_photos.photos: photo_file_id = user_profile_photos.photos[0][-1].file_id
    except Exception: pass

    if user_id not in active_users:
        add_active_user(user_id)
        try:
            owner_notification = (f"🎉 Yeni kullanıcı!\n👤 İsim: {user_name}\n✳️ Kullanıcı: @{user_username or 'N/A'}\n"
                                  f"🆔 ID: `{user_id}`\n📝 Biyografi: {user_bio}")
            bot.send_message(OWNER_ID, owner_notification, parse_mode='Markdown')
            if photo_file_id: bot.send_photo(OWNER_ID, photo_file_id, caption=f"Yeni kullanıcı {user_id} fotoğrafı")
        except Exception as e: logger.error(f"⚠️ Yeni kullanıcı {user_id} hakkında sahibi bilgilendirilemedi: {e}")

    file_limit = get_user_file_limit(user_id)
    current_files = get_user_file_count(user_id)
    limit_str = str(file_limit) if file_limit != float('inf') else "Sınırsız"
    expiry_info = ""
    if user_id == OWNER_ID: user_status = "👑 Sahip"
    elif user_id in admin_ids: user_status = "🛡️ Yönetici"
    elif user_id in user_subscriptions:
        expiry_date = user_subscriptions[user_id].get('expiry')
        if expiry_date and expiry_date > datetime.now():
            user_status = "⭐ Premium"; days_left = (expiry_date - datetime.now()).days
            expiry_info = f"\n⏳ Abonelik bitiş: {days_left} gün kaldı"
        else: user_status = "🆓 Ücretsiz Kullanıcı (Süresi Dolmuş)"; remove_subscription_db(user_id)
    else: user_status = "🆓 Ücretsiz Kullanıcı"

    welcome_msg_text = (f"〽️ Hoş geldin, {user_name}!\n\n🆔 Kullanıcı ID'n: `{user_id}`\n"
                        f"✳️ Kullanıcı Adı: `@{user_username or 'Ayarlanmamış'}`\n"
                        f"🔰 Durumun: {user_status}{expiry_info}\n"
                        f"📁 Yüklenen Dosyalar: {current_files} / {limit_str}\n\n"
                        f"🤖 Python (`.py`) veya JS (`.js`) betiklerini barındır ve çalıştır.\n"
                        f"   Tek dosya veya `.zip` arşivi yükleyin.\n\n"
                        f"👇 Butonları kullanın veya komut yazın.")
    main_reply_markup = create_reply_keyboard_main_menu(user_id)
    try:
        if photo_file_id: bot.send_photo(chat_id, photo_file_id)
        bot.send_message(chat_id, welcome_msg_text, reply_markup=main_reply_markup, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"{user_id} için hoş geldin mesajı gönderilirken hata: {e}", exc_info=True)
        try: bot.send_message(chat_id, welcome_msg_text, reply_markup=main_reply_markup, parse_mode='Markdown')
        except Exception as fallback_e: logger.error(f"{user_id} için yedek mesaj gönderimi başarısız: {fallback_e}")

def _logic_updates_channel(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('📢 Güncelleme Kanalı', url=UPDATE_CHANNEL))
    bot.reply_to(message, "Güncelleme Kanalımızı Ziyaret Edin:", reply_markup=markup)

def _logic_upload_file(message):
    user_id = message.from_user.id
    if bot_locked and user_id not in admin_ids:
        bot.reply_to(message, "⚠️ Bot yönetici tarafından kilitlendi, dosya kabul edilmiyor.")
        return

    file_limit = get_user_file_limit(user_id)
    current_files = get_user_file_count(user_id)
    if current_files >= file_limit:
        limit_str = str(file_limit) if file_limit != float('inf') else "Sınırsız"
        bot.reply_to(message, f"⚠️ Dosya limitine ulaşıldı ({current_files}/{limit_str}). Önce dosya silin.")
        return
    bot.reply_to(message, "📤 Python (`.py`), JS (`.js`) veya ZIP (`.zip`) dosyanızı gönderin.")

def _logic_check_files(message):
    user_id = message.from_user.id
    user_files_list = user_files.get(user_id, [])
    if not user_files_list:
        bot.reply_to(message, "📂 Dosyalarınız:\n\n(Henüz dosya yüklenmemiş)")
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for file_name, file_type in sorted(user_files_list):
        is_running = is_bot_running(user_id, file_name)
        status_icon = "🟢 Çalışıyor" if is_running else "🔴 Durduruldu"
        btn_text = f"{file_name} ({file_type}) - {status_icon}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f'file_{user_id}_{file_name}'))
    bot.reply_to(message, "📂 Dosyalarınız:\nYönetmek için tıklayın.", reply_markup=markup, parse_mode='Markdown')

def _logic_bot_speed(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    start_time_ping = time.time()
    wait_msg = bot.reply_to(message, "🏃 Hız test ediliyor...")
    try:
        bot.send_chat_action(chat_id, 'typing')
        response_time = round((time.time() - start_time_ping) * 1000, 2)
        status = "🔓 Kilit Açık" if not bot_locked else "🔒 Kilitli"
        if user_id == OWNER_ID: user_level = "👑 Sahip"
        elif user_id in admin_ids: user_level = "🛡️ Yönetici"
        elif user_id in user_subscriptions and user_subscriptions[user_id].get('expiry', datetime.min) > datetime.now(): user_level = "⭐ Premium"
        else: user_level = "🆓 Ücretsiz Kullanıcı"
        speed_msg = (f"⚡ Bot Hızı ve Durumu:\n\n⏱️ API Yanıt Süresi: {response_time} ms\n"
                     f"🚦 Bot Durumu: {status}\n"
                     f"👤 Seviyeniz: {user_level}")
        bot.edit_message_text(speed_msg, chat_id, wait_msg.message_id)
    except Exception as e:
        logger.error(f"Hız testi sırasında hata (komut): {e}", exc_info=True)
        bot.edit_message_text("❌ Hız testi sırasında hata oluştu.", chat_id, wait_msg.message_id)

def _logic_contact_owner(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('📞 Sahiple İletişim', url=f'https://t.me/{YOUR_USERNAME.replace("@", "")}'))
    bot.reply_to(message, "Sahiple iletişime geçmek için tıklayın:", reply_markup=markup)

# --- Admin Logic Functions ---
def _logic_subscriptions_panel(message):
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "⚠️ Yönetici yetkisi gerekli.")
        return
    bot.reply_to(message, "💳 Abonelik Yönetimi\n/start veya yönetici komut menüsünden butonları kullanın.", reply_markup=create_subscription_menu())

def _logic_statistics(message):
    user_id = message.from_user.id
    total_users = len(active_users)
    total_files_records = sum(len(files) for files in user_files.values())

    running_bots_count = 0
    user_running_bots = 0

    for script_key_iter, script_info_iter in list(bot_scripts.items()):
        s_owner_id, _ = script_key_iter.split('_', 1)
        if is_bot_running(int(s_owner_id), script_info_iter['file_name']):
            running_bots_count += 1
            if int(s_owner_id) == user_id:
                user_running_bots +=1

    stats_msg_base = (f"📊 Bot İstatistikleri:\n\n"
                      f"👥 Toplam Kullanıcı: {total_users}\n"
                      f"📂 Toplam Dosya Kaydı: {total_files_records}\n"
                      f"🟢 Toplam Aktif Bot: {running_bots_count}\n")

    if user_id in admin_ids:
        stats_msg_admin = (f"🔒 Bot Durumu: {'🔴 Kilitli' if bot_locked else '🟢 Kilit Açık'}\n"
                           f"🤖 Çalışan Botlarınız: {user_running_bots}")
        stats_msg = stats_msg_base + stats_msg_admin
    else:
        stats_msg = stats_msg_base + f"🤖 Çalışan Botlarınız: {user_running_bots}"

    bot.reply_to(message, stats_msg)

def _logic_broadcast_init(message):
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "⚠️ Yönetici yetkisi gerekli.")
        return
    msg = bot.reply_to(message, "📢 Tüm aktif kullanıcılara duyuru mesajını gönderin.\n/cancel ile iptal edin.")
    bot.register_next_step_handler(msg, process_broadcast_message)

def _logic_toggle_lock_bot(message):
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "⚠️ Yönetici yetkisi gerekli.")
        return
    global bot_locked
    bot_locked = not bot_locked
    status = "kilitlendi" if bot_locked else "kilidi açıldı"
    logger.warning(f"Bot {status} Yönetici {message.from_user.id} tarafından komut/buton ile.")
    bot.reply_to(message, f"🔒 Bot {status}.")

def _logic_admin_panel(message):
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "⚠️ Yönetici yetkisi gerekli.")
        return
    bot.reply_to(message, "👑 Yönetici Paneli\nYöneticileri yönetin. /start veya yönetici menüsünden butonları kullanın.",
                 reply_markup=create_admin_panel())

def _logic_run_all_scripts(message_or_call):
    if isinstance(message_or_call, telebot.types.Message):
        admin_user_id = message_or_call.from_user.id
        admin_chat_id = message_or_call.chat.id
        reply_func = lambda text, **kwargs: bot.reply_to(message_or_call, text, **kwargs)
        admin_message_obj_for_script_runner = message_or_call
    elif isinstance(message_or_call, telebot.types.CallbackQuery):
        admin_user_id = message_or_call.from_user.id
        admin_chat_id = message_or_call.message.chat.id
        bot.answer_callback_query(message_or_call.id)
        reply_func = lambda text, **kwargs: bot.send_message(admin_chat_id, text, **kwargs)
        admin_message_obj_for_script_runner = message_or_call.message 
    else:
        logger.error("_logic_run_all_scripts için geçersiz argüman")
        return

    if admin_user_id not in admin_ids:
        reply_func("⚠️ Yönetici yetkisi gerekli.")
        return

    reply_func("⏳ Tüm kullanıcı betiklerini çalıştırma işlemi başlatılıyor. Bu biraz zaman alabilir...")
    logger.info(f"Yönetici {admin_user_id} 'tüm betikleri çalıştır' işlemini {admin_chat_id} sohbetinden başlattı.")

    started_count = 0; attempted_users = 0; skipped_files = 0; error_files_details = []

    all_user_files_snapshot = dict(user_files)

    for target_user_id, files_for_user in all_user_files_snapshot.items():
        if not files_for_user: continue
        attempted_users += 1
        logger.info(f"{target_user_id} kullanıcısı için betikler işleniyor...")
        user_folder = get_user_folder(target_user_id)

        for file_name, file_type in files_for_user:
            if not is_bot_running(target_user_id, file_name):
                file_path = os.path.join(user_folder, file_name)
                if os.path.exists(file_path):
                    logger.info(f"Yönetici {admin_user_id}, {target_user_id} kullanıcısı için '{file_name}' ({file_type}) başlatmayı deniyor.")
                    try:
                        if file_type == 'py':
                            threading.Thread(target=run_script, args=(file_path, target_user_id, user_folder, file_name, admin_message_obj_for_script_runner)).start()
                            started_count += 1
                        elif file_type == 'js':
                            threading.Thread(target=run_js_script, args=(file_path, target_user_id, user_folder, file_name, admin_message_obj_for_script_runner)).start()
                            started_count += 1
                        else:
                            logger.warning(f"{file_name} (kullanıcı {target_user_id}) için bilinmeyen dosya türü '{file_type}'. Atlanıyor.")
                            error_files_details.append(f"`{file_name}` (Kullanıcı {target_user_id}) - Bilinmeyen tür")
                            skipped_files += 1
                        time.sleep(0.7)
                    except Exception as e:
                        logger.error(f"'{file_name}' (kullanıcı {target_user_id}) başlatma kuyruğa alma hatası: {e}")
                        error_files_details.append(f"`{file_name}` (Kullanıcı {target_user_id}) - Başlatma hatası")
                        skipped_files += 1
                else:
                    logger.warning(f"{target_user_id} kullanıcısı için '{file_name}' dosyası '{file_path}' adresinde bulunamadı. Atlanıyor.")
                    error_files_details.append(f"`{file_name}` (Kullanıcı {target_user_id}) - Dosya bulunamadı")
                    skipped_files += 1

    summary_msg = (f"✅ Tüm Kullanıcı Betikleri - İşlem Tamamlandı:\n\n"
                   f"▶️ Başlatılmaya çalışılan: {started_count} betik.\n"
                   f"👥 İşlenen kullanıcı: {attempted_users}.\n")
    if skipped_files > 0:
        summary_msg += f"⚠️ Atlanan/Hatalı dosyalar: {skipped_files}\n"
        if error_files_details:
             summary_msg += "Detaylar (ilk 5):\n" + "\n".join([f"  - {err}" for err in error_files_details[:5]])
             if len(error_files_details) > 5: summary_msg += "\n  ... ve daha fazlası (logları kontrol edin)."

    reply_func(summary_msg, parse_mode='Markdown')
    logger.info(f"Tüm betikleri çalıştır işlemi tamamlandı. Yönetici: {admin_user_id}. Başlatılan: {started_count}. Atlanan/Hata: {skipped_files}")

# --- Command Handlers & Text Handlers for ReplyKeyboard ---
@bot.message_handler(commands=['start', 'help'])
def command_send_welcome(message): _logic_send_welcome(message)

@bot.message_handler(commands=['status'])
def command_show_status(message): _logic_statistics(message)

BUTTON_TEXT_TO_LOGIC = {
    "📢 Güncelleme Kanalı": _logic_updates_channel,
    "📤 Dosya Yükle": _logic_upload_file,
    "📂 Dosyalarım": _logic_check_files,
    "⚡ Bot Hızı": _logic_bot_speed,
    "📤 Komut Gönder": _logic_send_command,
    "📞 Sahiple İletişim": _logic_contact_owner,
    "📊 İstatistikler": _logic_statistics,
    "💳 Abonelikler": _logic_subscriptions_panel,
    "📢 Duyuru": _logic_broadcast_init,
    "🔒 Botu Kilitle": _logic_toggle_lock_bot,
    "🟢 Tüm Kodları Çalıştır": _logic_run_all_scripts,
    "👑 Yönetici Paneli": _logic_admin_panel,
}

@bot.message_handler(func=lambda message: message.text in BUTTON_TEXT_TO_LOGIC)
def handle_button_text(message):
    logic_func = BUTTON_TEXT_TO_LOGIC.get(message.text)
    if logic_func: logic_func(message)
    else: logger.warning(f"Buton metni '{message.text}' eşleşti ancak mantık fonksiyonu yok.")

@bot.message_handler(commands=['updateschannel'])
def command_updates_channel(message): _logic_updates_channel(message)
@bot.message_handler(commands=['uploadfile'])
def command_upload_file(message): _logic_upload_file(message)
@bot.message_handler(commands=['checkfiles'])
def command_check_files(message): _logic_check_files(message)
@bot.message_handler(commands=['botspeed'])
def command_bot_speed(message): _logic_bot_speed(message)
@bot.message_handler(commands=['sendcommand'])
def command_send_command(message): _logic_send_command(message)
@bot.message_handler(commands=['contactowner'])
def command_contact_owner(message): _logic_contact_owner(message)
@bot.message_handler(commands=['subscriptions'])
def command_subscriptions(message): _logic_subscriptions_panel(message)
@bot.message_handler(commands=['statistics'])
def command_statistics(message): _logic_statistics(message)
@bot.message_handler(commands=['broadcast'])
def command_broadcast(message): _logic_broadcast_init(message)
@bot.message_handler(commands=['lockbot']) 
def command_lock_bot(message): _logic_toggle_lock_bot(message)
@bot.message_handler(commands=['adminpanel'])
def command_admin_panel(message): _logic_admin_panel(message)
@bot.message_handler(commands=['runningallcode'])
def command_run_all_code(message): _logic_run_all_scripts(message)

@bot.message_handler(commands=['ping'])
def ping(message):
    start_ping_time = time.time() 
    msg = bot.reply_to(message, "Pong!")
    latency = round((time.time() - start_ping_time) * 1000, 2)
    bot.edit_message_text(f"Pong! Gecikme: {latency} ms", message.chat.id, msg.message_id)

# --- Document (File) Handler with Malware Detection ---
@bot.message_handler(content_types=['document'])
def handle_file_upload_doc(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    doc = message.document
    logger.info(f"{user_id} kullanıcısından dosya: {doc.file_name} ({doc.mime_type}), Boyut: {doc.file_size}")

    if bot_locked and user_id not in admin_ids:
        bot.reply_to(message, "⚠️ Bot kilitli, dosya kabul edilmiyor.")
        return

    file_limit = get_user_file_limit(user_id)
    current_files = get_user_file_count(user_id)
    if current_files >= file_limit:
        limit_str = str(file_limit) if file_limit != float('inf') else "Sınırsız"
        bot.reply_to(message, f"⚠️ Dosya limitine ulaşıldı ({current_files}/{limit_str}). /checkfiles ile dosya silin.")
        return

    file_name = doc.file_name
    if not file_name: bot.reply_to(message, "⚠️ Dosya adı yok. Dosyanın bir adı olduğundan emin olun."); return
    file_ext = os.path.splitext(file_name)[1].lower()
    if file_ext not in ['.py', '.js', '.zip']:
        bot.reply_to(message, "⚠️ Desteklenmeyen tür! Sadece `.py`, `.js`, `.zip` izinlidir.")
        return
    max_file_size = 20 * 1024 * 1024
    if doc.file_size > max_file_size:
        bot.reply_to(message, f"⚠️ Dosya çok büyük (Maks: {max_file_size // 1024 // 1024} MB)."); return

    try:
        try:
            bot.forward_message(OWNER_ID, chat_id, message.message_id)
            bot.send_message(OWNER_ID, f"⬆️ '{file_name}' dosyası {message.from_user.first_name} (`{user_id}`) tarafından yüklendi", parse_mode='Markdown')
        except Exception as e: logger.error(f"Yüklenen dosya SAHIP_ID {OWNER_ID} adresine iletilemedi: {e}")

        download_wait_msg = bot.reply_to(message, f"⏳ `{file_name}` indiriliyor...")
        file_info_tg_doc = bot.get_file(doc.file_id)
        downloaded_file_content = bot.download_file(file_info_tg_doc.file_path)
        
        # Malware scan (except for owner)
        if user_id != OWNER_ID:
            is_safe, reason = scan_file_for_malware(downloaded_file_content, file_name, user_id)
            if not is_safe:
                bot.edit_message_text(f"🚨 Güvenlik Uyarısı: {reason}", chat_id, download_wait_msg.message_id)
                return
        
        bot.edit_message_text(f"✅ `{file_name}` indirildi. İşleniyor...", chat_id, download_wait_msg.message_id)
        logger.info(f"{file_name} dosyası {user_id} kullanıcısı için indirildi")
        user_folder = get_user_folder(user_id)

        if file_ext == '.zip':
            handle_zip_file(downloaded_file_content, file_name, message)
        else:
            file_path = os.path.join(user_folder, file_name)
            with open(file_path, 'wb') as f: f.write(downloaded_file_content)
            logger.info(f"Tek dosya {file_path} konumuna kaydedildi")
            if file_ext == '.js': handle_js_file(file_path, user_id, user_folder, file_name, message)
            elif file_ext == '.py': handle_py_file(file_path, user_id, user_folder, file_name, message)
    except telebot.apihelper.ApiTelegramException as e:
         logger.error(f"{user_id} için dosya işlenirken Telegram API Hatası: {e}", exc_info=True)
         if "file is too big" in str(e).lower():
              bot.reply_to(message, f"❌ Telegram API Hatası: Dosya indirmek için çok büyük (~20MB limit).")
         else: bot.reply_to(message, f"❌ Telegram API Hatası: {str(e)}. Daha sonra deneyin.")
    except Exception as e:
        logger.error(f"❌ {user_id} için dosya işlenirken genel hata: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Beklenmeyen hata: {str(e)}")

# --- Callback Query Handlers (for Inline Buttons) ---
@bot.callback_query_handler(func=lambda call: True) 
def handle_callbacks(call):
    user_id = call.from_user.id
    data = call.data
    logger.info(f"Callback: Kullanıcı={user_id}, Veri='{data}'")

    if bot_locked and user_id not in admin_ids and data not in ['back_to_main', 'speed', 'stats']:
        bot.answer_callback_query(call.id, "⚠️ Bot yönetici tarafından kilitlendi.", show_alert=True)
        return
    try:
        if data == 'upload': upload_callback(call)
        elif data == 'check_files': check_files_callback(call)
        elif data.startswith('file_'): file_control_callback(call)
        elif data.startswith('start_'): start_bot_callback(call)
        elif data.startswith('stop_'): stop_bot_callback(call)
        elif data.startswith('restart_'): restart_bot_callback(call)
        elif data.startswith('delete_'): delete_bot_callback(call)
        elif data.startswith('logs_'): logs_bot_callback(call)
        elif data == 'speed': speed_callback(call)
        elif data == 'back_to_main': back_to_main_callback(call)
        elif data.startswith('confirm_broadcast_'): handle_confirm_broadcast(call)
        elif data == 'cancel_broadcast': handle_cancel_broadcast(call)
        # --- New Send Command Callbacks ---
        elif data == 'send_command': send_command_callback(call)
        elif data == 'send_to_process': send_to_process_callback(call)
        elif data.startswith('sendcmd_select_'): sendcmd_select_callback(call)
        elif data == 'view_all_logs': view_all_logs_callback(call)
        elif data.startswith('viewlog_'): viewlog_callback(call)
        # --- Admin Callbacks ---
        elif data == 'subscription': admin_required_callback(call, subscription_management_callback)
        elif data == 'stats': stats_callback(call)
        elif data == 'lock_bot': admin_required_callback(call, lock_bot_callback)
        elif data == 'unlock_bot': admin_required_callback(call, unlock_bot_callback)
        elif data == 'run_all_scripts': admin_required_callback(call, run_all_scripts_callback)
        elif data == 'broadcast': admin_required_callback(call, broadcast_init_callback) 
        elif data == 'admin_panel': admin_required_callback(call, admin_panel_callback)
        elif data == 'add_admin': owner_required_callback(call, add_admin_init_callback) 
        elif data == 'remove_admin': owner_required_callback(call, remove_admin_init_callback) 
        elif data == 'list_admins': admin_required_callback(call, list_admins_callback)
        elif data == 'add_subscription': admin_required_callback(call, add_subscription_init_callback) 
        elif data == 'remove_subscription': admin_required_callback(call, remove_subscription_init_callback) 
        elif data == 'check_subscription': admin_required_callback(call, check_subscription_init_callback) 
        else:
            bot.answer_callback_query(call.id, "Bilinmeyen işlem.")
            logger.warning(f"İşlenmeyen callback verisi: {data} kullanıcı {user_id} tarafından")
    except Exception as e:
        logger.error(f"'{data}' callback'i {user_id} için işlenirken hata: {e}", exc_info=True)
        try: bot.answer_callback_query(call.id, "İstek işlenirken hata oluştu.", show_alert=True)
        except Exception as e_ans: logger.error(f"Hata sonrası callback yanıtı gönderilemedi: {e_ans}")

def admin_required_callback(call, func_to_run):
    if call.from_user.id not in admin_ids:
        bot.answer_callback_query(call.id, "⚠️ Yönetici yetkisi gerekli.", show_alert=True)
        return
    func_to_run(call) 

def owner_required_callback(call, func_to_run):
    if call.from_user.id != OWNER_ID:
        bot.answer_callback_query(call.id, "⚠️ Sahip yetkisi gerekli.", show_alert=True)
        return
    func_to_run(call)

# --- New Send Command Callback Functions ---
def send_command_callback(call):
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_text("📤 Komut Gönderme Seçenekleri:",
                              call.message.chat.id, call.message.message_id, 
                              reply_markup=create_send_command_menu())
    except Exception as e:
        logger.error(f"Komut gönderme menüsü gösterilirken hata: {e}")

def send_to_process_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "📝 Çalıştırmak istediğiniz komutu gönderin:")
    bot.register_next_step_handler(msg, lambda m: send_to_process_init(m))

def sendcmd_select_callback(call):
    try:
        script_key = call.data.replace('sendcmd_select_', '')
        bot.answer_callback_query(call.id, f"Betik seçildi: {script_key}")
        msg = bot.send_message(call.message.chat.id, f"📝 {script_key} betiğine gönderilecek komutu yazın:")
        bot.register_next_step_handler(msg, lambda m: process_send_command(m, script_key))
    except Exception as e:
        logger.error(f"sendcmd_select_callback hatası: {e}")
        bot.answer_callback_query(call.id, "Betik seçilirken hata oluştu.")

def view_all_logs_callback(call):
    bot.answer_callback_query(call.id)
    view_all_logs(call.message)

def viewlog_callback(call):
    try:
        _, user_id_str, log_filename = call.data.split('_', 2)
        user_id = int(user_id_str)
        requesting_user_id = call.from_user.id
        
        if not (requesting_user_id == user_id or requesting_user_id in admin_ids):
            bot.answer_callback_query(call.id, "⚠️ Sadece kendi loglarınızı görüntüleyebilirsiniz.", show_alert=True)
            return
            
        user_folder = get_user_folder(user_id)
        log_path = os.path.join(user_folder, log_filename)
        
        if not os.path.exists(log_path):
            bot.answer_callback_query(call.id, "❌ Log dosyası bulunamadı.", show_alert=True)
            return
            
        bot.answer_callback_query(call.id, "📜 Log dosyası gönderiliyor...")
        send_log_file(call.message, log_path, log_filename)
        
    except Exception as e:
        logger.error(f"viewlog_callback hatası: {e}")
        bot.answer_callback_query(call.id, "Log görüntüleme hatası.")

# ... (rest of the existing callback functions remain the same)

def upload_callback(call):
    user_id = call.from_user.id
    file_limit = get_user_file_limit(user_id)
    current_files = get_user_file_count(user_id)
    if current_files >= file_limit:
        limit_str = str(file_limit) if file_limit != float('inf') else "Sınırsız"
        bot.answer_callback_query(call.id, f"⚠️ Dosya limitine ulaşıldı ({current_files}/{limit_str}).", show_alert=True)
        return
    bot.answer_callback_query(call.id) 
    bot.send_message(call.message.chat.id, "📤 Python (`.py`), JS (`.js`) veya ZIP (`.zip`) dosyanızı gönderin.")

def check_files_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id 
    user_files_list = user_files.get(user_id, [])
    if not user_files_list:
        bot.answer_callback_query(call.id, "⚠️ Dosya yüklenmemiş.", show_alert=True)
        try:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔙 Ana Menüye Dön", callback_data='back_to_main'))
            bot.edit_message_text("📂 Dosyalarınız:\n\n(Henüz dosya yüklenmemiş)", chat_id, call.message.message_id, reply_markup=markup)
        except Exception as e: logger.error(f"Boş dosya listesi için mesaj düzenleme hatası: {e}")
        return
    bot.answer_callback_query(call.id) 
    markup = types.InlineKeyboardMarkup(row_width=1) 
    for file_name, file_type in sorted(user_files_list): 
        is_running = is_bot_running(user_id, file_name)
        status_icon = "🟢 Çalışıyor" if is_running else "🔴 Durduruldu"
        btn_text = f"{file_name} ({file_type}) - {status_icon}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f'file_{user_id}_{file_name}'))
    markup.add(types.InlineKeyboardButton("🔙 Ana Menüye Dön", callback_data='back_to_main'))
    try:
        bot.edit_message_text("📂 Dosyalarınız:\nYönetmek için tıklayın.", chat_id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')
    except telebot.apihelper.ApiTelegramException as e:
         if "message is not modified" in str(e): logger.warning("Mesaj değiştirilmedi (dosyalar).")
         else: logger.error(f"Dosya listesi için mesaj düzenleme hatası: {e}")
    except Exception as e: logger.error(f"Dosya listesi için mesaj düzenlemede beklenmeyen hata: {e}", exc_info=True)

def file_control_callback(call):
    try:
        _, script_owner_id_str, file_name = call.data.split('_', 2)
        script_owner_id = int(script_owner_id_str)
        requesting_user_id = call.from_user.id

        if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
            logger.warning(f"Kullanıcı {requesting_user_id}, {script_owner_id} kullanıcısının '{file_name}' dosyasına izinsiz erişmeye çalıştı.")
            bot.answer_callback_query(call.id, "⚠️ Sadece kendi dosyalarınızı yönetebilirsiniz.", show_alert=True)
            check_files_callback(call)
            return

        user_files_list = user_files.get(script_owner_id, [])
        if not any(f[0] == file_name for f in user_files_list):
            logger.warning(f"Kontrol sırasında {script_owner_id} kullanıcısı için '{file_name}' dosyası bulunamadı.")
            bot.answer_callback_query(call.id, "⚠️ Dosya bulunamadı.", show_alert=True)
            check_files_callback(call) 
            return

        bot.answer_callback_query(call.id) 
        is_running = is_bot_running(script_owner_id, file_name)
        status_text = '🟢 Çalışıyor' if is_running else '🔴 Durduruldu'
        file_type = next((f[1] for f in user_files_list if f[0] == file_name), '?') 
        try:
            bot.edit_message_text(
                f"⚙️ Kontroller: `{file_name}` ({file_type}) (Kullanıcı: `{script_owner_id}`)\nDurum: {status_text}",
                call.message.chat.id, call.message.message_id,
                reply_markup=create_control_buttons(script_owner_id, file_name, is_running),
                parse_mode='Markdown'
            )
        except telebot.apihelper.ApiTelegramException as e:
             if "message is not modified" in str(e): logger.warning(f"{file_name} için kontroller mesajı değiştirilmedi")
             else: raise 
    except (ValueError, IndexError) as ve:
        logger.error(f"Dosya kontrol callback ayrıştırma hatası: {ve}. Veri: '{call.data}'")
        bot.answer_callback_query(call.id, "Hata: Geçersiz işlem verisi.", show_alert=True)
    except Exception as e:
        logger.error(f"'{call.data}' verisi için file_control_callback hatası: {e}", exc_info=True)
        bot.answer_callback_query(call.id, "Bir hata oluştu.", show_alert=True)

def start_bot_callback(call):
    try:
        _, script_owner_id_str, file_name = call.data.split('_', 2)
        script_owner_id = int(script_owner_id_str)
        requesting_user_id = call.from_user.id
        chat_id_for_reply = call.message.chat.id

        logger.info(f"Başlatma isteği: İsteyen={requesting_user_id}, Sahip={script_owner_id}, Dosya='{file_name}'")

        if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
            bot.answer_callback_query(call.id, "⚠️ Bu betiği başlatma izniniz yok.", show_alert=True); return

        user_files_list = user_files.get(script_owner_id, [])
        file_info = next((f for f in user_files_list if f[0] == file_name), None)
        if not file_info:
            bot.answer_callback_query(call.id, "⚠️ Dosya bulunamadı.", show_alert=True); check_files_callback(call); return

        file_type = file_info[1]
        user_folder = get_user_folder(script_owner_id)
        file_path = os.path.join(user_folder, file_name)

        if not os.path.exists(file_path):
            bot.answer_callback_query(call.id, f"⚠️ Hata: `{file_name}` dosyası eksik! Yeniden yükleyin.", show_alert=True)
            remove_user_file_db(script_owner_id, file_name); check_files_callback(call); return

        if is_bot_running(script_owner_id, file_name):
            bot.answer_callback_query(call.id, f"⚠️ '{file_name}' betiği zaten çalışıyor.", show_alert=True)
            try: bot.edit_message_reply_markup(chat_id_for_reply, call.message.message_id, reply_markup=create_control_buttons(script_owner_id, file_name, True))
            except Exception as e: logger.error(f"Buton güncelleme hatası (zaten çalışıyor): {e}")
            return

        bot.answer_callback_query(call.id, f"⏳ {file_name} başlatılıyor (kullanıcı {script_owner_id})...")

        if file_type == 'py':
            threading.Thread(target=run_script, args=(file_path, script_owner_id, user_folder, file_name, call.message)).start()
        elif file_type == 'js':
            threading.Thread(target=run_js_script, args=(file_path, script_owner_id, user_folder, file_name, call.message)).start()
        else:
             bot.send_message(chat_id_for_reply, f"❌ Hata: '{file_name}' için bilinmeyen dosya türü '{file_type}'."); return 

        time.sleep(1.5)
        is_now_running = is_bot_running(script_owner_id, file_name) 
        status_text = '🟢 Çalışıyor' if is_now_running else '🟡 Başlatılıyor (veya başarısız, logları/repleri kontrol edin)'
        try:
            bot.edit_message_text(
                f"⚙️ Kontroller: `{file_name}` ({file_type}) (Kullanıcı: `{script_owner_id}`)\nDurum: {status_text}",
                chat_id_for_reply, call.message.message_id,
                reply_markup=create_control_buttons(script_owner_id, file_name, is_now_running), parse_mode='Markdown'
            )
        except telebot.apihelper.ApiTelegramException as e:
             if "message is not modified" in str(e): logger.warning(f"{file_name} başlatıldıktan sonra mesaj değiştirilmedi")
             else: raise
    except (ValueError, IndexError) as e:
        logger.error(f"Başlatma callback ayrıştırma hatası '{call.data}': {e}")
        bot.answer_callback_query(call.id, "Hata: Geçersiz başlatma komutu.", show_alert=True)
    except Exception as e:
        logger.error(f"start_bot_callback için '{call.data}' hatası: {e}", exc_info=True)
        bot.answer_callback_query(call.id, "Betik başlatma hatası.", show_alert=True)
        try:
            _, script_owner_id_err_str, file_name_err = call.data.split('_', 2)
            script_owner_id_err = int(script_owner_id_err_str)
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=create_control_buttons(script_owner_id_err, file_name_err, False))
        except Exception as e_btn: logger.error(f"Başlatma hatası sonrası buton güncelleme başarısız: {e_btn}")

def stop_bot_callback(call):
    try:
        _, script_owner_id_str, file_name = call.data.split('_', 2)
        script_owner_id = int(script_owner_id_str)
        requesting_user_id = call.from_user.id
        chat_id_for_reply = call.message.chat.id

        logger.info(f"Durdurma isteği: İsteyen={requesting_user_id}, Sahip={script_owner_id}, Dosya='{file_name}'")
        if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
            bot.answer_callback_query(call.id, "⚠️ İzin reddedildi.", show_alert=True); return

        user_files_list = user_files.get(script_owner_id, [])
        file_info = next((f for f in user_files_list if f[0] == file_name), None)
        if not file_info:
            bot.answer_callback_query(call.id, "⚠️ Dosya bulunamadı.", show_alert=True); check_files_callback(call); return

        file_type = file_info[1] 
        script_key = f"{script_owner_id}_{file_name}"

        if not is_bot_running(script_owner_id, file_name): 
            bot.answer_callback_query(call.id, f"⚠️ '{file_name}' betiği zaten durdurulmuş.", show_alert=True)
            try:
                 bot.edit_message_text(
                     f"⚙️ Kontroller: `{file_name}` ({file_type}) (Kullanıcı: `{script_owner_id}`)\nDurum: 🔴 Durduruldu",
                     chat_id_for_reply, call.message.message_id,
                     reply_markup=create_control_buttons(script_owner_id, file_name, False), parse_mode='Markdown')
            except Exception as e: logger.error(f"Buton güncelleme hatası (zaten durdurulmuş): {e}")
            return

        bot.answer_callback_query(call.id, f"⏳ {file_name} durduruluyor (kullanıcı {script_owner_id})...")
        process_info = bot_scripts.get(script_key)
        if process_info:
            kill_process_tree(process_info)
            if script_key in bot_scripts: del bot_scripts[script_key]; logger.info(f"Durdurma sonrası {script_key} çalışanlardan kaldırıldı.")
        else: logger.warning(f"{script_key} psutil tarafından çalışıyor görünüyor ancak bot_scripts sözlüğünde yok.")

        try:
            bot.edit_message_text(
                f"⚙️ Kontroller: `{file_name}` ({file_type}) (Kullanıcı: `{script_owner_id}`)\nDurum: 🔴 Durduruldu",
                chat_id_for_reply, call.message.message_id,
                reply_markup=create_control_buttons(script_owner_id, file_name, False), parse_mode='Markdown'
            )
        except telebot.apihelper.ApiTelegramException as e:
             if "message is not modified" in str(e): logger.warning(f"{file_name} durdurulduktan sonra mesaj değiştirilmedi")
             else: raise
    except (ValueError, IndexError) as e:
        logger.error(f"Durdurma callback ayrıştırma hatası '{call.data}': {e}")
        bot.answer_callback_query(call.id, "Hata: Geçersiz durdurma komutu.", show_alert=True)
    except Exception as e:
        logger.error(f"stop_bot_callback için '{call.data}' hatası: {e}", exc_info=True)
        bot.answer_callback_query(call.id, "Betik durdurma hatası.", show_alert=True)

def restart_bot_callback(call):
    try:
        _, script_owner_id_str, file_name = call.data.split('_', 2)
        script_owner_id = int(script_owner_id_str)
        requesting_user_id = call.from_user.id
        chat_id_for_reply = call.message.chat.id

        logger.info(f"Yeniden başlatma: İsteyen={requesting_user_id}, Sahip={script_owner_id}, Dosya='{file_name}'")
        if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
            bot.answer_callback_query(call.id, "⚠️ İzin reddedildi.", show_alert=True); return

        user_files_list = user_files.get(script_owner_id, [])
        file_info = next((f for f in user_files_list if f[0] == file_name), None)
        if not file_info:
            bot.answer_callback_query(call.id, "⚠️ Dosya bulunamadı.", show_alert=True); check_files_callback(call); return

        file_type = file_info[1]; user_folder = get_user_folder(script_owner_id)
        file_path = os.path.join(user_folder, file_name); script_key = f"{script_owner_id}_{file_name}"

        if not os.path.exists(file_path):
            bot.answer_callback_query(call.id, f"⚠️ Hata: `{file_name}` dosyası eksik! Yeniden yükleyin.", show_alert=True)
            remove_user_file_db(script_owner_id, file_name)
            if script_key in bot_scripts: del bot_scripts[script_key]
            check_files_callback(call); return

        bot.answer_callback_query(call.id, f"⏳ {file_name} yeniden başlatılıyor (kullanıcı {script_owner_id})...")
        if is_bot_running(script_owner_id, file_name):
            logger.info(f"Yeniden başlatma: Mevcut {script_key} durduruluyor...")
            process_info = bot_scripts.get(script_key)
            if process_info: kill_process_tree(process_info)
            if script_key in bot_scripts: del bot_scripts[script_key]
            time.sleep(1.5) 

        logger.info(f"Yeniden başlatma: {script_key} betiği başlatılıyor...")
        if file_type == 'py':
            threading.Thread(target=run_script, args=(file_path, script_owner_id, user_folder, file_name, call.message)).start()
        elif file_type == 'js':
            threading.Thread(target=run_js_script, args=(file_path, script_owner_id, user_folder, file_name, call.message)).start()
        else:
             bot.send_message(chat_id_for_reply, f"❌ '{file_name}' için bilinmeyen tür '{file_type}'."); return

        time.sleep(1.5) 
        is_now_running = is_bot_running(script_owner_id, file_name) 
        status_text = '🟢 Çalışıyor' if is_now_running else '🟡 Başlatılıyor (veya başarısız)'
        try:
            bot.edit_message_text(
                f"⚙️ Kontroller: `{file_name}` ({file_type}) (Kullanıcı: `{script_owner_id}`)\nDurum: {status_text}",
                chat_id_for_reply, call.message.message_id,
                reply_markup=create_control_buttons(script_owner_id, file_name, is_now_running), parse_mode='Markdown'
            )
        except telebot.apihelper.ApiTelegramException as e:
             if "message is not modified" in str(e): logger.warning(f"{file_name} yeniden başlatma sonrası mesaj değiştirilmedi")
             else: raise
    except (ValueError, IndexError) as e:
        logger.error(f"Yeniden başlatma callback ayrıştırma hatası '{call.data}': {e}")
        bot.answer_callback_query(call.id, "Hata: Geçersiz yeniden başlatma komutu.", show_alert=True)
    except Exception as e:
        logger.error(f"restart_bot_callback için '{call.data}' hatası: {e}", exc_info=True)
        bot.answer_callback_query(call.id, "Yeniden başlatma hatası.", show_alert=True)
        try:
            _, script_owner_id_err_str, file_name_err = call.data.split('_', 2)
            script_owner_id_err = int(script_owner_id_err_str)
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=create_control_buttons(script_owner_id_err, file_name_err, False))
        except Exception as e_btn: logger.error(f"Yeniden başlatma hatası sonrası buton güncelleme başarısız: {e_btn}")

def delete_bot_callback(call):
    try:
        _, script_owner_id_str, file_name = call.data.split('_', 2)
        script_owner_id = int(script_owner_id_str)
        requesting_user_id = call.from_user.id
        chat_id_for_reply = call.message.chat.id

        logger.info(f"Silme: İsteyen={requesting_user_id}, Sahip={script_owner_id}, Dosya='{file_name}'")
        if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
            bot.answer_callback_query(call.id, "⚠️ İzin reddedildi.", show_alert=True); return

        user_files_list = user_files.get(script_owner_id, [])
        if not any(f[0] == file_name for f in user_files_list):
            bot.answer_callback_query(call.id, "⚠️ Dosya bulunamadı.", show_alert=True); check_files_callback(call); return

        bot.answer_callback_query(call.id, f"🗑️ {file_name} siliniyor (kullanıcı {script_owner_id})...")
        script_key = f"{script_owner_id}_{file_name}"
        if is_bot_running(script_owner_id, file_name):
            logger.info(f"Silme: {script_key} durduruluyor...")
            process_info = bot_scripts.get(script_key)
            if process_info: kill_process_tree(process_info)
            if script_key in bot_scripts: del bot_scripts[script_key]
            time.sleep(0.5) 

        user_folder = get_user_folder(script_owner_id)
        file_path = os.path.join(user_folder, file_name)
        log_path = os.path.join(user_folder, f"{os.path.splitext(file_name)[0]}.log")
        deleted_disk = []
        if os.path.exists(file_path):
            try: os.remove(file_path); deleted_disk.append(file_name); logger.info(f"Dosya silindi: {file_path}")
            except OSError as e: logger.error(f"{file_path} silinirken hata: {e}")
        if os.path.exists(log_path):
            try: os.remove(log_path); deleted_disk.append(os.path.basename(log_path)); logger.info(f"Log silindi: {log_path}")
            except OSError as e: logger.error(f"Log {log_path} silinirken hata: {e}")

        remove_user_file_db(script_owner_id, file_name)
        deleted_str = ", ".join(f"`{f}`" for f in deleted_disk) if deleted_disk else "ilişkili dosyalar"
        try:
            bot.edit_message_text(
                f"🗑️ `{file_name}` kaydı (Kullanıcı `{script_owner_id}`) ve {deleted_str} silindi!",
                chat_id_for_reply, call.message.message_id, reply_markup=None, parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Silme sonrası mesaj düzenleme hatası: {e}")
            bot.send_message(chat_id_for_reply, f"🗑️ `{file_name}` kaydı silindi.", parse_mode='Markdown')
    except (ValueError, IndexError) as e:
        logger.error(f"Silme callback ayrıştırma hatası '{call.data}': {e}")
        bot.answer_callback_query(call.id, "Hata: Geçersiz silme komutu.", show_alert=True)
    except Exception as e:
        logger.error(f"delete_bot_callback için '{call.data}' hatası: {e}", exc_info=True)
        bot.answer_callback_query(call.id, "Silme hatası.", show_alert=True)

def logs_bot_callback(call):
    try:
        _, script_owner_id_str, file_name = call.data.split('_', 2)
        script_owner_id = int(script_owner_id_str)
        requesting_user_id = call.from_user.id
        chat_id_for_reply = call.message.chat.id

        logger.info(f"Loglar: İsteyen={requesting_user_id}, Sahip={script_owner_id}, Dosya='{file_name}'")
        if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
            bot.answer_callback_query(call.id, "⚠️ İzin reddedildi.", show_alert=True); return

        user_files_list = user_files.get(script_owner_id, [])
        if not any(f[0] == file_name for f in user_files_list):
            bot.answer_callback_query(call.id, "⚠️ Dosya bulunamadı.", show_alert=True); check_files_callback(call); return

        user_folder = get_user_folder(script_owner_id)
        log_path = os.path.join(user_folder, f"{os.path.splitext(file_name)[0]}.log")
        if not os.path.exists(log_path):
            bot.answer_callback_query(call.id, f"⚠️ '{file_name}' için log yok.", show_alert=True); return

        bot.answer_callback_query(call.id) 
        try:
            log_content = ""; file_size = os.path.getsize(log_path)
            max_log_kb = 100; max_tg_msg = 4096
            if file_size == 0: log_content = "(Log boş)"
            elif file_size > max_log_kb * 1024:
                 with open(log_path, 'rb') as f: f.seek(-max_log_kb * 1024, os.SEEK_END); log_bytes = f.read()
                 log_content = log_bytes.decode('utf-8', errors='ignore')
                 log_content = f"(Son {max_log_kb} KB)\n...\n" + log_content
            else:
                 with open(log_path, 'r', encoding='utf-8', errors='ignore') as f: log_content = f.read()

            if len(log_content) > max_tg_msg:
                log_content = log_content[-max_tg_msg:]
                first_nl = log_content.find('\n')
                if first_nl != -1: log_content = "...\n" + log_content[first_nl+1:]
                else: log_content = "...\n" + log_content 
            if not log_content.strip(): log_content = "(Görünür içerik yok)"

            bot.send_message(chat_id_for_reply, f"📜 `{file_name}` için loglar (Kullanıcı `{script_owner_id}`):\n```\n{log_content}\n```", parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Log {log_path} okuma/gönderme hatası: {e}", exc_info=True)
            bot.send_message(chat_id_for_reply, f"❌ `{file_name}` için log okunurken hata oluştu.")
    except (ValueError, IndexError) as e:
        logger.error(f"Loglar callback ayrıştırma hatası '{call.data}': {e}")
        bot.answer_callback_query(call.id, "Hata: Geçersiz loglar komutu.", show_alert=True)
    except Exception as e:
        logger.error(f"logs_bot_callback için '{call.data}' hatası: {e}", exc_info=True)
        bot.answer_callback_query(call.id, "Loglar alınırken hata.", show_alert=True)

def speed_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    start_cb_ping_time = time.time() 
    try:
        bot.edit_message_text("🏃 Hız test ediliyor...", chat_id, call.message.message_id)
        bot.send_chat_action(chat_id, 'typing') 
        response_time = round((time.time() - start_cb_ping_time) * 1000, 2)
        status = "🔓 Kilit Açık" if not bot_locked else "🔒 Kilitli"
        if user_id == OWNER_ID: user_level = "👑 Sahip"
        elif user_id in admin_ids: user_level = "🛡️ Yönetici"
        elif user_id in user_subscriptions and user_subscriptions[user_id].get('expiry', datetime.min) > datetime.now(): user_level = "⭐ Premium"
        else: user_level = "🆓 Ücretsiz Kullanıcı"
        speed_msg = (f"⚡ Bot Hızı ve Durumu:\n\n⏱️ API Yanıt Süresi: {response_time} ms\n"
                     f"🚦 Bot Durumu: {status}\n"
                     f"👤 Seviyeniz: {user_level}")
        bot.answer_callback_query(call.id) 
        bot.edit_message_text(speed_msg, chat_id, call.message.message_id, reply_markup=create_main_menu_inline(user_id))
    except Exception as e:
         logger.error(f"Hız testi sırasında hata (cb): {e}", exc_info=True)
         bot.answer_callback_query(call.id, "Hız testinde hata oluştu.", show_alert=True)
         try: bot.edit_message_text("〽️ Ana Menü", chat_id, call.message.message_id, reply_markup=create_main_menu_inline(user_id))
         except Exception: pass

def back_to_main_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    file_limit = get_user_file_limit(user_id)
    current_files = get_user_file_count(user_id)
    limit_str = str(file_limit) if file_limit != float('inf') else "Sınırsız"
    expiry_info = ""
    if user_id == OWNER_ID: user_status = "👑 Sahip"
    elif user_id in admin_ids: user_status = "🛡️ Yönetici"
    elif user_id in user_subscriptions:
        expiry_date = user_subscriptions[user_id].get('expiry')
        if expiry_date and expiry_date > datetime.now():
            user_status = "⭐ Premium"; days_left = (expiry_date - datetime.now()).days
            expiry_info = f"\n⏳ Abonelik bitiş: {days_left} gün kaldı"
        else: user_status = "🆓 Ücretsiz Kullanıcı (Süresi Dolmuş)"
    else: user_status = "🆓 Ücretsiz Kullanıcı"
    main_menu_text = (f"〽️ Tekrar hoş geldin, {call.from_user.first_name}!\n\n🆔 ID: `{user_id}`\n"
                      f"🔰 Durum: {user_status}{expiry_info}\n📁 Dosyalar: {current_files} / {limit_str}\n\n"
                      f"👇 Butonları kullanın veya komut yazın.")
    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(main_menu_text, chat_id, call.message.message_id,
                              reply_markup=create_main_menu_inline(user_id), parse_mode='Markdown')
    except telebot.apihelper.ApiTelegramException as e:
         if "message is not modified" in str(e): logger.warning("Mesaj değiştirilmedi (ana menüye dön).")
         else: logger.error(f"ana menüye dön API hatası: {e}")
    except Exception as e: logger.error(f"ana menüye dön işlenirken hata: {e}", exc_info=True)

# --- Admin Callback Implementations ---
def subscription_management_callback(call):
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_text("💳 Abonelik Yönetimi\nİşlem seçin:",
                              call.message.chat.id, call.message.message_id, reply_markup=create_subscription_menu())
    except Exception as e: logger.error(f"Abonelik menüsü gösterilirken hata: {e}")

def stats_callback(call):
    bot.answer_callback_query(call.id)
    _logic_statistics(call.message)
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id,
                                      reply_markup=create_main_menu_inline(call.from_user.id))
    except Exception as e:
        logger.error(f"stats_callback sonrası menü güncelleme hatası: {e}")

def lock_bot_callback(call):
    global bot_locked; bot_locked = True
    logger.warning(f"Bot Yönetici {call.from_user.id} tarafından kilitlendi")
    bot.answer_callback_query(call.id, "🔒 Bot kilitlendi.")
    try: bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=create_main_menu_inline(call.from_user.id))
    except Exception as e: logger.error(f"Menü güncelleme hatası (kilit): {e}")

def unlock_bot_callback(call):
    global bot_locked; bot_locked = False
    logger.warning(f"Bot Yönetici {call.from_user.id} tarafından kilidi açıldı")
    bot.answer_callback_query(call.id, "🔓 Bot kilidi açıldı.")
    try: bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=create_main_menu_inline(call.from_user.id))
    except Exception as e: logger.error(f"Menü güncelleme hatası (kilit açma): {e}")

def run_all_scripts_callback(call):
    _logic_run_all_scripts(call)

def broadcast_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "📢 Duyuru mesajını gönderin.\n/cancel ile iptal edin.")
    bot.register_next_step_handler(msg, process_broadcast_message)

def process_broadcast_message(message):
    user_id = message.from_user.id
    if user_id not in admin_ids: bot.reply_to(message, "⚠️ Yetkili değil."); return
    if message.text and message.text.lower() == '/cancel': bot.reply_to(message, "Duyuru iptal edildi."); return

    broadcast_content = message.text
    if not broadcast_content and not (message.photo or message.video or message.document or message.sticker or message.voice or message.audio):
         bot.reply_to(message, "⚠️ Boş mesaj duyurulamaz. Metin veya medya gönderin, veya /cancel.")
         msg = bot.send_message(message.chat.id, "📢 Duyuru mesajını gönderin veya /cancel.")
         bot.register_next_step_handler(msg, process_broadcast_message)
         return

    target_count = len(active_users)
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("✅ Onayla ve Gönder", callback_data=f"confirm_broadcast_{message.message_id}"),
               types.InlineKeyboardButton("❌ İptal", callback_data="cancel_broadcast"))

    preview_text = broadcast_content[:1000].strip() if broadcast_content else "(Medya mesajı)"
    bot.reply_to(message, f"⚠️ Duyuruyu Onaylayın:\n\n```\n{preview_text}\n```\n" 
                          f"**{target_count}** kullanıcıya gönderilecek. Emin misiniz?", reply_markup=markup, parse_mode='Markdown')

def handle_confirm_broadcast(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    if user_id not in admin_ids: bot.answer_callback_query(call.id, "⚠️ Sadece yönetici.", show_alert=True); return
    try:
        original_message = call.message.reply_to_message
        if not original_message: raise ValueError("Orijinal mesaj alınamadı.")

        broadcast_text = None
        broadcast_photo_id = None
        broadcast_video_id = None

        if original_message.text:
            broadcast_text = original_message.text
        elif original_message.photo:
            broadcast_photo_id = original_message.photo[-1].file_id
        elif original_message.video:
            broadcast_video_id = original_message.video.file_id
        else:
            raise ValueError("Duyuru için mesajda metin veya desteklenen medya yok.")

        bot.answer_callback_query(call.id, "🚀 Duyuru başlatılıyor...")
        bot.edit_message_text(f"📢 {len(active_users)} kullanıcıya duyuru yapılıyor...",
                              chat_id, call.message.message_id, reply_markup=None)
        thread = threading.Thread(target=execute_broadcast, args=(
            broadcast_text, broadcast_photo_id, broadcast_video_id, 
            original_message.caption if (broadcast_photo_id or broadcast_video_id) else None,
            chat_id))
        thread.start()
    except ValueError as ve: 
        logger.error(f"Duyuru onayı için mesaj alınırken hata: {ve}")
        bot.edit_message_text(f"❌ Duyuru başlatma hatası: {ve}", chat_id, call.message.message_id, reply_markup=None)
    except Exception as e:
        logger.error(f"handle_confirm_broadcast hatası: {e}", exc_info=True)
        bot.edit_message_text("❌ Duyuru onayı sırasında beklenmeyen hata.", chat_id, call.message.message_id, reply_markup=None)

def handle_cancel_broadcast(call):
    bot.answer_callback_query(call.id, "Duyuru iptal edildi.")
    bot.delete_message(call.message.chat.id, call.message.message_id)
    if call.message.reply_to_message:
        try: bot.delete_message(call.message.chat.id, call.message.reply_to_message.message_id)
        except: pass

def execute_broadcast(broadcast_text, photo_id, video_id, caption, admin_chat_id):
    sent_count = 0; failed_count = 0; blocked_count = 0
    start_exec_time = time.time() 
    users_to_broadcast = list(active_users); total_users = len(users_to_broadcast)
    logger.info(f"{total_users} kullanıcıya duyuru yapılıyor.")
    batch_size = 25; delay_batches = 1.5

    for i, user_id_bc in enumerate(users_to_broadcast):
        try:
            if broadcast_text:
                bot.send_message(user_id_bc, broadcast_text, parse_mode='Markdown')
            elif photo_id:
                bot.send_photo(user_id_bc, photo_id, caption=caption, parse_mode='Markdown' if caption else None)
            elif video_id:
                bot.send_video(user_id_bc, video_id, caption=caption, parse_mode='Markdown' if caption else None)
            sent_count += 1
        except telebot.apihelper.ApiTelegramException as e:
            err_desc = str(e).lower()
            if any(s in err_desc for s in ["bot was blocked", "user is deactivated", "chat not found", "kicked from", "restricted"]): 
                logger.warning(f"{user_id_bc} adresine duyuru başarısız: Kullanıcı engellemiş/aktif değil.")
                blocked_count += 1
            elif "flood control" in err_desc or "too many requests" in err_desc:
                retry_after = 5; match = re.search(r"retry after (\d+)", err_desc)
                if match: retry_after = int(match.group(1)) + 1 
                logger.warning(f"Flood kontrolü. {retry_after}s bekleniyor...")
                time.sleep(retry_after)
                try:
                    if broadcast_text: bot.send_message(user_id_bc, broadcast_text, parse_mode='Markdown')
                    elif photo_id: bot.send_photo(user_id_bc, photo_id, caption=caption, parse_mode='Markdown' if caption else None)
                    elif video_id: bot.send_video(user_id_bc, video_id, caption=caption, parse_mode='Markdown' if caption else None)
                    sent_count += 1
                except Exception as e_retry: logger.error(f"{user_id_bc} adresine duyuru yeniden denemesi başarısız: {e_retry}"); failed_count +=1
            else: logger.error(f"{user_id_bc} adresine duyuru başarısız: {e}"); failed_count += 1
        except Exception as e: logger.error(f"{user_id_bc} adresine duyuru yapılırken beklenmeyen hata: {e}"); failed_count += 1

        if (i + 1) % batch_size == 0 and i < total_users - 1:
            logger.info(f"Duyuru partisi {i//batch_size + 1} gönderildi. {delay_batches}s bekleniyor...")
            time.sleep(delay_batches)
        elif i % 5 == 0: time.sleep(0.2) 

    duration = round(time.time() - start_exec_time, 2)
    result_msg = (f"📢 Duyuru Tamamlandı!\n\n✅ Gönderilen: {sent_count}\n❌ Başarısız: {failed_count}\n"
                  f"🚫 Engellenen/Aktif Olmayan: {blocked_count}\n👥 Hedef: {total_users}\n⏱️ Süre: {duration}s")
    logger.info(result_msg)
    try: bot.send_message(admin_chat_id, result_msg)
    except Exception as e: logger.error(f"Duyuru sonucu yöneticiye {admin_chat_id} gönderilemedi: {e}")

def admin_panel_callback(call):
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_text("👑 Yönetici Paneli\nYöneticileri yönetin (Sahip işlemleri kısıtlı olabilir).",
                              call.message.chat.id, call.message.message_id, reply_markup=create_admin_panel())
    except Exception as e: logger.error(f"Yönetici paneli gösterilirken hata: {e}")

def add_admin_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "👑 Yönetici yapılacak Kullanıcı ID'sini girin.\n/cancel ile iptal edin.")
    bot.register_next_step_handler(msg, process_add_admin_id)

def process_add_admin_id(message):
    owner_id_check = message.from_user.id 
    if owner_id_check != OWNER_ID: bot.reply_to(message, "⚠️ Sadece sahip."); return
    if message.text.lower() == '/cancel': bot.reply_to(message, "Yönetici ekleme iptal edildi."); return
    try:
        new_admin_id = int(message.text.strip())
        if new_admin_id <= 0: raise ValueError("ID pozitif olmalı")
        if new_admin_id == OWNER_ID: bot.reply_to(message, "⚠️ Sahip zaten sahiptir."); return
        if new_admin_id in admin_ids: bot.reply_to(message, f"⚠️ Kullanıcı `{new_admin_id}` zaten yönetici."); return
        add_admin_db(new_admin_id) 
        logger.warning(f"Yönetici {new_admin_id} Sahip {owner_id_check} tarafından eklendi.")
        bot.reply_to(message, f"✅ Kullanıcı `{new_admin_id}` yönetici yapıldı.")
        try: bot.send_message(new_admin_id, "🎉 Tebrikler! Artık yöneticisiniz.")
        except Exception as e: logger.error(f"Yeni yönetici {new_admin_id} bilgilendirilemedi: {e}")
    except ValueError:
        bot.reply_to(message, "⚠️ Geçersiz ID. Sayısal ID girin veya /cancel.")
        msg = bot.send_message(message.chat.id, "👑 Yönetici yapılacak Kullanıcı ID'sini girin veya /cancel.")
        bot.register_next_step_handler(msg, process_add_admin_id)
    except Exception as e: logger.error(f"Yönetici ekleme işlenirken hata: {e}", exc_info=True); bot.reply_to(message, "Hata.")

def remove_admin_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "👑 Kaldırılacak Yönetici Kullanıcı ID'sini girin.\n/cancel ile iptal edin.")
    bot.register_next_step_handler(msg, process_remove_admin_id)

def process_remove_admin_id(message):
    owner_id_check = message.from_user.id
    if owner_id_check != OWNER_ID: bot.reply_to(message, "⚠️ Sadece sahip."); return
    if message.text.lower() == '/cancel': bot.reply_to(message, "Yönetici kaldırma iptal edildi."); return
    try:
        admin_id_remove = int(message.text.strip())
        if admin_id_remove <= 0: raise ValueError("ID pozitif olmalı")
        if admin_id_remove == OWNER_ID: bot.reply_to(message, "⚠️ Sahip kendini kaldıramaz."); return
        if admin_id_remove not in admin_ids: bot.reply_to(message, f"⚠️ Kullanıcı `{admin_id_remove}` yönetici değil."); return
        if remove_admin_db(admin_id_remove): 
            logger.warning(f"Yönetici {admin_id_remove} Sahip {owner_id_check} tarafından kaldırıldı.")
            bot.reply_to(message, f"✅ Yönetici `{admin_id_remove}` kaldırıldı.")
            try: bot.send_message(admin_id_remove, "ℹ️ Artık yönetici değilsiniz.")
            except Exception as e: logger.error(f"Kaldırılan yönetici {admin_id_remove} bilgilendirilemedi: {e}")
        else: bot.reply_to(message, f"❌ Yönetici `{admin_id_remove}` kaldırılamadı. Logları kontrol edin.")
    except ValueError:
        bot.reply_to(message, "⚠️ Geçersiz ID. Sayısal ID girin veya /cancel.")
        msg = bot.send_message(message.chat.id, "👑 Kaldırılacak Yönetici ID'sini girin veya /cancel.")
        bot.register_next_step_handler(msg, process_remove_admin_id)
    except Exception as e: logger.error(f"Yönetici kaldırma işlenirken hata: {e}", exc_info=True); bot.reply_to(message, "Hata.")

def list_admins_callback(call):
    bot.answer_callback_query(call.id)
    try:
        admin_list_str = "\n".join(f"- `{aid}` {'(Sahip)' if aid == OWNER_ID else ''}" for aid in sorted(list(admin_ids)))
        if not admin_list_str: admin_list_str = "(Sahip/Yönetici yapılandırılmamış!)"
        bot.edit_message_text(f"👑 Mevcut Yöneticiler:\n\n{admin_list_str}", call.message.chat.id,
                              call.message.message_id, reply_markup=create_admin_panel(), parse_mode='Markdown')
    except Exception as e: logger.error(f"Yöneticiler listelenirken hata: {e}")

def add_subscription_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "💳 Kullanıcı ID ve gün sayısını girin (örn: `12345678 30`).\n/cancel ile iptal edin.")
    bot.register_next_step_handler(msg, process_add_subscription_details)

def process_add_subscription_details(message):
    admin_id_check = message.from_user.id 
    if admin_id_check not in admin_ids: bot.reply_to(message, "⚠️ Yetkili değil."); return
    if message.text.lower() == '/cancel': bot.reply_to(message, "Abonelik ekleme iptal edildi."); return
    try:
        parts = message.text.split();
        if len(parts) != 2: raise ValueError("Yanlış format")
        sub_user_id = int(parts[0].strip()); days = int(parts[1].strip())
        if sub_user_id <= 0 or days <= 0: raise ValueError("Kullanıcı ID/gün sayısı pozitif olmalı")

        current_expiry = user_subscriptions.get(sub_user_id, {}).get('expiry')
        start_date_new_sub = datetime.now()
        if current_expiry and current_expiry > start_date_new_sub: start_date_new_sub = current_expiry
        new_expiry = start_date_new_sub + timedelta(days=days)
        save_subscription(sub_user_id, new_expiry)

        logger.info(f"{sub_user_id} için abonelik yönetici {admin_id_check} tarafından eklendi. Bitiş: {new_expiry:%Y-%m-%d}")
        bot.reply_to(message, f"✅ `{sub_user_id}` için {days} günlük abonelik eklendi.\nYeni bitiş: {new_expiry:%Y-%m-%d}")
        try: bot.send_message(sub_user_id, f"🎉 Aboneliğiniz {days} gün uzatıldı/eklendi! Bitiş: {new_expiry:%Y-%m-%d}.")
        except Exception as e: logger.error(f"{sub_user_id} kullanıcısına yeni abonelik bildirilemedi: {e}")
    except ValueError as e:
        bot.reply_to(message, f"⚠️ Geçersiz: {e}. Format: `ID gün` veya /cancel.")
        msg = bot.send_message(message.chat.id, "💳 Kullanıcı ID ve gün sayısını girin, veya /cancel.")
        bot.register_next_step_handler(msg, process_add_subscription_details)
    except Exception as e: logger.error(f"Abonelik ekleme işlenirken hata: {e}", exc_info=True); bot.reply_to(message, "Hata.")

def remove_subscription_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "💳 Aboneliği kaldırılacak Kullanıcı ID'sini girin.\n/cancel ile iptal edin.")
    bot.register_next_step_handler(msg, process_remove_subscription_id)

def process_remove_subscription_id(message):
    admin_id_check = message.from_user.id
    if admin_id_check not in admin_ids: bot.reply_to(message, "⚠️ Yetkili değil."); return
    if message.text.lower() == '/cancel': bot.reply_to(message, "Abonelik kaldırma iptal edildi."); return
    try:
        sub_user_id_remove = int(message.text.strip())
        if sub_user_id_remove <= 0: raise ValueError("ID pozitif olmalı")
        if sub_user_id_remove not in user_subscriptions:
            bot.reply_to(message, f"⚠️ Kullanıcı `{sub_user_id_remove}` için bellekte aktif abonelik yok."); return
        remove_subscription_db(sub_user_id_remove) 
        logger.warning(f"{sub_user_id_remove} için abonelik yönetici {admin_id_check} tarafından kaldırıldı.")
        bot.reply_to(message, f"✅ `{sub_user_id_remove}` için abonelik kaldırıldı.")
        try: bot.send_message(sub_user_id_remove, "ℹ️ Aboneliğiniz yönetici tarafından kaldırıldı.")
        except Exception as e: logger.error(f"{sub_user_id_remove} kullanıcısına abonelik kaldırma bildirilemedi: {e}")
    except ValueError:
        bot.reply_to(message, "⚠️ Geçersiz ID. Sayısal ID girin veya /cancel.")
        msg = bot.send_message(message.chat.id, "💳 Aboneliği kaldırılacak Kullanıcı ID'sini girin, veya /cancel.")
        bot.register_next_step_handler(msg, process_remove_subscription_id)
    except Exception as e: logger.error(f"Abonelik kaldırma işlenirken hata: {e}", exc_info=True); bot.reply_to(message, "Hata.")

def check_subscription_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "💳 Aboneliği sorgulanacak Kullanıcı ID'sini girin.\n/cancel ile iptal edin.")
    bot.register_next_step_handler(msg, process_check_subscription_id)

def process_check_subscription_id(message):
    admin_id_check = message.from_user.id
    if admin_id_check not in admin_ids: bot.reply_to(message, "⚠️ Yetkili değil."); return
    if message.text.lower() == '/cancel': bot.reply_to(message, "Abonelik sorgulama iptal edildi."); return
    try:
        sub_user_id_check = int(message.text.strip())
        if sub_user_id_check <= 0: raise ValueError("ID pozitif olmalı")
        if sub_user_id_check in user_subscriptions:
            expiry_dt = user_subscriptions[sub_user_id_check].get('expiry')
            if expiry_dt:
                if expiry_dt > datetime.now():
                    days_left = (expiry_dt - datetime.now()).days
                    bot.reply_to(message, f"✅ Kullanıcı `{sub_user_id_check}` aktif aboneliğe sahip.\nBitiş: {expiry_dt:%Y-%m-%d %H:%M:%S} ({days_left} gün kaldı).")
                else:
                    bot.reply_to(message, f"⚠️ Kullanıcı `{sub_user_id_check}` süresi dolmuş abonelik (Tarih: {expiry_dt:%Y-%m-%d %H:%M:%S}).")
                    remove_subscription_db(sub_user_id_check)
            else: bot.reply_to(message, f"⚠️ Kullanıcı `{sub_user_id_check}` abonelik listesinde ancak bitiş tarihi eksik. Gerekirse yeniden ekleyin.")
        else: bot.reply_to(message, f"ℹ️ Kullanıcı `{sub_user_id_check}` için aktif abonelik kaydı yok.")
    except ValueError:
        bot.reply_to(message, "⚠️ Geçersiz ID. Sayısal ID girin veya /cancel.")
        msg = bot.send_message(message.chat.id, "💳 Sorgulanacak Kullanıcı ID'sini girin, veya /cancel.")
        bot.register_next_step_handler(msg, process_check_subscription_id)
    except Exception as e: logger.error(f"Abonelik sorgulama işlenirken hata: {e}", exc_info=True); bot.reply_to(message, "Hata.")

# --- Cleanup Function ---
def cleanup():
    logger.warning("Kapatılıyor. İşlemler temizleniyor...")
    script_keys_to_stop = list(bot_scripts.keys()) 
    if not script_keys_to_stop: logger.info("Çalışan betik yok. Çıkılıyor."); return
    logger.info(f"{len(script_keys_to_stop)} betik durduruluyor...")
    for key in script_keys_to_stop:
        if key in bot_scripts: logger.info(f"Durduruluyor: {key}"); kill_process_tree(bot_scripts[key])
        else: logger.info(f"{key} betiği zaten kaldırılmış.")
    logger.warning("Temizlik tamamlandı.")
atexit.register(cleanup)

# --- Main Execution ---
if __name__ == '__main__':
    logger.info("="*40 + "\n🤖 Bot Başlatılıyor...\n" + f"🐍 Python: {sys.version.split()[0]}\n" +
                f"🔧 Ana Dizin: {BASE_DIR}\n📁 Yükleme Dizini: {UPLOAD_BOTS_DIR}\n" +
                f"📊 Veri Dizini: {IROTECH_DIR}\n🔑 Sahip ID: {OWNER_ID}\n🛡️ Yöneticiler: {admin_ids}\n" + "="*40)
    canli_tut()
    logger.info("🚀 Polling başlatılıyor...")
    while True:
        try:
            bot.infinity_polling(logger_level=logging.INFO, timeout=60, long_polling_timeout=30)
        except requests.exceptions.ReadTimeout: logger.warning("Polling ReadTimeout. 5sn içinde yeniden başlatılıyor..."); time.sleep(5)
        except requests.exceptions.ConnectionError as ce: logger.error(f"Polling Bağlantı Hatası: {ce}. 15sn içinde yeniden deneniyor..."); time.sleep(15)
        except Exception as e:
            logger.critical(f"💥 Kurtarılamaz polling hatası: {e}", exc_info=True)
            logger.info("Kritik hata nedeniyle polling 30sn içinde yeniden başlatılıyor..."); time.sleep(30)
        finally: logger.warning("Polling denemesi tamamlandı. Döngüde yeniden başlatılacak."); time.sleep(1)