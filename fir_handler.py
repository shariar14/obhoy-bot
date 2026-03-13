"""
OBHOY — FIR Conversation Handler
Asks 6 questions, collects answers, generates PDF
"""

import os
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from fir_generator import generate_fir_pdf

logger = logging.getLogger(__name__)

# Conversation states
(
    FIR_AGE,
    FIR_DATE,
    FIR_TIME,
    FIR_LOCATION,
    FIR_RELATION,
    FIR_DESCRIPTION,
    FIR_WITNESS,
    FIR_PREVIOUS,
    FIR_DISTRICT,
    FIR_CONFIRM,
) = range(10, 20)


# ── TIME OPTIONS ─────────────────────────────────────
def time_keyboard():
    return ReplyKeyboardMarkup([
        ["🌅 ভোর (৪টা-৬টা)", "🌞 সকাল (৬টা-১২টা)"],
        ["🌤️ দুপুর (১২টা-৩টা)", "🌇 বিকেল (৩টা-৬টা)"],
        ["🌆 সন্ধ্যা (৬টা-৯টা)", "🌙 রাত (৯টা-১২টা)"],
        ["🌑 গভীর রাত (১২টা-৪টা)", "⏰ সঠিক সময় জানি না"],
    ], resize_keyboard=True)


# ── RELATION OPTIONS ──────────────────────────────────
def relation_keyboard():
    return ReplyKeyboardMarkup([
        ["👨‍👩‍👦 পরিবারের সদস্য", "🏘️ প্রতিবেশী"],
        ["🏫 শিক্ষক বা মাদ্রাসা শিক্ষক", "👔 কর্মক্ষেত্রের পরিচিত"],
        ["❓ অপরিচিত ব্যক্তি", "👥 বন্ধু বা পরিচিত"],
        ["🚗 পরিবহন চালক", "অন্য কেউ"],
    ], resize_keyboard=True)


# ── WITNESS OPTIONS ───────────────────────────────────
def witness_keyboard():
    return ReplyKeyboardMarkup([
        ["✅ হ্যাঁ, সাক্ষী আছে", "❌ না, কোনো সাক্ষী নেই"],
        ["🤔 নিশ্চিত নই"],
    ], resize_keyboard=True)


# ── PREVIOUS REPORT OPTIONS ───────────────────────────
def previous_keyboard():
    return ReplyKeyboardMarkup([
        ["✅ হ্যাঁ, আগে রিপোর্ট করেছি", "❌ না, এটাই প্রথম"],
    ], resize_keyboard=True)


# ── DISTRICT OPTIONS ──────────────────────────────────
def district_keyboard():
    return ReplyKeyboardMarkup([
        ["ঢাকা", "চট্টগ্রাম"],
        ["রাজশাহী", "খুলনা"],
        ["সিলেট", "বরিশাল"],
        ["ময়মনসিংহ", "রংপুর"],
        ["অন্য জেলা — লিখুন"],
    ], resize_keyboard=True)


# ── CONFIRM OPTIONS ───────────────────────────────────
def confirm_keyboard():
    return ReplyKeyboardMarkup([
        ["✅ হ্যাঁ, FIR তৈরি করুন"],
        ["✏️ না, সংশোধন করতে চাই"],
        ["❌ বাতিল করুন"],
    ], resize_keyboard=True)


