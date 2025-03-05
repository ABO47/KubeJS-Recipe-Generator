import json

def load_config():
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        return config.get("item_file_path"), config.get("recipes_file_path")
    except FileNotFoundError:
        return None, None

def save_config(item_file_path, recipes_file_path):
    config = {
        "item_file_path": item_file_path,
        "recipes_file_path": recipes_file_path
    }
    with open("config.json", "w") as f:
        json.dump(config, f)