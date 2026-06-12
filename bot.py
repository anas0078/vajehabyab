import os
import json
import random
from datetime import date
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
    "کتاب", "درخت", "زمین", "شهر", "کوه", "دریا", "برف", "خانه",
    "میوه", "بهار", "پاییز", "زمستان", "مدرسه", "بازار", "پرنده",
    "باغبان", "نقاشی", "موسیقی", "دانشجو", "ورزشکار", "آشپزی",
    "ساختمان", "بیمارستان", "داروخانه", "فروشگاه", "رستوران",
    "کتابخانه", "دوچرخه", "ماهیگیر", "گلدان", "ستاره", "تابستان",
    "فوتبال", "معلمان", "دانشگاه", "آسمان", "روشنایی", "تاریکی",
    "خورشید", "باران", "باغچه", "گلستان", "چراغ", "پنجره", "درب"
]

DAILY_WORDS = ["کتاب", "درخت", "زمین", "شهر", "کوه", "دریا", "برف", "خانه",
               "میوه", "بهار", "پاییز", "زمستان", "مدرسه", "بازار", "پرنده"]

THEMES = {
    "classic": {"g": "🟩", "y": "🟨", "gr": "⬛"},
    "fire":    {"g": "🔴", "y": "🟠", "gr": "⬫"},
    "ice":     {"g": "🔵", "y": "🩵", "gr": "⬜"},
    "gold":    {"g": "🥇", "y": "🥈", "gr": "🥉"},
}

def load():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"users": {}, "queue": [], "matches": {}}

def save(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(data, uid):
    uid = str(uid)
    if uid not in data["users"]:
        data["users"][uid] = {
            "name": "بازیکن",
            "score": 0,
            "coins": 10,
            "wins": 0,
            "games": 0,
            "streak": 0,
            "best_streak": 0,
            "current_game": None,
            "theme": "classic",
            "daily_date": None,
            "buf": ""
        }
    return data["users"][uid]

def get_t(user):
    return THEMES.get(user.get("theme", "classic"), THEMES["classic"])

def check_guess(secret, guess):
    statuses = [None] * len(guess)
    used = [False] * len(secret)
    for i, (g, s) in enumerate(zip(guess, secret)):
        if g == s:
            statuses[i] = "g"
            used[i] = True
    for i, g in enumerate(guess):
        if statuses[i]:
            continue
        for j, s in enumerate(secret):
            if not used[j] and g == s:
                statuses[i] = "y"
                used[j] = True
                break
        if not statuses[i]:
            statuses[i] = "gr"
    return list(zip(guess, statuses))

def render(guesses, t, slen):
    lines = []
    for guess, result in guesses:
        row = ""
        for char, status in result:
            row += t["g"] if status == "g" else t["y"] if status == "y" else t["gr"]
        lines.append(row + "  `" + guess + "`")
    for _ in range(MAX_TRIES - len(guesses)):
        lines.append(EMPTY * slen)
    return "\n".join(lines)

def main_kb():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🎮 بازی جدید"), KeyboardButton("📅 چالش روزانه")],
        [KeyboardButton("⚔️ رقابت آنلاین"), KeyboardButton("🏆 جدول برترین‌ها")],
        [KeyboardButton("💰 کیف پول"), KeyboardButton("🎨 پوسته‌ها")],
        [KeyboardButton("📊 آمار من"), KeyboardButton("📖 راهنما")]
    ], resize_keyboard=True)

