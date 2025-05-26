import os
import json
import time
import discord
import asyncio

# Store server data in the 'servers' folder at the project root
SERVERS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "servers")

def ensure_servers_folder():
    """Create the servers folder if it doesn't exist."""
    if not os.path.exists(SERVERS_DIR):
        os.makedirs(SERVERS_DIR)
        print(f"[Output] Created servers folder at {SERVERS_DIR}")
    else:
        print(f"[Output] Servers folder exists at {SERVERS_DIR}")

# Ensure servers folder exists when this util loads
ensure_servers_folder()

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

def update_active_spawn_status(guild_id, pokemon_id, status, trainer):
    servers_dir = os.path.join(os.getcwd(), "servers")
    data_file = os.path.join(servers_dir, str(guild_id), "data.json")
    if not os.path.isfile(data_file):
        return

    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    updated = False
    spawn = data.get("active_spawn")
    if spawn and spawn["id"] == pokemon_id and spawn["status"] == "active":
        spawn["status"] = status
        spawn["trainer"] = trainer
        spawn["spawn_time"] = int(time.time())  # Update spawn_time to now
        data["active_spawn"] = spawn
        updated = True

    if updated:
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"[Output] Updated spawn {pokemon_id} to status '{status}' for guild {guild_id} (trainer: {trainer})")


def setup_server_savedata(guild_id):
    os.makedirs(SERVERS_DIR, exist_ok=True)
    guild_folder = os.path.join(SERVERS_DIR, str(guild_id))
    os.makedirs(guild_folder, exist_ok=True)
    data_file = os.path.join(guild_folder, "data.json")
    if not os.path.exists(data_file):
        generate_server_data(guild_id)
        print(f"[Output] Created server data for guild {guild_id}")
    else:
        print(f"[Output] Server data for guild {guild_id} already exists")
    return guild_folder

def generate_server_data(guild_id):
    guild_folder = os.path.join(SERVERS_DIR, str(guild_id))
    os.makedirs(guild_folder, exist_ok=True)
    data_file = os.path.join(guild_folder, "data.json")
    default_data = {
        "guild_id": guild_id,
        "created": True,
        "settings": {}, 
        "channels": {},
        "active_spawn": {},
        "active_battles": []
        }
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(default_data, f, indent=2)
    print(f"[Output] Generated new data.json for guild {guild_id}")
    return data_file

def read_server_data(guild_id):
    data_file = os.path.join(SERVERS_DIR, str(guild_id), "data.json")
    if not os.path.exists(data_file):
        print(f"[Output] No data.json found for guild {guild_id}")
        return None
    with open(data_file, "r", encoding="utf-8") as f:
        print(f"[Output] Read data.json for guild {guild_id}")
        return json.load(f)

def update_server_data(guild_id, data):
    data_file = os.path.join(SERVERS_DIR, str(guild_id), "data.json")
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"[Output] Updated data.json for guild {guild_id}")

def delete_server_data(guild_id):
    data_file = os.path.join(SERVERS_DIR, str(guild_id), "data.json")
    if os.path.exists(data_file):
        os.remove(data_file)
        print(f"[Output] Deleted data.json for guild {guild_id}")
    else:
        print(f"[Output] No data.json to delete for guild {guild_id}")

async def generate_pokemon_channels(guild):
    setup_server_savedata(guild.id)
    data = read_server_data(guild.id) or {}

    # Check if already created
    if "channels" in data and all(k in data["channels"] for k in ["guide", "general", "wild"]):
        print(f"[Output] Pokémon channels already exist for guild {guild.id}")
        return data["channels"]

    # Create category
    category = discord.utils.get(guild.categories, name="pokemon")
    if not category:
        category = await guild.create_category("pokemon")
        print(f"[Output] Created category 'pokemon' in guild {guild.id}")

    # Create channels
    channel_names = ["guide", "general", "wild"]
    channel_ids = {}
    for name in channel_names:
        channel = discord.utils.get(category.channels, name=name)
        if not channel:
            channel = await guild.create_text_channel(name, category=category)
            print(f"[Output] Created channel '{name}' in category 'pokemon' for guild {guild.id}")
        channel_ids[name] = channel.id

    # Save to data.json
    data["channels"] = {
        "category": category.id,
        **channel_ids
    }
    update_server_data(guild.id, data)
    print(f"[Output] Saved Pokémon channel IDs to data.json for guild {guild.id}")
    return data["channels"]

