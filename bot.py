import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes
load_dotenv()
TOKEN=os.getenv("BOT_TOKEN","")
WEBAPP=os.getenv("WEBAPP_URL","")
async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if not WEBAPP.startswith("https://"):
        await update.message.reply_text("Mini App URL সেটআপ করা হয়নি। WEBAPP_URL-এ HTTPS URL দিন।")
        return
    keyboard=[[InlineKeyboardButton("🐔 Open CHIKEN USDT",web_app=WebAppInfo(url=WEBAPP))]]
    await update.message.reply_text("🐔 Welcome to CHIKEN USDT!\n\nOpen your farm using the button below.",reply_markup=InlineKeyboardMarkup(keyboard))
async def help_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Start the bot and tap Open CHIKEN USDT.")
def main():
    if not TOKEN: raise SystemExit("BOT_TOKEN missing in .env")
    app=Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start",start));app.add_handler(CommandHandler("help",help_cmd))
    app.run_polling()
if __name__=="__main__": main()
