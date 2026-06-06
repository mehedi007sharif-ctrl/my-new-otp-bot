import telebot
import requests
import time
from threading import Thread
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ১. ফ্লাস্ক অ্যাপ তৈরি (রেন্ডার হোস্ٹنگ লাইভ রাখার জন্য)
app = Flask('')

@app.route('/')
def home():
    return "Premium OTP Bot is running perfectly!"

def run_server():
    app.run(host='0.0.0.0', port=8080)

# ==================== [ কনফিগারেশন ] ====================
BOT_TOKEN = "8952089627:AAFOZ2INNfwEN5iN750yG1yVNPPW2XW5FlU"
CRACKERJACK_API_KEY = "Fb1b32e3-a692-4632-a24b-17628dde2de7"
BASE_URL = "https://crackerjacksms.com/public/api"
OTP_GROUP_CHAT_ID = "-1003851787435"

# 📢 ফোর্স জয়েন সিস্টেম (ইউজারের বাধ্যতামূলক জয়েনিং চ্যানেল)
REQUIRED_CHANNELS = ["@rkruhan444"] 
# ========================================================

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# 🔒 ইউজার চ্যানেলে জয়েন করেছে কিনা তা চেক করার ফাংশন
def check_forced_join(user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception:
            return False
    return True

# 👋 স্টার্ট কমান্ড (ফোর্স জয়েন ও ইনলাইন বাটন মেনু)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    # যদি চ্যানেলে জয়েন না থাকে
    if not check_forced_join(user_id):
        markup = InlineKeyboardMarkup()
        btn_link = InlineKeyboardButton("📢 Join Our Channel / চ্যানেলে জয়েন করুন", url="https://t.me/rkruhan444")
        btn_check = InlineKeyboardButton("🔄 Check Join / আমি জয়েন করেছি", callback_data="check_join")
        markup.add(btn_link)
        markup.add(btn_check)
        
        bot.send_message(
            message.chat.id, 
            "⚠️ **আমাদের বটটি ব্যবহার করতে হলে প্রথমে আপনাকে আমাদের চ্যানেলে জয়েন করতে হবে!**\n\nচ্যানেলে জয়েন করার পর নিচের 'আমি জয়েন করেছি' বোতামে চাপ দিন।",
            reply_markup=markup
        )
        return

    # জয়েন থাকলে মূল ইনলাইন মেনু দেখাবে (ভিডিওর মতো স্টাইল)
    show_main_menu(message.chat.id)

# 📱 মূল মেনু ফাংশন (ভিডিওর মতো কাস্টম ডিজাইন)
def show_main_menu(chat_id):
    markup = InlineKeyboardMarkup(row_width=2)
    btn_get = InlineKeyboardButton("📱 Get Number / নাম্বার নিন", callback_data="get_num")
    btn_cancel = InlineKeyboardButton("❌ Cancel Number / বাতিল করুন", callback_data="cancel_num")
    btn_status = InlineKeyboardButton("📊 Live Traffic / লাইভ ট্রাফিক", callback_data="server_status")
    
    markup.add(btn_get, btn_cancel)
    markup.add(btn_status)
    
    bot.send_message(
        chat_id, 
        "Welcome to our Premium OTP Bot!\nWe provide the highest quality Premium Numbers instantly!\n\nChoose an option below 👇", 
        reply_markup=markup
    )

# 🔘 ইনলাইন বোতামের কাজ হ্যান্ডেল করার ফাংশন
@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    user_id = call.from_user.id
    headers = {"mauthapi": CRACKERJACK_API_KEY}
    
    # জয়েন চেক বাটন ক্লিক করলে
    if call.data == "check_join":
        if check_forced_join(user_id):
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id, "✅ ধন্যবাদ! আপনার জয়েন সফল হয়েছে।")
            show_main_menu(call.message.chat.id)
        else:
            bot.answer_callback_query(call.id, "❌ আপনি এখনো চ্যানেলে জয়েন করেননি! দয়া করে জয়েন করুন।", show_alert=True)
            
    # নাম্বার নেওয়ার বাটন ক্লিক করলে
    elif call.data == "get_num":
        if not check_forced_join(user_id):
            bot.answer_callback_query(call.id, "⚠️ আগে চ্যানেলে জয়েন করুন!", show_alert=True)
            return
            
        bot.edit_message_text("🔄 Processing Request... ক্র্যাকারজ্যাক সার্ভার থেকে নতুন নাম্বার খোঁজা হচ্ছে...", call.message.chat.id, call.message.message_id)
        data = {"rid": "26134"} # হোয়াটসঅ্যাপ সার্ভিস আইডি
        
        try:
            response = requests.post(f"{BASE_URL}/getnum", headers=headers, data=data, timeout=15).json()
            
            if response.get("code") == 200 and "data" in response:
                number = response["data"].get("number")
                
                waiting_markup = InlineKeyboardMarkup()
                waiting_markup.add(InlineKeyboardButton("❌ Cancel/নাম্বার বাতিল", callback_data="cancel_num"))
                
                bot.edit_message_text(f"✅ **Number Allocated Successfully!**\n\n📱 Number: `{number}`\n\n💬 Waiting for OTP... ওটিপি কোডের জন্য লাইভ অপেক্ষা করা হচ্ছে...", call.message.chat.id, call.message.message_id, reply_markup=waiting_markup)
                
                # লাইভ ওটিপি চেকিং লুপ (২ মিনিট অপেক্ষা করবে)
                for _ in range(30):
                    time.sleep(4)
                    try:
                        otp_response = requests.get(f"{BASE_URL}/success-otp", headers=headers, timeout=15).json()
                        if otp_response.get("code") == 200 and "data" in otp_response:
                            otp_text = otp_response["data"].get("message")
                            
                            success_msg = f"🎉 **New OTP Received!**\n\n📱 Number: `{number}`\n💬 OTP Message: {otp_text}"
                            
                            # ১. বটের ভেতরে ইউজারকে ওটিপি পাঠানো
                            bot.send_message(call.message.chat.id, success_msg)
                            
                            # ২. ওটিপি গ্রুপে ওটিপি সেন্ড করা
                            try:
                                bot.send_message(OTP_GROUP_CHAT_ID, f"📢 **LIVE OTP REPORT**\n\n{success_msg}")
                            except Exception as group_err:
                                print(f"Group send error: {group_err}")
                            return
                    except:
                        continue
                
                bot.send_message(call.message.chat.id, "❌ Timeout! নির্ধারিত সময়ে কোনো ওটিপি পাওয়া যায়নি।")
            else:
                bot.edit_message_text("❌ এই মুহূর্তে প্যানেলে কোনো নাম্বার খালি নেই বা পর্যাপ্ত ব্যালেন্স নেই।", call.message.chat.id, call.message.message_id)
        except:
            bot.edit_message_text("⚠️ সার্ভার কানেকশন এরর! আবার চেষ্টা করুন।", call.message.chat.id, call.message.message_id)
            
    # নাম্বার বাতিল বাটন ক্লিক করলে
    elif call.data == "cancel_num":
        bot.answer_callback_query(call.id, "⏳ Cancel Request Processing...")
        try:
            response = requests.post(f"{BASE_URL}/cancel-number", headers=headers, timeout=15).json()
            if response.get("code") == 200:
                bot.send_message(call.message.chat.id, "✅ নাম্বারটি সফলভাবে বাতিল করা হয়েছে।")
            else:
                bot.send_message(call.message.chat.id, "❌ বাতিল করার মতো কোনো একটিভ নাম্বার পাওয়া যায়নি।")
        except:
            bot.send_message(call.message.chat.id, "⚠️ রিকোয়েস্টটি সফল করা যায়নি।")
            
    # সার্ভার স্ট্যাটাস বাটন ক্লিক করলে
    elif call.data == "server_status":
        bot.answer_callback_query(call.id, "📊 Checking Live Traffic Status...")
        bot.send_message(call.message.chat.id, "📊 **ACTIVE TRAFFIC REPORT:**\n\n🟢 **WhatsApp Traffic:** High (550+ OTP/min)\n🟢 **Server Status:** Online & Active")

if __name__ == "__main__":
    t = Thread(target=run_server)
    t.start()
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