def letter_kb():
    return ReplyKeyboardMarkup([
        [KeyboardButton("ا"), KeyboardButton("ب"), KeyboardButton("پ"), KeyboardButton("ت"), KeyboardButton("ث"), KeyboardButton("ج"), KeyboardButton("چ")],
        [KeyboardButton("ح"), KeyboardButton("خ"), KeyboardButton("د"), KeyboardButton("ذ"), KeyboardButton("ر"), KeyboardButton("ز"), KeyboardButton("ژ")],
        [KeyboardButton("س"), KeyboardButton("ش"), KeyboardButton("ص"), KeyboardButton("ض"), KeyboardButton("ط"), KeyboardButton("ظ"), KeyboardButton("ع")],
        [KeyboardButton("غ"), KeyboardButton("ف"), KeyboardButton("ق"), KeyboardButton("ک"), KeyboardButton("گ"), KeyboardButton("ل"), KeyboardButton("م")],
        [KeyboardButton("ن"), KeyboardButton("و"), KeyboardButton("ه"), KeyboardButton("ی"), KeyboardButton("◀️ پاک"), KeyboardButton("✅ تایید")],
        [KeyboardButton("🏳️ تسلیم"), KeyboardButton("💡 راهنمایی (۵ سکه)")]
    ], resize_keyboard=True)

async def start(update, context):
    data = load()
    uid = update.effective_user.id
    user = get_user(data, uid)
    user["name"] = update.effective_user.first_name or "بازیکن"
    save(data)
    await update.message.reply_text(
        f"سلام {user['name']} عزیز! 👋\n\n"
        "🟩 به *واژه‌یاب* خوش اومدی!\n\n"
        f"💰 سکه: {user['coins']} 🪙\n\n"
        "🟩 حرف درست، جای درست\n"
        "🟨 حرف درست، جای اشتباه\n"
        "⬛ حرف اشتباه\n\n"
        "از منو یه گزینه انتخاب کن 👇",
        parse_mode="Markdown",
        reply_markup=main_kb()
    )

async def new_game(update, context):
    data = load()
    uid = update.effective_user.id
    user = get_user(data, uid)
    word = random.choice(WORDS)
    user["current_game"] = {"word": word, "guesses": [], "mode": "normal"}
    user["buf"] = ""
    user["games"] += 1
    save(data)
    t = get_t(user)
    board = render([], t, len(word))
    await update.message.reply_text(
        f"🎮 *بازی جدید!*\n\n{board}\n\n"
        f"کلمه {len(word)} حرفی رو حدس بزن 👇\n"
        f"_(تلاش ۱ از {MAX_TRIES})_",
        parse_mode="Markdown",
        reply_markup=letter_kb()
    )

async def daily(update, context):
    data = load()
    uid = update.effective_user.id
    user = get_user(data, uid)
    today = str(date.today())
    if user["daily_date"] == today:
        await update.message.reply_text("📅 امروز قبلاً بازی کردی!\nفردا برگرد 🌅", reply_markup=main_kb())
        return
    random.seed(today)
    word = random.choice(DAILY_WORDS)
    random.seed()
    user["current_game"] = {"word": word, "guesses": [], "mode": "daily"}
    user["buf"] = ""
    save(data)
    t = get_t(user)
    board = render([], t, len(word))
    await update.message.reply_text(
        f"📅 *چالش روزانه!*\n\n{board}\n\n"
        f"کلمه {len(word)} حرفی بنویس 👇",
        parse_mode="Markdown",
        reply_markup=letter_kb()
    )

async def online_match(update, context):
    data = load()
    uid = str(update.effective_user.id)
    user = get_user(data, update.effective_user.id)
    if "queue" not in data:
        data["queue"] = []
    if uid in data["queue"]:
        await update.message.reply_text("⏳ داری منتظر حریف میمونی...", reply_markup=main_kb())
        return
    queue = data["queue"]
    if queue and queue[0] != uid:
        opp_id = queue.pop(0)
        word = random.choice(WORDS)
        opp_user = get_user(data, int(opp_id))
        opp_user["current_game"] = {"word": word, "guesses": [], "mode": "online", "opp": uid}
        opp_user["buf"] = ""
        user["current_game"] = {"word": word, "guesses": [], "mode": "online", "opp": opp_id}
        user["buf"] = ""
        data["queue"] = queue
        save(data)
        t = get_t(user)
        board = render([], t, len(word))
        msg = f"⚔️ *حریف پیدا شد!*\n\n{board}\n\nکلمه {len(word)} حرفی رو حدس بزن 🔥"
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=letter_kb())
        try:
            await context.bot.send_message(chat_id=int(opp_id), text=msg, parse_mode="Markdown", reply_markup=letter_kb())
        except Exception:
            pass
    else:
        data["queue"] = queue + [uid]
        save(data)
        await update.message.reply_text("⏳ *دنبال حریف میگردم...*\nصبر کن! 🔍", parse_mode="Markdown", reply_markup=main_kb())

