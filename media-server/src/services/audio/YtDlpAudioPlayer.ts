import { EventEmitter } from 'events';
import { IAudioPlayer, IPlaybackStatus } from './AudioPlayer';
import Speaker from 'speaker';
import { spawn } from 'child_process';
import { join } from 'path';
import { createHash } from 'crypto';
import { existsSync, mkdirSync, createReadStream, rmSync } from 'fs';

interface TrackInfo {
  duration: number;
  title: string;
}

export class YtDlpAudioPlayer extends EventEmitter implements IAudioPlayer {
  private speaker: Speaker | null = null;
  private ffmpeg: any = null;
  private ytDlp: any = null;
  private status: IPlaybackStatus = {
    isPlaying: false
  };
  private startTime: number = 0;
  private readonly cacheDir: string;

  constructor() {
    super();
    // Create cache directory in user's home directory
    this.cacheDir = join(process.env.HOME || process.env.USERPROFILE || '.', '.audio-cache');
    if (!existsSync(this.cacheDir)) {
      mkdirSync(this.cacheDir, { recursive: true });
    }
  }

  private getCacheFilePath(url: string): string {
    const hash = createHash('md5').update(url).digest('hex');
    return join(this.cacheDir, `${hash}.opus`); // Using .opus since we prefer opus codec
  }

