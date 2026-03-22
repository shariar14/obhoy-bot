"""
╔══════════════════════════════════════════════════════════════╗
║         OBHOY BOT — সম্পূর্ণ সংস্করণ v3                    ║
║  ৫টি বিভাগ: আইন • FIR PDF • আইনজীবী • হেল্পলাইন • ডেটাবেজ  ║
║         obhoy.com | @ObhoyBDbot                              ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import io
import logging
import urllib.request
from datetime import datetime, date, timedelta

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler,
)

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ─────────────────────────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────────────────────────
TOKEN          = os.environ.get("TOKEN")
DATABASE_URL   = os.environ.get("DATABASE_URL")       # Railway PostgreSQL
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "obhoy@admin2026")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────
#  DATABASE — PostgreSQL (Railway) অথবা SQLite (local)
# ─────────────────────────────────────────────────────────────────

USE_PG = bool(DATABASE_URL)

if USE_PG:
    import psycopg2
    import psycopg2.extras
else:
    import sqlite3

def get_conn():
    if USE_PG:
        return psycopg2.connect(DATABASE_URL, sslmode="require")
    else:
        return sqlite3.connect("obhoy.db")

def setup_db():
    conn = get_conn()
    cur  = conn.cursor()
    if USE_PG:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id          SERIAL PRIMARY KEY,
                division    TEXT NOT NULL,
                district    TEXT NOT NULL,
                upazila     TEXT DEFAULT '',
                case_type   TEXT NOT NULL,
                inc_date    DATE NOT NULL,
                description TEXT DEFAULT '',
                source      TEXT DEFAULT 'admin',
                created_at  TIMESTAMP DEFAULT NOW()
            )
        """)
    else:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                division    TEXT NOT NULL,
                district    TEXT NOT NULL,
                upazila     TEXT DEFAULT '',
                case_type   TEXT NOT NULL,
                inc_date    TEXT NOT NULL,
                description TEXT DEFAULT '',
                source      TEXT DEFAULT 'admin',
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)
    conn.commit()
    cur.close()
    conn.close()
    logger.info("Database প্রস্তুত ✅")

def add_incident(division, district, upazila, case_type, inc_date, description, source="admin"):
    conn = get_conn()
    cur  = conn.cursor()
    if USE_PG:
        cur.execute(
            "INSERT INTO incidents (division,district,upazila,case_type,inc_date,description,source) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (division, district, upazila, case_type, inc_date, description, source)
        )
    else:
        cur.execute(
            "INSERT INTO incidents (division,district,upazila,case_type,inc_date,description,source) "
            "VALUES (?,?,?,?,?,?,?)",
            (division, district, upazila, case_type, str(inc_date), description, source)
        )
    conn.commit()
    cur.close()
    conn.close()

def search_incidents(division=None, district=None, case_type=None, days=30):
    conn    = get_conn()
    cur     = conn.cursor()
    cutoff  = (date.today() - timedelta(days=days)).isoformat()
    clauses = ["inc_date >= %s" if USE_PG else "inc_date >= ?"]
    params  = [cutoff]
    if division:
        clauses.append("%s" if not USE_PG else "%s")
        clauses[-1] = ("division = %s" if USE_PG else "division = ?")
        params.append(division)
    if district:
        clauses.append("district = %s" if USE_PG else "district = ?")
        params.append(district)
    if case_type:
        clauses.append("case_type = %s" if USE_PG else "case_type = ?")
        params.append(case_type)
    sql = "SELECT division,district,upazila,case_type,inc_date,description FROM incidents"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY inc_date DESC LIMIT 20"
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def count_incidents(division=None, days=30):
    conn   = get_conn()
    cur    = conn.cursor()
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    p      = "%s" if USE_PG else "?"
    if division:
        cur.execute(f"SELECT COUNT(*) FROM incidents WHERE inc_date>={p} AND division={p}",
                    [cutoff, division])
    else:
        cur.execute(f"SELECT COUNT(*) FROM incidents WHERE inc_date>={p}", [cutoff])
    n = cur.fetchone()[0]
    cur.close()
    conn.close()
    return n

# ─────────────────────────────────────────────────────────────────
#  FONT SETUP FOR PDF
# ─────────────────────────────────────────────────────────────────
FONT_PATH     = "/tmp/NotoSansBengali.ttf"
FONT_BOLD_PATH= "/tmp/NotoSansBengaliBold.ttf"
FONT_URL      = "https://cdn.jsdelivr.net/gh/googlefonts/noto-fonts/hinted/ttf/NotoSansBengali/NotoSansBengali-Regular.ttf"
FONT_BOLD_URL = "https://cdn.jsdelivr.net/gh/googlefonts/noto-fonts/hinted/ttf/NotoSansBengali/NotoSansBengali-Bold.ttf"
FONT_READY    = False

def setup_fonts():
    global FONT_READY
    try:
        if not os.path.exists(FONT_PATH):
            urllib.request.urlretrieve(FONT_URL, FONT_PATH)
        if not os.path.exists(FONT_BOLD_PATH):
            urllib.request.urlretrieve(FONT_BOLD_URL, FONT_BOLD_PATH)
        pdfmetrics.registerFont(TTFont("Bengali",      FONT_PATH))
        pdfmetrics.registerFont(TTFont("Bengali-Bold", FONT_BOLD_PATH))
        FONT_READY = True
        logger.info("Bengali ফন্ট প্রস্তুত ✅")
    except Exception as e:
        logger.warning(f"ফন্ট লোড ব্যর্থ: {e}")
        FONT_READY = False

setup_fonts()

def BN():   return "Bengali"      if FONT_READY else "Helvetica"
def BNB():  return "Bengali-Bold" if FONT_READY else "Helvetica-Bold"

# ─────────────────────────────────────────────────────────────────
#  CONVERSATION STATES
# ─────────────────────────────────────────────────────────────────
MAIN_MENU    = 0
LAW_MENU     = 1
HELP_DIST    = 2

FIR_NAME     = 10
FIR_FATHER   = 11
FIR_MOTHER   = 12
FIR_AGE      = 13
FIR_NID      = 14
FIR_PADDR    = 15
FIR_CADDR    = 16
FIR_MOBILE   = 17
FIR_STATION  = 18
FIR_DIST_F   = 19
FIR_IDATE    = 20
FIR_ITIME    = 21
FIR_ILOC     = 22
FIR_REL      = 23
FIR_DESC     = 24
FIR_WITNESS  = 25
FIR_CONFIRM  = 26

LAW_DIST     = 30
LAW_TYPE     = 31

SRCH_DIV     = 40
SRCH_DIST    = 41
SRCH_TYPE    = 42
SRCH_DAYS    = 43

ADMIN_PASS   = 50
ADMIN_DIV    = 51
ADMIN_DIST_A = 52
ADMIN_UPZ    = 53
ADMIN_TYPE_A = 54
ADMIN_DATE_A = 55
ADMIN_DESC_A = 56
ADMIN_CONF_A = 57

# ─────────────────────────────────────────────────────────────────
#  STATIC DATA
# ─────────────────────────────────────────────────────────────────

DIVISIONS = ["ঢাকা","চট্টগ্রাম","রাজশাহী","খুলনা","সিলেট","বরিশাল","ময়মনসিংহ","রংপুর"]

