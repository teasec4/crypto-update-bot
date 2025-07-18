from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from crypto_utils import get_price, get_top_coins
from datetime import time as dtime
import pytz
import logging
import re
from db import get_user, get_all_users, save_user, remove_user, init_db
from json_migrate_to_db import migrate_from_json

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("crypto_reminder_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CryptoReminderBot:
    def __init__(self, token):
        self.app = (
            ApplicationBuilder()
            .token(token)
            .post_init(self.setup_jobs)
            .build()
        )
        self._register_handlers()
        self.alerted_coins = set()

    def _register_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("price", self.price))
        self.app.add_handler(CommandHandler("help", self.help))
        self.app.add_handler(CommandHandler("subscribe", self.subscribe))
        self.app.add_handler(CommandHandler("unsubscribe", self.unsubscribe))
        self.app.add_handler(CommandHandler("testmorning", self.test_morning))
        self.app.add_handler(CallbackQueryHandler(self.button_handler))
        self.app.add_handler(CommandHandler("settimezone", self.change_timezone))
        self.app.add_handler(CommandHandler("setcoins", self.set_coins))
        self.app.add_handler(CommandHandler("settime", self.set_time))
        # Handle unknown commands
        self.app.add_handler(MessageHandler(filters.COMMAND, self.unknown_command))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Welcome to Crypto Reminder Bot!\nUse /help to see available commands. \nAnd also use /subscribe"
        )

    async def price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Please specify one or more coin IDs, e.g., /price bitcoin eth or type /help for help")
            return

        coin_ids = [coin.lower() for coin in context.args]
        prices = get_price(",".join(coin_ids))

        for coin in coin_ids:
            data = prices.get(coin)
            if data:
                change = data['change_24h']
                if change > 0:
                    emoji = "📈"
                elif change < 0:
                    emoji = "📉"
                msg = (
                    f"{coin.upper()}\n"
                    f"Price: ${data['usd']:,.2f}\n"
                    f"24h Change: {emoji} {data['change_24h']:.2f}%\n"
                    f"Market Cap: ${data['market_cap']:,.0f}\n"
                )
                await update.message.reply_text(msg, parse_mode="HTML", disable_web_page_preview=False)
            else:
                await update.message.reply_text(f"❌ '{coin}' not found.")

        if any(prices.get(coin) is None for coin in coin_ids):
            top_coins = get_top_coins()
            await update.message.reply_text("📈 Top 10 Coin IDs:\n" + ", ".join(top_coins))

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = (
            "📘 <b>Crypto Reminder Bot Help</b>\n\n"
            "Here are the available commands:\n\n"
            "🟢 <b>/start</b> — Start the bot and see a welcome message.\n"
            "🟢 <b>/price &lt;coin_id&gt;</b> — Get the price, market cap, and 24h change.\n"
            "  <i>Example:</i> <code>/price bitcoin eth</code>\n\n"
            "🟢 <b>/subscribe</b> — Subscribe to daily crypto updates.\n"
            "🟢 <b>/unsubscribe</b> — Stop receiving daily updates.\n\n"
            "🟢 <b>/settimezone</b> — Change your timezone for daily updates.\n"
            "🟢 <b>/setcoins &lt;coin_ids&gt;</b> — Choose which coins to include.\n"
            "  <i>Example:</i> <code>/setcoins bitcoin eth dogecoin</code>\n\n"
            "🟢 <b>/settime &lt;HH:MM&gt;</b> — Set your preferred daily update time.\n"
            "  <i>Example:</i> <code>/settime 09:30</code>\n\n"
            "🟢 <b>/testmorning</b> — Test the morning message immediately.\n\n"
            "💡 <b>Tip:</b> Use coin IDs like <code>bitcoin</code>, <code>ethereum</code>, <code>dogecoin</code>.\n"
            "❓ If you see strange output, check your coin ID spelling.\n"
        )
        await update.message.reply_text(text, parse_mode="HTML")

    async def subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = str(update.effective_chat.id)
        user = get_user(chat_id)
        if user:
            await update.message.reply_text("📬 You're already subscribed.")
        else:
            save_user(chat_id, "Asia/Shanghai",["bitcoin", "ethereum", "dogecoin"], '08:00')
            await self.setup_jobs(self.app)
            await update.message.reply_text("✅ You've subscribed to daily updates.")
       

    async def unsubscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = str(update.effective_chat.id)
        if remove_user(chat_id):
            if self.app.job_queue:
                jobs = self.app.job_queue.get_jobs_by_name(f"daily_morning_reminder_{chat_id}")
                for job in jobs:
                    job.schedule_removal()
                logger.info(f"Removed job for chat {chat_id}")
            await update.message.reply_text("🚫 You've unsubscribed.")
        else:
            await update.message.reply_text("❌ You weren't subscribed.")

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data
        chat_id = str(update.effective_chat.id)
        # get data from button

        # subscribe button handler       
        if data == "subscribe":
            user = get_user(chat_id)
            if user:
                await query.message.reply_text("📬 You're already subscribed.")
            else:
                save_user(chat_id, "Asia/Shanghai", ["bitcoin", "ethereum", "dogecoin"], "08:00")
                await self.setup_jobs(self.app)
                await query.message.reply_text("✅ You've subscribed to daily updates.")
        # unsubscribe button handler
        elif data == "unsubscribe":
            if remove_user(chat_id):
                if self.app.job_queue:
                    jobs = self.app.job_queue.get_jobs_by_name(f"daily_morning_reminder_{chat_id}")
                    for job in jobs:
                        job.schedule_removal()
                    logger.info(f"Removed job for chat {chat_id}")
                await query.message.reply_text("🚫 Unsubscribed via button.")
            else:
                await query.message.reply_text("❌ You weren't subscribed.")
        elif data.startswith("tz_"):
            tz = data.replace("tz_", "")
            user = get_user(chat_id)
            if user:
                save_user(chat_id, tz, user['coins'], user['time'])
                if self.app.job_queue:
                    jobs = self.app.job_queue.get_jobs_by_name(f"daily_morning_reminder_{chat_id}")
                    for job in jobs:
                        job.schedule_removal()
                    hour, minute = map(int, user['time'].split(":"))
                    tz_obj = pytz.timezone(tz)
                    self.app.job_queue.run_daily(
                        callback=self.morning_reminder,
                        time=dtime(hour=hour, minute=minute, tzinfo=tz_obj),
                        name=f"daily_morning_reminder_{chat_id}",
                        data={"chat_id": int(chat_id)}
                    )
                    logger.info(f"Rescheduled reminder for chat {chat_id} in timezone {tz}")
                await query.message.reply_text(f"🌍 Timezone changed to {tz.replace('_', ' ')} for daily reminders.")
            else:
                await query.message.reply_text("❌ You need to subscribe first to change timezone.")

    async def morning_reminder(self, context: ContextTypes.DEFAULT_TYPE):
        chat_id = str(context.job.data['chat_id'])
        user = get_user(chat_id)
        if not user:
            logger.warning(f"No configuration found for chat {chat_id}")
            return

        coins = user.get('coins', ['bitcoin', 'ethereum', 'dogecoin'])
        prices = get_price(",".join(coins))

        lines = ["🌅 Morning Crypto Update\n"]
        for coin in coins:
            data = prices.get(coin)
            if data:
                emoji = "🔺" if data['change_24h'] >= 0 else "🔻"
                lines.append(f"{coin.upper()}: ${data['usd']:,.2f} {emoji}{data['change_24h']:.1f}%")

        message = "\n".join(lines)
        await context.bot.send_message(chat_id=chat_id, text=message)

    async def test_morning(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = str(update.effective_chat.id)
        fake_context = type("ctx", (), {
            "bot": context.bot,
            "job": type("job", (), {"data": {"chat_id": chat_id}})
        })
        await self.morning_reminder(fake_context)

    async def change_timezone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("🇨🇳 Asia/Shanghai", callback_data="tz_Asia/Shanghai")],
            [InlineKeyboardButton("🇯🇵 Asia/Tokyo", callback_data="tz_Asia/Tokyo")],
            [InlineKeyboardButton("🇷🇺 Europe/Moscow", callback_data="tz_Europe/Moscow")],
            [InlineKeyboardButton("🇩🇪 Europe/Berlin", callback_data="tz_Europe/Berlin")],
            [InlineKeyboardButton("🇺🇸 America/New_York", callback_data="tz_America/New_York")],
        ]
        await update.message.reply_text(
            "🌍 Choose your timezone for daily reminders:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def set_coins(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = str(update.effective_chat.id)
        if not context.args:
            await update.message.reply_text("❌ Please specify coin IDs. Example: /setcoins bitcoin eth doge")
            return
        coins = [coin.lower() for coin in context.args]
        valid_coins, invalid_coins = self._validate_coins(coins)

        if not valid_coins:
            msg = "❌ None of the provided coin IDs are valid. Please try again."
            top_coins = get_top_coins()
            msg += f"\n📈 Top 10 Coin IDs: {', '.join(top_coins)}"
            await update.message.reply_text(msg)
            return

        try:
            user = get_user(chat_id)
            if not user:
                save_user(chat_id, "Asia/Shanghai", valid_coins, "08:00")
            else:
                save_user(chat_id, user["timezone"], valid_coins, user["time"])
            msg = f"✅ Your daily update coins have been set to: {', '.join(valid_coins).upper()}"
            if invalid_coins:
                msg += f"\nInvalid coins ignored: {', '.join(invalid_coins)}"
            await update.message.reply_text(msg)
        except Exception as e:
            logger.error(f"Error setting coins for chat {chat_id}: {e}")
            await update.message.reply_text("❌ Failed to set coins. Please try again.")


    def _validate_coins(self, coins):
        valid_coins = get_top_coins(limit=1000)
        validated = []
        invalid = []
        for coin in coins:
            if coin.lower() in valid_coins:
                validated.append(coin.lower())
            else:
                invalid.append(coin)
        logger.info(f"User input coins: {coins}")
        logger.info(f"Valid coins after validation: {validated}")
        logger.info(f"Invalid coins: {invalid}")
        return validated, invalid

        

    async def set_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = str(update.effective_chat.id)
        if not context.args:
            await update.message.reply_text("❌ Please provide a time in HH:MM format. Example: /settime 09:30")
            return

        time_input = context.args[0]
        if not re.match(r'^\d{2}:\d{2}$', time_input):
            await update.message.reply_text("❌ Invalid time format. Please use HH:MM (24-hour format).")
            return
        
        try:
            hour, minute = map(int, time_input.split(":"))
            if not (0 <= hour <= 23 and 0 <= minute <=59):
                raise ValueError
        except ValueError:
            await update.message.reply_text("Invalid time value. Hours should be 00-23 and minuts 00-59")
            return
        
        user = get_user(chat_id)
        if not user:
            save_user(chat_id, "Asia/Shanghai", ["bitcoin"], time_input)
        else:
            save_user(chat_id, user["timezone"], user["coins"], time_input)
            # Reschedule job with new time
            if self.app.job_queue:
                jobs = self.app.job_queue.get_jobs_by_name(f"daily_morning_reminder_{chat_id}")
                for job in jobs:
                    job.schedule_removal()
                tz = pytz.timezone(user["timezone"])
                self.app.job_queue.run_daily(
                    callback=self.morning_reminder,
                    time=dtime(hour=hour, minute=minute, tzinfo=tz),
                    name=f"daily_morning_reminder_{chat_id}",
                    data={"chat_id": int(chat_id)}
                )
                logger.info(f"Rescheduled reminder for chat {chat_id} at {time_input}")

        await update.message.reply_text(f"✅ Your daily update time is set to {time_input}.")

    
    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("❓ Unknown command. Type /help to see available commands.")

    async def price_alert_monitor(self, context: ContextTypes.DEFAULT_TYPE):
        users = get_all_users()
        threshold = 5

        tracked_coins = set()
        for user in users:
            tracked_coins.update(user.get('coins', []))

        prices = get_price(",".join(tracked_coins))

        for coin, data in prices.items():
            change_24h = data.get('change_24h', 0)
            if abs(change_24h) >= threshold and coin not in self.alerted_coins:
                emoji = "🔺" if change_24h >= 0 else "🔻"
                message = f"⚡️{coin.upper()} has changed {emoji} {change_24h:+.2f}% - now ${data['usd']:,.2f}"
                for user in users:
                    if coin in user.get('coins', []):
                        await context.bot.send_message(chat_id=user["user_id"], text=message)
                self.alerted_coins.add(coin)
            elif abs(change_24h) < threshold and coin in self.alerted_coins:
                self.alerted_coins.remove(coin)

    async def setup_jobs(self, app):
        if not app.job_queue:
            logging.error("❌ JobQueue not available. Daily reminders will not be scheduled.")
            return
        
        logging.info("✅ Job queue initialized:", app.job_queue is not None)
        
        users = get_all_users()
        for user in users:
            chat_id = user["user_id"]
            time_str = user.get('time', '08:00')
            hour, minute = map(int, time_str.split(':'))
            tz_name = user.get('timezone', 'Asia/Shanghai')

            tz = pytz.timezone(tz_name)

            app.job_queue.run_daily(
                callback=self.morning_reminder,
                time=dtime(hour=hour, minute=minute, tzinfo=tz),
                name=f"daily_morning_reminder_{chat_id}",
                data={"chat_id": int(chat_id)}
            )
            logger.info(f"📅 Scheduled reminder for chat {chat_id} at {time_str} in timezone {tz_name}")
        
        # Price alert job every 5 minutes
        app.job_queue.run_repeating(
            self.price_alert_monitor,
            interval=300,
            first=10,
            name="price_alert_monitor"
        )
        logger.info("🚨 Price alert monitor scheduled every 5 minutes.")

    def run(self):
        init_db()
        migrate_from_json()
        logger.info("🚀 Bot started and polling for updates...")
        self.app.run_polling()