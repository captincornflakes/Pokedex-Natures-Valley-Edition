import os
import json
import random

def update_active_spawn_status(guild_id, pokemon_id, status, trainer):
    servers_dir = os.path.join(os.getcwd(), "servers")
    data_file = os.path.join(servers_dir, str(guild_id), "data.json")
    if not os.path.isfile(data_file):
        print(f"[WARN] No data.json found for guild {guild_id} to update spawn.")
        return

    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    updated = False
    spawn = data.get("active_spawn")
    if spawn and spawn["id"] == pokemon_id and spawn["status"] == "active":
        spawn["status"] = status
        spawn["trainer"] = trainer
        data["active_spawn"] = spawn
        updated = True

    if updated:
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"[Output] Updated spawn {pokemon_id} to status '{status}' for guild {guild_id} (trainer: {trainer})")
    else:
        print(f"[WARN] No active spawn found to update for guild {guild_id}, pokemon {pokemon_id}")

async def update_wild_pokemon_message(bot, guild_id, status_message, new_embed=None):
    servers_dir = os.path.join(os.getcwd(), "servers")
    data_file = os.path.join(servers_dir, str(guild_id), "data.json")
    if not os.path.isfile(data_file):
        print(f"[WARN] No data.json found for guild {guild_id}.")
        return False

    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    active_spawn = data.get("active_spawn")
    if not active_spawn or "message_id" not in active_spawn:
        print(f"[WARN] No active spawn message_id found for guild {guild_id}.")
        return False

    channels = data.get("channels", {})
    wild_channel_id = channels.get("wild")
    if not wild_channel_id:
        print(f"[WARN] No wild channel set for guild {guild_id}.")
        return False

    channel = bot.get_channel(int(wild_channel_id))
    if not channel:
        print(f"[WARN] Could not fetch channel {wild_channel_id} for guild {guild_id}.")
        return False

    try:
        message = await channel.fetch_message(active_spawn["message_id"])
        # Keep original content, append status message
        original_content = message.content or ""
        updated_content = f"{original_content}\n\n{status_message}"
        await message.edit(
            content=updated_content,
            embed=new_embed if new_embed is not None else (message.embeds[0] if message.embeds else None),
            view=None  # Remove the button
        )
        print(f"[INFO] Updated wild Pokémon message in guild {guild_id}.")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to update wild Pokémon message in guild {guild_id}: {e}")
        return False

def generate_wild_pokemon(bot, level_range=(1, 10)):
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
        return "mythic"
    elif roll < 0.02:
        return "legendary"
    elif roll < 0.07:
        return "rare"
    elif roll < 0.20:
        return "uncommon"
    else:
        return "common"