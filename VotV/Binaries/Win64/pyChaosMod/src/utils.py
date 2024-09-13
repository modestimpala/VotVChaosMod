import os
import configparser

def load_config():
    config = {}
    config_files = {
        'chatShop': 'chatShop.cfg',
        'emails': 'emails.cfg',
        'twitch': 'twitch.cfg',
        'voting': 'voting.cfg'
    }

    base_path = './pyChaosMod/'

    for section, filename in config_files.items():
        config_path = os.path.join(base_path, filename)
        parser = configparser.ConfigParser()
        # check if file exists
        if not os.path.exists(config_path):
            base_path = './'
            config_path = os.path.join(base_path, filename)
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Config file not found: {config_path} \n You may need to run the mod in-game once to generate the config files.")
        
        parser.read(config_path)
        
        config[section] = {}
        for section_name in parser.sections():
            for key, value in parser.items(section_name):
                # Convert to appropriate type
                if value.replace('.', '').isdigit():
                    if '.' in value:
                        config[section][key] = float(value)
                    else:
                        config[section][key] = int(value)
                elif value.lower() in ['true', 'false']:
                    config[section][key] = value.lower() == 'true'
                else:
                    config[section][key] = value

    # Add file paths
    config['files'] = {
        'emails_master': os.path.join(base_path, 'emails_master.json'),
        'shops_master': os.path.join(base_path, 'shops_master.json'),
        'commands': os.path.join(base_path, 'commands.json'),
        'emails_enable': os.path.join(base_path, 'emails_enable.txt'),
        'votes': os.path.join(base_path, 'votes.txt'),
        'enable': os.path.join(base_path, 'enable.txt'),
        'isVoting': os.path.join(base_path, 'voting_enabled.txt'),
        'shopOpen': os.path.join(base_path, 'shopOpen.txt'),
    }

    return config

def is_chaos_enabled(config):
    return os.path.exists(config['files']['enable'])