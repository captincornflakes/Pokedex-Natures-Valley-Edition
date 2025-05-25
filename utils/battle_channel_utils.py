import discord
import os
import json
import asyncio
from utils.player_handler import read_user_record

async def create_battle_channel(guild: discord.Guild, user1: discord.Member, user2: discord.Member, category_name="pokemon", bot=None):
    category = discord.utils.get(guild.categories, name=category_name)
    if category is None:
        category = await guild.create_category(category_name)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False, read_message_history=True),
        user1: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        user2: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
    }
    channel_name = f"battle-{user1.display_name}-vs-{user2.display_name}".lower().replace(" ", "-")
    channel = await guild.create_text_channel(
        name=channel_name,
        overwrites=overwrites,
        category=category,
        topic=f"Pokémon battle between {user1.display_name} and {user2.display_name}"
    )
    def get_active_pokemon(guild_id, user_id):
        servers_dir = os.path.join(os.getcwd(), "servers")
        player_file = os.path.join(servers_dir, str(guild_id), "players.json")
        if os.path.isfile(player_file):
            with open(player_file, "r", encoding="utf-8") as f:
                players = json.load(f)
            user_data = players.get(str(user_id))
            if user_data and user_data.get("active_pokemon"):
                # Use the first active Pokémon for battle
                poke = user_data["active_pokemon"][0]
                return {
                    "id": poke.get("id"),
                    "name": poke.get("name"),
                    "cp": poke.get("cp"),
                    "hp": poke.get("hp"),
                    "type": poke.get("type"),
                    "level": poke.get("level"),
                    "rarity": poke.get("rarity"),
                    "abilities": poke.get("special_abilities", []),
                    "current_hp": poke.get("hp"),  # Track current HP for battle
                }
        return None
    user1_pokemon = get_active_pokemon(guild.id, user1.id)
    user2_pokemon = get_active_pokemon(guild.id, user2.id)
    servers_dir = os.path.join(os.getcwd(), "servers")
    data_file = os.path.join(servers_dir, str(guild.id), "data.json")
    if os.path.isfile(data_file):
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    if "active_battles" not in data:
        data["active_battles"] = []

    battle_entry = {
        "channel_id": channel.id,
        "user1_id": user1.id,
        "user2_id": user2.id,
        "user1_name": user1.display_name,
        "user2_name": user2.display_name,
        "user1_pokemon": user1_pokemon,
        "user2_pokemon": user2_pokemon,
        "user1_played": [],
        "user2_played": [],
        "round": 1,
        "best_of": 3,
        "turn": user1.id,  # user1 starts
        "started_at": int(discord.utils.utcnow().timestamp())
    }

    data["active_battles"].append(battle_entry)

    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return channel

async def delete_battle_channel(guild: discord.Guild, channel_id: int):
    channel = guild.get_channel(channel_id)
    if channel:
        await channel.delete(reason="Battle ended")
    servers_dir = os.path.join(os.getcwd(), "servers")
    data_file = os.path.join(servers_dir, str(guild.id), "data.json")
    if os.path.isfile(data_file):
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        battles = data.get("active_battles", [])
        data["active_battles"] = [b for b in battles if b.get("channel_id") != channel_id]
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

async def monitor_battle_channel_inactivity(bot, guild: discord.Guild, channel_id: int, timeout_seconds=1800):
    channel = guild.get_channel(channel_id)
    if not channel:
        return

    def check(message):
        return message.channel.id == channel_id

    try:
        while True:
            await bot.wait_for("message", check=check, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        await delete_battle_channel(guild, channel_id)
        print(f"[INFO] Deleted inactive battle channel {channel_id} in guild {guild.id}")

async def monitor_all_battle_channels_clock(bot):
    await bot.wait_until_ready()
    while not bot.is_closed():
        for guild in bot.guilds:
            # Load data.json for the guild
            servers_dir = os.path.join(os.getcwd(), "servers")
            data_file = os.path.join(servers_dir, str(guild.id), "data.json")
            if os.path.isfile(data_file):
                with open(data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                active_battles = data.get("active_battles", [])
                for battle in active_battles:
                    channel_id = battle.get("channel_id")
                    asyncio.create_task(monitor_battle_channel_inactivity(bot, guild, channel_id))
        await asyncio.sleep(300)  # Check every 5 minutes