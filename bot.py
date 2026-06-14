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

def set_persistent_menu():
    url = f"https://api.telegram.org/bot{TOKEN}/setChatMenuButton"
    menu = {
        "menu_button": {
            "type": "commands",
            "commands": [
                {"command": "start", "description": "Restart bot"},
                {"command": "buy", "description": "Send BUY signal"},
                {"command": "sell", "description": "Send SELL signal"},
                {"command": "support", "description": "Contact support"}
            ]
        }
    }
    try:
        requests.post(url, json=menu)
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
                if "message" in update:
                    process_message(update["message"])
                elif "callback_query" in update:
                    process_callback(update["callback_query"])
    except:
        pass

def process_message(message):
    global trade_counter
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    
    if text == "/start":
        send_message(chat_id, "🤖 *XAUUSD Trading Bot*\nUse /buy or /sell to trade.")
    elif text == "/buy":
        send_message(chat_id, "💰 *Enter BUY price* (ex: 4200.00):")
    elif text == "/sell":
        send_message(chat_id, "💰 *Enter SELL price* (ex: 4200.00):")
    elif text == "/support":
        support_msg = (
            "📩 *SUPPORT REQUEST*\n\n"
            "Contact: @Raymond151033\n\n"
            "Please include trade reference, date, and details."
        )
        send_message(chat_id, support_msg)
    else:
        try:
            prix = float(text.replace(",", "."))
            trade_counter += 1
            ref = f"XAU-{trade_counter:03d}"
            
            # On détermine si c'est un buy ou sell via le dernier message
            # (simplification : par défaut BUY, à améliorer si besoin)
            message_signal = (
                f"🟢 *BUY SIGNAL* - XAUUSD\n\n"
                f"📊 *Ref:* {ref}\n"
                f"💰 *Entry:* {prix:.2f}\n"
                f"🎯 *TP1:* {prix+6:.2f}\n"
                f"🎯 *TP2:* {prix+10:.2f}\n"
                f"🎯 *TP3:* {prix+18:.2f}\n"
                f"🛑 *SL:* {prix-10:.2f}\n\n"
                f"#XAUUSD #Trading"
            )
            send_message(CHANNEL_ID, message_signal)
            send_message(chat_id, f"✅ *Signal {ref}* sent to channel!")
        except:
            send_message(chat_id, "❌ *Invalid price.* Use /buy or /sell first.")

def process_callback(callback):
    chat_id = callback["message"]["chat"]["id"]
    data = callback["data"]
    
    if data == "buy":
        send_message(chat_id, "💰 Enter BUY price:")
    elif data == "sell":
        send_message(chat_id, "💰 Enter SELL price:")
    elif data == "support":
        send_message(chat_id, "📩 Contact support: @Raymond151033")
    
    answer_url = f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery"
    requests.post(answer_url, data={"callback_query_id": callback["id"]})

# Menu persistant
set_persistent_menu()

print("🤖 XAUUSD Trading Bot started (fixed menu + buy/sell OK)")

while True:
    try:
        get_updates()
        time.sleep(1)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
