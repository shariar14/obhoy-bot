"""
╔══════════════════════════════════════════════════════════════╗
║                    OBHOY TELEGRAM BOT                        ║
║         অভয় — Sexual Violence Prevention Platform           ║
║                   obhoy.com | @ObhoyBDbot                    ║
╚══════════════════════════════════════════════════════════════╝

SETUP INSTRUCTIONS:
1. Replace YOUR_BOT_TOKEN_HERE with your actual token from @BotFather
2. Install requirements: pip install python-telegram-bot
3. Run: python obhoy_bot.py
4. Or deploy to Railway.app / Render.com for 24/7 hosting

REQUIREMENTS (requirements.txt):
    python-telegram-bot==20.7
"""

import logging
from fir_handler import fir_conversation
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# ─────────────────────────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────────────────────────

import os
TOKEN = os.environ.get("TOKEN")  # ← Replace with your BotFather token

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
(
    MAIN_MENU,
    LAW_MENU,
    LAW_DETAIL,
    REPORT_MENU,
    REPORT_DISTRICT,
    REPORT_DETAIL,
    HELPLINE_MENU,
) = range(7)


# ─────────────────────────────────────────────────────────────────
#  KNOWLEDGE BASE — LAWS
# ─────────────────────────────────────────────────────────────────

