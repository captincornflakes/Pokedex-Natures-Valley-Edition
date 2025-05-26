import random
import os
import json
import discord
import asyncio
import time
from utils.capture_utils import CaptureButton
from utils.server_handler import read_server_data, log_active_spawn

MIN_SPAWN_INTERVAL = 10  # seconds, adjust as needed

async def update_wild_pokemon_message(bot, guild_id, status_message, new_embed=None):
    from utils.server_handler import read_server_data
    data = read_server_data(guild_id)
    if not data:
        return False
    active_spawn = data.get("active_spawn")
    if not active_spawn or "message_id" not in active_spawn:
        return False
    channels = data.get("channels", {})
    wild_channel_id = channels.get("wild")
    if not wild_channel_id:
        return False
    channel = bot.get_channel(int(wild_channel_id))
    if not channel:
        return False
    try:
        message = await channel.fetch_message(active_spawn["message_id"])
        original_content = message.content or ""
        updated_content = f"{original_content}\n\n{status_message}"
        await message.edit(
            content=updated_content,
            embed=new_embed if new_embed is not None else (message.embeds[0] if message.embeds else None),
            view=None  # Remove the button
        )
        return True
    except Exception as e:
        return False

def generate_wild_pokemon(bot):
    pokemon_list = bot.pokemon
    rarity = get_random_rarity()
    filtered = [p for p in pokemon_list if p.get("rarity", "common").lower() == rarity]
    if not filtered:
        filtered = pokemon_list
    chosen = random.choice(filtered)
    return chosen.get("id")

def get_random_rarity():
    roll = random.random()
    if roll < 0.005:
        rarity = "mythic"
    elif roll < 0.02:
        rarity = "legendary"
    elif roll < 0.07:
        rarity = "rare"
    elif roll < 0.20:
        rarity = "uncommon"
    else:
        rarity = "common"
    #print(f"[get_random_rarity] roll={roll:.4f}, rarity={rarity}")
    return rarity
    
def can_spawn_pokemon(data, min_spawn_interval: int = MIN_SPAWN_INTERVAL) -> bool:
    active_spawn = data.get("active_spawn")
    now = int(time.time())
    if not active_spawn or "spawn_time" not in active_spawn:
        print(f"[can_spawn_pokemon] No active spawn or no spawn_time: True")
        return True
    spawn_time = int(active_spawn.get("spawn_time", 0))
    result = (now - spawn_time) >= min_spawn_interval
    print(f"[can_spawn_pokemon] now={now}, spawn_time={spawn_time}, interval={now-spawn_time}, min={min_spawn_interval}, result={result}")
    return result

async def handle_active_spawn(bot, guild_id, data, active_spawn):
    channels = data.get("channels", {})
    wild_channel_id = channels.get("wild")
    if not wild_channel_id:
        return
    channel = bot.get_channel(int(wild_channel_id))
    if not channel or "message_id" not in active_spawn:
        return
    try:
        message = await channel.fetch_message(active_spawn["message_id"])
        if message.components or message.attachments or getattr(message, "view", None):
            await update_wild_pokemon_message(
                bot,
                guild_id,
                status_message="The wild Pokémon ran away!",
                new_embed=None
            )
    except discord.NotFound:
        pass
    except Exception as e:
        print(f"[WARN] Could not update previous wild Pokémon message for guild {guild_id}: {e}")

async def spawn_wild_pokemon_in_all_servers(bot):
    servers_dir = os.path.join(os.getcwd(), "servers")
    for guild_id in os.listdir(servers_dir):
        data = read_server_data(guild_id)
        if not data:
            continue

        if not can_spawn_pokemon(data):
            continue  # Only time-based check

        channels = data.get("channels", {})
        wild_channel_id = channels.get("wild")
        if not wild_channel_id:
            continue

        pokemon_id = generate_wild_pokemon(bot)
        pokemon = next((p for p in bot.pokemon if p.get("id") == pokemon_id), None)
        if not pokemon:
            continue

        name = pokemon.get("name", "Unknown")
        poke_type = ", ".join(pokemon.get("type", []))
        rarity = pokemon.get("rarity", "Unknown")
        cp = pokemon.get("cp", "?")
        embed = discord.Embed(
            title=f"A wild {name} appeared!",
            color=discord.Color.green()
        )
        embed.add_field(name="Type", value=poke_type or "Unknown", inline=True)
        embed.add_field(name="Rarity", value=rarity, inline=True)
        embed.add_field(name="CP", value=str(cp), inline=True)
        embed.set_image(url=f"{bot.media}/pokemon/{pokemon_id}.png?width=100&height=100")

        channel = bot.get_channel(int(wild_channel_id))
        if channel:
            view = CaptureButton(guild_id, pokemon_id)
            message = await channel.send(embed=embed, view=view)
            log_active_spawn(guild_id, pokemon_id, status="active", trainer=None, message_id=message.id)

async def wild_pokemon_spawn_clock(bot):
    await bot.wait_until_ready()
    while not bot.is_closed():
        await spawn_wild_pokemon_in_all_servers(bot)
        await asyncio.sleep(bot.spawnrate)
