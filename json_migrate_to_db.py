import json
import logging
from db import save_user

# Configure logging to match remainder_bot.py
logger = logging.getLogger(__name__)

def migrate_from_json(json_file="subscribers.json"):
    try:
        with open(json_file, "r") as f:
            data = json.load(f)
        for user, config in data.items():
            save_user(
                user,
                config.get("timezone", "Asia/Shanghai"),
                config.get("coins", ["bitcoin", "ethereum", "dogecoin"]),
                config.get("time", "08:00")
            )
        logger.info(f"Migration from {json_file} to SQLite completed successfully")
    except FileNotFoundError:
        logger.info(f"No JSON file found at {json_file}, skipping migration")
    except Exception as e:
        logger.error(f"Error during migration from {json_file}: {e}")