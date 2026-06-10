import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from words import get_random_word, get_daily_word

TOKEN = "8212503990:AAGd7Oyj-CK9uugGF5G13gV8l0D10WvgtpA"
MAX_TRIES = 6
GREEN = "🟩"
YELLOW = "🟨"
GRAY = "⬛"
EMPTY = "⬜"

games = {}

def check_guess(secret, guess):
    result = []
    used = [False]*len(secret)
    statuses = [None]*len(guess)
    for i,(g,s) in enumerate(zip(guess,secret)):
        if g==s:
            statuses[i]="green"
            used[i]=True
    for i,g in enumerate(guess):
        if statuses[i]: continue
        for j,s in enumerate(secret):
            if not used[j] and g==s:
                statuses[i]="yellow"
                used[j]=True
                break
        if not statuses[i]: statuses[i]="gray"
    return list(zip(guess,statuses))

def render_board(guesses,slen=5):
    lines=[]
    for guess,result in guesses:
        row=""
        for char,status in result:
            row+=GREEN if status=="green" else YELLOW if status=="yellow" else GRAY
        lines.append(row+f"  `{guess}`")
    for _ in range(MAX_TRIES-len(guesses)):
        lines.append(EMPTY*slen)
    return "\n".join(lines)

async def start(update,context):
    uid=update.effective_user.id
    name=update.effective_user.first_name or "بازیکن"
    kb=[[KeyboardButton("🎮 بازی جدید"),KeyboardButton("📅 چالش روزانه")],[KeyboardButton("📖 راهنما")]]
    await update.message.reply_text(f"سلام {name}! 👋\nبه واژه‌یاب خوش اومدی 🟩\nکلمه ۵ حرفی رو حدس بزن!",reply_markup=ReplyKeyboardMarkup(kb,resize_keyboard=True))

async def handle(update,context):
    uid=update.effective_user.id
    text=update.message.text.strip()
    if text=="🎮 بازی جدید":
        word=get_random_word()
        games[uid]={"word":word,"guesses":[]}
        board=render_board([],len(word))
        await update.message.reply_text(f"🎮 بازی شروع شد!\n\n{board}\n\nکلمه ۵ حرفی بنویس 👇",parse_mode="Markdown")
        return
    if text=="📅 چالش روزانه":
        word=get_daily_word()
        games[uid]={"word":word,"guesses":[]}
        board=render_board([],len(word))
        await update.message.reply_text(f"📅 چالش روزانه!\n\n{board}\n\nکلمه ۵ حرفی بنویس 👇",parse_mode="Markdown")
        return
    if text=="📖 راهنما":
        await update.message.reply_text(f"🟩 حرف درست، جای درست\n🟨 حرف درست، جای اشتباه\n⬛ حرف اشتباه\n\n۶ تلاش داری!")
        return
    game=games.get(uid)
    if not game:
        await update.message.reply_text("اول 🎮 بازی جدید رو بزن!")
        return
    secret=game["word"]
    if len(text)!=len(secret):
        await update.message.reply_text(f"کلمه باید {len(secret)} حرف باشه!")
        return
    result=check_guess(secret,text)
    game["guesses"].append((text,result))
    tries=len(game["guesses"])
    board=render_board(game["guesses"],len(secret))
    won=all(s=="green" for _,s in result)
    if won:
        del games[uid]
        await update.message.reply_text(f"{board}\n\n🎉 آفرین! در {tries} تلاش پیدا کردی!\nکلمه: *{secret}*",parse_mode="Markdown")
    elif tries>=MAX_TRIES:
        del games[uid]
        await update.message.reply_text(f"{board}\n\n😔 کلمه: *{secret}*\nدوباره تلاش کن!",parse_mode="Markdown")
    else:
        await update.message.reply_text(f"{board}\n\n_تلاش {tries+1} از {MAX_TRIES}_",parse_mode="Markdown")

app=ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start",start))
app.add_handler(MessageHandler(filters.TEXT&~filters.COMMAND,handle))
print("ربات شروع شد!")
app.run_polling()
