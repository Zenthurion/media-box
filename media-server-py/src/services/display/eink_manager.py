from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path
import time
import asyncio
import logging

# Set simulator mode only if explicitly requested
SIMULATOR_MODE = os.environ.get('WAVESHARE_SIMULATOR', '0') == '1'
if SIMULATOR_MODE:
    logging.info("Running in e-ink simulator mode (set by WAVESHARE_SIMULATOR)")
else:
    logging.info("Attempting to use real e-ink hardware")

# Import the waveshare e-Paper library
# For 2.13 inch display V4 (264x176 pixels)
try:
    # First try to import from the project's lib directory
    import sys
    lib_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 'lib')
    print(f"Looking for lib directory at: {lib_dir}")
    print(f"Directory exists: {os.path.exists(lib_dir)}")
    if os.path.exists(lib_dir):
        sys.path.append(lib_dir)
        print(f"Added lib directory to path: {lib_dir}")
        print(f"Current sys.path: {sys.path}")
    
    # Only try to import real library if not in simulator mode
    if not SIMULATOR_MODE:
        from waveshare_epd import epd2in13_V4
        print("Successfully imported waveshare V4 library")
    else:
        from waveshare_epd.simulator import get_epd_class
        epd2in13_V4 = type('epd2in13_V4', (), {'EPD': get_epd_class("epd2in13_V4")})
        print("Using simulator EPD class")
