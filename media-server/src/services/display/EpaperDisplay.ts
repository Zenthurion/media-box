import * as spi from 'spi-device';
import { Gpio } from 'onoff';
import { existsSync } from 'fs';
import { promises as fs } from 'fs';

export class EpaperDisplay {
  private spi: any;
  private dcPin: Gpio | null = null;
  private resetPin: Gpio | null = null;
  private busyPin: Gpio | null = null;
  private csPin: Gpio | null = null;

  // Display dimensions for 2.13 inch
  private readonly WIDTH = 250;
  private readonly HEIGHT = 122;

  constructor() {
    try {
      // Wait for GPIO system to be ready
      if (!existsSync('/dev/gpiomem')) {
        throw new Error('GPIO is not enabled. Check /boot/config.txt');
      }

      console.log('Initializing GPIO pins...');
      
      // Initialize pins one at a time with error checking
      const pins = [
        { name: 'DC', pin: 25, direction: 'out' as const },
        { name: 'RESET', pin: 17, direction: 'out' as const },
        { name: 'BUSY', pin: 24, direction: 'in' as const },
        { name: 'CS', pin: 8, direction: 'out' as const }
      ];

      for (const { name, pin, direction } of pins) {
        try {
          // Export GPIO synchronously
          const gpioPath = `/sys/class/gpio/gpio${pin}`;
          if (!existsSync(gpioPath)) {
            const exportPath = '/sys/class/gpio/export';
            require('fs').writeFileSync(exportPath, pin.toString());
            // Small delay to let the system set up the GPIO
            require('child_process').execSync('sleep 0.1');
          }

          const gpio = new Gpio(pin, direction);
          console.log(`Successfully initialized ${name} pin (GPIO${pin})`);
          switch (name) {
            case 'DC': this.dcPin = gpio; break;
            case 'RESET': this.resetPin = gpio; break;
            case 'BUSY': this.busyPin = gpio; break;
            case 'CS': this.csPin = gpio; break;
          }
        } catch (error) {
          console.error(`Failed to initialize ${name} pin (GPIO${pin}):`, error);
          throw error;
        }
      }

      // Set initial states
      console.log('Setting initial pin states...');
      this.dcPin?.writeSync(1);
      this.resetPin?.writeSync(1);
      this.csPin?.writeSync(1);

      console.log('Initializing SPI...');
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
      this.cleanup();
      throw error;
    }
  }

  private cleanup(): void {
    try {
        if (this.spi) {
            this.spi.close();
        }
        this.dcPin?.unexport();
        this.resetPin?.unexport();
        this.busyPin?.unexport();
        this.csPin?.unexport();
    } catch (error) {
        console.error('Error during cleanup:', error);
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
    await this.resetPin?.write(1);
    await new Promise(resolve => setTimeout(resolve, 200));
    await this.resetPin?.write(0);
    await new Promise(resolve => setTimeout(resolve, 200));
    await this.resetPin?.write(1);
    await new Promise(resolve => setTimeout(resolve, 200));
  }

  private async waitUntilIdle(): Promise<void> {
    while (await this.busyPin?.read()) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }
  }

  private async sendCommand(cmd: number): Promise<void> {
    await this.dcPin?.write(0);
    await this.csPin?.write(0);
    await this.spi.transfer([{ sendBuffer: Buffer.from([cmd]) }]);
    await this.csPin?.write(1);
  }

  private async sendData(data: number): Promise<void> {
    await this.dcPin?.write(1);
    await this.csPin?.write(0);
    await this.spi.transfer([{ sendBuffer: Buffer.from([data]) }]);
    await this.csPin?.write(1);
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