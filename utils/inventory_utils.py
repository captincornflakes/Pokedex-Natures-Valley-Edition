import os
import json

SERVERS_DIR = os.path.join(os.getcwd(), "servers")

def get_player_inventory(guild_id, user_id):
    """Load a player's inventory from their data file."""
    user_file = os.path.join(SERVERS_DIR, str(guild_id), f"{user_id}.json")
    if not os.path.isfile(user_file):
        return []
    with open(user_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("inventory", [])

def save_player_inventory(guild_id, user_id, inventory):
    """Save a player's inventory to their data file."""
    user_file = os.path.join(SERVERS_DIR, str(guild_id), f"{user_id}.json")
    if not os.path.isfile(user_file):
        data = {}
    else:
        with open(user_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    data["inventory"] = inventory
    with open(user_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def add_item_to_inventory(guild_id, user_id, item_id, amount=1):
    """Add an item to a player's inventory."""
    inventory = get_player_inventory(guild_id, user_id)
    for entry in inventory:
        if entry["id"] == item_id:
            entry["amount"] += amount
            break
    else:
        inventory.append({"id": item_id, "amount": amount})
    save_player_inventory(guild_id, user_id, inventory)

def remove_item_from_inventory(guild_id, user_id, item_id, amount=1):
    """Remove an item from a player's inventory. Returns True if successful."""
    inventory = get_player_inventory(guild_id, user_id)
    for entry in inventory:
        if entry["id"] == item_id:
            if entry["amount"] >= amount:
                entry["amount"] -= amount
                if entry["amount"] == 0:
                    inventory.remove(entry)
                save_player_inventory(guild_id, user_id, inventory)
                return True
            else:
                return False
    return False

def has_item(guild_id, user_id, item_id, amount=1):
    """Check if a player has at least a certain amount of an item."""
    inventory = get_player_inventory(guild_id, user_id)
    for entry in inventory:
        if entry["id"] == item_id and entry["amount"] >= amount:
            return True
    return False

def get_item_amount(guild_id, user_id, item_id):
    """Get the amount of a specific item a player has."""
    inventory = get_player_inventory(guild_id, user_id)
    for entry in inventory:
        if entry["id"] == item_id:
            return entry["amount"]
    return 0