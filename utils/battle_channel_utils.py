import discord
import os
import json
import asyncio

async def create_battle_channel(guild: discord.Guild, user1: discord.Member, user2: discord.Member, category_name="pokemon"):

    # Find or create the category
    category = discord.utils.get(guild.categories, name=category_name)
    if category is None:
        category = await guild.create_category(category_name)

    # Set permissions: everyone can view, only the two users can send messages
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False, read_message_history=True),
        user1: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        user2: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
    }

    # Create the channel
    channel_name = f"battle-{user1.display_name}-vs-{user2.display_name}".lower().replace(" ", "-")
    channel = await guild.create_text_channel(
        name=channel_name,
        overwrites=overwrites,
        category=category,
        topic=f"Pokémon battle between {user1.display_name} and {user2.display_name}"
    )

    # Log to data.json
    servers_dir = os.path.join(os.getcwd(), "servers")
    data_file = os.path.join(servers_dir, str(guild.id), "data.json")
    if os.path.isfile(data_file):
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    if "active_battles" not in data:
        data["active_battles"] = []

    data["active_battles"].append({
        "channel_id": channel.id,
        "user1_id": user1.id,
        "user2_id": user2.id,
        "started_at": int(discord.utils.utcnow().timestamp())
    })

    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return channel

async def delete_battle_channel(guild: discord.Guild, channel_id: int):
    """
    Deletes the specified battle channel and removes it from active_battles in data.json.
    """
    # Delete the channel
    channel = guild.get_channel(channel_id)
    if channel:
        await channel.delete(reason="Battle ended")

    # Remove from data.json
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
    """
    Monitors the battle channel for inactivity. If no messages are sent for `timeout_seconds`, deletes the channel.
    """
    channel = guild.get_channel(channel_id)
    if not channel:
        return

    def check(message):
        return message.channel.id == channel_id

    try:
        while True:
            # Wait for a message in the channel or timeout
            await bot.wait_for("message", check=check, timeout=timeout_seconds)
            # If a message is received, loop and wait again
    except asyncio.TimeoutError:
        # No message received in timeout_seconds, delete the channel
        await delete_battle_channel(guild, channel_id)
        print(f"[INFO] Deleted inactive battle channel {channel_id} in guild {guild.id}")

async def monitor_all_battle_channels_clock(bot):
    """
    Monitors all battle channels in all guilds for inactivity.
    """
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
                    # Monitor each battle channel for inactivity
                    asyncio.create_task(monitor_battle_channel_inactivity(bot, guild, channel_id))
        # Wait for a while before checking again
        await asyncio.sleep(300)  # Check every 5 minutes

# To start monitoring all battle channels, uncomment the following line and replace `bot` with your bot instance
