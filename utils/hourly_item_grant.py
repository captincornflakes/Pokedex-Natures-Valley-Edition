import asyncio
import os
import json
import time
from utils.inventory_utils import add_item_to_inventory, get_item_amount


def item_grant(bot):
    SERVERS_DIR = os.path.join(os.getcwd(), "servers")
    item_id=1
    max_amount=12
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
        
        
async def hourly_item_grant(bot):
    await bot.wait_until_ready()
    while not bot.is_closed():
        item_grant(bot)
        await asyncio.sleep(bot.pokeballrate)