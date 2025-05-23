import random
import os
import json
import discord
import asyncio
import time
from utils.capture_utils import CaptureButton
from utils.spawn_utils import generate_wild_pokemon

async def spawn_wild_pokemon_in_all_servers(bot):
    servers_dir = os.path.join(os.getcwd(), "servers")
    for guild_id in os.listdir(servers_dir):
        if random.random() > 0.5:
            continue
        guild_folder = os.path.join(servers_dir, guild_id)
        data_file = os.path.join(guild_folder, "data.json")
        if not os.path.isfile(data_file):
            continue
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Prevent double spawning: check if an active spawn exists and was spawned less than 30 seconds ago
        active_spawn = data.get("active_spawn")
        now = int(time.time())
        if active_spawn and (now - active_spawn.get("spawn_time", 0)) < 30:
            continue  # Skip this server if a wild Pokémon was spawned less than 30 seconds ago

        channels = data.get("channels", {})
        wild_channel_id = channels.get("wild")
        if not wild_channel_id:
            continue

        # Generate a wild Pokémon
        pokemon_id = generate_wild_pokemon(bot)
        pokemon = next((p for p in bot.pokemon if p.get("id") == pokemon_id), None)
        if not pokemon:
            continue

        # Log the active spawn to the server's data.json
        log_active_spawn(guild_id, pokemon_id, status="active", trainer=None)

        # Build the embed
        name = pokemon.get("name", "Unknown")
        poke_type = ", ".join(pokemon.get("type", []))
        rarity = pokemon.get("rarity", "Unknown")
        abilities = ", ".join(pokemon.get("special_abilities", []))
        embed = discord.Embed(
            title=f"A wild {name} appeared!",
            color=discord.Color.green()
        )
        embed.add_field(name="Type", value=poke_type or "Unknown", inline=True)
        embed.add_field(name="Rarity", value=rarity, inline=True)
        embed.add_field(name="Abilities", value=abilities or "Unknown", inline=False)

        # Send to the wild channel with capture button
        channel = bot.get_channel(int(wild_channel_id))
        if channel:
            view = CaptureButton(guild_id, pokemon_id)
            await channel.send(embed=embed, view=view)

def log_active_spawn(guild_id, pokemon_id, status="active", trainer=None):
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
    data["active_spawn"] = spawn_entry
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"[Output] Logged active spawn for guild {guild_id}: {spawn_entry}")



async def wild_pokemon_spawn_clock(bot):
    await bot.wait_until_ready()
    while not bot.is_closed():
        await spawn_wild_pokemon_in_all_servers(bot)
        await asyncio.sleep(bot.spawnrate)  # Use bot.spawnrate for interval
