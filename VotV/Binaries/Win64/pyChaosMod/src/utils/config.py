import os
import configparser
from typing import Dict, Any, Callable, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import asyncio
import logging
from functools import partial

logger = logging.getLogger(__name__)

class NoSpacesConfigParser(configparser.ConfigParser):
    def write(self, fp, space_around_delimiters=False):
        """Write an .ini-format representation of the configuration state."""
        # Override the default behavior by setting space_around_delimiters=False
        super().write(fp, space_around_delimiters=False)


class AsyncConfigManager:
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.base_path = self._find_base_path()
        self.observer = None
        self._change_callbacks: List[Callable] = []
        self._shutdown_event = asyncio.Event()
        self._loop = asyncio.get_event_loop()
        self._config_files = {
            'chatShop': 'chatShop.cfg',
            'emails': 'emails.cfg',
            'twitch': 'twitch.cfg',
            'voting': 'voting.cfg',
            'direct': 'direct.cfg',
            'hints': 'hints.cfg',
            'misc': 'misc.cfg',
        }
        self._config_parsers = {}  # Store parsers to maintain file structure
        
    # Dictionary-like access methods
    def __getitem__(self, key):
        """Allow dictionary-like access to config sections: config['section']"""
        return self.config[key]
        
    def __setitem__(self, key, value):
        """Allow dictionary-like setting of config sections: config['section'] = {...}"""
        self.config[key] = value
        
    def __contains__(self, key):
        """Support 'in' operator: 'section' in config"""
        return key in self.config
        
    def get(self, key, default=None):
        """Mimic dict.get() method"""
        return self.config.get(key, default)
        
    def _find_base_path(self) -> str:
        if os.path.exists('./listen') or os.path.exists('./cfg'):
            return './'
        elif os.path.exists('./pyChaosMod/listen') or os.path.exists('./pyChaosMod/cfg'):
            return './pyChaosMod/'
        else:
            raise FileNotFoundError("Could not find pyChaosMod directory structure")

    def register_change_callback(self, callback: Callable[[Dict[str, Any]], None]):
        self._change_callbacks.append(callback)

    def load_config(self) -> Dict[str, Any]:
        config: Dict[str, Any] = {}
        
        base_path_listen = os.path.join(self.base_path, 'listen')
        base_path_cfg = os.path.join(self.base_path, 'cfg')
        
        for section, filename in self._config_files.items():
            config_path = os.path.join(base_path_cfg, filename)
            parser = NoSpacesConfigParser()
            
            if not os.path.exists(config_path):
                alt_config_path = os.path.join('./cfg', filename)
                if os.path.exists(alt_config_path):
                    config_path = alt_config_path
                else:
                    raise FileNotFoundError(
                        f"Config file not found: {config_path} or {alt_config_path}\n"
                        "You may need to run the mod in-game once to generate the config files."
                    )
            
            try:
                parser.read(config_path)
            except configparser.ParsingError as e:
                logger.error(f"Config parsing error in {config_path}: {e}")
                logger.info(f"Attempting to backup corrupted config file: {filename}")
                
                # Create backup of corrupted file
                backup_path = f"{config_path}.corrupted.backup"
                try:
                    os.rename(config_path, backup_path)
                    logger.info(f"Corrupted config backed up to: {backup_path}")
                except OSError:
                    logger.warning(f"Could not backup corrupted config file: {config_path}")
                
                logger.warning(f"Config file {config_path} backed up to {backup_path}. "
                               "Please run the mod in-game to regenerate it.")
                
                raise FileNotFoundError(
                    f"Malformed config file: {config_path}\n"
                    f"Please check the file format or delete it to regenerate. Error: {e}"
                )
                    
            except configparser.Error as e:
                logger.error(f"General config error in {config_path}: {e}")
                raise FileNotFoundError(
                    f"Config file error: {config_path}\n"
                    f"Try deleting the file to regenerate it. Error: {e}"
                )
            except Exception as e:
                logger.error(f"Unexpected error reading config {config_path}: {e}")
                raise FileNotFoundError(
                    f"Unexpected error reading config: {config_path}\n"
                    f"Error: {e}"
                )
            
            self._config_parsers[section] = {
                'parser': parser,
                'path': config_path
            }
            
            config[section] = {}
            for section_name in parser.sections():
                for key, value in parser.items(section_name):
                    if value.replace('.', '').isdigit():
                        if '.' in value:
                            config[section][key] = float(value)
                        else:
                            config[section][key] = int(value)
                    elif value.lower() in ['true', 'false']:
                        config[section][key] = value.lower() == 'true'
                    else:
                        config[section][key] = value

        config['files'] = {
            'commands': os.path.join(base_path_cfg, 'twitchChannelPoints.cfg')
        }
        
        if not os.path.exists(config['files']['commands']):
            config['files']['commands'] = os.path.join(self.base_path, 'twitchChannelPoints.cfg')
                       
        # VERSION
        config['version'] = '3.2.0'
        # VERSION
        
        self.config = config
        return config

    def update_config_value(self, section: str, key: str, value: Any) -> bool:
        """
        Update a configuration value in memory
        
        Args:
            section: The section name in the config
            key: The key to update
            value: The new value
            
        Returns:
            bool: True if successful, False otherwise
        """
        if section not in self.config:
            logger.error(f"Section {section} not found in config")
            return False
            
        self.config[section][key] = value
        return True
        
    def save_config(self, section: str = None) -> bool:
        """
        Save the configuration to the file system
        
        Args:
            section: Optional section to save. If None, saves all sections
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if section is not None:
                return self._save_section(section)
                
            # Save all sections
            success = True
            for section_name in self._config_parsers:
                if not self._save_section(section_name):
                    success = False
            return success
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
            
    def _save_section(self, section: str) -> bool:
        """
        Save a specific section to its config file
        
        Args:
            section: The section to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        if section not in self._config_parsers:
            logger.error(f"No parser found for section {section}")
            return False
            
        parser_info = self._config_parsers[section]
        parser = parser_info['parser']
        path = parser_info['path']
        
        # Update parser with current values
        for section_name in parser.sections():
            for key, value in parser.items(section_name):
                if key in self.config[section]:
                    # Convert Python types back to string for configparser
                    new_value = self.config[section][key]
                    if isinstance(new_value, bool):
                        new_value = 'true' if new_value else 'false'
                    parser.set(section_name, key, str(new_value))
        
        # Write to file
        try:
            with open(path, 'w') as configfile:
                parser.write(configfile)
            logger.info(f"Config section {section} saved to {path}")
            return True
        except Exception as e:
            logger.error(f"Error writing config file {path}: {e}")
            return False

    class ConfigFileHandler(FileSystemEventHandler):
        def __init__(self, config_manager):
            self.config_manager = config_manager
            self.last_modified_times: Dict[str, float] = {}
            self._is_our_write = False
            
        def on_modified(self, event):
            if not event.is_directory and event.src_path.endswith('.cfg'):
                # Skip if this is our own write operation
                if self._is_our_write:
                    self._is_our_write = False
                    return
                    
                current_time = os.path.getmtime(event.src_path)
                last_time = self.last_modified_times.get(event.src_path, 0)
                
                if current_time > last_time:
                    self.last_modified_times[event.src_path] = current_time
                    self.config_manager._loop.call_soon_threadsafe(
                        self.config_manager._handle_config_change
                    )
        
        def mark_our_write(self):
            """Mark that the next file change is from our own write operation"""
            self._is_our_write = True

    def _handle_config_change(self):
        try:
            self.load_config()
            for callback in self._change_callbacks:
                try:
                    callback(self.config)
                except Exception as e:
                    logger.error(f"Error in config change callback: {e}")
        except Exception as e:
            logger.error(f"Error reloading configuration: {e}")

    async def start(self) -> None:
        self.observer = Observer()
        handler = self.ConfigFileHandler(self)
        self._file_handler = handler  # Store reference to handler
        
        cfg_paths = [
            os.path.join(self.base_path, 'cfg')
        ]
        
        for path in cfg_paths:
            if os.path.exists(path):
                self.observer.schedule(handler, path, recursive=False)
                logger.debug(f"Cfg Observer: {path} added")
                
        self.observer.start()
        
        try:
            while not self._shutdown_event.is_set():
                await asyncio.sleep(1)
        finally:
            await self.stop()

    async def stop(self) -> None:
        self._shutdown_event.set()
        if self.observer:
            self.observer.stop()
            self.observer.join()
        logger.info("Configuration manager stopped")

async def create_config_manager() -> AsyncConfigManager:
    manager = AsyncConfigManager()
    manager.load_config()
    asyncio.create_task(manager.start())
    return manager

# Usage example:
# async def main():
#     config = await create_config_manager()
#     
#     # Getting config values - direct dictionary-like access
#     twitch_enabled = config['twitch'].get('enabled', False)
#     
#     # Checking if a section exists
#     if 'misc' in config:
#         print("Misc section exists")
#     
#     # Updating config values
#     config.update_config_value('twitch', 'enabled', True)
#     
#     # Save to disk
#     config.save_config('twitch')  # Save just twitch section
#     # or
#     config.save_config()  # Save all sections
#     
# if __name__ == "__main__":
#     asyncio.run(main())