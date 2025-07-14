import json
import os

OLD_FILE = "subscribers.json"
BACKUP_FILE = "subscribers_backup.json"

def migrate_subscribers():
    if not os.path.exists(OLD_FILE):
        print("subscribers.json not found")
        return
    
    with open(OLD_FILE, "r") as f:
        old_data = json.load(f)

    #backup old data 
    with open (BACKUP_FILE, "w") as backup:
        json.dump(old_data, backup, indent=4)
        print(f"Backup created at {BACKUP_FILE}")

    new_data = {}

    if isinstance(old_data, dict):
        # old format: {chat_id: "Asia/Shanghai"}
        for chat_id, timezone in old_data.items():
            new_data[chat_id] = {
                "timezone" : timezone,
                "coins" : ["bitcoin", "ethereum"],
                "time": "08:00"  # default time
            }
    elif isinstance(old_data, list):
        # handle list format: [chat_ids]
        for chat_id in old_data:
            new_data[str(chat_id)] = {
                "timezone": "Asia/Shanghai",
                "coins": ["bitcoin", "ethereum", "dogecoin"],
                "time": "08:00"
            }
    else:
        print("❌ Unknown format in subscribers.json")
        return
    
    with open(OLD_FILE, "w") as f:
        json.dump(new_data, f, indent=4)
        print("✅ subscribers.json has been migrated to the new format.")

if __name__ == "__main__":
    migrate_subscribers()