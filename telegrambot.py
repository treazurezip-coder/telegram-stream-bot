from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import asyncio
import time

TOKEN = "YOUR_BOT_TOKEN_HERE"

# =========================
# DATA
# =========================
teams = {
    "spotify": [],
    "genie": [],
    "youtube": []
}

checkin_count = {}
last_checkin_time = {}

ADMINS = {8117134987}

BATCH_SIZE = 20
COOLDOWN = 60 * 10  # 10 minutes

# =========================
# TOPICS (optional use later)
# =========================
TOPIC_RULES = {
    68: "spotify",
    48: "youtube",
    65: "genie"
}

# =========================
# ADMIN CHECK
# =========================
def is_admin(user_id: int):
    return user_id in ADMINS

# =========================
# JOIN SYSTEM (PUBLIC)
# =========================
async def joinspotify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in teams["spotify"]:
        teams["spotify"].append(update.effective_user.id)
    await update.message.reply_text("✅ Joined Spotify streamers!")

# =========================
# CHECKIN (PUBLIC + cooldown)
# =========================
async def checkin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    now = time.time()

    team = "spotify"  # simplified for stability

    if user.id not in teams[team]:
        await update.message.reply_text("❌ You are not a streamer yet.")
        return

    if user.id in last_checkin_time:
        if now - last_checkin_time[user.id] < COOLDOWN:
            await update.message.reply_text("⏳ 10 min cooldown active.")
            return

    last_checkin_time[user.id] = now
    checkin_count[user.id] = checkin_count.get(user.id, 0) + 1

    await update.message.reply_text(
        f"🙏 Thanks @{user.username or user.first_name}\n"
        f"🎬 Streams: {checkin_count[user.id]}"
    )

# =========================
# HIDDEN MENTIONS BUILDER
# =========================
def build_hidden_mentions(user_ids):
    return "".join([f'<a href="tg://user?id={uid}">‎</a>' for uid in user_ids])

# =========================
# NOTIFY SYSTEM (FIXED)
# =========================
async def notify_team(update: Update, context: ContextTypes.DEFAULT_TYPE, team_name: str):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only.")
        return

    members = teams.get(team_name, [])

    if not members:
        await update.message.reply_text(f"No {team_name} streamers found.")
        return

    # custom message support
    parts = update.message.text.split(" ", 1)
    custom_message = parts[1] if len(parts) > 1 else "Please continue streaming!"

    # batching
    batches = [members[i:i + BATCH_SIZE] for i in range(0, len(members), BATCH_SIZE)]

    for batch in batches:
        hidden = build_hidden_mentions(batch)

        await update.message.reply_text(
            f"📢 {team_name.upper()} STREAMING CALL\n\n"
            f"{custom_message}\n\n"
            f"{hidden}",
            parse_mode="HTML"
        )

        await asyncio.sleep(1)  # avoid spam limits

# =========================
# COMMANDS (ADMIN ONLY)
# =========================
async def notifyspotify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await notify_team(update, context, "spotify")

async def notifyyoutube(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await notify_team(update, context, "youtube")

async def notifygenie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await notify_team(update, context, "genie")

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎧 Bot is running.")

# =========================
# SETUP BOT
# =========================
app = ApplicationBuilder().token(TOKEN).build()

# PUBLIC COMMANDS ONLY
app.add_handler(CommandHandler("joinspotify", joinspotify))
app.add_handler(CommandHandler("checkin", checkin))

# ADMIN COMMANDS
app.add_handler(CommandHandler("notifyspotify", notifyspotify))
app.add_handler(CommandHandler("notifyyoutube", notifyyoutube))
app.add_handler(CommandHandler("notifygenie", notifygenie))

# START
app.add_handler(CommandHandler("start", start))

print("Bot running...")
app.run_polling()
