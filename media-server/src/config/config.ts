export const config = {
    mqtt: {
        port: parseInt(process.env.MQTT_PORT || '1883', 10),
        host: process.env.MQTT_HOST || 'localhost',
        // Topic that the ESP32 will publish URLs to
        urlTopic: 'nfc/url',
        // Optional: Add authentication credentials if needed
        auth: {
          username: process.env.MQTT_USERNAME,
          password: process.env.MQTT_PASSWORD
        }
      },
    chromecast: {
      ip: process.env.CHROMECAST_IP || 'YOUR_CHROMECAST_IP'
    },
    audio: {
      device: process.env.AUDIO_DEVICE || 'default'
    }
  };