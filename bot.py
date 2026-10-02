import requests
import json
import time
import datetime
import os
from zoneinfo import ZoneInfo
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "-1003340688495")

if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN manquant dans les variables d'environnement.")

PARIS_TZ = ZoneInfo("Europe/Paris")

last_update_id = 0

user_state = {}


def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    try:
        response = requests.post(url, data=data, timeout=10)
        print(f"📤 Envoi message à {chat_id}: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur envoi: {e}")


def get_updates():
    global last_update_id
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    params = {"offset": last_update_id + 1, "timeout": 30}
    try:
        response = requests.get(url, params=params, timeout=35)
        try:
            updates = response.json()
        except Exception:
            print(f"❌ Réponse non-JSON de Telegram: {response.text[:300]}")
            return

        if updates.get("ok") and updates.get("result"):
            for update in updates["result"]:
                last_update_id = update["update_id"]
                if "message" in update:
                    process_message(update["message"])
                elif "callback_query" in update:
                    process_callback(update["callback_query"])
    except Exception as e:
        print(f"❌ Erreur get_updates: {e}")


def start_flow(chat_id, mode):
    user_state[chat_id] = {"mode": mode, "step": "sl"}
    send_message(chat_id, "💰 *Entrez le Stop Loss en $* (ex: 7):")


def build_signal_message(mode, sl_dollars, entry):
    now_paris = datetime.datetime.now(PARIS_TZ)
    date_str = now_paris.strftime("%d/%m/%Y")
    time_str = now_paris.strftime("%H:%M")

    entry_low = entry - 1
    entry_high = entry + 1

    if mode == "buy":
        sl_price = entry - sl_dollars
        tp1 = entry + sl_dollars * 1
        tp2 = entry + sl_dollars * 2
        tp3 = entry + sl_dollars * 3
        emoji = "🟢"
        label = "BUY SIGNAL"
    else:
        sl_price = entry + sl_dollars
        tp1 = entry - sl_dollars * 1
        tp2 = entry - sl_dollars * 2
        tp3 = entry - sl_dollars * 3
        emoji = "🔴"
        label = "SELL SIGNAL"

    message = (
        f"{emoji} *{label}* - XAUUSD\n\n"
        f"📅 *Date:* {date_str}\n"
        f"⏰ *Time:* {time_str}\n\n"
        f"📊 *Entry Zone:* {entry_low:.2f} - {entry_high:.2f}\n\n"
        f"🎯 *TP1 (RR 1):* {tp1:.2f}\n"
        f"🎯 *TP2 (RR 2):* {tp2:.2f}\n"
        f"🎯 *TP3 (RR 3):* {tp3:.2f}\n"
        f"🔄 *TP4 SWING*\n\n"
        f"🛑 *SL:* {sl_price:.2f} (-1R)\n\n"
        f"This trade is sent by ORYECHNIK STRATEGY 🚀"
    )
    return message


def process_message(message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    print(f"📩 Message reçu de {chat_id}: '{text}'")

    if text == "/start":
        keyboard = {
            "inline_keyboard": [
                [{"text": "🟢 BUY", "callback_data": "buy"}],
                [{"text": "🔴 SELL", "callback_data": "sell"}],
            ]
        }
        send_message(chat_id, "🤖 *XAUUSD Trading Bot*\nChoose an action:", keyboard)
        user_state.pop(chat_id, None)
        return

    if text in ["/buy", "/sell"]:
        mode = "buy" if text == "/buy" else "sell"
        start_flow(chat_id, mode)
        return

    state = user_state.get(chat_id)
    if not state:
        send_message(chat_id, "❌ Use /buy or /sell first.")
        return

    if state["step"] == "sl":
        try:
            sl_dollars = float(text.replace(",", "."))
            if sl_dollars <= 0:
                raise ValueError("SL doit être positif")
        except Exception:
            send_message(chat_id, "❌ *Stop Loss invalide.* Exemple: 7")
            return

        state["sl"] = sl_dollars
        state["step"] = "price"
        send_message(chat_id, "📊 *Entrez le prix d'entrée:*")
        return

    if state["step"] == "price":
        try:
            entry = float(text.replace(",", "."))
        except Exception:
            send_message(chat_id, "❌ *Prix d'entrée invalide.*")
            return

        mode = state["mode"]
        sl_dollars = state["sl"]
        user_state.pop(chat_id, None)

        signal_text = build_signal_message(mode, sl_dollars, entry)
        send_message(CHANNEL_ID, signal_text)
        send_message(chat_id, f"✅ *Signal {mode.upper()}* sent to channel!")
        return


def process_callback(callback):
    chat_id = callback["message"]["chat"]["id"]
    data = callback["data"]

    print(f"📩 Callback reçu de {chat_id}: {data}")

    if data in ["buy", "sell"]:
        start_flow(chat_id, data)

    answer_url = f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery"
    try:
        requests.post(answer_url, data={"callback_query_id": callback["id"]}, timeout=10)
    except Exception as e:
        print(f"❌ Erreur callback: {e}")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()


def run_http():
    HTTPServer(("0.0.0.0", 10000), Handler).serve_forever()


Thread(target=run_http, daemon=True).start()

print("🤖 XAUUSD Bot - Étape 1 : nouveau format de message")
print("✅ Bot démarré. En attente des messages...")

while True:
    try:
        get_updates()
        time.sleep(1)
    except Exception as e:
        print(f"❌ Erreur boucle principale: {e}")
        time.sleep(5)
