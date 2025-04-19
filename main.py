from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Store mapping between message_id and sender user_id & username
user_data_map = {}
driver_list = {}

def format_ride_message(parts):
    return f"🚗 *New Ride Request!*\n\n📍 From: {parts[0]}\n📍 To: {parts[1]}\n👥 Pax: {parts[2]}\n⏰ Time: {parts[3]}"

def handle_message(update: Update, context: CallbackContext):
    user = update.effective_user
    text = update.message.text
    parts = [part.strip() for part in text.split(">")]

    if len(parts) != 4:
        return

    context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)

    ride_msg = format_ride_message(parts)

    keyboard = [
        [InlineKeyboardButton("✅ Taken", callback_data="taken")],
        [InlineKeyboardButton("👤 Contact", callback_data="contact")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    sent_msg = context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=ride_msg,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

    user_data_map[sent_msg.message_id] = {
        "user_id": user.id,
        "username": user.username or "NoUsername"
    }

def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    action = query.data
    msg_id = query.message.message_id
    from_user = query.from_user

    user_info = user_data_map.get(msg_id)

    if not user_info:
        query.edit_message_text(f"{query.message.text}\n\nStatus: ❗Expired or missing data.")
        return

    if action == "taken":
        if from_user.id != user_info["user_id"]:
            query.answer("Only the original sender can mark this as Taken.", show_alert=True)
            return
        query.edit_message_text(f"{query.message.text}\n\nStatus: ✅ Taken")

    elif action == "contact":
        username = user_info["username"]
        if username == "NoUsername":
            query.answer("User has no username set!", show_alert=True)
        else:
            query.answer()
            context.bot.send_message(
                chat_id=from_user.id,
                text=f"🚗 Contact passenger: https://t.me/{username}"
            )

def register_driver(update: Update, context: CallbackContext):
    user = update.effective_user
    driver_list[user.id] = user.username or "NoUsername"
    update.message.reply_text("✅ You are registered as a driver.")

def list_drivers(update: Update, context: CallbackContext):
    if not driver_list:
        update.message.reply_text("❌ No drivers registered yet.")
        return
    msg = "🚖 *Registered Drivers:*\n"
    for uid, username in driver_list.items():
        user_display = f"@{username}" if username != "NoUsername" else f"User ID: {uid}"
        msg += f"• {user_display}\n"
    update.message.reply_text(msg, parse_mode="Markdown")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("register_driver", register_driver))
    dp.add_handler(CommandHandler("list_drivers", list_drivers))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(button))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
