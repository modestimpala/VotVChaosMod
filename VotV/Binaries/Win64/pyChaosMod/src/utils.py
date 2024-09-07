import json
import os

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

def is_chaos_enabled(config):
    return os.path.exists(config['files']['enable'])

