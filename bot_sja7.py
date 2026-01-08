from telegram.ext import ApplicationBuilder, CommandHandler
from telegram import Update
from telegram.ext import ContextTypes

TOKEN = "8376494600:AAHJedKMXU075lfANlXI1D_9N-wf_BJ17Zs"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ BOT OK")

print("🚀 Bot en démarrage...")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.run_polling()
