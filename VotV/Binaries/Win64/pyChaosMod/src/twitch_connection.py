import socket
import threading
import queue
import time

class TwitchConnection:
    def __init__(self, twitch_config):
        self.config = twitch_config
        self.message_queue = queue.Queue()
        self.outgoing_message_queue = queue.Queue()
        self.twitch_socket = None
        self.is_connected = False
        print("Connecting to Twitch...")
        if self.config['twitch']['oauth_token'] == 'notset' or self.config['twitch']['bot_username'] == 'notset' or self.config['twitch']['channel'] == 'notset':
            raise ValueError("Twitch configuration is not set properly. Please check your config.")
        threading.Thread(target=self.connect_to_twitch, daemon=True).start()
        threading.Thread(target=self.send_twitch_messages, daemon=True).start()

    def connect_to_twitch(self):
        while True:
            try:
                self.twitch_socket = socket.socket()
                self.twitch_socket.connect(("irc.chat.twitch.tv", 6667))
                self.twitch_socket.send(f"PASS oauth:{self.config['twitch']['oauth_token']}\r\n".encode('utf-8'))
                self.twitch_socket.send(f"NICK {self.config['twitch']['bot_username']}\r\n".encode('utf-8'))
                self.twitch_socket.send(f"JOIN #{self.config['twitch']['channel']}\r\n".encode('utf-8'))
                self.twitch_socket.setblocking(False)
                self.is_connected = True
                buffer = ""
                while True:
                    try:
                        data = self.twitch_socket.recv(1024).decode('utf-8')
                        buffer += data
                        messages = buffer.split("\r\n")
                        buffer = messages.pop()
                        for message in messages:
                            if message.startswith('PING'):
                                self.twitch_socket.send("PONG\r\n".encode('utf-8'))
                            elif 'PRIVMSG' in message:
                                self.message_queue.put(message)
                    except socket.error:
                        time.sleep(0.1)
            except Exception as e:
                print(f"Twitch connection error: {e}")
                self.is_connected = False
                time.sleep(5)  # Wait before attempting to reconnect

    def send_twitch_messages(self):
        while True:
            try:
                message = self.outgoing_message_queue.get()
                if self.twitch_socket and self.is_connected:
                    self.twitch_socket.send(f"PRIVMSG #{self.config['twitch']['channel']} :{message}\r\n".encode('utf-8'))
                time.sleep(1)  # Rate limiting
            except Exception as e:
                print(f"Error sending message to Twitch: {e}")
                self.is_connected = False

    def send_message(self, message):
        self.outgoing_message_queue.put(message)

    def get_messages(self):
        messages = []
        while not self.message_queue.empty():
            messages.append(self.message_queue.get())
        return messages

    def is_connected_to_twitch(self):
        return self.is_connected