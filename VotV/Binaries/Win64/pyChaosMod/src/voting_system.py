import logging
import time
import os

class VotingSystem:
    def __init__(self, config):
        self.config = config
        self.voting_active = False
        self.votes = {}
        self.voters = set()
        self.current_options = []
        self.is_voting_file = config['files']['isVoting']
        self.votes_file = config['files']['votes']
        self.last_write_time = 0
        self.write_interval = 1  # Write every 1 second
        self.current_voting_status = False  # Voting status from last check

        self.logger = logging.getLogger(__name__)

    def check_voting_status(self):
        """Check if voting is enabled by reading the status file."""
        try:
            if os.path.exists(self.is_voting_file):
                try:
                    with open(self.is_voting_file, 'r') as f:
                        content = f.read().strip()
                        return content.lower() == 'true'
                except PermissionError:
                    # Log the error but don't crash
                    self.logger.debug(f"Permission denied when reading {self.is_voting_file}, will retry next update")
                    return self.current_voting_status  # Return last known status
                except Exception as e:
                    self.logger.error(f"Error reading voting status file: {e}")
                    return self.current_voting_status  # Return last known status
        except Exception as e:
            self.logger.error(f"Error checking voting file existence: {e}")
            return self.current_voting_status  # Return last known status

    def read_voting_options(self):
        self.current_options = []
        self.votes = {}
        if os.path.exists(self.votes_file):
            with open(self.votes_file, 'r') as f:
                for line in f:
                    parts = line.strip().split('=')
                    if len(parts) == 2:
                        option, votes = parts
                        num, command = option.split(';')
                        self.current_options.append((int(num), command))
                        self.votes[int(num)] = int(votes)

    def write_votes_to_file(self):
        current_time = time.time()
        if current_time - self.last_write_time >= self.write_interval:
            try:
                with open(self.votes_file, 'w') as f:
                    for num, command in self.current_options:
                        votes = self.votes.get(num, 0)
                        line = f"{num};{command}={votes}\n"
                        f.write(line)
                self.last_write_time = current_time
            except IOError as e:
                self.logger.error(f"Failed to write votes to file: {self.votes_file}")
                self.logger.error(f"IOError: {str(e)}")
            except Exception as e:
                self.logger.error(f"Unexpected error while writing votes to file: {self.votes_file}")
                self.logger.error(f"Error: {str(e)}")

    def process_vote(self, username, vote):
        if self.voting_active and vote in [num for num, _ in self.current_options] and username not in self.voters:
            self.votes[vote] = self.votes.get(vote, 0) + 1
            self.voters.add(username)
           
    def update_config(self, config):
        self.config = config

    def update(self):
        try:
            new_status = self.check_voting_status()
            if new_status != self.current_voting_status:
                self.logger.debug(f"Voting status changed to: {new_status}")
                self.current_voting_status = new_status
        except Exception as e:
            self.logger.error(f"Error in voting system update: {e}")
            # Continue running even if there's an error
            pass  # Use last known status

        is_voting = self.current_voting_status
       
        if is_voting and not self.voting_active:
            # Voting just started
            self.logger.debug("Voting opened")
            self.voting_active = True
            self.read_voting_options()
            self.voters.clear()
        elif not is_voting and self.voting_active:
            # Voting just ended
            self.logger.debug("Voting closed")
            self.voting_active = False
            self.voters.clear()

        if self.voting_active:
            self.write_votes_to_file() 