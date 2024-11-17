import os
import configparser

def find_base_path():
    """Determine the correct base path based on directory structure."""
    # Check if we're in the pyChaosMod directory
    if os.path.exists('./listen') or os.path.exists('./cfg'):
        return './'
    # Check if pyChaosMod is a subdirectory
    elif os.path.exists('./pyChaosMod/listen') or os.path.exists('./pyChaosMod/cfg'):
        return './pyChaosMod/'
    else:
        raise FileNotFoundError("Could not find pyChaosMod directory structure")

def load_config():
    """Load configuration files."""
    config = {}
    config_files = {
        'chatShop': 'chatShop.cfg',
        'emails': 'emails.cfg',
        'twitch': 'twitch.cfg',
        'voting': 'voting.cfg',
        'direct': 'direct.cfg',
        'hints': 'hints.cfg',
    }
    
    # Determine base paths
    base_path = find_base_path()
    base_path_listen = os.path.join(base_path, 'listen')
    base_path_cfg = os.path.join(base_path, 'cfg')

    # Process each config file
    for section, filename in config_files.items():
        config_path = os.path.join(base_path_cfg, filename)
        parser = configparser.ConfigParser()
        
        # If file doesn't exist in primary location, try alternate location
        if not os.path.exists(config_path):
            alt_config_path = os.path.join('./cfg', filename)
            if os.path.exists(alt_config_path):
                config_path = alt_config_path
            else:
                raise FileNotFoundError(
                    f"Config file not found: {config_path} or {alt_config_path}\n"
                    "You may need to run the mod in-game once to generate the config files."
                )
        
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
        'hints_master': os.path.join(base_path, 'hints_master.json'),
        'direct_master': os.path.join(base_path, 'direct_master.json'),
        'emails_enable': os.path.join(base_path_listen, 'emails_enable.txt'),
        'commands': os.path.join(base_path_cfg, 'twitchChannelPoints.cfg'),
        'votes': os.path.join(base_path_listen, 'votes.txt'),
        'enable': os.path.join(base_path_listen, 'enable.txt'),
        'isVoting': os.path.join(base_path_listen, 'voting_enabled.txt'),
        'shopOpen': os.path.join(base_path_listen, 'shopOpen.txt'),
    }

    # Check for alternate commands file location
    if not os.path.exists(config['files']['commands']):
        config['files']['commands'] = os.path.join(base_path, 'twitchChannelPoints.cfg')

    config['version'] = '3.0.0'
    return config

def is_chaos_enabled(config):
    """Check if chaos is enabled."""
    return os.path.exists(config['files']['enable'])