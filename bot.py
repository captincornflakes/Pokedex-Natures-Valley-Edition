import discord
from discord.ext import commands
import os
import tracemalloc
import logging
import json
from utils.github_utils import load_github
from utils.database_utils import setup_database_connection
from utils.config_utils import load_config
from utils.wild_utils import wild_pokemon_spawn_clock
from utils.battle_channel_utils import monitor_all_battle_channels_clock
from utils.battle_commands_utils import on_message_battle_commands
from utils.hourly_item_grant import hourly_item_grant


handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
logging.basicConfig(level=logging.INFO, handlers=[handler])

config = load_config()
load_github(config)

# Load pokemon.json and abilities.json into bot attributes
def load_json_data(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# Define the intents for the bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

# Prefix and bot initialization
PREFIX = "!"

# Ensure application_id exists in config
application_id = int(config.get('application_id', 0))
bot = commands.AutoShardedBot(command_prefix=PREFIX, intents=intents, application_id=application_id, help_command=None)
bot.config = config
bot.db_connection = setup_database_connection(config)
bot.media = "https://echodebates.com/bot_media/pokemon/"

POKEMON_JSON_PATH = os.path.join("datastores", "pokemon.json")
ABILITIES_JSON_PATH = os.path.join("datastores", "abilities.json")
BADGES_JSON_PATH = os.path.join("datastores", "badges.json")
TYPES_JSON_PATH = os.path.join("datastores", "types.json")
ITEMS_JSON_PATH = os.path.join("datastores", "items.json")
# Load Pokémon and abilities data into bot attributes
bot.pokemon = load_json_data(POKEMON_JSON_PATH)
bot.abilities = load_json_data(ABILITIES_JSON_PATH)
bot.badges = load_json_data(BADGES_JSON_PATH)
bot.types = load_json_data(TYPES_JSON_PATH)
bot.items = load_json_data(ITEMS_JSON_PATH)
bot.spawnrate = 60
bot.pokeballrate = 3600

# Start memory tracking
tracemalloc.start()

# Function to load all Python files from a directory as extensions
async def load_extensions_from_folder(folder):
    for filename in os.listdir(folder):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = filename[:-3]
            module_path = f'{folder}.{module_name}'
            try:
                await bot.load_extension(module_path)
                print(f'Loaded extension: {module_path}')
            except Exception as e:
                print(f'Failed to load extension {module_path}. Reason: {e}')

@bot.event
async def on_ready():
    db_status = config['database'].get('status', 'Online') if 'database' in config else 'Online'
    activity = discord.Activity(type=discord.ActivityType.playing, name=db_status)
    await bot.change_presence(status=discord.Status.online, activity=activity)
    
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print(f"Shard ID: {bot.shard_id}")
    print(f"Total Shards: {bot.shard_count}")

    for shard_id, latency in bot.latencies:
        print(f"Shard ID: {shard_id} | Latency: {latency*1000:.2f}ms")

# In setup_hook, you can also add:
async def setup_hook():
    await load_extensions_from_folder('functions')
    await bot.tree.sync()
    bot.loop.create_task(wild_pokemon_spawn_clock(bot))
    bot.loop.create_task(monitor_all_battle_channels_clock(bot))
    bot.loop.create_task(hourly_item_grant(bot))
    
# Assign setup_hook to the bot
bot.setup_hook = setup_hook

@bot.event
async def on_message(message):
    await on_message_battle_commands(bot, message)
    await bot.process_commands(message)

# Run the bot with token
if __name__ == '__main__':
    token = config.get('token', '')
    if token:
        bot.run(token, log_handler=handler, log_level=logging.INFO)
    else:
        print("No token found in config! Please check your config.json file.")