DISTRICTS = {
    "ঢাকা":       ["ঢাকা","গাজীপুর","নারায়ণগঞ্জ","মুন্সিগঞ্জ","মানিকগঞ্জ","টাঙ্গাইল","কিশোরগঞ্জ","নরসিংদী","ফরিদপুর","মাদারীপুর","শরীয়তপুর","রাজবাড়ী","গোপালগঞ্জ"],
    "চট্টগ্রাম":  ["চট্টগ্রাম","কক্সবাজার","বান্দরবান","রাঙ্গামাটি","খাগড়াছড়ি","ফেনী","লক্ষ্মীপুর","নোয়াখালী","কুমিল্লা","চাঁদপুর","ব্রাহ্মণবাড়িয়া"],
    "রাজশাহী":    ["রাজশাহী","চাঁপাইনবাবগঞ্জ","নওগাঁ","নাটোর","বগুড়া","জয়পুরহাট","সিরাজগঞ্জ","পাবনা"],
    "খুলনা":      ["খুলনা","বাগেরহাট","সাতক্ষীরা","যশোর","ঝিনাইদহ","মাগুরা","নড়াইল","কুষ্টিয়া","চুয়াডাঙ্গা","মেহেরপুর"],
    "সিলেট":      ["সিলেট","মৌলভীবাজার","হবিগঞ্জ","সুনামগঞ্জ"],
    "বরিশাল":     ["বরিশাল","পটুয়াখালী","ভোলা","পিরোজপুর","ঝালকাঠি","বরগুনা"],
    "ময়মনসিংহ":  ["ময়মনসিংহ","জামালপুর","শেরপুর","নেত্রকোনা"],
    "রংপুর":      ["রংপুর","গাইবান্ধা","কুড়িগ্রাম","লালমনিরহাট","নীলফামারী","ঠাকুরগাঁও","পঞ্চগড়","দিনাজপুর"],
}

CASE_TYPES = ["ধর্ষণ","গণধর্ষণ","শিশু যৌন নির্যাতন","যৌন হয়রানি","ডিজিটাল যৌন অপরাধ","পারিবারিক নির্যাতন"]

LAWS = {
    "১": (
        "📜 নারী ও শিশু নির্যাতন দমন আইন ২০০০\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "ধারা ৯(১) — সাধারণ ধর্ষণ\n"
        "শাস্তি: যাবজ্জীবন কারাদণ্ড ও অর্থদণ্ড\n\n"
        "ধারা ৯(২) — ধর্ষণের ফলে মৃত্যু\n"
        "শাস্তি: মৃত্যুদণ্ড বা যাবজ্জীবন কারাদণ্ড\n\n"
        "ধারা ৯(৩) — গণধর্ষণ\n"
        "শাস্তি: মৃত্যুদণ্ড বা যাবজ্জীবন কারাদণ্ড\n\n"
        "ধারা ৯(৪) — শিশু ধর্ষণ (১৮ বছরের নিচে)\n"
        "শাস্তি: মৃত্যুদণ্ড বা যাবজ্জীবন কারাদণ্ড\n\n"
        "ধারা ৯(৫) — ধর্ষণের চেষ্টা\n"
        "শাস্তি: সর্বোচ্চ ১০ বছর কারাদণ্ড\n\n"
        "তদন্ত সময়সীমা: ৩০ কার্যদিবস\n"
        "বিচার সময়সীমা: ১৮০ কার্যদিবস\n\n"
        "অধিকার:\n"
        "→ মহিলা পুলিশের কাছে জবানবন্দির অধিকার\n"
        "→ পরিচয় গোপন রাখার অধিকার\n"
        "→ বিনামূল্যে আইনজীবী ও চিকিৎসার অধিকার"
    ),
    "২": (
        "📜 দণ্ডবিধি ধারা ৩৭৫ ও ৩৭৬\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "ধারা ৩৭৫ — ধর্ষণের সংজ্ঞা\n"
        "→ সম্মতি ছাড়া যেকোনো যৌন সম্পর্ক ধর্ষণ\n"
        "→ ১৪ বছরের নিচে সম্মতি আইনত বৈধ নয়\n\n"
        "ধারা ৩৭৬ — ধর্ষণের শাস্তি\n"
        "→ ন্যূনতম: ৭ বছর কারাদণ্ড\n"
        "→ সর্বোচ্চ: যাবজ্জীবন ও অর্থদণ্ড\n\n"
        "বিশেষ ক্ষেত্রে কঠোর শাস্তি:\n"
        "→ অভিভাবক কর্তৃক: যাবজ্জীবন\n"
        "→ পুলিশ বা সরকারি কর্মকর্তা কর্তৃক: যাবজ্জীবন\n\n"
        "বিবাহিত নারীর ক্ষেত্রেও সমানভাবে প্রযোজ্য"
    ),
    "৩": (
        "📜 শিশু ধর্ষণ আইন\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "শিশু আইন ২০১৩:\n"
        "→ দ্রুত বিচার বাধ্যতামূলক\n"
        "→ তদন্ত সময়: ১৫ কার্যদিবস\n\n"
        "শাস্তি: মৃত্যুদণ্ড বা যাবজ্জীবন\n\n"
        "পরিচয় সুরক্ষা:\n"
        "→ শিশুর নাম প্রকাশ সম্পূর্ণ নিষিদ্ধ\n"
        "→ প্রকাশে শাস্তি: ২ বছর কারাদণ্ড\n\n"
        "বিনামূল্যে সুবিধা:\n"
        "→ OCC চিকিৎসা ও কাউন্সেলিং\n"
        "→ সরকারি আইনজীবী সম্পূর্ণ বিনামূল্যে\n\n"
        "শিশু হেল্পলাইন: 1098"
    ),
    "৪": (
        "📜 গণধর্ষণ আইন\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "একাধিক ব্যক্তি দ্বারা = গণধর্ষণ\n"
        "সকলের শাস্তি: মৃত্যুদণ্ড বা যাবজ্জীবন\n"
        "সাহায্যকারীরও একই শাস্তি\n"
        "তদন্তকালীন কোনো জামিন নেই\n\n"
        "২০২০ সালের সংশোধনী:\n"
        "→ সর্বোচ্চ শাস্তি: মৃত্যুদণ্ড (ফাঁসি)\n\n"
        "ডিজিটাল প্রমাণ:\n"
        "→ ভিডিও ধারণ বা প্রচার আলাদা অপরাধ\n"
        "→ ডিজিটাল নিরাপত্তা আইনে অতিরিক্ত শাস্তি"
    ),
    "৫": (
        "📜 ডিজিটাল অপরাধ ও সাইবার আইন\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "ডিজিটাল নিরাপত্তা আইন ২০১৮ ধারা ২৬:\n"
        "→ সম্মতি ছাড়া ঘনিষ্ঠ ছবি/ভিডিও প্রকাশ\n"
        "→ শাস্তি: ৫ বছর ও ৫ লাখ টাকা জরিমানা\n\n"
        "ধারা ২৯ — অনলাইন যৌন হয়রানি:\n"
        "→ শাস্তি: ৩ বছর ও ৩ লাখ টাকা জরিমানা\n\n"
        "পর্নোগ্রাফি নিয়ন্ত্রণ আইন ২০১২:\n"
        "→ শাস্তি: ৭ বছর ও ২ লাখ টাকা জরিমানা\n\n"
        "ডিজিটাল প্রমাণ সংগ্রহ করুন:\n"
        "→ স্ক্রিনশট ও চ্যাট সংরক্ষণ করুন\n"
        "→ সাইবার সাপোর্ট: 01320-000888"
    ),
    "৬": (
        "📜 ভিকটিমের সম্পূর্ণ আইনি অধিকার\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "বিনামূল্যে আইনি সহায়তা:\n"
        "→ জাতীয় আইনগত সহায়তা: 16430\n\n"
        "পরিচয় ও সম্মান সুরক্ষা:\n"
        "→ মিডিয়া বা আদালতে নাম প্রকাশ নিষিদ্ধ\n"
        "→ মহিলা পুলিশের কাছে জবানবন্দির অধিকার\n\n"
        "বিনামূল্যে চিকিৎসা:\n"
        "→ OCC ফরেনসিক পরীক্ষা বিনামূল্যে\n"
        "→ ট্রমা কাউন্সেলিং বিনামূল্যে\n\n"
        "বিচার প্রক্রিয়ায় অধিকার:\n"
        "→ সাক্ষী সুরক্ষার অধিকার\n"
        "→ ক্ষতিপূরণ দাবির অধিকার\n"
        "→ উচ্চ আদালতে আপিলের অধিকার\n\n"
        "এই অধিকারগুলো আপনার —\n"
        "কেউ কেড়ে নিতে পারবে না।"
    ),
}

