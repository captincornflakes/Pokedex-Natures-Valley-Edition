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

def pick_random_pokemon(pokemon_list, rarity_weights=None):
    if not pokemon_list:
        return None

    if rarity_weights:
        # Build a weighted list based on rarity
        weighted = []
        for p in pokemon_list:
            rarity = p.get("rarity", "Common")
            weight = rarity_weights.get(rarity, 1)
            weighted.extend([p] * weight)
        return random.choice(weighted) if weighted else random.choice(pokemon_list)
    else:
        return random.choice(pokemon_list)

def generate_wild_pokemon(bot, level_range=(1, 10)):
    pokemon_list = bot.pokemon
    rarity = get_random_rarity()
    # Filter Pokémon by rarity (case-insensitive)
    filtered = [p for p in pokemon_list if p.get("rarity", "common").lower() == rarity]
    if not filtered:
        # Fallback: pick any Pokémon if none match the rarity
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