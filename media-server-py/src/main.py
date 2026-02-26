import logging
import asyncio
from services.mqtt_service import MQTTService
from services.media_player import MediaPlayer
from handlers.url_handler import identify_url
from src.shutdown_handler import shutdown_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Server:
    def __init__(self):
        self.mqtt_service = MQTTService()
        self.media_player = MediaPlayer()

    async def start(self):
        await self.mqtt_service.start()
        self.mqtt_service.on('url', self.process_url)
        self.mqtt_service.on('system', self.process_system_command)
        self.mqtt_service.on('playback', self.process_media_command)

        logger.info("Server started")

    async def stop(self):
        await self.mqtt_service.stop()
        logger.info("Server stopped")

    async def process_url(self, url: str) -> None:
        logger.info(f"Processing URL: {url}")
        try:
            media_type = await identify_url(url)
            logger.info(f"Media type: {media_type}")
            if media_type == 'invalid':
                logger.warning(f"Invalid URL: {url}")
                # TODO: Print to display
                return

            if media_type == 'youtube-music':
                logger.info('Playing audio from YouTube Music')
                await self.media_player.play_audio(url)
            elif media_type == 'youtube-video':
                raise NotImplementedError('YouTube video playback not implemented')
            else:
                logger.warning(f"Unsupported media type for URL: {url}")
                
        except Exception as error:
            logger.error(f"Error processing URL: {error}", exc_info=True)

    async def process_system_command(self, command: str) -> None:
        logger.info(f"Processing system command: {command}")
        normalized = command.strip().lower()

        if normalized == "shutdown":
            await shutdown_manager.shutdown()
        elif normalized == "start":
            logger.info("Start command received; no action required while running.")
        else:
            logger.warning(f"Unknown system command received: {command}")

    async def process_media_command(self, command: str) -> None:
        logger.info(f"Processing media command: {command}")
        try:
            await self.media_player.process_command(command)
        except Exception as error:
            logger.error(f"Error handling media command {command}: {error}", exc_info=True)


async def main():
    logger.info("Running main.py")
    
    # Set up shutdown handler
    shutdown_manager.setup()
    
    server = Server()
    try:
        await server.start()
        
        # Keep the application running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        await server.stop()
        logger.info("Shutting down...")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 
