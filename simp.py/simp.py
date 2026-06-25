import requests
import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)


import os

BOT_TOKEN = os.getenv("8858371855:AAFzWawMRK4Gg9NTyutAxYhgfLSq8Zk3gL8")
SIMPLELOGIN_API_KEY = os.getenv("uhmoblgrrbegpsqvyjpcvcuzagarjcyyetoxgzdakolhiqetzmfpubfptmhb")

# ==========================
# ЛОГИ
# ==========================

logging.basicConfig(level=logging.INFO)


HEADERS = {
    "Authentication": "uhmoblgrrbegpsqvyjpcvcuzagarjcyyetoxgzdakolhiqetzmfpubfptmhb"
}

# ==========================
# МЕНЮ
# ==========================

def get_menu():
    keyboard = [
        [InlineKeyboardButton("📧 Создать почту", callback_data="create")],
        [InlineKeyboardButton("🔄 Обновить меню", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==========================
# /start или /mail
# ==========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📨 SimpleLogin Bot\n\nВыберите действие:",
        reply_markup=get_menu()
    )

# ==========================
# КНОПКИ
# ==========================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # --------------------------
    # СОЗДАНИЕ АЛИАСА
    # --------------------------
    if query.data == "create":
        try:
            response = requests.post(
                "https://app.simplelogin.io/api/alias/random/new",
                headers=HEADERS,
                timeout=15
            )

            if response.status_code in (200, 201):
                data = response.json()

                alias = (
                    data.get("alias")
                    or data.get("email")
                    or str(data)
                )

                await query.message.reply_text(f"✅ Почта создана:\n\n{alias}")

            else:
                await query.message.reply_text(
                    f"❌ Ошибка API:\n{response.status_code}\n{response.text}"
                )

        except Exception as e:
            await query.message.reply_text(f"❌ Ошибка:\n{e}")


    # --------------------------
    # МЕНЮ
    # --------------------------
    elif query.data == "menu":
        await query.message.edit_text(
            "📨 SimpleLogin Bot\n\nВыберите действие:",
            reply_markup=get_menu()
        )

# ==========================
# MAIN
# ==========================

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler(["start", "mail"], start))
    app.add_handler(CallbackQueryHandler(buttons))

    print("Bot started...")
    app.run_polling()

# ==========================

if __name__ == "__main__":
    main()
