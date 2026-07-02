import asyncio
import requests
import json
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# =========================
# 🔧 CONFIG
# =========================

BOT_TOKEN = "8870233137:AAFCLHEGjMJ6xuZNbkfTcU01uCM6mnr1des"

MAIN_CHAT_ID = -1003861206213
ZPD_CHAT_ID = -5536723301
BROKEN_CHAT_ID = -5522999875
JOKER_CHAT_ID = -5141561349
MARTINEZ_CHAT_ID = -5308626568
KKAZANTSEVV_CHAT_ID = -5387239081

TELOBAL_API_URL = "https://my.telobal.com/api/v1/sms/inbox/"

TOKENS = {
    "MAIN": "40009eefff36915e11beb235e5bff36f73bf5310ad1c8cd2ed555c8011bb4d77",
    "SECOND": "4d744f96ea88775c823bd27b20c9a77525c6c18c6c8c63a60885a2a908108a49"
}

STYLE = {
    "MAIN": "🟢 MAIN",
    "SECOND": "🔵 SECOND"
}

# =========================
# HELPERS (SAVE STATE)
# =========================

SEEN_FILE = "/var/lib/postgresql/data/seen_sms.json"

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen():
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen_sms), f)

    print("SAVED:", len(seen_sms))

def normalize(num):
    return ''.join(filter(str.isdigit, str(num)))

ZPD_NUMBERS = [
    normalize("0"),
    normalize("0"),
    normalize("0"),
]

BROKEN_NUMBERS = [
    normalize("0"),
    normalize("0"),
    normalize("0"),
]

JOKER_NUMBERS = [
    normalize("380947100960"),
    normalize("0"),
    normalize("0"),
]

MARTINEZ_NUMBERS = [
    normalize("380947100490"),
    normalize("0"),
    normalize("0"),

]

KKAZANTSEVV_NUMBERS = [
    normalize("0"),
    normalize("0"),
    normalize("0"),

]

seen_sms = load_seen()
print("LOADED SMS:", len(seen_sms))

    

# =========================
# UI
# =========================

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 SMS BOT ACTIVE", callback_data="info")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "SMS bot started",
        reply_markup=menu()
    )

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text("Bot running", reply_markup=menu())

# =========================
# API
# =========================

def get_sms(token):
    try:
        r = requests.get(
            TELOBAL_API_URL,
            headers={"Authorization": token},
            timeout=10
        )

        if r.status_code == 200:
            return r.json().get("result", [])

    except Exception as e:
        print("API ERROR:", e)

    return []
    # Первичный импорт существующих SMS
if not seen_sms:
    print("BUILDING INITIAL CACHE...")

    for token in TOKENS.values():
        for sms in get_sms(token):
            sms_id = sms.get("uu_id") or sms.get("uuid") or sms.get("id")

            if sms_id:
                seen_sms.add(sms_id)

    save_seen()
    print("INITIAL CACHE:", len(seen_sms))

# =========================
# SEND
# =========================

async def send(app, text, recipient):

    if recipient in ZPD_NUMBERS:
        chat_id = ZPD_CHAT_ID

    elif recipient in BROKEN_NUMBERS:
        chat_id = BROKEN_CHAT_ID

    elif recipient in JOKER_NUMBERS:
        chat_id = JOKER_CHAT_ID
    
    elif recipient in MARTINEZ_NUMBERS:
        chat_id = MARTINEZ_CHAT_ID
    
    elif recipient in KKAZANTSEVV_NUMBERS:
        chat_id = KKAZANTSEVV_CHAT_ID

    else:
        chat_id = MAIN_CHAT_ID

    try:
        await app.bot.send_message(
            chat_id=chat_id,
            text=text
        )
    except Exception as e:
        print("SEND ERROR:", e)
# =========================
# WORKER
# =========================

    # =========================
# WORKER
# =========================

async def worker(app):
    while True:
        for label, token in TOKENS.items():

            sms_list = get_sms(token)

            for sms in sms_list:

                sms_id = sms.get("uu_id") or sms.get("uuid") or sms.get("id")

                print("SMS ID:", sms_id)
                print("SMS DATA:", sms)

                if not sms_id or sms_id in seen_sms:
                    continue

                dest = sms.get("destination", "")

                if isinstance(dest, dict):
                    recipient = dest.get("number", "")
                else:
                    recipient = dest or ""

                recipient = normalize(recipient)

                sender = sms.get("sender", {}).get("number", "")
                message = sms.get("message", "")

                text = (
                    f"{STYLE[label]} SMS\n\n"
                    f"📤 From: {sender}\n"
                    f"📥 To: {recipient}\n"
                    f"💬 {message}"
                )

                await send(app, text, recipient)

                seen_sms.add(sms_id)
                save_seen()

        await asyncio.sleep(5)

# =========================
# MAIN
# =========================

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("sms", start))
    app.add_handler(CallbackQueryHandler(handler))

    async def post_init(app):
        asyncio.create_task(worker(app))

    app.post_init = post_init

    app.run_polling()


if __name__ == "__main__":
    main()
