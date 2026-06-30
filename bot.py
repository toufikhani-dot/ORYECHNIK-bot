import requests
import json
import time
import datetime
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

TOKEN = "8520274534:AAEQlC31qLlWKubwbleMCCV_x8Va2OmdeRM"
CHANNEL_ID = "-1003340688495"

last_update_id = 0
trade_counter = 0
user_mode = {}

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
                if "message" in update:
                    process_message(update["message"])
                elif "callback_query" in update:
                    process_callback(update["callback_query"])
    except:
        pass

def process_message(message):
    global trade_counter, user_mode
    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    if text == "/start":
        keyboard = {
            "inline_keyboard": [
                [{"text": "🟢 BUY", "callback_data": "buy"}],
                [{"text": "🔴 SELL", "callback_data": "sell"}],
                [{"text": "🆘 SUPPORT", "callback_data": "support"}]
            ]
        }
        send_message(chat_id, "🤖 *XAUUSD Trading Bot*\nChoose an action:", keyboard)
        user_mode.pop(chat_id, None)
        return

    if text in ["/buy", "/sell"]:
        mode = "buy" if text == "/buy" else "sell"
        user_mode[chat_id] = mode
        send_message(chat_id, f"💰 *Enter {mode.upper()} price* (ex: 4200.00):")
        return

    if text == "/support":
        send_message(chat_id, "📩 Contact support: @Raymond151033")
        return

    if chat_id not in user_mode:
        send_message(chat_id, "❌ Use /buy or /sell first.")
        return

    try:
        prix = float(text.replace(",", "."))
        mode = user_mode.pop(chat_id)
        trade_counter += 1

        now = datetime.datetime.now()
        date_str = now.strftime("%d/%m/%Y")
        time_str = now.strftime("%H:%M")

        if mode == "buy":
            message_signal = (
                f"🟢 *BUY SIGNAL* - XAUUSD\n\n"
                f"📅 *Date:* {date_str}\n"
                f"⏰ *Time:* {time_str}\n\n"
                f"💰 *Entry:* {prix:.2f}\n\n"
                f"🎯 *TP1:* {prix+6:.2f}\n"
                f"🎯 *TP2:* {prix+10:.2f}\n"
                f"🎯 *TP3:* {prix+18:.2f}\n\n"
                f"🛑 *SL:* {prix-10:.2f}\n\n"
                f"#XAUUSD #Trading"
            )
        else:
            message_signal = (
                f"🔴 *SELL SIGNAL* - XAUUSD\n\n"
                f"📅 *Date:* {date_str}\n"
                f"⏰ *Time:* {time_str}\n\n"
                f"💰 *Entry:* {prix:.2f}\n\n"
                f"🎯 *TP1:* {prix-6:.2f}\n"
                f"🎯 *TP2:* {prix-10:.2f}\n"
                f"🎯 *TP3:* {prix-18:.2f}\n\n"
                f"🛑 *SL:* {prix+10:.2f}\n\n"
                f"#XAUUSD #Trading"
            )

        send_message(CHANNEL_ID, message_signal)
        send_message(chat_id, f"✅ *Signal {mode.upper()}* sent to channel!")

    except:
        send_message(chat_id, "❌ *Invalid price.*")

def process_callback(callback):
    chat_id = callback["message"]["chat"]["id"]
    data = callback["data"]

    if data == "buy":
        user_mode[chat_id] = "buy"
        send_message(chat_id, "💰 Enter BUY price:")
    elif data == "sell":
        user_mode[chat_id] = "sell"
        send_message(chat_id, "💰 Enter SELL price:")
    elif data == "support":
        send_message(chat_id, "📩 Contact support: @Raymond151033")

    answer_url = f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery"
    requests.post(answer_url, data={"callback_query_id": callback["id"]})

# === FAUX SERVEUR HTTP POUR RENDER ===
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_http():
    HTTPServer(("0.0.0.0", 10000), Handler).serve_forever()

Thread(target=run_http, daemon=True).start()
# ====================================

print("🤖 XAUUSD Bot - Date/Time added, Ref removed")

while True:
    try:
        get_updates()
        time.sleep(1)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
