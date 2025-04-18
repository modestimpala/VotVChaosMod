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
        consecutive_failures = 0
        
        while self.should_run:
            try:
                # Add initial delay if this is a restart after multiple failures
                if consecutive_failures > 3:
                    await asyncio.sleep(5.0)  # Force minimum 5-second delay after repeated failures
                
                self.tasks[name] = asyncio.create_task(coro(*args, **kwargs))
                await self.tasks[name]
                # If we get here, task completed normally
                consecutive_failures = 0
            except asyncio.CancelledError:
                logger.info(f"Task {name} was cancelled")
                break
            except Exception as e:
                if not self.should_run:
                    break
                    
                consecutive_failures += 1
                logger.error(f"Task {name} failed with error: {str(e)}")
                logger.error(f"Traceback for {name}:")
                traceback.print_exc()
                
                # Calculate delay with exponential backoff
                delay = self.get_next_delay(name)
                # Use longer delay for network-related errors
                if "address already in use" in str(e).lower() or "socket" in str(e).lower():
                    delay = max(delay, 10.0)  # Minimum 10-second delay for network errors
                    
                logger.info(f"Restarting {name} in {delay} seconds...")
                await asyncio.sleep(delay)
            finally:
                if name in self.tasks:
                    del self.tasks[name]

    async def stop_task(self, name: str):
        """Stop a specific task gracefully."""
        if name not in self.tasks:
            logger.debug(f"Task {name} not found - may have already been stopped")
            return

        task = self.tasks[name]
        if not task.done():
            logger.info(f"Cancelling task: {name}")
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info(f"Task {name} cancelled successfully")
            except Exception as e:
                logger.error(f"Error while stopping task {name}: {e}")

        await self.tasks.pop(name, None)  # Safely remove task
        self.reset_delay(name)

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
        logger.info("TaskManager stopping all tasks...")
        self.should_run = False
        
        # Make a copy of tasks to avoid dict changes during iteration
        tasks_to_stop = list(self.tasks.items())
        
        # First attempt to cancel all tasks
        for name, task in tasks_to_stop:
            if not task.done():
                logger.info(f"Cancelling task: {name}")
                task.cancel()
        
        if tasks_to_stop:
            # Wait for all tasks with a timeout
            try:
                await asyncio.wait_for(
                    asyncio.gather(*[task for _, task in tasks_to_stop], return_exceptions=True),
                    timeout=10.0
                )
            except asyncio.TimeoutError:
                logger.warning("Some tasks did not terminate within timeout, forcing shutdown")
        
        # Clear any remaining tasks
        self.tasks.clear()
        logger.info("All tasks stopped")
