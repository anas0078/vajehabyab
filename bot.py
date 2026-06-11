import os
import json
import random
from datetime import date, datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
DATA_FILE = "data.json"
MAX_TRIES = 6
GREEN = "🟩"
YELLOW = "🟨"
GRAY = "⬛"
EMPTY = "⬜"

WORDS = [
    "کتاب","درخت","زمین","آتش","شهر","کوه","دریا","برف","ستاره","خانه",
    "اتاق","میوه","مدرسه","بازار","فوتبال","بهار","تابستان","پاییز","زمستان",
    "صبحانه","ناهار","شامگاه","گلدان","پرنده","ماهیگیر","باغبان","دوچرخه",
    "کتابخانه","دانشجو","معلمان","آشپزی","ورزشکار","نقاشی","موسیقی","رستوران",
    "بیمارستان","داروخانه","فروشگاه","ساختمان","آسمانخراش"
]

DAILY_WORDS = ["کتاب","درخت","زمین","آتش","شهر","کوه","دریا","برف","ستاره","خانه",
               "اتاق","میوه","مدرسه","بازار","فوتبال","بهار","پاییز","زمستان"]

THEMES = {
    "classic": {"green": "🟩", "yellow": "🟨", "gray": "⬛"},
    "fire":    {"green": "🔴", "yellow": "🟠", "gray": "⬫"},
    "ice":     {"green": "🔵", "yellow": "🩵", "gray": "⬜"},
    "gold":    {"green": "🥇", "yellow": "🥈", "gray": "🥉"},
}

KEYBOARD = [
    ["ا","ب","پ","ت","ث","ج","چ"],
    ["ح","خ","د","ذ","ر","ز","ژ"],
    ["س","ش","ص","ض","ط","ظ","ع"],
    ["غ","ف","ق","ک","گ","ل","م"],
    ["ن","و","ه","ی","◀️ پاک"]
]

def load():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE,"r",encoding="utf-8") as f:
            return json.load(f)
    return {"users":{},"queue":[],"matches":{}}

def save(data):
    with open(DATA_FILE,"w",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)

def get_user(data, uid):
    uid = str(uid)
    if uid not in data["users"]:
        data["users"][uid] = {
            "name":"بازیکن","score":0,"coins":10,"wins":0,
            "games":0,"streak":0,"best_streak":0,
            "current_game":None,"theme":"classic",
            "daily_date":None,"typing_buffer":""
        }
    return data["users"][uid]

def get_theme(user):
    return THEMES.get(user.get("theme","classic"), THEMES["classic"])

def check_guess(secret, guess):
    statuses = [None]*len(guess)
    used = [False]*len(secret)
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

def render_board(guesses, theme, slen=5):
    lines=[]
    for guess,result in guesses:
        row=""
        for char,status in result:
            row+=theme["green"] if status=="green" else theme["yellow"] if status=="yellow" else theme["gray"]
        lines.append(row+f"  `{guess}`")
    for _ in range(MAX_TRIES-len(guesses)):
        lines.append(EMPTY*slen)
    return "\n".join(lines)

def main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🎮 بازی جدید"), KeyboardButton("📅 چالش روزانه")],
        [KeyboardButton("⚔️ رقابت آنلاین"), KeyboardButton("🏆 جدول برترین‌ها")],
        [KeyboardButton("💰 کیف پول"), KeyboardButton("🎨 پوسته‌ها")],
        [KeyboardButton("📊 آمار من"), KeyboardButton("📖 راهنما")]
    ], resize_keyboard=True)

def letter_keyboard():
    kb = []
    for row in KEYBOARD:
        kb.append([KeyboardButton(c) for c in row])
    kb.append([KeyboardButton("🏳️ تسلیم"), KeyboardButton("💡 راهنمایی (۵ سکه)")])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

