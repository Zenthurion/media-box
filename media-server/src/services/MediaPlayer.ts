import { exec, spawn } from 'child_process';
import { promisify } from 'util';
import { stream, YouTubeStream, setToken, authorization } from 'play-dl';
import chromecastApi from 'chromecast-api';

const execAsync = promisify(exec);

export class MediaPlayer {
  private chromecast: any | null = null;

  constructor() {
    // Initialize and find your Chromecast
    const client = new chromecastApi();
    client.on('device', (device: any) => {
      this.chromecast = device;
    });
  }

  async playAudio(url: string): Promise<void> {
    console.log(`Playing audio from URL: ${url}`);
    try {
      // Get the direct audio URL using yt-dlp
      // const command = `yt-dlp -f bestaudio -g "${url}"`;
      // console.log('Executing command:', command);

      const process = spawn('yt-dlp', [
        '-f', 'bestaudio',
        '--hls-prefer-ffmpeg', // Faster HLS stream handling
        '--live-from-start', // Start as soon as possible
        '--geo-bypass', // Avoid region issues
        '--verbose',
        '--buffer-size', '16K',
        '--throttled-rate', '500K',
        '-o', '-',
        url
      ]);
      //  '-f', 'bestaudio[ext=mp3]', // Prefer MP3 for instant play
      // '--hls-prefer-ffmpeg', // Faster HLS stream handling
      // '--live-from-start', // Start as soon as possible
      // '--no-warnings', // Remove startup delay
      // '--geo-bypass', // Avoid region issues
      // '--force-ipv4', // Faster network resolution
      // '-o', '-',

      // const { stdout: audioUrl } = await execAsync(
      //   command,
      //   { maxBuffer: 1024 * 1024 * 10 } // 10MB buffer
      // );

      console.log('Got direct audio URL');

      const ffmpeg = spawn('ffmpeg', [
        '-i', 'pipe:0',       // Read from stdin (yt-dlp output)
        '-f', 'mp3',          // Convert to MP3 (stabilize format)
        '-b:a', '192k',       // Use constant bitrate (CBR) for stability
        '-bufsize', '64K',    // Reduce buffer to avoid lag
        '-acodec', 'mp3',     // Force MP3 codec
        '-'
    ]);

      // Platform-specific audio player initialization
      // const player = process.platform === 'win32'
      //   ? exec(`ffplay -nodisp -autoexit -hide_banner -i "${audioUrl.trim()}"`)
      //   : exec(`mplayer -ao alsa -really-quiet -noconsolecontrols "${audioUrl.trim()}"`);
      const player = spawn('ffplay', [
        '-nodisp', 
        '-autoexit', 
        '-loglevel', 'quiet',
        '-probesize', '512K',
        '-analyzeduration', '1000000',
        '-i', '-']);
        
      process.stdout.pipe(ffmpeg.stdin);
      ffmpeg.stdout.pipe(player.stdin);

      if (!player.stdin) {
        throw new Error('Failed to create player');
      }

      console.log('Created player process');

      process.on('close', () => {
        console.log('Playback finished');
      });

      process.on('error', (err) => {
        console.error('Error:', err);
      });

      // Add error handlers
      player.on('error', (error) => {
        console.error('Player process error:', error);
      });

      // player.stderr?.on('data', (data) => {
      //   console.error('Player stderr:', data.toString());
      // });

      // Wait for playback to finish
      return new Promise((resolve, reject) => {
        player.on('close', (code) => {
          console.log('Player process closed with code:', code);
          if (code !== 0) {
            reject(new Error(`Player process exited with code ${code}`));
          } else {
            resolve();
          }
        });
      });

    } catch (error) {
      console.error('Error playing audio:', error);
      throw error;
    }
  }

  async castVideo(url: string): Promise<void> {
    return;
    // try {
    //   if (!this.chromecast) {
    //     throw new Error('No Chromecast device found');
    //   }

    //   // Get the highest quality stream URL
    //   const videoInfo = await stream(url);
    //   const videoUrl = videoInfo.url;

    //   await this.chromecast.play(videoUrl, {
    //     contentType: 'video/mp4',
    //     autoplay: true,
    //   });
    // } catch (error) {
    //   console.error('Error casting video:', error);
    // }
  }
}