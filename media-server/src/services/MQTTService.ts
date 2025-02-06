import Aedes, { AedesPublishPacket, Client } from 'aedes';
import { createServer, Server } from 'net';
import { config } from '../config/config';
import { URLHandler } from '../handlers/URLHandler';
import { MediaPlayer } from './MediaPlayer';
import play from 'play-dl';
// import { MQTTMessage, MQTTClient } from '../types/mqtt';

export class MQTTService {
  private aedes: Aedes;
  private server: Server;
  private urlHandler: URLHandler;
  private mediaPlayer: MediaPlayer;

  constructor() {
    this.aedes = new Aedes();
    this.server = createServer(this.aedes.handle);
    this.urlHandler = new URLHandler();
    this.mediaPlayer = new MediaPlayer();

    // Bind methods to maintain 'this' context
    this.handlePublish = this.handlePublish.bind(this);
    this.handleClientConnect = this.handleClientConnect.bind(this);
    this.handleClientDisconnect = this.handleClientDisconnect.bind(this);
  }

  async start(): Promise<void> {
    // Set up event handlers
    this.setupEventHandlers();

    return new Promise((resolve, reject) => {
      this.server.listen(config.mqtt.port, () => {
        console.log(`MQTT broker running on port ${config.mqtt.port}`);
        resolve();
      }).on('error', (error) => {
        console.error('Failed to start MQTT broker:', error);
        reject(error);
      });
    });
  }

  private setupEventHandlers(): void {
    // Handle client connections
    this.aedes.on('client', this.handleClientConnect);
    
    // Handle client disconnections
    this.aedes.on('clientDisconnect', this.handleClientDisconnect);
    
    // Handle published messages
    this.aedes.on('publish', this.handlePublish as any);
  }

  private async handlePublish(packet: AedesPublishPacket, client: Client): Promise<void> {
    if (!client) return;

    try {
      // Convert payload to string if it's a Buffer
      const message = packet.payload instanceof Buffer 
        ? packet.payload.toString() 
        : packet.payload as string;

      console.log(`Received message from ${client.id} on topic ${packet.topic}`);

      // Only process messages from the expected topic
      if (packet.topic === config.mqtt.urlTopic) {
        console.log(`Processing URL: ${message}`);
        await this.processUrl(message);
      }
    } catch (error) {
      console.error('Error processing published message:', error);
    }
  }

  private async processUrl(url: string): Promise<void> {
    try {
      // url = url.replace('music.youtube.com', 'youtube.com');
      const mediaType = await this.urlHandler.determineMediaType(url);
      
      // Validate the URL first
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

  private handleClientConnect(client: Client): void {
    console.log(`Client connected: ${client.id}`);
  }

  private handleClientDisconnect(client: Client): void {
    console.log(`Client disconnected: ${client.id}`);
  }

  async stop(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.aedes.close(() => {
          this.server.close((err) => {
            if (err) {
              console.error('Error closing server:', err);
              reject(err);
              return;
            }
            console.log('MQTT broker stopped');
            resolve();
          });
        });
      } catch (error) {
        console.error('Error stopping MQTT broker:', error);
        reject(error);
      }
    });
  }
}