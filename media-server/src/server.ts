import { MQTTService } from "./services/MQTTService";
import { identifyUrl } from './handlers/URLHandler';
import { MediaPlayer } from './services/MediaPlayer';

export class Server {

    private mqttService: MQTTService;
    private mediaPlayer: MediaPlayer;

    constructor() {
        this.mqttService = new MQTTService();
        this.mediaPlayer = new MediaPlayer();
    }

    public async start() {

        await this.mqttService.start();
        this.mqttService.on('url', (url: string) => this.processUrl(url));

        // TODO: Add handling for stop and restart buttons

        console.log('Server started');
    }

    public async stop() {

        await this.mqttService.stop();

        console.log('Server stopped');
    }

    
  private async processUrl(url: string): Promise<void> {
    try {
      const mediaType = await identifyUrl(url);
      
      if (mediaType === 'invalid') {
        console.log(`Invalid URL: ${url}`);
        // TODO: Print to display
        return;
      }

      switch (mediaType) {
        case 'youtube-music':
          console.log('Playing audio from YouTube Music');

          await this.mediaPlayer.playAudio(url);
          break;
        case 'youtube-video':
          throw new Error('Not implemented');
        default:
          console.log(`Unsupported media type for URL: ${url}`);
      }
    } catch (error) {
      console.error('Error processing URL:', error);
    }
  }
}