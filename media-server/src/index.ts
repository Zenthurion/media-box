import { MQTTService } from "./services/MQTTService";

async function main() {
    const mqttService = new MQTTService();

    // Handle process termination
    process.on('SIGINT', async () => {
      console.log('Shutting down...');
      await mqttService.stop();
      process.exit(0);
    });
  
    try {
      await mqttService.start();
      console.log('Server started successfully');
    } catch (error) {
      console.error('Failed to start server:', error);
      process.exit(1);
    }
}

main();