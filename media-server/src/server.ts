import { MQTTService } from "./services/MQTTService";

import { URLHandler } from './handlers/URLHandler';
import { MediaPlayer } from './services/MediaPlayer';
import play from 'play-dl';

export class Server {

    private mqttService: MQTTService;
    private urlHandler: URLHandler;
    private mediaPlayer: MediaPlayer;

    constructor() {
        this.mqttService = new MQTTService();
        this.urlHandler = new URLHandler();
        this.mediaPlayer = new MediaPlayer();
    }

    public async start() {

        await this.mqttService.start();
        this.mqttService.on('url', (url: string) => {
            this.processUrl(url);
        });

        // TODO: Add handling for stop and restart buttons

        console.log('Server started');
    }

    public async stop() {

        await this.mqttService.stop();

        console.log('Server stopped');
    }

    
  private async processUrl(url: string): Promise<void> {
    try {
      const mediaType = await this.urlHandler.determineMediaType(url);
      
      const validateUrl = await play.validate(url);
      if (!validateUrl) {
        console.log(`Invalid URL: ${url}`);
        return;
      }

      switch (mediaType) {
        case 'youtube-music':
          console.log('Playing audio from YouTube Music');

          await this.mediaPlayer.playAudio(url);
          break;
        case 'youtube-video':
          console.log('Casting video from YouTube');
          await this.mediaPlayer.castVideo(url);
          break;
        default:
          console.log(`Unsupported media type for URL: ${url}`);
      }
    } catch (error) {
      console.error('Error processing URL:', error);
    }
  }
}