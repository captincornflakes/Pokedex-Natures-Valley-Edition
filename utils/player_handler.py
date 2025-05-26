import os
import json
import discord

# Store player files in servers/<guild_id>/<user_id>.json
SERVERS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "servers")

def get_user_file_path(guild_id, user_id):
    guild_folder = os.path.join(SERVERS_DIR, str(guild_id))
    os.makedirs(guild_folder, exist_ok=True)
    return os.path.join(guild_folder, f"{user_id}.json")

def create_user_record(guild_id, user_id):
    user_file = get_user_file_path(guild_id, user_id)
    if not os.path.exists(user_file):
        user_data = {
            "inventory": [],
            "pokedex": [],
            "active_pokemon": [],
            "badges": [],
            "coin": 100,
            "gender": "",
            "pronouns": "",
            "nickname": "",
            "power": 0
        }
        with open(user_file, "w", encoding="utf-8") as f:
            json.dump(user_data, f, indent=2)
    return read_user_record(guild_id, user_id)

def read_user_record(guild_id, user_id):
    user_file = get_user_file_path(guild_id, user_id)
    if not os.path.exists(user_file):
        return None
    with open(user_file, "r", encoding="utf-8") as f:
        return json.load(f)

def update_user_record(guild_id, user_id, user_data):
    user_file = get_user_file_path(guild_id, user_id)
    with open(user_file, "w", encoding="utf-8") as f:
        json.dump(user_data, f, indent=2)

def delete_user_record(guild_id, user_id):
    user_file = get_user_file_path(guild_id, user_id)
    if os.path.exists(user_file):
        os.remove(user_file)

def add_pokemon_to_pokedex(guild_id, user_id, pokemon_id):
    user_data = read_user_record(guild_id, user_id)
    if user_data is None:
        user_data = create_user_record(guild_id, user_id)
    if pokemon_id not in user_data["pokedex"]:
        user_data["pokedex"].append(pokemon_id)
        update_user_record(guild_id, user_id, user_data)
        print(f"[Output] Added Pokémon ID {pokemon_id} to your pokedex.")

def add_active_pokemon(guild_id, user_id, pokemon_obj):
    user_data = read_user_record(guild_id, user_id)
    if user_data is None:
        user_data = create_user_record(guild_id, user_id)
    if len(user_data["active_pokemon"]) < 6:
        user_data["active_pokemon"].append(pokemon_obj)
        update_user_power(user_data)
        update_user_record(guild_id, user_id, user_data)
        print(f"[Output] Added Pokémon {pokemon_obj.get('name', pokemon_obj.get('id'))} to your {user_id}'s active team.")
    else:
        print(f"[Output] User {user_id} already has 6 active Pokémon.")

def remove_active_pokemon(guild_id, user_id, index):
    user_data = read_user_record(guild_id, user_id)
    if user_data is None or not user_data["active_pokemon"]:
        print(f"[Output] No active Pokémon to remove.")
        return False
    if 0 <= index < len(user_data["active_pokemon"]):
        removed = user_data["active_pokemon"].pop(index)
        update_user_power(user_data)
        update_user_record(guild_id, user_id, user_data)
        print(f"[Output] Removed Pokémon {removed.get('name', removed.get('id'))} from your {user_id}'s active team.")
        return True
    else:
        print(f"[Output] Invalid index {index} for removing active Pokémon for user {user_id}.")
        return False

