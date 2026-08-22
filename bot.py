import requests
import json
import time
import datetime
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

TOKEN = "8520274534:AAFRoKXGKtsM9BXk4sHPjdkDRGJ8nW60LX4"
CHANNEL_ID = "-1003340688495"

last_update_id = 0
user_mode = {}

def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    try:
        response = requests.post(url, data=data)
        print(f"📤 Envoi message à {chat_id}: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur envoi: {e}")

def get_updates():
    global last_update_id
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    params = {"offset": last_update_id + 1, "timeout": 30}
    try:
        print("📥 Checking updates...")
        response = requests.get(url, params=params)
        print(f"📥 Réponse API: {response.status_code}")
        updates = response.json()
        
        # Affiche les 500 premiers caractères pour debug
        print(f"📥 Données reçues: {str(updates)[:500]}")
        
        if updates.get("ok") and updates.get("result"):
            for update in updates["result"]:
                last_update_id = update["update_id"]
                if "message" in update:
                    process_message(update["message"])
                elif "callback_query" in update:
                    process_callback(update["callback_query"])
    except Exception as e:
        print(f"❌ Erreur get_updates: {e}")

def process_message(message):
    global user_mode
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    
    print(f"📩 Message reçu de {chat_id}: '{text}'")
    
    # Test simple : répondre à tout message pour vérifier que le bot fonctionne
    # send_message(chat_id, f"✅ Message reçu: {text}")
    # return

    if text == "/start":
        keyboard = {
            "inline_keyboard": [
                [{"text": "🟢 BUY", "callback_data": "buy"}],
                [{"text": "🔴 SELL", "callback_data": "sell"}]
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

    if chat_id not in user_mode:
        send_message(chat_id, "❌ Use /buy or /sell first.")
        return

    try:
        prix = float(text.replace(",", "."))
        mode = user_mode.pop(chat_id)

        now = datetime.datetime.now()
        date_str = now.strftime("%d/%m/%Y")
        time_str = now.strftime("%H:%M")

        entry_low = prix - 2
        entry_high = prix + 3

        if mode == "buy":
            message_signal = (
                f"🟢 *BUY SIGNAL* - XAUUSD\n\n"
                f"📅 *Date:* {date_str}\n"
                f"⏰ *Time:* {time_str}\n\n"
                f"📊 *Entry Zone:* {entry_low:.2f} - {entry_high:.2f}\n"
                f"📈 *Time Frame:* 10min\n\n"
                f"🎯 *TP1:* {prix+20:.2f}\n"
                f"🎯 *TP2:* {prix+30:.2f}\n"
                f"🎯 *TP3:* {prix+40:.2f}\n"
                f"🔄 *Swing:* Small lot after TP3\n\n"
                f"🛑 *SL:* {prix-20:.2f}\n\n"
                f"#XAUUSD #Trading"
            )
        else:
            message_signal = (
                f"🔴 *SELL SIGNAL* - XAUUSD\n\n"
                f"📅 *Date:* {date_str}\n"
                f"⏰ *Time:* {time_str}\n\n"
                f"📊 *Entry Zone:* {entry_low:.2f} - {entry_high:.2f}\n"
                f"📈 *Time Frame:* 10min\n\n"
                f"🎯 *TP1:* {prix-20:.2f}\n"
                f"🎯 *TP2:* {prix-30:.2f}\n"
                f"🎯 *TP3:* {prix-40:.2f}\n"
                f"🔄 *Swing:* Small lot after TP3\n\n"
                f"🛑 *SL:* {prix+20:.2f}\n\n"
                f"#XAUUSD #Trading"
            )

        send_message(CHANNEL_ID, message_signal)
        send_message(chat_id, f"✅ *Signal {mode.upper()}* sent to channel!")

    except Exception as e:
        print(f"❌ Erreur traitement prix: {e}")
        send_message(chat_id, "❌ *Invalid price.*")

def process_callback(callback):
    chat_id = callback["message"]["chat"]["id"]
    data = callback["data"]
    
    print(f"📩 Callback reçu de {chat_id}: {data}")

    if data == "buy":
        user_mode[chat_id] = "buy"
        send_message(chat_id, "💰 Enter BUY price:")
    elif data == "sell":
        user_mode[chat_id] = "sell"
        send_message(chat_id, "💰 Enter SELL price:")

    answer_url = f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery"
    try:
        requests.post(answer_url, data={"callback_query_id": callback["id"]})
    except Exception as e:
        print(f"❌ Erreur callback: {e}")

# === FAUX SERVEUR HTTP POUR RENDER (avec HEAD supporté) ===
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()
# ==========================================================

def run_http():
    HTTPServer(("0.0.0.0", 10000), Handler).serve_forever()

Thread(target=run_http, daemon=True).start()

print("🤖 XAUUSD Bot - TP/SL 20/20/30/40 + Swing + Entry Zone + 10min + HEAD support")
print("✅ Bot démarré. En attente des messages...")

while True:
    try:
        get_updates()
        time.sleep(1)
    except Exception as e:
        print(f"❌ Erreur boucle principale: {e}")
        time.sleep(5)