# ─────────────────────────────────────────────────────
#  STEP 1: START FIR
# ─────────────────────────────────────────────────────
async def fir_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fir_answers'] = {}
    await update.message.reply_text(
        "📋 *FIR খসড়া তৈরি করুন*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "আমি আপনাকে ৬টি প্রশ্ন জিজ্ঞেস করব।\n"
        "আপনার উত্তর দিয়ে আমি একটি সম্পূর্ণ\n"
        "আইনি FIR খসড়া তৈরি করব।\n\n"
        "⚠️ *আপনার পরিচয় সম্পূর্ণ গোপন থাকবে*\n"
        "⚠️ *যেকোনো সময় /cancel লিখে বের হতে পারবেন*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "প্রশ্ন ১/৮ 👇\n\n"
        "*ভিকটিমের বয়স কত?*\n"
        "_(শুধু সংখ্যা লিখুন, যেমন: 16)_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return FIR_AGE


# ─────────────────────────────────────────────────────
#  STEP 2: AGE → DATE
# ─────────────────────────────────────────────────────
async def fir_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fir_answers']['victim_age'] = update.message.text
    await update.message.reply_text(
        "✅ বয়স নোট করা হয়েছে।\n\n"
        "প্রশ্ন ২/৮ 👇\n\n"
        "*ঘটনাটি কবে ঘটেছে?*\n"
        "_(তারিখ লিখুন, যেমন: ১২ মার্চ ২০২৬\n"
        "অথবা আনুমানিক: মার্চ ২০২৬)_",
        parse_mode="Markdown"
    )
    return FIR_DATE


# ─────────────────────────────────────────────────────
#  STEP 3: DATE → TIME
# ─────────────────────────────────────────────────────
async def fir_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fir_answers']['incident_date'] = update.message.text
    await update.message.reply_text(
        "✅ তারিখ নোট করা হয়েছে।\n\n"
        "প্রশ্ন ৩/৮ 👇\n\n"
        "*ঘটনাটি কোন সময়ে ঘটেছে?*\n"
        "নিচের অপশন থেকে বেছে নিন 👇",
        parse_mode="Markdown",
        reply_markup=time_keyboard()
    )
    return FIR_TIME


# ─────────────────────────────────────────────────────
#  STEP 4: TIME → LOCATION
# ─────────────────────────────────────────────────────
async def fir_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fir_answers']['incident_time'] = update.message.text
    await update.message.reply_text(
        "✅ সময় নোট করা হয়েছে।\n\n"
        "প্রশ্ন ৪/৮ 👇\n\n"
        "*ঘটনাটি কোথায় ঘটেছে?*\n"
        "_(উপজেলা এবং স্থানের ধরন লিখুন\n"
        "যেমন: গাজীপুর, বাড়িতে\n"
        "অথবা: মিরপুর, স্কুলের কাছে)_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return FIR_LOCATION


# ─────────────────────────────────────────────────────
#  STEP 5: LOCATION → RELATION
# ─────────────────────────────────────────────────────
async def fir_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fir_answers']['incident_location'] = update.message.text
    await update.message.reply_text(
        "✅ স্থান নোট করা হয়েছে।\n\n"
        "প্রশ্ন ৫/৮ 👇\n\n"
        "*অভিযুক্ত ব্যক্তি ভিকটিমের কী হয়?*\n"
        "নিচের অপশন থেকে বেছে নিন 👇",
        parse_mode="Markdown",
        reply_markup=relation_keyboard()
    )
    return FIR_RELATION


# ─────────────────────────────────────────────────────
#  STEP 6: RELATION → DESCRIPTION
# ─────────────────────────────────────────────────────
async def fir_relation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fir_answers']['perpetrator_relation'] = update.message.text
    await update.message.reply_text(
        "✅ সম্পর্ক নোট করা হয়েছে।\n\n"
        "প্রশ্ন ৬/৮ 👇\n\n"
        "*সংক্ষেপে ঘটনাটি বর্ণনা করুন*\n\n"
        "_(নাম বলার দরকার নেই।\n"
        "শুধু কী ঘটেছে সেটুকু লিখুন।\n"
        "আপনি যতটুকু স্বাচ্ছন্দ্যবোধ করেন।)_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return FIR_DESCRIPTION


# ─────────────────────────────────────────────────────
#  STEP 7: DESCRIPTION → WITNESS
# ─────────────────────────────────────────────────────
async def fir_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fir_answers']['description'] = update.message.text
    await update.message.reply_text(
        "✅ বিবরণ নোট করা হয়েছে।\n\n"
        "প্রশ্ন ৭/৮ 👇\n\n"
        "*ঘটনার কোনো সাক্ষী আছে?*",
        parse_mode="Markdown",
        reply_markup=witness_keyboard()
    )
    return FIR_WITNESS


# ─────────────────────────────────────────────────────
#  STEP 8: WITNESS → PREVIOUS REPORT
# ─────────────────────────────────────────────────────
async def fir_witness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fir_answers']['witness'] = update.message.text
    await update.message.reply_text(
        "✅ সাক্ষী তথ্য নোট করা হয়েছে।\n\n"
        "প্রশ্ন ৮/৮ 👇\n\n"
        "*এই ঘটনায় আগে কি কোনো রিপোর্ট করা হয়েছে?*",
        parse_mode="Markdown",
        reply_markup=previous_keyboard()
    )
    return FIR_PREVIOUS


# ─────────────────────────────────────────────────────
#  STEP 9: PREVIOUS → DISTRICT
# ─────────────────────────────────────────────────────
async def fir_previous(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fir_answers']['previous_report'] = update.message.text
    await update.message.reply_text(
        "✅ প্রায় শেষ!\n\n"
        "*আপনি এখন কোন বিভাগে আছেন?*\n"
        "_(আমরা নিকটতম সহায়তা কেন্দ্রের তথ্য যোগ করব)_",
        parse_mode="Markdown",
        reply_markup=district_keyboard()
    )
    return FIR_DISTRICT


# ─────────────────────────────────────────────────────
#  STEP 10: DISTRICT → CONFIRM
# ─────────────────────────────────────────────────────
async def fir_district(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fir_answers']['contact_district'] = update.message.text
    answers = context.user_data['fir_answers']
    
    summary = (
        "✅ *সকল তথ্য সংগ্রহ হয়েছে!*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "*আপনার দেওয়া তথ্য:*\n\n"
        f"👤 বয়স: {answers.get('victim_age')}\n"
        f"📅 তারিখ: {answers.get('incident_date')}\n"
        f"⏰ সময়: {answers.get('incident_time')}\n"
        f"📍 স্থান: {answers.get('incident_location')}\n"
        f"👥 সম্পর্ক: {answers.get('perpetrator_relation')}\n"
        f"👁️ সাক্ষী: {answers.get('witness')}\n"
        f"📋 আগের রিপোর্ট: {answers.get('previous_report')}\n"
        f"🗺️ বিভাগ: {answers.get('contact_district')}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "এই তথ্য দিয়ে FIR খসড়া তৈরি করব?"
    )
    
    await update.message.reply_text(
        summary,
        parse_mode="Markdown",
        reply_markup=confirm_keyboard()
    )
    return FIR_CONFIRM


# ─────────────────────────────────────────────────────
#  STEP 11: CONFIRM → GENERATE PDF
# ─────────────────────────────────────────────────────
async def fir_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if "বাতিল" in text or "cancel" in text.lower():
        await update.message.reply_text(
            "FIR তৈরি বাতিল করা হয়েছে।\n"
            "যেকোনো সময় /fir লিখে আবার শুরু করতে পারবেন।",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    elif "সংশোধন" in text:
        await update.message.reply_text(
            "ঠিক আছে। /fir লিখে আবার শুরু করুন।",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    elif "হ্যাঁ" in text or "FIR তৈরি" in text:
        await update.message.reply_text(
            "⏳ আপনার FIR খসড়া তৈরি হচ্ছে...\n"
            "কয়েক সেকেন্ড অপেক্ষা করুন।",
            reply_markup=ReplyKeyboardRemove()
        )
        
        try:
            answers = context.user_data['fir_answers']
            user_id = update.message.from_user.id
            output_path = f"/tmp/fir_{user_id}.pdf"
            
            # Generate PDF
            generate_fir_pdf(answers, output_path)
            
            # Send PDF to user
            with open(output_path, 'rb') as pdf_file:
                await update.message.reply_document(
                    document=pdf_file,
                    filename=f"Obhoy_FIR_Draft_{user_id}.pdf",
                    caption=(
                        "✅ *আপনার FIR খসড়া তৈরি হয়েছে!*\n\n"
                        "এই PDF-এ আছে:\n"
                        "📋 আপনার ঘটনার বিবরণ\n"
                        "⚖️ প্রযোজ্য আইন ও শাস্তি\n"
                        "📞 নিকটতম সহায়তা কেন্দ্রের নম্বর\n"
                        "🔢 পরবর্তী পদক্ষেপের গাইড\n\n"
                        "*এখন কী করবেন:*\n"
                        "১. এই PDF নিয়ে নিকটস্থ থানায় যান\n"
                        "২. মহিলা পুলিশ অফিসার চাইতে পারেন\n"
                        "৩. বিনামূল্যে আইনজীবী: *16430*\n"
                        "৪. BLAST: *01730-329945*\n\n"
                        "⚠️ জরুরি প্রয়োজনে: *999*"
                    ),
                    parse_mode="Markdown"
                )
            
            # Clean up temp file
            if os.path.exists(output_path):
                os.remove(output_path)
                
        except Exception as e:
            logger.error(f"FIR generation error: {e}")
            await update.message.reply_text(
                "❌ দুঃখিত, PDF তৈরিতে সমস্যা হয়েছে।\n"
                "অনুগ্রহ করে আবার চেষ্টা করুন: /fir\n\n"
                "অথবা সরাসরি সাহায্য নিন:\n"
                "BLAST: 01730-329945\n"
                "আইনি সহায়তা: 16430"
            )
        
        return ConversationHandler.END
    
    else:
        await update.message.reply_text(
            "অনুগ্রহ করে নিচের অপশন থেকে বেছে নিন।",
            reply_markup=confirm_keyboard()
        )
        return FIR_CONFIRM


# ─────────────────────────────────────────────────────
#  CANCEL HANDLER
# ─────────────────────────────────────────────────────
async def fir_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "FIR তৈরি বাতিল করা হয়েছে।\n\n"
        "যেকোনো সময় /fir লিখে আবার শুরু করতে পারবেন।\n"
        "জরুরি সাহায্যে: 999",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


# ─────────────────────────────────────────────────────
#  CONVERSATION HANDLER — plug into main bot
# ─────────────────────────────────────────────────────
fir_conversation = ConversationHandler(
    entry_points=[CommandHandler("fir", fir_start)],
    states={
        FIR_AGE:         [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_age)],
        FIR_DATE:        [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_date)],
        FIR_TIME:        [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_time)],
        FIR_LOCATION:    [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_location)],
        FIR_RELATION:    [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_relation)],
        FIR_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_description)],
        FIR_WITNESS:     [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_witness)],
        FIR_PREVIOUS:    [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_previous)],
        FIR_DISTRICT:    [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_district)],
        FIR_CONFIRM:     [MessageHandler(filters.TEXT & ~filters.COMMAND, fir_confirm)],
    },
    fallbacks=[CommandHandler("cancel", fir_cancel)],
    allow_reentry=True,
)
