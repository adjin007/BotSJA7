#Imports
#from flask import Flask
from threading import Thread
import os
import pytz #Pas utiliser pour le moment j'ai utiliser zoneinfo
import asyncio
import json
import time
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

BOT_TOKEN = "8376494600:AAHJedKMXU075lfANlXI1D_9N-wf_BJ17Zs"
CANAL_ID = -1003586151168
ADMIN_ID = 5068784805
WHITELIST_FILE = "whitelist.json"
attente_id = {}

dernier_signal_fun = {}
dernier_signal_premium = {}
DELAI_SIGNAL = 3 * 60  # en secondes
DELAI_SIGNAL_PREMIUM = 3 * 60  # 3 minutes exprimées en secondes

#Fonctions pour gerer l'historique des predictions fun
HISTORIQUE_FUN_FILE = "historique_fun.json"
def charger_historique_fun():
    if not os.path.exists(HISTORIQUE_FUN_FILE):
        return {}
    with open(HISTORIQUE_FUN_FILE, "r") as f:
        return json.load(f)
def sauvegarder_historique_fun(hist):
    with open(HISTORIQUE_FUN_FILE, "w") as f:
        json.dump(hist, f)

#Fonctions pour gerer la whitelist
def ajouter_a_whitelist(user_id):
    if not os.path.exists(WHITELIST_FILE):
        with open(WHITELIST_FILE, "w") as f:
            json.dump([], f)
    with open(WHITELIST_FILE, "r") as f:
        whitelist = json.load(f)
    if str(user_id) not in whitelist:
        whitelist.append(str(user_id))
        with open(WHITELIST_FILE, "w") as f:
            json.dump(whitelist, f)

def est_dans_whitelist(user_id):
    if not os.path.exists(WHITELIST_FILE):
        return False
    with open(WHITELIST_FILE, "r") as f:
        whitelist = json.load(f)
    return str(user_id) in whitelist

#Fonctions pour gerer les credits donnés au joeur premium
CREDIT_FILE = "premium_credits.json"
def ajouter_credit_premium(user_id: int, nombre: int):
    if not os.path.exists(CREDIT_FILE):
        with open(CREDIT_FILE, "w") as f:
            json.dump({}, f)

    with open(CREDIT_FILE, "r") as f:
        credits = json.load(f)

    user_id_str = str(user_id)
    if user_id_str in credits:
        credits[user_id_str] += nombre
    else:
        credits[user_id_str] = nombre

    with open(CREDIT_FILE, "w") as f:
        json.dump(credits, f)

PREMIUM_CREDITS_FILE = "premium_credits.json"

def charger_credits():
    if not os.path.exists(PREMIUM_CREDITS_FILE):
        return {}
    with open(PREMIUM_CREDITS_FILE, "r") as f:
        return json.load(f)

def sauvegarder_credits(credits):
    with open(PREMIUM_CREDITS_FILE, "w") as f:
        json.dump(credits, f)

def get_credit_premium(user_id):
    credits = charger_credits()
    return int(credits.get(str(user_id), 0))

def decrementer_credit_premium(user_id):
    credits = charger_credits()
    uid = str(user_id)
    if uid in credits and credits[uid] > 0:
        credits[uid] -= 1
        sauvegarder_credits(credits)

# Historique global des signaux recu par les utilisateurs premium de mon bot

HISTORIQUE_GLOBAL_FILE = "historique_global.json"

def enregistrer_historique_global(user_id: int, type_signal: str, contenu: dict):
    if not os.path.exists(HISTORIQUE_GLOBAL_FILE):
        historique = []
    else:
        with open(HISTORIQUE_GLOBAL_FILE, "r") as f:
            try:
                historique = json.load(f)
            except json.JSONDecodeError:
                historique = []

    entree = {
        "user_id": user_id,
        "type": type_signal,  # "FUN" ou "PREMIUM"
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "prediction": contenu
    }
    historique.append(entree)

    with open(HISTORIQUE_GLOBAL_FILE, "w") as f:
        json.dump(historique, f, indent=2)
        