async def wallet(update, context):
    data = load()
    user = get_user(data, update.effective_user.id)
    await update.message.reply_text(
        f"💰 *کیف پول*\n\nسکه: {user['coins']} 🪙\n\n"
        "*خرید با سکه:*\n"
        "💡 راهنمایی = ۵ سکه\n"
        "🔤 نشون دادن کلمه = ۳۰ سکه\n\n"
        "*کسب سکه:*\n"
        "✅ برد = ۱۰ سکه\n"
        "⚔️ برد آنلاین = ۲۵ سکه\n"
        "📅 چالش روزانه = ۵۰ سکه",
        parse_mode="Markdown",
        reply_markup=main_kb()
    )

async def themes(update, context):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🟩 کلاسیک", callback_data="th_classic"),
         InlineKeyboardButton("🔴 آتش", callback_data="th_fire")],
        [InlineKeyboardButton("🔵 یخ", callback_data="th_ice"),
         InlineKeyboardButton("🥇 طلا", callback_data="th_gold")]
    ])
    await update.message.reply_text("🎨 *پوسته انتخاب کن:*", parse_mode="Markdown", reply_markup=kb)

async def theme_cb(update, context):
    query = update.callback_query
    await query.answer()
    data = load()
    user = get_user(data, query.from_user.id)
    th = query.data.replace("th_", "")
    user["theme"] = th
    save(data)
    names = {"classic": "کلاسیک", "fire": "آتش", "ice": "یخ", "gold": "طلا"}
    await query.edit_message_text(f"✅ پوسته *{names.get(th, th)}* انتخاب شد!", parse_mode="Markdown")

async def stats(update, context):
    data = load()
    user = get_user(data, update.effective_user.id)
    uid = str(update.effective_user.id)
    wr = int((user["wins"] / user["games"]) * 100) if user["games"] > 0 else 0
    scores = sorted([u["score"] for u in data["users"].values()], reverse=True)
    rank = scores.index(user["score"]) + 1 if user["score"] in scores else "-"
    await update.message.reply_text(
        f"📊 *آمار {user['name']}*\n\n"
        f"💎 امتیاز: *{user['score']}*\n"
        f"🥇 رتبه: *#{rank}*\n"
        f"🎮 بازی‌ها: *{user['games']}*\n"
        f"✅ بردها: *{user['wins']}*\n"
        f"📈 درصد برد: *{wr}٪*\n"
        f"🔥 رشته برد: *{user['streak']}*\n"
        f"⚡ بهترین رشته: *{user['best_streak']}*\n"
        f"💰 سکه: *{user['coins']}*",
        parse_mode="Markdown",
        reply_markup=main_kb()
    )

async def lb(update, context):
    data = load()
    uid = str(update.effective_user.id)
    top = sorted(data["users"].items(), key=lambda x: x[1]["score"], reverse=True)[:10]
    medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
    lines = ["🏆 *جدول برترین‌ها*\n"]
    for i, (user_id, u) in enumerate(top):
        marker = " ◀️" if user_id == uid else ""
        lines.append(f"{medals[i]} *{u.get('name', 'بازیکن')}* — {u['score']} 💎{marker}")
    if not top:
        lines.append("هنوز کسی بازی نکرده!")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown", reply_markup=main_kb())

async def help_cmd(update, context):
    await update.message.reply_text(
        "📖 *راهنما*\n\n"
        "🟩 حرف درست، جای درست\n"
        "🟨 حرف درست، جای اشتباه\n"
        "⬛ حرف اشتباه\n\n"
        f"۶ تلاش داری!\n\n"
        "از کیبورد حروف بزن، بعد ✅ تایید بزن\n\n"
        "💰 *سکه:*\n"
        "با برد سکه جمع میکنی\n"
        "با سکه راهنمایی بگیر\n\n"
        "⚔️ *آنلاین:*\n"
        "با حریف تصادفی بازی کن!",
        parse_mode="Markdown",
        reply_markup=main_kb()
    )

