import telebot
from telebot import types
from databace import init_db, save_message
from config import token, admin_ids

# Initialize the bot
bot = telebot.TeleBot(token)

# Bot holati (ishlayotgan yoki to‘xtatilgan)
bot_running = True

# Foydalanuvchilarning bot ishlamayotgan paytda xabar jo‘natganlari
offline_users = set()

def admin_control_keyboard():
    """Creates admin panel buttons for starting and stopping the bot."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    start_button = types.KeyboardButton("▶ Botni ishga tushurish")
    stop_button = types.KeyboardButton("⏹ Botni to‘xtatish")
    markup.add(start_button, stop_button)
    return markup

def reply_to_user_button(user_id):
    """Adds a reply button for the user."""
    markup = types.InlineKeyboardMarkup()
    reply_button = types.InlineKeyboardButton("✉️ Reply", callback_data=f"reply_{user_id}")
    markup.add(reply_button)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome_message(message):
    """Sends a welcome message when the user issues the /start command."""
    global bot_running
    if not bot_running:
        bot.send_message(message.chat.id, "❌ Bot hozir ish jarayonida emas. Iltimos, keyinroq urinib ko‘ring.")
        offline_users.add(message.chat.id)
        return
    
    bot.send_message(
        message.chat.id,
        (
            "Hello! Welcome.\n\n"
            "📌 *Writing review costs 5,000 UZS for two writings*\n\n"
            "💳 *Card number:* 9860 1901 0702 0777\n\n"
            "📸 *Please*, take a picture or screenshot of the receipt and send it.\n\n"
            "✍️ Then send your writing for review."
        ),
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: message.text in ["▶ Botni ishga tushurish", "⏹ Botni to‘xtatish"])
def handle_bot_control(message):
    """Handles bot start and stop commands from admin."""
    global bot_running
    if message.chat.id not in admin_ids:
        bot.send_message(message.chat.id, "❌ Sizda bu amalni bajarish huquqi yo‘q!")
        return
    
    if message.text == "▶ Botni ishga tushurish":
        bot_running = True
        bot.send_message(message.chat.id, "✅ Bot ishga tushdi!")
        for user_id in offline_users:
            bot.send_message(user_id, "✅ Bot ishga tushdi va siz adminga xabar jo‘natishingiz mumkin!")
        offline_users.clear()
    elif message.text == "⏹ Botni to‘xtatish":
        bot_running = False
        bot.send_message(message.chat.id, "⏹ Bot ish faoliyati to‘xtatildi!")

@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'sticker'])
def forward_to_admin(message):
    """Forwards all user messages to the admin."""
    global bot_running
    if not bot_running:
        bot.send_message(message.chat.id, "❌ Bot hozir ish jarayonida emas. Iltimos, keyinroq urinib ko‘ring.")
        offline_users.add(message.chat.id)
        return
    
    username = message.from_user.username or "No username"
    first_name = message.from_user.first_name or "No first name"
    phone_number = message.contact.phone_number if message.contact else "No phone number"
    user_id = message.from_user.id
    message_type = message.content_type

    if message_type == 'text':
        message_content = message.text
    else:
        message_content = f"{message_type} file"

    save_message(user_id, username, message_type, message_content)
    bot.send_message(message.chat.id, "Please wait for the admin's reply!")

    for admin_id in admin_ids:
        bot.send_message(
            admin_id,
            f"📩 New message from @{username} (ID: {user_id}):\n👤 Name: {first_name}\n📞 Phone: {phone_number}\n\n{message_content}",
            reply_markup=reply_to_user_button(user_id)
        )
        bot.send_message(admin_id, "Use the buttons below:", reply_markup=admin_control_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("reply_"))
def handle_reply(call):
    """Handles the reply button click by the admin."""
    user_id = int(call.data.split("_")[1])
    msg = bot.send_message(call.message.chat.id, "✍️ Write your reply or send a file:")
    bot.register_next_step_handler(msg, send_reply_to_user, user_id)

def send_reply_to_user(message, user_id):
    """Admin sends a reply to the user."""
    try:
        if message.content_type == 'text':
            bot.send_message(user_id, f"📩 Admin reply:\n\n{message.text}")
        else:
            bot.copy_message(user_id, message.chat.id, message.message_id)

        bot.send_message(message.chat.id, "✅ Reply sent to the user.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {e}")

if __name__ == "__main__":
    import time
    init_db()
    print("Starting the bot...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(1)