async def add_pokemon_to_player(bot, guild_id, user_id, pokemon_id, interaction=None):
    user_data = read_user_record(guild_id, user_id)
    if user_data is None:
        user_data = create_user_record(guild_id, user_id)

    pokemon_obj = next((p for p in bot.pokemon if p.get("id") == pokemon_id), None)
    if not pokemon_obj:
        return "not_found"

    if pokemon_id not in user_data["pokedex"]:
        user_data["pokedex"].append(pokemon_id)

    if any(p.get("id") == pokemon_id for p in user_data["active_pokemon"]):
        return "duplicate"

    if len(user_data["active_pokemon"]) < 6:
        user_data["active_pokemon"].append(pokemon_obj)
        update_user_power(user_data)
        update_user_record(guild_id, user_id, user_data)
        print(f"[Output] Added Pokémon {pokemon_obj.get('name', pokemon_obj.get('id'))} to user {user_id}'s active team.")
        return "success"

    if interaction is not None:
        class ReplacePokemonView(discord.ui.View):
            def __init__(self, active_pokemon):
                super().__init__(timeout=180)
                for idx, poke in enumerate(active_pokemon):
                    label = f"{poke.get('name', str(poke.get('id', '?')))} (CP: {poke.get('cp', '?')})"
                    self.add_item(discord.ui.Button(label=f"{idx+1}: {label}", style=discord.ButtonStyle.primary, custom_id=str(idx)))

            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, custom_id="cancel")
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_message("Cancelled replacement.", ephemeral=True)
                self.stop()

        active_pokemon = user_data["active_pokemon"]
        description = "\n".join([
            f"{idx+1}: {poke.get('name', poke.get('id'))} (CP: {poke.get('cp', '?')})"
            for idx, poke in enumerate(active_pokemon)
        ])
        embed = discord.Embed(
            title="Active Pokémon Full",
            description=f"You already have 6 active Pokémon:\n{description}\n\nSelect one to replace.",
            color=discord.Color.orange()
        )
        view = ReplacePokemonView(active_pokemon)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        # Wait for button click
        original_msg = await interaction.original_response()
        def check(i):
            return i.user.id == user_id and i.message.id == original_msg.id
        try:
            button_interaction = await bot.wait_for("interaction", check=check, timeout=60)
            if button_interaction.data["custom_id"] == "cancel":
                return "cancel"
            idx = int(button_interaction.data["custom_id"])
            removed = user_data["active_pokemon"].pop(idx)
            # Prevent adding duplicate after replacement
            if any(p.get("id") == pokemon_id for p in user_data["active_pokemon"]):
                await button_interaction.response.send_message(
                    f"You already have {pokemon_obj.get('name', pokemon_obj.get('id'))} in your active team!", ephemeral=True
                )
                # Put the removed Pokémon back
                user_data["active_pokemon"].insert(idx, removed)
                return "duplicate"
            user_data["active_pokemon"].append(pokemon_obj)
            update_user_power(user_data)
            update_user_record(guild_id, user_id, user_data)
            await button_interaction.response.send_message(
                f"Replaced {removed.get('name', removed.get('id'))} with {pokemon_obj.get('name', pokemon_obj.get('id'))} in your active team.",
                ephemeral=True
            )
            print(f"[Output] Replaced Pokémon for user {user_id}: {removed.get('name', removed.get('id'))} -> {pokemon_obj.get('name', pokemon_obj.get('id'))}")
            return "success"
        except Exception as e:
            print(f"[ERROR] Replacement selection failed: {e}")
            await interaction.followup.send("No selection made. Pokémon not added.", ephemeral=True)
            return "timeout"
    else:
        print(f"[Output] User {user_id} already has 6 active Pokémon. No interaction provided for replacement.")
        return "full"

def add_pokemon_to_player_no_interaction(bot, guild_id, user_id, pokemon_id):
    user_data = read_user_record(guild_id, user_id)
    if user_data is None:
        user_data = create_user_record(guild_id, user_id)

    pokemon_obj = next((p for p in bot.pokemon if p.get("id") == pokemon_id), None)
    if not pokemon_obj:
        return "not_found"

    if pokemon_id not in user_data["pokedex"]:
        user_data["pokedex"].append(pokemon_id)

    if any(p.get("id") == pokemon_id for p in user_data["active_pokemon"]):
        return "duplicate"

    if len(user_data["active_pokemon"]) < 6:
        user_data["active_pokemon"].append(pokemon_obj)
        update_user_power(user_data)
        update_user_record(guild_id, user_id, user_data)
        print(f"[Output] Added Pokémon {pokemon_obj.get('name', pokemon_obj.get('id'))} to user {user_id}'s active team.")
        return "success"
    else:
        print(f"[Prompt] User {user_id} already has 6 active Pokémon:")
        for idx, poke in enumerate(user_data["active_pokemon"]):
            print(f"{idx+1}: {poke.get('name', poke.get('id'))} (CP: {poke.get('cp', '?')})")
        try:
            idx = int(input(f"Enter the number (1-6) of the Pokémon to replace for user {user_id}, or 0 to cancel: ")) - 1
            if idx < 0 or idx >= 6:
                print("[Prompt] Replacement cancelled or invalid.")
                return "full"
            removed = user_data["active_pokemon"].pop(idx)
            if any(p.get("id") == pokemon_id for p in user_data["active_pokemon"]):
                print(f"[Prompt] You already have {pokemon_obj.get('name', pokemon_obj.get('id'))} in your active team!")
                user_data["active_pokemon"].insert(idx, removed)
                return "duplicate"
            user_data["active_pokemon"].append(pokemon_obj)
            update_user_power(user_data)
            update_user_record(guild_id, user_id, user_data)
            print(f"[Output] Replaced Pokémon for user {user_id}: {removed.get('name', removed.get('id'))} -> {pokemon_obj.get('name', pokemon_obj.get('id'))}")
            return "success"
        except Exception as e:
            print(f"[ERROR] Replacement selection failed: {e}")
            return "timeout"

def update_user_power(user_data):
    """
    Updates the user's 'power' field based on the average CP of their active Pokémon.
    """
    active_pokemon = user_data.get("active_pokemon", [])
    if not active_pokemon:
        user_data["power"] = 0
    else:
        total_cp = sum(poke.get("cp", 0) for poke in active_pokemon)
        user_data["power"] = int(total_cp / len(active_pokemon))