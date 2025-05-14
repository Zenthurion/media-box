from typing import Protocol, Optional
from abc import abstractmethod
import asyncio
from services.audio.ytdlp_audio_player import YtDlpAudioPlayer

class AudioPlayer(Protocol):
    """Protocol defining the interface for audio players"""
    
    @abstractmethod
    async def play(self, url: str) -> None:
        """Play audio from the given URL"""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop current playback"""
        pass
    
    @abstractmethod
    def get_status(self) -> dict:
        """Get current playback status"""
        pass
    
    @abstractmethod
    def on(self, event: str, callback: callable) -> None:
        """Register an event handler"""
        pass

class MediaPlayer:
    def __init__(self, audio_player: Optional[AudioPlayer] = None):
        self.audio_player = audio_player or YtDlpAudioPlayer()
        
        # Set up event listeners
        self.audio_player.on('error', self._handle_error)
        self.audio_player.on('stopped', self._handle_stopped)
    
    def _handle_error(self, error: Exception) -> None:
        print(f"Audio player error: {error}")
    
    def _handle_stopped(self) -> None:
        print("Playback stopped")
    
    async def play_audio(self, url: str) -> None:
        print(f"Playing audio from URL: {url}")
        try:
            # Ensure any existing playback is stopped first
            await self.stop_audio()
            await self.audio_player.play(url)
        except Exception as error:
            print(f"Error playing audio: {error}")
            await self.stop_audio()  # Ensure cleanup on error
            raise
    
    async def stop_audio(self) -> None:
        try:
            await self.audio_player.stop()
        except Exception as error:
            print(f"Error stopping audio: {error}")
    
    def get_playback_status(self) -> dict:
        """Get current playback status"""
        return self.audio_player.get_status() 