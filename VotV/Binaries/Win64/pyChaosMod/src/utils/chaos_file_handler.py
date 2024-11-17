import json
import time
import os
from typing import List, Dict, Any

class ChaosFileHandler:
    def __init__(self, master_file_path: str):
        """
        Initialize the ChaosFileHandler with the path to the master file.
        
        Args:
            master_file_path (str): Path to the master file that stores chaos commands
        """
        self.master_file = master_file_path

    def read_master_file(self) -> List[Dict[str, Any]]:
        """
        Read the master file and return its contents.
        
        Returns:
            List[Dict[str, Any]]: List of chaos command entries
        """
        if os.path.exists(self.master_file):
            with open(self.master_file, 'r') as f:
                return json.load(f)
        return []

    def write_master_file(self, data: List[Dict[str, Any]]) -> None:
        """
        Write data to the master file.
        
        Args:
            data (List[Dict[str, Any]]): List of chaos command entries to write
        """
        with open(self.master_file, 'w') as f:
            json.dump(data, f, indent=2)

    async def process_chaos_command(self, command_type: str, command: str) -> None:
        """
        Process and store a new chaos command.
        
        Args:
            command_type (str): Type of the command (e.g., 'trigger_chaos', 'trigger_event')
            command (str): The actual command or event to be processed
        """
        directs = self.read_master_file()
        directs.append({
            "type": command_type,
            "command": command,
            "timestamp": time.time(),
            "processed": False
        })
        self.write_master_file(directs)