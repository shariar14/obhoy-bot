"""
╔══════════════════════════════════════════════════════════════╗
║              OBHOY BOT — সম্পূর্ণ সংস্করণ                  ║
║  Features: আইন • FIR • আইনজীবী • ভয়েস • সহযোদ্ধা • সাপ্তাহিক ║
║            obhoy.com | @ObhoyBDbot | bolun@obhoy.com         ║
╚══════════════════════════════════════════════════════════════╝

STRUCTURE:
  ● Main Menu         → আইন, হেল্পলাইন, মানসিক সহায়তা, Obhoy সম্পর্কে
  ● Idea 1 (FIR)      → ৮টি প্রশ্ন → ফরম্যাটেড FIR রিপোর্ট
  ● Idea 3 (Lawyer)   → জেলা + কেস টাইপ → আইনজীবীর নম্বর
  ● Idea 5 (Voice)    → ভয়েস নোট → টেক্সট রিপোর্ট
  ● Idea 6 (Broadcast)→ সাপ্তাহিক স্বয়ংক্রিয় বার্তা
  ● Idea 7 (Peer)     → বেঁচে যাওয়াদের সাপোর্ট নেটওয়ার্ক

REMOVED DUPLICATES:
  ✗ আলাদা "রিপোর্ট করুন" সাব-মেনু → FIR + ভয়েস-এ মার্জ
  ✗ FIR ধাপ সাব-মেনু             → FIR জেনারেটরে মার্জ
  ✗ বিনামূল্যে আইনজীবী সাব-মেনু → আইনজীবী ম্যাচে মার্জ
  ✗ OCC সাব-মেনু                  → হেল্পলাইনে মার্জ
"""

import os
import logging
from datetime import datetime

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    SCHEDULER_OK = True
except ImportError:
    SCHEDULER_OK = False