async def handle(update, context):
    data = load()
    uid = update.effective_user.id
    user = get_user(data, uid)
    text = update.message.text.strip()

    if text == "🎮 بازی جدید":
        await new_game(update, context)
        return
    if text == "📅 چالش روزانه":
        await daily(update, context)
        return
    if text == "⚔️ رقابت آنلاین":
        await online_match(update, context)
        return
    if text == "🏆 جدول برترین‌ها":
        await lb(update, context)
        return
    if text == "💰 کیف پول":
        await wallet(update, context)
        return
    if text == "🎨 پوسته‌ها":
        await themes(update, context)
        return
    if text == "📊 آمار من":
        await stats(update, context)
        return
    if text == "📖 راهنما":
        await help_cmd(update, context)
        return

    if text == "🏳️ تسلیم":
        game = user.get("current_game")
        if game:
            user["current_game"] = None
            user["streak"] = 0
            user["buf"] = ""
            save(data)
            await update.message.reply_text(f"🏳️ تسلیم شدی!\nکلمه: *{game['word']}*", parse_mode="Markdown", reply_markup=main_kb())
        else:
            await update.message.reply_text("بازی شروع نشده!", reply_markup=main_kb())
        return

    if text == "💡 راهنمایی (۵ سکه)":
        game = user.get("current_game")
        if not game:
            await update.message.reply_text("اول بازی رو شروع کن!", reply_markup=main_kb())
            return
        if user["coins"] < 5:
            await update.message.reply_text(f"سکه کافی نداری! سکه: {user['coins']}", reply_markup=letter_kb())
            return
        secret = game["word"]
        found = set()
        for g, r in game["guesses"]:
            for ch, st in r:
                if st == "g":
                    found.add(ch)
        rest = [c for c in secret if c not in found]
        if rest:
            hint = random.choice(rest)
            user["coins"] -= 5
            save(data)
            await update.message.reply_text(f"💡 یه حرف از کلمه: *{hint}*\n💰 ۵ سکه کم شد", parse_mode="Markdown", reply_markup=letter_kb())
        return

    game = user.get("current_game")
    if not game:
        await update.message.reply_text("برای شروع روی 🎮 بازی جدید بزن!", reply_markup=main_kb())
        return

    secret = game["word"]
    buf = user.get("buf", "")

    if text == "◀️ پاک":
        user["buf"] = buf[:-1] if buf else ""
        save(data)
        cur = user["buf"]
        msg = f"✏️ *{cur}*  ({len(cur)}/{len(secret)})" if cur else "✏️ خالی"
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=letter_kb())
        return

    if text == "✅ تایید":
        if len(buf) != len(secret):
            await update.message.reply_text(f"❌ کلمه باید {len(secret)} حرف باشه!\nالان: {len(buf)} حرف", reply_markup=letter_kb())
            return
        guess = buf
        user["buf"] = ""
        result = check_guess(secret, guess)
        game["guesses"].append((guess, result))
        tries = len(game["guesses"])
        t = get_t(user)
        board = render(game["guesses"], t, len(secret))
        won = all(s == "g" for _, s in result)

        if won:
            sc = {1: 100, 2: 80, 3: 60, 4: 40, 5: 20, 6: 10}
            earned = sc.get(tries, 10)
            coins = 10
            if game.get("mode") == "daily":
                earned = int(earned * 1.5)
                coins = 50
                user["daily_date"] = str(date.today())
            elif game.get("mode") == "online":
                earned = int(earned * 2)
                coins = 25
                opp_id = game.get("opp")
                if opp_id:
                    try:
                        await context.bot.send_message(
                            chat_id=int(opp_id),
                            text=f"😔 حریفت زودتر پیدا کرد!\nکلمه: *{secret}*",
                            parse_mode="Markdown",
                            reply_markup=main_kb()
                        )
                        opp_data = load()
                        opp_u = get_user(opp_data, int(opp_id))
                        opp_u["current_game"] = None
                        opp_u["buf"] = ""
                        save(opp_data)
                    except Exception:
                        pass
            user["score"] += earned
            user["wins"] += 1
            user["coins"] += coins
            user["streak"] += 1
            if user["streak"] > user["best_streak"]:
                user["best_streak"] = user["streak"]
            user["current_game"] = None
            save(data)
            await update.message.reply_text(
                f"{board}\n\n🎉 *آفرین! پیدا کردی!*\n\n"
                f"کلمه: *{secret}*\n"
                f"تلاش: {tries} از {MAX_TRIES}\n"
                f"امتیاز: +{earned} 💎\n"
                f"سکه: +{coins} 🪙\n"
                f"رشته برد: {user['streak']} 🔥",
                parse_mode="Markdown",
                reply_markup=main_kb()
            )
        elif tries >= MAX_TRIES:
            user["streak"] = 0
            user["current_game"] = None
            save(data)
            await update.message.reply_text(
                f"{board}\n\n😔 *بازی تموم شد!*\n\nکلمه: *{secret}*\nدوباره تلاش کن! 💪",
                parse_mode="Markdown",
                reply_markup=main_kb()
            )
        else:
            save(data)
            rem = MAX_TRIES - tries
            await update.message.reply_text(
                f"{board}\n\n_(تلاش {tries + 1} از {MAX_TRIES} | {rem} تلاش مانده)_\n✏️ *{user['buf']}*" if user.get("buf") else f"{board}\n\n_(تلاش {tries + 1} از {MAX_TRIES} | {rem} تلاش مانده)_",
                parse_mode="Markdown",
                reply_markup=letter_kb()
            )
        return

    persian_chars = set("ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی")
    if len(text) == 1 and text in persian_chars:
        buf += text
        user["buf"] = buf
        save(data)
        await update.message.reply_text(
            f"✏️ *{buf}*  ({len(buf)}/{len(secret)})",
            parse_mode="Markdown",
            reply_markup=letter_kb()
        )
        return

    if len(text) > 1 and all(c in persian_chars for c in text):
        user["buf"] = ""
        save(data)
        if len(text) != len(secret):
            await update.message.reply_text(f"❌ کلمه باید {len(secret)} حرف باشه!", reply_markup=letter_kb())
            return
        guess = text
        result = check_guess(secret, guess)
        game["guesses"].append((guess, result))
        tries = len(game["guesses"])
        t = get_t(user)
        board = render(game["guesses"], t, len(secret))
        won = all(s == "g" for _, s in result)
        if won:
            sc = {1: 100, 2: 80, 3: 60, 4: 40, 5: 20, 6: 10}
            earned = sc.get(tries, 10)
            coins = 10
            user["score"] += earned
            user["wins"] += 1
            user["coins"] += coins
            user["streak"] += 1
            if user["streak"] > user["best_streak"]:
                user["best_streak"] = user["streak"]
            user["current_game"] = None
            save(data)
            await update.message.reply_text(
                f"{board}\n\n🎉 *آفرین!*\n\nکلمه: *{secret}*\nامتیاز: +{earned} 💎",
                parse_mode="Markdown",
                reply_markup=main_kb()
            )
        elif tries >= MAX_TRIES:
            user["streak"] = 0
            user["current_game"] = None
            save(data)
            await update.message.reply_text(
                f"{board}\n\n😔 کلمه: *{secret}*",
                parse_mode="Markdown",
                reply_markup=main_kb()
            )
        else:
            save(data)
            await update.message.reply_text(
                f"{board}\n\n_(تلاش {tries + 1} از {MAX_TRIES})_",
                parse_mode="Markdown",
                reply_markup=letter_kb()
            )

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CallbackQueryHandler(theme_cb, pattern="^th_"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
print("🤖 واژه‌یاب v2 شروع شد!")
app.run_polling()    ["س","ش","ص","ض","ط","ظ","ع"],
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
