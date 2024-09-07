import pyglet

class SoundManager:
    def __init__(self):
        self.sound_activated = pyglet.media.StaticSource(pyglet.media.load('./sounds/activated.wav'))
        self.sound_voting = pyglet.media.StaticSource(pyglet.media.load('./sounds/voting.wav'))
        self.sound_command = pyglet.media.StaticSource(pyglet.media.load('./sounds/command.wav'))
        self.sound_vote = pyglet.media.StaticSource(pyglet.media.load('./sounds/vote.wav'))
        self.sound_500cigs = pyglet.media.StaticSource(pyglet.media.load('./sounds/500cigs.wav'))

    def play_activated_sound(self):
        self.sound_activated.play()

    def play_voting_sound(self):
        self.sound_voting.play()

    def play_command_sound(self):
        self.sound_command.play()

    def play_vote_sound(self):
        self.sound_vote.play()

    def play_500cigs_sound(self):
        self.sound_500cigs.play()