async def start(update, context):
    data = load()
    uid = update.effective_user.id
    user = get_user(data, uid)
    user["name"] = update.effective_user.first_name or "بازیکن"
    save(data)
    await update.message.reply_text(
        f"سلام {user['name']} عزیز! 👋\n\n"
        "🟩 به *واژه‌یاب* خوش اومدی!\n\n"
        f"💰 سکه‌های شما: {user['coins']}\n\n"
        "کلمه فارسی رو حدس بزن!\n"
        "🟩 حرف درست، جای درست\n"
        "🟨 حرف درست، جای اشتباه\n"
        "⬛ حرف اشتباه",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

async def new_game(update, context):
    data = load()
    uid = update.effective_user.id
    user = get_user(data, uid)
    word = random.choice(WORDS)
    user["current_game"] = {"word":word,"guesses":[],"mode":"normal","typing_buffer":""}
    user["games"] += 1
    save(data)
    theme = get_theme(user)
    board = render_board([], theme, len(word))
    await update.message.reply_text(
        f"🎮 *بازی جدید شروع شد!*\n\n{board}\n\n"
        f"کلمه {len(word)} حرفی رو حدس بزن 👇\n"
        f"_(تلاش ۱ از {MAX_TRIES})_",
        parse_mode="Markdown",
        reply_markup=letter_keyboard()
    )

async def daily(update, context):
    data = load()
    uid = update.effective_user.id
    user = get_user(data, uid)
    today = str(date.today())
    if user["daily_date"] == today:
        await update.message.reply_text("📅 امروز قبلاً چالش روزانه بازی کردی!\nفردا برگرد 🌅", reply_markup=main_keyboard())
        return
    random.seed(today)
    word = random.choice(DAILY_WORDS)
    random.seed()
    user["current_game"] = {"word":word,"guesses":[],"mode":"daily","typing_buffer":""}
    save(data)
    theme = get_theme(user)
    board = render_board([], theme, len(word))
    await update.message.reply_text(
        f"📅 *چالش روزانه!*\n\n{board}\n\n"
        "همه امروز یه کلمه دارن!\n"
        f"کلمه {len(word)} حرفی بنویس 👇\n"
        f"_(تلاش ۱ از {MAX_TRIES})_",
        parse_mode="Markdown",
        reply_markup=letter_keyboard()
    )

async def online_match(update, context):
    data = load()
    uid = str(update.effective_user.id)
    user = get_user(data, update.effective_user.id)
    
    if uid in data.get("queue", []):
        await update.message.reply_text("⏳ داری منتظر حریف میمونی...", reply_markup=main_keyboard())
        return
    
    queue = data.get("queue", [])
    
    if queue and queue[0] != uid:
        opponent_id = queue.pop(0)
        word = random.choice(WORDS)
        match_id = f"{opponent_id}_{uid}"
        
        if "matches" not in data:
            data["matches"] = {}
        
        data["matches"][match_id] = {
            "word": word,
            "players": {
                opponent_id: {"guesses": [], "done": False, "tries": 0},
                uid: {"guesses": [], "done": False, "tries": 0}
            },
            "started": datetime.now().isoformat()
        }
        
        opp_user = get_user(data, int(opponent_id))
        opp_user["current_game"] = {"word":word,"guesses":[],"mode":"online","match_id":match_id,"opponent":uid,"typing_buffer":""}
        user["current_game"] = {"word":word,"guesses":[],"mode":"online","match_id":match_id,"opponent":opponent_id,"typing_buffer":""}
        
        data["queue"] = queue
        save(data)
        
        theme = get_theme(user)
        board = render_board([], theme, len(word))
        
        await update.message.reply_text(
            f"⚔️ *حریف پیدا شد!*\n\n{board}\n\nبازی شروع شه! کلمه {len(word)} حرفی رو حدس بزن 🔥",
            parse_mode="Markdown",
            reply_markup=letter_keyboard()
        )
        
        try:
            await context.bot.send_message(
                chat_id=int(opponent_id),
                text=f"⚔️ *حریف پیدا شد!*\n\n{board}\n\nبازی شروع شه! کلمه {len(word)} حرفی رو حدس بزن 🔥",
                parse_mode="Markdown",
                reply_markup=letter_keyboard()
            )
        except:
            pass
    else:
        data["queue"] = queue + [uid]
        save(data)
        await update.message.reply_text(
            "⏳ *دنبال حریف میگردم...*\n\nصبر کن یه نفر پیدا بشه! 🔍",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )

async def show_wallet(update, context):
    data = load()
    user = get_user(data, update.effective_user.id)
    await update.message.reply_text(
        f"💰 *کیف پول*\n\n"
        f"سکه: {user['coins']} 🪙\n\n"
        f"*خرید با سکه:*\n"
        f"💡 نشون دادن یه حرف = ۵ سکه\n"
        f"🔤 نشون دادن کلمه = ۳۰ سکه\n"
        f"➕ یه تلاش اضافه = ۱۵ سکه\n\n"
        f"*کسب سکه:*\n"
        f"✅ برد = ۱۰ سکه\n"
        f"⚔️ برد آنلاین = ۲۵ سکه\n"
        f"📅 چالش روزانه = ۵۰ سکه",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

async def show_themes(update, context):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🟩 کلاسیک", callback_data="theme_classic"),
         InlineKeyboardButton("🔴 آتش", callback_data="theme_fire")],
        [InlineKeyboardButton("🔵 یخ", callback_data="theme_ice"),
         InlineKeyboardButton("🥇 طلا", callback_data="theme_gold")]
    ])
    await update.message.reply_text("🎨 *پوسته رو انتخاب کن:*", parse_mode="Markdown", reply_markup=kb)

