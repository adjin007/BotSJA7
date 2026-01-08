from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os

# Fonction pour /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello!")

# Récupérer le token depuis les variables d'environnement
TOKEN = "8376494600:AAHJedKMXU075lfANlXI1D_9N-wf_BJ17Zs"

# Création de l'application du bot
app = ApplicationBuilder().token(TOKEN).build()

# Ajouter le handler pour /start
app.add_handler(CommandHandler("start", start))

# Lancer le bot
print("Bot en route...")
app.run_polling()
