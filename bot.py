import os
import json
from typing import Set
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# === Configuration ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8514728370:AAGhbWu7d_lz2aU_-hNJszfM7Seg3H5SfT0")
PAYPAL_LINK = os.getenv("PAYPAL_LINK", "https://www.paypal.me/yourusername/5")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
PAID_USERS_FILE = "paid_users.json"
BAD_WORDS = {"badword1", "badword2", "foo"}

# === Helpers ===
def load_paid_users() -> Set[int]:
    if not os.path.exists(PAID_USERS_FILE):
        return set()
    try:
        with open(PAID_USERS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()

def save_paid_users(users: Set[int]) -> None:
    try:
        with open(PAID_USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(users), f)
    except Exception:
        pass

PAID_USERS = load_paid_users()

def is_admin(user_id: int) -> bool:
    return ADMIN_ID != 0 and user_id == ADMIN_ID

# === Commands ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome! Use /buy to get the PayPal link.\n"
        "Admins can use /approve, /addbadword, /removebadword."
    )

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Pay here: {PAYPAL_LINK}\n"
        f"Your Telegram ID: {update.effective_user.id}\n"
        "Send this ID to the admin after payment."
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in PAID_USERS:
        await update.message.reply_text("✅ You are marked as PAID.")
    else:
        await update.message.reply_text("❌ You are NOT marked as paid.")

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("You are not authorized.")
        return
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /approve <user_id>")
        return
    try:
        user_id = int(context.args[0])
        PAID_USERS.add(user_id)
        save_paid_users(PAID_USERS)
        await update.message.reply_text(f"User {user_id} approved.")
    except ValueError:
        await update.message.reply_text("Invalid user ID.")

async def badwords(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bad words:\n" + ", ".join(sorted(BAD_WORDS)))

async def addbadword(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("You are not authorized.")
        return
    if context.args:
        word = context.args[0].lower()
        BAD_WORDS.add(word)
        await update.message.reply_text(f"Added: {word}")
    else:
        await update.message.reply_text("Usage: /addbadword <word>")

async def removebadword(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("You are not authorized.")
        return
    if context.args:
        word = context.args[0].lower()
        if word in BAD_WORDS:
            BAD_WORDS.remove(word)
            await update.message.reply_text(f"Removed: {word}")
        else:
            await update.message.reply_text("Word not found.")
    else:
        await update.message.reply_text("Usage: /removebadword <word>")

# === Message filter ===
async def filter_bad_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if any(bad in text for bad in BAD_WORDS):
        try:
            await update.message.delete()
        except Exception:
            pass
        await update.effective_chat.send_message(
            f"Message from @{update.effective_user.username or update.effective_user.id} was removed."
        )

# === Main ===
async def main():
    if TELEGRAM_BOT_TOKEN == "PUT_YOUR_BOT_TOKEN_HERE":
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN as an environment variable.")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("badwords", badwords))
    app.add_handler(CommandHandler("addbadword", addbadword))
    app.add_handler(CommandHandler("removebadword", removebadword))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, filter_bad_words))

    print("Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
