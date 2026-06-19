import asyncio
import requests

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# =========================
# 🔧 CONFIG (ВСТАВЬ СВОИ ДАННЫЕ)
# =========================

BOT_TOKEN = "8870233137:AAEoxO2rYc85mGJJw0QqFP7qM2QxiE5g4Q8"

MAIN_CHAT_ID = -1003861206213
SECOND_CHAT_ID = -5536723301

TELOBAL_API_URL = "https://my.telobal.com/api/v1/sms/inbox/"

TOKENS = {
    "MAIN": "40009eefff36915e11beb235e5bff36f73bf5310ad1c8cd2ed555c8011bb4d77",
    "SECOND": "4d744f96ea88775c823bd27b20c9a77525c6c18c6c8c63a60885a2a908108a49"
}

STYLE = {
    "MAIN": "🟢 MAIN",
    "SECOND": "🔵 SECOND"
}

SPECIAL_NUMBERS = []
seen_sms = set()

# =========================
# UI
# =========================

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 SMS BOT ACTIVE", callback_data="info")],
        [InlineKeyboardButton("📱 Мои номера", callback_data="numbers")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📱 SMS BOT",
        reply_markup=menu()
    )

# =========================
# CALLBACK HANDLER
# =========================

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "info":
        await q.edit_message_text("📡 Bot running", reply_markup=menu())

    elif q.data == "numbers":
        await q.edit_message_text(
            f"📱 ТВОИ НОМЕРА\n\n"
            f"🟢 MAIN:\n{TOKENS['MAIN']}\n\n"
            f"🔵 SECOND:\n{TOKENS['SECOND']}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🟢 MAIN", callback_data="main_nums")],
                [InlineKeyboardButton("🔵 SECOND", callback_data="second_nums")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back")]
            ])
        )

    elif q.data == "main_nums":
        await q.edit_message_text(
            f"🟢 MAIN:\n{TOKENS['MAIN']}",
            reply_markup=menu()
        )

    elif q.data == "second_nums":
        await q.edit_message_text(
            f"🔵 SECOND:\n{TOKENS['SECOND']}",
            reply_markup=menu()
        )

    elif q.data == "back":
        await q.edit_message_text("📱 SMS BOT", reply_markup=menu())

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

# =========================
# SEND
# =========================

async def send(app, text):
    try:
        await app.bot.send_message(chat_id=MAIN_CHAT_ID, text=text)
    except Exception as e:
        print("SEND ERROR:", e)

# =========================
# WORKER
# =========================

async def worker(app):
    while True:
        for label, token in TOKENS.items():

            sms_list = get_sms(token)

            for sms in sms_list:

                sms_id = sms.get("uu_id") or sms.get("uuid") or sms.get("id")
                if not sms_id or sms_id in seen_sms:
                    continue

                sender = sms.get("sender", {}).get("number", "")
                message = sms.get("message", "")

                text = (
                    f"{STYLE[label]} SMS\n\n"
                    f"📤 From: {sender}\n"
                    f"💬 {message}"
                )

                await send(app, text)
                seen_sms.add(sms_id)

        await asyncio.sleep(5)

# =========================
# MAIN
# =========================

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handler))

    async def post_init(app):
        asyncio.create_task(worker(app))

    app.post_init = post_init

    app.run_polling()


if __name__ == "__main__":
    main()