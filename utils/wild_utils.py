import random
import os
import json
import discord
import asyncio
import time
from utils.player_handler import add_pokemon_to_player, read_user_record

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

async def wild_pokemon_spawn_clock(bot):
    await bot.wait_until_ready()
    while not bot.is_closed():
        await spawn_wild_pokemon_in_all_servers(bot)
        await asyncio.sleep(bot.spawnrate)  # Use bot.spawnrate for interval

def log_active_spawn(guild_id, pokemon_id, status="active", trainer=None):
    """
    Logs the current active wild Pokémon spawn to the server's data.json file.
    Only one active spawn is kept (overwrites previous).
    Stores: id, spawn_time, status, trainer.
    """
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

    # Overwrite the current active spawn
    data["active_spawn"] = spawn_entry

    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"[Output] Logged active spawn for guild {guild_id}: {spawn_entry}")

def update_active_spawn_status(guild_id, pokemon_id, status, trainer):
    """
    Updates the status and trainer for the current active spawn in the server's data.json.
    """
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

def calculate_capture_success(player_power, pokemon_cp):
    if player_power <= 0 or pokemon_cp <= 0:
        return False  # Invalid values

    # Calculate chance (between 5% and 95%)
    success_chance = min(0.95, max(0.05, player_power / (player_power + pokemon_cp)))
    roll = random.random()
    return roll < success_chance

class CaptureButton(discord.ui.View):
    def __init__(self, guild_id, pokemon_id):
        super().__init__(timeout=60)
        self.guild_id = guild_id
        self.pokemon_id = pokemon_id

    @discord.ui.button(label="Capture Pokémon", style=discord.ButtonStyle.green)
    async def capture(self, interaction: discord.Interaction, button: discord.ui.Button):
        trainer_name = interaction.user.display_name
        user_id = interaction.user.id
        guild_id = self.guild_id
        pokemon_id = self.pokemon_id

        # Check if the Pokémon is still active in data.json
        servers_dir = os.path.join(os.getcwd(), "servers")
        data_file = os.path.join(servers_dir, str(guild_id), "data.json")
        if not os.path.isfile(data_file):
            await interaction.response.send_message("Server data not found.", ephemeral=True)
            return
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        spawn = data.get("active_spawn")
        if not spawn or spawn.get("id") != pokemon_id or spawn.get("status") != "active":
            await interaction.response.send_message("The Pokémon has left the area!", ephemeral=True)
            return

        # Get player power and pokemon cp
        user_data = read_user_record(guild_id, user_id)
        if user_data is None:
            await interaction.response.send_message("You need to set up your profile first with `/join`.", ephemeral=True)
            return

        player_power = user_data.get("power", 0)
        # Find the Pokémon object from bot.pokemon (bot is accessible via interaction.client)
        bot = interaction.client
        pokemon_obj = next((p for p in bot.pokemon if p.get("id") == pokemon_id), None)
        if not pokemon_obj:
            await interaction.response.send_message("Pokémon data not found.", ephemeral=True)
            return
        pokemon_cp = pokemon_obj.get("cp", 100)

        # Calculate capture success
        success = calculate_capture_success(player_power, pokemon_cp)
        if success:
            update_active_spawn_status(guild_id, pokemon_id, "captured", trainer_name)
            await add_pokemon_to_player(bot, guild_id, user_id, pokemon_id, interaction)
            await interaction.response.send_message(
                f"🎉 {trainer_name} successfully captured {pokemon_obj.get('name', 'the Pokémon')}!", ephemeral=False
            )
        else:
            update_active_spawn_status(guild_id, pokemon_id, "escaped", trainer_name)
            await interaction.response.send_message(
                f"{pokemon_obj.get('name', 'The Pokémon')} broke free! Better luck next time, {trainer_name}.", ephemeral=False
            )
        # Disable the button after use
        self.capture.disabled = True
        await interaction.message.edit(view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        # Optionally, you can send a message to the channel that the capture has expired
        guild_id = self.guild_id
        pokemon_id = self.pokemon_id
        servers_dir = os.path.join(os.getcwd(), "servers")
        data_file = os.path.join(servers_dir, str(guild_id), "data.json")
        if os.path.isfile(data_file):
            with open(data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            spawn = data.get("active_spawn")
            if spawn and spawn.get("id") == pokemon_id:
                # Mark as escaped due to timeout
                update_active_spawn_status(guild_id, pokemon_id, "escaped", "System")
        await super().on_timeout()