HELPLINES = {
    "ঢাকা":       {"emoji":"🏙️","police":"01320-000999","occ":"02-55165088","blast":"01730-329945","ask":"01730-029945","women":"01320-000112","legal":"02-9514424"},
    "চট্টগ্রাম":  {"emoji":"⚓","police":"031-639944",  "occ":"031-630903", "blast":"031-710441",  "ask":"031-2853985","women":"01320-100222","legal":"031-711069"},
    "রাজশাহী":    {"emoji":"🍎","police":"0721-775555", "occ":"0721-772150","blast":"01730-329945","ask":"0721-775588", "women":"01320-200333","legal":"0721-774878"},
    "খুলনা":      {"emoji":"🌿","police":"041-761999",  "occ":"041-762595", "blast":"041-810552",  "ask":"041-731522", "women":"01320-400555","legal":"041-761234"},
    "সিলেট":      {"emoji":"🍵","police":"0821-713666", "occ":"0821-713151","blast":"01730-329945","ask":"0821-716677","women":"01320-300444","legal":"0821-714523"},
    "বরিশাল":     {"emoji":"🌊","police":"0431-66666",  "occ":"0431-2176175","blast":"0431-64411","ask":"16430",      "women":"01320-500666","legal":"0431-65432"},
    "ময়মনসিংহ":  {"emoji":"🌾","police":"091-65100",   "occ":"091-67553",  "blast":"01730-329945","ask":"091-66700", "women":"01320-600777","legal":"091-64321"},
    "রংপুর":      {"emoji":"🌻","police":"0521-66666",  "occ":"0521-63750", "blast":"01730-329945","ask":"0521-64488","women":"01320-700888","legal":"0521-65123"},
}

LAWYERS = {
    "ঢাকা":{"ধর্ষণ":["BLAST ঢাকা: 01730-329945","ASK ঢাকা: 01730-029945"],"শিশু":["BLAST শিশু: 01730-329945","BNWLA: 01711-526303"],"ডিজিটাল":["ASK ঢাকা: 01730-029945","সাইবার সাপোর্ট: 01320-000888"],"হয়রানি":["ASK ঢাকা: 01730-029945","মহিলা পরিষদ: 02-9125676"]},
    "চট্টগ্রাম":{"ধর্ষণ":["BLAST চট্টগ্রাম: 031-710441","YPSA: 031-2853985"],"শিশু":["YPSA চট্টগ্রাম: 031-2853985"],"ডিজিটাল":["আইনি সহায়তা: 16430"],"হয়রানি":["BLAST চট্টগ্রাম: 031-710441"]},
    "রাজশাহী":{"ধর্ষণ":["RDRS রাজশাহী: 0721-775588"],"শিশু":["RDRS রাজশাহী: 0721-775588"],"ডিজিটাল":["আইনি সহায়তা: 16430"],"হয়রানি":["Nagorik Uddyog: 0721-810035"]},
    "default":{"ধর্ষণ":["জাতীয় আইনি সহায়তা: 16430","BLAST জাতীয়: 01730-329945"],"শিশু":["শিশু হেল্পলাইন: 1098","BLAST জাতীয়: 01730-329945"],"ডিজিটাল":["সাইবার সাপোর্ট: 01320-000888"],"হয়রানি":["জাতীয় আইনি সহায়তা: 16430"]},
}

# ─────────────────────────────────────────────────────────────────
#  KEYBOARDS
# ─────────────────────────────────────────────────────────────────

def main_keyboard():
    return ReplyKeyboardMarkup([
        ["📜 আইন ও শাস্তি"],
        ["📋 FIR আবেদন তৈরি করুন"],
        ["👩‍⚖️ আইনজীবী খুঁজুন"],
        ["📞 জরুরি হেল্পলাইন"],
        ["🔍 ঘটনার ডেটাবেজ অনুসন্ধান"],
    ], resize_keyboard=True)

def law_keyboard():
    return ReplyKeyboardMarkup([
        ["১. নারী ও শিশু নির্যাতন আইন ২০০০"],
        ["২. দণ্ডবিধি ধারা ৩৭৫-৩৭৬"],
        ["৩. শিশু ধর্ষণ আইন"],
        ["৪. গণধর্ষণ আইন"],
        ["৫. ডিজিটাল অপরাধ আইন"],
        ["৬. ভিকটিমের সম্পূর্ণ আইনি অধিকার"],
        ["🔙 মূল মেনুতে ফিরুন"],
    ], resize_keyboard=True)

