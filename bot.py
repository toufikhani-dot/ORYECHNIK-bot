import requests
import json
import time

TOKEN = "8520274534:AAG0bctoo3jUYw2mJjYE3Intu8M36KtTVKU"
CHANNEL_ID = "-1003340688495"

last_update_id = 0
trade_counter = 0

def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
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
    global trade_counter
    if "message" not in update:
        return
    
    message = update["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    
    if text == "/start":
        keyboard = {
            "inline_keyboard": [
                [{"text": "🟢 BUY", "callback_data": "buy"}],
                [{"text": "🔴 SELL", "callback_data": "sell"}],
                [{"text": "❌ CANCEL", "callback_data": "cancel"}],
                [{"text": "🆘 SUPPORT", "callback_data": "support"}]
            ]
        }
        send_message(chat_id, "🤖 *XAUUSD Trading Bot*\nWelcome! Choose an action below:", keyboard)
    
    elif text.startswith("/"):
        pass
    
    else:
        try:
            prix = float(text.replace(",", "."))
            trade_counter += 1
            ref = f"XAU-{trade_counter:03d}"
            
            message_signal = f"🟢 *BUY SIGNAL* - XAUUSD\n\n📊 *Ref:* {ref}\n💰 *Entry:* {prix:.2f}\n🎯 *TP1:* {prix+6:.2f}\n🎯 *TP2:* {prix+10:.2f}\n🎯 *TP3:* {prix+18:.2f}\n🛑 *SL:* {prix-10:.2f}\n\n#XAUUSD #Trading"
            
            send_message(CHANNEL_ID, message_signal)
            send_message(chat_id, f"✅ *Signal {ref}* sent to channel!")
        except:
            send_message(chat_id, "❌ *Invalid price.*\nPlease enter a number (ex: 4200.00)")

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
                        send_message(chat_id, "💰 *Enter BUY price* (ex: 4200.00):")
                    elif action == "sell":
                        send_message(chat_id, "💰 *Enter SELL price* (ex: 4200.00):")
                    elif action == "cancel":
                        send_message(chat_id, "❌ *Action cancelled.* Type /start to restart.")
                    elif action == "support":
                        support_message = (
                            "📩 *SUPPORT REQUEST*\n\n"
                            "For any specific question, partnership, or assistance regarding signals:\n\n"
                            "👉 *Contact:* @Raymond151033\n\n"
                            "📌 *Please include:*\n"
                            "• Trade reference (if applicable)\n"
                            "• Date and time\n"
                            "• Clear description of your request\n\n"
                            "Thank you for using *TRaymonding Trading Bot*.\n"
                            "We will respond as soon as possible."
                        )
                        send_message(chat_id, support_message)
                    
                    answer_url = f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery"
                    requests.post(answer_url, data={"callback_query_id": callback["id"]})
    except:
        pass

print("🤖 XAUUSD Trading Bot started! Go to @ORYECHNIK_bot and type /start")

while True:
    try:
        get_updates()
        handle_callback()
        time.sleep(1)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
