from telegram.ext import ApplicationBuilder, CommandHandler
import asyncio

TOKEN = "8376494600:AAHJedKMXU075lfANlXI1D_9N-wf_BJ17Zs"

async def start(update, context):
    await update.message.reply_text("✅ Bot en ligne")

print("🚀 Bot en démarrage...")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))

app.run_polling()