  private async playLoadingSound(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        // Create ffmpeg process for the sound effect
        const ffmpeg = spawn('ffmpeg', [
          '-i', join(__dirname, '../../../assets/loading-1.wav'),
          '-loglevel', 'error',    // Only show actual errors
          '-hide_banner',          // Hide FFmpeg compilation info
          '-f', 's16le',
          '-ar', '48000',
          '-ac', '2',
          'pipe:1'
        ]);

        // Create temporary speaker for the sound effect
        const loadingSpeaker = new Speaker({
          channels: 2,
          bitDepth: 16,
          sampleRate: 48000
        });

        // Handle completion
        loadingSpeaker.on('finish', () => {
          resolve();
        });

        // Handle only real errors
        ffmpeg.stderr.on('data', (data: Buffer) => {
          const error = data.toString().trim();
          if (error) {  // Only log if there's an actual error
            console.error('Loading sound effect error:', error);
          }
        });

        // Pipe the audio
        ffmpeg.stdout.pipe(loadingSpeaker);

      } catch (error) {
        console.error('Failed to play loading sound:', error);
        resolve(); // Resolve anyway to continue with main playback
      }
    });
  }

  async play(url: string): Promise<void> {
    try {
      // Ensure previous playback is fully stopped before starting new one
      await this.stop();
      
      // Add a small delay to ensure cleanup is complete
      await new Promise(resolve => setTimeout(resolve, 100));

      const cacheFile = this.getCacheFilePath(url);
      let trackInfo: TrackInfo;

      if (!existsSync(cacheFile)) {
        this.playLoadingSound().catch(console.error);
        // Get info and download if not cached
        trackInfo = await this.getTrackInfo(url);
        
        console.log('\n▶️ Downloading:', trackInfo.title);
        console.log(`⏱️ Duration: ${Math.floor(trackInfo.duration / 60)}:${(trackInfo.duration % 60).toString().padStart(2, '0')}`);
        
        await this.downloadToCache(url, cacheFile);
      } else {
        // Get duration of cached file
        const duration = await this.getCachedFileDuration(cacheFile);
        // Try to get title from metadata, fallback to URL
        const title = await this.getCachedFileTitle(cacheFile) || url;
        trackInfo = { duration, title };
        
        console.log('\n▶️ Playing from cache:', trackInfo.title);
        console.log(`⏱️ Duration: ${Math.floor(trackInfo.duration / 60)}:${(trackInfo.duration % 60).toString().padStart(2, '0')}`);
      }

      // Play the cached file
      await this.playFromCache(cacheFile, trackInfo);

    } catch (error) {
      console.error('Error in YtDlpAudioPlayer:', error);
      await this.stop();
      throw error;
    }
  }

  private async getTrackInfo(url: string): Promise<TrackInfo> {
    const infoProcess = spawn('yt-dlp', [
      '--get-title',       // This should come first
      '--get-duration',
      '--no-playlist',
      '--no-check-formats',
      '--no-warnings',
      '--extract-audio',   // Add this to ensure we get audio info
      url
    ]);

    return new Promise<TrackInfo>((resolve, reject) => {
      let output = '';
      infoProcess.stdout.on('data', (data: Buffer) => {
        output += data.toString();
      });
      
      infoProcess.on('close', (code) => {
        if (code !== 0) {
          reject(new Error('Failed to get track info'));
          return;
        }
        const lines = output.trim().split('\n');
        if (lines.length < 2) {
          reject(new Error('Invalid yt-dlp output format'));
          return;
        }
        
        const title = lines[0].trim();
        const durationStr = lines[1].trim();
        
        console.log('Debug - Title:', title); // Debug log
        console.log('Debug - Duration:', durationStr); // Debug log
        
        const parts = durationStr.split(':').map(Number);
        let seconds = 0;
        if (parts.length === 3) { // HH:MM:SS
          seconds = parts[0] * 3600 + parts[1] * 60 + parts[2];
        } else if (parts.length === 2) { // MM:SS
          seconds = parts[0] * 60 + parts[1];
        } else { // SS
          seconds = parts[0];
        }
        resolve({ duration: seconds, title });
      });

      infoProcess.stderr.on('data', (data: Buffer) => {
        console.error('yt-dlp error:', data.toString());
      });

      infoProcess.on('error', reject);
    });
  }

  private async getCachedFileTitle(filePath: string): Promise<string | null> {
    return new Promise((resolve) => {
      const ffprobe = spawn('ffprobe', [
        '-v', 'error',
        '-select_streams', 'a:0', // Select audio stream
        '-show_entries', 'format_tags=title,TITLE:stream_tags=title,TITLE', // Check both format and stream tags
        '-of', 'json=c=1',  // Output in JSON format for easier parsing
        filePath
      ]);

      let output = '';
      ffprobe.stdout.on('data', (data) => {
        output += data.toString();
      });

      ffprobe.on('close', (code) => {
        if (code === 0 && output.trim()) {
          try {
            const metadata = JSON.parse(output);
            // Try to find title in different possible locations
            const title = metadata.format?.tags?.title || 
                         metadata.format?.tags?.TITLE ||
                         metadata.streams?.[0]?.tags?.title ||
                         metadata.streams?.[0]?.tags?.TITLE;
            
            if (title) {
              resolve(title);
            } else {
              resolve(null);
            }
          } catch (e) {
            console.error('Error parsing ffprobe output:', e);
            resolve(null);
          }
        } else {
          resolve(null);
        }
      });

      ffprobe.on('error', () => resolve(null));
    });
  }

  private async downloadToCache(url: string, cacheFile: string): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      const ytDlp = spawn('yt-dlp', [
        '-f', 'bestaudio[acodec=opus]/bestaudio',
        '--no-playlist',
        '--no-check-formats',
        '--no-warnings',
        '--force-ipv4',
        '--no-part',
        '--no-cache-dir',
        '--prefer-ffmpeg',
        '--add-metadata',        // Add this to include metadata
        '--embed-metadata',      // And this to embed it in the file
        '--embed-info-json',     // Embed all info in the file
        '--write-info-json',     // Also write info to separate file
        '-o', cacheFile,
        url
      ]);

      ytDlp.stderr.on('data', (data: Buffer) => {
        const error = data.toString().trim();
        if (error && !error.includes('Download completed')) {
          console.error('yt-dlp error:', error);
        }
      });

      ytDlp.on('close', (code) => {
        if (code === 0) {
          resolve();
        } else {
          reject(new Error(`yt-dlp exited with code ${code}`));
        }
      });

      ytDlp.on('error', reject);
    });
  }

  private async getCachedFileDuration(filePath: string): Promise<number> {
    return new Promise<number>((resolve, reject) => {
      const ffprobe = spawn('ffprobe', [
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        filePath
      ]);

      let output = '';
      ffprobe.stdout.on('data', (data) => {
        output += data.toString();
      });

      ffprobe.on('close', (code) => {
        if (code === 0) {
          resolve(parseFloat(output.trim()));
        } else {
          reject(new Error('Failed to get duration'));
        }
      });

      ffprobe.on('error', reject);
    });
  }

  private async playFromCache(filePath: string, trackInfo: TrackInfo): Promise<void> {
    // Create ffmpeg process to decode the cached file
    this.ffmpeg = spawn('ffmpeg', [
      '-i', filePath,
      '-ar', '48000',
      '-ac', '2',
      '-acodec', 'pcm_s16le',
      '-f', 's16le',
      '-bufsize', '8192',
      '-loglevel', 'error',
      'pipe:1'
    ]);

    // Create speaker
    this.speaker = new Speaker({
      channels: 2,
      bitDepth: 16,
      sampleRate: 48000
    });

    // Set up error handling
    this.ffmpeg.stdout.on('error', (error: Error) => {
      if (!error.message.includes('EPIPE')) {
        console.error('ffmpeg output stream error:', error);
        this.emit('error', error);
      }
    });

    // Store the finish handler so we can remove it later
    const finishHandler = () => {
      if (this.speaker === speaker) { // Only update status if this is still the current speaker
        this.status.isPlaying = false;
        console.log('Debug - Stopped from finish');
        this.emit('stopped');
      }
    };

    const speaker = this.speaker; // Store reference to current speaker
    speaker.on('finish', finishHandler);

    // Connect the pipeline
    this.ffmpeg.stdout.pipe(this.speaker);

    // Update status with title
    this.status = {
      isPlaying: true,
      currentUrl: filePath,
      duration: trackInfo.duration,
      title: trackInfo.title
    };
    this.startTime = Date.now();

    // Handle completion
    this.speaker.on('finish', () => {
      this.status.isPlaying = false;
      console.log('Debug - Stopped from finish');
      this.emit('stopped');
    });

    // Start progress updates
    this.startProgressUpdates();
  }

  private startProgressUpdates() {
    let lastLines = 0; // Keep track of how many lines we printed
    const updateInterval = setInterval(() => {
      if (this.status.isPlaying && this.status.duration) {
        const elapsed = (Date.now() - this.startTime) / 1000;
        this.status.progress = Math.min(elapsed / this.status.duration, 1);
        
        // Create a progress bar
        const width = 30;
        const complete = Math.floor(this.status.progress * width);
        const incomplete = width - complete;
        const progressBar = '█'.repeat(complete) + '▒'.repeat(incomplete);
        
        // Calculate time
        const currentTime = Math.floor(elapsed);
        const totalTime = Math.floor(this.status.duration);
        const currentMin = Math.floor(currentTime / 60);
        const currentSec = (currentTime % 60).toString().padStart(2, '0');
        const totalMin = Math.floor(totalTime / 60);
        const totalSec = (totalTime % 60).toString().padStart(2, '0');
        
        // Clear previous lines
        if (lastLines > 0) {
          process.stdout.write(`\x1b[${lastLines}A\x1b[0J`);
        }
        
        // Show new status
        console.log(`⏯️  ${this.status.title}`);
        console.log(`   ${progressBar} ${currentMin}:${currentSec}/${totalMin}:${totalSec}`);
        
        lastLines = 2; // We printed 2 lines
        
        if (this.status.progress >= 1) {
          console.log('✅ Playback complete');
          clearInterval(updateInterval);
        }
      } else {
        clearInterval(updateInterval);
      }
    }, 1000);
  }

  async stop(): Promise<void> {
    try {
      if (!this.speaker && !this.ffmpeg && !this.ytDlp) {
        return; // Nothing to stop
      }

      return new Promise<void>((resolve) => {
        // First, end input streams
        if (this.ytDlp) {
          this.ytDlp.stdout.unpipe();
          this.ytDlp.kill('SIGKILL');
          this.ytDlp = null;
        }

        // Wait for ffmpeg to finish processing
        if (this.ffmpeg) {
          this.ffmpeg.stdin.end();
          this.ffmpeg.stdout.unpipe();
          this.ffmpeg.kill('SIGKILL');
          this.ffmpeg = null;
        }

        // Clean up speaker and wait for it to finish
        if (this.speaker) {
          this.speaker.on('close', () => {
            this.speaker = null;
            this.status = { isPlaying: false };
            this.emit('stopped');
            resolve();
          });
          this.speaker.end();
        } else {
          resolve();
        }
      });

    } catch (error) {
      console.error('Error during stop:', error);
      // Force cleanup in case of error
      this.ytDlp = null;
      this.ffmpeg = null;
      this.speaker = null;
      this.status.isPlaying = false;
      throw error;
    }
  }

  async pause(): Promise<void> {
    if (this.speaker) {
      // @ts-ignore - Speaker does have pause() but it's not in the types
      this.speaker.pause();
      this.status.isPlaying = false;
      this.emit('paused');
    }
  }

  async resume(): Promise<void> {
    if (this.speaker) {
      // @ts-ignore - Speaker does have resume() but it's not in the types
      this.speaker.resume();
      this.status.isPlaying = true;
      this.emit('resumed');
    }
  }

  getStatus(): IPlaybackStatus {
    return { ...this.status };
  }

  public clearCache(): void {
    try {
      rmSync(this.cacheDir, { recursive: true, force: true });
      mkdirSync(this.cacheDir, { recursive: true });
      console.log('Cache cleared successfully');
    } catch (error) {
      console.error('Error clearing cache:', error);
    }
  }
} 