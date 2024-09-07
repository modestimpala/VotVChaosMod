import random
import time
import json
import os
from src.utils import is_chaos_enabled

class VotingSystem:
    def __init__(self, config, sound_manager):
        self.config = config
        self.voting_active = False
        self.votes = {}
        self.voters = set()
        self.current_options = []
        self.vote_end_time = 0
        self.cooldown_end_time = 0
        self.winner = None
        self.winner_trigger_text = None
        self.winner_display_end_time = 0
        self.command_cooldowns = {}
        self.rounds_since_last_vote = 0
        self.result_version = 0
        self.sound_manager = sound_manager

        with open(config['files']['commands'], 'r') as commands_file:
            self.all_commands = json.load(commands_file)['commands']

    def start_voting(self):
        if self.voting_active or not is_chaos_enabled(self.config):
            return
        self.voting_active = True
        self.votes = {}
        self.voters.clear()

        available_commands = [cmd for cmd in self.all_commands if self.command_cooldowns.get(cmd['name'], 0) == 0]

        if len(available_commands) < self.config['voting']['num_options']:
            self.command_cooldowns = {cmd['name']: 0 for cmd in self.all_commands}
            available_commands = self.all_commands

        self.current_options = []
        for _ in range(self.config['voting']['num_options']):
            if random.random() < self.config['voting'].get('combine_commands_chance', 0.1) and len(available_commands) >= 2:
                cmd1, cmd2 = random.sample(available_commands, 2)
                combined_command = {
                    'name': f"{cmd1['name']} + {cmd2['name']}",
                    'command': f"{cmd1['command']};{cmd2['command']}",
                    'trigger_text': f"{cmd1['trigger_text']} and {cmd2['trigger_text']}",
                }
                self.current_options.append(combined_command)
            else:
                cmd = random.choice(available_commands)
                self.current_options.append(cmd)
            
            available_commands = [cmd for cmd in available_commands if cmd not in self.current_options]

        self.vote_end_time = time.time() + self.config['voting']['duration']
        self.winner = None
        self.winner_trigger_text = None
        self.rounds_since_last_vote += 1
        self.sound_manager.play_voting_sound()

    def end_voting(self):
        self.voting_active = False
        if self.votes:
            winner_id = max(self.votes, key=self.votes.get)
            winning_command = self.current_options[winner_id - 1]
            self.winner = winning_command['name']
            self.winner_trigger_text = winning_command['trigger_text']
            self.winner_display_end_time = time.time() + 15
            self.result_version += 1
            self.save_result(winning_command)
            if '500cigs' in winning_command['name']:
                self.sound_manager.play_500cigs_sound()
            else:
                self.sound_manager.play_command_sound()

            for cmd_name in winning_command['name'].split(' + '):
                self.command_cooldowns[cmd_name] = self.config['voting']['command_cooldown_rounds']

        for cmd in self.all_commands:
            self.command_cooldowns[cmd['name']] = max(0, self.command_cooldowns.get(cmd['name'], 0) - 1)

        self.cooldown_end_time = time.time() + random.randint(
            self.config['voting']['cooldown_min'], 
            self.config['voting']['cooldown_max']
        )
        
        self.rounds_since_last_vote = 0

    def process_vote(self, username, vote):
        if self.voting_active and 1 <= vote <= len(self.current_options) and username not in self.voters:
            self.votes[vote] = self.votes.get(vote, 0) + 1
            self.voters.add(username)
            self.sound_manager.play_vote_sound()

    def trigger_voting(self):
        if is_chaos_enabled(self.config) and not self.voting_active:
            print("Manual voting triggered")
            self.start_voting()

    def update(self):
        current_time = time.time()

        if not is_chaos_enabled(self.config):
            self.reset_mod_state()
            return

        if self.voting_active:
            if current_time > self.vote_end_time:
                self.end_voting()
        else:
            if current_time >= self.cooldown_end_time:
                self.start_voting()

        if self.winner and current_time >= self.winner_display_end_time:
            self.winner = None
            self.winner_trigger_text = None

        if self.rounds_since_last_vote >= self.config['voting']['reset_cooldown_after_rounds']:
            self.command_cooldowns = {cmd['name']: 0 for cmd in self.all_commands}
            self.rounds_since_last_vote = 0

    def reset_mod_state(self):
        self.voting_active = False
        self.winner = None
        self.winner_trigger_text = None
        self.votes = {}
        self.voters.clear()
        self.current_options = []
        self.cooldown_end_time = 0
        self.vote_end_time = 0
        self.winner_display_end_time = 0
        self.rounds_since_last_vote = 0
        self.command_cooldowns = {cmd['name']: 0 for cmd in self.all_commands}
        self.end_voting()

    def save_result(self, winning_command):
        with open(self.config['files']['result'], 'w') as f:
            json.dump({
                "version": self.result_version,
                "command": winning_command['command'],
                "name": winning_command['name']
            }, f)