def division_keyboard(back=True):
    rows = [["ঢাকা","চট্টগ্রাম"],["রাজশাহী","খুলনা"],["সিলেট","বরিশাল"],["ময়মনসিংহ","রংপুর"]]
    if back:
        rows.append(["🔙 মূল মেনুতে ফিরুন"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def district_keyboard(division, back=True):
    dists = DISTRICTS.get(division, [])
    rows  = [[d] for d in dists]
    if back:
        rows.append(["🔙 মূল মেনুতে ফিরুন"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def case_type_keyboard(back=True):
    rows = [[c] for c in CASE_TYPES]
    rows.append(["সব ধরনের ঘটনা"])
    if back:
        rows.append(["🔙 মূল মেনুতে ফিরুন"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def days_keyboard():
    return ReplyKeyboardMarkup([
        ["গত ৭ দিন","গত ১৫ দিন"],
        ["গত ৩০ দিন","গত ৯০ দিন"],
        ["গত ১ বছর"],
        ["🔙 মূল মেনুতে ফিরুন"],
    ], resize_keyboard=True)

def case_keyboard():
    return ReplyKeyboardMarkup([
        ["ধর্ষণ মামলা"],
        ["শিশু নির্যাতন"],
        ["ডিজিটাল অপরাধ"],
        ["যৌন হয়রানি"],
        ["🔙 মূল মেনুতে ফিরুন"],
    ], resize_keyboard=True)

def time_keyboard():
    return ReplyKeyboardMarkup([
        ["ভোর (৪টা-৬টা)","সকাল (৬টা-১২টা)"],
        ["দুপুর (১২টা-৩টা)","বিকেল (৩টা-৬টা)"],
        ["সন্ধ্যা (৬টা-৯টা)","রাত (৯টা-১২টা)"],
        ["গভীর রাত (১২টা-৪টা)","সঠিক সময় মনে নেই"],
    ], resize_keyboard=True)

def relation_keyboard():
    return ReplyKeyboardMarkup([
        ["পরিবারের সদস্য","প্রতিবেশী"],
        ["শিক্ষক","কর্মক্ষেত্রের পরিচিত"],
        ["অপরিচিত ব্যক্তি","বন্ধু বা পরিচিত"],
        ["পরিবহন চালক","অন্য কেউ"],
    ], resize_keyboard=True)

def witness_keyboard():
    return ReplyKeyboardMarkup([
        ["হ্যাঁ, সাক্ষী আছে"],
        ["না, কোনো সাক্ষী নেই"],
        ["নিশ্চিত নই"],
    ], resize_keyboard=True)

def skip_keyboard():
    return ReplyKeyboardMarkup([["এড়িয়ে যান"]], resize_keyboard=True)

def confirm_keyboard():
    return ReplyKeyboardMarkup([
        ["✅ হ্যাঁ, PDF তৈরি করুন"],
        ["✏️ না, নতুন করে শুরু করুন"],
        ["❌ বাতিল করুন"],
    ], resize_keyboard=True)

def admin_confirm_keyboard():
    return ReplyKeyboardMarkup([
        ["✅ হ্যাঁ, সংরক্ষণ করুন"],
        ["❌ বাতিল করুন"],
    ], resize_keyboard=True)

# ─────────────────────────────────────────────────────────────────
#  PDF GENERATOR
# ─────────────────────────────────────────────────────────────────

def build_fir_pdf(d: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        topMargin=1.5*cm, bottomMargin=1.5*cm,
        leftMargin=2.5*cm, rightMargin=2.5*cm)

    def P(text, bold=False, size=11, align=0, color="#000000", sb=0, sa=5):
        style = ParagraphStyle("s",
            fontName=BNB() if bold else BN(),
            fontSize=size, alignment=align,
            textColor=colors.HexColor(color),
            spaceBefore=sb, spaceAfter=sa, leading=size*1.6)
        return Paragraph(text, style)

    def section_bar(title):
        t = Table([[P(f"  {title}", bold=True, size=11, color="#FFFFFF", sa=2)]],
                  colWidths=["100%"])
        t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#0D2B5E")),
            ("PADDING",(0,0),(-1,-1),5)]))
        return t

    def info_row(label, value):
        v = value if value and "এড়িয়ে" not in value else "—"
        return [P(label,bold=True,size=10,sa=2), P(":",size=10), P(v,size=10,sa=2)]

    now  = datetime.now()
    ref  = f"OBH-{now.strftime('%Y%m%d%H%M%S')}"
    elem = []

    elem.append(P("গণপ্রজাতন্ত্রী বাংলাদেশ সরকার",bold=True,size=13,align=1,color="#0D2B5E"))
    elem.append(P("বাংলাদেশ পুলিশ",bold=True,size=12,align=1,color="#0D2B5E"))
    elem.append(Spacer(1,2*mm))
    elem.append(HRFlowable(width="100%",thickness=2,color=colors.HexColor("#0D2B5E")))
    elem.append(Spacer(1,2*mm))
    elem.append(P("প্রাথমিক তথ্য বিবরণী (FIR) আবেদনপত্র",bold=True,size=14,align=1,color="#B03A2E"))
    elem.append(P("First Information Report — Initial Application",size=10,align=1,color="#555555"))
    elem.append(HRFlowable(width="100%",thickness=0.5,color=colors.HexColor("#CCCCCC")))
    elem.append(Spacer(1,3*mm))

    ref_t = Table([[P(f"রিপোর্ট আইডি: {ref}",size=9,color="#555555"),
                    P(f"তারিখ: {now.strftime('%d/%m/%Y')}",size=9,align=2,color="#555555")]],
                  colWidths=["60%","40%"])
    ref_t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#F4F6F8")),("PADDING",(0,0),(-1,-1),4)]))
    elem.append(ref_t)
    elem.append(Spacer(1,4*mm))

    station = d.get("station","___________")
    elem.append(P("বরাবর,",bold=True))
    elem.append(P("অফিসার ইনচার্জ"))
    elem.append(P(f"{station} থানা"))
    elem.append(P(f"জেলা: {d.get('district','___________')}"))
    elem.append(Spacer(1,3*mm))
    elem.append(P("বিষয়: নারী ও শিশু নির্যাতন দমন আইন ২০০০ এর ধারা ৯ এবং দণ্ডবিধি ধারা ৩৭৬ "
                  "অনুযায়ী প্রাথমিক তথ্য বিবরণী দাখিল প্রসঙ্গে।",
                  bold=True,size=10,color="#0D2B5E",sb=2,sa=6))
    elem.append(HRFlowable(width="100%",thickness=0.5,color=colors.HexColor("#CCCCCC")))
    elem.append(Spacer(1,3*mm))
    elem.append(P("মহোদয়,",bold=True))
    elem.append(P("আমি নিম্নস্বাক্ষরকারী আপনার নিকট নিম্নলিখিত ঘটনা সম্পর্কে প্রাথমিক তথ্য বিবরণী "
                  "দাখিল করছি এবং অপরাধীদের বিরুদ্ধে আইনানুগ ব্যবস্থা গ্রহণের জন্য বিনীতভাবে "
                  "আবেদন জানাচ্ছি।",sa=6))
    elem.append(Spacer(1,3*mm))

    elem.append(section_bar("বিভাগ ১: আবেদনকারীর তথ্য"))
    elem.append(Spacer(1,2*mm))
    rows1 = [info_row("আবেদনকারীর নাম",d.get("name","")),
             info_row("পিতার নাম",      d.get("father","")),
             info_row("মাতার নাম",      d.get("mother","")),
             info_row("বয়স",            d.get("age","")),
             info_row("জাতীয় পরিচয়পত্র নম্বর",d.get("nid","")),
             info_row("স্থায়ী ঠিকানা", d.get("paddr","")),
             info_row("বর্তমান ঠিকানা",d.get("caddr","")),
             info_row("মোবাইল নম্বর",  d.get("mobile",""))]
    t1 = Table(rows1,colWidths=["38%","3%","59%"])
    t1.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#DDDDDD")),
        ("PADDING",(0,0),(-1,-1),5),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.HexColor("#F9F9F9"),colors.white]),
        ("VALIGN",(0,0),(-1,-1),"TOP")]))
    elem.append(t1)

    elem.append(Spacer(1,3*mm))
    elem.append(section_bar("বিভাগ ২: ঘটনার বিবরণ"))
    elem.append(Spacer(1,2*mm))
    rows2 = [info_row("ঘটনার তারিখ",          d.get("idate","")),
             info_row("ঘটনার সময়",             d.get("itime","")),
             info_row("ঘটনার স্থান",            d.get("iloc","")),
             info_row("থানা",                   d.get("station","")),
             info_row("অভিযুক্তের সাথে সম্পর্ক",d.get("relation","")),
             info_row("সাক্ষী",                 d.get("witness",""))]
    t2 = Table(rows2,colWidths=["38%","3%","59%"])
    t2.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#DDDDDD")),
        ("PADDING",(0,0),(-1,-1),5),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.HexColor("#F9F9F9"),colors.white]),
        ("VALIGN",(0,0),(-1,-1),"TOP")]))
    elem.append(t2)

    elem.append(Spacer(1,3*mm))
    elem.append(section_bar("বিভাগ ৩: ঘটনার বিস্তারিত বর্ণনা"))
    elem.append(Spacer(1,2*mm))
    dt = Table([[P(d.get("desc","—"),sa=0)]],colWidths=["100%"])
    dt.setStyle(TableStyle([("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#CCCCCC")),
        ("PADDING",(0,0),(-1,-1),8),
        ("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#FFFAF9")),
        ("MINROWHEIGHT",(0,0),(-1,-1),2.5*cm),("VALIGN",(0,0),(-1,-1),"TOP")]))
    elem.append(dt)

    elem.append(Spacer(1,3*mm))
    elem.append(section_bar("বিভাগ ৪: প্রযোজ্য আইন ও ধারা"))
    elem.append(Spacer(1,2*mm))
    law_data = [
        [P("আইনের নাম",bold=True,size=10),P("ধারা",bold=True,size=10),P("শাস্তি",bold=True,size=10)],
        [P("নারী ও শিশু নির্যাতন দমন আইন ২০০০",size=10),P("ধারা ৯(১)",size=10),P("যাবজ্জীবন কারাদণ্ড",size=10)],
        [P("দণ্ডবিধি",size=10),P("ধারা ৩৭৬",size=10),P("ন্যূনতম ৭ বছর থেকে যাবজ্জীবন",size=10)],
        [P("নারী ও শিশু আইন ২০০০\n(ভিকটিম ১৮ বছরের নিচে)",size=10),P("ধারা ৯(৪)",size=10),P("মৃত্যুদণ্ড বা যাবজ্জীবন",size=10)],
    ]
    lt = Table(law_data,colWidths=["45%","20%","35%"])
    lt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1A56A4")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#CCCCCC")),
        ("PADDING",(0,0),(-1,-1),6),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.HexColor("#F4F6F8"),colors.white]),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE")]))
    elem.append(lt)

    elem.append(Spacer(1,3*mm))
    elem.append(section_bar("বিভাগ ৫: আবেদন"))
    elem.append(Spacer(1,2*mm))
    elem.append(P("অতএব, মহোদয়ের নিকট বিনীত আবেদন এই যে, উপরোক্ত বর্ণিত ঘটনার সুষ্ঠু তদন্ত করে "
                  "অপরাধীদের বিরুদ্ধে নারী ও শিশু নির্যাতন দমন আইন ২০০০ এর ধারা ৯ ও দণ্ডবিধি ধারা "
                  "৩৭৬ অনুযায়ী আইনানুগ ব্যবস্থা গ্রহণ করে ন্যায়বিচার নিশ্চিত করার জন্য বিনীতভাবে "
                  "প্রার্থনা করছি।",sa=8))
    elem.append(Spacer(1,5*mm))

    sig = Table([[P(f"আবেদনকারীর স্বাক্ষর:\n\n\n___________________________\n{d.get('name','আবেদনকারী')}\n{now.strftime('%d/%m/%Y')}",size=10),
                  P(f"অফিসার ইনচার্জের সিল ও স্বাক্ষর:\n\n\n___________________________\n{station} থানা",size=10)]],
               colWidths=["50%","50%"])
    sig.setStyle(TableStyle([("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#CCCCCC")),
        ("PADDING",(0,0),(-1,-1),10),("VALIGN",(0,0),(-1,-1),"TOP")]))
    elem.append(sig)
    elem.append(Spacer(1,4*mm))

    sup = Table([[P("বিনামূল্যে সহায়তা:  BLAST: 01730-329945  |  ASK: 01730-029945  |  "
                    "আইনি সহায়তা: 16430  |  জরুরি: 999  |  OCC: 02-55165088",
                    size=9,align=1,color="#FFFFFF",sa=0)]],colWidths=["100%"])
    sup.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#1A7A4A")),("PADDING",(0,0),(-1,-1),6)]))
    elem.append(sup)
    elem.append(Spacer(1,2*mm))

    ft = Table([[P(f"তৈরি: @ObhoyBDbot",size=8,color="#888888"),
                 P(now.strftime('%d/%m/%Y %H:%M'),size=8,align=1,color="#888888"),
                 P("obhoy.com",size=8,align=2,color="#888888")]],
               colWidths=["33%","34%","33%"])
    ft.setStyle(TableStyle([("PADDING",(0,0),(-1,-1),2)]))
    elem.append(ft)

    doc.build(elem)
    buf.seek(0)
    return buf.read()

