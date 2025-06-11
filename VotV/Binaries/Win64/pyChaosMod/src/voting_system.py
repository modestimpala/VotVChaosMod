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
        self.option_names = []  # Store option names
        self.websocket_handler = None
        self.overlay_server = None  # Reference to overlay server
        self.logger = logging.getLogger(__name__)
        self._vote_update_task = None

    def set_websocket_handler(self, websocket_handler):
        self.websocket_handler = websocket_handler
        
    def set_overlay_server(self, overlay_server):
        self.overlay_server = overlay_server
        
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
                self.logger.debug(f"Sent vote update: {vote_counts}")
            except Exception as e:
                self.logger.error(f"Failed to send vote update: {e}")
        else:
            self.logger.error("No game connection available to send vote update")
            
        # Also send to overlay server
        if self.overlay_server:
            try:
                await self.overlay_server.send_voting_update()
            except Exception as e:
                self.logger.error(f"Failed to send overlay update: {e}")

    async def vote_update_loop(self):
        """Continuously send vote updates while voting is active."""
        while True:
            try:
                if self.voting_active:
                    await self.send_votes_update()
                    await asyncio.sleep(1)  # Update interval is 1 second
                else:
                    # Voting is not active, exit the loop
                    break
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
        if self.voting_active and 1 <= vote <= self.num_options and username not in self.voters:
            self.logger.debug(f"Received vote from {username}: {vote}")
            self.votes[vote - 1] = self.votes.get(vote - 1, 0) + 1
            self.voters.add(username)
        else:
            self.logger.debug(f"Ignored vote from {username}: {vote}, voting_active={self.voting_active}, num_options={self.num_options}, username in voters={username in self.voters}")

    def set_voting_active(self, active, num_options=0, option_names=None):
        """Set the voting status, number of options, and option names."""
        if active != self.voting_active:
            self.voting_active = active
            if active:
                self.logger.debug(f"Voting opened with {num_options} options")
                self.num_options = num_options
                self.option_names = option_names or [f"Option {i+1}" for i in range(num_options)]
                self.votes = {i: 0 for i in range(num_options)}
                self.voters.clear()
                self.start_vote_updates()
            else:
                self.logger.debug("Voting closed")
                
                # Determine winner before clearing data
                winner = self.get_winning_option()
                
                self.voters.clear()
                self.stop_vote_updates()
                
                # Send result to overlay if there was a winner
                if winner and self.overlay_server:
                    asyncio.create_task(self.overlay_server.send_voting_result(winner))
                    # Don't send the voting update immediately - let the result display first
                else:
                    # No winner, safe to hide immediately
                    if self.overlay_server:
                        asyncio.create_task(self.overlay_server.send_voting_update())

    def get_winning_option(self):
        """Get the winning option name."""
        if not self.votes or not self.option_names:
            return None
            
        # Find the option with the most votes
        max_votes = max(self.votes.values()) if self.votes.values() else 0
        if max_votes == 0:
            return None
            
        # Find all options with max votes (handle ties)
        winning_indices = [i for i, votes in self.votes.items() if votes == max_votes]
        
        if len(winning_indices) == 1:
            winning_index = winning_indices[0]
            if winning_index < len(self.option_names):
                return f"{winning_index + 1}. {self.option_names[winning_index]} ({max_votes} votes)"
        else:
            # Handle tie
            tied_options = []
            for i in winning_indices:
                if i < len(self.option_names):
                    tied_options.append(f"{i + 1}. {self.option_names[i]}")
            if tied_options:
                return f"Tie between: {', '.join(tied_options)} ({max_votes} votes each)"
                
        return None

    def update_config(self, config):
        self.config = config