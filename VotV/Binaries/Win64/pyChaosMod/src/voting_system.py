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

    def check_voting_status(self):
        if os.path.exists(self.is_voting_file):
            with open(self.is_voting_file, 'r') as f:
                content = f.read().strip()
                return content.lower() == 'true'
        return False

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
            with open(self.votes_file, 'w') as f:
                for num, command in self.current_options:
                    votes = self.votes.get(num, 0)
                    f.write(f"{num};{command}={votes}\n")
            self.last_write_time = current_time

    def process_vote(self, username, vote):
        if self.voting_active and vote in [num for num, _ in self.current_options] and username not in self.voters:
            self.votes[vote] = self.votes.get(vote, 0) + 1
            self.voters.add(username)
           

    def update(self):
        is_voting = self.check_voting_status()
       
        if is_voting and not self.voting_active:
            # Voting just started
            self.voting_active = True
            self.read_voting_options()
            self.voters.clear()
        elif not is_voting and self.voting_active:
            # Voting just ended
            self.voting_active = False
            self.voters.clear()

        if self.voting_active:
            self.write_votes_to_file() 