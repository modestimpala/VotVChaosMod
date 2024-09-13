import re

class MessageHandler:
    def __init__(self, voting_system, email_system, shop_system):
        self.voting_system = voting_system
        self.email_system = email_system
        self.shop_system = shop_system
        
        self.chat_pattern = re.compile(r':(\w+)!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :(\d+)')
        self.email_pattern = re.compile(r':(\w+)!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :!email subject:(.+)body:(.+)')
        self.shop_pattern = re.compile(r':(\w+)!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :!shop(?:\s+(\w+))?')

    def handle_message(self, message):
        # Vote handling
        vote_match = self.chat_pattern.search(message)
        if vote_match and self.voting_system.voting_active:
            username, vote = vote_match.groups()
            self.voting_system.process_vote(username, int(vote))

        # Email handling
        if self.email_system.emails_enabled:
            email_match = self.email_pattern.search(message)
            if email_match:
                username, subject, body = email_match.groups()
                self.email_system.process_email(username, subject, body)
            elif '!email' in message:
                username_match = re.search(r':(\w+)!', message)
                if username_match:
                    username = username_match.group(1)
                    self.email_system.process_email(username, "General", "No body")

        # Shop handling
        shop_match = self.shop_pattern.search(message)
        if shop_match:
            username, item = shop_match.groups()
            self.shop_system.process_shop(username, item)