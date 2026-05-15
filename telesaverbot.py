import telebot
import yt_dlp
import os
from telebot import types
import os
from threading import Thread
from flask import Flask

app = Flask('')

@app.route('/')
def home():
    return "Bot ishlanyapti!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

# Botni ishga tushirishdan oldin serverni yoqamiz
keep_alive()


TOKEN = "8619930243:AAFZ-aa1R071xWnSa_TViBEp8c0l3nYmxgs"

bot = telebot.TeleBot(TOKEN)

DOWNLOAD_PATH = "downloads"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

user_state = {}

# ==================== TIMEOUT VA TEZKOR SOZLAMALAR ====================
def get_ydl_opts():
    return {
        'format': 'best[height<=480]/best',     # Pastroq sifat (tezroq yuklanadi)
        'outtmpl': f'{DOWNLOAD_PATH}/%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 30,          # Timeoutni oshirish
        'retries': 5,                  # Qayta urinish
        'fragment_retries': 5,
        'http_chunk_size': 1048576,    # 1MB chunk
    }

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📸 Instagram", "🎵 TikTok", "▶️ YouTube", "📘 Facebook", "🌐 Boshqa")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 
        "👋 Salom!\n\nPlatformani tanlang va link yuboring:", 
        reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text in ["📸 Instagram","🎵 TikTok","▶️ YouTube","📘 Facebook","🌐 Boshqa"])
def choose_platform(message):
    user_id = message.chat.id
    if "Instagram" in message.text: user_state[user_id] = "instagram"
    elif "TikTok" in message.text: user_state[user_id] = "tiktok"
    elif "YouTube" in message.text: user_state[user_id] = "youtube"
    elif "Facebook" in message.text: user_state[user_id] = "facebook"
    else: user_state[user_id] = "other"
    
    bot.send_message(user_id, f"✅ {message.text} tanlandi!\nEndi link yuboring:", 
                     reply_markup=main_menu())

# ==================== ASOSIY YUKLASH ====================
@bot.message_handler(func=lambda message: True)
def handle_link(message):
    user_id = message.chat.id
    url = message.text.strip()

    if user_id not in user_state:
        bot.send_message(user_id, "❌ Avval tugmalardan birini bosing!", reply_markup=main_menu())
        return

    if not url.startswith("http"):
        bot.reply_to(message, "❌ To'g'ri link yuboring.")
        return

    status_msg = bot.reply_to(message, "⏳ Yuklab olinmoqda... (Bu safar tezroq bo'lishi kerak)")

    try:
        with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if os.path.exists(filename):
            file_size_mb = round(os.path.getsize(filename) / (1024*1024), 1)
            
            bot.send_chat_action(user_id, 'upload_video')
            
            with open(filename, 'rb') as video:
                bot.send_video(
                    user_id, 
                    video,
                    caption=f"✅ Yuklab olindi!\n\n📌 {info.get('title', 'Video')}\n📏 {file_size_mb} MB",
                    reply_to_message_id=message.message_id
                )
            os.remove(filename)
        else:
            bot.edit_message_text("❌ Video topilmadi.", status_msg.chat.id, status_msg.message_id)

    except Exception as e:
        error = str(e)
        print(error)
        if "timeout" in error.lower() or "connection" in error.lower():
            bot.edit_message_text("❌ Internet sekin. Keyinroq urinib ko'ring yoki Wi-Fi ga ulaning.", 
                                status_msg.chat.id, status_msg.message_id)
        else:
            bot.edit_message_text(f"❌ Xatolik:\n{error[:250]}", 
                                status_msg.chat.id, status_msg.message_id)

if __name__ == "__main__":
    print("🤖 Bot yangilandi (Timeout tuzatilgan)")
    bot.infinity_polling()
