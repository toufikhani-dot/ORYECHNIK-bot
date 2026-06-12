import requests
import json
import time

TOKEN = "8520274534:AAG0bctoo3jUYw2mJjYE3Intu8M36KtTVKU"
CHANNEL_ID = "-1003340688495"

last_update_id = 0

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, data=data)
    except:
        pass

def get_updates():
    global last_update_id
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    params = {"offset": last_update_id + 1, "timeout": 30}
    try:
        response = requests.get(url, params=params)
        updates = response.json()
        if updates.get("ok") and updates.get("result"):
            for update in updates["result"]:
                last_update_id = update["update_id"]
                process_update(update)
    except:
        pass

def process_update(update):
    if "message" not in update:
        return
    
    message = update["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    
    if text == "/start":
        keyboard = {
            "inline_keyboard": [
                [{"text": "🟢 BUY", "callback_data": "buy"}],
                [{"text": "🔴 SELL", "callback_data": "sell"}]
            ]
        }
        reply_markup = json.dumps(keyboard)
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": "🤖 Bot Trading XAUUSD\nChoisissez BUY ou SELL :", "reply_markup": reply_markup}
        requests.post(url, data=data)
    
    elif text.startswith("/"):
        pass
    
    else:
        try:
            prix = float(text.replace(",", "."))
            message_signal = f"🟢 SIGNAL BUY - XAUUSD\n\n💰 Prix: {prix:.2f}\n🎯 TP1: {prix+6:.2f}\n🎯 TP2: {prix+10:.2f}\n🎯 TP3: {prix+18:.2f}\n🛑 SL: {prix-10:.2f}\n\n#XAUUSD"
            send_message(CHANNEL_ID, message_signal)
            send_message(chat_id, "✅ Signal BUY envoyé!")
        except:
            send_message(chat_id, "❌ Prix invalide")

def handle_callback():
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    try:
        response = requests.get(url)
        updates = response.json()
        if updates.get("ok") and updates.get("result"):
            for update in updates["result"]:
                if "callback_query" in update:
                    callback = update["callback_query"]
                    action = callback["data"]
                    chat_id = callback["message"]["chat"]["id"]
                    
                    if action == "buy":
                        send_message(chat_id, "💰 Entrez le prix pour BUY (ex: 4200):")
                    elif action == "sell":
                        send_message(chat_id, "💰 Entrez le prix pour SELL (ex: 4200):")
                    
                    answer_url = f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery"
                    requests.post(answer_url, data={"callback_query_id": callback["id"]})
                    
                    # Supprimer le callback pour ne pas le traiter plusieurs fois
                    delete_url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
                    requests.get(delete_url, params={"offset": callback["update_id"] + 1})
    except:
        pass

print("🤖 Bot Trading démarré! Va sur @ORYECHNIK_bot et tape /start")

while True:
    try:
        get_updates()
        handle_callback()
        time.sleep(1)
    except Exception as e:
        print(f"Erreur: {e}")
        time.sleep(5)
