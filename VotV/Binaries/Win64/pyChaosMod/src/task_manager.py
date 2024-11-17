import asyncio
import logging
import traceback
from typing import Dict

logger = logging.getLogger(__name__)

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, asyncio.Task] = {}
        self.should_run = True
        self.restart_delays = {}  # Track delay times for exponential backoff
        self.max_restart_delay = 300  # Maximum delay of 5 minutes
        self.base_delay = 1  # Start with 1 second delay
        
    async def start_task(self, name: str, coro, *args, **kwargs):
        """Start a task with automatic restart on failure."""
        while self.should_run:
            try:
                self.tasks[name] = asyncio.create_task(coro(*args, **kwargs))
                await self.tasks[name]
            except asyncio.CancelledError:
                logger.info(f"Task {name} was cancelled")
                break
            except Exception as e:
                if not self.should_run:
                    break
                    
                logger.error(f"Task {name} failed with error: {str(e)}")
                logger.error(f"Traceback for {name}:")
                traceback.print_exc()
                
                # Calculate delay with exponential backoff
                delay = self.get_next_delay(name)
                logger.info(f"Restarting {name} in {delay} seconds...")
                await asyncio.sleep(delay)
            finally:
                if name in self.tasks:
                    del self.tasks[name]

    def get_next_delay(self, name: str) -> float:
        """Calculate the next retry delay with exponential backoff."""
        current_delay = self.restart_delays.get(name, self.base_delay)
        next_delay = min(current_delay * 2, self.max_restart_delay)
        self.restart_delays[name] = next_delay
        return current_delay

    def reset_delay(self, name: str):
        """Reset the retry delay for a task."""
        if name in self.restart_delays:
            del self.restart_delays[name]

    async def stop_all(self):
        """Stop all tasks gracefully."""
        self.should_run = False
        for name, task in self.tasks.items():
            if not task.done():
                logger.info(f"Cancelling task: {name}")
                task.cancel()
                
        await asyncio.gather(*self.tasks.values(), return_exceptions=True)