# Fonction de blocage utilisateur
                 
BLACKLIST_FILE = "blacklist.json"
def ajouter_a_blacklist(user_id):
    if not os.path.exists(BLACKLIST_FILE):
        with open(BLACKLIST_FILE, "w") as f:
            json.dump([], f)

    with open(BLACKLIST_FILE, "r") as f:
        blacklist = json.load(f)

    if str(user_id) not in blacklist:
        blacklist.append(str(user_id))

    with open(BLACKLIST_FILE, "w") as f:
        json.dump(blacklist, f)

def est_dans_blacklist(user_id):
    if not os.path.exists(BLACKLIST_FILE):
        return False
    with open(BLACKLIST_FILE, "r") as f:
        blacklist = json.load(f)
    return str(user_id) in blacklist

#Commande start et bouton de vérification
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Rejoindre le canal Telegram", url="https://t.me/+VqK5KU0QE7ZjODg8")],
        [InlineKeyboardButton("Rejoindre le groupe WhatsApp", url="https://whatsapp.com/channel/0029VbAwX6w4dTnLQahLoV1H")],
        [InlineKeyboardButton("VÉRIFICATION", callback_data="verifier")]
    ]
    await update.message.reply_text(
        "📮 BIENVENUE DANS SJA7 SUPER PREDICTOR !🚀\n\nPour continuer, veuillez rejoindre notre canal Telegram et WhatsApp.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

#Callback verification et reception ID
async def bouton_verification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
   # ajouter_a_whitelist(user_id)
    attente_id[user_id] = True

    await context.bot.send_message(
        chat_id=user_id,
        text=(
            "📲 Voici comment accéder au bot\n"
            "1️⃣ Créez un compte 1WIN avec le code SJA7\n"
            "2️⃣ Rechargez au moins 5000F\n"
            "3️⃣ Cliquez ici pour vous inscrire 👉 [Lien](https://1wzitc.com/?p=a7j8)\n\n"
            "⚠ Sans ces étapes, le bot ne fonctionnera pas !"
        ),
        parse_mode="Markdown"
    )
    await context.bot.send_message(chat_id=user_id, text="✍ Entrez maintenant votre ID 1WIN ici.")

async def recevoir_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in attente_id:
        identifiant = update.message.text.strip()
        del attente_id[user_id]

        await update.message.reply_text("📋 Vérification en cours...")
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"🔔 Nouvelle demande de validation\n"
                f"ID Telegram: {user_id}\n"
                f"Nom: @{update.effective_user.username or 'inconnu'}\n"
                f"ID 1WIN: {identifiant}\n\n"
                f"/valider {user_id} ou /rejeter {user_id}"
            )
        )
    else:
        await update.message.reply_text("❌ Tapez d'abord sur le bouton VÉRIFICATION.")

#Callback verification et reception ID  
async def bouton_verification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    try:
        membre = await context.bot.get_chat_member(chat_id=CANAL_ID, user_id=user_id)
        if membre.status in ["left", "kicked"]:
            await context.bot.send_message(
                chat_id=user_id,
                text="🚫 Vous devez d’abord rejoindre le canal Telegram pour continuer.\n\n👉 [Lien du canal](https://t.me/+VqK5KU0QE7ZjODg8)",
                parse_mode="Markdown"
            )
            return
    except Exception as e:
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Une erreur est survenue lors de la vérification de votre abonnement.\nMerci de réessayer."
        )
        return

    # S'il est bien abonné :
    attente_id[user_id] = True
    await context.bot.send_message(
        chat_id=user_id,
        text=(
            "📲 Voici comment accéder au bot\n"
            "1️⃣ Créez un compte 1WIN avec le code SJA7\n"
            "2️⃣ Rechargez au moins 5000F\n"
            "3️⃣ Cliquez ici pour vous inscrire 👉 [Lien](https://1wzitc.com/?p=a7j8)\n\n"
            "⚠ Sans ces étapes, le bot ne fonctionnera pas !"
        ),
        parse_mode="Markdown"
    )
    await context.bot.send_message(chat_id=user_id, text="✍ Entrez maintenant votre ID 1WIN ici.")
