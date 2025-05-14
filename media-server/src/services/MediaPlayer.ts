import { exec, spawn } from 'child_process';
import { promisify } from 'util';
import { stream, YouTubeStream, setToken, authorization } from 'play-dl';
import { IAudioPlayer } from './audio/AudioPlayer';
import { YtDlpAudioPlayer } from './audio/YtDlpAudioPlayer';

const execAsync = promisify(exec);

export class MediaPlayer {
  private audioPlayer: IAudioPlayer;

  constructor(audioPlayer?: IAudioPlayer) {
    this.audioPlayer = audioPlayer || new YtDlpAudioPlayer();

    // Set up event listeners
    this.audioPlayer.on('error', (error: any) => {
      console.error('Audio player error:', error);
    });

    this.audioPlayer.on('stopped', () => {
      console.log('Playback stopped');
    });
  }

  async playAudio(url: string): Promise<void> {
    console.log(`Playing audio from URL: ${url}`);
    try {
      // Ensure any existing playback is stopped first
      await this.stopAudio();
      await this.audioPlayer.play(url);
    } catch (error) {
      console.error('Error playing audio:', error);
      await this.stopAudio(); // Ensure cleanup on error
      throw error;
    }
  }

  async stopAudio(): Promise<void> {
    try {
      await this.audioPlayer.stop();
    } catch (error) {
      console.error('Error stopping audio:', error);
    }
  }

  getPlaybackStatus() {
    return this.audioPlayer.getStatus();
  }
}