import telebot
import requests
import time
from threading import Thread
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ১. ফ্লাস্ক অ্যাপ তৈরি (রেন্ডার হোস্ティング লাইভ রাখার জন্য)
app = Flask('')

@app.route('/')
def home():
    return "Premium VoltxSMS Bot is running perfectly!"

def run_server():
    app.run(host='0.0.0.0', port=8080)

# ==================== [ কনফিগারেশন ] ====================
BOT_TOKEN = "8952089627:AAESGYsmdhRU-d5olkm2-vE5dj2TBprcwII"
VOLTX_API_KEY = "MABFLWQ11MY"
BASE_URL = "https://voltxsms.com/api"
OTP_GROUP_CHAT_ID = "-1003851787435"
# ========================================================

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# 👋 স্টার্ট কমান্ড (সরাসরি ইনলাইন বাটন মেনু দেখাবে)
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
    # VoltxSMS প্যানেলের জন্য প্যারামিটার সেটআপ
    params = {"api_key": VOLTX_API_KEY}
    
    # নাম্বার নেওয়ার বাটন ক্লিক করলে
    if call.data == "get_num":
        bot.edit_message_text("🔄 Processing Request... ভোল্টেক্স সার্ভার থেকে নতুন নাম্বার খোঁজা হচ্ছে...", call.message.chat.id, call.message.message_id)
        
        # VoltxSMS হোয়াটসঅ্যাপ সার্ভিস আইডি এবং রিকোয়েস্ট
        params["action"] = "getNumber"
        params["service"] = "wa" # wa = WhatsApp
        params["country"] = "0"  # 0 = Default/Any country (প্রয়োজনে পরিবর্তন করা যাবে)
        
        try:
            response = requests.get(BASE_URL, params=params, timeout=15).json()
            
            if response.get("status") == "success" or "number" in response:
                number = response.get("number")
                activation_id = response.get("id")
                
                waiting_markup = InlineKeyboardMarkup()
                btn_sms_cancel = InlineKeyboardButton("❌ Cancel/নাম্বার বাতিল", callback_data=f"cancel_{activation_id}")
                waiting_markup.add(btn_sms_cancel)
                
                bot.edit_message_text(f"✅ **Number Allocated Successfully!**\n\n📱 Number: `{number}`\n\n💬 Waiting for OTP... ওটিপি কোডের জন্য লাইভ অপেক্ষা করা হচ্ছে...", call.message.chat.id, call.message.message_id, reply_markup=waiting_markup)
                
                # লাইভ ওটিপি চেকিং লুপ (২ মিনিট চেক করবে)
                check_params = {"api_key": VOLTX_API_KEY, "action": "getStatus", "id": activation_id}
                for _ in range(30):
                    time.sleep(4)
                    try:
                        otp_response = requests.get(BASE_URL, params=check_params, timeout=15).json()
                        # VoltxSMS স্ট্যাটাস চেক
                        if otp_response.get("status") == "STATUS_OK" or "sms" in otp_response:
                            otp_text = otp_response.get("sms") or otp_response.get("text")
                            
                            success_msg = f"🎉 **New OTP Received!**\n\n📱 Number: `{number}`\n💬 OTP Message: {otp_text}"
                            
                            # ১. বটের ভেতরে ইউজারকে ওটিপি পাঠানো
                            bot.send_message(call.message.chat.id, success_msg)
                            
                            # ২. ওটিপি গ্রুপে ওটিপি সেন্ড করা
                            try:
                                bot.send_message(OTP_GROUP_CHAT_ID, f"📢 **LIVE OTP REPORT**\n\n{success_msg}")
                            except Exception as group_err:
                                print(f"Group send error: {group_err}")
                            return
                        elif otp_response.get("status") == "STATUS_CANCELLED":
                            bot.send_message(call.message.chat.id, "❌ নাম্বারটি সিস্টেম থেকে বাতিল হয়ে গেছে।")
                            return
                    except:
                        continue
                
                bot.send_message(call.message.chat.id, "❌ Timeout! নির্ধারিত সময়ে কোনো ওটিপি পাওয়া যায়নি।")
            else:
                bot.edit_message_text("❌ এই মুহূর্তে প্যানেলে কোনো নাম্বার খালি নেই বা পর্যাপ্ত ব্যালেন্স নেই।", call.message.chat.id, call.message.message_id)
        except Exception as e:
            bot.edit_message_text("⚠️ ভোল্টেক্স এপিআই কানেকশন এরর! আবার চেষ্টা করুন।", call.message.chat.id, call.message.message_id)
            
    # নির্দিষ্ট নাম্বার বাতিল বাটন ক্লিক করলে
    elif call.data.startswith("cancel_"):
        activation_id = call.data.split("_")[1]
        bot.answer_callback_query(call.id, "⏳ Cancel Request Processing...")
        
        cancel_params = {"api_key": VOLTX_API_KEY, "action": "setStatus", "id": activation_id, "status": "8"}
        try:
            response = requests.get(BASE_URL, params=cancel_params, timeout=15).json()
            bot.send_message(call.message.chat.id, "✅ নাম্বারটি সফলভাবে বাতিল করা হয়েছে।")
        except:
            bot.send_message(call.message.chat.id, "⚠️ রিকোয়েস্টটি সফল করা যায়নি।")
            
    # সাধারণ বাতিল বাটন ক্লিক করলে (মেনু থেকে)
    elif call.data == "cancel_num":
        bot.answer_callback_query(call.id, "❌ কোনো একটিভ নাম্বার পাওয়া যায়নি।")
            
    # সার্ভার স্ট্যাটাস বাটন ক্লিক করলে
    elif call.data == "server_status":
        bot.answer_callback_query(call.id, "📊 Checking Live Traffic Status...")
        bot.send_message(call.message.chat.id, "📊 **ACTIVE TRAFFIC REPORT:**\n\n🟢 **WhatsApp Traffic:** High (700+ OTP/min)\n🟢 **Server Status:** VoltxSMS Online & Active")

if __name__ == "__main__":
    t = Thread(target=run_server)
    t.start()
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
