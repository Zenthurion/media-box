class MQTTConfig:
    def __init__(self):
        self.port = 1883
        self.host = "mqtt"  # This will resolve to the mqtt service name in docker-compose
        self.url_topic = "media-server/url"
        self.audio_state_topic = "media-server/audio-state"
        self.playback_topic = "media-server/playback-command"

class Config:
    def __init__(self):
        self.mqtt = MQTTConfig()

config = Config() 