import { EventEmitter } from 'events';

export interface IPlaybackStatus {
  isPlaying: boolean;
  currentUrl?: string;
  progress?: number;  // 0-1 for progress percentage
  duration?: number;  // in seconds
  title?: string;    // Add title to the interface
}

export interface IAudioPlayer extends EventEmitter {
  play(url: string): Promise<void>;
  stop(): Promise<void>;
  pause(): Promise<void>;
  resume(): Promise<void>;
  getStatus(): IPlaybackStatus;
}