# ─────────────────────────────────────────────────────────────────
#  SEARCH RESULT FORMATTER
# ─────────────────────────────────────────────────────────────────

def format_results(rows, division, district, case_type, days):
    if not rows:
        return (
            "🔍 কোনো ঘটনা পাওয়া যায়নি\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"অনুসন্ধান: {division or 'সব বিভাগ'} / "
            f"{district or 'সব জেলা'} / "
            f"{case_type or 'সব ধরন'} / "
            f"গত {days} দিন\n\n"
            "এই সময়ের মধ্যে কোনো নথিভুক্ত ঘটনা নেই।"
        )

    lines = [
        f"🔍 অনুসন্ধান ফলাফল",
        "━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"বিভাগ: {division or 'সব'} | জেলা: {district or 'সব'}",
        f"ধরন: {case_type or 'সব'} | সময়: গত {days} দিন",
        f"মোট ঘটনা: {len(rows)}টি",
        "━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        "⚠️ ভিকটিম ও আসামির নাম প্রকাশ করা হয়নি।",
        "",
    ]

    for i, row in enumerate(rows, 1):
        div_r, dist_r, upz_r, type_r, date_r, desc_r = row
        location = f"{dist_r}"
        if upz_r:
            location += f", {upz_r}"
        lines.append(f"ঘটনা {i}:")
        lines.append(f"তারিখ: {date_r}")
        lines.append(f"স্থান: {div_r} বিভাগ, {location}")
        lines.append(f"ধরন: {type_r}")
        if desc_r:
            lines.append(f"বিবরণ: {desc_r[:120]}{'...' if len(desc_r)>120 else ''}")
        lines.append("─────────────────────────")

    lines += [
        "",
        "সাহায্যের জন্য:",
        "BLAST: 01730-329945",
        "জরুরি সেবা: 999",
    ]
    return "\n".join(lines)

# ─────────────────────────────────────────────────────────────────
#  /start
# ─────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "🛡️ Obhoy-তে আপনাকে স্বাগতম\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "অভয় — বাংলাদেশের প্রথম AI-চালিত\n"
        "যৌন সহিংসতা প্রতিরোধ ও সহায়তা প্ল্যাটফর্ম।\n\n"
        "📜 আইন ও শাস্তি — ৬টি সম্পূর্ণ আইন\n"
        "📋 FIR আবেদন — PDF তৈরি করুন\n"
        "👩‍⚖️ আইনজীবী — জেলা অনুযায়ী খুঁজুন\n"
        "📞 হেল্পলাইন — সব বিভাগের নম্বর\n"
        "🔍 ডেটাবেজ — এলাকা ও সময় অনুযায়ী খুঁজুন\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "জরুরি প্রয়োজনে: 999\n\n"
        "নিচের মেনু থেকে বেছে নিন",
        reply_markup=main_keyboard()
    )
    return MAIN_MENU

