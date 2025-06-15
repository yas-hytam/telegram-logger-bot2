import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN") or "ISI_TOKEN_BOT_DISINI"
VALID_UIDS = ['UID1112', 'UID1807']

user_sessions = {}
user_monitoring_msg = {}
last_update = {}

# /start handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_sessions.pop(chat_id, None)
    await context.bot.send_message(chat_id, '📲 Masukkan UID kamu untuk mulai monitoring.')

# UID input handler
async def handle_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    uid = update.message.text.strip()
    if uid in VALID_UIDS:
        user_sessions[chat_id] = uid
        keyboard = [[
            InlineKeyboardButton("🔄 Monitoring", callback_data="monitoring"),
            InlineKeyboardButton("🚪 Keluar", callback_data="logout")
        ]]
        msg = await update.message.reply_text(
            f"✅ UID diterima: *{uid}*\nMenunggu data dari device...",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        user_monitoring_msg[chat_id] = msg.message_id
    else:
        await update.message.reply_text("❌ UID tidak valid. Coba lagi.")

# tombol monitoring dan logout
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat.id

    if query.data == "logout":
        user_sessions.pop(chat_id, None)
        user_monitoring_msg.pop(chat_id, None)
        last_update.pop(chat_id, None)
        await query.edit_message_text("🚪 Kamu telah keluar.\nGunakan /start untuk masuk lagi.")
    elif query.data == "monitoring":
        if chat_id in user_sessions:
            uid = user_sessions[chat_id]
            teks = last_update.get(chat_id, f"📲 UID: {uid}\n\nBelum ada data.")
            keyboard = [[
                InlineKeyboardButton("🔄 Monitoring", callback_data="monitoring"),
                InlineKeyboardButton("🚪 Keluar", callback_data="logout")
            ]]
            await query.edit_message_text(teks, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text("❌ Sesi kamu sudah habis. Gunakan /start.")

# update data dari APK logger
async def push_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    if not msg.startswith("UID:"):
        return
    lines = msg.split('\n')
    uid = lines[0].replace("UID:", "").strip()
    for chat_id, session_uid in user_sessions.items():
        if session_uid == uid:
            last_update[chat_id] = msg.strip()
            msg_id = user_monitoring_msg.get(chat_id)
            if msg_id:
                keyboard = [[
                    InlineKeyboardButton("🔄 Monitoring", callback_data="monitoring"),
                    InlineKeyboardButton("🚪 Keluar", callback_data="logout")
                ]]
                try:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=msg_id,
                        text=msg.strip(),
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                except:
                    pass

# jalankan bot
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & filters.Regex('^UID:'), push_data))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_uid))

print("Bot siap jalan...")
app.run_polling()