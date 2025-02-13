import * as spi from 'spi-device';
import { Gpio } from 'onoff';

export class EpaperDisplay {
  private spi: any;
  private readonly dcPin: Gpio;
  private readonly resetPin: Gpio;
  private readonly busyPin: Gpio;
  private readonly csPin: Gpio;

  // Display dimensions for 2.13 inch
  private readonly WIDTH = 250;
  private readonly HEIGHT = 122;

  constructor() {
    try {
      console.log('Initializing GPIO pins...');
      // Initialize GPIO pins
      this.dcPin = new Gpio(22, 'out');
      this.resetPin = new Gpio(11, 'out');
      this.busyPin = new Gpio(18, 'in');
      this.csPin = new Gpio(24, 'out');

      console.log('Initializing SPI...');
      // Initialize SPI
      this.spi = spi.open(0, 0, {
        mode: 0,
        maxSpeedHz: 4000000
      }, err => {
        if (err) {
          console.error('SPI initialization error:', err);
          throw err;
        }
        console.log('SPI initialized successfully');
      });

      this.init();
    } catch (error) {
      console.error('Display initialization failed:', error);
      throw error;
    }
  }

  private async init(): Promise<void> {
    await this.reset();
    await this.sendCommand(0x04); // Power on
    await this.waitUntilIdle();
    await this.sendCommand(0x00); // Panel setting
    await this.sendData(0x8F);    // LUT from OTP
  }

  private async reset(): Promise<void> {
    await this.resetPin.write(1);
    await new Promise(resolve => setTimeout(resolve, 200));
    await this.resetPin.write(0);
    await new Promise(resolve => setTimeout(resolve, 200));
    await this.resetPin.write(1);
    await new Promise(resolve => setTimeout(resolve, 200));
  }

  private async waitUntilIdle(): Promise<void> {
    while (await this.busyPin.read()) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }
  }

  private async sendCommand(cmd: number): Promise<void> {
    await this.dcPin.write(0);
    await this.csPin.write(0);
    await this.spi.transfer([{ sendBuffer: Buffer.from([cmd]) }]);
    await this.csPin.write(1);
  }

  private async sendData(data: number): Promise<void> {
    await this.dcPin.write(1);
    await this.csPin.write(0);
    await this.spi.transfer([{ sendBuffer: Buffer.from([data]) }]);
    await this.csPin.write(1);
  }

  public async displayTrackInfo(title: string, progress: number): Promise<void> {
    // Clear display buffer
    await this.sendCommand(0x10);
    for (let i = 0; i < this.WIDTH * this.HEIGHT / 8; i++) {
      await this.sendData(0xFF); // White background
    }

    // Create progress bar
    const progressWidth = Math.floor(this.WIDTH * progress);
    const progressY = 100;
    const progressHeight = 10;

    // Draw progress bar
    for (let y = progressY; y < progressY + progressHeight; y++) {
      for (let x = 0; x < this.WIDTH; x++) {
        const byte = x < progressWidth ? 0x00 : 0xFF;
        await this.sendData(byte);
      }
    }

    // Display title (simplified text rendering)
    const truncatedTitle = title.length > 20 ? title.substring(0, 17) + '...' : title;
    // Note: You'll need to implement actual text rendering here
    // This is a placeholder for the concept

    // Refresh display
    await this.sendCommand(0x12);
    await this.waitUntilIdle();
  }

  public async clear(): Promise<void> {
    await this.sendCommand(0x10);
    for (let i = 0; i < this.WIDTH * this.HEIGHT / 8; i++) {
      await this.sendData(0xFF);
    }
    await this.sendCommand(0x12);
    await this.waitUntilIdle();
  }
} 