except ImportError as e:
    logging.warning(f"Using simulation mode: {e}")
    # Dummy implementation for testing without hardware
    class epd2in13_V4:
        class EPD:
            # Define constants for update types
            FULL_UPDATE = 0
            PART_UPDATE = 1
            
            def __init__(self):
                self.width = 250
                self.height = 122
                logging.info("Initialized simulated display")
            
            def init(self, update=FULL_UPDATE): 
                logging.info(f"Display init (simulated) with update mode: {update}")
            
            def Clear(self): 
                logging.info("Display cleared (simulated)")
            
            def display(self, image): 
                logging.info("Display updated (simulated)")
            
            def sleep(self): 
                logging.info("Display put to sleep (simulated)")
            
            def getbuffer(self, image):
                logging.info("Getting buffer (simulated)")
                # Just return an empty buffer with the right size
                width, height = image.size
                buffer_size = ((width + 7) // 8) * height
                return bytearray([0xFF] * buffer_size)

class EinkDisplayManager:
    """Manages display of audio information on Waveshare 2.13" e-ink display"""
    
    def __init__(self, simulation_mode=False):
        """Initialize the display"""
        self.simulation_mode = simulation_mode or SIMULATOR_MODE
        
        if not self.simulation_mode:
            try:
                # Use V4 library
                self.epd = epd2in13_V4.EPD()
                self.epd.init()
                self.epd.Clear()
                self.width = self.epd.height  # Note the width/height swap for proper orientation
                self.height = self.epd.width
                logging.info(f"E-ink display V4 initialized: {self.width}x{self.height}")
            except Exception as e:
                logging.error(f"Error initializing e-ink display: {e}")
                self.simulation_mode = True
                self.width = 250
                self.height = 122
        else:
            logging.info("Using simulation mode for display")
            self.width = 250
            self.height = 122
        
        # Create image buffer
        self.image = Image.new('1', (self.width, self.height), 255)
        self.draw = ImageDraw.Draw(self.image)
        
        # Load fonts
        self._load_fonts()
        
        # Track last update time to limit refresh rate
        self.last_update = 0
        
        # Initialize with standby screen
        self.show_standby()
        
        # Add a clear test pattern to verify display works
        self._draw_test_pattern()
        
    def truncate_text(self, text, font, max_width):
        """Truncate text to fit within max_width pixels"""
        if not text:
            return ""
            
        width = self.draw.textlength(text, font=font)
        if width <= max_width:
            return text
            
        # Truncate and add ellipsis
        for i in range(len(text), 0, -1):
            truncated = text[:i] + "..."
            width = self.draw.textlength(truncated, font=font)
            if width <= max_width:
                return truncated
                
        return "..."
        
    def clear_display(self):
        """Clear the display"""
        self.image = Image.new('1', (self.width, self.height), 255)
        self.draw = ImageDraw.Draw(self.image)
        
    def update_display(self):
        """Update the physical display with current image buffer"""
        if self.simulation_mode:
            logging.info("Display update (simulated)")
            return
        
        try:
            # Use the same method as in the working example
            rotated_image = self.image.rotate(0)  # No rotation if needed
            buffer = self.epd.getbuffer(rotated_image)
            self.epd.display(buffer)
            logging.info("Physical display updated successfully")
        except Exception as e:
            logging.error(f"Error updating display: {e}")
            
    def show_standby(self):
        """Show standby screen"""
        self.clear_display()
        
        # Draw a bold border to verify display is working
        self.draw.rectangle((0, 0, self.width-1, self.height-1), outline=0, width=2)
        
        # Draw a heading
        self.draw.text((10, 10), "Media Player Ready", font=self.title_font, fill=0)
        
        # Draw some informative text
        self.draw.text((10, 40), "Waiting for", font=self.normal_font, fill=0)
        self.draw.text((10, 60), "audio input...", font=self.normal_font, fill=0)
        
        # Draw a footer
        current_time = time.strftime("%H:%M:%S")
        self.draw.text((10, self.height - 20), f"Time: {current_time}", font=self.small_font, fill=0)
        
        self.update_display()
        
        # Clear stored track info
        self.current_title = ""
        self.current_progress = 0
        self.is_playing = False
        
    def show_loading(self, text="Loading..."):
        """Show loading screen"""
        self.clear_display()
        self.draw.text((10, 30), text, font=self.title_font, fill=0)
        self.update_display()
        
    def show_playback(self, title, current_time, total_time, progress):
        """Show playback information"""
        self.clear_display()
        
        # Title (truncate if too long)
        title_truncated = self.truncate_text(title, self.title_font, self.width - 20)
        self.draw.text((10, 10), title_truncated, font=self.title_font, fill=0)
        
        # Progress bar
        bar_width = self.width - 20
        bar_height = 10
        bar_left = 10
        bar_top = 50
        
        # Draw progress bar outline
        self.draw.rectangle((bar_left, bar_top, bar_left + bar_width, bar_top + bar_height), outline=0)
        
        # Draw progress bar fill
        fill_width = int(progress * bar_width)
        if fill_width > 0:
            self.draw.rectangle(
                (bar_left, bar_top, bar_left + fill_width, bar_top + bar_height),
                fill=0
            )
        
        # Time display
        time_text = f"{current_time} / {total_time}"
        self.draw.text((10, 70), time_text, font=self.normal_font, fill=0)
        
        self.update_display()
        
    async def update_progress_display(self, title, current_time, total_time, progress):
        """Update the display with current progress (with rate limiting)"""
        # Store current values
        self.current_title = title
        self.current_progress = progress
        self.current_time = current_time
        self.total_time = total_time
        self.is_playing = True
        
        # Rate limit updates to avoid flickering and extend display life
        # E-ink displays shouldn't be refreshed too frequently
        current_time = time.time()
        if current_time - self.last_update < 5.0:  # Update at most every 5 seconds
            return
            
        self.last_update = current_time
        self.show_playback(title, current_time, total_time, progress)
        
    def cleanup(self):
        """Clean up the display when shutting down"""
        if not self.simulation_mode:
            try:
                self.epd.sleep()
            except Exception as e:
                logging.error(f"Error putting display to sleep: {e}") 

    def update_display_with_audio_info(self, title, is_playing, current_time, total_time, progress):
        """Update display with current audio track information"""
        logging.info(f"Updating display: {title} - Playing: {is_playing} - Progress: {progress:.1%}")
        
        if is_playing:
            self.show_playback(title, current_time, total_time, progress)
        else:
            if title:
                # If we have a title but not playing, show paused state
                self.show_playback(f"{title} (Paused)", current_time, total_time, progress)
            else:
                # No track playing
                self.show_standby() 

    def _draw_test_pattern(self):
        """Draw a test pattern to verify display is working"""
        try:
            logging.info("Drawing test pattern on display")
            # Clear the display
            self.clear_display()
            
            # Draw a border
            self.draw.rectangle((0, 0, self.width-1, self.height-1), outline=0)
            
            # Draw crossed lines
            self.draw.line((0, 0, self.width-1, self.height-1), fill=0, width=2)
            self.draw.line((0, self.height-1, self.width-1, 0), fill=0, width=2)
            
            # Draw text
            self.draw.text((self.width//2 - 40, self.height//2 - 10), 
                           "DISPLAY TEST", 
                           fill=0,
                           font=self.normal_font)
            
            # Update the display
            self.update_display()
            logging.info("Test pattern complete")
        except Exception as e:
            logging.error(f"Error drawing test pattern: {e}") 

    def _load_fonts(self):
        """Load fonts for the display"""
        font_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "fonts"
        font_dir.mkdir(exist_ok=True)
        
        # Default to system fonts if custom ones aren't available
        try:
            self.title_font = ImageFont.truetype(str(font_dir / "dejavu-sans.bold.ttf"), 16)
            self.normal_font = ImageFont.truetype(str(font_dir / "dejavu-sans.book.ttf"), 12)
            self.small_font = ImageFont.truetype(str(font_dir / "dejavu-sans.book.ttf"), 10)
        except IOError:
            # Fallback to default fonts
            self.title_font = ImageFont.load_default()
            self.normal_font = ImageFont.load_default()
            self.small_font = ImageFont.load_default() 