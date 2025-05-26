import os
import json
import asyncio
from utils.inventory_utils import add_item_to_inventory, get_item_amount

SERVERS_DIR = os.path.join(os.getcwd(), "servers")

async def hourly_item_grant(bot, item_id=1, max_amount=12, interval_seconds=3600):
    await bot.wait_until_ready()
    while not bot.is_closed():
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
        await asyncio.sleep(interval_seconds)