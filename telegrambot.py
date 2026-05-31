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
import os

# =========================

# TOKEN (USE ENV VAR IN RAILWAY)

# =========================

TOKEN = os.getenv("TOKEN")

# =========================

# ADMINS

# =========================

ADMINS = {8117134987}

def is_admin(user_id: int):
return user_id in ADMINS

# =========================

# DATA STORAGE (IN MEMORY)

# =========================

teams = {
"spotify": [],
"youtube": [],
"genie": []
}

checkin_count = {}
last_checkin_time = {}

COOLDOWN = 60 * 10  # 10 minutes
BATCH_SIZE = 20

# =========================

# TOPICS

# =========================

TOPIC_RULES = {
68: "spotify",
48: "youtube",
65: "genie"
}

LEADERBOARD_TOPIC_ID = 73
last_leaderboard_message_id = None

# =========================

# JOIN SYSTEM

# =========================

async def join_team(update: Update, context: ContextTypes.DEFAULT_TYPE, team: str):
user = update.effective_user

```
if user.id not in teams[team]:
    teams[team].append(user.id)

await update.message.reply_text(f"✅ You joined {team.upper()} streamer role!")
```

async def joinspotify(update: Update, context: ContextTypes.DEFAULT_TYPE):
await join_team(update, context, "spotify")

async def joinyoutube(update: Update, context: ContextTypes.DEFAULT_TYPE):
await join_team(update, context, "youtube")

async def joingenie(update: Update, context: ContextTypes.DEFAULT_TYPE):
await join_team(update, context, "genie")

# =========================

# CHECK-IN SYSTEM

# =========================

async def checkin(update: Update, context: ContextTypes.DEFAULT_TYPE):
user = update.effective_user
now = time.time()

```
topic_id = update.message.message_thread_id
team = TOPIC_RULES.get(topic_id)

if team not in ["spotify", "youtube"]:
    await update.message.reply_text("❌ Check-in only allowed in Spotify or YouTube topics.")
    return

if user.id not in teams[team]:
    await update.message.reply_text("❌ You are not part of this team.")
    return

if user.id in last_checkin_time:
    if now - last_checkin_time[user.id] < COOLDOWN:
        await update.message.reply_text("⏳ Cooldown active. Try again later.")
        return

last_checkin_time[user.id] = now
checkin_count[user.id] = checkin_count.get(user.id, 0) + 1

await update.message.reply_text(
    f"🙏 Thank you {user.username or user.first_name}\n"
    f"🎬 Streams: #{checkin_count[user.id]}"
)
```

# =========================

# LEADERBOARD

# =========================

def generate_leaderboard(team):
if not teams[team]:
return f"📊 {team.upper()} TOP STREAMERS\nNo data yet."

```
sorted_users = sorted(
    teams[team],
    key=lambda uid: checkin_count.get(uid, 0),
    reverse=True
)

text = f"🏆 {team.upper()} TOP STREAMERS\n\n"

for i, uid in enumerate(sorted_users[:10], 1):
    count = checkin_count.get(uid, 0)
    text += f"{i}. user_{uid} — {count}\n"

return text
```

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
spotify = generate_leaderboard("spotify")
youtube = generate_leaderboard("youtube")

```
await update.message.reply_text(spotify + "\n\n" + youtube)
```

# =========================

# RESET

# =========================

async def resetleaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
if not is_admin(update.effective_user.id):
await update.message.reply_text("❌ Admin only.")
return

```
checkin_count.clear()
last_checkin_time.clear()

await update.message.reply_text("✅ Leaderboard reset.")
```

# =========================

# HIDDEN MENTIONS

# =========================

def build_mentions(user_ids):
return "".join([f'<a href="tg://user?id={uid}">‎</a>' for uid in user_ids])

# =========================

# NOTIFY SYSTEM

# =========================

async def notify_team(update: Update, context: ContextTypes.DEFAULT_TYPE, team: str):
if not is_admin(update.effective_user.id):
await update.message.reply_text("❌ Admin only.")
return

```
members = teams.get(team, [])
if not members:
    await update.message.reply_text("No members found.")
    return

message_text = " ".join(update.message.text.split(" ")[1:]) or "Keep streaming!"

batches = [members[i:i+BATCH_SIZE] for i in range(0, len(members), BATCH_SIZE)]

for batch in batches:
    hidden = build_mentions(batch)

    await update.message.reply_text(
        f"📢 {team.upper()} ALERT\n\n"
        f"{message_text}\n\n"
        f"{hidden}",
        parse_mode="HTML"
    )
```

async def notifyspotify(update: Update, context: ContextTypes.DEFAULT_TYPE):
await notify_team(update, context, "spotify")

async def notifyyoutube(update: Update, context: ContextTypes.DEFAULT_TYPE):
await notify_team(update, context, "youtube")

async def notifygenie(update: Update, context: ContextTypes.DEFAULT_TYPE):
await notify_team(update, context, "genie")

# =========================

# TOPIC ENFORCEMENT

# =========================

async def enforce_topics(update: Update, context: ContextTypes.DEFAULT_TYPE):
msg = update.message
if not msg:
return

```
team = TOPIC_RULES.get(msg.message_thread_id)
if not team:
    return

if msg.from_user.id not in teams[team]:
    try:
        await msg.delete()
    except:
        pass
```

# =========================

# START

# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text("Streaming bot is active.")

# =========================

# APP SETUP

# =========================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.add_handler(CommandHandler("joinspotify", joinspotify))
app.add_handler(CommandHandler("joinyoutube", joinyoutube))
app.add_handler(CommandHandler("joingenie", joingenie))

app.add_handler(CommandHandler("checkin", checkin))
app.add_handler(CommandHandler("leaderboard", leaderboard))
app.add_handler(CommandHandler("resetleaderboard", resetleaderboard))

app.add_handler(CommandHandler("notifyspotify", notifyspotify))
app.add_handler(CommandHandler("notifyyoutube", notifyyoutube))
app.add_handler(CommandHandler("notifygenie", notifygenie))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, enforce_topics))

print("Bot running...")
app.run_polling()