LAWS = {

    "law_1": """
📜 *নারী ও শিশু নির্যাতন দমন আইন ২০০০*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ *ধারা ৯(১) — সাধারণ ধর্ষণ*
→ শাস্তি: যাবজ্জীবন কারাদণ্ড ও অর্থদণ্ড

✅ *ধারা ৯(২) — ধর্ষণের ফলে মৃত্যু*
→ শাস্তি: মৃত্যুদণ্ড বা যাবজ্জীবন কারাদণ্ড

✅ *ধারা ৯(৩) — গণধর্ষণ*
→ শাস্তি: মৃত্যুদণ্ড বা যাবজ্জীবন কারাদণ্ড

✅ *ধারা ৯(৪) — শিশু ধর্ষণ (১৮ বছরের নিচে)*
→ শাস্তি: মৃত্যুদণ্ড বা যাবজ্জীবন কারাদণ্ড

✅ *তদন্ত সময়সীমা:* ৩০ কার্যদিবস
✅ *বিচার সময়সীমা:* ১৮০ কার্যদিবস

⚠️ এই আইনে অভিযোগ দায়ের করা সম্পূর্ণ বিনামূল্যে।
""",

    "law_2": """
📜 *দণ্ডবিধি ধারা ৩৭৫ ও ৩৭৬*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ *ধারা ৩৭৫ — ধর্ষণের সংজ্ঞা*
→ সম্মতি ছাড়া যেকোনো যৌন সম্পর্ক ধর্ষণ হিসেবে গণ্য
→ ১৪ বছরের নিচে সম্মতি আইনত বৈধ নয়

✅ *ধারা ৩৭৬ — ধর্ষণের শাস্তি*
→ ন্যূনতম: ৭ বছর কারাদণ্ড
→ সর্বোচ্চ: যাবজ্জীবন কারাদণ্ড ও অর্থদণ্ড

✅ *বিশেষ ক্ষেত্র (ধারা ৩৭৬A-D)*
→ অভিভাবক কর্তৃক ধর্ষণ: যাবজ্জীবন
→ পুলিশ বা সরকারি কর্মকর্তা কর্তৃক: যাবজ্জীবন
→ হাসপাতালে ধর্ষণ: যাবজ্জীবন

⚠️ বিবাহিত নারীর ক্ষেত্রেও এই আইন সমানভাবে প্রযোজ্য।
""",

    "law_3": """
📜 *শিশু ধর্ষণ আইন (১৮ বছরের নিচে)*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ *শিশু আইন ২০১৩*
→ শিশু আদালতে দ্রুত বিচার বাধ্যতামূলক
→ তদন্ত সময়সীমা: ১৫ কার্যদিবস

✅ *নারী ও শিশু নির্যাতন দমন আইন ২০০০ ধারা ৯(৪)*
→ শাস্তি: মৃত্যুদণ্ড বা যাবজ্জীবন কারাদণ্ড

✅ *পরিচয় সুরক্ষা*
→ ভিকটিম শিশুর নাম/পরিচয় প্রকাশ সম্পূর্ণ নিষিদ্ধ
→ পরিচয় প্রকাশে শাস্তি: ২ বছর কারাদণ্ড ও অর্থদণ্ড

✅ *বিনামূল্যে সুবিধা*
→ ওয়ান স্টপ ক্রাইসিস সেন্টারে বিনামূল্যে চিকিৎসা
→ সরকারি আইনজীবী সম্পূর্ণ বিনামূল্যে

⚠️ শিশু ভিকটিমের পক্ষে অভিভাবক মামলা করতে পারবেন।
""",

    "law_4": """
📜 *গণধর্ষণ আইন*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ *নারী ও শিশু নির্যাতন দমন আইন ধারা ৯(৩)*
→ একাধিক ব্যক্তি দ্বারা ধর্ষণ = গণধর্ষণ
→ শাস্তি: সকলের মৃত্যুদণ্ড বা যাবজ্জীবন

✅ *সহযোগিতাকারীর শাস্তি*
→ সরাসরি অংশগ্রহণ না করলেও
→ পরিকল্পনায় থাকলে একই শাস্তি

✅ *২০২০ সালের সংশোধনী*
→ সর্বোচ্চ শাস্তি: মৃত্যুদণ্ড (ফাঁসি)
→ কোনো জামিন নেই তদন্ত চলাকালীন

✅ *দ্রুত বিচার*
→ নারী ও শিশু নির্যাতন দমন ট্রাইব্যুনালে বিচার
→ সময়সীমা: ১৮০ কার্যদিবসের মধ্যে রায়

⚠️ গণধর্ষণে ভিডিও ধারণ বা প্রচার আলাদা অপরাধ — ডিজিটাল নিরাপত্তা আইনে অতিরিক্ত শাস্তি।
""",

    "law_5": """
📜 *ধর্ষণের চেষ্টার শাস্তি*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ *নারী ও শিশু নির্যাতন দমন আইন ধারা ৯(৫)*
→ ধর্ষণের চেষ্টা করলেও শাস্তি প্রযোজ্য
→ শাস্তি: ১০ বছর পর্যন্ত কারাদণ্ড ও অর্থদণ্ড

✅ *যৌন হয়রানি (ধারা ১০)*
→ যৌন উদ্দেশ্যে আক্রমণ বা শ্লীলতাহানি
→ শাস্তি: ১০ বছর পর্যন্ত কারাদণ্ড

✅ *ইভ টিজিং*
→ সর্বোচ্চ ৭ বছর কারাদণ্ড
→ থানায় সরাসরি মামলা করা যায়

⚠️ চেষ্টার প্রমাণ হিসেবে সাক্ষী, ভিডিও, বা মেডিকেল রিপোর্ট ব্যবহার করা যায়।
""",

    "law_6": """
📜 *ডিজিটাল অপরাধ ও সাইবার আইন*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ *ডিজিটাল নিরাপত্তা আইন ২০১৮ ধারা ২৬*
→ সম্মতি ছাড়া ঘনিষ্ঠ ছবি/ভিডিও প্রকাশ
→ শাস্তি: ৫ বছর কারাদণ্ড ও ৫ লাখ টাকা জরিমানা

✅ *ধারা ২৯ — অনলাইন যৌন হয়রানি*
→ মানহানিকর যৌন বিষয়বস্তু প্রকাশ
→ শাস্তি: ৩ বছর কারাদণ্ড ও ৩ লাখ টাকা জরিমানা

✅ *পর্নোগ্রাফি নিয়ন্ত্রণ আইন ২০১২*
→ অনুমতি ছাড়া ভিডিও তৈরি বা প্রচার
→ শাস্তি: ৭ বছর কারাদণ্ড ও ২ লাখ টাকা জরিমানা

✅ *রিপোর্ট করুন:*
→ BGD e-GOV CIRT: cirt.gov.bd
→ পুলিশ সাইবার সাপোর্ট: 01320-000888

⚠️ স্ক্রিনশট ও চ্যাট হিস্ট্রি ডিজিটাল প্রমাণ হিসেবে গ্রহণযোগ্য।
""",

    "law_7": """
📜 *ভিকটিমের আইনি অধিকার সমূহ*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ *বিনামূল্যে আইনি সহায়তার অধিকার*
→ জাতীয় আইনগত সহায়তা সংস্থা (NLASO)
→ হটলাইন: 16430

✅ *মহিলা পুলিশের কাছে জবানবন্দির অধিকার*
→ কোনো পুরুষ পুলিশের সামনে বক্তব্য দিতে বাধ্য নন

✅ *পরিচয় গোপন রাখার অধিকার*
→ মিডিয়া বা আদালতে নাম প্রকাশ নিষিদ্ধ

✅ *বিনামূল্যে চিকিৎসার অধিকার*
→ ওয়ান স্টপ ক্রাইসিস সেন্টার (OCC)
→ ফরেনসিক পরীক্ষা সম্পূর্ণ বিনামূল্যে

✅ *সাক্ষী সুরক্ষার অধিকার*
→ আদালতে সাক্ষী দেওয়ার সময় নিরাপত্তা

✅ *ক্ষতিপূরণ দাবির অধিকার*
→ আদালত ক্ষতিপূরণ প্রদানের আদেশ দিতে পারেন

✅ *আপিলের অধিকার*
→ রায়ে অসন্তুষ্ট হলে উচ্চ আদালতে আপিল করা যাবে

⚠️ এই সকল অধিকার আপনার। কেউ এই অধিকার থেকে বঞ্চিত করতে পারবে না।
""",

    "law_8": """
📜 *FIR (প্রাথমিক তথ্য বিবরণী) কীভাবে করবেন*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ *ধাপ ১: নিকটস্থ থানায় যান*
→ সাথে নিন: জাতীয় পরিচয়পত্র (না থাকলেও চলবে)
→ মহিলা পুলিশ অফিসার চাইতে পারেন

✅ *ধাপ ২: লিখিত অভিযোগ দিন*
→ ঘটনার তারিখ, সময়, স্থান উল্লেখ করুন
→ অভিযুক্তের নাম বা বর্ণনা দিন

✅ *ধাপ ৩: মেডিকেল পরীক্ষা করান*
→ FIR দায়েরের পর পুলিশ মেডিকেল পাঠাবে
→ বা সরাসরি OCC-তে যেতে পারেন

✅ *ধাপ ৪: কেস নম্বর সংগ্রহ করুন*
→ FIR গ্রহণের পর থানা আপনাকে কেস নম্বর দেবে
→ এই নম্বর দিয়ে পরে মামলার অগ্রগতি জানা যাবে

⚠️ পুলিশ FIR নিতে অস্বীকার করলে:
→ সরাসরি আদালতে নালিশী মামলা করুন
→ বা BLAST/ASK-এর সাহায্য নিন (নম্বর নিচে দেওয়া আছে)
""",
}


