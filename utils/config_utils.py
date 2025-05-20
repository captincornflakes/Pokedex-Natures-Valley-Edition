import json

def load_config(config_file="datastores/config.json"):
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            print(f"Loaded configuration from {config_file}.")
            return config
    except FileNotFoundError:
        print(f"{config_file} not found...")
        return {}