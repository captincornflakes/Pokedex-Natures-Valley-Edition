import os
import json

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
        "settings": {}
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
