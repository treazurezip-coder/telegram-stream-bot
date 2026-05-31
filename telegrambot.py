from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import asyncio
import time

TOKEN = "8824672888:AAEQHlGKs-EIzyvpRd37VshlrFW1O0Ha_yA"

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

COOLDOWN = 60 * 30  # 30 minutes

# =========================
# TOPIC IDS
# =========================
TOPIC_RULES = {
    68: "spotify",
    48: "youtube",
    65: "genie"
}

LEADERBOARD_TOPIC_ID = 73

# store last leaderboard message (for auto delete)
last_leaderboard_message_id = None

# =========================
# JOIN SYSTEM
# =========================
async def joinspotify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await join_team(update, "spotify")

async def joingenie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await join_team(update, "genie")

async def joinyoutube(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await join_team(update, "youtube")

async def join_team(update, team):
    user = update.effective_user

    if user.id not in teams[team]:
        teams[team].append(user.id)

    await update.message.reply_text(f"✅ You joined {team.upper()} STREAMER role!")

# =========================
# CHECK-IN SYSTEM
# =========================
async def checkin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    now = time.time()

    topic_id = update.message.message_thread_id
    team = TOPIC_RULES.get(topic_id)

    if team not in ["spotify", "youtube"]:
        await update.message.reply_text("❌ Check-in only allowed in Spotify or YouTube topics.")
        return

    if user.id not in teams[team]:
        await update.message.reply_text("❌ You are not part of this streaming team.")
        return

    if user.id in last_checkin_time:
        if now - last_checkin_time[user.id] < COOLDOWN:
            await update.message.reply_text("⏳ You already checked in recently.")
            return

    last_checkin_time[user.id] = now
    checkin_count[user.id] = checkin_count.get(user.id, 0) + 1

    await update.message.reply_text(
        f"🙏 Thank you @{user.username or user.first_name}\n"
        f"🎬 Streams: #{checkin_count[user.id]}"
    )

# =========================
# FORMAT USER DISPLAY NAME
# =========================
def get_user_display(user):
    if user.username:
        return f"@{user.username}"
    return user.first_name

# =========================
# TOP 10 LEADERBOARD BUILDER
# =========================
def generate_leaderboard(team_name):
    if not teams[team_name]:
        return f"📊 {team_name.upper()} TOP STREAMERS\n\nNo streamers yet."

    sorted_users = sorted(
        teams[team_name],
        key=lambda uid: checkin_count.get(uid, 0),
        reverse=True
    )

    text = f"🏆 {team_name.upper()} TOP 10 STREAMERS\n\n"

    for i, uid in enumerate(sorted_users[:10], start=1):
        count = checkin_count.get(uid, 0)

        # try to get username (aesthetic fix)
        display = f"user_{uid}"
        text += f"{i}. {display} — {count} streams\n"

    return text

# =========================
# AUTO LEADERBOARD (HOURLY)
# =========================
async def post_leaderboards(app):
    global last_leaderboard_message_id

    while True:
        try:
            spotify_board = generate_leaderboard("spotify")
            youtube_board = generate_leaderboard("youtube")

            text = (
                "📊 HOURLY STREAMING LEADERBOARD\n\n"
                + spotify_board
                + "\n\n"
                + youtube_board
            )

            # delete old leaderboard message (if exists)
            if last_leaderboard_message_id:
                try:
                    await app.bot.delete_message(
                        chat_id=LEADERBOARD_TOPIC_ID,
                        message_id=last_leaderboard_message_id
                    )
                except:
                    pass

            msg = await app.bot.send_message(
                chat_id=LEADERBOARD_TOPIC_ID,
                text=text
            )

            last_leaderboard_message_id = msg.message_id

        except Exception as e:
            print("Leaderboard error:", e)

        await asyncio.sleep(3600)  # 1 hour

# =========================
# TOPIC ENFORCEMENT
# =========================
async def enforce_topics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    topic_id = msg.message_thread_id
    if not topic_id:
        return

    user = msg.from_user
    allowed_team = TOPIC_RULES.get(topic_id)

    if not allowed_team:
        return

    if user.id not in teams[allowed_team]:
        try:
            await msg.delete()
        except:
            await msg.reply_text("❌ You are not allowed here.")

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎧 Streaming Bot Active\n"
        "Use /joinspotify /joingenie /joinyoutube\n"
        "Use /checkin in Spotify/YouTube topics"
    )

# =========================
# STARTUP TASK
# =========================
async def on_startup(app):
    asyncio.create_task(post_leaderboards(app))

# =========================
# BOT SETUP
# =========================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.add_handler(CommandHandler("joinspotify", joinspotify))
app.add_handler(CommandHandler("joingenie", joingenie))
app.add_handler(CommandHandler("joinyoutube", joinyoutube))

app.add_handler(CommandHandler("checkin", checkin))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, enforce_topics))

app.post_init = on_startup

print("Bot running...")
app.run_polling()
