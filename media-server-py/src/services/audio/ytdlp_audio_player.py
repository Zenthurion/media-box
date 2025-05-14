from typing import Dict, Callable, List, Optional
import asyncio
import os
import json
import hashlib
from pathlib import Path
import vlc
import yt_dlp

# Import the EinkDisplayManager
from ..display.eink_manager import EinkDisplayManager

class YtDlpAudioPlayer:
    def __init__(self, use_eink_display=True):
        # Debug audio devices
        print("Available audio devices:")
        instance = vlc.Instance()
        mods = instance.audio_output_enumerate_devices()
        if mods:
            for m in mods:
                print(f"Device: {m}")
        else:
            print("No audio devices found!")
        
        # Initialize VLC with ALSA
        self._vlc_instance = vlc.Instance('--no-xlib', '--aout=alsa', '--alsa-audio-device=hw:1,0')
        self._player = self._vlc_instance.media_player_new()
        self._current_media = None
        self._status = {"is_playing": False}
        self._start_time = 0
        
        # Set up cache directory
        home = os.environ.get('HOME', os.environ.get('USERPROFILE', '.'))
        self._cache_dir = Path(home) / '.audio-cache'
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Event handlers
        self._event_handlers: Dict[str, List[Callable]] = {
            'error': [],
            'stopped': []
        }
        
        # Set up VLC event manager
        self._event_manager = self._player.event_manager()
        self._event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, 
                                       self._on_playback_finished)

        # Initialize e-ink display
        self._use_eink_display = use_eink_display
        if self._use_eink_display:
            try:
                self._display = EinkDisplayManager()
            except Exception as e:
                print(f"Error initializing e-ink display: {e}")
                self._use_eink_display = False

    def on(self, event: str, callback: Callable) -> None:
        """Register an event handler"""
        if event in self._event_handlers:
            self._event_handlers[event].append(callback)
    
    def _emit(self, event: str, *args) -> None:
        """Emit an event to all registered handlers"""
        if event in self._event_handlers:
            for handler in self._event_handlers[event]:
                handler(*args)

    def _on_playback_finished(self, event) -> None:
        """Handle playback finished event"""
        self._status["is_playing"] = False
        print('Debug - Stopped from finish')
        # Update the display to standby mode
        if self._use_eink_display:
            self._display.show_standby()
        self._emit('stopped')

    def _get_cache_file_path(self, url: str) -> Path:
        """Generate cache file path from URL"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self._cache_dir / f"{url_hash}.opus"
        
    def _get_metadata_file_path(self, url: str) -> Path:
        """Generate metadata file path from URL"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self._cache_dir / f"{url_hash}.json"
        
    async def _save_track_metadata(self, url: str, metadata: Dict) -> None:
        """Save track metadata to cache"""
        metadata_file = self._get_metadata_file_path(url)
        try:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f)
        except Exception as e:
            print(f"Error saving metadata: {e}")
            
    async def _load_track_metadata(self, url: str) -> Optional[Dict]:
        """Load track metadata from cache if available"""
        metadata_file = self._get_metadata_file_path(url)
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading metadata: {e}")
        return None

    async def _get_track_info(self, url: str) -> Dict:
        """Get track information using yt-dlp"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'format': 'bestaudio'
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await asyncio.to_thread(ydl.extract_info, url, download=False)
                return {
                    'duration': info.get('duration', 0),
                    'title': info.get('title', url)
                }
        except Exception as e:
            print(f"Error getting track info: {e}")
            raise

    async def play(self, url: str) -> None:
        """Play audio from URL"""
        try:
            # Stop any current playback
            await self.stop()
            await asyncio.sleep(0.1)  # Small delay for cleanup

            # Show loading screen on e-ink display
            if self._use_eink_display:
                self._display.show_loading("Downloading...")

            print(f"Checking cache for {url}")
            cache_file = self._get_cache_file_path(url)
            
            print(f"Cache file: {cache_file}")
            if not cache_file.exists():
                print('\n▶️ Downloading...')
                track_info = await self._get_track_info(url)
                await self._download_to_cache(url, cache_file)
                # Save metadata after download
                await self._save_track_metadata(url, track_info)
            else:
                print(f"Cache file found for {url}")
                # Try to load metadata from cache
                track_info = await self._load_track_metadata(url)
                if track_info is None:
                    # Fall back to online lookup if metadata not cached
                    print("Metadata not cached, fetching online...")
                    track_info = await self._get_track_info(url)
                    await self._save_track_metadata(url, track_info)
                print('\n▶️ Playing from cache')

            print(f"▶️ Playing: {track_info['title']}")
            duration_min = track_info['duration'] // 60
            duration_sec = track_info['duration'] % 60
            print(f"⏱️ Duration: {duration_min}:{duration_sec:02d}")

            # Update e-ink display with initial information
            if self._use_eink_display:
                current_time = "0:00"
                total_time = f"{duration_min}:{duration_sec:02d}"
                self._display.show_playback(track_info['title'], current_time, total_time, 0)

            # Play the cached file
            self._current_media = self._vlc_instance.media_new(str(cache_file))
            self._player.set_media(self._current_media)
            self._player.play()
            
            self._status = {
                "is_playing": True,
                "current_url": str(cache_file),
                "duration": track_info['duration'],
                "title": track_info['title']
            }
            # Get current time safely
            self._start_time = asyncio.get_running_loop().time()
            
            # Start progress updates
            asyncio.create_task(self._update_progress())

        except Exception as error:
            print(f"Error in play: {error}")
            await self.stop()
            raise

    async def _download_to_cache(self, url: str, cache_file: Path) -> None:
        """Download audio to cache using yt-dlp"""
        ydl_opts = {
            'format': 'bestaudio[acodec=opus]/bestaudio',
            'outtmpl': str(cache_file),
            'quiet': True,
            'no_warnings': True,
            'extract_audio': True,
            'audio_format': 'opus'
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                await asyncio.to_thread(ydl.download, [url])
            await self._save_track_metadata(url, await self._get_track_info(url))
        except Exception as e:
            print(f"Download error: {e}")
            raise

    async def _update_progress(self) -> None:
        """Update playback progress"""
        last_lines = 0
        while self._status.get("is_playing", False):
            if "duration" in self._status:
                # Get current time safely
                elapsed = asyncio.get_running_loop().time() - self._start_time
                progress = min(elapsed / self._status["duration"], 1)
                
                # Create progress bar
                width = 30
                complete = int(progress * width)
                incomplete = width - complete
                progress_bar = '█' * complete + '▒' * incomplete
                
                # Calculate times
                current_time = int(elapsed)
                total_time = int(self._status["duration"])
                current_min, current_sec = divmod(current_time, 60)
                total_min, total_sec = divmod(total_time, 60)
                
                current_time_str = f"{current_min}:{current_sec:02d}"
                total_time_str = f"{total_min}:{total_sec:02d}"
                
                # Clear previous lines and redraw progress in terminal
                if last_lines > 0:
                    # Move cursor up and clear lines
                    print(f"\033[{last_lines}A\033[J", end='')
                
                # Show new status in terminal
                print(f"⏯️  {self._status.get('title', 'Unknown')}")
                print(f"   {progress_bar} {current_time_str}/{total_time_str}")
                
                last_lines = 2
                
                # Update e-ink display
                if self._use_eink_display:
                    await self._display.update_progress_display(
                        self._status.get('title', 'Unknown'),
                        current_time_str,
                        total_time_str,
                        progress
                    )
                
                if progress >= 1:
                    print("✅ Playback complete")
                    if self._use_eink_display:
                        self._display.show_standby()
                    break
            
            await asyncio.sleep(1)

    async def stop(self) -> None:
        """Stop playback"""
        if self._player:
            self._player.stop()
            self._status = {"is_playing": False}
            
            # Update e-ink display to standby mode
            if self._use_eink_display:
                self._display.show_standby()
                
            self._emit('stopped')

    def get_status(self) -> Dict:
        """Get current playback status"""
        return dict(self._status)

    def clear_cache(self) -> None:
        """Clear the audio cache"""
        try:
            for file in self._cache_dir.glob('*'):
                file.unlink()
            print('Cache cleared successfully')
        except Exception as e:
            print(f'Error clearing cache: {e}')

    def __del__(self):
        """Ensure resources are cleaned up"""
        if hasattr(self, '_player') and self._player:
            self._player.stop()
        if hasattr(self, '_vlc_instance') and self._vlc_instance:
            del self._vlc_instance
        
        # Clean up the e-ink display
        if hasattr(self, '_use_eink_display') and self._use_eink_display:
            if hasattr(self, '_display'):
                self._display.cleanup()

    async def __aenter__(self):
        """Support for async context manager"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Support for async context manager"""
        await self.stop() 