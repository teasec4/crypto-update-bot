from reminder_bot import CryptoReminderBot
import os

BOT_TOKEN = os.getenv("BOT_TOKEN") 

if __name__ == "__main__":
    bot = CryptoReminderBot(BOT_TOKEN)
    bot.run()