import telebot
from telebot import types
from databace import init_db, save_message
from config import token, admin_ids

# Initialize the bot
bot = telebot.TeleBot(token)

@bot.message_handler(commands=['start'])
def send_welcome_message(message):
    """Sends a welcome message when the user issues the /start command."""
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

def reply_to_user_button(user_id):
    """Adds a reply button for the user."""
    markup = types.InlineKeyboardMarkup()
    reply_button = types.InlineKeyboardButton("✉️ Reply", callback_data=f"reply_{user_id}")
    markup.add(reply_button)
    return markup

def admin_reply_keyboard():
    """Creates reply buttons for the admin."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    button_paid = types.KeyboardButton("Payment completed ✅")
    button_not_paid = types.KeyboardButton("Payment not completed ❌")
    button_task_1 = types.KeyboardButton("Submit Task 1 ✅")
    button_task_2 = types.KeyboardButton("Submit Task 2 ✅")
    markup.add(button_paid, button_not_paid, button_task_1, button_task_2)
    return markup

@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'sticker'])
def forward_to_admin(message):
    """Forwards all user messages to the admin."""
    username = message.from_user.username or "No username"
    first_name = message.from_user.first_name or "No first name"
    user_id = message.from_user.id
    message_type = message.content_type

    if message_type == 'text':
        message_content = message.text
    else:
        message_content = f"{message_type} file"

    save_message(user_id, username, message_type, message_content)

    # Notify the user to wait for an admin response
    bot.send_message(message.chat.id, "Please wait for the admin's reply!")

    for admin_id in admin_ids:
        if message.content_type == 'text':
            bot.send_message(
                admin_id,
                (
                    f"📩 New message:\n\n{message.text}\n\n"
                    f"👤 User: @{username} (ID: {user_id})\n"
                    f"📛 Name: {first_name}"
                ),
                reply_markup=reply_to_user_button(user_id)
            )
        else:
            bot.forward_message(admin_id, message.chat.id, message.message_id)
            bot.send_message(
                admin_id,
                (
                    f"👤 User: @{username} (ID: {user_id})\n"
                    f"📛 Name: {first_name}"
                ),
                reply_markup=reply_to_user_button(user_id)
            )
        # Show admin reply buttons
        bot.send_message(admin_id, "Use the buttons below:", reply_markup=admin_reply_keyboard())

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

@bot.message_handler(func=lambda message: message.text in ["Payment completed ✅", "Payment not completed ❌"])
def handle_admin_choice(message):
    """Handles admin buttons for payment confirmation."""
    if message.text == "Payment completed ✅":
        response = "✅ Confirmed by admin: Payment completed."
    elif message.text == "Payment not completed ❌":
        response = "❌ Declined by admin: Payment not completed."
    else:
        return

    if message.reply_to_message:
        forwarded_from = message.reply_to_message.forward_from
        if forwarded_from:
            user_id = forwarded_from.id
            try:
                bot.send_message(user_id, response)
                bot.send_message(message.chat.id, "✅ Reply sent to the user.")
            except Exception as e:
                bot.send_message(message.chat.id, f"❌ Error: {e}")

@bot.message_handler(func=lambda message: message.text in ["Submit Task 1 ✅", "Submit Task 2 ✅"])
def handle_bot_tasks(message):
    """Handles task submission buttons."""
    if message.text == "Submit Task 1 ✅":
        bot.send_message(message.chat.id, "✅ Task 1 submission noted.")
    elif message.text == "Submit Task 2 ✅":
        bot.send_message(message.chat.id, "✅ Task 2 submission noted.")

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