# ─────────────────────────────────────────────────────────────────
#  MAIN MENU
# ─────────────────────────────────────────────────────────────────

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "আইন" in text:
        await update.message.reply_text(
            "📜 আইন ও শাস্তি\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "কোন আইন সম্পর্কে জানতে চান?",
            reply_markup=law_keyboard()
        )
        return LAW_MENU

    elif "FIR" in text or "আবেদন" in text:
        context.user_data['fir'] = {}
        await update.message.reply_text(
            "📋 FIR আবেদনপত্র তৈরি করুন\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "আমি ১৫টি প্রশ্ন করব।\n"
            "উত্তর দিলে একটি সম্পূর্ণ আইনি FIR PDF তৈরি হবে।\n"
            "যেটি থানায় জমা দিতে পারবেন।\n\n"
            "আপনার পরিচয় সম্পূর্ণ গোপন থাকবে।\n"
            "বাতিল করতে /cancel লিখুন।\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "প্রশ্ন ১/১৫\n\n"
            "আবেদনকারীর পুরো নাম কী?\n"
            "(যিনি FIR দাখিল করছেন)",
            reply_markup=ReplyKeyboardRemove()
        )
        return FIR_NAME

    elif "আইনজীবী" in text:
        await update.message.reply_text(
            "👩‍⚖️ আইনজীবী খুঁজুন\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "আপনি কোন বিভাগে আছেন?",
            reply_markup=division_keyboard()
        )
        return LAW_DIST

    elif "হেল্পলাইন" in text:
        await update.message.reply_text(
            "📞 জাতীয় জরুরি হেল্পলাইন\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "জাতীয় জরুরি সেবা: 999\n"
            "নারী হেল্পলাইন: 10921\n"
            "শিশু হেল্পলাইন: 1098\n"
            "আইনি সহায়তা: 16430\n"
            "কান পেত রই: 01779-554391\n"
            "ঢাকা OCC: 02-55165088\n"
            "BLAST: 01730-329945\n"
            "ASK: 01730-029945\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "আপনার বিভাগের বিস্তারিত নম্বর পেতে\n"
            "নিচে থেকে বিভাগ বেছে নিন",
            reply_markup=division_keyboard()
        )
        return HELP_DIST

    elif "ডেটাবেজ" in text or "অনুসন্ধান" in text:
        total = count_incidents(days=365)
        await update.message.reply_text(
            "🔍 ঘটনার ডেটাবেজ অনুসন্ধান\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"মোট নথিভুক্ত ঘটনা: {total}টি\n\n"
            "এখানে ভিকটিম বা আসামির নাম নেই।\n"
            "শুধু ঘটনার স্থান, তারিখ ও ধরন দেখাবে।\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "প্রথমে বিভাগ বেছে নিন:",
            reply_markup=division_keyboard()
        )
        return SRCH_DIV

    elif "মূল মেনু" in text or "ফিরুন" in text:
        await update.message.reply_text("মূল মেনুতে ফিরে এসেছেন।", reply_markup=main_keyboard())
        return MAIN_MENU

    else:
        await update.message.reply_text(
            "নিচের মেনু থেকে বেছে নিন\nজরুরি সাহায্যে: 999",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU

# ─────────────────────────────────────────────────────────────────
#  LAW HANDLERS
# ─────────────────────────────────────────────────────────────────

async def law_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "মূল মেনু" in text or "ফিরুন" in text:
        await update.message.reply_text("মূল মেনুতে ফিরে এসেছেন।", reply_markup=main_keyboard())
        return MAIN_MENU
    for key in LAWS:
        if text.startswith(key):
            await update.message.reply_text(LAWS[key], reply_markup=law_keyboard())
            return LAW_MENU
    await update.message.reply_text("মেনু থেকে বেছে নিন", reply_markup=law_keyboard())
    return LAW_MENU

# ─────────────────────────────────────────────────────────────────
#  HELPLINE HANDLERS
# ─────────────────────────────────────────────────────────────────

async def help_dist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "মূল মেনু" in text or "ফিরুন" in text:
        await update.message.reply_text("মূল মেনুতে ফিরে এসেছেন।", reply_markup=main_keyboard())
        return MAIN_MENU
    for div, info in HELPLINES.items():
        if div in text:
            msg = (
                f"{info['emoji']} {div} বিভাগের সম্পূর্ণ নম্বর\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"পুলিশ: {info['police']}\n"
                f"OCC কেন্দ্র: {info['occ']}\n"
                f"BLAST: {info['blast']}\n"
                f"NGO সহায়তা: {info['ask']}\n"
                f"মহিলা পুলিশ: {info['women']}\n"
                f"বিনামূল্যে আইনি সেবা: {info['legal']}\n"
                f"শিশু হেল্পলাইন: 1098\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "জাতীয় জরুরি সেবা: 999\n"
                "বিনামূল্যে আইনজীবী: 16430"
            )
            await update.message.reply_text(msg, reply_markup=division_keyboard())
            return HELP_DIST
    await update.message.reply_text("বিভাগের নাম বেছে নিন", reply_markup=division_keyboard())
    return HELP_DIST

# ─────────────────────────────────────────────────────────────────
#  FIR HANDLERS
# ─────────────────────────────────────────────────────────────────

async def fir_name(u, ctx):
    ctx.user_data.setdefault('fir',{})['name'] = u.message.text
    await u.message.reply_text("প্রশ্ন ২/১৫\n\nপিতার নাম কী?", reply_markup=skip_keyboard())
    return FIR_FATHER

async def fir_father(u, ctx):
    ctx.user_data['fir']['father'] = u.message.text
    await u.message.reply_text("প্রশ্ন ৩/১৫\n\nমাতার নাম কী?", reply_markup=skip_keyboard())
    return FIR_MOTHER

async def fir_mother(u, ctx):
    ctx.user_data['fir']['mother'] = u.message.text
    await u.message.reply_text("প্রশ্ন ৪/১৫\n\nবয়স কত?\n(সংখ্যায় লিখুন, যেমন: ২২)", reply_markup=ReplyKeyboardRemove())
    return FIR_AGE

async def fir_age(u, ctx):
    ctx.user_data['fir']['age'] = u.message.text
    await u.message.reply_text("প্রশ্ন ৫/১৫\n\nজাতীয় পরিচয়পত্র নম্বর (NID)?", reply_markup=skip_keyboard())
    return FIR_NID

async def fir_nid(u, ctx):
    ctx.user_data['fir']['nid'] = u.message.text
    await u.message.reply_text("প্রশ্ন ৬/১৫\n\nস্থায়ী ঠিকানা?\n(গ্রাম/মহল্লা, উপজেলা, জেলা)", reply_markup=skip_keyboard())
    return FIR_PADDR

async def fir_paddr(u, ctx):
    ctx.user_data['fir']['paddr'] = u.message.text
    await u.message.reply_text("প্রশ্ন ৭/১৫\n\nবর্তমান ঠিকানা?\n(স্থায়ী ঠিকানার মতো হলে এড়িয়ে যান)", reply_markup=skip_keyboard())
    return FIR_CADDR

async def fir_caddr(u, ctx):
    ctx.user_data['fir']['caddr'] = u.message.text
    await u.message.reply_text("প্রশ্ন ৮/১৫\n\nমোবাইল নম্বর?", reply_markup=skip_keyboard())
    return FIR_MOBILE

async def fir_mobile(u, ctx):
    ctx.user_data['fir']['mobile'] = u.message.text
    await u.message.reply_text("প্রশ্ন ৯/১৫\n\nকোন থানায় FIR দাখিল করতে চান?\n(যেমন: মিরপুর থানা)", reply_markup=ReplyKeyboardRemove())
    return FIR_STATION

async def fir_station(u, ctx):
    ctx.user_data['fir']['station'] = u.message.text
    await u.message.reply_text("প্রশ্ন ১০/১৫\n\nঘটনাটি কোন জেলায় ঘটেছে?\nবিভাগ বেছে নিন:", reply_markup=division_keyboard(back=False))
    return FIR_DIST_F

async def fir_dist_f(u, ctx):
    text = u.message.text
    for div in DIVISIONS:
        if div in text:
            ctx.user_data['fir']['division_sel'] = div
            await u.message.reply_text("জেলা বেছে নিন:", reply_markup=district_keyboard(div, back=False))
            return FIR_IDATE
    # If they typed a district name directly
    ctx.user_data['fir']['district'] = text
    await u.message.reply_text("প্রশ্ন ১১/১৫\n\nঘটনাটি কবে ঘটেছে?\n(যেমন: ১৫ মার্চ ২০২৬)", reply_markup=ReplyKeyboardRemove())
    return FIR_ITIME

async def fir_idate(u, ctx):
    text = u.message.text
    # Check if this is a district selection
    div = ctx.user_data['fir'].get('division_sel','')
    if div and text in DISTRICTS.get(div, []):
        ctx.user_data['fir']['district'] = text
        await u.message.reply_text("প্রশ্ন ১১/১৫\n\nঘটনাটি কবে ঘটেছে?\n(যেমন: ১৫ মার্চ ২০২৬)", reply_markup=ReplyKeyboardRemove())
        return FIR_ITIME
    ctx.user_data['fir']['idate'] = text
    await u.message.reply_text("প্রশ্ন ১২/১৫\n\nঘটনাটি কোন সময়ে ঘটেছে?", reply_markup=time_keyboard())
    return FIR_ITIME

async def fir_itime(u, ctx):
    fir = ctx.user_data['fir']
    if 'idate' not in fir:
        fir['idate'] = u.message.text
        await u.message.reply_text("প্রশ্ন ১২/১৫\n\nঘটনাটি কোন সময়ে ঘটেছে?", reply_markup=time_keyboard())
        return FIR_ITIME
    fir['itime'] = u.message.text
    await u.message.reply_text("প্রশ্ন ১৩/১৫\n\nঘটনাটি ঠিক কোথায় ঘটেছে?\n(বিস্তারিত স্থান লিখুন)", reply_markup=ReplyKeyboardRemove())
    return FIR_ILOC

async def fir_iloc(u, ctx):
    ctx.user_data['fir']['iloc'] = u.message.text
    await u.message.reply_text("প্রশ্ন ১৪/১৫\n\nঅভিযুক্ত ব্যক্তি ভিকটিমের কী হয়?", reply_markup=relation_keyboard())
    return FIR_REL

async def fir_rel(u, ctx):
    ctx.user_data['fir']['relation'] = u.message.text
    await u.message.reply_text("প্রশ্ন ১৫/১৫\n\nসংক্ষেপে ঘটনার বর্ণনা লিখুন।\nনাম বলার দরকার নেই।", reply_markup=ReplyKeyboardRemove())
    return FIR_DESC

async def fir_desc(u, ctx):
    ctx.user_data['fir']['desc'] = u.message.text
    await u.message.reply_text("শেষ প্রশ্ন\n\nঘটনার কোনো সাক্ষী আছে?", reply_markup=witness_keyboard())
    return FIR_WITNESS

async def fir_witness(u, ctx):
    ctx.user_data['fir']['witness'] = u.message.text
    fir = ctx.user_data.get('fir', {})
    summary = (
        "সকল তথ্য সংগ্রহ হয়েছে!\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"নাম: {fir.get('name','—')}\n"
        f"পিতা: {fir.get('father','—')}\n"
        f"মাতা: {fir.get('mother','—')}\n"
        f"বয়স: {fir.get('age','—')}\n"
        f"NID: {fir.get('nid','—')}\n"
        f"স্থায়ী ঠিকানা: {fir.get('paddr','—')}\n"
        f"বর্তমান ঠিকানা: {fir.get('caddr','—')}\n"
        f"মোবাইল: {fir.get('mobile','—')}\n"
        f"থানা: {fir.get('station','—')}\n"
        f"জেলা: {fir.get('district','—')}\n"
        f"তারিখ: {fir.get('idate','—')}\n"
        f"সময়: {fir.get('itime','—')}\n"
        f"স্থান: {fir.get('iloc','—')}\n"
        f"সম্পর্ক: {fir.get('relation','—')}\n"
        f"সাক্ষী: {fir.get('witness','—')}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "এই তথ্য দিয়ে PDF তৈরি করব?"
    )
    await u.message.reply_text(summary, reply_markup=confirm_keyboard())
    return FIR_CONFIRM

async def fir_confirm(u, ctx):
    text = u.message.text
    if "বাতিল" in text:
        await u.message.reply_text("FIR তৈরি বাতিল।", reply_markup=main_keyboard())
        return MAIN_MENU
    elif "নতুন" in text:
        ctx.user_data['fir'] = {}
        await u.message.reply_text("নতুন করে শুরু হচ্ছে।\n\nপ্রশ্ন ১/১৫\n\nআবেদনকারীর পুরো নাম কী?", reply_markup=ReplyKeyboardRemove())
        return FIR_NAME
    elif "হ্যাঁ" in text or "PDF" in text:
        await u.message.reply_text("PDF তৈরি হচ্ছে...", reply_markup=ReplyKeyboardRemove())
        try:
            pdf_bytes = build_fir_pdf(ctx.user_data.get('fir', {}))
            name = ctx.user_data.get('fir',{}).get('name','applicant').replace(' ','_')
            fname = f"Obhoy_FIR_{name}_{datetime.now().strftime('%Y%m%d')}.pdf"
            await u.message.reply_document(
                document=io.BytesIO(pdf_bytes),
                filename=fname,
                caption=(
                    "আপনার FIR আবেদনপত্র তৈরি হয়েছে!\n\n"
                    "এখন কী করবেন:\n"
                    "১. এই PDF প্রিন্ট করুন\n"
                    "২. নিকটস্থ থানায় নিয়ে যান\n"
                    "৩. মহিলা পুলিশ অফিসার চাইতে পারেন\n"
                    "৪. স্বাক্ষর করে জমা দিন\n\n"
                    "বিনামূল্যে আইনজীবী: 16430\n"
                    "BLAST: 01730-329945\n"
                    "জরুরি: 999"
                )
            )
            await u.message.reply_text("আর কোনো সাহায্য লাগলে নিচের মেনু থেকে বেছে নিন।", reply_markup=main_keyboard())
        except Exception as e:
            logger.error(f"PDF error: {e}")
            await u.message.reply_text("দুঃখিত, PDF তৈরিতে সমস্যা হয়েছে।\nBLAST: 01730-329945\nআইনি: 16430", reply_markup=main_keyboard())
        return MAIN_MENU
    else:
        await u.message.reply_text("নিচের অপশন থেকে বেছে নিন", reply_markup=confirm_keyboard())
        return FIR_CONFIRM

# ─────────────────────────────────────────────────────────────────
#  LAWYER HANDLERS
# ─────────────────────────────────────────────────────────────────

async def law_dist(u, ctx):
    text = u.message.text
    if "মূল মেনু" in text or "ফিরুন" in text:
        await u.message.reply_text("মূল মেনুতে ফিরে এসেছেন।", reply_markup=main_keyboard())
        return MAIN_MENU
    matched = "default"
    for d in LAWYERS:
        if d in text:
            matched = d
            break
    ctx.user_data['ldist'] = matched
    await u.message.reply_text(f"{text} বিভাগ নোট হয়েছে।\n\nকী ধরনের মামলায় আইনজীবী দরকার?", reply_markup=case_keyboard())
    return LAW_TYPE

async def law_type(u, ctx):
    text = u.message.text
    if "মূল মেনু" in text or "ফিরুন" in text:
        await u.message.reply_text("মূল মেনুতে ফিরে এসেছেন।", reply_markup=main_keyboard())
        return MAIN_MENU
    cmap = {"ধর্ষণ":"ধর্ষণ","শিশু":"শিশু","ডিজিটাল":"ডিজিটাল","হয়রানি":"হয়রানি"}
    ckey = "ধর্ষণ"
    for k, v in cmap.items():
        if k in text:
            ckey = v
            break
    dist = ctx.user_data.get('ldist','default')
    lawyers = LAWYERS.get(dist,{}).get(ckey) or LAWYERS['default'].get(ckey,[])
    contacts = "\n".join([f"✅ {l}" for l in lawyers])
    await u.message.reply_text(
        f"👩‍⚖️ {dist} — {ckey} মামলার আইনজীবী\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{contacts}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "বিনামূল্যে জাতীয় আইনি সহায়তা: 16430\n"
        "OCC বিনামূল্যে চিকিৎসা: 02-55165088\n"
        "জরুরি: 999",
        reply_markup=main_keyboard()
    )
    return MAIN_MENU

# ─────────────────────────────────────────────────────────────────
#  SEARCH HANDLERS (Idea — Crime Database)
# ─────────────────────────────────────────────────────────────────

async def srch_div(u, ctx):
    text = u.message.text
    if "মূল মেনু" in text or "ফিরুন" in text:
        await u.message.reply_text("মূল মেনুতে ফিরে এসেছেন।", reply_markup=main_keyboard())
        return MAIN_MENU
    matched = None
    for div in DIVISIONS:
        if div in text:
            matched = div
            break
    ctx.user_data['s_div'] = matched
    dname = matched or "সব বিভাগ"
    await u.message.reply_text(
        f"{dname} বেছে নেওয়া হয়েছে।\n\n"
        "এখন জেলা বেছে নিন:\n"
        "(বা 'সব জেলা' লিখুন)",
        reply_markup=district_keyboard(matched, back=True) if matched else division_keyboard()
    )
    return SRCH_DIST

async def srch_dist(u, ctx):
    text = u.message.text
    if "মূল মেনু" in text or "ফিরুন" in text:
        await u.message.reply_text("মূল মেনুতে ফিরে এসেছেন।", reply_markup=main_keyboard())
        return MAIN_MENU
    ctx.user_data['s_dist'] = None if "সব" in text else text
    await u.message.reply_text("ঘটনার ধরন বেছে নিন:", reply_markup=case_type_keyboard())
    return SRCH_TYPE

async def srch_type(u, ctx):
    text = u.message.text
    if "মূল মেনু" in text or "ফিরুন" in text:
        await u.message.reply_text("মূল মেনুতে ফিরে এসেছেন।", reply_markup=main_keyboard())
        return MAIN_MENU
    ctx.user_data['s_type'] = None if "সব" in text else text
    await u.message.reply_text("কত দিনের ঘটনা খুঁজছেন?", reply_markup=days_keyboard())
    return SRCH_DAYS

async def srch_days(u, ctx):
    text = u.message.text
    if "মূল মেনু" in text or "ফিরুন" in text:
        await u.message.reply_text("মূল মেনুতে ফিরে এসেছেন।", reply_markup=main_keyboard())
        return MAIN_MENU
    dmap = {"৭":7,"১৫":15,"৩০":30,"৯০":90,"১ বছর":365}
    days = 30
    for k, v in dmap.items():
        if k in text:
            days = v
            break
    div  = ctx.user_data.get('s_div')
    dist = ctx.user_data.get('s_dist')
    ctype= ctx.user_data.get('s_type')
    await u.message.reply_text("অনুসন্ধান চলছে...", reply_markup=ReplyKeyboardRemove())
    try:
        rows   = search_incidents(division=div, district=dist, case_type=ctype, days=days)
        result = format_results(rows, div, dist, ctype, days)
        await u.message.reply_text(result, reply_markup=main_keyboard())
    except Exception as e:
        logger.error(f"Search error: {e}")
        await u.message.reply_text("অনুসন্ধানে সমস্যা হয়েছে। পরে আবার চেষ্টা করুন।", reply_markup=main_keyboard())
    return MAIN_MENU

# ─────────────────────────────────────────────────────────────────
#  ADMIN HANDLERS — /admin command
# ─────────────────────────────────────────────────────────────────

async def admin_start(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['admin'] = {}
    await u.message.reply_text(
        "🔐 Admin প্যানেল\n\n"
        "পাসওয়ার্ড দিন:",
        reply_markup=ReplyKeyboardRemove()
    )
    return ADMIN_PASS

async def admin_pass(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if u.message.text.strip() != ADMIN_PASSWORD:
        await u.message.reply_text("❌ ভুল পাসওয়ার্ড।\nআবার চেষ্টা করুন বা /cancel করুন।")
        return ADMIN_PASS
    await u.message.reply_text(
        "✅ Admin প্যানেলে স্বাগতম!\n\n"
        "নতুন ঘটনা যোগ করতে বিভাগ বেছে নিন:",
        reply_markup=division_keyboard(back=False)
    )
    return ADMIN_DIV

async def admin_div(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = u.message.text
    matched = None
    for div in DIVISIONS:
        if div in text:
            matched = div
            break
    if not matched:
        await u.message.reply_text("সঠিক বিভাগ বেছে নিন:", reply_markup=division_keyboard(back=False))
        return ADMIN_DIV
    ctx.user_data['admin']['division'] = matched
    await u.message.reply_text(f"{matched} বিভাগ। এখন জেলা বেছে নিন:", reply_markup=district_keyboard(matched, back=False))
    return ADMIN_DIST_A

async def admin_dist(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['admin']['district'] = u.message.text
    await u.message.reply_text("উপজেলার নাম লিখুন:\n(না থাকলে 'এড়িয়ে যান' লিখুন)", reply_markup=skip_keyboard())
    return ADMIN_UPZ

async def admin_upz(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = u.message.text
    ctx.user_data['admin']['upazila'] = "" if "এড়িয়ে" in text else text
    await u.message.reply_text("ঘটনার ধরন বেছে নিন:", reply_markup=case_type_keyboard(back=False))
    return ADMIN_TYPE_A

async def admin_type(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['admin']['case_type'] = u.message.text
    await u.message.reply_text(
        "ঘটনার তারিখ লিখুন:\n(YYYY-MM-DD ফরম্যাটে, যেমন: 2026-03-15)",
        reply_markup=ReplyKeyboardRemove()
    )
    return ADMIN_DATE_A

async def admin_date(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = u.message.text.strip()
    try:
        datetime.strptime(text, "%Y-%m-%d")
        ctx.user_data['admin']['inc_date'] = text
    except ValueError:
        await u.message.reply_text("সঠিক ফরম্যাটে তারিখ লিখুন (YYYY-MM-DD):\nযেমন: 2026-03-15")
        return ADMIN_DATE_A
    await u.message.reply_text(
        "সংক্ষিপ্ত বিবরণ লিখুন:\n\n"
        "শুধু ঘটনার তথ্য — কোনো নাম লিখবেন না।\n"
        "(যেমন: রাতের বেলায় বাড়ি থেকে ফেরার পথে ঘটনাটি ঘটে)"
    )
    return ADMIN_DESC_A

async def admin_desc(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['admin']['description'] = u.message.text
    a = ctx.user_data['admin']
    summary = (
        "নতুন ঘটনার তথ্য:\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"বিভাগ: {a.get('division')}\n"
        f"জেলা: {a.get('district')}\n"
        f"উপজেলা: {a.get('upazila') or '—'}\n"
        f"ধরন: {a.get('case_type')}\n"
        f"তারিখ: {a.get('inc_date')}\n"
        f"বিবরণ: {a.get('description')}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "সংরক্ষণ করব?"
    )
    await u.message.reply_text(summary, reply_markup=admin_confirm_keyboard())
    return ADMIN_CONF_A

async def admin_confirm(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = u.message.text
    if "বাতিল" in text:
        await u.message.reply_text("বাতিল করা হয়েছে।", reply_markup=main_keyboard())
        return MAIN_MENU
    elif "হ্যাঁ" in text or "সংরক্ষণ" in text:
        try:
            a = ctx.user_data['admin']
            add_incident(
                division    = a['division'],
                district    = a['district'],
                upazila     = a.get('upazila',''),
                case_type   = a['case_type'],
                inc_date    = a['inc_date'],
                description = a['description'],
                source      = "admin"
            )
            await u.message.reply_text(
                "✅ ঘটনা সফলভাবে ডেটাবেজে সংরক্ষণ হয়েছে!\n\n"
                "এখন থেকে এই ঘটনা অনুসন্ধানে পাওয়া যাবে।\n\n"
                "আরেকটি যোগ করতে /admin লিখুন।",
                reply_markup=main_keyboard()
            )
        except Exception as e:
            logger.error(f"DB insert error: {e}")
            await u.message.reply_text(f"সংরক্ষণে সমস্যা: {e}", reply_markup=main_keyboard())
        return MAIN_MENU
    else:
        await u.message.reply_text("নিচের অপশন থেকে বেছে নিন", reply_markup=admin_confirm_keyboard())
        return ADMIN_CONF_A

# ─────────────────────────────────────────────────────────────────
#  CANCEL + ERROR
# ─────────────────────────────────────────────────────────────────

async def cancel(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await u.message.reply_text("বাতিল করা হয়েছে।\n/start লিখে আবার শুরু করুন।\nজরুরি: 999", reply_markup=main_keyboard())
    return MAIN_MENU

async def error_handler(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {ctx.error}")

# ─────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────

def main():
    if not TOKEN:
        raise ValueError("TOKEN পাওয়া যায়নি।")

    setup_db()

    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start",  start),
            CommandHandler("admin",  admin_start),
        ],
        states={
            MAIN_MENU:   [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu)],
            LAW_MENU:    [MessageHandler(filters.TEXT & ~filters.COMMAND, law_menu)],
            HELP_DIST:   [MessageHandler(filters.TEXT & ~filters.COMMAND, help_dist)],
            FIR_NAME:    [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_name)],
            FIR_FATHER:  [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_father)],
            FIR_MOTHER:  [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_mother)],
            FIR_AGE:     [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_age)],
            FIR_NID:     [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_nid)],
            FIR_PADDR:   [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_paddr)],
            FIR_CADDR:   [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_caddr)],
            FIR_MOBILE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_mobile)],
            FIR_STATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_station)],
            FIR_DIST_F:  [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_dist_f)],
            FIR_IDATE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_idate)],
            FIR_ITIME:   [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_itime)],
            FIR_ILOC:    [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_iloc)],
            FIR_REL:     [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_rel)],
            FIR_DESC:    [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_desc)],
            FIR_WITNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_witness)],
            FIR_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_confirm)],
            LAW_DIST:    [MessageHandler(filters.TEXT & ~filters.COMMAND, law_dist)],
            LAW_TYPE:    [MessageHandler(filters.TEXT & ~filters.COMMAND, law_type)],
            SRCH_DIV:    [MessageHandler(filters.TEXT & ~filters.COMMAND, srch_div)],
            SRCH_DIST:   [MessageHandler(filters.TEXT & ~filters.COMMAND, srch_dist)],
            SRCH_TYPE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, srch_type)],
            SRCH_DAYS:   [MessageHandler(filters.TEXT & ~filters.COMMAND, srch_days)],
            ADMIN_PASS:  [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_pass)],
            ADMIN_DIV:   [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_div)],
            ADMIN_DIST_A:[MessageHandler(filters.TEXT & ~filters.COMMAND, admin_dist)],
            ADMIN_UPZ:   [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_upz)],
            ADMIN_TYPE_A:[MessageHandler(filters.TEXT & ~filters.COMMAND, admin_type)],
            ADMIN_DATE_A:[MessageHandler(filters.TEXT & ~filters.COMMAND, admin_date)],
            ADMIN_DESC_A:[MessageHandler(filters.TEXT & ~filters.COMMAND, admin_desc)],
            ADMIN_CONF_A:[MessageHandler(filters.TEXT & ~filters.COMMAND, admin_confirm)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start",  start),
            CommandHandler("admin",  admin_start),
        ],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_error_handler(error_handler)

    mode = "PostgreSQL" if USE_PG else "SQLite"
    print(f"✅ Obhoy Bot v3 চালু — Database: {mode}")
    print("🛡️ অভয় — নির্ভয়ে কথা বলুন 🇧🇩")

    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
