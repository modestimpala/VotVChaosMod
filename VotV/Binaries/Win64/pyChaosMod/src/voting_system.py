import logging
import asyncio
import json

class VotingSystem:
    def __init__(self, config):
        self.config = config
        self.voting_active = False
        self.votes = {}  # key: option number, value: vote count
        self.voters = set()
        self.num_options = 0
        self.websocket_handler = None
        self.logger = logging.getLogger(__name__)
        self._vote_update_task = None

    def set_websocket_handler(self, websocket_handler):
        self.websocket_handler = websocket_handler
        
    async def send_votes_update(self):
        """Send current votes to the game via WebSocket."""
        if self.websocket_handler and self.websocket_handler.game_connection:
            try:
                # Convert votes to array format
                vote_counts = [self.votes.get(i, 0) for i in range(self.num_options)]
                
                message = {
                    "type": "vote_update",
                    "votes": vote_counts
                }
                
                await self.websocket_handler.game_connection.send(json.dumps(message))
                self.logger.info(f"Sent vote update: {vote_counts}")
            except Exception as e:
                self.logger.error(f"Failed to send vote update: {e}")
        else:
            self.logger.error("No game connection available to send vote update")

    async def vote_update_loop(self):
        """Continuously send vote updates while voting is active."""
        while True:
            try:
                if self.voting_active:
                    await self.send_votes_update()
                await asyncio.sleep(1)  # Update interval is 1 second
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in vote update loop: {e}")
                await asyncio.sleep(1)

    def start_vote_updates(self):
        """Start the vote update task."""
        if not self._vote_update_task:
            self._vote_update_task = asyncio.create_task(self.vote_update_loop())

    def stop_vote_updates(self):
        """Stop the vote update task."""
        if self._vote_update_task:
            self._vote_update_task.cancel()
            self._vote_update_task = None

    def process_vote(self, username, vote):
        """Process a vote from a user."""
        if self.voting_active and 0 <= vote < self.num_options and username not in self.voters:
            self.votes[vote - 1] = self.votes.get(vote, 0) + 1
            self.voters.add(username)

    def set_voting_active(self, active, num_options=0):
        """Set the voting status and number of options."""
        if active != self.voting_active:
            self.voting_active = active
            if active:
                self.logger.info(f"Voting opened with {num_options} options")
                self.num_options = num_options
                self.votes = {i: 0 for i in range(num_options)}
                self.voters.clear()
                self.start_vote_updates()
            else:
                self.logger.info("Voting closed")
                self.voters.clear()
                self.stop_vote_updates()

    def update_config(self, config):
        self.config = config