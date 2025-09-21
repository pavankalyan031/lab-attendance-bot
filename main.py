# main.py
import logging
import json
import requests
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler,
    CallbackQueryHandler,
)

# ---------------------
# CONFIG
# ---------------------
# Put your token here (or set via environment and read with os.getenv)
BOT_TOKEN = "8217846332:AAFlx9Oc90FO562-5f6WnFTRAZAY3v_Wv18"

# Google Form "formResponse" endpoint (make sure it ends with /formResponse)
FORM_URL = "https://docs.google.com/forms/u/0/d/e/1FAIpQLSdJq_hTWoOZ-wTfIIfPQ5CoX0_39I7FrlqOkFQhgjYh7YYEXA/formResponse"

# Field mapping for your Google Form (update if the form changes)
FIELDS = {
    "name": "entry.2134157106",
    "roll": "entry.790265619",
    "gender": "entry.1079838802",
    "batch": "entry.890719495",
    "phone": "entry.1090314474",
    "date": "entry.824846641",
    "time_from": "entry.317799120",
    "time_to": "entry.2145357821",
    "remarks": "entry.1790524061",
}

# ---------------------
# Logging
# ---------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------------------
# Conversation states
# ---------------------
(
    ASK_DAYS,
    ASK_NAME,
    ASK_ROLL,
    ASK_GENDER,
    ASK_BATCH,
    ASK_PHONE,
    ASK_DATE,
    ASK_FROM,
    ASK_TO,
    ASK_REMARKS,
    CONFIRMATION,
) = range(11)


# ---------------------
# Helpers
# ---------------------
def parse_date_to_date(d: str):
    """Try several date formats and return a datetime.date. If parsing fails, return today's date."""
    s = d.strip()
    fmts = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%m-%d-%Y",
        "%Y/%m/%d",
        "%b %d %Y",
        "%B %d %Y",
        "%d %b %Y",
        "%d %B %Y",
    ]
    for fmt in fmts:
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            continue
    # try to handle 'Sept 20' or '20 Sept' with current year
    try:
        now = datetime.now()
        try_formats = ["%b %d", "%B %d", "%d %b", "%d %B"]
        for fmt in try_formats:
            try:
                dt = datetime.strptime(s, fmt)
                return dt.replace(year=now.year).date()
            except Exception:
                pass
    except Exception:
        pass
    # fallback: today
    return datetime.now().date()


def parse_time_to_24(t: str):
    """Try several time formats and return 'HH:MM' 24-hour string; fallback returns cleaned input."""
    s = t.strip().upper().replace(".", ":")
    fmts = ["%H:%M", "%I:%M %p", "%I:%M%p", "%I %p"]
    for fmt in fmts:
        try:
            return datetime.strptime(s, fmt).strftime("%H:%M")
        except Exception:
            continue
    # try to zero-pad single-digit hours like "7:30" -> "07:30"
    try:
        parts = s.split(":")
        if len(parts) == 2:
            hh = parts[0].zfill(2)
            mm = parts[1][:2]  # cut off any trailing text (AM/PM handled above)
            return f"{hh}:{mm}"
    except Exception:
        pass
    return s


