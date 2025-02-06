declare module 'castv2-client' {
  export class Client {
    connect(host: string, callback: () => void): void;
    launch(receiver: any, callback: (err: Error | null, player: any) => void): void;
  }
  
  export const DefaultMediaReceiver: any;
} 