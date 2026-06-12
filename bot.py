from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = "8520274534:AAG0bctoo3jUYw2mJjYE3Intu8M36KtTVKU"
CHANNEL_ID = -1003340688495

user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🟢 BUY", callback_data="buy")],
        [InlineKeyboardButton("🔴 SELL", callback_data="sell")],
        [InlineKeyboardButton("❌ CANCEL", callback_data="cancel")]
    ]
    await update.message.reply_text("🤖 Bot de trading XAUUSD\nChoisissez :", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == "buy":
        user_states[user_id] = {"action": "buy"}
        await query.edit_message_text("💰 Entrez le prix (ex: 4206.56) :")
    elif query.data == "sell":
        user_states[user_id] = {"action": "sell"}
        await query.edit_message_text("💰 Entrez le prix (ex: 4206.56) :")
    elif query.data == "cancel":
        user_states.pop(user_id, None)
        await query.edit_message_text("❌ Annulé. Tapez /start")

async def handle_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in user_states:
        await update.message.reply_text("❌ Tapez /start d'abord")
        return
    
    try:
        prix = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text("❌ Prix invalide")
        return
    
    action = user_states[user_id]["action"]
    
    if action == "buy":
        tp1, tp2, tp3 = prix + 6, prix + 10, prix + 18
        sl = prix - 10
        emoji, texte = "🟢", "BUY"
    else:
        tp1, tp2, tp3 = prix - 6, prix - 10, prix - 18
        sl = prix + 10
        emoji, texte = "🔴", "SELL"
    
    message = f"{emoji} SIGNAL {texte} - XAUUSD\n\n💰 Prix : {prix:.2f}\n\n🎯 TP1 : {tp1:.2f}\n🎯 TP2 : {tp2:.2f}\n🎯 TP3 : {tp3:.2f}\n\n🛑 SL : {sl:.2f}\n\n#XAUUSD"
    
    try:
        await context.bot.send_message(chat_id=CHANNEL_ID, text=message)
        await update.message.reply_text("✅ Signal envoyé !")
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur : {e}")
    
    user_states.pop(user_id, None)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_price))
    print("✅ Bot démarré !")
    app.run_polling()

if __name__ == "__main__":
    main()
