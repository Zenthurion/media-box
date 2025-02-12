import { EventEmitter } from 'events';
import { stream, YouTubeStream, video_info } from 'play-dl';
import { IAudioPlayer, IPlaybackStatus } from './AudioPlayer';
import Speaker from 'speaker';
import { spawn } from 'child_process';
import { Readable } from 'stream';

export class PlayDLAudioPlayer extends EventEmitter implements IAudioPlayer {
  private currentStream: YouTubeStream | null = null;
  private speaker: Speaker | null = null;
  private ffmpeg: any = null;
  private status: IPlaybackStatus = {
    isPlaying: false
  };
  private startTime: number = 0;
  private videoInfo: Awaited<ReturnType<typeof video_info>> | null = null;

  async play(url: string): Promise<void> {
    try {
      await this.stop();

      try {
        // Try play-dl first
        this.videoInfo = await video_info(url);
        this.currentStream = await stream(url, {
          quality: 140,
          discordPlayerCompatibility: true
        });
      } catch (error) {
        console.log('play-dl failed, falling back to yt-dlp');
        // Fall back to yt-dlp direct streaming
        return this.playWithYtDlp(url);
      }

      // Update status
      this.status = {
        isPlaying: true,
        currentUrl: url,
        duration: this.videoInfo.video_details.durationInSec
      };
      this.startTime = Date.now();

      // Create ffmpeg process for transcoding
      this.ffmpeg = spawn('ffmpeg', [
        '-i', 'pipe:0',
        '-analyzeduration', '0',
        '-loglevel', '0',
        '-f', 's16le',
        '-ar', '48000',
        '-ac', '2',
        'pipe:1'
      ]);

      // Create speaker
      this.speaker = new Speaker({
        channels: 2,
        bitDepth: 16,
        sampleRate: 48000
      });

      // Set up pipeline
      this.currentStream.stream.pipe(this.ffmpeg.stdin);
      this.ffmpeg.stdout.pipe(this.speaker);

      // Handle events
      this.speaker.on('finish', () => {
        this.status.isPlaying = false;
        this.emit('stopped');
      });

      // Handle ffmpeg errors
      this.ffmpeg.stderr.on('data', (data: Buffer) => {
        console.error('FFmpeg error:', data.toString());
      });

      // Update progress periodically
      this.startProgressUpdates();

    } catch (error) {
      console.error('Error in PlayDLAudioPlayer:', error);
      await this.stop();
      throw error;
    }
  }

  private async playWithYtDlp(url: string): Promise<void> {
    // Create yt-dlp process
    const ytDlp = spawn('yt-dlp', [
      '-f', 'bestaudio',
      '--no-warnings',
      '-o', '-',
      url
    ]);

    // Create ffmpeg process
    this.ffmpeg = spawn('ffmpeg', [
      '-i', 'pipe:0',
      '-analyzeduration', '0',
      '-loglevel', '0',
      '-f', 's16le',
      '-ar', '48000',
      '-ac', '2',
      'pipe:1'
    ]);

    // Create speaker
    this.speaker = new Speaker({
      channels: 2,
      bitDepth: 16,
      sampleRate: 48000
    });

    // Set up pipeline
    ytDlp.stdout.pipe(this.ffmpeg.stdin);
    this.ffmpeg.stdout.pipe(this.speaker);

    // Update status
    this.status = {
      isPlaying: true,
      currentUrl: url
    };

    // Handle events
    this.speaker.on('finish', () => {
      this.status.isPlaying = false;
      this.emit('stopped');
    });

    // Error handling
    ytDlp.stderr.on('data', (data: Buffer) => {
      console.error('yt-dlp error:', data.toString());
    });

    this.ffmpeg.stderr.on('data', (data: Buffer) => {
      console.error('FFmpeg error:', data.toString());
    });
  }

  private startProgressUpdates() {
    const updateInterval = setInterval(() => {
      if (this.status.isPlaying && this.status.duration) {
        const elapsed = (Date.now() - this.startTime) / 1000;
        this.status.progress = Math.min(elapsed / this.status.duration, 1);
        
        if (this.status.progress >= 1) {
          clearInterval(updateInterval);
        }
      } else {
        clearInterval(updateInterval);
      }
    }, 1000);
  }

  async stop(): Promise<void> {
    if (this.currentStream) {
      this.currentStream.stream.destroy();
      this.currentStream = null;
    }

    if (this.ffmpeg) {
      this.ffmpeg.kill();
      this.ffmpeg = null;
    }

    if (this.speaker) {
      this.speaker.end();
      this.speaker = null;
    }

    this.status = {
      isPlaying: false
    };
    this.videoInfo = null;
    
    this.emit('stopped');
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
} 