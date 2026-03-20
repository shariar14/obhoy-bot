"""
╔══════════════════════════════════════════════════════════════╗
║           OBHOY BOT — সম্পূর্ণ সংস্করণ v2                  ║
║  ৪টি বিভাগ: আইন • FIR PDF • আইনজীবী • হেল্পলাইন            ║
║           obhoy.com | @ObhoyBDbot                            ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import io
import logging
import urllib.request
from datetime import datetime

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
TOKEN = os.environ.get("TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

FONT_PATH  = "/tmp/NotoSansBengali.ttf"
FONT_BOLD  = "/tmp/NotoSansBengali-Bold.ttf"
FONT_URL   = "https://cdn.jsdelivr.net/gh/googlefonts/noto-fonts/hinted/ttf/NotoSansBengali/NotoSansBengali-Regular.ttf"
FONT_BOLD_URL = "https://cdn.jsdelivr.net/gh/googlefonts/noto-fonts/hinted/ttf/NotoSansBengali/NotoSansBengali-Bold.ttf"

FONT_READY = False

def setup_fonts():
    global FONT_READY
    try:
        if not os.path.exists(FONT_PATH):
            logger.info("Bengali ফন্ট ডাউনলোড হচ্ছে...")
            urllib.request.urlretrieve(FONT_URL, FONT_PATH)
        if not os.path.exists(FONT_BOLD):
            urllib.request.urlretrieve(FONT_BOLD_URL, FONT_BOLD)
        pdfmetrics.registerFont(TTFont("Bengali", FONT_PATH))
        pdfmetrics.registerFont(TTFont("Bengali-Bold", FONT_BOLD))
        FONT_READY = True
        logger.info("Bengali ফন্ট প্রস্তুত ✅")
    except Exception as e:
        logger.warning(f"ফন্ট ডাউনলোড ব্যর্থ: {e} — ইংরেজি ফন্ট ব্যবহার হবে")
        FONT_READY = False

setup_fonts()

def BN(size=11):
    return "Bengali" if FONT_READY else "Helvetica"

def BNB(size=11):
    return "Bengali-Bold" if FONT_READY else "Helvetica-Bold"

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
FIR_IDATE    = 19
FIR_ITIME    = 20
FIR_ILOC     = 21
FIR_REL      = 22
FIR_DESC     = 23
FIR_WITNESS  = 24
FIR_CONFIRM  = 25

LAW_DIST     = 30
LAW_TYPE     = 31

# ─────────────────────────────────────────────────────────────────
#  LAWS DATABASE — বিস্তারিত
# ─────────────────────────────────────────────────────────────────
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
        "শাস্তি: সর্বোচ্চ ১০ বছর কারাদণ্ড ও অর্থদণ্ড\n\n"
        "তদন্ত সময়সীমা: ৩০ কার্যদিবস\n"
        "বিচার সময়সীমা: ১৮০ কার্যদিবস\n\n"
        "আবেদনকারীর অধিকার:\n"
        "→ মহিলা পুলিশ অফিসারের কাছে জবানবন্দি\n"
        "→ পরিচয় সম্পূর্ণ গোপন রাখার অধিকার\n"
        "→ বিনামূল্যে আইনজীবী ও চিকিৎসার অধিকার\n"
        "→ সাক্ষী সুরক্ষার অধিকার"
    ),
    "২": (
        "📜 দণ্ডবিধি ধারা ৩৭৫ ও ৩৭৬\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "ধারা ৩৭৫ — ধর্ষণের সংজ্ঞা\n"
        "→ সম্মতি ছাড়া যেকোনো যৌন সম্পর্ক ধর্ষণ\n"
        "→ ১৪ বছরের নিচে সম্মতি আইনত বৈধ নয়\n\n"
        "ধারা ৩৭৬ — ধর্ষণের শাস্তি\n"
        "→ ন্যূনতম: ৭ বছর কারাদণ্ড\n"
        "→ সর্বোচ্চ: যাবজ্জীবন কারাদণ্ড ও অর্থদণ্ড\n\n"
        "বিশেষ ক্ষেত্রে কঠোর শাস্তি:\n"
        "→ অভিভাবক কর্তৃক ধর্ষণ: যাবজ্জীবন\n"
        "→ পুলিশ বা সরকারি কর্মকর্তা কর্তৃক: যাবজ্জীবন\n"
        "→ হাসপাতালে ধর্ষণ: যাবজ্জীবন\n\n"
        "গুরুত্বপূর্ণ তথ্য:\n"
        "→ বিবাহিত নারীর ক্ষেত্রেও সমানভাবে প্রযোজ্য\n"
        "→ মেডিকেল রিপোর্ট প্রমাণ হিসেবে গ্রহণযোগ্য\n"
        "→ ঘটনার পর যত দ্রুত রিপোর্ট করবেন প্রমাণ তত শক্তিশালী"
    ),
    "৩": (
        "📜 শিশু ধর্ষণ আইন\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "শিশু আইন ২০১৩:\n"
        "→ শিশু আদালতে দ্রুত বিচার বাধ্যতামূলক\n"
        "→ তদন্ত সময়সীমা: ১৫ কার্যদিবস\n\n"
        "নারী ও শিশু নির্যাতন দমন আইন ২০০০ ধারা ৯(৪):\n"
        "→ শাস্তি: মৃত্যুদণ্ড বা যাবজ্জীবন কারাদণ্ড\n\n"
        "পরিচয় সুরক্ষা আইন:\n"
        "→ ভিকটিম শিশুর নাম বা পরিচয় প্রকাশ সম্পূর্ণ নিষিদ্ধ\n"
        "→ পরিচয় প্রকাশে শাস্তি: ২ বছর কারাদণ্ড ও অর্থদণ্ড\n\n"
        "বিনামূল্যে সুবিধা:\n"
        "→ OCC-তে বিনামূল্যে চিকিৎসা ও কাউন্সেলিং\n"
        "→ সরকারি আইনজীবী সম্পূর্ণ বিনামূল্যে\n"
        "→ অভিভাবক শিশুর পক্ষে মামলা করতে পারবেন\n\n"
        "জরুরি নম্বর:\n"
        "→ শিশু হেল্পলাইন: 1098\n"
        "→ জাতীয় আইনি সহায়তা: 16430"
    ),
    "৪": (
        "📜 গণধর্ষণ আইন\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "নারী ও শিশু নির্যাতন দমন আইন ধারা ৯(৩):\n"
        "→ একাধিক ব্যক্তি দ্বারা ধর্ষণ = গণধর্ষণ\n"
        "→ সকলের শাস্তি: মৃত্যুদণ্ড বা যাবজ্জীবন\n\n"
        "সহযোগিতাকারীর শাস্তি:\n"
        "→ সরাসরি অংশগ্রহণ না করলেও একই শাস্তি\n"
        "→ পরিকল্পনায় থাকলেও একই শাস্তি\n\n"
        "২০২০ সালের সংশোধনী:\n"
        "→ সর্বোচ্চ শাস্তি: মৃত্যুদণ্ড (ফাঁসি)\n"
        "→ তদন্ত চলাকালীন কোনো জামিন নেই\n\n"
        "দ্রুত বিচার:\n"
        "→ নারী ও শিশু নির্যাতন দমন ট্রাইব্যুনালে বিচার\n"
        "→ সময়সীমা: ১৮০ কার্যদিবসের মধ্যে রায়\n\n"
        "ডিজিটাল প্রমাণ:\n"
        "→ ভিডিও ধারণ বা প্রচার আলাদা অপরাধ\n"
        "→ ডিজিটাল নিরাপত্তা আইনে অতিরিক্ত শাস্তি"
    ),
    "৫": (
        "📜 ডিজিটাল অপরাধ ও সাইবার আইন\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "ডিজিটাল নিরাপত্তা আইন ২০১৮ ধারা ২৬:\n"
        "→ সম্মতি ছাড়া ঘনিষ্ঠ ছবি/ভিডিও প্রকাশ\n"
        "→ শাস্তি: ৫ বছর কারাদণ্ড ও ৫ লাখ টাকা জরিমানা\n\n"
        "ধারা ২৯ — অনলাইন যৌন হয়রানি:\n"
        "→ মানহানিকর যৌন বিষয়বস্তু প্রকাশ\n"
        "→ শাস্তি: ৩ বছর কারাদণ্ড ও ৩ লাখ টাকা জরিমানা\n\n"
        "পর্নোগ্রাফি নিয়ন্ত্রণ আইন ২০১২:\n"
        "→ অনুমতি ছাড়া ভিডিও তৈরি বা প্রচার\n"
        "→ শাস্তি: ৭ বছর কারাদণ্ড ও ২ লাখ টাকা জরিমানা\n\n"
        "ডিজিটাল প্রমাণ সংগ্রহ করুন:\n"
        "→ স্ক্রিনশট ও চ্যাট হিস্ট্রি প্রমাণ হিসেবে গ্রহণযোগ্য\n"
        "→ প্রমাণ মুছে ফেলবেন না\n\n"
        "রিপোর্ট করুন:\n"
        "→ পুলিশ সাইবার সাপোর্ট: 01320-000888\n"
        "→ BGD e-GOV CIRT: cirt.gov.bd"
    ),
    "৬": (
        "📜 ভিকটিমের সম্পূর্ণ আইনি অধিকার\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "বিনামূল্যে আইনি সহায়তার অধিকার:\n"
        "→ জাতীয় আইনগত সহায়তা সংস্থা: 16430\n"
        "→ সম্পূর্ণ বিনামূল্যে আইনজীবী পাওয়ার অধিকার\n\n"
        "পরিচয় ও সম্মান সুরক্ষার অধিকার:\n"
        "→ মিডিয়া বা আদালতে নাম প্রকাশ নিষিদ্ধ\n"
        "→ মহিলা পুলিশের কাছে জবানবন্দির অধিকার\n"
        "→ পুরুষ পুলিশের সামনে বক্তব্য দিতে বাধ্য নন\n\n"
        "বিনামূল্যে চিকিৎসার অধিকার:\n"
        "→ OCC-তে ফরেনসিক পরীক্ষা বিনামূল্যে\n"
        "→ ট্রমা কাউন্সেলিং বিনামূল্যে\n"
        "→ ওষুধ ও চিকিৎসা সম্পূর্ণ বিনামূল্যে\n\n"
        "বিচার প্রক্রিয়ায় অধিকার:\n"
        "→ সাক্ষী সুরক্ষার অধিকার\n"
        "→ আদালতে সাক্ষী দেওয়ার সময় নিরাপত্তা\n"
        "→ ক্ষতিপূরণ দাবির অধিকার\n"
        "→ রায়ে অসন্তুষ্ট হলে উচ্চ আদালতে আপিলের অধিকার\n\n"
        "মনে রাখবেন:\n"
        "→ এই অধিকারগুলো আপনার\n"
        "→ কেউ এই অধিকার থেকে বঞ্চিত করতে পারবে না"
    ),
}

# ─────────────────────────────────────────────────────────────────
#  HELPLINES DATABASE
# ─────────────────────────────────────────────────────────────────
HELPLINES = {
    "ঢাকা": {
        "emoji": "🏙️",
        "police": "ঢাকা মেট্রোপলিটন পুলিশ: 01320-000999",
        "occ": "OCC ঢাকা মেডিকেল কলেজ: 02-55165088",
        "blast": "BLAST ঢাকা: 01730-329945",
        "ask": "ASK ঢাকা: 01730-029945",
        "women": "মহিলা পুলিশ সহায়তা: 01320-000112",
        "legal": "জেলা লিগ্যাল এইড: 02-9514424",
        "child": "শিশু হেল্পলাইন: 1098",
    },
    "চট্টগ্রাম": {
        "emoji": "⚓",
        "police": "চট্টগ্রাম মেট্রোপলিটন পুলিশ: 031-639944",
        "occ": "OCC চট্টগ্রাম মেডিকেল: 031-630903",
        "blast": "BLAST চট্টগ্রাম: 031-710441",
        "ask": "YPSA চট্টগ্রাম: 031-2853985",
        "women": "মহিলা পুলিশ সহায়তা: 01320-100222",
        "legal": "জেলা লিগ্যাল এইড: 031-711069",
        "child": "শিশু হেল্পলাইন: 1098",
    },
    "রাজশাহী": {
        "emoji": "🍎",
        "police": "রাজশাহী মেট্রোপলিটন পুলিশ: 0721-775555",
        "occ": "OCC রাজশাহী মেডিকেল: 0721-772150",
        "blast": "BLAST রাজশাহী: 01730-329945",
        "ask": "RDRS রাজশাহী: 0721-775588",
        "women": "মহিলা পুলিশ সহায়তা: 01320-200333",
        "legal": "জেলা লিগ্যাল এইড: 0721-774878",
        "child": "শিশু হেল্পলাইন: 1098",
    },
    "খুলনা": {
        "emoji": "🌿",
        "police": "খুলনা মেট্রোপলিটন পুলিশ: 041-761999",
        "occ": "OCC খুলনা মেডিকেল: 041-762595",
        "blast": "BLAST খুলনা: 041-810552",
        "ask": "Rupantar খুলনা: 041-731522",
        "women": "মহিলা পুলিশ সহায়তা: 01320-400555",
        "legal": "জেলা লিগ্যাল এইড: 041-761234",
        "child": "শিশু হেল্পলাইন: 1098",
    },
    "সিলেট": {
        "emoji": "🍵",
        "police": "সিলেট মেট্রোপলিটন পুলিশ: 0821-713666",
        "occ": "OCC MAG ওসমানী মেডিকেল: 0821-713151",
        "blast": "BLAST জাতীয়: 01730-329945",
        "ask": "BNWLA সিলেট: 0821-716677",
        "women": "মহিলা পুলিশ সহায়তা: 01320-300444",
        "legal": "জেলা লিগ্যাল এইড: 0821-714523",
        "child": "শিশু হেল্পলাইন: 1098",
    },
    "বরিশাল": {
        "emoji": "🌊",
        "police": "বরিশাল মেট্রোপলিটন পুলিশ: 0431-66666",
        "occ": "OCC শের-ই-বাংলা মেডিকেল: 0431-2176175",
        "blast": "BLAST বরিশাল: 0431-64411",
        "ask": "জাতীয় আইনি সহায়তা: 16430",
        "women": "মহিলা পুলিশ সহায়তা: 01320-500666",
        "legal": "জেলা লিগ্যাল এইড: 0431-65432",
        "child": "শিশু হেল্পলাইন: 1098",
    },
    "ময়মনসিংহ": {
        "emoji": "🌾",
        "police": "ময়মনসিংহ মেট্রোপলিটন পুলিশ: 091-65100",
        "occ": "OCC ময়মনসিংহ মেডিকেল: 091-67553",
        "blast": "BRAC ময়মনসিংহ: 091-66700",
        "ask": "জাতীয় আইনি সহায়তা: 16430",
        "women": "মহিলা পুলিশ সহায়তা: 01320-600777",
        "legal": "জেলা লিগ্যাল এইড: 091-64321",
        "child": "শিশু হেল্পলাইন: 1098",
    },
    "রংপুর": {
        "emoji": "🌻",
        "police": "রংপুর মেট্রোপলিটন পুলিশ: 0521-66666",
        "occ": "OCC রংপুর মেডিকেল: 0521-63750",
        "blast": "RDRS রংপুর: 0521-64488",
        "ask": "জাতীয় আইনি সহায়তা: 16430",
        "women": "মহিলা পুলিশ সহায়তা: 01320-700888",
        "legal": "জেলা লিগ্যাল এইড: 0521-65123",
        "child": "শিশু হেল্পলাইন: 1098",
    },
}

# ─────────────────────────────────────────────────────────────────
#  LAWYER DATABASE
# ─────────────────────────────────────────────────────────────────
LAWYERS = {
    "ঢাকা": {
        "ধর্ষণ মামলা":       ["BLAST ঢাকা: 01730-329945", "ASK ঢাকা: 01730-029945"],
        "শিশু নির্যাতন":     ["BLAST শিশু বিভাগ: 01730-329945", "BNWLA: 01711-526303"],
        "ডিজিটাল অপরাধ":    ["সাইবার সাপোর্ট: 01320-000888", "ASK ঢাকা: 01730-029945"],
        "যৌন হয়রানি":       ["ASK ঢাকা: 01730-029945", "মহিলা পরিষদ: 02-9125676"],
    },
    "চট্টগ্রাম": {
        "ধর্ষণ মামলা":       ["BLAST চট্টগ্রাম: 031-710441", "YPSA: 031-2853985"],
        "শিশু নির্যাতন":     ["YPSA চট্টগ্রাম: 031-2853985"],
        "ডিজিটাল অপরাধ":    ["জাতীয় আইনি সহায়তা: 16430"],
        "যৌন হয়রানি":       ["BLAST চট্টগ্রাম: 031-710441"],
    },
    "রাজশাহী": {
        "ধর্ষণ মামলা":       ["RDRS রাজশাহী: 0721-775588"],
        "শিশু নির্যাতন":     ["RDRS রাজশাহী: 0721-775588"],
        "ডিজিটাল অপরাধ":    ["জাতীয় আইনি সহায়তা: 16430"],
        "যৌন হয়রানি":       ["Nagorik Uddyog: 0721-810035"],
    },
    "অন্যান্য": {
        "ধর্ষণ মামলা":       ["জাতীয় আইনি সহায়তা: 16430", "BLAST জাতীয়: 01730-329945"],
        "শিশু নির্যাতন":     ["শিশু হেল্পলাইন: 1098", "BLAST জাতীয়: 01730-329945"],
        "ডিজিটাল অপরাধ":    ["সাইবার সাপোর্ট: 01320-000888"],
        "যৌন হয়রানি":       ["জাতীয় আইনি সহায়তা: 16430"],
    },
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


def district_keyboard():
    return ReplyKeyboardMarkup([
        ["ঢাকা", "চট্টগ্রাম"],
        ["রাজশাহী", "খুলনা"],
        ["সিলেট", "বরিশাল"],
        ["ময়মনসিংহ", "রংপুর"],
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
        ["ভোর (৪টা-৬টা)", "সকাল (৬টা-১২টা)"],
        ["দুপুর (১২টা-৩টা)", "বিকেল (৩টা-৬টা)"],
        ["সন্ধ্যা (৬টা-৯টা)", "রাত (৯টা-১২টা)"],
        ["গভীর রাত (১২টা-৪টা)", "সঠিক সময় মনে নেই"],
    ], resize_keyboard=True)


def relation_keyboard():
    return ReplyKeyboardMarkup([
        ["পরিবারের সদস্য", "প্রতিবেশী"],
        ["শিক্ষক", "কর্মক্ষেত্রের পরিচিত"],
        ["অপরিচিত ব্যক্তি", "বন্ধু বা পরিচিত"],
        ["পরিবহন চালক", "অন্য কেউ"],
    ], resize_keyboard=True)


def witness_keyboard():
    return ReplyKeyboardMarkup([
        ["হ্যাঁ, সাক্ষী আছে"],
        ["না, কোনো সাক্ষী নেই"],
        ["নিশ্চিত নই"],
    ], resize_keyboard=True)


def skip_keyboard():
    return ReplyKeyboardMarkup([
        ["এড়িয়ে যান (তথ্য নেই)"],
    ], resize_keyboard=True)


def confirm_keyboard():
    return ReplyKeyboardMarkup([
        ["✅ হ্যাঁ, PDF তৈরি করুন"],
        ["✏️ না, নতুন করে শুরু করুন"],
        ["❌ বাতিল করুন"],
    ], resize_keyboard=True)


# ─────────────────────────────────────────────────────────────────
#  PDF GENERATOR — Bangladesh FIR Format
# ─────────────────────────────────────────────────────────────────

def build_fir_pdf(d: dict) -> bytes:
    """
    Build a proper Bangladesh Police FIR application PDF.
    d = dictionary with all user answers
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=1.5*cm, bottomMargin=1.5*cm,
        leftMargin=2.5*cm, rightMargin=2.5*cm,
    )

    BN_REG  = BN()
    BN_BOLD = BNB()

    def P(text, font=None, size=11, bold=False, align="LEFT", color="#000000",
          space_before=0, space_after=6):
        f = font or (BN_BOLD if bold else BN_REG)
        al = {
            "LEFT": 0, "CENTER": 1, "RIGHT": 2, "JUSTIFY": 4
        }.get(align, 0)
        style = ParagraphStyle(
            "s",
            fontName=f, fontSize=size,
            textColor=colors.HexColor(color),
            alignment=al,
            spaceBefore=space_before,
            spaceAfter=space_after,
            leading=size * 1.6,
        )
        return Paragraph(text, style)

    now  = datetime.now()
    ref  = f"OBH-{now.strftime('%Y%m%d%H%M%S')}"
    date = now.strftime("%d/%m/%Y")

    elems = []

    # ── TOP HEADER ─────────────────────────────────────────────
    elems.append(P("গণপ্রজাতন্ত্রী বাংলাদেশ সরকার",
                   bold=True, size=13, align="CENTER", color="#0D2B5E"))
    elems.append(P("বাংলাদেশ পুলিশ",
                   bold=True, size=12, align="CENTER", color="#0D2B5E"))
    elems.append(Spacer(1, 2*mm))
    elems.append(HRFlowable(width="100%", thickness=2,
                             color=colors.HexColor("#0D2B5E")))
    elems.append(Spacer(1, 2*mm))
    elems.append(P("প্রাথমিক তথ্য বিবরণী (FIR) আবেদনপত্র",
                   bold=True, size=14, align="CENTER", color="#B03A2E"))
    elems.append(P("First Information Report — Initial Application",
                   size=10, align="CENTER", color="#555555"))
    elems.append(HRFlowable(width="100%", thickness=1,
                             color=colors.HexColor("#CCCCCC")))
    elems.append(Spacer(1, 3*mm))

    # Ref + Date row
    ref_table = Table(
        [[P(f"রিপোর্ট আইডি: {ref}", size=9, color="#555555"),
          P(f"তারিখ: {date}", size=9, align="RIGHT", color="#555555")]],
        colWidths=["60%", "40%"],
    )
    ref_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F4F6F8")),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    elems.append(ref_table)
    elems.append(Spacer(1, 4*mm))

    # ── TO SECTION ─────────────────────────────────────────────
    elems.append(P("বরাবর,", bold=True, size=11))
    station = d.get("station", "___________")
    elems.append(P(f"অফিসার ইনচার্জ", size=11))
    elems.append(P(f"{station} থানা", size=11))
    elems.append(P(f"জেলা: {d.get('district', '___________')}", size=11))
    elems.append(Spacer(1, 3*mm))

    # ── SUBJECT ────────────────────────────────────────────────
    elems.append(P(
        "বিষয়: নারী ও শিশু নির্যাতন দমন আইন ২০০০ এর ধারা ৯ এবং "
        "দণ্ডবিধি ধারা ৩৭৬ অনুযায়ী ধর্ষণ/যৌন নির্যাতনের অভিযোগে "
        "প্রাথমিক তথ্য বিবরণী দাখিল প্রসঙ্গে।",
        bold=True, size=10, color="#0D2B5E", space_before=2, space_after=6,
    ))
    elems.append(HRFlowable(width="100%", thickness=0.5,
                             color=colors.HexColor("#CCCCCC")))
    elems.append(Spacer(1, 3*mm))

    # ── OPENING ────────────────────────────────────────────────
    elems.append(P(
        "মহোদয়,",
        bold=True, size=11, space_after=4,
    ))
    elems.append(P(
        "আমি নিম্নস্বাক্ষরকারী আপনার নিকট নিম্নলিখিত ঘটনা সম্পর্কে "
        "প্রাথমিক তথ্য বিবরণী দাখিল করছি এবং অপরাধীদের বিরুদ্ধে "
        "আইনানুগ ব্যবস্থা গ্রহণের জন্য বিনীতভাবে আবেদন জানাচ্ছি।",
        size=11, space_after=6,
    ))
    elems.append(Spacer(1, 3*mm))

    # ── SECTION 1: APPLICANT INFO ──────────────────────────────
    def section_header(text):
        elems.append(Spacer(1, 2*mm))
        t = Table([[P(f"  {text}", bold=True, size=11,
                      color="#FFFFFF", space_before=2, space_after=2)]],
                  colWidths=["100%"])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0D2B5E")),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        elems.append(t)
        elems.append(Spacer(1, 2*mm))

    def info_row(label, value):
        val = value if value and value != "এড়িয়ে যান (তথ্য নেই)" else "—"
        return [
            P(label, bold=True, size=10, space_after=3),
            P(":", size=10),
            P(val, size=10, space_after=3),
        ]

    section_header("বিভাগ ১: আবেদনকারীর তথ্য")
    info_data = [
        info_row("আবেদনকারীর নাম",  d.get("name", "")),
        info_row("পিতার নাম",        d.get("father", "")),
        info_row("মাতার নাম",        d.get("mother", "")),
        info_row("বয়স",              d.get("age", "")),
        info_row("জাতীয় পরিচয়পত্র নম্বর", d.get("nid", "")),
        info_row("স্থায়ী ঠিকানা",   d.get("paddr", "")),
        info_row("বর্তমান ঠিকানা",  d.get("caddr", "")),
        info_row("মোবাইল নম্বর",    d.get("mobile", "")),
    ]
    t1 = Table(info_data, colWidths=["38%", "3%", "59%"])
    t1.setStyle(TableStyle([
        ("GRID",       (0, 0), (-1, -1), 0.3, colors.HexColor("#DDDDDD")),
        ("PADDING",    (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1),
         [colors.HexColor("#F9F9F9"), colors.white]),
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
    ]))
    elems.append(t1)

    # ── SECTION 2: INCIDENT INFO ───────────────────────────────
    section_header("বিভাগ ২: ঘটনার বিবরণ")
    inc_data = [
        info_row("ঘটনার তারিখ",       d.get("idate", "")),
        info_row("ঘটনার সময়",         d.get("itime", "")),
        info_row("ঘটনার স্থান",        d.get("iloc", "")),
        info_row("থানা",               d.get("station", "")),
        info_row("অভিযুক্তের সাথে সম্পর্ক", d.get("relation", "")),
        info_row("সাক্ষী",             d.get("witness", "")),
    ]
    t2 = Table(inc_data, colWidths=["38%", "3%", "59%"])
    t2.setStyle(TableStyle([
        ("GRID",       (0, 0), (-1, -1), 0.3, colors.HexColor("#DDDDDD")),
        ("PADDING",    (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1),
         [colors.HexColor("#F9F9F9"), colors.white]),
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
    ]))
    elems.append(t2)

    # ── SECTION 3: DESCRIPTION ─────────────────────────────────
    section_header("বিভাগ ৩: ঘটনার বিস্তারিত বর্ণনা")
    desc_text = d.get("desc", "—")
    desc_table = Table(
        [[P(desc_text, size=11, space_after=0)]],
        colWidths=["100%"],
    )
    desc_table.setStyle(TableStyle([
        ("BOX",     (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFFAF9")),
        ("MINROWHEIGHT", (0, 0), (-1, -1), 2.5*cm),
        ("VALIGN",  (0, 0), (-1, -1), "TOP"),
    ]))
    elems.append(desc_table)

    # ── SECTION 4: LEGAL BASIS ─────────────────────────────────
    section_header("বিভাগ ৪: প্রযোজ্য আইন ও ধারা")
    law_data = [
        [P("আইনের নাম", bold=True, size=10),
         P("ধারা", bold=True, size=10),
         P("শাস্তি", bold=True, size=10)],
        [P("নারী ও শিশু নির্যাতন দমন আইন ২০০০", size=10),
         P("ধারা ৯(১)", size=10),
         P("যাবজ্জীবন কারাদণ্ড", size=10)],
        [P("দণ্ডবিধি", size=10),
         P("ধারা ৩৭৬", size=10),
         P("ন্যূনতম ৭ বছর থেকে যাবজ্জীবন", size=10)],
        [P("নারী ও শিশু আইন ২০০০\n(ভিকটিম ১৮ বছরের নিচে হলে)", size=10),
         P("ধারা ৯(৪)", size=10),
         P("মৃত্যুদণ্ড বা যাবজ্জীবন", size=10)],
    ]
    t3 = Table(law_data, colWidths=["45%", "20%", "35%"])
    t3.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0), colors.HexColor("#1A56A4")),
        ("TEXTCOLOR",      (0, 0), (-1, 0), colors.white),
        ("GRID",           (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("PADDING",        (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#F4F6F8"), colors.white]),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elems.append(t3)

    # ── SECTION 5: PRAYER ──────────────────────────────────────
    section_header("বিভাগ ৫: আবেদন")
    elems.append(P(
        "অতএব, মহোদয়ের নিকট বিনীত আবেদন এই যে, উপরোক্ত বর্ণিত "
        "ঘটনার সুষ্ঠু তদন্ত করে অপরাধীদের বিরুদ্ধে নারী ও শিশু "
        "নির্যাতন দমন আইন ২০০০ এর ধারা ৯ ও দণ্ডবিধি ধারা ৩৭৬ "
        "অনুযায়ী আইনানুগ ব্যবস্থা গ্রহণ করে ন্যায়বিচার নিশ্চিত "
        "করার জন্য বিনীতভাবে প্রার্থনা করছি।",
        size=11, space_after=8,
    ))
    elems.append(Spacer(1, 5*mm))

    # ── SIGNATURE BLOCK ────────────────────────────────────────
    sig_data = [
        [
            P("আবেদনকারীর স্বাক্ষর:\n\n\n___________________________\n"
              + d.get("name", "আবেদনকারী") + "\n" + date,
              size=10, align="LEFT"),
            P("অফিসার ইনচার্জের সিল ও স্বাক্ষর:\n\n\n"
              "___________________________\n"
              + station + " থানা",
              size=10, align="LEFT"),
        ]
    ]
    t4 = Table(sig_data, colWidths=["50%", "50%"])
    t4.setStyle(TableStyle([
        ("BOX",     (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("PADDING", (0, 0), (-1, -1), 10),
        ("VALIGN",  (0, 0), (-1, -1), "TOP"),
    ]))
    elems.append(t4)
    elems.append(Spacer(1, 5*mm))

    # ── SUPPORT INFO BOX ───────────────────────────────────────
    support_data = [[
        P(
            "বিনামূল্যে সহায়তা:  BLAST: 01730-329945  |  "
            "ASK: 01730-029945  |  আইনি সহায়তা: 16430  |  "
            "জরুরি সেবা: 999  |  OCC ঢাকা: 02-55165088",
            size=9, align="CENTER", color="#FFFFFF",
        )
    ]]
    t5 = Table(support_data, colWidths=["100%"])
    t5.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1A7A4A")),
        ("PADDING",    (0, 0), (-1, -1), 6),
    ]))
    elems.append(t5)

    # ── FOOTER ─────────────────────────────────────────────────
    elems.append(Spacer(1, 2*mm))
    footer_data = [[
        P(f"তৈরি: @ObhoyBDbot", size=8, color="#888888"),
        P(f"{now.strftime('%d/%m/%Y %H:%M')}", size=8,
          align="CENTER", color="#888888"),
        P("obhoy.com", size=8, align="RIGHT", color="#888888"),
    ]]
    tf = Table(footer_data, colWidths=["33%", "34%", "33%"])
    tf.setStyle(TableStyle([("PADDING", (0, 0), (-1, -1), 2)]))
    elems.append(tf)

    doc.build(elems)
    buf.seek(0)
    return buf.read()


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
        "📜 আইন ও শাস্তি — ৬টি সম্পূর্ণ আইন বিস্তারিত\n"
        "📋 FIR আবেদন — তথ্য দিন, PDF ডাউনলোড করুন\n"
        "👩‍⚖️ আইনজীবী — জেলা ও কেস অনুযায়ী খুঁজুন\n"
        "📞 হেল্পলাইন — সব বিভাগের বিস্তারিত নম্বর\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "জরুরি প্রয়োজনে এখনই কল করুন: 999\n\n"
        "নিচের মেনু থেকে বেছে নিন",
        reply_markup=main_keyboard()
    )
    return MAIN_MENU


# ─────────────────────────────────────────────────────────────────
#  MAIN MENU HANDLER
# ─────────────────────────────────────────────────────────────────

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "আইন" in text:
        await update.message.reply_text(
            "📜 আইন ও শাস্তি\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "কোন আইন সম্পর্কে জানতে চান?\n"
            "নিচের মেনু থেকে বেছে নিন",
            reply_markup=law_keyboard()
        )
        return LAW_MENU

    elif "FIR" in text or "আবেদন" in text:
        context.user_data['fir'] = {}
        await update.message.reply_text(
            "📋 FIR আবেদনপত্র তৈরি করুন\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "আমি আপনাকে ১৫টি প্রশ্ন করব।\n"
            "উত্তর দিলেই একটি সম্পূর্ণ\n"
            "আইনি FIR আবেদনপত্র PDF তৈরি হবে।\n\n"
            "যেটি আপনি থানায় জমা দিতে পারবেন।\n\n"
            "আপনার পরিচয় সম্পূর্ণ গোপন থাকবে।\n"
            "বাতিল করতে যেকোনো সময় /cancel লিখুন\n\n"
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
            "আপনি কোন বিভাগে আছেন?\n"
            "নিচের মেনু থেকে বেছে নিন",
            reply_markup=district_keyboard()
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
            reply_markup=district_keyboard()
        )
        return HELP_DIST

    elif "মূল মেনু" in text or "ফিরুন" in text:
        await update.message.reply_text(
            "মূল মেনুতে ফিরে এসেছেন।",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU

    else:
        await update.message.reply_text(
            "নিচের মেনু থেকে বেছে নিন\n"
            "জরুরি সাহায্যের জন্য: 999",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU


# ─────────────────────────────────────────────────────────────────
#  LAW HANDLERS
# ─────────────────────────────────────────────────────────────────

async def law_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "মূল মেনু" in text or "ফিরুন" in text:
        await update.message.reply_text(
            "মূল মেনুতে ফিরে এসেছেন।",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU

    for key in LAWS:
        if text.startswith(key):
            await update.message.reply_text(
                LAWS[key],
                reply_markup=law_keyboard()
            )
            return LAW_MENU

    await update.message.reply_text(
        "মেনু থেকে বেছে নিন",
        reply_markup=law_keyboard()
    )
    return LAW_MENU


# ─────────────────────────────────────────────────────────────────
#  HELPLINE DISTRICT HANDLER
# ─────────────────────────────────────────────────────────────────

async def help_dist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "মূল মেনু" in text or "ফিরুন" in text:
        await update.message.reply_text(
            "মূল মেনুতে ফিরে এসেছেন।",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU

    for dist, info in HELPLINES.items():
        if dist in text:
            msg = (
                f"{info['emoji']} {dist} বিভাগের সম্পূর্ণ নম্বর\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🚔 পুলিশ: {info['police']}\n\n"
                f"🏥 OCC কেন্দ্র: {info['occ']}\n\n"
                f"⚖️ BLAST: {info['blast']}\n\n"
                f"⚖️ অন্য NGO: {info['ask']}\n\n"
                f"👮‍♀️ {info['women']}\n\n"
                f"📋 বিনামূল্যে আইনি সেবা: {info['legal']}\n\n"
                f"👶 {info['child']}\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "জাতীয় জরুরি সেবা: 999\n"
                "বিনামূল্যে আইনজীবী: 16430"
            )
            await update.message.reply_text(
                msg, reply_markup=district_keyboard()
            )
            return HELP_DIST

    await update.message.reply_text(
        "বিভাগের নাম বেছে নিন",
        reply_markup=district_keyboard()
    )
    return HELP_DIST


# ─────────────────────────────────────────────────────────────────
#  FIR HANDLERS — ১৫টি প্রশ্ন
# ─────────────────────────────────────────────────────────────────

async def fir_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault('fir', {})['name'] = update.message.text
    await update.message.reply_text(
        "প্রশ্ন ২/১৫\n\n"
        "পিতার নাম কী?",
        reply_markup=skip_keyboard()
    )
    return FIR_FATHER


async def fir_father(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fir']['father'] = update.message.text
    await update.message.reply_text(
        "প্রশ্ন ৩/১৫\n\n"
        "মাতার নাম কী?",
        reply_markup=skip_keyboard()
    )
    return FIR_MOTHER


async def fir_mother(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fir']['mother'] = update.message.text
    await update.message.reply_text(
        "প্রশ্ন ৪/১৫\n\n"
        "বয়স কত?\n"
        "(সংখ্যায় লিখুন, যেমন: ২২)",
        reply_markup=ReplyKeyboardRemove()
    )
    return FIR_AGE


async def fir_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fir']['age'] = update.message.text
    await update.message.reply_text(
        "প্রশ্ন ৫/১৫\n\n"
        "জাতীয় পরিচয়পত্র নম্বর (NID)?\n"
        "(না থাকলে বা বলতে না চাইলে 'এড়িয়ে যান' বাটন চাপুন)",
        reply_markup=skip_keyboard()
    )
    return FIR_NID


async def fir_nid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fir']['nid'] = update.message.text
    await update.message.reply_text(
        "প্রশ্ন ৬/১৫\n\n"
        "স্থায়ী ঠিকানা কী?\n"
        "(গ্রাম/মহল্লা, উপজেলা, জেলা লিখুন)",
        reply_markup=skip_keyboard()
    )
    return FIR_PADDR


async def fir_paddr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fir']['paddr'] = update.message.text
    await update.message.reply_text(
        "প্রশ্ন ৭/১৫\n\n"
        "বর্তমান ঠিকানা কী?\n"
        "(স্থায়ী ঠিকানার মতো হলে 'এড়িয়ে যান' বাটন চাপুন)",
        reply_markup=skip_keyboard()
    )
    return FIR_CADDR


async def fir_caddr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fir']['caddr'] = update.message.text
    await update.message.reply_text(
        "প্রশ্ন ৮/১৫\n\n"
        "মোবাইল নম্বর কী?\n"
        "(যোগাযোগের জন্য — না দিতে চাইলে 'এড়িয়ে যান' বাটন চাপুন)",
        reply_markup=skip_keyboard()
    )
    return FIR_MOBILE


async def fir_mobile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fir']['mobile'] = update.message.text
    await update.message.reply_text(
        "প্রশ্ন ৯/১৫\n\n"
        "কোন থানায় FIR দাখিল করতে চান?\n"
        "(থানার নাম লিখুন, যেমন: মিরপুর থানা, মোহাম্মদপুর থানা)",
        reply_markup=ReplyKeyboardRemove()
    )
    return FIR_STATION


async def fir_station(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fir']['station'] = update.message.text
    await update.message.reply_text(
        "প্রশ্ন ১০/১৫\n\n"
        "ঘটনাটি কোন জেলায় ঘটেছে?\n"
        "নিচের মেনু থেকে বেছে নিন",
        reply_markup=district_keyboard()
    )
    return FIR_IDATE  # we use district next before date


async def fir_idate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # If district was selected, save it and ask for date
    if text in HELPLINES:
        context.user_data['fir']['district'] = text
        await update.message.reply_text(
            "প্রশ্ন ১১/১৫\n\n"
            "ঘটনাটি কবে ঘটেছে?\n"
            "(তারিখ লিখুন, যেমন: ১৫ মার্চ ২০২৬\n"
            "অথবা আনুমানিক: মার্চ ২০২৬)",
            reply_markup=ReplyKeyboardRemove()
        )
        return FIR_ITIME

    # If they typed a date directly
    context.user_data['fir']['idate'] = text
    await update.message.reply_text(
        "প্রশ্ন ১২/১৫\n\n"
        "ঘটনাটি কোন সময়ে ঘটেছে?\n"
        "নিচের অপশন থেকে বেছে নিন",
        reply_markup=time_keyboard()
    )
    return FIR_ITIME


async def fir_itime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if 'idate' not in context.user_data.get('fir', {}):
        # date came here, save and ask time
        context.user_data['fir']['idate'] = text
        await update.message.reply_text(
            "প্রশ্ন ১২/১৫\n\n"
            "ঘটনাটি কোন সময়ে ঘটেছে?\n"
            "নিচের অপশন থেকে বেছে নিন",
            reply_markup=time_keyboard()
        )
        return FIR_ITIME

    context.user_data['fir']['itime'] = text
    await update.message.reply_text(
        "প্রশ্ন ১৩/১৫\n\n"
        "ঘটনাটি ঠিক কোথায় ঘটেছে?\n"
        "(বিস্তারিত স্থান লিখুন\n"
        "যেমন: গাজীপুর সদর, বাড়ির ভেতরে\n"
        "অথবা: মিরপুর ১০, স্কুলের পাশে)",
        reply_markup=ReplyKeyboardRemove()
    )
    return FIR_ILOC


async def fir_iloc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fir']['iloc'] = update.message.text
    await update.message.reply_text(
        "প্রশ্ন ১৪/১৫\n\n"
        "অভিযুক্ত ব্যক্তি ভিকটিমের কী হয়?\n"
        "নিচের অপশন থেকে বেছে নিন",
        reply_markup=relation_keyboard()
    )
    return FIR_REL


async def fir_rel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fir']['relation'] = update.message.text
    await update.message.reply_text(
        "প্রশ্ন ১৫/১৫\n\n"
        "সংক্ষেপে ঘটনার বর্ণনা লিখুন।\n\n"
        "নাম বলার দরকার নেই।\n"
        "শুধু কী ঘটেছে সেটুকু লিখুন।\n"
        "আপনি যতটুকু স্বাচ্ছন্দ্যবোধ করেন।",
        reply_markup=ReplyKeyboardRemove()
    )
    return FIR_DESC


async def fir_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fir']['desc'] = update.message.text
    await update.message.reply_text(
        "শেষ প্রশ্ন\n\n"
        "ঘটনার কোনো সাক্ষী আছে?",
        reply_markup=witness_keyboard()
    )
    return FIR_WITNESS


async def fir_witness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fir']['witness'] = update.message.text
    fir = context.user_data.get('fir', {})

    summary = (
        "সকল তথ্য সংগ্রহ হয়েছে!\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"নাম: {fir.get('name', '—')}\n"
        f"পিতা: {fir.get('father', '—')}\n"
        f"মাতা: {fir.get('mother', '—')}\n"
        f"বয়স: {fir.get('age', '—')}\n"
        f"NID: {fir.get('nid', '—')}\n"
        f"স্থায়ী ঠিকানা: {fir.get('paddr', '—')}\n"
        f"বর্তমান ঠিকানা: {fir.get('caddr', '—')}\n"
        f"মোবাইল: {fir.get('mobile', '—')}\n"
        f"থানা: {fir.get('station', '—')}\n"
        f"জেলা: {fir.get('district', '—')}\n"
        f"ঘটনার তারিখ: {fir.get('idate', '—')}\n"
        f"ঘটনার সময়: {fir.get('itime', '—')}\n"
        f"ঘটনার স্থান: {fir.get('iloc', '—')}\n"
        f"অভিযুক্তের সম্পর্ক: {fir.get('relation', '—')}\n"
        f"সাক্ষী: {fir.get('witness', '—')}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "এই তথ্য দিয়ে FIR আবেদনপত্র PDF তৈরি করব?"
    )
    await update.message.reply_text(summary, reply_markup=confirm_keyboard())
    return FIR_CONFIRM


async def fir_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "বাতিল" in text:
        await update.message.reply_text(
            "FIR তৈরি বাতিল হয়েছে।\n\n"
            "যেকোনো সময় আবার শুরু করতে\n"
            "'FIR আবেদন তৈরি করুন' বেছে নিন।",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU

    elif "নতুন করে" in text:
        context.user_data['fir'] = {}
        await update.message.reply_text(
            "নতুন করে শুরু হচ্ছে।\n\n"
            "প্রশ্ন ১/১৫\n\n"
            "আবেদনকারীর পুরো নাম কী?",
            reply_markup=ReplyKeyboardRemove()
        )
        return FIR_NAME

    elif "হ্যাঁ" in text or "PDF" in text:
        await update.message.reply_text(
            "আপনার FIR আবেদনপত্র তৈরি হচ্ছে...\n"
            "কয়েক সেকেন্ড অপেক্ষা করুন।",
            reply_markup=ReplyKeyboardRemove()
        )
        try:
            fir_data = context.user_data.get('fir', {})
            pdf_bytes = build_fir_pdf(fir_data)
            name = fir_data.get('name', 'applicant').replace(' ', '_')
            filename = f"Obhoy_FIR_{name}_{datetime.now().strftime('%Y%m%d')}.pdf"

            await update.message.reply_document(
                document=io.BytesIO(pdf_bytes),
                filename=filename,
                caption=(
                    "আপনার FIR আবেদনপত্র তৈরি হয়েছে!\n\n"
                    "এই PDF-এ আছে:\n"
                    "আপনার সম্পূর্ণ তথ্য\n"
                    "ঘটনার বিবরণ\n"
                    "প্রযোজ্য আইন ও ধারা\n"
                    "স্বাক্ষরের জায়গা\n\n"
                    "এখন কী করবেন:\n"
                    "১. এই PDF প্রিন্ট করুন\n"
                    "২. নিকটস্থ থানায় নিয়ে যান\n"
                    "৩. মহিলা পুলিশ অফিসার চাইতে পারেন\n"
                    "৪. স্বাক্ষর করে জমা দিন\n\n"
                    "বিনামূল্যে আইনজীবী: 16430\n"
                    "BLAST: 01730-329945\n"
                    "জরুরি সাহায্য: 999"
                )
            )
            await update.message.reply_text(
                "আর কোনো সাহায্য লাগলে\n"
                "নিচের মেনু থেকে বেছে নিন।",
                reply_markup=main_keyboard()
            )

        except Exception as e:
            logger.error(f"PDF error: {e}")
            await update.message.reply_text(
                "দুঃখিত, PDF তৈরিতে সমস্যা হয়েছে।\n\n"
                "সরাসরি সাহায্য নিন:\n"
                "BLAST: 01730-329945\n"
                "আইনি সহায়তা: 16430",
                reply_markup=main_keyboard()
            )
        return MAIN_MENU

    else:
        await update.message.reply_text(
            "নিচের অপশন থেকে বেছে নিন",
            reply_markup=confirm_keyboard()
        )
        return FIR_CONFIRM


# ─────────────────────────────────────────────────────────────────
#  LAWYER HANDLERS
# ─────────────────────────────────────────────────────────────────

async def law_dist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "মূল মেনু" in text or "ফিরুন" in text:
        await update.message.reply_text(
            "মূল মেনুতে ফিরে এসেছেন।",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU

    matched = "অন্যান্য"
    for d in LAWYERS:
        if d in text:
            matched = d
            break

    context.user_data['ldist'] = matched
    await update.message.reply_text(
        f"{matched} বিভাগ নোট হয়েছে।\n\n"
        "কী ধরনের মামলায় আইনজীবী দরকার?\n"
        "নিচের অপশন থেকে বেছে নিন",
        reply_markup=case_keyboard()
    )
    return LAW_TYPE


async def law_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "মূল মেনু" in text or "ফিরুন" in text:
        await update.message.reply_text(
            "মূল মেনুতে ফিরে এসেছেন।",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU

    case_map = {
        "ধর্ষণ":    "ধর্ষণ মামলা",
        "শিশু":     "শিশু নির্যাতন",
        "ডিজিটাল": "ডিজিটাল অপরাধ",
        "হয়রানি":  "যৌন হয়রানি",
    }
    case_key = "ধর্ষণ মামলা"
    for k, v in case_map.items():
        if k in text:
            case_key = v
            break

    dist = context.user_data.get('ldist', 'অন্যান্য')
    lawyers_list = (
        LAWYERS.get(dist, {}).get(case_key)
        or LAWYERS['অন্যান্য'].get(case_key, [])
    )
    contacts = "\n".join([f"✅ {l}" for l in lawyers_list])

    await update.message.reply_text(
        f"👩‍⚖️ {dist} — {case_key}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{contacts}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "বিনামূল্যে জাতীয় আইনি সহায়তা: 16430\n"
        "OCC বিনামূল্যে চিকিৎসা: 02-55165088\n"
        "জরুরি সাহায্য: 999",
        reply_markup=main_keyboard()
    )
    return MAIN_MENU


# ─────────────────────────────────────────────────────────────────
#  CANCEL + ERROR
# ─────────────────────────────────────────────────────────────────

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "বাতিল করা হয়েছে।\n\n"
        "যেকোনো সময় /start লিখে আবার শুরু করুন।\n"
        "জরুরি সাহায্যে: 999",
        reply_markup=main_keyboard()
    )
    return MAIN_MENU


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}")


# ─────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────

def main():
    if not TOKEN:
        raise ValueError("TOKEN পাওয়া যায়নি। Railway Variables-এ TOKEN যোগ করুন।")

    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
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
            FIR_IDATE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_idate)],
            FIR_ITIME:   [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_itime)],
            FIR_ILOC:    [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_iloc)],
            FIR_REL:     [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_rel)],
            FIR_DESC:    [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_desc)],
            FIR_WITNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_witness)],
            FIR_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_confirm)],
            LAW_DIST:    [MessageHandler(filters.TEXT & ~filters.COMMAND, law_dist)],
            LAW_TYPE:    [MessageHandler(filters.TEXT & ~filters.COMMAND, law_type)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),
        ],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_error_handler(error_handler)

    print("✅ Obhoy Bot v2 চালু হয়েছে")
    print("🛡️ অভয় — নির্ভয়ে কথা বলুন 🇧🇩")

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
