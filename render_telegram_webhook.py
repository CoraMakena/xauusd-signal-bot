from flask import Flask, request, jsonify
import requests
import logging
from datetime import datetime
import os

# --- Konfiguration ---
# Hole Token und Chat ID aus Umgebungsvariablen (für Sicherheit auf Render.com)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "DEIN_TOKEN_HIER")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "DEINE_CHAT_ID_HIER")
WEBHOOK_PASSPHRASE = os.environ.get("WEBHOOK_PASSPHRASE", "TelegramBot2026")

# Logging einrichten
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)

def send_telegram_message(message):
    """Sendet die formatierte Nachricht an Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            logging.info("Telegram Nachricht erfolgreich gesendet")
            return True
        else:
            logging.error(f"Fehler beim Senden der Telegram Nachricht: {response.text}")
            return False
    except Exception as e:
        logging.error(f"Exception beim Senden der Telegram Nachricht: {str(e)}")
        return False

@app.route('/webhook', methods=['POST'])
def webhook():
    """Empfängt die Alerts von TradingView"""
    try:
        # JSON Daten aus dem Request holen
        data = request.json
        
        # Sicherheitsprüfung
        if data.get('passphrase') != WEBHOOK_PASSPHRASE:
            logging.warning("Unautorisierter Webhook-Zugriff (Falsches Passwort)")
            return jsonify({"status": "error", "message": "Unauthorized"}), 401
            
        # Daten extrahieren
        action = data.get('action')
        symbol = data.get('symbol')
        timeframe = data.get('timeframe')
        entry = float(data.get('entry', 0))
        sl = float(data.get('sl', 0))
        tp1 = float(data.get('tp1', 0))
        tp2 = float(data.get('tp2', 0))
        tp3 = float(data.get('tp3', 0))
        
        logging.info(f"Webhook empfangen: {action} {symbol}")
        
        # Icon bestimmen
        icon = "🟢" if action == "LONG" else "🔴"
        
        # Aktuelle Zeit
        current_time = datetime.utcnow().strftime("%H:%00 UTC")
        
        # Nachricht formatieren
        message = f"""
{icon} <b>{symbol} {action} SIGNAL</b>
━━━━━━━━━━━━━━━━
📍 <b>Einstieg:</b>    {entry:.2f}

🎯 <b>TP 1:</b>        {tp1:.2f}
🎯 <b>TP 2:</b>        {tp2:.2f}
🎯 <b>TP 3:</b>        {tp3:.2f}

🛑 <b>Stop Loss:</b>   {sl:.2f}
━━━━━━━━━━━━━━━━
📊 Zeitrahmen:  {timeframe}
⚡ Strategie:   BB Breakout
🕐 Zeit:        {current_time}
"""
        
        # An Telegram senden
        success = send_telegram_message(message)
        
        if success:
            return jsonify({"status": "success", "message": "Telegram message sent"}), 200
        else:
            return jsonify({"status": "error", "message": "Failed to send Telegram message"}), 500
            
    except Exception as e:
        logging.error(f"Webhook Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/', methods=['GET'])
def health_check():
    """Einfacher Health Check für Render.com"""
    return "TradingView to Telegram Webhook is running!", 200

if __name__ == '__main__':
    # Render.com vergibt den Port dynamisch über die PORT Umgebungsvariable
    port = int(os.environ.get("PORT", 10000))
    logging.info(f"Starte TradingView -> Telegram Webhook Server auf Port {port}...")
    app.run(host='0.0.0.0', port=port)