async def send_welcome_embed(channel, image_url=None):
    print(f"[Debug] Sending welcome embed to channel {channel.id}")
    welcome_embed = discord.Embed(
        title="Welcome to the World of Pokémon!",
        description=(
            "To get started on your adventure, use `/join` to set up your trainer profile.\n"
            "Then, use `/starter` to pick your very first Pokémon!\n\n"
            "Good luck, Trainer!"
        ),
        color=discord.Color.green()
    )
    if image_url:
        welcome_embed.set_image(url=image_url)
    await channel.send(embed=welcome_embed)

async def send_general_guide_embed(channel, image_url=None):
    print(f"[Debug] Sending general guide embed to channel {channel.id}")
    guide_embed = discord.Embed(
        title="Pokédex Bot Guide",
        description=(
            "This channel contains helpful information about using the Pokédex bot.\n\n"
            "**Getting Started:**\n"
            "• Use `/pokedex` to view your Pokédex.\n"
            "• Use `/pokedex_summary` to view your Pokédex summary.\n"
            "• Catch wild Pokémon in the #wild channel!\n\n"
            "For more commands and help, use `/help`."
        ),
        color=discord.Color.gold()
    )
    if image_url:
        guide_embed.set_image(url=image_url)
    await channel.send(embed=guide_embed)

async def send_battle_guide_embed(channel):
    print(f"[Debug] Sending battle guide embed to channel {channel.id}")
    battle_guide_embed = discord.Embed(
        title="Pokédex Battle Guide",
        description=(
            "**How to Battle:**\n"
            "• Use `/challenge @user` to start a battle with another trainer.\n"
            "• Use `/endbattle` to end the current battle.\n"
            "**How to Battle:**\n"
            "• The following have to be sent in the battle channel.\n"
            "• When the battle channel opens, use `!choose` to show your Pokémon.\n"
            "• When the battle channel opens, use `!choose #<slot>` to select your Pokémon.\n"
            "• Once both trainers have chosen, use `!attack` to take your turn.\n"
            "• The battle is best of 3 rounds. Each round, the winner is tracked.\n"
            "• When a Pokémon faints, choose your next one with `!choose`.\n"
            "• The winner is the trainer who wins the most rounds!\n\n"
            "**Commands:**\n"
            "• `!choose` — Pick your Pokémon for the round.\n"
            "• `!attack` — Attack your opponent on your turn.\n"
            "• `!forfeit` — Forfeit the battle.\n\n"
            "Good luck, Trainers!"
        ),
        color=discord.Color.blue()
    )
    battle_guide_embed.set_thumbnail(url="https://bots.media/pokemon/25.png")
    await channel.send(embed=battle_guide_embed)

async def setup_guide_channel(guild):
    setup_server_savedata(guild.id)
    data = read_server_data(guild.id) or {}

    # Find or create the 'pokemon' category
    category = discord.utils.get(guild.categories, name="pokemon")
    if not category:
        category = await guild.create_category("pokemon")
        print(f"[Output] Created category 'pokemon' in guild {guild.id}")

    # Find or create the 'guide' channel
    guide_channel = discord.utils.get(category.channels, name="guide")
    if not guide_channel:
        guide_channel = await guild.create_text_channel("guide", category=category)
        print(f"[Output] Created channel 'guide' in category 'pokemon' for guild {guild.id}")

    # Set permissions: everyone can read, but not send messages
    overwrite = {
        guild.default_role: discord.PermissionOverwrite(
            read_messages=True,
            send_messages=False,
            add_reactions=False,
            send_tts_messages=False,
            manage_messages=False,
            embed_links=True,
            attach_files=False,
            mention_everyone=False
        )
    }
    await guide_channel.edit(overwrites=overwrite)
    print(f"[Output] Set 'guide' channel to read-only in guild {guild.id}")

    # Wait 5 seconds before sending embeds (now just a wait, no embeds will be sent)
    await asyncio.sleep(5)

    # Update data.json with the guide channel ID
    data.setdefault("channels", {})
    data["channels"]["guide"] = guide_channel.id
    update_server_data(guild.id, data)
    print(f"[Output] Saved guide channel ID to data.json for guild {guild.id}")
    return guide_channel