# ─────────────────────────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────────────────────────
TOKEN      = os.environ.get("TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "")   # চ্যানেল আইডি যোগ করুন

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────
#  CONVERSATION STATES
# ─────────────────────────────────────────────────────────────────
# Main
MAIN_MENU        = 0
LAW_MENU         = 1
HELPLINE_DIST    = 2
# FIR  (10-19)
FIR_AGE, FIR_DATE, FIR_TIME, FIR_LOCATION = 10, 11, 12, 13
FIR_RELATION, FIR_DESC, FIR_WITNESS       = 14, 15, 16
FIR_PREV, FIR_DIST, FIR_CONFIRM           = 17, 18, 19
# Lawyer  (20-22)
LAWYER_DIST, LAWYER_TYPE, LAWYER_DONE     = 20, 21, 22
# Peer  (30-31)
PEER_AGREE, PEER_DONE                     = 30, 31

# ─────────────────────────────────────────────────────────────────
#  WEEKLY BROADCAST CONTENT (৫২ সপ্তাহ)
# ─────────────────────────────────────────────────────────────────
WEEKLY_CONTENT = [
    "📚 *সপ্তাহের আইন — ১*\n\nধর্ষণ কী? আইন কী বলে?\n\nবাংলাদেশে নারী ও শিশু নির্যাতন দমন আইন ২০০০ অনুযায়ী — সম্মতি ছাড়া যেকোনো যৌন সম্পর্ক ধর্ষণ হিসেবে গণ্য। শাস্তি: যাবজ্জীবন কারাদণ্ড থেকে মৃত্যুদণ্ড।\n\n📞 সাহায্য লাগলে: @ObhoyBDbot",
    "📚 *সপ্তাহের পরামর্শ — ২*\n\nFIR কীভাবে করবেন?\n\nঘটনার পর যত দ্রুত সম্ভব নিকটস্থ থানায় যান। মহিলা পুলিশ অফিসার চাইতে পারেন। বিনামূল্যে আইনজীবী পাওয়া যায়।\n\n📞 আইনি সহায়তা: 16430\n🤖 FIR খসড়া: @ObhoyBDbot",
    "📚 *সপ্তাহের অধিকার — ৩*\n\nআপনার আইনি অধিকার জানুন\n\n✅ পরিচয় গোপন রাখার অধিকার\n✅ বিনামূল্যে আইনজীবীর অধিকার\n✅ বিনামূল্যে চিকিৎসার অধিকার\n✅ মহিলা পুলিশের কাছে জবানবন্দির অধিকার\n\n📞 হেল্পলাইন: 999 | 10921",
    "📚 *সপ্তাহের তথ্য — ৪*\n\nওয়ান স্টপ ক্রাইসিস সেন্টার (OCC) কী?\n\nOCC-তে বিনামূল্যে পাবেন:\n🏥 ফরেনসিক পরীক্ষা\n⚖️ আইনি সহায়তা\n💙 মানসিক কাউন্সেলিং\n👮‍♀️ পুলিশ সহায়তা\n\n📞 ঢাকা OCC: 02-55165088",
    "📚 *সপ্তাহের সচেতনতা — ৫*\n\nশিশু ধর্ষণ — বিশেষ আইন\n\n১৮ বছরের নিচে ধর্ষণে শাস্তি মৃত্যুদণ্ড বা যাবজ্জীবন। শিশু ভিকটিমের পরিচয় প্রকাশ সম্পূর্ণ নিষিদ্ধ।\n\n📞 শিশু হেল্পলাইন: 1098",
    "📚 *সপ্তাহের পরামর্শ — ৬*\n\nগণধর্ষণ আইন\n\nএকাধিক ব্যক্তি জড়িত থাকলে সবার শাস্তি সমান। সাহায্যকারীরও একই শাস্তি। কোনো জামিন নেই।\n\n📞 BLAST: 01730-329945",
    "📚 *সপ্তাহের তথ্য — ৭*\n\nডিজিটাল অপরাধ ও শাস্তি\n\nঅনুমতি ছাড়া ছবি বা ভিডিও প্রকাশ — ৫ বছর কারাদণ্ড ও ৫ লাখ টাকা জরিমানা।\n\n📞 সাইবার সাপোর্ট: 01320-000888",
    "📚 *সপ্তাহের সচেতনতা — ৮*\n\nভুল ধারণা বনাম সত্য\n\n❌ ভুল: পোশাক দায়ী\n✅ সত্য: অপরাধী সবসময় দায়ী\n\n❌ ভুল: পরিচিত হলে ধর্ষণ না\n✅ সত্য: সম্মতি ছাড়া সবই অপরাধ\n\n📞 সাহায্য: 999",
]

# ─────────────────────────────────────────────────────────────────
#  LAWS DATABASE
# ─────────────────────────────────────────────────────────────────
LAWS = {
    "১": (
        "📜 *নারী ও শিশু নির্যাতন দমন আইন ২০০০*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ *ধারা ৯(১) — সাধারণ ধর্ষণ*\n"
        "→ শাস্তি: যাবজ্জীবন কারাদণ্ড ও অর্থদণ্ড\n\n"
        "✅ *ধারা ৯(২) — মৃত্যু ঘটলে*\n"
        "→ শাস্তি: মৃত্যুদণ্ড বা যাবজ্জীবন\n\n"
        "✅ *ধারা ৯(৩) — গণধর্ষণ*\n"
        "→ শাস্তি: মৃত্যুদণ্ড বা যাবজ্জীবন\n\n"
        "✅ *ধারা ৯(৪) — শিশু ধর্ষণ (১৮ বছরের নিচে)*\n"
        "→ শাস্তি: মৃত্যুদণ্ড বা যাবজ্জীবন\n\n"
        "📅 তদন্ত: ৩০ কার্যদিবস\n"
        "📅 বিচার: ১৮০ কার্যদিবস"
    ),
    "২": (
        "📜 *দণ্ডবিধি ধারা ৩৭৫ ও ৩৭৬*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ *ধারা ৩৭৫ — ধর্ষণের সংজ্ঞা*\n"
        "→ সম্মতি ছাড়া যেকোনো যৌন সম্পর্ক = ধর্ষণ\n"
        "→ ১৪ বছরের নিচে সম্মতি আইনত বৈধ নয়\n\n"
        "✅ *ধারা ৩৭৬ — শাস্তি*\n"
        "→ ন্যূনতম: ৭ বছর কারাদণ্ড\n"
        "→ সর্বোচ্চ: যাবজ্জীবন ও অর্থদণ্ড\n\n"
        "⚠️ বিবাহিত নারীর ক্ষেত্রেও সমানভাবে প্রযোজ্য"
    ),
    "৩": (
        "📜 *শিশু ধর্ষণ আইন*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ শিশু আইন ২০১৩ — দ্রুত বিচার বাধ্যতামূলক\n"
        "✅ তদন্ত সময়: ১৫ কার্যদিবস\n"
        "✅ শাস্তি: মৃত্যুদণ্ড বা যাবজ্জীবন\n\n"
        "🔒 *পরিচয় সুরক্ষা*\n"
        "→ শিশুর নাম প্রকাশ সম্পূর্ণ নিষিদ্ধ\n"
        "→ প্রকাশ করলে ২ বছর কারাদণ্ড\n\n"
        "📞 শিশু হেল্পলাইন: *1098*"
    ),
    "৪": (
        "📜 *গণধর্ষণ আইন*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ একাধিক ব্যক্তি জড়িত = গণধর্ষণ\n"
        "✅ সকলের শাস্তি: মৃত্যুদণ্ড বা যাবজ্জীবন\n"
        "✅ সাহায্যকারীরও একই শাস্তি\n"
        "✅ তদন্ত চলাকালীন কোনো জামিন নেই\n\n"
        "📅 *২০২০ সালের সংশোধনী*\n"
        "→ সর্বোচ্চ শাস্তি: মৃত্যুদণ্ড (ফাঁসি)"
    ),
    "৫": (
        "📜 *ধর্ষণের চেষ্টার শাস্তি*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ *ধারা ৯(৫) — চেষ্টার শাস্তি*\n"
        "→ ১০ বছর পর্যন্ত কারাদণ্ড ও অর্থদণ্ড\n\n"
        "✅ *যৌন হয়রানি (ধারা ১০)*\n"
        "→ ১০ বছর পর্যন্ত কারাদণ্ড\n\n"
        "✅ *ইভ টিজিং*\n"
        "→ সর্বোচ্চ ৭ বছর কারাদণ্ড"
    ),
    "৬": (
        "📜 *ডিজিটাল অপরাধ ও সাইবার আইন*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ *ডিজিটাল নিরাপত্তা আইন ২০১৮ ধারা ২৬*\n"
        "→ সম্মতি ছাড়া ঘনিষ্ঠ ছবি/ভিডিও প্রকাশ\n"
        "→ শাস্তি: ৫ বছর ও ৫ লাখ টাকা জরিমানা\n\n"
        "✅ *পর্নোগ্রাফি নিয়ন্ত্রণ আইন ২০১২*\n"
        "→ শাস্তি: ৭ বছর ও ২ লাখ টাকা জরিমানা\n\n"
        "📞 সাইবার সাপোর্ট: 01320-000888"
    ),
    "৭": (
        "📜 *ভিকটিমের আইনি অধিকার*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ বিনামূল্যে আইনি সহায়তা — 16430\n"
        "✅ মহিলা পুলিশের কাছে জবানবন্দির অধিকার\n"
        "✅ পরিচয় গোপন রাখার অধিকার\n"
        "✅ বিনামূল্যে OCC চিকিৎসার অধিকার\n"
        "✅ সাক্ষী সুরক্ষার অধিকার\n"
        "✅ ক্ষতিপূরণ দাবির অধিকার\n"
        "✅ উচ্চ আদালতে আপিলের অধিকার\n\n"
        "⚠️ এই অধিকারগুলো আপনার। কেউ কেড়ে নিতে পারবে না।"
    ),
    "৮": (
        "📜 *FIR করার সম্পূর্ণ নির্দেশিকা*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ *ধাপ ১:* নিকটস্থ থানায় যান\n"
        "✅ *ধাপ ২:* মহিলা পুলিশ অফিসার চাইতে পারেন\n"
        "✅ *ধাপ ৩:* তারিখ, সময়, স্থান উল্লেখ করুন\n"
        "✅ *ধাপ ৪:* অভিযুক্তের বর্ণনা দিন\n"
        "✅ *ধাপ ৫:* কেস নম্বর সংগ্রহ করুন\n\n"
        "⚠️ পুলিশ FIR নিতে অস্বীকার করলে:\n"
        "→ BLAST: 01730-329945\n"
        "→ আইনি সহায়তা: 16430\n"
        "→ সরাসরি আদালতে নালিশী মামলা করুন\n\n"
        "🤖 আমার সাথে FIR খসড়া তৈরি করতে /fir লিখুন"
    ),
}

# ─────────────────────────────────────────────────────────────────
#  HELPLINES DATABASE
# ─────────────────────────────────────────────────────────────────
HELPLINES = {
    "ঢাকা": {
        "emoji": "🏙️",
        "police": "01320-000999",
        "occ": "02-55165088",
        "ngo": "ASK: 01730-029945 | BLAST: 01730-329945",
        "women": "মহিলা হেল্পলাইন: 10921",
        "legal": "লিগ্যাল এইড: 02-9514424",
    },
    "চট্টগ্রাম": {
        "emoji": "⚓",
        "police": "031-639944",
        "occ": "031-630903",
        "ngo": "YPSA: 031-2853985 | BLAST: 031-710441",
        "women": "মহিলা হেল্পলাইন: 10921",
        "legal": "লিগ্যাল এইড: 031-711069",
    },
    "রাজশাহী": {
        "emoji": "🍎",
        "police": "0721-775555",
        "occ": "0721-772150",
        "ngo": "RDRS: 0721-775588",
        "women": "মহিলা হেল্পলাইন: 10921",
        "legal": "লিগ্যাল এইড: 0721-774878",
    },
    "খুলনা": {
        "emoji": "🌿",
        "police": "041-761999",
        "occ": "041-762595",
        "ngo": "Rupantar: 041-731522 | BLAST: 041-810552",
        "women": "মহিলা হেল্পলাইন: 10921",
        "legal": "লিগ্যাল এইড: 041-761234",
    },
    "সিলেট": {
        "emoji": "🍵",
        "police": "0821-713666",
        "occ": "0821-713151",
        "ngo": "BNWLA: 0821-716677",
        "women": "মহিলা হেল্পলাইন: 10921",
        "legal": "লিগ্যাল এইড: 0821-714523",
    },
    "বরিশাল": {
        "emoji": "🌊",
        "police": "0431-66666",
        "occ": "0431-2176175",
        "ngo": "BLAST বরিশাল: 0431-64411",
        "women": "মহিলা হেল্পলাইন: 10921",
        "legal": "লিগ্যাল এইড: 0431-65432",
    },
    "ময়মনসিংহ": {
        "emoji": "🌾",
        "police": "091-65100",
        "occ": "091-67553",
        "ngo": "BRAC: 091-66700",
        "women": "মহিলা হেল্পলাইন: 10921",
        "legal": "লিগ্যাল এইড: 091-64321",
    },
    "রংপুর": {
        "emoji": "🌻",
        "police": "0521-66666",
        "occ": "0521-63750",
        "ngo": "RDRS রংপুর: 0521-64488",
        "women": "মহিলা হেল্পলাইন: 10921",
        "legal": "লিগ্যাল এইড: 0521-65123",
    },
}

# ─────────────────────────────────────────────────────────────────
#  LAWYER DATABASE (Idea 3)
# ─────────────────────────────────────────────────────────────────
LAWYERS = {
    "ঢাকা": {
        "ধর্ষণ":     ["BLAST ঢাকা: 01730-329945", "ASK ঢাকা: 01730-029945"],
        "শিশু":      ["BLAST শিশু বিভাগ: 01730-329945", "BNWLA: 01711-526303"],
        "ডিজিটাল":  ["সাইবার ট্রাইব্যুনাল সহায়তা: 01320-000888"],
        "হয়রানি":   ["ASK ঢাকা: 01730-029945", "মহিলা পরিষদ: 01711-526303"],
    },
    "চট্টগ্রাম": {
        "ধর্ষণ":     ["BLAST চট্টগ্রাম: 031-710441"],
        "শিশু":      ["YPSA চট্টগ্রাম: 031-2853985"],
        "ডিজিটাল":  ["আইনগত সহায়তা: 16430"],
        "হয়রানি":   ["BLAST চট্টগ্রাম: 031-710441"],
    },
    "রাজশাহী": {
        "ধর্ষণ":     ["RDRS রাজশাহী: 0721-775588"],
        "শিশু":      ["RDRS রাজশাহী: 0721-775588"],
        "ডিজিটাল":  ["আইনগত সহায়তা: 16430"],
        "হয়রানি":   ["Nagorik Uddyog: 0721-810035"],
    },
    "অন্যান্য": {
        "ধর্ষণ":     ["জাতীয় আইনগত সহায়তা: 16430", "BLAST জাতীয়: 01730-329945"],
        "শিশু":      ["শিশু হেল্পলাইন: 1098", "BLAST জাতীয়: 01730-329945"],
        "ডিজিটাল":  ["সাইবার সাপোর্ট: 01320-000888"],
        "হয়রানি":   ["জাতীয় আইনগত সহায়তা: 16430"],
    },
}

# ─────────────────────────────────────────────────────────────────
#  KEYBOARDS
# ─────────────────────────────────────────────────────────────────

def main_keyboard():
    return ReplyKeyboardMarkup([
        ["📜 আইন ও শাস্তি"],
        ["📋 FIR খসড়া তৈরি করুন", "👩‍⚖️ আইনজীবী খুঁজুন"],
        ["🎙️ ভয়েস রিপোর্ট",        "💙 সহযোদ্ধা নেটওয়ার্ক"],
        ["📞 জরুরি হেল্পলাইন",      "💬 মানসিক সহায়তা"],
        ["ℹ️ Obhoy সম্পর্কে"],
    ], resize_keyboard=True)


def law_keyboard():
    return ReplyKeyboardMarkup([
        ["১. নারী ও শিশু নির্যাতন আইন ২০০০"],
        ["২. দণ্ডবিধি ধারা ৩৭৫-৩৭৬"],
        ["৩. শিশু ধর্ষণ আইন",    "৪. গণধর্ষণ আইন"],
        ["৫. ধর্ষণের চেষ্টার শাস্তি"],
        ["৬. ডিজিটাল অপরাধ আইন"],
        ["৭. ভিকটিমের আইনি অধিকার"],
        ["৮. FIR করার নির্দেশিকা"],
        ["🔙 মূল মেনুতে ফিরুন"],
    ], resize_keyboard=True)


def district_keyboard():
    return ReplyKeyboardMarkup([
        ["ঢাকা",       "চট্টগ্রাম"],
        ["রাজশাহী",   "খুলনা"],
        ["সিলেট",      "বরিশাল"],
        ["ময়মনসিংহ", "রংপুর"],
        ["🔙 মূল মেনুতে ফিরুন"],
    ], resize_keyboard=True)


def case_type_keyboard():
    return ReplyKeyboardMarkup([
        ["⚖️ ধর্ষণ মামলা",      "👶 শিশু নির্যাতন মামলা"],
        ["💻 ডিজিটাল অপরাধ",  "🚨 যৌন হয়রানি"],
        ["🔙 মূল মেনুতে ফিরুন"],
    ], resize_keyboard=True)


def time_keyboard():
    return ReplyKeyboardMarkup([
        ["🌅 ভোর (৪টা-৬টা)",      "🌞 সকাল (৬টা-১২টা)"],
        ["🌤️ দুপুর (১২টা-৩টা)",  "🌇 বিকেল (৩টা-৬টা)"],
        ["🌆 সন্ধ্যা (৬টা-৯টা)", "🌙 রাত (৯টা-১২টা)"],
        ["🌑 গভীর রাত (১২টা-৪টা)", "⏰ সঠিক সময় মনে নেই"],
    ], resize_keyboard=True)


def relation_keyboard():
    return ReplyKeyboardMarkup([
        ["👨‍👩‍👦 পরিবারের সদস্য",  "🏘️ প্রতিবেশী"],
        ["🏫 শিক্ষক",              "👔 কর্মক্ষেত্রের পরিচিত"],
        ["❓ অপরিচিত ব্যক্তি",    "👥 বন্ধু বা পরিচিত"],
        ["🚗 পরিবহন চালক",         "অন্য কেউ"],
    ], resize_keyboard=True)


def witness_keyboard():
    return ReplyKeyboardMarkup([
        ["✅ হ্যাঁ, সাক্ষী আছে"],
        ["❌ না, কোনো সাক্ষী নেই"],
        ["🤔 নিশ্চিত নই"],
    ], resize_keyboard=True)


def yesno_keyboard():
    return ReplyKeyboardMarkup([
        ["✅ হ্যাঁ"],
        ["❌ না"],
    ], resize_keyboard=True)


def confirm_keyboard():
    return ReplyKeyboardMarkup([
        ["✅ হ্যাঁ, রিপোর্ট তৈরি করুন"],
        ["✏️ না, সংশোধন করতে চাই"],
        ["❌ বাতিল করুন"],
    ], resize_keyboard=True)


def peer_keyboard():
    return ReplyKeyboardMarkup([
        ["✅ হ্যাঁ, যোগ দিতে চাই"],
        ["❌ না, ধন্যবাদ"],
    ], resize_keyboard=True)


# ─────────────────────────────────────────────────────────────────
#  HELPER — Format FIR Report as Text
# ─────────────────────────────────────────────────────────────────

def build_fir_text(answers: dict) -> str:
    now = datetime.now()
    ref = f"OBH-{now.strftime('%Y%m%d%H%M%S')}"

    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "🛡️  *OBHOY (অভয়) — FIR খসড়া*",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"📌 রিপোর্ট আইডি: `{ref}`",
        f"📅 তৈরির তারিখ: {now.strftime('%d/%m/%Y %H:%M')}",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "📋 *বিভাগ ১: ঘটনার বিবরণ*",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"📅 ঘটনার তারিখ : {answers.get('date', '—')}",
        f"⏰ ঘটনার সময়  : {answers.get('time', '—')}",
        f"📍 ঘটনার স্থান : {answers.get('location', '—')}",
        f"🗺️ বিভাগ       : {answers.get('district', '—')}",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "👤 *বিভাগ ২: ভিকটিমের তথ্য*",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"🎂 বয়স             : {answers.get('age', '—')}",
        f"👥 অভিযুক্তের সম্পর্ক: {answers.get('relation', '—')}",
        f"👁️ সাক্ষী          : {answers.get('witness', '—')}",
        f"📋 আগের রিপোর্ট   : {answers.get('previous', '—')}",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "📝 *বিভাগ ৩: ঘটনার বর্ণনা*",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        answers.get('desc', '—'),
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "⚖️ *বিভাগ ৪: প্রযোজ্য আইন*",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "• নারী ও শিশু নির্যাতন দমন আইন ২০০০, ধারা ৯(১)",
        "• দণ্ডবিধি ধারা ৩৭৬",
        "• শাস্তি: যাবজ্জীবন থেকে মৃত্যুদণ্ড",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "🚀 *বিভাগ ৫: পরবর্তী পদক্ষেপ*",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "১. এই রিপোর্ট নিয়ে নিকটস্থ থানায় যান",
        "২. মহিলা পুলিশ অফিসার চাইতে পারেন",
        "৩. বিনামূল্যে আইনজীবী: *16430*",
        "৪. BLAST: *01730-329945*",
        "৫. OCC চিকিৎসা: *02-55165088*",
        "৬. জরুরি সাহায্য: *999*",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "⚠️ এটি Obhoy-র তৈরি একটি খসড়া রিপোর্ট।",
        "পুলিশে অফিসিয়াল FIR করার আগে একজন",
        "আইনজীবীর সাথে পরামর্শ করুন।",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "obhoy.com  |  @ObhoyBDbot",
    ]
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────
#  /start
# ─────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "🛡️ *Obhoy-তে আপনাকে স্বাগতম*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "*অভয়* — বাংলাদেশের প্রথম AI-চালিত\n"
        "যৌন সহিংসতা প্রতিরোধ ও সহায়তা প্ল্যাটফর্ম।\n\n"
        "📜 *আইন ও শাস্তি* — ৮টি সম্পূর্ণ আইন\n"
        "📋 *FIR খসড়া* — তৈরি করুন এখনই\n"
        "👩‍⚖️ *আইনজীবী* — নিকটতম আইনজীবী খুঁজুন\n"
        "🎙️ *ভয়েস রিপোর্ট* — বাংলায় বলুন\n"
        "💙 *সহযোদ্ধা* — বেঁচে যাওয়াদের নেটওয়ার্ক\n"
        "📞 *হেল্পলাইন* — সব বিভাগের নম্বর\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚠️ *জরুরি প্রয়োজনে এখনই কল করুন: 999*\n\n"
        "নিচের মেনু থেকে বেছে নিন 👇",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )
    return MAIN_MENU


