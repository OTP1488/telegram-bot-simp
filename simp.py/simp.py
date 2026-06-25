from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = "ТВОЙ_ТОКЕН"

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("COMMAND RECEIVED")
    await update.message.reply_text("Работает!")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("test", test))

print("Bot started...")
app.run_polling()