async def theme_callback(update, context):
    query = update.callback_query
    await query.answer()
    data = load()
    user = get_user(data, query.from_user.id)
    theme_name = query.data.replace("theme_", "")
    user["theme"] = theme_name
    save(data)
    themes_fa = {"classic":"کلاسیک","fire":"آتش","ice":"یخ","gold":"طلا"}
    await query.edit_message_text(f"✅ پوسته *{themes_fa.get(theme_name,theme_name)}* انتخاب شد!", parse_mode="Markdown")

async def show_stats(update, context):
    data = load()
    user = get_user(data, update.effective_user.id)
    winrate = int((user["wins"]/user["games"])*100) if user["games"] > 0 else 0
    all_scores = sorted([u["score"] for u in data["users"].values()], reverse=True)
    rank = all_scores.index(user["score"])+1 if user["score"] in all_scores else "-"
    await update.message.reply_text(
        f"📊 *آمار {user['name']}*\n\n"
        f"💎 امتیاز: *{user['score']}*\n"
        f"🥇 رتبه: *#{rank}*\n"
        f"🎮 بازی‌ها: *{user['games']}*\n"
        f"✅ بردها: *{user['wins']}*\n"
        f"📈 درصد برد: *{winrate}٪*\n"
        f"🔥 رشته برد: *{user['streak']}*\n"
        f"⚡ بهترین رشته: *{user['best_streak']}*\n"
        f"💰 سکه: *{user['coins']}*",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

async def leaderboard(update, context):
    data = load()
    uid = str(update.effective_user.id)
    sorted_users = sorted(data["users"].items(), key=lambda x: x[1]["score"], reverse=True)[:10]
    medals = ["🥇","🥈","🥉"]+["🏅"]*7
    lines = ["🏆 *جدول برترین‌ها*\n"]
    for i,(user_id,u) in enumerate(sorted_users):
        marker = " ◀️" if user_id==uid else ""
        lines.append(f"{medals[i]} *{u.get('name','بازیکن')}* — {u['score']} 💎{marker}")
    if not sorted_users:
        lines.append("هنوز کسی بازی نکرده!")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown", reply_markup=main_keyboard())

async def help_cmd(update, context):
    await update.message.reply_text(
        "📖 *راهنما*\n\n"
        "🟩 حرف درست، جای درست\n"
        "🟨 حرف درست، جای اشتباه\n"
        "⬛ حرف اشتباه\n\n"
        f"۶ تلاش داری!\n\n"
        "💰 *سکه:*\n"
        "با برد سکه جمع میکنی\n"
        "با سکه میتونی راهنمایی بگیری\n\n"
        "⚔️ *رقابت آنلاین:*\n"
        "با یه حریف همزمان بازی کن\n"
        "هر کی زودتر پیدا کرد برنده‌ست!",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

async def handle(update, context):
    data = load()
    uid = update.effective_user.id
    user = get_user(data, uid)
    text = update.message.text.strip()

    if text == "🎮 بازی جدید": await new_game(update, context); return
    if text == "📅 چالش روزانه": await daily(update, context); return
    if text == "⚔️ رقابت آنلاین": await online_match(update, context); return
    if text == "🏆 جدول برترین‌ها": await leaderboard(update, context); return
    if text == "💰 کیف پول": await show_wallet(update, context); return
    if text == "🎨 پوسته‌ها": await show_themes(update, context); return
    if text == "📊 آمار من": await show_stats(update, context); return
    if text == "📖 راهنما": await help_cmd(update, context); return
    if text == "🏳️ تسلیم":
        game = user.get("current_game")
        if game:
            user["current_game"] = None
            user["streak"] = 0
            save(data)
            await update.message.reply_text(f"🏳️ تسلیم شدی!\nکلمه: *{game['word']}*", parse_mode="Markdown", reply_markup=main_keyboard())
        return
    if text == "💡 راهنمایی (۵ سکه)":
        game = user.get("current_game")
        if not game:
            await update.message.reply_text("اول بازی رو شروع کن!", reply_markup=main_keyboard())
            return
        if user["coins"] < 5:
            await update.message.reply_text(f"💰 سکه کافی نداری! سکه‌های تو: {user['coins']}", reply_markup=letter_keyboard())
            return
        secret = game["word"]
        guessed = set()
        for g,r in game["guesses"]:
            for ch,st in r:
                if st == "green": guessed.add(ch)
        remaining = [c for c in secret if c not in guessed]
        if remaining:
            hint_char = random.choice(remaining)
            user["coins"] -= 5
            save(data)
            await update.message.reply_text(f"💡 یه حرف از کلمه: *{hint_char}*\n💰 ۵ سکه کم شد", parse_mode="Markdown", reply_markup=letter_keyboard())
        return

    game = user.get("current_game")
    if not game:
        await update.message.reply_text("برای شروع روی 🎮 بازی جدید بزن!", reply_markup=main_keyboard())
        return

    buf = game.get("typing_buffer", "")
    
    if text == "◀️ پاک":
        game["typing_buffer"] = buf[:-1] if buf else ""
        save(data)
        await update.message.reply_text(f"✏️ کلمه فعلی: *{game['typing_buffer']}*" if game["typing_buffer"] else "✏️ خالی", parse_mode="Markdown", reply_markup=letter_keyboard())
        return

    if len(text) == 1 and text not in ["🎮","📅","⚔️","🏆","💰","🎨","📊","📖","🏳️","💡"]:
        buf += text
        game["typing_buffer"] = buf
        secret = game["word"]
        
        if len(buf) < len(secret):
            save(data)
            await update.message.reply_text(f"✏️ *{buf}*  ({len(buf)}/{len(secret)})", parse_mode="Markdown", reply_markup=letter_keyboard())
            return
        elif len(buf) == len(secret):
            guess = buf
            game["typing_buffer"] = ""
        else:
            game["typing_buffer"] = buf
            save(data)
            return
    elif len(text) > 1 and all(c in "ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی" for c in text):
        guess = text
        game["typing_buffer"] = ""
    else:
        save(data)
        return

    secret = game["word"]
    if len(guess) != len(secret):
        await update.message.reply_text(f"❌ کلمه باید {len(secret)} حرف باشه!", reply_markup=letter_keyboard())
        return

    result = check_guess(secret, guess)
    game["guesses"].append((guess, result))
    tries = len(game["guesses"])
    theme = get_theme(user)
    board = render_board(game["guesses"], theme, len(secret))
    won = all(s=="green" for _,s in result)

    if won:
        scores = {1:100,2:80,3:60,4:40,5:20,6:10}
        earned_score = scores.get(tries,10)
        coins = 10
        if game.get("mode") == "daily":
            earned_score = int(earned_score*1.5)
            coins = 50
        elif game.get("mode") == "online":
            coins = 25
            earned_score = int(earned_score*2)
            opp_id = game.get("opponent")
            if opp_id:
                try:
                    await context.bot.send_message(
                        chat_id=int(opp_id),
                        text=f"😔 حریفت زودتر پیدا کرد!\nکلمه: *{secret}*",
                        parse_mode="Markdown",
                        reply_markup=main_keyboard()
                    )
                    opp_data = load()
                    opp_user = get_user(opp_data, int(opp_id))
                    opp_user["current_game"] = None
                    save(opp_data)
                except:
                    pass
        
        user["score"] += earned_score
        user["wins"] += 1
        user["coins"] += coins
        user["streak"] += 1
        if user["streak"] > user["best_streak"]:
            user["best_streak"] = user["streak"]
        if game.get("mode") == "daily":
            user["daily_date"] = str(date.today())
        user["current_game"] = None
        save(data)
        
        stars = "⭐" * tries
        await update.message.reply_text(
            f"{board}\n\n"
            f"🎉 *آفرین! پیدا کردی!*\n\n"
            f"کلمه: *{secret}*\n"
            f"تلاش: {tries} از {MAX_TRIES}\n"
            f"امتیاز: +{earned_score} 💎\n"
            f"سکه: +{coins} 🪙\n"
            f"رشته برد: {user['streak']} 🔥\n\n{stars}",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
    elif tries >= MAX_TRIES:
        user["streak"] = 0
        user["current_game"] = None
        save(data)
        await update.message.reply_text(
            f"{board}\n\n😔 *بازی تموم شد!*\n\nکلمه: *{secret}*\nدوباره تلاش کن! 💪",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
    else:
        save(data)
        remaining = MAX_TRIES - tries
        await update.message.reply_text(
            f"{board}\n\n_(تلاش {tries+1} از {MAX_TRIES} | {remaining} تلاش مانده)_",
            parse_mode="Markdown",
            reply_markup=letter_keyboard()
        )

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CallbackQueryHandler(theme_callback, pattern="^theme_"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
print("🤖 واژه‌یاب شروع شد!")
app.run_polling()
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