# ─────────────────────────────────────────────────────────────────
#  KNOWLEDGE BASE — HELPLINES (ALL 8 DIVISIONS + NATIONAL)
# ─────────────────────────────────────────────────────────────────

HELPLINES = {
    "ঢাকা": {
        "emoji": "🏙️",
        "police": "ঢাকা মেট্রোপলিটন পুলিশ: 01320-000999",
        "occ": "OCC ঢাকা মেডিকেল কলেজ: 02-55165088",
        "ngo": "ASK: 01730-029945 | BLAST: 01730-329945",
        "women_police": "মহিলা সহায়তা কেন্দ্র: 01320-000112",
        "legal_aid": "জেলা লিগ্যাল এইড: 02-9514424",
    },
    "চট্টগ্রাম": {
        "emoji": "⚓",
        "police": "চট্টগ্রাম মেট্রোপলিটন পুলিশ: 031-639944",
        "occ": "OCC চট্টগ্রাম মেডিকেল: 031-630903",
        "ngo": "YPSA: 031-2853985 | BLAST চট্টগ্রাম: 031-710441",
        "women_police": "মহিলা সহায়তা: 01320-100222",
        "legal_aid": "জেলা লিগ্যাল এইড: 031-711069",
    },
    "রাজশাহী": {
        "emoji": "🍎",
        "police": "রাজশাহী মেট্রোপলিটন পুলিশ: 0721-775555",
        "occ": "OCC রাজশাহী মেডিকেল: 0721-772150",
        "ngo": "RDRS: 0721-775588 | Nagorik Uddyog: 0721-810035",
        "women_police": "মহিলা সহায়তা: 01320-200333",
        "legal_aid": "জেলা লিগ্যাল এইড: 0721-774878",
    },
    "খুলনা": {
        "emoji": "🌿",
        "police": "খুলনা মেট্রোপলিটন পুলিশ: 041-761999",
        "occ": "OCC খুলনা মেডিকেল: 041-762595",
        "ngo": "Rupantar: 041-731522 | BLAST খুলনা: 041-810552",
        "women_police": "মহিলা সহায়তা: 01320-400555",
        "legal_aid": "জেলা লিগ্যাল এইড: 041-761234",
    },
    "সিলেট": {
        "emoji": "🍵",
        "police": "সিলেট মেট্রোপলিটন পুলিশ: 0821-713666",
        "occ": "OCC MAG ওসমানী মেডিকেল: 0821-713151",
        "ngo": "BNWLA সিলেট: 0821-716677",
        "women_police": "মহিলা সহায়তা: 01320-300444",
        "legal_aid": "জেলা লিগ্যাল এইড: 0821-714523",
    },
    "বরিশাল": {
        "emoji": "🌊",
        "police": "বরিশাল মেট্রোপলিটন পুলিশ: 0431-66666",
        "occ": "OCC শের-ই-বাংলা মেডিকেল: 0431-2176175",
        "ngo": "BLAST বরিশাল: 0431-64411",
        "women_police": "মহিলা সহায়তা: 01320-500666",
        "legal_aid": "জেলা লিগ্যাল এইড: 0431-65432",
    },
    "ময়মনসিংহ": {
        "emoji": "🌾",
        "police": "ময়মনসিংহ মেট্রোপলিটন পুলিশ: 091-65100",
        "occ": "OCC ময়মনসিংহ মেডিকেল: 091-67553",
        "ngo": "BRAC ময়মনসিংহ: 091-66700",
        "women_police": "মহিলা সহায়তা: 01320-600777",
        "legal_aid": "জেলা লিগ্যাল এইড: 091-64321",
    },
    "রংপুর": {
        "emoji": "🌻",
        "police": "রংপুর মেট্রোপলিটন পুলিশ: 0521-66666",
        "occ": "OCC রংপুর মেডিকেল: 0521-63750",
        "ngo": "RDRS রংপুর: 0521-64488",
        "women_police": "মহিলা সহায়তা: 01320-700888",
        "legal_aid": "জেলা লিগ্যাল এইড: 0521-65123",
    },
}

