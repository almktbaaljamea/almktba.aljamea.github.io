from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import pandas as pd
from collections import defaultdict

TOKEN = "8637755299:AAHzpRhO5RYntkgMzvUZAgGuPQRPpcZIXdo"

def search(book):
    df = pd.read_excel("books.xlsx")
    result = df[df["book_name"].str.contains(book, case=False, na=False)]
    return result.values.tolist()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("افتح التطبيق", web_app=WebAppInfo(url="https://almktbaaljamea.github.io/almktba_aljamea.github.io/"))]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "اكتب اسم الكتاب أو افتح التطبيق:",
        reply_markup=reply_markup
    )

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    results = search(query)

    if results:
        data = defaultdict(lambda: defaultdict(list))

        for r in results:
            publisher = r[1]
            library = r[2]
            city = r[3]
            price = r[4]

            data[city][library].append((publisher, price))

        max_city_len = max(len(city) for city in data.keys())

        text = "📚 النتائج:\n\n```text\n"

        for city, libraries in data.items():
            first_row = True

            for lib, items in libraries.items():

                if first_row:
                    city_col = city.ljust(max_city_len)
                    first_row = False
                else:
                    city_col = " " * max_city_len

                details = []
                for pub, price in items:
                    details.append(f"{pub}:{price}💰")

                data_col = " , ".join(details)

                line = f"{city_col} │ {lib} │ {data_col}"

                text += line + "\n"

            text += "\n"

        text += "```"
    else:
        text = "ما في نتائج"

    await update.message.reply_text(text)

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

app.run_polling()