from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from crypto_utils import get_price, get_top_coins, _add_subscriber, _remove_subscriber, load_subscribers, save_subscribers
from datetime import time as dtime
import pytz
import logging
import re

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
        self._add_subscriber = _add_subscriber
        self._remove_subscriber = _remove_subscriber

    def _register_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("price", self.price))
        self.app.add_handler(CommandHandler("help", self.help))
        self.app.add_handler(CommandHandler("subscribe", self.subscribe))
        self.app.add_handler(CommandHandler("unsubscribe", self.unsubscribe))
        self.app.add_handler(CommandHandler("testmorning", self.test_morning))
        self.app.add_handler(CallbackQueryHandler(self.button_handler))
        self.app.add_handler(CommandHandler("change", self.change_timezone))
        self.app.add_handler(CommandHandler("setcoins", self.set_coins))
        self.app.add_handler(CommandHandler("settime", self.set_time))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        top_coins = get_top_coins()
        #create a top 10 coins buttons witch can return data
        keyboard = [
            [InlineKeyboardButton(coin1.title(), callback_data=f"price_{coin1}"),
            InlineKeyboardButton(coin2.title(), callback_data=f"price_{coin2}")]
            for coin1, coin2 in zip(top_coins[::2], top_coins[1::2])
        ]
        if len(top_coins) % 2 != 0:
            keyboard.append([InlineKeyboardButton(top_coins[-1].title(), callback_data=f"price_{top_coins[-1]}")])
        keyboard.append([InlineKeyboardButton("Top 10 Coins", callback_data="top10")])
        keyboard.append([
            InlineKeyboardButton("📬 Subscribe", callback_data="subscribe"),
            InlineKeyboardButton("🚫 Unsubscribe", callback_data="unsubscribe")
        ])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Welcome to Crypto Reminder Bot!\nUse /help for full instructions.",
            reply_markup=reply_markup
        )

    async def price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Please specify one or more coin IDs, e.g., /price bitcoin eth or tipe /help for help")
            return

        coin_ids = [coin.lower() for coin in context.args]
        prices = get_price(",".join(coin_ids))

        for coin in coin_ids:
            data = prices.get(coin)
            if data:
                change = data['change_24h']
                if change >= 0:
                    emoji = "🟢" 
                else:
                    emoji = "🔻"
                msg = (
                    f"<b>💰 {coin.upper()}</b>\n"
                    f"Price: <code>${data['usd']:,.2f}</code>\n"
                    f"24h Change: {emoji} <i>{data['change_24h']:.2f}%</i>\n"
                    f"Market Cap: <code>${data['market_cap']:,.0f}</code>\n"
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
            "Here's what you can do:\n\n"
            "🟢 <b>/start</b> — Show interactive buttons for top coins.\n"
            "🟢 <b>/price &lt;coin_id&gt;</b> — Get price, market cap, and 24h change.\n"
            "   <i>Example:</i> <code>/price bitcoin eth</code>\n"
            "🟢 <b>/subscribe</b> — Subscribe to daily 8:00 AM crypto updates.\n"
            "🟢 <b>/unsubscribe</b> — Stop receiving daily updates.\n"
            "🟢 <b>/change</b> — For change a Time Zone for corrent time daily updates.\n"
            #"🟢 <b>/testmorning</b> — Immediately test the morning message.\n\n"
            "💡 Use coin IDs like <code>bitcoin</code>, <code>ethereum</code>, <code>dogecoin</code>, etc.\n"
            "📈 Use the buttons or commands at any time for fresh info.\n\n"
            "❓ If you see strange output, check your coin ID spelling.\n"
        )
        await update.message.reply_text(text, parse_mode="HTML")

    async def subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        subs = load_subscribers()
        if _add_subscriber(chat_id):
            subs[chat_id] = {
                "timezone": "Asia/Shanghai",
                "coins": ["bitcoin", "ethereum", "dogecoin"],
                "time": "08:00"
            }
            save_subscribers(subs)
            await update.message.reply_text("✅ You've subscribed to daily updates.")
        else:
            await update.message.reply_text("📬 You're already subscribed.")

    async def unsubscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        if _remove_subscriber(chat_id):
            await update.message.reply_text("🚫 You've unsubscribed.")
        else:
            await update.message.reply_text("❌ You weren't subscribed.")

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data
        # get data from button
        if data.startswith("price_"):
            coin_id = data.replace("price_", "")
            prices = get_price(coin_id)
            coin_data = prices.get(coin_id)
            if coin_data:
                # get up or down emoji
                change = coin_data['change_24h']
                if change >= 0:
                    emoji = "🟢" 
                else:
                    emoji = "🔻"
                # output message
                msg = (
                    f"💰<b>{coin_id.upper()}</b>\n"
                    f"Price: <code>${coin_data['usd']:,.2f}</code>\n"
                    f"{emoji} 24h Change: <i>{coin_data['change_24h']:.2f}%</i>\n"
                    f"Market Cap: <code>${coin_data['market_cap']:,.0f}</code>\n"
                )
                await query.message.reply_text(msg, parse_mode="HTML", disable_web_page_preview=False)
            else:
                await query.message.reply_text(f"❌ Could not find price for '{coin_id}'")
        # top 10 coin by cap
        elif data == "top10":
            top_coins = get_top_coins()
            await query.message.reply_text("📈 Top 10 Coin IDs:\n" + ", ".join(top_coins))
        # subscribe button handler       
        elif data == "subscribe":
            chat_id = update.effective_chat.id
            if self._add_subscriber(chat_id):
                await query.message.reply_text("✅ You've subscribed to daily updates.")
            else:
                await query.message.reply_text("📬 You're already subscribed.")
        # unsubscribe button handler
        elif data == "unsubscribe":
            chat_id = update.effective_chat.id
            if self._remove_subscriber(chat_id):
                await query.message.reply_text("🚫 Unsubscribed via button.")
            else:
                await query.message.reply_text("❌ You weren't subscribed.")
        elif data.startswith("tz_"):
            tz = data.replace("tz_", "")
            chat_id = str(update.effective_chat.id)

            subscribers = load_subscribers()
            if chat_id in subscribers:
                subscribers[chat_id]['timezone'] = tz
                save_subscribers(subscribers)
                await query.message.reply_text(f"🌍 Timezone changed to {tz.replace('_', ' ')} for daily reminders.")
            else:
                await query.message.reply_text("❌ You need to subscribe first to change timezone.")

    async def morning_reminder(self, context: ContextTypes.DEFAULT_TYPE):
        chat_id = str(context.job.data['chat_id'])
        subscribers = load_subscribers()
        user_config = subscribers.get(chat_id)

        if not user_config:
            logger.warning(f"No configuration found for chat {chat_id}")
            return

        coins = user_config.get('coins', ['bitcoin', 'ethereum', 'dogecoin'])
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
        fake_context = type("ctx", (), {"bot": context.bot})
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
            await update.message.reply_text("None of the provided coin IDs are valid. Please try again")
            return
        
        subscribers = load_subscribers()

        if chat_id not in subscribers:
            subscribers[chat_id] = {"timezone" : "Asia/Shanghai", "coins": valid_coins, "time": "08:00"}
        else:
            subscribers[chat_id]['coins'] = valid_coins

        save_subscribers(subscribers)
        msg = (f"✅ Your daily update coins have been set to: {', '.join(coins).upper()}")

        if invalid_coins:
            msg += f"\Invalid coins ignored: {','.join(invalid_coins)}"

        await update.message.reply_text(msg)

        def _validate_coins(self, coins):
            valid_coins = get_top_coins()
            validated = []
            invalid = []
            for coin in coins:
                if coin.lower() in valid_coins:
                    validated.append(coin.lower())
                else:
                    invalid.append(coin)
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
        
        subscribers = load_subscribers()
        if chat_id not in subscribers:
            subscribers[chat_id] = {"timezone": "Asia/Shanghai", "coins": ["bitcoin"], "time": time_input}
        else:
            subscribers[chat_id]['time'] = time_input

        save_subscribers(subscribers)
        await update.message.reply_text(f"✅ Your daily update time is set to {time_input}.")

    async def setup_jobs(self, app):
        if not app.job_queue:
            logging.error("❌ JobQueue not available. Daily reminders will not be scheduled.")
            return
        
        logging.info("✅ Job queue initialized:", app.job_queue is not None)
        
        app.job_queue.jobs().clear()
        subscribers = load_subscribers()
        for chat_id, config in subscribers.items():
            time_str = config.get('time', '08:00')
            hour, minute = map(int, time_str.split(':'))
            tz_name = config.get('timezone', 'Asia/Shanghai')

            tz = pytz.timezone(tz_name)

            app.job_queue.run_daily(
                callback=self.morning_reminder,
                time=dtime(hour=hour, minute=minute, tzinfo=tz),
                name=f"daily_morning_reminder_{chat_id}",
                data={"chat_id": int(chat_id)}
            )
            logger.info(f"📅 Scheduled reminder for chat {chat_id} at {time_str} in timezone {tz_name}")

    def run(self):
        logger.info("🚀 Bot started and polling for updates...")
        self.app.run_polling()