NATIONAL_HELPLINES = """
📞 *জাতীয় জরুরি হেল্পলাইন নম্বর*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚨 *জরুরি সেবা (২৪/৭)*
→ জাতীয় জরুরি সেবা: *999*
→ জাতীয় নারী হেল্পলাইন: *10921*
→ শিশু হেল্পলাইন: *1098*

⚖️ *আইনি সহায়তা (বিনামূল্যে)*
→ জাতীয় আইনগত সহায়তা: *16430*
→ BLAST (আইনি সহায়তা): 01730-329945
→ ASK (আইন ও সালিশ কেন্দ্র): 01730-029945

🏥 *চিকিৎসা ও মানসিক সহায়তা*
→ কান পেতরই (মানসিক স্বাস্থ্য): 01779-554391
→ ঢাকা OCC (২৪/৭): 02-55165088
→ জাতীয় মানসিক স্বাস্থ্য ইনস্টিটিউট: 02-9118193

🌐 *অনলাইন রিপোর্ট*
→ পুলিশ সাইবার সাপোর্ট: 01320-000888
→ BGD e-GOV CIRT: cirt.gov.bd

⚠️ আপনি যদি এখনই বিপদে থাকেন — *999* ডায়াল করুন।
"""


# ─────────────────────────────────────────────────────────────────
#  KEYBOARDS
# ─────────────────────────────────────────────────────────────────

