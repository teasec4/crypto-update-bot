from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from crypto_utils import get_price, get_top_coins, _add_subscriber, _remove_subscriber, load_subscribers
from datetime import time as dtime


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
        #self.app.add_handler(CommandHandler("testmorning", self.test_morning))
        self.app.add_handler(CallbackQueryHandler(self.button_handler))

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
            #"🟢 <b>/testmorning</b> — Immediately test the morning message.\n\n"
            "💡 Use coin IDs like <code>bitcoin</code>, <code>ethereum</code>, <code>dogecoin</code>, etc.\n"
            "📈 Use the buttons or commands at any time for fresh info.\n\n"
            "❓ If you see strange output, check your coin ID spelling.\n"
        )
        await update.message.reply_text(text, parse_mode="HTML")

    async def subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        if _add_subscriber(chat_id):
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
    
    async def morning_reminder(self, context: ContextTypes.DEFAULT_TYPE):
        coins = ['bitcoin', 'ethereum']
        messages = []

        for coin in coins:
            data = get_price(coin).get(coin)
            if not data:
                continue
            if data['change_24h'] >= 0:
                emoji = "🟢" 
            else:
                emoji = "🔻"

            msg = (
                f"🔹 <b>{coin.upper()}</b>\n"
                f"💰 Price: <code>${data['usd']:,.2f}</code>\n"
                f"{emoji} 24h Change:  <i>{data['change_24h']:.2f}%</i>\n"
                f"🏦 Market Cap: <code>${data['market_cap']:,.0f}</code>\n\n"
            )
            messages.append(msg)
        
        full_message = "<b>🌅 Morning Crypto Update</b>\n\n" + "\n".join(messages)
        for chat_id in load_subscribers():
                await context.bot.send_message(chat_id=chat_id, text=full_message, parse_mode="HTML")

    async def test_morning(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        fake_context = type("ctx", (), {"bot": context.bot})
        await self.morning_reminder(fake_context)

    async def setup_jobs(self, app):
        print("✅ Job queue initialized:", app.job_queue is not None)
        if app.job_queue:
            app.job_queue.run_daily(
                self.morning_reminder,
                time=dtime(hour=8, minute=0),
                name="daily_morning_reminder"
            )
        else:
            print("❌ job_queue is None")

        print(f"[DEBUG] JobQueue available: {app.job_queue}")

    def run(self):
        self.app.run_polling()