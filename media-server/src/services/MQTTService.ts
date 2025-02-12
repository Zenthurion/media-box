import Aedes, { AedesPublishPacket, Client } from 'aedes';
import { createServer, Server } from 'net';
import { config } from '../config/config';
import EventEmitter from 'events';

export class MQTTService extends EventEmitter {
  private aedes: Aedes;
  private server: Server;

  constructor() {
    super();

    this.aedes = new Aedes();
    this.server = createServer(this.aedes.handle);

    this.handlePublish = this.handlePublish.bind(this);
    this.handleClientConnect = this.handleClientConnect.bind(this);
    this.handleClientDisconnect = this.handleClientDisconnect.bind(this);
  }

  async start(): Promise<void> {
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
    this.aedes.on('client', this.handleClientConnect);
    this.aedes.on('clientDisconnect', this.handleClientDisconnect);
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

      if (packet.topic === config.mqtt.urlTopic) {
        console.log(`Processing URL: ${message}`);
        this.emit('url', message);
      }
    } catch (error) {
      console.error('Error processing published message:', error);
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