#Reception ID 

async def recevoir_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    if user_id in attente_id:
        del attente_id[user_id]
        await update.message.reply_text("📋 Vérification en cours...")
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"🔔 Nouvelle demande de validation\n"
                f"ID Telegram: {user_id}\n"
                f"Nom: @{update.message.from_user.username or 'Inconnu'}\n"
                f"ID 1WIN: {text}\n\n"
                f"/valider {user_id} ou /rejeter {user_id}"
            )
        )
#Commandes valider et rejeter 
async def valider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        user_id = int(context.args[0])
        ajouter_a_whitelist(user_id)

        await context.bot.send_message(user_id, "✅ Vous avez été validé avec succès !")

        keyboard_principal = [
            [KeyboardButton("🔥 OBTENIR UNE PRÉDICTION")],
            [KeyboardButton("🎲 SIGNAL PREMIUM")],
            [KeyboardButton("👥 PARRAINAGE"), KeyboardButton("❓ AIDE")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard_principal, resize_keyboard=True)

        await context.bot.send_message(
            chat_id=user_id,
            text="✅ Vous êtes maintenant validé !\n\nChoisissez une des action ci-dessous :",
            reply_markup=reply_markup
        )

        await update.message.reply_text("Validation envoyée.")

    except:
        await update.message.reply_text("❌ Format attendu : /valider [id]")

async def rejeter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        user_id = int(context.args[0])
        await context.bot.send_message(user_id, "❌ Votre demande a été rejetée. Veuillez reprendre depuis le début avec le bon code promo.")
        await update.message.reply_text("Rejet envoyé.")
    except:
        await update.message.reply_text("❌ Format attendu : /rejeter [id]")        

#Commandes bloquer utilisateur
async def bloquer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Vous n'êtes pas autorisé à faire ça.")
        return

    try:
        user_id = int(context.args[0])
        ajouter_a_blacklist(user_id)
        await update.message.reply_text(f"🚫 L'utilisateur {user_id} a été bloqué.")
        await context.bot.send_message(
            chat_id=user_id,
            text="🚫 Vous avez été bloqué de ce bot pour non respect des règles. Contactez l’administrateur si besoin."
        )
    except:
        await update.message.reply_text("❌ Utilisation : /bloquer [user_id]")
               
# === COMMANDE ADMIN POUR DÉBLOQUER UN UTILISATEUR ===
async def debloquer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Vous n'êtes pas autorisé à utiliser cette commande.")
        return

    try:
        user_id = str(context.args[0])

        # Charger le fichier de blacklist
        if os.path.exists(BLACKLIST_FILE):
            with open(BLACKLIST_FILE, "r") as f:
                blacklist = json.load(f)
        else:
            blacklist = []

        if user_id in blacklist:
            blacklist.remove(user_id)
            with open(BLACKLIST_FILE, "w") as f:
                json.dump(blacklist, f)
            await update.message.reply_text(f"✅ L'utilisateur {user_id} a été débloqué.")
        else:
            await update.message.reply_text("ℹ Cet utilisateur n'était pas bloqué.")
    except:
        await update.message.reply_text("❌ Utilisation : /debloquer [user_id]")
        
# === COMMANDE ADMIN POUR AFFICHER LA WHITELIST AVEC USERNAMES ===
async def voir_whitelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not os.path.exists(WHITELIST_FILE):
        await update.message.reply_text("📁 Aucun utilisateur validé pour le moment.")
        return

    with open(WHITELIST_FILE, "r") as f:
        whitelist = json.load(f)

    if not whitelist:
        await update.message.reply_text("📁 Aucun utilisateur validé pour le moment.")
        return

    # Construction du message
    message = "<b>📋 Liste des utilisateurs validés :</b>\n\n"
    for user_id in whitelist:
        message += f"• <code>{user_id}</code>\n"

    await update.message.reply_text(message, parse_mode="HTML")
        
# Commande pour ajouter crédit             
async def ajouter_credit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Vous n'êtes pas autorisé à utiliser cette commande.")
        return

    try:
        user_id = int(context.args[0])
        nombre = int(context.args[1])
        ajouter_credit_premium(user_id, nombre)

        await update.message.reply_text(f"✅ {nombre} crédits PREMIUM ont été ajoutés à l'utilisateur {user_id}.")

        await context.bot.send_message(
            chat_id=user_id,
            text=f"🎁 {nombre} prédiction(s) PREMIUM vous ont été offertes par l’administrateur. Profitez-en !"
        )
    except:
        await update.message.reply_text("❌ Utilisation : /credit [user_id] [nombre]")

#Fonctions pour les boutons du menu principal
async def bouton_prediction_fun(update, context):
    import time  # À mettre en haut si pas encore importé
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # Vérification dans la blacklist
    if est_dans_blacklist(update.effective_user.id):
        await update.message.reply_text("🚫 Vous avez été bloqué de ce bot pour non respect des règles.")
        return

    # 1. Vérification de la whitelist
    if not est_dans_whitelist(user_id):
        await update.message.reply_text("❌ Tapez d'abord sur le bouton VÉRIFICATION.")
        return

    # 2. Vérification du délai
    maintenant = time.time()
    if user_id in dernier_signal_fun:
        if maintenant - dernier_signal_fun[user_id] < DELAI_SIGNAL:
            await update.message.reply_text("⏳ Attendez 3 minutes avant de demander un nouveau signal FUN.")
            return
    dernier_signal_fun[user_id] = maintenant

    # 3. Animation avec le sticker
    sticker_msg = await context.bot.send_sticker(
        chat_id, sticker="CAACAgIAAxkBAAICo2g1sgF6Ru6Dy01bp_j1fgJOMUbxAAJQAAP3AsgPBMOGfB7N13I2BA"
    )
    await asyncio.sleep(5)
    await context.bot.delete_message(chat_id=chat_id, message_id=sticker_msg.message_id)

    # 4. Lecture des prédictions
    with open("fun_predictions.json", "r") as f:
        predictions = json.load(f)

    # 5. Gérer l'historique
    HISTORIQUE_FUN_FILE = "historique_fun.json"

    def charger_historique_fun():
        if not os.path.exists(HISTORIQUE_FUN_FILE):
            return {}
        with open(HISTORIQUE_FUN_FILE, "r") as f:
            return json.load(f)

    def sauvegarder_historique_fun(hist):
        with open(HISTORIQUE_FUN_FILE, "w") as f:
            json.dump(hist, f)

    historique = charger_historique_fun()
    deja_envoyees = historique.get(str(user_id), [])
    dispo = [p for p in predictions if p["cote"] not in deja_envoyees]

    if not dispo:
        # Toutes les prédictions ont été vues, on réinitialise
        deja_envoyees = []
        dispo = predictions

    # 6. Choisir une prédiction aléatoire parmi celles dispo
    prediction = random.choice(dispo)
    deja_envoyees.append(prediction["cote"])
    historique[str(user_id)] = deja_envoyees
    sauvegarder_historique_fun(historique)

    # 7. Heure de prédiction
    heure_pred = (datetime.now(pytz.timezone("Africa/Porto-Novo")) + timedelta(minutes=2)).strftime("%H:%M")

    # 8. Message formaté
    message = (
        "SJA7 LUCKYJET PREDICTOR\n"
        "┏━━━━━━━━━━━━━\n"
        f"┠ ◆ ﻿﻿𝐇𝐄𝐔𝐑𝐄 : {heure_pred} 🇧🇯\n"
        "┠\n"
        f"┠ ◆𝐂𝐎𝐄𝐅𝐅𝐈𝐂𝐈𝐄𝐍𝐓 : {prediction['cote']} 🎯\n"
        "┠\n"
        f"┠ ◆𝐀𝐒𝐒𝐔𝐑𝐀𝐍𝐂𝐄 : {prediction['assurance']} 🛡\n"
        "┗━━━━━━━━━━━━━\n\n"
        "S'INSCRIRE SUR 1WIN ICI...✍\n"
        "[https://1wzitc.com/?p=a7j8](https://1wzitc.com/?p=a7j8)\n"
        "Code promo : SJA7"
    )

    await update.message.reply_text(message, parse_mode="Markdown")


# === FONCTION - SIGNAL PREMIUM (STRUCTURÉ) ===

PREMIUM_FILE = "premium_predictions.json"

async def bouton_prediction_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # Vérification dans la blacklist
    if est_dans_blacklist(update.effective_user.id):
        await update.message.reply_text("🚫 Vous avez été bloqué de ce bot pour non respect des règles.")
        return

    # Vérification dans la whitelist
    if not est_dans_whitelist(user_id):
        await update.message.reply_text("❌ Tapez d'abord sur le bouton VÉRIFICATION.")
        return

    # Vérification des crédits
    credits = get_credit_premium(user_id)
    if credits <= 0:
        await update.message.reply_text("❌ Vous n’avez plus de crédits PREMIUM disponibles.\nVeuillez contacter l’administrateur.")
        return

    # Vérification du délai
    maintenant = time.time()
    if user_id in dernier_signal_premium:
        if maintenant - dernier_signal_premium[user_id] < DELAI_SIGNAL_PREMIUM:
            await update.message.reply_text("⏳ Attendez 3 minutes avant de redemander un signal PREMIUM.")
            return

    dernier_signal_premium[user_id] = maintenant

    # Animation avec sticker et attente
    sticker_msg = await context.bot.send_sticker(chat_id, "CAACAgIAAxkBAAICo2g1sgF6Ru6Dy01bp_j1fgJOMUbxAAJQAAP3AsgPBMOGfB7N13I2BA")
    await asyncio.sleep(4)
    await context.bot.delete_message(chat_id=chat_id, message_id=sticker_msg.message_id)

    # Charger les prédictions premium
    try:
        with open(PREMIUM_FILE, "r") as f:
            data = json.load(f)
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur de chargement du fichier de prédictions premium.\nDétail: {e}")
        return

    # Heure actuelle au Bénin
    now = datetime.now(pytz.timezone("Africa/Porto-Novo"))
    min_time = now + timedelta(minutes=3)
    max_time = now + timedelta(minutes=30)

    def parse_time(t):
        return datetime.strptime(t, "%H:%M").time()

    candidats = []
    for pred in data:
        try:
            heure_min = parse_time(pred["heure_min"])
            heure_min_full = now.replace(hour=heure_min.hour, minute=heure_min.minute, second=0, microsecond=0)
            if min_time <= heure_min_full <= max_time:
                candidats.append((heure_min_full, pred))
        except:
            continue

    if not candidats:
        prochaines = sorted([
            now.replace(hour=parse_time(p["heure_min"]).hour, minute=parse_time(p["heure_min"]).minute)
            for p in data
        ])
        for heure in prochaines:
            if heure > now:
                heure_txt = (heure - timedelta(minutes=5)).strftime("%H:%M")
                await update.message.reply_text(f"❌ Aucun signal PREMIUM disponible.\n\n📌 Prochaine prédiction à {heure_txt}")
                return
        await update.message.reply_text("📉 Aucune autre prédiction disponible pour le moment.")
        return

    # Prédiction la plus proche
    prediction = sorted(candidats)[0][1]

    # Format du message premium
    message = (
        "SJA7 LUCKYJET PREDICTOR\n"
        "┏━━━━━━━━━━━━━\n"
        f"┠ ◆ 𝐇𝐄𝐔𝐑𝐄 : {prediction['heure_min']} - {prediction['heure_max']} 🇧🇯\n"
        "┠\n"
        f"┠ ◆ 𝐂𝐎𝐄𝐅𝐅𝐈𝐂𝐈𝐄𝐍𝐓 : {prediction['coefficient']} 🎯\n"
        "┠\n"
        f"┠ ◆ 𝐀𝐒𝐒𝐔𝐑𝐀𝐍𝐂𝐄 : {prediction['assurance']} 🛡\n"
        "┗━━━━━━━━━━━━━\n\n"
        "S'INSCRIRE SUR 1WIN ICI...✍\n"
        "👉 [https://1wzitc.com/?p=a7j8](https://1wzitc.com/?p=a7j8)\n"
        "Code promo : SJA7"
    )

    # Décrémenter et informer
    decrementer_credit_premium(user_id)
    await update.message.reply_text(message, parse_mode="Markdown")

    restants = get_credit_premium(user_id)
    enregistrer_historique_global(user_id, "PREMIUM", {
    "heure_min": prediction["heure_min"],
    "heure_max": prediction["heure_max"],
    "coefficient": prediction["coefficient"],
    "assurance": prediction["assurance"]})
    await update.message.reply_text(f"🔔 Il vous reste {restants} prédiction(s) PREMIUM disponible(s).")

async def bouton_parrainage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Condition est dans la whitelist
    if not est_dans_whitelist(update.effective_user.id):
         await update.message.reply_text("❌ Tapez d'abord sur le bouton VÉRIFICATION.")
         return
    await update.message.reply_text(
        "🎁 INVITEZ DES AMIS POUR RECEVOIR DES RÉCOMPENSES !\n\n"
        "🔗 Canal Telegram : https://t.me/+VqK5KU0QE7ZjODg8\n"
        "🔗 Groupe WhatsApp : https://chat.whatsapp.com/LpXOPvR3oVZLj1lhfBz8bQ\n\n"
        "🎉 Plus vous invitez, plus vous êtes récompensé !"
    )

async def bouton_aide(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Condition est dans la whitelist
    if not est_dans_whitelist(update.effective_user.id):
         await update.message.reply_text("❌ Tapez d'abord sur le bouton VÉRIFICATION.")
         return

    await update.message.reply_text(
        "❓ BESOIN D'AIDE ?\n\n"
        "👉 Contacte @The_bigestt ou @SJA7_PCS sur Telegram."
)

#from flask import Flask
#from threading import Thread
#from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# === SERVEUR FLASK POUR REPLIT ===
#flask_app = Flask('')
#@flask_app.route('/')
#def home():
 #   return "Bot SJA7 en ligne !"

#def run():
 #   flask_app.run(host='0.0.0.0', port=8080)

#def keep_alive():
 #   t = Thread(target=run)
  #  t.start()

# === LANCEMENT DU BOT TELEGRAM ===
if __name__ == "__main__":
   # keep_alive()

    tg_app = ApplicationBuilder().token(BOT_TOKEN).build()

    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(CallbackQueryHandler(bouton_verification, pattern="^verifier$"))
    tg_app.add_handler(CommandHandler("valider", valider))
    tg_app.add_handler(CommandHandler("rejeter", rejeter))
    tg_app.add_handler(CommandHandler("bloquer", bloquer))
    tg_app.add_handler(CommandHandler("debloquer", debloquer))
    tg_app.add_handler(CommandHandler("whitelist", voir_whitelist))
    tg_app.add_handler(CommandHandler("credit", ajouter_credit_command))

    tg_app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^🔥 OBTENIR UNE PRÉDICTION$"), bouton_prediction_fun))
    tg_app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^🎲 SIGNAL PREMIUM$"), bouton_prediction_premium))
    tg_app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^👥 PARRAINAGE$"), bouton_parrainage))
    tg_app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^❓ AIDE$"), bouton_aide))

    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, recevoir_id))

    print("Bot en ligne...")
    tg_app.run_polling()





