def main_keyboard():
    return ReplyKeyboardMarkup([
        ["📜 আইন ও শাস্তি জানুন"],
        ["🆘 ঘটনা রিপোর্ট করুন"],
        ["📞 জরুরি হেল্পলাইন"],
        ["💬 মানসিক সহায়তা"],
        ["ℹ️ Obhoy সম্পর্কে"],
    ], resize_keyboard=True)


def law_keyboard():
    return ReplyKeyboardMarkup([
        ["১. নারী ও শিশু নির্যাতন আইন ২০০০"],
        ["২. দণ্ডবিধি ধারা ৩৭৫-৩৭৬"],
        ["৩. শিশু ধর্ষণ আইন"],
        ["৪. গণধর্ষণ আইন"],
        ["৫. ধর্ষণের চেষ্টার শাস্তি"],
        ["৬. ডিজিটাল অপরাধ আইন"],
        ["৭. ভিকটিমের আইনি অধিকার"],
        ["৮. FIR কীভাবে করবেন"],
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


def report_keyboard():
    return ReplyKeyboardMarkup([
        ["📍 নিকটতম থানা ও সংস্থার নম্বর পান"],
        ["📋 FIR করার ধাপসমূহ জানুন"],
        ["⚖️ বিনামূল্যে আইনজীবী পান"],
        ["🏥 নিকটতম OCC খুঁজুন"],
        ["🔙 মূল মেনুতে ফিরুন"],
    ], resize_keyboard=True)


# ─────────────────────────────────────────────────────────────────
#  HANDLERS
# ─────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point — /start command"""
    await update.message.reply_text(
        "🛡️ *Obhoy-তে আপনাকে স্বাগতম*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "আমি *অভয়* — বাংলাদেশের প্রথম AI-চালিত\n"
        "যৌন সহিংসতা প্রতিরোধ ও সহায়তা প্ল্যাটফর্ম।\n\n"
        "আমি আপনাকে সাহায্য করতে পারি:\n"
        "📜 ধর্ষণ সংক্রান্ত আইন ও শাস্তি জানতে\n"
        "🆘 ঘটনা রিপোর্ট করার প্রক্রিয়া জানতে\n"
        "📞 নিকটতম সহায়তা কেন্দ্রের নম্বর পেতে\n"
        "💬 মানসিক সহায়তা পেতে\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚠️ *জরুরি প্রয়োজনে এখনই কল করুন: 999*\n\n"
        "নিচের মেনু থেকে বেছে নিন 👇",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )
    return MAIN_MENU


async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu selections"""
    text = update.message.text

    # ── LAW SECTION ──
    if "আইন" in text:
        await update.message.reply_text(
            "📜 *আইন ও শাস্তি*\n\n"
            "কোন বিষয়ে জানতে চান? নিচ থেকে বেছে নিন:",
            parse_mode="Markdown",
            reply_markup=law_keyboard()
        )
        return LAW_MENU

    # ── REPORT SECTION ──
    elif "রিপোর্ট" in text:
        await update.message.reply_text(
            "🆘 *ঘটনা রিপোর্ট করুন*\n\n"
            "আপনি কীভাবে সাহায্য চান?",
            parse_mode="Markdown",
            reply_markup=report_keyboard()
        )
        return REPORT_MENU

    # ── HELPLINE SECTION ──
    elif "হেল্পলাইন" in text:
        await update.message.reply_text(
            NATIONAL_HELPLINES,
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU

    # ── MENTAL SUPPORT ──
    elif "মানসিক" in text:
        await update.message.reply_text(
            "💬 *মানসিক সহায়তা*\n\n"
            "আপনি একা নন। সাহায্য নেওয়া শক্তির লক্ষণ।\n\n"
            "✅ *কান পেতরই* (২৪/৭ বাংলা হেল্পলাইন)\n"
            "→ 01779-554391\n\n"
            "✅ *জাতীয় মানসিক স্বাস্থ্য ইনস্টিটিউট (NIMH)*\n"
            "→ 02-9118193\n\n"
            "✅ *OCC ট্রমা কাউন্সেলিং (বিনামূল্যে)*\n"
            "→ ঢাকা মেডিকেল OCC: 02-55165088\n\n"
            "✅ *Obhoy সাপোর্ট টিম*\n"
            "→ care@obhoy.com\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💙 আপনার অনুভূতি সম্পূর্ণ স্বাভাবিক।\n"
            "আপনি যা ঘটেছে তার জন্য দায়ী নন।",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU

    # ── ABOUT SECTION ──
    elif "Obhoy সম্পর্কে" in text or "সম্পর্কে" in text:
        await update.message.reply_text(
            "ℹ️ *Obhoy (অভয়) সম্পর্কে*\n\n"
            "অভয় মানে নির্ভয়। আমরা বিশ্বাস করি\n"
            "প্রতিটি বেঁচে যাওয়া মানুষ নির্ভয়ে\n"
            "ন্যায়বিচার চাইতে পারেন।\n\n"
            "🔴 অপরাধ পূর্বাভাস\n"
            "🗣️ নিরাপদ익명 রিপোর্টিং\n"
            "⚖️ মামলা ট্র্যাকিং\n"
            "🤝 কমিউনিটি সুরক্ষা\n"
            "💙 বেঁচে যাওয়াদের সহায়তা\n\n"
            "🌐 obhoy.com\n"
            "📧 hello@obhoy.com\n"
            "📘 facebook.com/obhoybd\n"
            "📸 instagram.com/obhoybd",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU

    # ── BACK ──
    elif "মূল মেনু" in text:
        await update.message.reply_text(
            "মূল মেনুতে ফিরে এসেছেন। কীভাবে সাহায্য করতে পারি?",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU

    else:
        await update.message.reply_text(
            "অনুগ্রহ করে নিচের মেনু থেকে বেছে নিন।\n"
            "জরুরি সাহায্যের জন্য: *999* ডায়াল করুন।",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU


async def handle_law_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle law menu selections"""
    text = update.message.text

    law_map = {
        "১.": "law_1",
        "২.": "law_2",
        "৩.": "law_3",
        "৪.": "law_4",
        "৫.": "law_5",
        "৬.": "law_6",
        "৭.": "law_7",
        "৮.": "law_8",
    }

    matched_law = None
    for key, law_key in law_map.items():
        if key in text:
            matched_law = law_key
            break

    if matched_law:
        await update.message.reply_text(
            LAWS[matched_law],
            parse_mode="Markdown",
            reply_markup=law_keyboard()
        )
        return LAW_MENU

    elif "মূল মেনু" in text:
        await update.message.reply_text(
            "মূল মেনুতে ফিরে এসেছেন।",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU

    else:
        await update.message.reply_text(
            "অনুগ্রহ করে মেনু থেকে বেছে নিন।",
            reply_markup=law_keyboard()
        )
        return LAW_MENU


async def handle_report_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle report menu selections"""
    text = update.message.text

    if "থানা" in text or "নম্বর পান" in text:
        await update.message.reply_text(
            "📍 আপনি কোন বিভাগে আছেন?\n"
            "আপনার বিভাগের নাম বেছে নিন:",
            reply_markup=district_keyboard()
        )
        return REPORT_DISTRICT

    elif "FIR" in text or "ধাপ" in text:
        await update.message.reply_text(
            LAWS["law_8"],
            parse_mode="Markdown",
            reply_markup=report_keyboard()
        )
        return REPORT_MENU

    elif "আইনজীবী" in text:
        await update.message.reply_text(
            "⚖️ *বিনামূল্যে আইনজীবী পাওয়ার উপায়*\n\n"
            "✅ *জাতীয় আইনগত সহায়তা সংস্থা*\n"
            "→ হটলাইন: 16430 (বিনামূল্যে)\n\n"
            "✅ *BLAST (বাংলাদেশ লিগ্যাল এইড)*\n"
            "→ ফোন: 01730-329945\n"
            "→ ইমেইল: mail@blast.org.bd\n\n"
            "✅ *ASK (আইন ও সালিশ কেন্দ্র)*\n"
            "→ ফোন: 01730-029945\n"
            "→ ইমেইল: ask@citechco.net\n\n"
            "✅ *জেলা লিগ্যাল এইড অফিস*\n"
            "→ আপনার জেলার কোর্ট বিল্ডিংয়ে\n"
            "→ সম্পূর্ণ বিনামূল্যে সেবা প্রদান করে",
            parse_mode="Markdown",
            reply_markup=report_keyboard()
        )
        return REPORT_MENU

    elif "OCC" in text or "চিকিৎসা" in text:
        await update.message.reply_text(
            "🏥 *ওয়ান স্টপ ক্রাইসিস সেন্টার (OCC)*\n\n"
            "OCC-তে বিনামূল্যে পাবেন:\n"
            "✅ ফরেনসিক মেডিকেল পরীক্ষা\n"
            "✅ ট্রমা কাউন্সেলিং\n"
            "✅ আইনি সহায়তা\n"
            "✅ পুলিশ সহায়তা\n"
            "✅ সামাজিক সেবা\n\n"
            "📍 *প্রধান OCC কেন্দ্রসমূহ:*\n\n"
            "→ ঢাকা মেডিকেল: 02-55165088\n"
            "→ চট্টগ্রাম মেডিকেল: 031-630903\n"
            "→ রাজশাহী মেডিকেল: 0721-772150\n"
            "→ সিলেট ওসমানী: 0821-713151\n"
            "→ খুলনা মেডিকেল: 041-762595\n\n"
            "⚠️ OCC ২৪ ঘণ্টা খোলা থাকে।",
            parse_mode="Markdown",
            reply_markup=report_keyboard()
        )
        return REPORT_MENU

    elif "মূল মেনু" in text:
        await update.message.reply_text(
            "মূল মেনুতে ফিরে এসেছেন।",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU

    else:
        await update.message.reply_text(
            "অনুগ্রহ করে মেনু থেকে বেছে নিন।",
            reply_markup=report_keyboard()
        )
        return REPORT_MENU


async def handle_district(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle district selection and show local helplines"""
    text = update.message.text

    if "মূল মেনু" in text:
        await update.message.reply_text(
            "মূল মেনুতে ফিরে এসেছেন।",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU

    # Find matching district
    matched = None
    for district in HELPLINES.keys():
        if district in text:
            matched = district
            break

    if matched:
        info = HELPLINES[matched]
        msg = (
            f"{info['emoji']} *{matched} বিভাগের জরুরি নম্বর*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🚔 *পুলিশ:* {info['police']}\n\n"
            f"🏥 *OCC কেন্দ্র:* {info['occ']}\n\n"
            f"⚖️ *NGO সহায়তা:* {info['ngo']}\n\n"
            f"👮‍♀️ *মহিলা পুলিশ:* {info['women_police']}\n\n"
            f"📋 *বিনামূল্যে আইনি সেবা:* {info['legal_aid']}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆘 জাতীয় জরুরি সেবা: *999*\n"
            f"📞 নারী হেল্পলাইন: *10921*"
        )
        await update.message.reply_text(
            msg,
            parse_mode="Markdown",
            reply_markup=district_keyboard()
        )
    else:
        await update.message.reply_text(
            "অনুগ্রহ করে মেনু থেকে আপনার বিভাগ বেছে নিন।\n"
            "এছাড়া জাতীয় জরুরি নম্বর: *999*",
            parse_mode="Markdown",
            reply_markup=district_keyboard()
        )

    return REPORT_DISTRICT


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel and return to main menu"""
    await update.message.reply_text(
        "মূল মেনুতে ফিরে এসেছেন।\n"
        "যেকোনো সাহায্যে /start টাইপ করুন।",
        reply_markup=main_keyboard()
    )
    return ConversationHandler.END


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors"""
    logger.error(f"Error: {context.error}")


# ─────────────────────────────────────────────────────────────────
#  MAIN — RUN THE BOT
# ─────────────────────────────────────────────────────────────────

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Conversation handler with all states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu)
            ],
            LAW_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_law_menu)
            ],
            REPORT_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_report_menu)
            ],
            REPORT_DISTRICT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_district)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),
        ],
    )

    app.add_handler(conv_handler)
    app.add_handler(fir_conversation)
    app.add_error_handler(error_handler)

    print("✅ Obhoy Bot is running...")
    print("🛡️ অভয় বট চালু হয়েছে")
    print("Press Ctrl+C to stop")

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
