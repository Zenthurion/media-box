import { Server } from "./server";

async function main() {
  const server = new Server();
    // Handle process termination
    process.on('SIGINT', async () => {
      console.log('Shutting down...');
      await server.stop();
      process.exit(0);
    });
  
    try {
      await server.start();
      console.log('Server started successfully');
    } catch (error) {
      console.error('Failed to start server:', error);
      process.exit(1);
    }
}

main();