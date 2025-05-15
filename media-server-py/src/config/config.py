class MQTTConfig:
    def __init__(self):
        self.port = 1883
        self.host = "mqtt"  # This will resolve to the mqtt service name in docker-compose
        self.url_topic = "nfc/url"
        self.audio_state_topic = "media-server/audio-state"

class Config:
    def __init__(self):
        self.mqtt = MQTTConfig()

config = Config() 