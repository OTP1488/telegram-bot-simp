import asyncio
import requests

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# =========================
# CONFIG
# =========================

BOT_TOKEN = "8870233137:AAEoxO2rYc85mGJJw0QqFP7qM2QxiE5g4Q8"

MAIN_CHAT_ID = -1003861206213
SECOND_CHAT_ID = -5536723301

TELOBAL_API_URL = "https://my.telobal.com/api/v1/sms/inbox/"

TOKENS = {
    "MAIN": "40009eefff36915e11beb235e5bff36f73bf5310ad1c8cd2ed555c8011bb4d77"
    "SECOND": "4d744f96ea88775c823bd27b20c9a77525c6c18c6c8c63a60885a2a908108a49"
}

STYLE = {
    "MAIN": "🟢 MAIN",
    "SECOND": "🔵 SECOND"
}

seen_sms = set()

# =========================
# MENU (ПАНЕЛЬ)
# =========================

def panel_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Список номеров", callback_data="numbers")],
        [InlineKeyboardButton("📡 Статус бота", callback_data="status")]
    ])

def back_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Назад", callback_data="panel")]
    ])

# =========================
# START / PANEL
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📱 SMS BOT PANEL",
        reply_markup=panel_menu()
    )

async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📱 ПАНЕЛЬ УПРАВЛЕНИЯ",
        reply_markup=panel_menu()
    )

# =========================
# CALLBACKS
# =========================

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    # 📱 PANEL
    if q.data == "panel":
        await q.edit_message_text(
            "📱 ПАНЕЛЬ УПРАВЛЕНИЯ",
            reply_markup=panel_menu()
        )

    # 📋 СПИСОК НОМЕРОВ
    elif q.data == "numbers":
        text = (
            "📋 СПИСОК НОМЕРОВ\n\n"
            f"🟢 MAIN:\n{TOKENS['MAIN']}\n\n"
            f"🔵 SECOND:\n{TOKENS['SECOND']}"
        )

        await q.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🟢 MAIN", callback_data="main")],
                [InlineKeyboardButton("🔵 SECOND", callback_data="second")],
                [InlineKeyboardButton("🔙 Назад", callback_data="panel")]
            ])
        )

    elif q.data == "main":
        await q.edit_message_text(
            f"🟢 MAIN\n\n{TOKENS['MAIN']}",
            reply_markup=back_menu()
        )

    elif q.data == "second":
        await q.edit_message_text(
            f"🔵 SECOND\n\n{TOKENS['SECOND']}",
            reply_markup=back_menu()
        )

    elif q.data == "status":
        await q.edit_message_text(
            "📡 Бот работает нормально",
            reply_markup=panel_menu()
        )

# =========================
# SMS API
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

    except:
        pass

    return []

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

                try:
                    await app.bot.send_message(chat_id=MAIN_CHAT_ID, text=text)
                except:
                    pass

                seen_sms.add(sms_id)

        await asyncio.sleep(5)

# =========================
# MAIN
# =========================

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", panel))
    app.add_handler(CallbackQueryHandler(handler))

    async def post_init(app):
        asyncio.create_task(worker(app))

    app.post_init = post_init

    app.run_polling()

if __name__ == "__main__":
    main()
