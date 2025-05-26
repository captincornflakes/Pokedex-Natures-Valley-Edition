import os
import json
import time
from utils.inventory_utils import add_item_to_inventory, get_item_amount

SERVERS_DIR = os.path.join(os.getcwd(), "servers")

def hourly_item_grant_thread(bot, item_id=1, max_amount=12, interval_seconds=3600):
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    while True:
        print("[HourlyItemGrant] Running hourly item grant...")
        for guild in bot.guilds:
            guild_dir = os.path.join(SERVERS_DIR, str(guild.id))
            if not os.path.isdir(guild_dir):
                continue
            for filename in os.listdir(guild_dir):
                if filename == "data.json":
                    continue
                user_id = filename[:-5]
                try:
                    amount = get_item_amount(guild.id, user_id, item_id)
                    if amount < max_amount:
                        add_item_to_inventory(guild.id, user_id, item_id, 1)
                except Exception as e:
                    print(f"[HourlyItemGrant] Error processing {filename} in {guild_dir}: {e}")
        print("[HourlyItemGrant] Done. Sleeping until next hour...")
        time.sleep(interval_seconds)