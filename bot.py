from reminder_bot import CryptoReminderBot
import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN") 

if __name__ == "__main__":
    bot = CryptoReminderBot(BOT_TOKEN)
    bot.run()

# я работал как со списком, а переделал на словарь, и все сломалось

