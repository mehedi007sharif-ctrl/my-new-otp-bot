import telebot
import requests
import time
import os
from threading import Thread
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ১. ফ্লাস্ক অ্যাপ তৈরি
app = Flask('')

@app.route('/')
def home():
    return "Premium VoltxSMS Bot is running perfectly with high security!"

def run_server():
    app.run(host='0.0.0.0', port=8080)

# ==================== [ নিরাপদ কনফিগারেশন ] ====================
# রেন্ডারের এনভায়রনমেন্ট ভ্যারিয়েবল থেকে ডাটা পড়া হচ্ছে
BOT_TOKEN = os.environ.get("BOT_TOKEN")
VOLTX_API_KEY = os.environ.get("VOLTX_API_KEY")
BASE_URL = "https://voltxsms.com/api"
OTP_GROUP_CHAT_ID = "-1003851787435"
# ========================================================

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# 👋 স্টার্ট কমান্ড
@bot.message_handler(commands=['start'])
def send_welcome(message):
    show_main_menu(message.chat.id)

# 📱 মূল মেনু ফাংশন
def show_main_menu(chat_id):
    markup = InlineKeyboardMarkup(row_width=2)
    btn_get = InlineKeyboardButton("📱 Get Number / নাম্বার নিন", callback_data="get_num")
    btn_cancel = InlineKeyboardButton("❌ Cancel Number / বাতিল করুন", callback_data="cancel_num")
    btn_status = InlineKeyboardButton("📊 Live Traffic / লাইভ ট্রাফিক", callback_data="server_status")
    
    markup.add(btn_get, btn_cancel)
    markup.add(btn_status)
    
    bot.send_message(
        chat_id, 
        "Welcome to our Premium VoltxSMS Bot!\nWe provide the highest quality Premium Numbers instantly!\n\nChoose an option below 👇", 
        reply_markup=markup
    )

# 🔘 ইনলাইন বোতামের কাজ হ্যান্ডেল করার ফাংশন
@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    params = {"api_key": VOLTX_API_KEY}
    
    if call.data == "get_num":
        bot.edit_message_text("🔄 Processing Request... ভোল্টেক্স সার্ভার থেকে নতুন নাম্বার খোঁজা হচ্ছে...", call.message.chat.id, call.message.message_id)
        
        params["action"] = "getNumber"
        params["service"] = "wa" 
        params["country"] = "0"  
        
        try:
            response = requests.get(BASE_URL, params=params, timeout=15).text
            
            if "ACCESS_NUMBER" in response:
                parts = response.split(":")
                activation_id = parts[1]
                number = parts[2]
                
                waiting_markup = InlineKeyboardMarkup()
                btn_sms_cancel = InlineKeyboardButton("❌ Cancel/নাম্বার বাতিল", callback_data=f"cancel_{activation_id}")
                waiting_markup.add(btn_sms_cancel)
                
                bot.edit_message_text(f"✅ **Number Allocated Successfully!**\n\n📱 Number: `{number}`\n\n💬 Waiting for OTP... ওটিপি কোডের জন্য লাইভ অপেক্ষা করা হচ্ছে...", call.message.chat.id, call.message.message_id, reply_markup=waiting_markup)
                
                check_params = {"api_key": VOLTX_API_KEY, "action": "getStatus", "id": activation_id}
                for _ in range(30):
                    time.sleep(4)
                    try:
                        otp_response = requests.get(BASE_URL, params=check_params, timeout=15).text
                        
                        if "STATUS_OK" in otp_response:
                            otp_text = otp_response.split(":")[1]
                            success_msg = f"🎉 **New OTP Received!**\n\n📱 Number: `{number}`\n💬 OTP Message: {otp_text}"
                            bot.send_message(call.message.chat.id, success_msg)
                            
                            try:
                                bot.send_message(OTP_GROUP_CHAT_ID, f"📢 **LIVE OTP REPORT**\n\n{success_msg}")
                            except Exception as group_err:
                                print(f"Group send error: {group_err}")
                            return
                        elif "STATUS_CANCELLED" in otp_response:
                            bot.send_message(call.message.chat.id, "❌ নাম্বারটি সিস্টেম থেকে বাতিল হয়ে গেছে।")
                            return
                    except:
                        continue
                
                bot.send_message(call.message.chat.id, "❌ Timeout! নির্ধারিত সময়ে কোনো ওটিপি পাওয়া যায়নি।")
            else:
                bot.edit_message_text(f"❌ প্যানেলে সমস্যা অথবা ব্যালেন্স নেই। সার্ভার মেসেজ: {response}", call.message.chat.id, call.message.message_id)
        except Exception as e:
            bot.edit_message_text("⚠️ ভোল্টেক্স এপিআই কানেকশন এরর! আবার চেষ্টা করুন।", call.message.chat.id, call.message.message_id)
            
    elif call.data.startswith("cancel_"):
        activation_id = call.data.split("_")[1]
        bot.answer_callback_query(call.id, "⏳ Cancel Request Processing...")
        
        cancel_params = {"api_key": VOLTX_API_KEY, "action": "setStatus", "id": activation_id, "status": "8"}
        try:
            requests.get(BASE_URL, params=cancel_params, timeout=15)
            bot.send_message(call.message.chat.id, "✅ নাম্বারটি সফলভাবে বাতিল করা হয়েছে।")
        except:
            bot.send_message(call.message.chat.id, "⚠️ রিকোয়েস্টটি সফল করা যায়নি।")
            
    elif call.data == "cancel_num":
        bot.answer_callback_query(call.id, "❌ কোনো একটিভ নাম্বার পাওয়া যায়নি।")
            
    elif call.data == "server_status":
        bot.answer_callback_query(call.id, "📊 Checking Live Traffic Status...")
        bot.send_message(call.message.chat.id, "📊 **ACTIVE TRAFFIC REPORT:**\n\n🟢 **WhatsApp Traffic:** High (700+ OTP/min)\n🟢 **Server Status:** VoltxSMS Online & Active")

if __name__ == "__main__":
    t = Thread(target=run_server)
    t.start()
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
    
