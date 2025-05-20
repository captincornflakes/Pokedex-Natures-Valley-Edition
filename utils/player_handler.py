import os
import json

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
            "coin": 0,
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