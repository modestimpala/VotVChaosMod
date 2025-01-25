import os
import configparser
from typing import Dict, Any, Callable, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import asyncio
import logging
from functools import partial

logger = logging.getLogger(__name__)

class AsyncConfigManager:
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.base_path = self._find_base_path()
        self.observer = None
        self._change_callbacks: List[Callable] = []
        self._shutdown_event = asyncio.Event()
        self._loop = asyncio.get_event_loop()
        
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
        config_files = {
            'chatShop': 'chatShop.cfg',
            'emails': 'emails.cfg',
            'twitch': 'twitch.cfg',
            'voting': 'voting.cfg',
            'direct': 'direct.cfg',
            'hints': 'hints.cfg',
            'misc': 'misc.cfg',
        }
        
        base_path_listen = os.path.join(self.base_path, 'listen')
        base_path_cfg = os.path.join(self.base_path, 'cfg')
        
        for section, filename in config_files.items():
            config_path = os.path.join(base_path_cfg, filename)
            parser = configparser.ConfigParser()
            
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
            
        config['version'] = '3.1.2'
        self.config = config
        return config

    class ConfigFileHandler(FileSystemEventHandler):
        def __init__(self, config_manager):
            self.config_manager = config_manager
            self.last_modified_times: Dict[str, float] = {}
            
        def on_modified(self, event):
            if not event.is_directory and event.src_path.endswith('.cfg'):
                current_time = os.path.getmtime(event.src_path)
                last_time = self.last_modified_times.get(event.src_path, 0)
                
                if current_time > last_time:
                    self.last_modified_times[event.src_path] = current_time
                    self.config_manager._loop.call_soon_threadsafe(
                        self.config_manager._handle_config_change
                    )

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