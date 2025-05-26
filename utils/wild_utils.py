import random
import os
import json
import discord
import asyncio
import time
from utils.capture_utils import CaptureButton
from utils.spawn_utils import generate_wild_pokemon, update_wild_pokemon_message

MIN_SPAWN_INTERVAL = 10  # seconds, adjust as needed

async def spawn_wild_pokemon_in_all_servers(bot):
    servers_dir = os.path.join(os.getcwd(), "servers")
    now = int(time.time())
    for guild_id in os.listdir(servers_dir):
        if random.random() > 0.5:
            continue
        guild_folder = os.path.join(servers_dir, guild_id)
        data_file = os.path.join(guild_folder, "data.json")
        if not os.path.isfile(data_file):
            continue
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        active_spawn = data.get("active_spawn")

        # Prevent double spawn if previous is still active (existing logic)
        if active_spawn and active_spawn.get("status") == "active":
            channels = data.get("channels", {})
            wild_channel_id = channels.get("wild")
            if wild_channel_id:
                channel = bot.get_channel(int(wild_channel_id))
                if channel and "message_id" in active_spawn:
                    try:
                        message = await channel.fetch_message(active_spawn["message_id"])
                        # If the message still has a view (button), update it to show the Pokémon ran away
                        if message.components or message.attachments or getattr(message, "view", None):
                            await update_wild_pokemon_message(
                                bot,
                                guild_id,
                                status_message="The wild Pokémon ran away!",
                                new_embed=None
                            )
                    except discord.NotFound as e:
                        pass
                    except Exception as e:
                        print(f"[WARN] Could not update previous wild Pokémon message for guild {guild_id}: {e}")
            continue  # <-- Prevent double spawn!

        # NEW: Prevent spawning if last spawn was too recent
        if active_spawn and "spawn_time" in active_spawn:
            if now - int(active_spawn["spawn_time"]) < MIN_SPAWN_INTERVAL:
                continue

        channels = data.get("channels", {})
        wild_channel_id = channels.get("wild")
        if not wild_channel_id:
            continue

        # Generate a wild Pokémon
        pokemon_id = generate_wild_pokemon(bot)
        pokemon = next((p for p in bot.pokemon if p.get("id") == pokemon_id), None)
        if not pokemon:
            continue

        # Build the embed
        name = pokemon.get("name", "Unknown")
        poke_type = ", ".join(pokemon.get("type", []))
        rarity = pokemon.get("rarity", "Unknown")
        abilities = ", ".join(pokemon.get("special_abilities", []))
        cp = pokemon.get("cp", "?")
        embed = discord.Embed(
            title=f"A wild {name} appeared!",
            color=discord.Color.green()
        )
        embed.add_field(name="Type", value=poke_type or "Unknown", inline=True)
        embed.add_field(name="Rarity", value=rarity, inline=True)
        embed.add_field(name="CP", value=str(cp), inline=True)
        embed.add_field(name="Abilities", value=abilities or "Unknown", inline=False)
        # Add Pokémon image using bot.media
        if hasattr(bot, "media"):
            poke_id = pokemon.get("id", "unknown")
            # Example for a CDN that supports resizing via query string:
            embed.set_image(url=f"{bot.media}/pokemon/{poke_id}.png?width=100&height=100")

        # Send to the wild channel with capture button
        channel = bot.get_channel(int(wild_channel_id))
        if channel:
            view = CaptureButton(guild_id, pokemon_id)
            message = await channel.send(embed=embed, view=view)
            # Log the active spawn to the server's data.json, now with message_id
            log_active_spawn(guild_id, pokemon_id, status="active", trainer=None, message_id=message.id)

def log_active_spawn(guild_id, pokemon_id, status="active", trainer=None, message_id=None):
    servers_dir = os.path.join(os.getcwd(), "servers")
    data_file = os.path.join(servers_dir, str(guild_id), "data.json")
    if not os.path.isfile(data_file):
        print(f"[WARN] No data.json found for guild {guild_id} to log spawn.")
        return
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    spawn_entry = {
        "id": pokemon_id,
        "spawn_time": int(time.time()),
        "status": status,
        "trainer": trainer
    }
    if message_id is not None:
        spawn_entry["message_id"] = message_id
    data["active_spawn"] = spawn_entry
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"[Output] Logged active spawn for guild {guild_id}: {spawn_entry}")



async def wild_pokemon_spawn_clock(bot):
    await bot.wait_until_ready()
    while not bot.is_closed():
        await spawn_wild_pokemon_in_all_servers(bot)
        await asyncio.sleep(bot.spawnrate)
