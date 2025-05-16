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
                
                # Check if the update modes are available, otherwise define defaults
                # Some versions of the library don't have these constants
                if hasattr(self.epd, 'FULL_UPDATE'):
                    self.FULL_UPDATE = self.epd.FULL_UPDATE
                    self.PART_UPDATE = self.epd.PART_UPDATE
                    logging.info(f"Using library-defined update modes - FULL: {self.FULL_UPDATE}, PARTIAL: {self.PART_UPDATE}")
                else:
                    # Define fallback values based on the waveshare documentation
                    logging.info("Library doesn't provide update mode constants, using defaults")
                    self.FULL_UPDATE = 0
                    self.PART_UPDATE = 1
                
                # Initialize with FULL_UPDATE for initial screen
                self.epd.init(self.FULL_UPDATE)
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
            self.FULL_UPDATE = 0
            self.PART_UPDATE = 1
        
        # Create image buffer
        self.image = Image.new('1', (self.width, self.height), 255)
        self.draw = ImageDraw.Draw(self.image)
        
        # Load fonts
        self._load_fonts()
        
        # Track last update time to limit refresh rate
        self.last_update = 0
        self.last_progress = 0
        
        # Keep track of current display state
        self.current_title = ""
        self.current_progress = 0
        self.current_time = "0:00"
        self.total_time = "0:00"
        self.is_playing = False
        
        logging.info("Starting display initialization sequence...")
        
        # First try to show the logo
        logo_success = self.show_logo()
        logging.info(f"Logo display {'successful' if logo_success else 'failed'}")
        
        if not logo_success:
            # Only show standby if logo display failed
            logging.info("Showing standby screen after logo display failed")
            self.show_standby()
        
        # No test pattern at startup
        # self._draw_test_pattern()
        
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
        
    def update_display(self, use_partial_update=False):
        """Update the physical display with current image buffer"""
        if self.simulation_mode:
            logging.info(f"Display update (simulated) - Partial: {use_partial_update}")
            return
        
        try:
            # Log what we're about to do
            update_mode = self.PART_UPDATE if use_partial_update else self.FULL_UPDATE
            logging.info(f"Initializing display with mode: {update_mode} (partial={use_partial_update})")
            
            # Initialize with partial update if requested
            self.epd.init(update_mode)
            
            # Use the same method as in the working example
            rotated_image = self.image.rotate(0)  # No rotation if needed
            buffer = self.epd.getbuffer(rotated_image)
            self.epd.display(buffer)
            logging.info(f"Physical display updated successfully - Partial: {use_partial_update}")
        except Exception as e:
            logging.error(f"Error updating display: {e}")
            import traceback
            logging.error(traceback.format_exc())
            
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
        current_time = time.strftime("%H:%M")  # Removed seconds
        self.draw.text((10, self.height - 20), f"Time: {current_time}", font=self.small_font, fill=0)
        
        # Use full update for standby screen
        self.update_display(use_partial_update=False)
        
        # Clear stored track info
        self.current_title = ""
        self.current_progress = 0
        self.current_time = "0:00"
        self.total_time = "0:00"
        self.is_playing = False
        
    def show_loading(self, text="Loading..."):
        """Show loading screen"""
        self.clear_display()
        self.draw.text((10, 30), text, font=self.title_font, fill=0)
        
        # Use full update for loading screen
        self.update_display(use_partial_update=False)
        
    def show_playback(self, title, current_time, total_time, progress):
        """Show playback information"""
        # Check if only the progress and time need update (for partial refresh)
        progress_only_update = (
            title == self.current_title and 
            abs(progress - self.current_progress) < 0.5  # Only significant progress changes
        )
        
        if progress_only_update:
            # Just update the progress section
            self._update_progress_section(current_time, total_time, progress)
            return
            
        # Full screen update needed
        self.clear_display()
        
        # Title (truncate if too long)
        title_truncated = self.truncate_text(title, self.title_font, self.width - 20)
        self.draw.text((10, 10), title_truncated, font=self.title_font, fill=0)
        
        # Draw progress bar and time
        self._draw_progress_bar(current_time, total_time, progress)
        
        # Store current values
        self.current_title = title
        self.current_time = current_time
        self.total_time = total_time
        self.current_progress = progress
        
        # Use full update for full screen refresh
        self.update_display(use_partial_update=False)
    
    def _update_progress_section(self, current_time, total_time, progress):
        """Update only the progress bar and time sections (for partial refresh)"""
        logging.info(f"Doing partial update for progress: {progress:.2f}")
        
        # Calculate positions
        bar_width = self.width - 20
        bar_height = 10
        bar_left = 10
        bar_top = 50
        
        # Clear just the progress bar and time area
        self.draw.rectangle(
            (bar_left - 2, bar_top - 2, bar_left + bar_width + 2, self.height - 10),
            fill=255
        )
        
        # Redraw progress bar and time
        self._draw_progress_bar(current_time, total_time, progress)
        
        # Store current values
        self.current_time = current_time
        self.total_time = total_time
        self.current_progress = progress
        
        # Use partial update for minimal refresh
        logging.info("Using PARTIAL UPDATE for progress bar")
        self.update_display(use_partial_update=True)
    
    def _draw_progress_bar(self, current_time, total_time, progress):
        """Draw progress bar and time display"""
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
        
        # Only show total duration, not current time
        # This prevents constant updating of the time display
        approx_min = int(float(progress) * float(self._parse_time_to_seconds(total_time)) / 60)
        time_text = f"~{approx_min} min / {total_time}" 
        self.draw.text((10, 70), time_text, font=self.normal_font, fill=0)
    
    def _parse_time_to_seconds(self, time_str):
        """Convert a time string (MM:SS) to seconds"""
        try:
            parts = time_str.split(':')
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            return 0
        except (ValueError, IndexError):
            return 0
    
    async def update_progress_display(self, title, current_time, total_time, progress):
        """Update the display with current progress (with rate limiting)"""
        # Store current values for future reference
        self.is_playing = True
        
        # Rate limit updates to avoid flickering and extend display life
        current_time_sec = time.time()
        
        # Calculate percentage change in progress
        progress_delta = abs(progress - self.current_progress)
        
        # Only update if:
        # 1. It's been at least 10 seconds since last update, or
        # 2. Progress has changed by at least 5%
        if (current_time_sec - self.last_update < 10.0 and progress_delta < 0.05):
            return
        
        # Remember last update time
        self.last_update = current_time_sec
        
        # Determine if we need full refresh or partial refresh
        if title != self.current_title:
            # Title changed - do a full refresh
            self.show_playback(title, current_time, total_time, progress)
        else:
            # Only progress changed - use partial refresh
            self._update_progress_section(current_time, total_time, progress)

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
            # Only update if significant changes
            progress_delta = abs(progress - self.current_progress)
            time_delta = time.time() - self.last_update
            
            if (title != self.current_title or 
                time_delta > 10.0 or 
                progress_delta > 0.05):
                
                if title != self.current_title:
                    # Full refresh for new title
                    self.show_playback(title, current_time, total_time, progress)
                else:
                    # Partial refresh for progress updates
                    self._update_progress_section(current_time, total_time, progress)
                
                self.last_update = time.time()
                self.current_progress = progress
                self.current_title = title
        else:
            if title:
                # If we have a title but not playing, show paused state
                pause_title = f"{title} (Paused)"
                if pause_title != self.current_title:
                    self.show_playback(pause_title, current_time, total_time, progress)
                    self.current_title = pause_title
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
            
            # Update the display with full update
            logging.info("Doing FULL update test pattern")
            self.update_display(use_partial_update=False)
            
            # Wait a moment
            import time
            time.sleep(2)
            
            # Now try a partial update of just one section
            logging.info("Doing PARTIAL update test")
            self.draw.rectangle((10, 90, 100, 110), fill=0)
            self.update_display(use_partial_update=True)
            
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

    def show_logo(self):
        """Show the logo image at startup"""
        logging.info("Attempting to show logo at startup...")
        try:
            # Look for logo in the root directory and multiple possible locations
            project_root = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
            logging.info(f"Project root directory: {project_root}")
            
            # Try multiple possible locations with debug output
            possible_paths = [
                project_root / "logo.png",
                Path(os.path.dirname(os.path.abspath(__file__))) / "logo.png",
                Path("/app/logo.png"),  # For Docker environment
                Path("logo.png"),       # Current working directory
            ]
            
            # Debug output for all paths
            for path in possible_paths:
                logging.info(f"Checking for logo at: {path} (exists: {path.exists()})")
            
            logo_path = None
            for path in possible_paths:
                if path.exists():
                    logo_path = path
                    break
            
            if logo_path:
                logging.info(f"Found logo at {logo_path}")
                try:
                    logo_img = Image.open(logo_path)
                    logging.info(f"Successfully opened logo image: {logo_img.size} mode={logo_img.mode}")
                    
                    # Resize if necessary to fit display
                    if logo_img.size != (self.width, self.height):
                        logging.info(f"Resizing logo from {logo_img.size} to {(self.width, self.height)}")
                        logo_img = logo_img.resize((self.width, self.height), Image.LANCZOS)
                    
                    # Convert to 1-bit color depth if needed
                    if logo_img.mode != '1':
                        logging.info(f"Converting logo from {logo_img.mode} to 1-bit mode")
                        logo_img = logo_img.convert('1')
                    
                    # Clear display first
                    logging.info("Clearing display before showing logo")
                    self.clear_display()
                    
                    # Replace the current image buffer with the logo
                    self.image = logo_img
                    self.draw = ImageDraw.Draw(self.image)
                    
                    # Update display with logo
                    logging.info("Sending logo to display...")
                    self.update_display(use_partial_update=False)
                    logging.info("Logo displayed successfully")
                    
                    # Wait a moment to display the logo
                    logging.info("Waiting 3 seconds to show logo...")
                    time.sleep(3)
                    logging.info("Logo display complete")
                    
                    # Return True to indicate success
                    return True
                except Exception as e:
                    logging.error(f"Error processing logo image: {e}")
                    import traceback
                    logging.error(traceback.format_exc())
            else:
                logging.warning(f"Logo file not found in any of these locations: {possible_paths}")
                # Try the debug logo as fallback
                logging.info("Trying debug logo instead...")
                return self.draw_debug_logo()
        except Exception as e:
            logging.error(f"Error in show_logo: {e}")
            import traceback
            logging.error(traceback.format_exc())
            
        # If we get here, try the debug logo
        logging.info("Attempting debug logo after failure...")
        return self.draw_debug_logo()

    def draw_debug_logo(self):
        """Draw a simple logo for debugging"""
        logging.info("Creating debug logo image")
        self.clear_display()
        
        # Draw a border
        self.draw.rectangle((0, 0, self.width-1, self.height-1), outline=0, width=3)
        
        # Draw diagonal lines
        self.draw.line((0, 0, self.width-1, self.height-1), fill=0, width=2)
        self.draw.line((0, self.height-1, self.width-1, 0), fill=0, width=2)
        
        # Draw text in the center
        self.draw.text((self.width//2 - 40, self.height//2 - 10), 
                      "DEBUG LOGO", 
                      fill=0,
                      font=self.title_font)
        
        # Update the display with full update
        logging.info("Displaying debug logo...")
        self.update_display(use_partial_update=False)
        logging.info("Debug logo displayed")
        time.sleep(3)
        return True 