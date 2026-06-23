import asyncio
import requests
import os
import psycopg2

DATABASE_URL = os.getenv("postgresql://postgres:voQbMdZyzvLkQuFobYhYLPYSEJtrQvjr@postgres.railway.internal:5432/railway")


# ================= DB =================

def get_conn():
    return psycopg2.connect(postgresql://postgres:voQbMdZyzvLkQuFobYhYLPYSEJtrQvjr@postgres.railway.internal:5432/railway)


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS seen_sms (
            sms_id TEXT PRIMARY KEY
        );
    """)
    conn.commit()
    cur.close()
    conn.close()


def is_seen(sms_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM seen_sms WHERE sms_id=%s", (sms_id,))
    res = cur.fetchone()
    cur.close()
    conn.close()
    return res is not None


def mark_seen(sms_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO seen_sms (sms_id)
        VALUES (%s)
        ON CONFLICT DO NOTHING;
    """, (sms_id,))
    conn.commit()
    cur.close()
    conn.close()


# ================= TELEGRAM =================

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes


BOT_TOKEN = "8870233137:AAEoxO2rYc85mGJJw0QqFP7qM2QxiE5g4Q8"

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


# ================= GROUPS (3 номера) =================

def normalize(n):
    return ''.join(filter(str.isdigit, str(n)))


ZPD_NUMBERS = [
    normalize("380947100246"),
    normalize("380947100247"),
    normalize("380947100248"),
]

BROKEN_NUMBERS = [
    normalize("380000000002"),
    normalize("380000000003"),
    normalize("380000000004"),
]

JOKER_NUMBERS = [
    normalize("380947222222"),
    normalize("380947333333"),
    normalize("380947444444"),
]

MARTINEZ_NUMBERS = [
    normalize("380947100361"),
    normalize("380947100362"),
    normalize("380947100363"),
]

KKAZANTSEVV_NUMBERS = [
    normalize("380947101540"),
    normalize("380947100981"),
    normalize("380947100597"),
]


# ================= UI =================

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 SMS BOT ACTIVE", callback_data="info")]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("SMS bot started", reply_markup=menu())


async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text("Bot running", reply_markup=menu())


# ================= API =================

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


# ================= SEND =================

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
        await app.bot.send_message(chat_id=chat_id, text=text)
    except Exception as e:
        print("SEND ERROR:", e)


# ================= WORKER =================

async def worker(app):
    while True:
        for label, token in TOKENS.items():

            sms_list = get_sms(token)

            for sms in sms_list:

                sms_id = sms.get("uu_id") or sms.get("uuid") or sms.get("id")
                if not sms_id:
                    continue

                if is_seen(sms_id):
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

                mark_seen(sms_id)

        await asyncio.sleep(5)


# ================= MAIN =================

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("sms", start))
    app.add_handler(CallbackQueryHandler(handler))

    async def post_init(app):
        asyncio.create_task(worker(app))

    app.post_init = post_init
    app.run_polling()


if __name__ == "__main__":
    main()