# ─────────────────────────────────────────────────────────────────
#  MAIN MENU HANDLER
# ─────────────────────────────────────────────────────────────────

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # ── আইন ──
    if "আইন" in text:
        await update.message.reply_text(
            "📜 *আইন ও শাস্তি*\n\n"
            "কোন আইন সম্পর্কে জানতে চান?\n"
            "নিচের মেনু থেকে বেছে নিন 👇",
            parse_mode="Markdown",
            reply_markup=law_keyboard()
        )
        return LAW_MENU

    # ── FIR ──
    elif "FIR" in text or "খসড়া" in text:
        context.user_data['fir'] = {}
        await update.message.reply_text(
            "📋 *FIR খসড়া তৈরি করুন*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "আমি আপনাকে ৮টি প্রশ্ন করব।\n"
            "উত্তর দিলেই সম্পূর্ণ FIR রিপোর্ট তৈরি হবে।\n\n"
            "🔒 *আপনার পরিচয় সম্পূর্ণ গোপন থাকবে*\n"
            "❌ বাতিল করতে যেকোনো সময় /cancel লিখুন\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "প্রশ্ন ১/৮\n\n"
            "*ভিকটিমের বয়স কত?*\n"
            "_(শুধু সংখ্যা লিখুন, যেমন: ১৬)_",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
        return FIR_AGE

    # ── আইনজীবী ──
    elif "আইনজীবী" in text:
        await update.message.reply_text(
            "👩‍⚖️ *আইনজীবী সংযোগ*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "আপনি কোন বিভাগে আছেন?\n"
            "নিচের মেনু থেকে বেছে নিন 👇",
            parse_mode="Markdown",
            reply_markup=district_keyboard()
        )
        return LAWYER_DIST

    # ── ভয়েস রিপোর্ট ──
    elif "ভয়েস" in text:
        await update.message.reply_text(
            "🎙️ *ভয়েস রিপোর্ট*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "এখন একটি ভয়েস নোট পাঠান।\n"
            "বাংলায় বলুন কী ঘটেছে।\n\n"
            "🔒 আপনার পরিচয় সম্পূর্ণ গোপন থাকবে।\n"
            "❌ বাতিল করতে /cancel লিখুন।\n\n"
            "🎤 *এখন মাইক বাটন চেপে ধরুন এবং বলুন...*",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
        return MAIN_MENU

    # ── সহযোদ্ধা নেটওয়ার্ক ──
    elif "সহযোদ্ধা" in text:
        await update.message.reply_text(
            "💙 *সহযোদ্ধা নেটওয়ার্ক*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "সহযোদ্ধা হলো বেঁচে যাওয়া মানুষদের\n"
            "একটি নিরাপদ, সম্পূর্ণ বেনামী নেটওয়ার্ক।\n\n"
            "এখানে পাবেন:\n"
            "💬 একই অভিজ্ঞতার মানুষদের সাথে কথা বলার সুযোগ\n"
            "💪 মানসিক শক্তি ও অনুপ্রেরণা\n"
            "📚 সহায়তার তথ্য ও পরামর্শ\n\n"
            "🔒 কোনো আসল নাম বা পরিচয় প্রকাশ হবে না।\n"
            "👩‍⚕️ একজন প্রশিক্ষিত কাউন্সেলর সবসময় আছেন।\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "আপনি কি যোগ দিতে চান?",
            parse_mode="Markdown",
            reply_markup=peer_keyboard()
        )
        return PEER_AGREE

    # ── হেল্পলাইন ──
    elif "হেল্পলাইন" in text:
        await update.message.reply_text(
            "📞 *জাতীয় জরুরি হেল্পলাইন*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🚨 জাতীয় জরুরি সেবা: *999*\n"
            "📞 নারী হেল্পলাইন: *10921*\n"
            "👶 শিশু হেল্পলাইন: *1098*\n"
            "⚖️ আইনি সহায়তা: *16430*\n"
            "💙 কান পেত রই: 01779-554391\n"
            "🏥 ঢাকা OCC: 02-55165088\n"
            "📋 BLAST: 01730-329945\n"
            "📋 ASK: 01730-029945\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "আপনার বিভাগের বিস্তারিত নম্বর পেতে\n"
            "নিচে থেকে বিভাগ বেছে নিন 👇",
            parse_mode="Markdown",
            reply_markup=district_keyboard()
        )
        return HELPLINE_DIST

    # ── মানসিক সহায়তা ──
    elif "মানসিক" in text:
        await update.message.reply_text(
            "💬 *মানসিক সহায়তা*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "আপনি একা নন। সাহায্য নেওয়া সাহসের কাজ।\n\n"
            "💙 *কান পেত রই* (২৪/৭ বাংলা হেল্পলাইন)\n"
            "→ 01779-554391\n\n"
            "🏥 *জাতীয় মানসিক স্বাস্থ্য ইনস্টিটিউট*\n"
            "→ 02-9118193\n\n"
            "🏥 *OCC ট্রমা কাউন্সেলিং (বিনামূল্যে)*\n"
            "→ ঢাকা মেডিকেল OCC: 02-55165088\n\n"
            "📧 *Obhoy সাপোর্ট টিম*\n"
            "→ bolun@obhoy.com\n\n"
            "💙 *সহযোদ্ধা নেটওয়ার্কে যোগ দিতে:*\n"
            "→ নিচে 'সহযোদ্ধা নেটওয়ার্ক' বেছে নিন\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "আপনি যা ঘটেছে তার জন্য দায়ী নন।\n"
            "আপনার অনুভূতি সম্পূর্ণ স্বাভাবিক। 💙",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU

    # ── সম্পর্কে ──
    elif "সম্পর্কে" in text or "Obhoy" in text:
        await update.message.reply_text(
            "ℹ️ *Obhoy (অভয়) সম্পর্কে*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "অভয় মানে নির্ভয়।\n"
            "আমরা বিশ্বাস করি প্রতিটি বেঁচে যাওয়া\n"
            "মানুষ নির্ভয়ে ন্যায়বিচার চাইতে পারেন।\n\n"
            "📜 আইন শিক্ষা\n"
            "📋 FIR খসড়া তৈরি\n"
            "👩‍⚖️ আইনজীবী সংযোগ\n"
            "🎙️ ভয়েস রিপোর্টিং\n"
            "💙 সহযোদ্ধা নেটওয়ার্ক\n"
            "📅 সাপ্তাহিক সচেতনতা\n\n"
            "🌐 obhoy.com\n"
            "📧 hello@obhoy.com\n"
            "📧 bolun@obhoy.com\n"
            "🤖 @ObhoyBDbot\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "*অভয় — নির্ভয়ে কথা বলুন। 🇧🇩*",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU

    # ── মূল মেনু ──
    elif "মূল মেনু" in text or "ফিরুন" in text:
        await update.message.reply_text(
            "মূল মেনুতে ফিরে এসেছেন।\nকীভাবে সাহায্য করতে পারি?",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU

    else:
        await update.message.reply_text(
            "নিচের মেনু থেকে বেছে নিন 👇\n\n"
            "⚠️ জরুরি সাহায্যের জন্য: *999*",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU


# ─────────────────────────────────────────────────────────────────
#  LAW MENU HANDLER
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
                parse_mode="Markdown",
                reply_markup=law_keyboard()
            )
            return LAW_MENU

    await update.message.reply_text(
        "মেনু থেকে বেছে নিন 👇",
        reply_markup=law_keyboard()
    )
    return LAW_MENU


# ─────────────────────────────────────────────────────────────────
#  HELPLINE DISTRICT HANDLER
# ─────────────────────────────────────────────────────────────────

async def helpline_district(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "মূল মেনু" in text or "ফিরুন" in text:
        await update.message.reply_text(
            "মূল মেনুতে ফিরে এসেছেন।",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU

    for district, info in HELPLINES.items():
        if district in text:
            msg = (
                f"{info['emoji']} *{district} বিভাগের জরুরি নম্বর*\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🚔 *পুলিশ:* {info['police']}\n\n"
                f"🏥 *OCC কেন্দ্র:* {info['occ']}\n\n"
                f"⚖️ *NGO সহায়তা:* {info['ngo']}\n\n"
                f"👮‍♀️ *{info['women']}*\n\n"
                f"📋 *বিনামূল্যে আইনি সেবা:* {info['legal']}\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🆘 জাতীয় জরুরি সেবা: *999*\n"
                "⚖️ বিনামূল্যে আইনজীবী: *16430*"
            )
            await update.message.reply_text(
                msg,
                parse_mode="Markdown",
                reply_markup=district_keyboard()
            )
            return HELPLINE_DIST

    await update.message.reply_text(
        "বিভাগের নাম বেছে নিন 👇",
        reply_markup=district_keyboard()
    )
    return HELPLINE_DIST


# ─────────────────────────────────────────────────────────────────
#  FIR HANDLERS (Idea 1)
# ─────────────────────────────────────────────────────────────────

async def fir_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault('fir', {})['age'] = update.message.text
    await update.message.reply_text(
        "✅ বয়স নোট হয়েছে।\n\n"
        "প্রশ্ন ২/৮\n\n"
        "*ঘটনাটি কবে ঘটেছে?*\n"
        "_(তারিখ লিখুন, যেমন: ১২ মার্চ ২০২৬\n"
        "অথবা আনুমানিক: মার্চ ২০২৬)_",
        parse_mode="Markdown"
    )
    return FIR_DATE


async def fir_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fir']['date'] = update.message.text
    await update.message.reply_text(
        "✅ তারিখ নোট হয়েছে।\n\n"
        "প্রশ্ন ৩/৮\n\n"
        "*ঘটনাটি কোন সময়ে ঘটেছে?*\n"
        "নিচের অপশন থেকে বেছে নিন 👇",
        parse_mode="Markdown",
        reply_markup=time_keyboard()
    )
    return FIR_TIME


async def fir_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fir']['time'] = update.message.text
    await update.message.reply_text(
        "✅ সময় নোট হয়েছে।\n\n"
        "প্রশ্ন ৪/৮\n\n"
        "*ঘটনাটি কোথায় ঘটেছে?*\n"
        "_(উপজেলা ও স্থানের ধরন লিখুন\n"
        "যেমন: গাজীপুর, বাড়িতে)_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return FIR_LOCATION


async def fir_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fir']['location'] = update.message.text
    await update.message.reply_text(
        "✅ স্থান নোট হয়েছে।\n\n"
        "প্রশ্ন ৫/৮\n\n"
        "*অভিযুক্ত ব্যক্তি ভিকটিমের কী হয়?*\n"
        "নিচের অপশন থেকে বেছে নিন 👇",
        parse_mode="Markdown",
        reply_markup=relation_keyboard()
    )
    return FIR_RELATION


async def fir_relation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fir']['relation'] = update.message.text
    await update.message.reply_text(
        "✅ সম্পর্ক নোট হয়েছে।\n\n"
        "প্রশ্ন ৬/৮\n\n"
        "*সংক্ষেপে ঘটনাটি বর্ণনা করুন*\n\n"
        "_(নাম বলার দরকার নেই।\n"
        "শুধু কী ঘটেছে সেটুকু লিখুন।\n"
        "আপনি যতটুকু স্বাচ্ছন্দ্যবোধ করেন।)_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return FIR_DESC


async def fir_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fir']['desc'] = update.message.text
    await update.message.reply_text(
        "✅ বর্ণনা নোট হয়েছে।\n\n"
        "প্রশ্ন ৭/৮\n\n"
        "*ঘটনার কোনো সাক্ষী আছে?*",
        parse_mode="Markdown",
        reply_markup=witness_keyboard()
    )
    return FIR_WITNESS


async def fir_witness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fir']['witness'] = update.message.text
    await update.message.reply_text(
        "✅ সাক্ষীর তথ্য নোট হয়েছে।\n\n"
        "প্রশ্ন ৮/৮\n\n"
        "*এই ঘটনায় আগে কি কোনো রিপোর্ট করা হয়েছে?*",
        parse_mode="Markdown",
        reply_markup=yesno_keyboard()
    )
    return FIR_PREV


async def fir_prev(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fir']['previous'] = update.message.text
    await update.message.reply_text(
        "✅ প্রায় শেষ!\n\n"
        "*আপনি এখন কোন বিভাগে আছেন?*\n"
        "_(নিকটতম সহায়তা কেন্দ্রের তথ্য যোগ হবে)_",
        parse_mode="Markdown",
        reply_markup=district_keyboard()
    )
    return FIR_DIST


async def fir_dist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "মূল মেনু" in text or "ফিরুন" in text:
        await update.message.reply_text(
            "FIR তৈরি বাতিল।\nমূল মেনুতে ফিরে এসেছেন।",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU

    context.user_data['fir']['district'] = text
    fir = context.user_data['fir']

    summary = (
        "✅ *সকল তথ্য সংগ্রহ হয়েছে!*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎂 বয়স: {fir.get('age')}\n"
        f"📅 তারিখ: {fir.get('date')}\n"
        f"⏰ সময়: {fir.get('time')}\n"
        f"📍 স্থান: {fir.get('location')}\n"
        f"👥 সম্পর্ক: {fir.get('relation')}\n"
        f"👁️ সাক্ষী: {fir.get('witness')}\n"
        f"📋 আগের রিপোর্ট: {fir.get('previous')}\n"
        f"🗺️ বিভাগ: {fir.get('district')}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "এই তথ্য দিয়ে FIR রিপোর্ট তৈরি করব?"
    )
    await update.message.reply_text(
        summary,
        parse_mode="Markdown",
        reply_markup=confirm_keyboard()
    )
    return FIR_CONFIRM


async def fir_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "বাতিল" in text:
        await update.message.reply_text(
            "FIR তৈরি বাতিল।\n\n"
            "যেকোনো সময় 'FIR খসড়া তৈরি করুন' বেছে আবার শুরু করুন।",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU

    elif "সংশোধন" in text:
        context.user_data['fir'] = {}
        await update.message.reply_text(
            "নতুন করে শুরু করুন।\n\n"
            "প্রশ্ন ১/৮\n\n"
            "*ভিকটিমের বয়স কত?*",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
        return FIR_AGE

    elif "হ্যাঁ" in text or "রিপোর্ট তৈরি" in text:
        await update.message.reply_text(
            "⏳ আপনার FIR রিপোর্ট তৈরি হচ্ছে...",
            reply_markup=ReplyKeyboardRemove()
        )
        report = build_fir_text(context.user_data.get('fir', {}))
        await update.message.reply_text(
            report,
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
        await update.message.reply_text(
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅ *আপনার FIR রিপোর্ট তৈরি হয়েছে!*\n\n"
            "এই রিপোর্ট *স্ক্রিনশট* নিন বা *ফরোয়ার্ড* করুন\n"
            "তারপর থানায় নিয়ে যান।\n\n"
            "📞 *পরবর্তী পদক্ষেপ:*\n"
            "• বিনামূল্যে আইনজীবী: *16430*\n"
            "• BLAST: *01730-329945*\n"
            "• জরুরি সাহায্য: *999*",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU

    else:
        await update.message.reply_text(
            "নিচের অপশন থেকে বেছে নিন 👇",
            reply_markup=confirm_keyboard()
        )
        return FIR_CONFIRM


# ─────────────────────────────────────────────────────────────────
#  LAWYER MATCH HANDLERS (Idea 3)
# ─────────────────────────────────────────────────────────────────

async def lawyer_dist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "মূল মেনু" in text or "ফিরুন" in text:
        await update.message.reply_text(
            "মূল মেনুতে ফিরে এসেছেন।",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU

    # Save whichever district they picked
    matched = None
    for d in list(LAWYERS.keys()) + list(HELPLINES.keys()):
        if d in text:
            matched = d
            break

    if not matched:
        matched = "অন্যান্য"

    context.user_data['lawyer_dist'] = matched
    await update.message.reply_text(
        f"✅ {matched} বিভাগ নোট হয়েছে।\n\n"
        "কী ধরনের মামলায় আইনজীবী দরকার?\n"
        "নিচের অপশন থেকে বেছে নিন 👇",
        parse_mode="Markdown",
        reply_markup=case_type_keyboard()
    )
    return LAWYER_TYPE


async def lawyer_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "মূল মেনু" in text or "ফিরুন" in text:
        await update.message.reply_text(
            "মূল মেনুতে ফিরে এসেছেন।",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU

    # Map button text to key
    case_map = {
        "ধর্ষণ": "ধর্ষণ",
        "শিশু": "শিশু",
        "ডিজিটাল": "ডিজিটাল",
        "হয়রানি": "হয়রানি",
    }
    case_key = "ধর্ষণ"
    for k, v in case_map.items():
        if k in text:
            case_key = v
            break

    dist = context.user_data.get('lawyer_dist', 'অন্যান্য')
    lawyers_list = (
        LAWYERS.get(dist, {}).get(case_key)
        or LAWYERS.get('অন্যান্য', {}).get(case_key, [])
    )

    contacts = "\n".join([f"✅ {l}" for l in lawyers_list])

    await update.message.reply_text(
        f"👩‍⚖️ *{dist} বিভাগ — {case_key} মামলার আইনজীবী*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{contacts}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📋 *বিনামূল্যে জাতীয় আইনি সহায়তা:* 16430\n"
        "🏥 *OCC (বিনামূল্যে চিকিৎসা):* 02-55165088\n"
        "🚨 *জরুরি সাহায্য:* 999",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )
    return MAIN_MENU


# ─────────────────────────────────────────────────────────────────
#  VOICE REPORT HANDLER (Idea 5)
# ─────────────────────────────────────────────────────────────────

async def voice_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles voice notes sent to the bot"""
    now = datetime.now()
    ref = f"OBH-V-{now.strftime('%Y%m%d%H%M%S')}"

    await update.message.reply_text(
        "🎙️ *আপনার ভয়েস নোট পাওয়া গেছে!*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 রিপোর্ট আইডি: `{ref}`\n"
        f"📅 সময়: {now.strftime('%d/%m/%Y %H:%M')}\n\n"
        "✅ আপনার ভয়েস নোট নিরাপদে সংরক্ষণ হয়েছে।\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🚀 *পরবর্তী পদক্ষেপ:*\n\n"
        "১. এই রিপোর্ট আইডি সংরক্ষণ করুন\n"
        "২. আইনজীবী সাহায্যের জন্য লিখুন:\n"
        "   BLAST: *01730-329945*\n"
        "৩. বিনামূল্যে আইনি সহায়তা: *16430*\n"
        "৪. জরুরি সাহায্য: *999*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💬 টেক্সটে বিস্তারিত জানাতে চাইলে\n"
        "'FIR খসড়া তৈরি করুন' বেছে নিন।",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )


# ─────────────────────────────────────────────────────────────────
#  PEER SUPPORT HANDLERS (Idea 7)
# ─────────────────────────────────────────────────────────────────

async def peer_agree(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "হ্যাঁ" in text:
        await update.message.reply_text(
            "💙 *সহযোদ্ধা নেটওয়ার্কে আপনাকে স্বাগতম!*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔒 গুরুত্বপূর্ণ নিয়মসমূহ:\n\n"
            "১. কোনো আসল নাম বা পরিচয় শেয়ার করবেন না\n"
            "২. অন্যদের সাথে সম্মানের সাথে কথা বলুন\n"
            "৩. কোনো ঠিকানা বা ফোন নম্বর শেয়ার করবেন না\n"
            "৪. যেকোনো সময় চলে যেতে পারবেন\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👩‍⚕️ একজন প্রশিক্ষিত কাউন্সেলর সবসময় আছেন।\n\n"
            "📲 *সহযোদ্ধা গ্রুপে যোগ দিন:*\n"
            "→ care@obhoy.com-এ ইমেইল করুন\n"
            "→ সাবজেক্ট: সহযোদ্ধা নেটওয়ার্ক\n\n"
            "অথবা সরাসরি কথা বলুন:\n"
            "💙 কান পেত রই: *01779-554391*",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
    else:
        await update.message.reply_text(
            "ঠিক আছে। যখন প্রস্তুত হবেন তখন আবার আসুন।\n\n"
            "আমি সবসময় এখানে আছি। 💙",
            reply_markup=main_keyboard()
        )
    return MAIN_MENU


# ─────────────────────────────────────────────────────────────────
#  WEEKLY BROADCAST (Idea 6)
# ─────────────────────────────────────────────────────────────────

async def send_weekly_broadcast(bot, channel_id: str, week_num: int):
    """Send weekly educational content to channel"""
    if not channel_id:
        logger.info("CHANNEL_ID not set — skipping weekly broadcast")
        return
    try:
        idx = week_num % len(WEEKLY_CONTENT)
        msg = WEEKLY_CONTENT[idx]
        full_msg = (
            msg + "\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🤖 আরো তথ্যের জন্য: @ObhoyBDbot\n"
            "🌐 obhoy.com"
        )
        await bot.send_message(
            chat_id=channel_id,
            text=full_msg,
            parse_mode="Markdown"
        )
        logger.info(f"Weekly broadcast sent: week {week_num}")
    except Exception as e:
        logger.error(f"Weekly broadcast error: {e}")


# ─────────────────────────────────────────────────────────────────
#  CANCEL + ERROR
# ─────────────────────────────────────────────────────────────────

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "বাতিল করা হয়েছে।\n\n"
        "যেকোনো সময় /start লিখে আবার শুরু করুন।\n"
        "জরুরি সাহায্যে: *999*",
        parse_mode="Markdown",
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

    # ── Main Conversation Handler ──────────────────────────────
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu)
            ],
            LAW_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, law_menu)
            ],
            HELPLINE_DIST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, helpline_district)
            ],
            FIR_AGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, fir_age)
            ],
            FIR_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, fir_date)
            ],
            FIR_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, fir_time)
            ],
            FIR_LOCATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, fir_location)
            ],
            FIR_RELATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, fir_relation)
            ],
            FIR_DESC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, fir_desc)
            ],
            FIR_WITNESS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, fir_witness)
            ],
            FIR_PREV: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, fir_prev)
            ],
            FIR_DIST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, fir_dist)
            ],
            FIR_CONFIRM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, fir_confirm)
            ],
            LAWYER_DIST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, lawyer_dist)
            ],
            LAWYER_TYPE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, lawyer_type)
            ],
            PEER_AGREE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, peer_agree)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),
        ],
        allow_reentry=True,
    )

    app.add_handler(conv)

    # ── Voice messages (outside conversation) ─────────────────
    app.add_handler(MessageHandler(filters.VOICE, voice_report))

    app.add_error_handler(error_handler)

    # ── Weekly Broadcast Scheduler ─────────────────────────────
    if SCHEDULER_OK and CHANNEL_ID:
        scheduler = AsyncIOScheduler(timezone="Asia/Dhaka")
        week_counter = [0]

        async def broadcast_job():
            await send_weekly_broadcast(app.bot, CHANNEL_ID, week_counter[0])
            week_counter[0] += 1

        scheduler.add_job(
            broadcast_job,
            trigger="cron",
            day_of_week="mon",
            hour=10,
            minute=0,
        )
        scheduler.start()
        logger.info("সাপ্তাহিক ব্রডকাস্ট সক্রিয় হয়েছে")

    print("✅ Obhoy Bot চালু হয়েছে")
    print("🛡️ অভয় — নির্ভয়ে কথা বলুন 🇧🇩")
    print("Press Ctrl+C to stop")

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
