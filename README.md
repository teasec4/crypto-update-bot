#Crypto Update Telegram Bot

A Telegram bot that provides real-time cryptocurrency prices, daily reminders, and market updates using the CoinGecko API.

#Features
•	Get current prices, 24h price changes, and market caps for multiple cryptocurrencies.
•	Subscribe/unsubscribe to daily morning price reminders.
•	Interactive inline buttons for top cryptocurrencies.
•	Support for multiple coin queries.
•	Clean, formatted messages with emojis and links.
•	Runs on Python using the python-telegram-bot library.

1.	Clone the repository:
        git clone https://github.com/teasec4/crypto-update-bot.git
        cd crypto-update-bot

2.	Create and activate a Python virtual environment (recommended):
        python3 -m venv .venv
        source .venv/bin/activate  # Linux/macOS
        .venv\Scripts\activate     # Windows

3.	Install dependencies:
        pip install -r requirements.txt

4.	Set your Telegram Bot Token as an environment variable:
        export BOT_TOKEN="your_bot_token_here"  # Linux/macOS
        set BOT_TOKEN=your_bot_token_here       # Windows

#Usage
    python bot.py

#Commands
/start  Show top coin buttons and welcome message
/price <ids> Get price info for one or more coin IDs
/subscribe Subscribe to daily 8:00 AM crypto updates
/unsubscribe Unsubscribe from daily updates
/help Show the help message

#Development
•	The bot uses the CoinGecko API for crypto data.
•	Written in Python 3.9+.
•	Uses the python-telegram-bot library with job queue support.

#Contributing
Feel free to open issues or pull requests to improve the bot!

#License
MIT License © 2025 Kovalev

#Contact
•	GitHub: https://github.com/teasec4