def save_local_entry(entry: dict, path="submissions.json"):
    """Append entry to a local JSON array file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            arr = json.load(f)
    except Exception:
        arr = []
    arr.append(entry)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(arr, f, indent=2, ensure_ascii=False)


def submit_form_once(entry: dict) -> (int, str):
    """Submit one entry to Google Form. Return (status_code, short_response_text)."""
    payload = {
        FIELDS["name"]: entry["name"],
        FIELDS["roll"]: entry["roll"],
        FIELDS["gender"]: entry["gender"],
        FIELDS["batch"]: entry["batch"],
        FIELDS["phone"]: entry["phone"],
        FIELDS["date"]: entry["date"],
        FIELDS["time_from"]: entry["time_from"],
        FIELDS["time_to"]: entry["time_to"],
        FIELDS["remarks"]: entry["remarks"],
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible)",
        "Referer": FORM_URL.replace("/formResponse", "/viewform"),
    }
    try:
        r = requests.post(FORM_URL, data=payload, headers=headers, timeout=15)
        short = (r.text[:200] + "...") if r.text else ""
        logger.info("Form submission status: %s", r.status_code)
        return r.status_code, short
    except Exception as e:
        logger.exception("Exception while submitting form: %s", e)
        return 0, str(e)[:200]


def build_preview(data: dict) -> str:
    return (
        "📋 Please review your details:\n\n"
        f"👤 Full Name: {data.get('name')}\n"
        f"🎓 Roll Number: {data.get('roll')}\n"
        f"⚧ Gender: {data.get('gender')}\n"
        f"👩‍💻 Batch: {data.get('batch')}\n"
        f"📱 Phone: {data.get('phone')}\n"
        f"📅 Start Date: {data.get('date')}\n"
        f"⏰ Time From: {data.get('time_from')}\n"
        f"⏰ Time To: {data.get('time_to')}\n"
        f"📝 Remarks: {data.get('remarks')}\n\n"
        "Press *Submit* to send entries for the next N days (auto-increment dates),\n"
        "or *Edit* to restart, or *Cancel* to abort."
    )


# ---------------------
# Handlers
# ---------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Lab Automation Bot!\n"
        "I will help you submit your lab attendance.\n\n"
        "🤖 Created by: *Pavan Kalyan* 🚀\n\n"
        "How many days do you want to submit? (1–30)\n\n"
        "You can send like: `Hi 10` or reply with a number.",
        parse_mode="Markdown",
    )
    return ASK_DAYS


async def ask_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    # support "Hi 10" quick start
    if text.lower().startswith("hi "):
        text = text.split(None, 1)[1]
    try:
        days = int(text)
        if days < 1 or days > 60:
            raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ Please enter a valid number of days (1–60).")
        return ASK_DAYS
    context.user_data["days"] = days
    await update.message.reply_text("✍️ Enter Full Name:")
    return ASK_NAME


async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text("🎓 Enter Roll Number:")
    return ASK_ROLL


async def ask_roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["roll"] = update.message.text.strip()
    await update.message.reply_text("⚧️ Enter Gender (Male/Female/Other):")
    return ASK_GENDER


async def ask_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["gender"] = update.message.text.strip()
    await update.message.reply_text("👩‍💻 Enter Batch (e.g., 2023):")
    return ASK_BATCH


async def ask_batch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["batch"] = update.message.text.strip()
    await update.message.reply_text("📱 Enter Phone Number:")
    return ASK_PHONE


async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text.strip()
    await update.message.reply_text("📅 Enter Start Date (YYYY-MM-DD or MM/DD/YYYY):")
    return ASK_DATE


async def ask_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["date"] = update.message.text.strip()
    await update.message.reply_text("⏰ Enter Time From (e.g. 07:30 or 7:30 PM):")
    return ASK_FROM


async def ask_from(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["time_from"] = update.message.text.strip()
    await update.message.reply_text("⏰ Enter Time To (e.g. 09:30 or 9:30 PM):")
    return ASK_TO


async def ask_to(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["time_to"] = update.message.text.strip()
    await update.message.reply_text("📝 Enter Remarks (or NA):")
    return ASK_REMARKS


async def ask_remarks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["remarks"] = update.message.text.strip() or "NA"
    # preview and buttons
    # normalize date/time for preview
    try:
        parsed_date = parse_date_to_date(context.user_data["date"])
        context.user_data["date"] = parsed_date.isoformat()
    except Exception:
        # keep as-is if error
        pass
    context.user_data["time_from"] = parse_time_to_24(context.user_data["time_from"])
    context.user_data["time_to"] = parse_time_to_24(context.user_data["time_to"])

    preview = build_preview(context.user_data)
    keyboard = [
        [InlineKeyboardButton("✅ Submit", callback_data="submit")],
        [InlineKeyboardButton("✏️ Edit (restart)", callback_data="edit"), InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
    ]
    await update.message.reply_text(
        preview, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=None
    )
    return CONFIRMATION


async def confirmation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "cancel":
        context.user_data.clear()
        await query.edit_message_text("❌ Submission cancelled. Use /start to try again.")
        return ConversationHandler.END

    if data == "edit":
        # simple edit: restart the flow (less complex). User can start again.
        context.user_data.clear()
        await query.edit_message_text("🔄 Restarting the form. Use /start to begin again.")
        return ConversationHandler.END

    if data == "submit":
        # Auto-increment dates and submit for N days
        user = context.user_data.copy()
        days = int(user.get("days", 1))
        # parse start date robustly
        start_date = parse_date_to_date(user.get("date", ""))
        successes = 0
        failures = 0
        details = []
        for i in range(days):
            day_date = (start_date + timedelta(days=i)).isoformat()
            entry = {
                "name": user.get("name", ""),
                "roll": user.get("roll", ""),
                "gender": user.get("gender", ""),
                "batch": user.get("batch", ""),
                "phone": user.get("phone", ""),
                "date": day_date,
                "time_from": parse_time_to_24(user.get("time_from", "")),
                "time_to": parse_time_to_24(user.get("time_to", "")),
                "remarks": user.get("remarks", "NA"),
                "submitted_at": datetime.now().isoformat(),
            }
            status, short = submit_form_once(entry)
            # Treat 200 or 302 as success; some forms redirect (302)
            if status in (200, 302, 204):
                successes += 1
                ok = True
            else:
                failures += 1
                ok = False
            details.append({"date": day_date, "ok": ok, "status": status, "short": short})
            # save locally regardless
            save_local_entry(entry)
        # build result message
        msg = f"🏁 Process completed.\n✅ Submitted: {successes} | ❌ Failed: {failures}\n\n"
        # include small per-day detail if there were failures
        if failures:
            msg += "Failures details (first few):\n"
            for d in details[:5]:
                if not d["ok"]:
                    msg += f"- {d['date']}: status={d['status']}\n"
        await query.edit_message_text(msg)
        context.user_data.clear()
        return ConversationHandler.END


async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Operation cancelled. Use /start to begin again.")
    return ConversationHandler.END


# ---------------------
# Main
# ---------------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex(r"(?i)^hi\s+\d+$"), ask_days),
        ],
        states={
            ASK_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_days)],
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_ROLL: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_roll)],
            ASK_GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_gender)],
            ASK_BATCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_batch)],
            ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            ASK_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_date)],
            ASK_FROM: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_from)],
            ASK_TO: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_to)],
            ASK_REMARKS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_remarks)],
            CONFIRMATION: [CallbackQueryHandler(confirmation_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel_cmd)],
        per_message=False,
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("help", lambda u, c: u.message.reply_text(
        "Use /start to begin. Send Hi <n> (e.g. Hi 5) to quick start.\nUse /cancel to stop."
    )))
    app.add_handler(CommandHandler("creator", lambda u, c: u.message.reply_text("🤖 Created by: Pavan Kalyan")))

    logger.info("Bot starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
